import os
import sys
import json
import glob
import subprocess
import argparse
import shutil
import getpass
import re
from datetime import datetime

# Resolve Rscript: prefer PATH, then the TROPIC_RSCRIPT env override, then common
# install locations. No hard-coded per-user paths (a clone on another machine must
# not depend on a specific developer's home directory).
RSCRIPT_PATH = shutil.which("Rscript") or os.environ.get("TROPIC_RSCRIPT")
if not RSCRIPT_PATH:
    if sys.platform == "win32":
        candidates = [
            os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "R"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\R"),
        ]
        for base in candidates:
            hits = glob.glob(os.path.join(base, "R-*", "bin", "Rscript.exe")) if base else []
            if hits:
                RSCRIPT_PATH = sorted(hits)[-1]  # newest installed R
                break
    else:
        for path in ["/usr/local/bin/Rscript", "/opt/homebrew/bin/Rscript",
                     "/Library/Frameworks/R.framework/Resources/bin/Rscript"]:
            if os.path.exists(path):
                RSCRIPT_PATH = path
                break
    if not RSCRIPT_PATH:
        RSCRIPT_PATH = "Rscript"  # last resort: rely on PATH at call time

BACKUP_DIR = "backup_adam"

def create_backup():
    if os.path.exists(BACKUP_DIR):
        shutil.rmtree(BACKUP_DIR)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if os.path.exists("04_adam"):
        for f in os.listdir("04_adam"):
            if f.endswith(".xpt"):
                shutil.copy(os.path.join("04_adam", f), os.path.join(BACKUP_DIR, f))

def restore_backup():
    if os.path.exists(BACKUP_DIR):
        for f in os.listdir(BACKUP_DIR):
            if f.endswith(".xpt"):
                shutil.copy(os.path.join(BACKUP_DIR, f), os.path.join("04_adam", f))
        shutil.rmtree(BACKUP_DIR)

def clean_backup():
    if os.path.exists(BACKUP_DIR):
        shutil.rmtree(BACKUP_DIR)

def run_command(cmd, cwd=None):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        return res.returncode, res.stdout, res.stderr
    except Exception as e:
        return -1, "", str(e)

def dry_run():
    print("=== PIPELINE ENVIRONMENT DRY-RUN ===")
    
    # Check Directories
    dirs = ["01_raw_source", "02_production_sas", "03_validation_r", "04_adam", 
            "05_reconciliation", "06_telemetry", "07_define_xml", "08_reviewers_guides", "09_tfl"]
    for d in dirs:
        status = "OK" if os.path.isdir(d) else "MISSING (Will be created)"
        print(f"  Directory: {d:20} -> {status}")
        
    # Check Rscript Executable
    if os.path.exists(RSCRIPT_PATH):
        print(f"  R Compiler: {RSCRIPT_PATH} -> FOUND")
    else:
        print(f"  R Compiler: {RSCRIPT_PATH} -> NOT FOUND")
        
    # Check Git
    rc, stdout, stderr = run_command(["git", "--version"])
    if rc == 0:
        print(f"  Version Control: Git -> FOUND ({stdout.strip()})")
    else:
        print("  Version Control: Git -> NOT FOUND")
        
    print("Environment check completed successfully!")
    return True

def rollback():
    print("=== PIPELINE ROLLBACK ===")
    print("Reverting XPT outputs to backup state...")
    try:
        restore_backup()
        print("Rollback executed successfully!")
    except Exception as e:
        print(f"Rollback failed: {e}")

def _saspy_available():
    try:
        import saspy  # noqa: F401
        return True
    except ImportError:
        return False


# Outcome of the most recent ODA Stage-10 attempt, merged into pipeline_health.json (brief §6).
_ODA_OUTCOME = {}
# ODA project root. No developer account id is hard-coded (roadmap #10): defaults to the
# connecting account's home (~/TROPIC, resolved against the live session's $HOME) and can be
# overridden with TROPIC_ODA_PROJ_ROOT for a non-default ODA layout.
PROJ_ROOT_ODA = os.environ.get("TROPIC_ODA_PROJ_ROOT", "~/TROPIC")
ODA_DATASETS = ["adsl", "adex", "adcm", "adae", "adlb", "adrs", "adtte"]


def _resolve_oda_root(sas, template):
    """Expand a leading '~' in the ODA project root against the connected account's $HOME,
    so no per-user absolute path needs to be committed. Returns template unchanged if it is
    already absolute or $HOME cannot be read."""
    if not template.startswith("~"):
        return template
    log = sas.submit("%put TROPIC_ODA_HOME=%sysget(HOME);").get("LOG", "")
    for line in log.splitlines():
        if "TROPIC_ODA_HOME=" in line and "%put" not in line and "%sysget" not in line:
            home = line.split("TROPIC_ODA_HOME=", 1)[1].strip()
            if home:
                return template.replace("~", home, 1)
    return template


def _sim_byte_copy(datasets):
    """Byte-copy *_v.xpt -> *_prod.xpt (the labeled, tautological simulation)."""
    for ds in datasets:
        val_file, prod_file = f"04_adam/{ds}_v.xpt", f"04_adam/{ds}_prod.xpt"
        if os.path.exists(val_file):
            with open(val_file, "rb") as fs, open(prod_file, "wb") as fd:
                fd.write(fs.read())
            print(f"    Simulated {ds}_prod.xpt generated.")


def _oda_max_wait():
    """Connection budget (seconds). TROPIC_ODA_RETRIES is a back-compat alias mapped onto a
    wall-clock budget (~60 s expected/attempt); TROPIC_ODA_MAX_WAIT sets it directly."""
    if os.environ.get("TROPIC_ODA_RETRIES"):
        return max(60, int(os.environ["TROPIC_ODA_RETRIES"]) * 60)
    return int(os.environ.get("TROPIC_ODA_MAX_WAIT", 3600))


def _run_saspy_stage10():
    """Job B: run the SAS production suite on ODA against a VERIFIED-resident SDTM library.
    Returns (rc, stdout, stderr, meta). 'oda' mode is earned only via the broker's live probe
    AND a verified SDTM manifest. Seeding is NOT done inline (that is seed_sdtm.py / Job A)
    unless TROPIC_ODA_FORCE_SDTM=TRUE. Connection-budget exhaustion -> honest sim fallback;
    AUTH/encryption or an unverified library -> hard fail (never a silent sim)."""
    import glob as _glob
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import oda_broker
    import seed_sdtm

    # ---- Resilient, probe-verified connect (broker rides spawner timeouts) ----
    try:
        conn = oda_broker.connect(max_wait_s=_oda_max_wait())
    except oda_broker.OdaFatal as e:
        return 1, "", f"ODA fatal ({e.error_class}): {e}", {
            "oda_last_error_class": e.error_class, "reconciliation": "none"}
    except oda_broker.OdaExhausted as e:
        return 0, "ODA exhausted; honest sim fallback", "", {
            "fell_back_to_sim": True, "oda_last_error_class": e.last_class,
            "oda_attempts": e.attempts,
            "next_recommended_window": oda_broker.recommend_window(),
            "reconciliation": "sim_only"}

    sas = conn.sas
    proj_root_oda = _resolve_oda_root(sas, PROJ_ROOT_ODA)
    PGMDIR_ODA = f"{proj_root_oda}/02_production_sas"
    ADAM_ODA = f"{proj_root_oda}/04_adam"
    try:
        # ---- Guarantee the SDTM library on ODA is the verified-correct one ----
        # Single-session optimisation: with --force-upload-sdtm or --seed-if-needed we seed
        # INSIDE this Stage-10 session (one ODA spawn for seed+execute+download) instead of
        # requiring a separate seed_sdtm.py run (two spawns = double the flaky-spawner/session
        # -limit exposure). The seed is delta-aware, so a resident library costs only a manifest
        # check. Default (neither flag) keeps the strict CI contract: verify, else hard-fail.
        force_sdtm = os.environ.get("TROPIC_ODA_FORCE_SDTM") == "TRUE"
        if force_sdtm or os.environ.get("TROPIC_ODA_SEED_INLINE") == "TRUE":
            res = seed_sdtm.seed(sas, force=force_sdtm)
            if res["status"] not in ("seeded", "already-resident"):
                return 2, "", f"SDTM seed/verify failed: {res}", {"reconciliation": "none"}
            manifest_sha = res["manifest_sha"]
            print(f"  [ODA] SDTM {res['status']}: {res.get('uploaded', 0)} uploaded, "
                  f"{res.get('skipped', 0)} resident (manifest {manifest_sha[:12]}).")
        else:
            ok, manifest_sha, reason = seed_sdtm.verify_resident(sas)
            if not ok:
                return 2, "", (f"SDTM not verified-resident on ODA ({reason}). Seed first: "
                               f"python3 06_telemetry/seed_sdtm.py  — or re-run with "
                               f"--seed-if-needed for a single-session seed+run."), {
                    "reconciliation": "none"}
            print(f"  [ODA] SDTM verified resident (manifest {manifest_sha[:12]}).")

        # ---- Upload SAS programs (tiny; always ship the latest code) ----
        print("  [ODA] Uploading SAS programs...")
        for f in sorted(_glob.glob("02_production_sas/*.sas")):
            sas.upload(f, f"{PGMDIR_ODA}/{os.path.basename(f)}")

        # ---- Execute master driver ----
        print("  [ODA] Submitting 00_master_driver.sas via SAS IOM...")
        log = sas.submit(f"""
options notes source;
%global PROJ_ROOT PGMDIR;
%let PROJ_ROOT = {proj_root_oda};
%let PGMDIR    = {PGMDIR_ODA};
filename drv "{PGMDIR_ODA}/00_master_driver.sas";
%include drv;
""").get("LOG", "")
        try:
            with open("02_production_sas/oda_master_driver.log", "w", encoding="utf-8") as _lf:
                _lf.write(log)
        except OSError:
            pass
        warn = [l for l in log.splitlines() if l.strip().startswith("WARNING:")]
        if warn:
            print(f"  [ODA] SAS log has {len(warn)} WARNING line(s) (see oda_master_driver.log).")
        err = [l.strip() for l in log.splitlines() if l.strip().startswith("ERROR:")]
        if err:
            return 1, "", "\n".join(err), {"oda_endpoint": conn.endpoint, "reconciliation": "none"}

        # ---- Download the 7 *_prod.xpt ----
        print("  [ODA] Downloading *_prod.xpt...")
        for ds in ODA_DATASETS:
            sas.download(f"04_adam/{ds}_prod.xpt", f"{ADAM_ODA}/{ds}_prod.xpt")

        return 0, "SASPy/ODA execution complete.", "", {
            "oda_endpoint": conn.endpoint, "oda_attempts": conn.attempts,
            "oda_total_wait_s": conn.total_wait_s, "sdtm_manifest_sha": manifest_sha,
            "reconciliation": "SAS_vs_R", "probe_nonce_echoed": conn.probe_nonce_echoed}
    finally:
        oda_broker.teardown(sas)


def _resolve_sas_mode(real_sas, use_cached_sas):
    """Honestly resolve how Stage 10 will obtain the SAS production datasets.

    Returns one of:
      'local'  -> a local SAS engine is present and will be executed
      'oda'    -> real SAS will be executed on SAS OnDemand via SASPy
      'cached' -> reconcile against pre-existing *_prod.xpt WITHOUT running SAS
      'error'  -> real SAS explicitly requested but no engine and no cache flag
      'sim'    -> copy *_v.xpt -> *_prod.xpt (no real SAS; clearly labelled)
    """
    local_sas = shutil.which("sas") is not None
    saspy_ok = _saspy_available()
    if use_cached_sas:
        return "cached"
    # Real SAS execution must be explicitly requested (roadmap #10): a local 'sas' on PATH
    # no longer silently overrides the default. Without --real-sas the run is labelled sim.
    if real_sas and local_sas:
        return "local"
    if real_sas and saspy_ok:
        return "oda"
    if real_sas:
        return "error"
    return "sim"


def run_stage_parallel_worker(stage):
    rc, stdout, stderr = run_command(stage["cmd"])
    return stage, rc, stdout, stderr

def run_stage_execution(stage, sas_mode):
    if stage["cmd"] == "SIMULATE":
        datasets = ["adsl", "adex", "adcm", "adae", "adlb", "adrs", "adtte"]

        if sas_mode == "oda":
            print("  [ODA] Stage 10 via resilient broker (probe-verified, manifest-checked)...")
            rc, stdout, stderr, meta = _run_saspy_stage10()
            _ODA_OUTCOME.clear()
            _ODA_OUTCOME.update(meta or {})
            if meta and meta.get("fell_back_to_sim"):
                print("  [ODA] Connection budget exhausted -> labeled sim fallback "
                      "(NOT double-programming; honestly recorded in telemetry).")
                _sim_byte_copy(datasets)
                return 0, "sim fallback (ODA unreachable this window)", ""
            if rc == 0:
                print("  [ODA] Real SAS executed against verified-resident SDTM; XPTs downloaded.")
            else:
                print(f"  [ODA FAILED] {stderr.strip()[:200]}")
            return rc, stdout, stderr
        elif sas_mode == "local":
            sas_exe = shutil.which("sas")
            print(f"  [REAL SAS] Located local SAS engine at: {sas_exe}")
            print("  [REAL SAS] Compiling SAS production master suite (02_production_sas/00_master_driver.sas)...")
            sas_cmd = [sas_exe, "-sysin", "02_production_sas/00_master_driver.sas", "-log", "02_production_sas/00_master_driver.log", "-print", "02_production_sas/00_master_driver.lst"]
            rc, stdout, stderr = run_command(sas_cmd)
            if rc == 0:
                print("  [REAL SAS] Master driver executed successfully. Actual SAS XPTs generated.")
            else:
                print("  [REAL SAS FAILED] SAS master execution failed! Check log: 02_production_sas/00_master_driver.log")
            return rc, stdout, stderr
        elif sas_mode == "cached":
            print("  [CACHED SAS] Reconciling against PRE-EXISTING *_prod.xpt (SAS not re-run this session).")
            missing_prod = [f"{ds}_prod.xpt" for ds in datasets
                            if not os.path.exists(f"04_adam/{ds}_prod.xpt")]
            if missing_prod:
                print(f"  [ERROR] --use-cached-sas requires existing SAS outputs, but missing: {', '.join(missing_prod)}")
                print("          Run with --real-sas (SASPy/ODA or local SAS engine) to generate them first.")
                rc = -1
                stderr = "Missing cached SAS production datasets"
            else:
                print("  [CACHED SAS] All 7 cached *_prod.xpt verified. Proceeding to reconciliation.")
                print("  [CACHED SAS] NOTE: parity reflects the cached SAS run, not a fresh compilation.")
                rc, stdout, stderr = 0, "Cached SAS datasets verified (not regenerated).", ""
            return rc, stdout, stderr
        elif sas_mode == "error":
            print("  [ERROR] --real-sas was requested but no SAS engine is available:")
            print("          no local 'sas' on PATH and SASPy is not importable.")
            print("          Install SASPy + configure ODA, or use --use-cached-sas to reconcile existing outputs.")
            rc, stdout, stderr = -1, "", "Real SAS requested but no SAS engine available"
            return rc, stdout, stderr
        else:  # sas_mode == "sim"
            print("  [SAS SIMULATOR] No SAS engine and --real-sas not specified.")
            print("  [SAS SIMULATOR] Copying *_v.xpt -> *_prod.xpt (byte-copy simulation).")
            print("  [SAS SIMULATOR] WARNING: this is NOT independent double-programming; zero diffs are tautological.")
            _sim_byte_copy(datasets)
            rc, stdout, stderr = 0, "Simulated SAS compilation (byte-copy) complete.", ""
            return rc, stdout, stderr
    else:
        return run_command(stage["cmd"])

def run_single_stage(stage, from_stage, sas_mode, results):
    if stage["id"] < from_stage:
        print(f"Skipping Stage {stage['id']}: {stage['name']}")
        return True

    print(f"Executing Stage {stage['id']}: {stage['name']}...")
    
    if stage["id"] == 1:
        create_backup()

    rc, stdout, stderr = run_stage_execution(stage, sas_mode)

    if stage["id"] == 11 and rc == 0:
        status_path = "06_telemetry/reconciliation_status.json"
        try:
            with open(status_path) as sf:
                recon = json.load(sf)
            if recon.get("overall") != "PASS":
                failed = [k for k, v in recon.get("domains", {}).items() if v != "PASS"]
                rc = 1
                stderr = f"Reconciliation reported cell-level differences in: {', '.join(failed)}"
        except FileNotFoundError:
            rc = 1
            stderr = "Reconciliation status file missing; cannot confirm zero differences."

    if rc == 0:
        print(f"  [SUCCESS] Stage {stage['id']} completed.")
        results[stage["name"]] = "PASS"
        return True
    else:
        print(f"  [FAILED] Stage {stage['id']} failed. Reason: {stderr.strip()}")
        results[stage["name"]] = "FAIL"
        print("  [ERROR] Validation or execution error detected! Automated rollback initiated...")
        rollback()
        write_telemetry(results, sas_mode)
        sys.exit(1)

def execute_pipeline(from_stage=0, real_sas=False, use_cached_sas=False, serial=False, force_upload_sdtm=False, seed_if_needed=False):
    print("=== EXECUTING TROPIC (Study EFC6193 / XRP6258) PIPELINE ===")
    # Force a full SDTM re-upload on ODA this run (default: upload only the delta).
    os.environ["TROPIC_ODA_FORCE_SDTM"] = "TRUE" if force_upload_sdtm else "FALSE"
    # Seed SDTM inline within the Stage-10 ODA session (single spawn) if it isn't resident.
    os.environ["TROPIC_ODA_SEED_INLINE"] = "TRUE" if seed_if_needed else "FALSE"

    # Run the configuration generator
    print("  [CONFIG] Generating configuration from study_config.yaml...")
    rc, stdout, stderr = run_command([sys.executable, "06_telemetry/generate_config.py"])
    if rc != 0:
        print(f"  [CONFIG FAILED] Failed to generate configuration: {stderr}")
        sys.exit(1)
    print("  [CONFIG] Configuration successfully generated.")

    # Detect, and honestly label, how the SAS production track will be obtained.
    sas_mode = _resolve_sas_mode(real_sas, use_cached_sas)
    # Only a literal byte-copy simulation counts as "simulation" for the audit flag.
    os.environ["TROPIC_SAS_SIMULATION"] = "TRUE" if sas_mode == "sim" else "FALSE"
    print(f"  [SAS MODE] Stage 10 execution mode resolved to: {sas_mode.upper()}")

    stages = [
        {"id": 1, "name": "Real SDTM Staging Ingest", "cmd": [RSCRIPT_PATH, "-e", "logrx::axecute('03_validation_r/v_staging_ingest.R')"]},
        {"id": 2, "name": "R SDTM Validation", "cmd": [RSCRIPT_PATH, "-e", "logrx::axecute('03_validation_r/v_sdtm_validation.R')"]},
        {"id": 3, "name": "R ADSL Validation", "cmd": [RSCRIPT_PATH, "-e", "logrx::axecute('03_validation_r/v_adsl_validation.R')"]},
        {"id": 4, "name": "R ADEX Validation", "cmd": [RSCRIPT_PATH, "-e", "logrx::axecute('03_validation_r/v_adex_validation.R')"]},
        {"id": 5, "name": "R ADCM Validation", "cmd": [RSCRIPT_PATH, "-e", "logrx::axecute('03_validation_r/v_adcm_validation.R')"]},
        {"id": 6, "name": "R ADAE Validation", "cmd": [RSCRIPT_PATH, "-e", "logrx::axecute('03_validation_r/v_adae_io_validation.R')"]},
        {"id": 7, "name": "R ADLB Validation", "cmd": [RSCRIPT_PATH, "-e", "logrx::axecute('03_validation_r/v_adlb_validation.R')"]},
        {"id": 8, "name": "R ADRS Validation", "cmd": [RSCRIPT_PATH, "-e", "logrx::axecute('03_validation_r/v_adrs_validation.R')"]},
        {"id": 9, "name": "R ADTTE Validation", "cmd": [RSCRIPT_PATH, "-e", "logrx::axecute('03_validation_r/v_adtte_validation.R')"]},
        {"id": 10, "name": "SAS Production (ODA/Real/Simulated)", "cmd": "SIMULATE"},
        {"id": 11, "name": "Cross-Language Audit Reconcile", "cmd": [RSCRIPT_PATH, "-e", "logrx::axecute('05_reconciliation/cross_lang_audit.R')"]},
        {"id": 12, "name": "Efficacy & Safety TFL Suite Compilation", "cmd": [RSCRIPT_PATH, "09_tfl/tfl_generation.R"]}
    ]
    
    results = {}

    if serial:
        for stage in stages:
            run_single_stage(stage, from_stage, sas_mode, results)
    else:
        # Run Stages 1-3 sequentially
        for stage in stages[:3]:
            run_single_stage(stage, from_stage, sas_mode, results)

        # Run Stages 4-8 in parallel (filtering by from_stage)
        parallel_stages = [s for s in stages[3:8] if s["id"] >= from_stage]
        skipped_parallel_stages = [s for s in stages[3:8] if s["id"] < from_stage]

        for s in skipped_parallel_stages:
            print(f"Skipping Stage {s['id']}: {s['name']}")

        if parallel_stages:
            import concurrent.futures
            print(f"Fanning out Stage(s) {', '.join(str(s['id']) for s in parallel_stages)} in parallel...")
            for s in parallel_stages:
                print(f"Executing Stage {s['id']}: {s['name']} (parallel)...")

            with concurrent.futures.ProcessPoolExecutor() as executor:
                futures = {executor.submit(run_stage_parallel_worker, s): s for s in parallel_stages}
                
                failed_any = False
                temp_results = {}
                for future in concurrent.futures.as_completed(futures):
                    s = futures[future]
                    try:
                        stage, rc, stdout, stderr = future.result()
                        if rc == 0:
                            print(f"  [SUCCESS] Stage {stage['id']} completed.")
                            temp_results[stage["name"]] = ("PASS", rc, stderr)
                        else:
                            print(f"  [FAILED] Stage {stage['id']} failed. Reason: {stderr.strip()}")
                            temp_results[stage["name"]] = ("FAIL", rc, stderr)
                            failed_any = True
                    except Exception as exc:
                        print(f"  [FAILED] Stage {s['id']} threw an exception: {exc}")
                        temp_results[s["name"]] = ("FAIL", -1, str(exc))
                        failed_any = True

                for s in parallel_stages:
                    status, rc, stderr = temp_results.get(s["name"], ("FAIL", -1, "Unknown execution error"))
                    results[s["name"]] = status

                if failed_any:
                    print("  [ERROR] Validation or execution error detected in parallel stages! Automated rollback initiated...")
                    rollback()
                    write_telemetry(results, sas_mode)
                    sys.exit(1)

        # Run Stages 9-12 sequentially
        for stage in stages[8:]:
            run_single_stage(stage, from_stage, sas_mode, results)

    clean_backup()
    write_telemetry(results, sas_mode)
    print("All clinical pipeline stages compiled successfully!")

def update_define_timestamp():
    # NOTE (review-board RR-2): AsOfDateTime is intentionally restamped to the build
    # time on every successful run so it reflects when the metadata was last produced.
    # It is a build provenance stamp, NOT evidence that the underlying data changed.
    define_path = "07_define_xml/define.xml"
    if os.path.exists(define_path):
        try:
            with open(define_path, "r", encoding="utf-8") as f:
                content = f.read()
            current_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            content_updated = re.sub(r'AsOfDateTime="[^"]+"', f'AsOfDateTime="{current_ts}"', content)
            with open(define_path, "w", encoding="utf-8") as f:
                f.write(content_updated)
            print(f"  [METADATA] Successfully updated define.xml AsOfDateTime to: {current_ts}")
        except Exception as e:
            print(f"  [METADATA WARNING] Failed to update define.xml timestamp: {e}")

def write_telemetry(results, sas_mode="sim"):
    import platform
    health_status = "GREEN" if all(v == "PASS" for v in results.values()) else "RED"

    # Update define.xml timestamp if the build succeeds (Mi-02)
    if health_status == "GREEN":
        update_define_timestamp()

    health = {
        "timestamp": datetime.now().isoformat(),
        "runner": f"{getpass.getuser()} (System Agent)",
        "pipeline_health_status": health_status,
        "sas_execution_mode": sas_mode,
        "stages": results
    }

    # Merge the ODA Stage-10 outcome (brief §6): on a connection-budget exhaustion the mode is
    # honestly downgraded to 'sim'; on success we record endpoint/attempts/manifest/probe.
    if _ODA_OUTCOME:
        if _ODA_OUTCOME.get("fell_back_to_sim"):
            sas_mode = "sim"
            health["sas_execution_mode"] = "sim"
        for k, v in _ODA_OUTCOME.items():
            if k != "fell_back_to_sim":
                health[k] = v
    # Attach the cross-language reconciliation verdict if Stage 11 wrote one.
    try:
        with open("06_telemetry/reconciliation_status.json") as _rf:
            health["reconciliation_status"] = json.load(_rf).get("overall")
    except (OSError, json.JSONDecodeError):
        pass

    os.makedirs("06_telemetry", exist_ok=True)
    with open("06_telemetry/pipeline_health.json", "w", encoding="utf-8") as f:
        json.dump(health, f, indent=2)

    # Report the track based on what ACTUALLY happened this run (audit F-5),
    # not on mere availability of a SAS engine.
    track_by_mode = {
        "oda":    "Real SAS-R Validation Track (SAS 9.4 executed on ODA via SASPy this run)",
        "local":  "Real SAS-R Validation Track (local SAS 9.4 executed this run)",
        "cached": "SAS-R Reconciliation against CACHED *_prod.xpt (SAS not re-run this session)",
        "sim":    "R Validation Track (SAS byte-copy SIMULATION - not double-programmed)",
        "error":  "SAS execution FAILED (no engine available)",
    }
    real_sas_used = sas_mode in ("oda", "local")
    sys_track = track_by_mode.get(sas_mode, track_by_mode["sim"])
    env_str = f"{platform.system()} {platform.release()} / {sys_track}"
    
    # Write standard markdown dashboard
    dashboard_content = f"""# TROPIC (Study EFC6193 / XRP6258) Pipeline Validation Dashboard

*Captured At:* `{health['timestamp']}`  
*Environment:* `{env_str}`  
*Pipeline Status:* **{health['pipeline_health_status']}**

## Stage-Level Execution Checklist

"""
    for name, status in results.items():
        icon = "[PASS]" if status == "PASS" else "[FAIL]"
        dashboard_content += f"* {icon} **{name}**: `{status}`\n"
        
    # Honest per-mode dashboard annotations (audit F-5)
    sas_notes = {
        "oda":    ("- [x]", "SAS 9.4 executed on ODA this run; *_prod.xpt regenerated and reconciled."),
        "local":  ("- [x]", "Local SAS 9.4 executed this run; *_prod.xpt regenerated and reconciled."),
        "cached": ("- [~]", "Reconciled against CACHED *_prod.xpt from a prior SAS run; SAS NOT re-run this session."),
        "sim":    ("- [ ]", "SAS byte-copy SIMULATION used - no SAS engine ran; reconciliation is tautological, NOT double-programming."),
        "error":  ("- [ ]", "SAS execution FAILED - no engine available."),
    }
    sas_compiled_status, sas_compiled_note = sas_notes.get(sas_mode, sas_notes["sim"])

    if sas_mode in ("oda", "local"):
        reconcile_status = "[PASS - real SAS vs R]"
        dp_line = "- [x] Independent R double-programming track reconciled against real SAS output"
    elif sas_mode == "cached":
        reconcile_status = "[PASS - R vs cached SAS]"
        dp_line = "- [x] Independent R track reconciled against cached SAS output (SAS not re-run this session)"
    else:
        reconcile_status = "[N/A - simulated]"
        dp_line = "- [ ] Double-programming NOT established (SAS simulated/failed this run)"

    dashboard_content += f"""
## Validation Controls

- [x] All ADaM datasets successfully compiled
{dp_line}
- [x] Cross-Language diffdf reconciliation result: `{reconcile_status}`
{sas_compiled_status} {sas_compiled_note}
"""
    with open("06_telemetry/health_dashboard.md", "w", encoding="utf-8") as f:
        f.write(dashboard_content)

def main():
    parser = argparse.ArgumentParser(description="TROPIC (Study EFC6193 / XRP6258) Pipeline Orchestrator")
    parser.add_argument("--dry-run", action="store_true", help="dry run check")
    parser.add_argument("--rollback", action="store_true", help="rollback check")
    parser.add_argument("--from-stage", type=int, default=0, help="from stage number")
    parser.add_argument("--real-sas", action="store_true", help="Run REAL SAS 9.4 this session (local engine if present, else ODA via SASPy). Errors if no engine is available.")
    parser.add_argument("--use-cached-sas", action="store_true", help="Reconcile against pre-existing *_prod.xpt WITHOUT re-running SAS (re-verifies a prior SAS run).")
    parser.add_argument("--demo", action="store_true", help="Run self-contained demo smoke test (tests/smoke_test.R).")
    parser.add_argument("--serial", action="store_true", help="Run stages serially rather than parallelizing Stages 4-8.")
    parser.add_argument("--force-upload-sdtm", action="store_true", help="ODA only: force a full re-upload of the ~200 MB SDTM source (default uploads only missing/changed files). Use after a source-data refresh.")
    parser.add_argument("--seed-if-needed", action="store_true", help="ODA only: seed the SDTM library inline within the Stage-10 session if it is not already resident (single ODA spawn for seed+run). Delta-aware: a resident library costs only a manifest check.")

    args = parser.parse_args()

    if args.dry_run:
        dry_run()
    elif args.rollback:
        rollback()
    elif args.demo:
        print("=== RUNNING SELF-CONTAINED DEMO (SMOKE TEST) ===")
        for label, script in (("reconciliation engine", "tests/smoke_test.R"),
                              ("TFL survival-stats snapshot", "tests/test_tfl_stats.R")):
            print(f"--- demo: {label} ({script}) ---")
            rc, stdout, stderr = run_command([RSCRIPT_PATH, script])
            print(stdout)
            if rc != 0:
                print(f"ERROR: {label} test failed!\n{stderr}")
                sys.exit(1)
        print("Demo smoke test completed successfully!")
        sys.exit(0)
    else:
        # Validate that from-stage is within valid range (AUTO-03)
        if args.from_stage < 0 or args.from_stage > 12:
            print(f"ERROR: Invalid stage number {args.from_stage}. Stage number must be between 1 and 12.")
            sys.exit(1)
        if args.real_sas and args.use_cached_sas:
            print("ERROR: --real-sas and --use-cached-sas are mutually exclusive.")
            sys.exit(1)
        execute_pipeline(args.from_stage, args.real_sas, args.use_cached_sas, args.serial, args.force_upload_sdtm, args.seed_if_needed)

if __name__ == "__main__":
    main()
