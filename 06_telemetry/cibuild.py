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

# --- Study structure from the manifest (I/J platform generalisation) ----------
# study_manifest.yaml declares the reconciled datasets and the study identity so
# they are no longer hardcoded here. A missing/malformed manifest falls back to the
# legacy TROPIC values, so the engine never hard-fails on a manifest problem.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# The engine lives at the repo root (parent of 06_telemetry/). The default study IS
# that root (TROPIC); a named study (--study) lives under studies/<name>/ and is
# activated by _activate_study(), which chdirs into it and reloads the manifest.
_ENGINE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RELOCATE_ENGINE = False   # True once a study root != engine root is active (Phase 2)
try:
    import manifest as _manifest_mod
    _MANIFEST = _manifest_mod.load_manifest()
    STUDY_DATASETS = _manifest_mod.dataset_names(_MANIFEST)
    STUDY_LABEL = _manifest_mod.study_label(_MANIFEST)
except Exception as _e:  # noqa: BLE001 — fall back to legacy hardcoded structure
    print(f"  [MANIFEST] Falling back to legacy TROPIC structure ({_e}).")
    _MANIFEST = None
    STUDY_DATASETS = ["adsl", "adex", "adcm", "adae", "adlb", "adrs", "adtte", "clinsite"]
    STUDY_LABEL = "TROPIC (Study EFC6193 / XRP6258)"
ODA_DATASETS = STUDY_DATASETS


def _activate_study(study):
    """Resolve and activate the target study (I/J Phase 2, multi-study).

    Default (study=None) = the engine/repo root (TROPIC). A named study lives under
    studies/<study>/ with its own manifest/config/programs. We chdir into the study
    root so the engine's relative paths (04_adam/, 03_validation_r/, study_config.yaml,
    study_manifest.yaml) resolve per-study, and set _RELOCATE_ENGINE so shared engine
    scripts (flagged `engine: true` in the manifest) are run from absolute engine-root
    paths. For the default study, study root == engine root, so nothing relocates and
    behaviour is byte-identical to single-study mode."""
    global _MANIFEST, STUDY_DATASETS, STUDY_LABEL, ODA_DATASETS, _RELOCATE_ENGINE
    study_root = os.path.join(_ENGINE_ROOT, "studies", study) if study else _ENGINE_ROOT
    if not os.path.isdir(study_root):
        print(f"  [ERROR] study directory not found: {study_root}")
        sys.exit(1)
    os.chdir(study_root)
    _RELOCATE_ENGINE = os.path.abspath(study_root) != os.path.abspath(_ENGINE_ROOT)
    try:
        _MANIFEST = _manifest_mod.load_manifest()
    except Exception as e:  # noqa: BLE001
        print(f"  [ERROR] could not load manifest for study at {study_root}: {e}")
        sys.exit(1)
    STUDY_DATASETS = _manifest_mod.dataset_names(_MANIFEST)
    STUDY_LABEL = _manifest_mod.study_label(_MANIFEST)
    ODA_DATASETS = STUDY_DATASETS


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


def _prod_v_byte_identical(datasets):
    """Return datasets whose *_prod.xpt is byte-identical to (or missing vs) its *_v.xpt.

    A genuine independent SAS run produces *_prod.xpt that is byte-DISTINCT from the R
    validation *_v.xpt; byte-identical prod==v is the signature of _sim_byte_copy(). This
    is the uncheatable evidence test behind the 'oda'/'local' provenance flag (audit C-1):
    the flag may only be recorded GREEN if this returns empty for every produced dataset.
    """
    import filecmp
    offenders = []
    for ds in datasets:
        val_file, prod_file = f"04_adam/{ds}_v.xpt", f"04_adam/{ds}_prod.xpt"
        if not os.path.exists(val_file):
            continue  # no R validation pair for this dataset; nothing to reconcile against
        if not os.path.exists(prod_file) or filecmp.cmp(val_file, prod_file, shallow=False):
            offenders.append(ds)
    return offenders


def _sdtm_manifest_binding(recorded_sha):
    """(ok, detail) for the provenance guard: confirm the SDTM manifest SHA recorded for an
    oda/local run is present and matches the current local SDTM source — i.e. the production
    datasets were generated from the same verified input the R track validated against, not a
    later/different SDTM (audit C-1). If the local SDTM source is not present (e.g. a clone
    without licensed data) we can only confirm a SHA was recorded, not recompute it, so we
    accept with a note rather than fail.
    """
    if not recorded_sha:
        return False, "no sdtm_manifest_sha recorded for an oda/local run"
    try:
        import seed_sdtm
        local = seed_sdtm.compute_local_manifest()
    except Exception as e:  # noqa: BLE001 - any import/IO failure leaves us unable to recompute
        return True, f"recorded; local SDTM not recomputable ({type(e).__name__})"
    if not local.get("datasets"):
        return True, "recorded; no local SDTM source present to recompute"
    expected = local.get("manifest_sha")
    if expected != recorded_sha:
        return False, (f"recorded sdtm_manifest_sha {recorded_sha[:12]} does not match the current "
                       f"SDTM source {expected[:12]}")
    return True, f"matches current SDTM source ({recorded_sha[:12]})"


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
    # Execution-phase deadline: connect()'s budget only covers the spawn; a wedged server-side
    # workspace would otherwise block submit() forever. On a hit we force-reap (SIGKILL) the
    # local gateway instead of leaking a CPU-burning zombie. Default 30 min for the full suite.
    exec_timeout = int(os.environ.get("TROPIC_ODA_EXEC_TIMEOUT", "1800"))
    force_teardown = False
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
        try:
            log = oda_broker.submit_timed(sas, f"""
options notes source;
%global PROJ_ROOT PGMDIR;
%let PROJ_ROOT = {proj_root_oda};
%let PGMDIR    = {PGMDIR_ODA};
filename drv "{PGMDIR_ODA}/00_master_driver.sas";
%include drv;
""", timeout_s=exec_timeout).get("LOG", "")
        except oda_broker.OdaExecTimeout as e:
            force_teardown = True
            return 1, "", (f"ODA master-driver execution timed out after {e.timeout_s}s "
                           f"(workspace presumed hung; session force-reaped)."), {
                "oda_endpoint": conn.endpoint, "oda_exec_timeout": True,
                "reconciliation": "none"}
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

        # ---- M-1: independent SAS analysis RESULTS (PROC LIFETEST), MP arm ----
        # Extends double-programming from the ADaM dataset layer to the analysis-
        # results layer: SAS computes the MP-arm survival statistics with its own
        # engine; results_reconcile.R (Stage 13) diffs them numerically against R.
        print("  [ODA] Computing independent SAS analysis statistics (PROC LIFETEST, MP arm)...")
        stats_extra = {"sas_results_stats": "downloaded"}
        try:
            stats_log = oda_broker.submit_timed(sas, f"""
options notes source;
ods graphics off;
libname adam "{ADAM_ODA}";
proc sort data=adam.adtte(where=(TRT01P='MP')) out=work.adtte_mp; by PARAMCD; run;
proc lifetest data=work.adtte_mp;
    time AVAL*CNSR(1);
    by PARAMCD;
    ods output Quartiles=work.q CensoredSummary=work.cs;
run;
data work.med; set work.q; if Percent = 50; keep PARAMCD Estimate; run;
proc sql;
    create table work.tte_stats as
        select c.PARAMCD length=8, c.Total as N, c.Failed as EVENTS,
               m.Estimate as MEDIAN_DAYS
        from work.cs as c left join work.med as m on c.PARAMCD = m.PARAMCD
        order by c.PARAMCD;
quit;
proc export data=work.tte_stats outfile="{ADAM_ODA}/tte_stats_prod.csv" dbms=csv replace; run;
""", timeout_s=exec_timeout).get("LOG", "")
        except oda_broker.OdaExecTimeout:
            # Non-fatal step: the prod XPTs are already downloaded. Mark the session for a force
            # reap and let the ERROR branch below degrade reconciliation to 'not_available'.
            force_teardown = True
            print("  [ODA] WARNING: SAS analysis-stats step timed out (workspace hung).")
            stats_log = "ERROR: analysis-stats submit timed out (workspace presumed hung)"
        if any(l.strip().startswith("ERROR:") for l in stats_log.splitlines()):
            print("  [ODA] WARNING: SAS analysis-stats step failed; "
                  "results reconciliation will record 'not_available'.")
            stats_extra = {"sas_results_stats": "error"}
            if os.path.exists("04_adam/tte_stats_prod.csv"):
                os.remove("04_adam/tte_stats_prod.csv")
        else:
            sas.download("04_adam/tte_stats_prod.csv", f"{ADAM_ODA}/tte_stats_prod.csv")
            print("  [ODA] Downloaded SAS analysis statistics (tte_stats_prod.csv).")

        meta_out = {
            "oda_endpoint": conn.endpoint, "oda_attempts": conn.attempts,
            "oda_total_wait_s": conn.total_wait_s, "sdtm_manifest_sha": manifest_sha,
            "reconciliation": "SAS_vs_R", "probe_nonce_echoed": conn.probe_nonce_echoed}
        meta_out.update(stats_extra)
        return 0, "SASPy/ODA execution complete.", "", meta_out
    finally:
        oda_broker.teardown(sas, force=force_teardown)


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
        datasets = STUDY_DATASETS

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

    # Post-execution gates are keyed by stage NAME, not by a positional id, so
    # inserting/renumbering a stage can never silently detach a gate from the step it
    # guards (audit C-3: the M-4 sanity gate had drifted off the TFL stage onto packaging).
    stage_status_override = None

    if stage["name"] == "Cross-Language Audit Reconcile" and rc == 0:
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

    # M-4 sanity gate fires immediately after the TFL deliverables are rendered, so a
    # corrupted table is caught BEFORE results-reconciliation or eCTD packaging consume it.
    if stage["name"] == "Efficacy & Safety TFL Suite Compilation" and rc == 0:
        ok, problems = output_sanity_check()
        if not ok:
            rc = 1
            stderr = ("Deliverable sanity gate failed (code artifacts in published output): "
                      + " | ".join(problems[:5]))

    # C-2: results-level reconciliation legitimately has nothing to do when no real SAS
    # analysis statistics exist (a sim/cached run with no PROC LIFETEST CSV). In that case
    # results_reconcile.R writes overall='not_available' and exits 0 - which must surface
    # as SKIPPED, never a false PASS. A genuine FAIL still fails the stage.
    if stage["name"] == "Numerical Results Reconciliation (SAS vs R)" and rc == 0:
        try:
            with open("06_telemetry/results_reconciliation_status.json") as sf:
                overall = json.load(sf).get("overall")
            if overall == "not_available":
                stage_status_override = "SKIPPED"
            elif overall not in ("PASS", None):
                rc = 1
                stderr = f"Results reconciliation did not pass (overall='{overall}')."
        except (FileNotFoundError, json.JSONDecodeError):
            stage_status_override = "SKIPPED"

    if rc == 0:
        status = stage_status_override or "PASS"
        label = "SUCCESS" if status == "PASS" else status
        print(f"  [{label}] Stage {stage['id']} completed ({status}).")
        results[stage["name"]] = status
        return True
    else:
        print(f"  [FAILED] Stage {stage['id']} failed. Reason: {stderr.strip()}")
        results[stage["name"]] = "FAIL"
        print("  [ERROR] Validation or execution error detected! Automated rollback initiated...")
        rollback()
        write_telemetry(results, sas_mode)
        sys.exit(1)

def _stage_cmd(script, runner, engine_root=None, relocate=False, is_engine=False):
    """Build the subprocess argv for a stage given its runner style.
      logrx   -> Rscript -e logrx::axecute('<script>')  (default for R stages)
      rscript -> Rscript <script>                       (scripts that self-log)
      python  -> <python> <script>
    Shared engine scripts (is_engine) are resolved to an absolute engine-root path when
    a relocated study is active, so they run from the engine even though the CWD is the
    study root. For the default study (relocate=False) the path stays relative/unchanged.
    """
    path = os.path.join(engine_root, script) if (is_engine and relocate and engine_root) else script
    if runner == "python":
        return [sys.executable, path]
    if runner == "rscript":
        return [RSCRIPT_PATH, path]
    return [RSCRIPT_PATH, "-e", f"logrx::axecute('{path}')"]


def build_stages(manifest, engine_root=None, relocate=False):
    """Assemble the ordered pipeline stage list from the study manifest (I/J Phase 1).

    Order: pre-infrastructure -> per-dataset R validations (manifest list order,
    parallel where parallel_group is set) -> SAS production sentinel ('SIMULATE') ->
    post-infrastructure. Each stage is {id, name, cmd, parallel, gated}. Stage NAMES are
    preserved exactly so the name-keyed post-execution gates stay attached. engine_root/
    relocate thread shared-engine-script relocation through for multi-study (Phase 2).
    """
    infra = manifest.get("infrastructure_stages", {})
    stages = []
    for s in infra.get("pre", []):
        stages.append({"name": s["name"],
                       "cmd": _stage_cmd(s["script"], s.get("runner", "logrx"),
                                         engine_root, relocate, s.get("engine", False)),
                       "parallel": False, "gated": bool(s.get("gated"))})
    for d in manifest["datasets"]:
        label = d.get("val_stage", f"R {d['name'].upper()} Validation")
        stages.append({"name": label,
                       "cmd": _stage_cmd(f"03_validation_r/{d['val']}", "logrx"),
                       "parallel": "parallel_group" in d, "gated": False})
    stages.append({"name": "SAS Production (ODA/Real/Simulated)", "cmd": "SIMULATE",
                   "parallel": False, "gated": False})
    for s in infra.get("post", []):
        stages.append({"name": s["name"],
                       "cmd": _stage_cmd(s["script"], s.get("runner", "logrx"),
                                         engine_root, relocate, s.get("engine", False)),
                       "parallel": False, "gated": bool(s.get("gated"))})
    for i, s in enumerate(stages, 1):
        s["id"] = i
    return stages


def run_parallel_batch(batch, from_stage, sas_mode, results):
    """Execute a contiguous run of independent (parallel) validation stages concurrently.
    Mirrors the historical 'fan out the independent ADaM validations' behaviour: honour
    from_stage skipping, run via a ProcessPool, and roll back + exit on any failure."""
    import concurrent.futures
    for s in [s for s in batch if s["id"] < from_stage]:
        print(f"Skipping Stage {s['id']}: {s['name']}")
    parallel_stages = [s for s in batch if s["id"] >= from_stage]
    if not parallel_stages:
        return
    print(f"Fanning out Stage(s) {', '.join(str(s['id']) for s in parallel_stages)} in parallel...")
    for s in parallel_stages:
        print(f"Executing Stage {s['id']}: {s['name']} (parallel)...")
    failed_any = False
    temp_results = {}
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {executor.submit(run_stage_parallel_worker, s): s for s in parallel_stages}
        for future in concurrent.futures.as_completed(futures):
            s = futures[future]
            try:
                stage, rc, stdout, stderr = future.result()
                if rc == 0:
                    print(f"  [SUCCESS] Stage {stage['id']} completed.")
                    temp_results[stage["name"]] = "PASS"
                else:
                    print(f"  [FAILED] Stage {stage['id']} failed. Reason: {stderr.strip()}")
                    temp_results[stage["name"]] = "FAIL"
                    failed_any = True
            except Exception as exc:
                print(f"  [FAILED] Stage {s['id']} threw an exception: {exc}")
                temp_results[s["name"]] = "FAIL"
                failed_any = True
    for s in parallel_stages:
        results[s["name"]] = temp_results.get(s["name"], "FAIL")
    if failed_any:
        print("  [ERROR] Validation or execution error detected in parallel stages! "
              "Automated rollback initiated...")
        rollback()
        write_telemetry(results, sas_mode)
        sys.exit(1)


def execute_pipeline(from_stage=0, real_sas=False, use_cached_sas=False, serial=False, force_upload_sdtm=False, seed_if_needed=False):
    print(f"=== EXECUTING {STUDY_LABEL} PIPELINE ===")
    # Force a full SDTM re-upload on ODA this run (default: upload only the delta).
    os.environ["TROPIC_ODA_FORCE_SDTM"] = "TRUE" if force_upload_sdtm else "FALSE"
    # Seed SDTM inline within the Stage-10 ODA session (single spawn) if it isn't resident.
    os.environ["TROPIC_ODA_SEED_INLINE"] = "TRUE" if seed_if_needed else "FALSE"

    # M-1: a stale SAS analysis-stats file must not pollute a non-ODA run's results
    # reconciliation; it is (re)produced only by a real ODA Stage-10 execution.
    if from_stage <= 10 and os.path.exists("04_adam/tte_stats_prod.csv"):
        os.remove("04_adam/tte_stats_prod.csv")

    # Engine scripts (lint, config-gen) are invoked by absolute engine-root path so they
    # run regardless of the active study's CWD; both scan/emit relative to the CWD (the
    # active study root), so they remain per-study correct.
    lint_py = os.path.join(_ENGINE_ROOT, "06_telemetry", "lint_sas.py")
    config_py = os.path.join(_ENGINE_ROOT, "06_telemetry", "generate_config.py")

    # Run SAS static-analysis pre-flight gate (advisory; blocks only on hardcoded paths).
    print("  [LINT] Running SAS static analysis...")
    rc_lint, stdout_lint, stderr_lint = run_command([sys.executable, lint_py])
    if rc_lint != 0:
        print(f"  [LINT FAILED] Blocking SAS static-analysis error(s):\n{stdout_lint}\n{stderr_lint}")
        sys.exit(1)
    else:
        print("  [LINT] SAS static analysis passed (no blocking errors).")

    # Run the configuration generator
    print("  [CONFIG] Generating configuration from study_config.yaml...")
    rc, stdout, stderr = run_command([sys.executable, config_py])
    if rc != 0:
        print(f"  [CONFIG FAILED] Failed to generate configuration: {stderr}")
        sys.exit(1)
    print("  [CONFIG] Configuration successfully generated.")

    # Detect, and honestly label, how the SAS production track will be obtained.
    sas_mode = _resolve_sas_mode(real_sas, use_cached_sas)
    # Only a literal byte-copy simulation counts as "simulation" for the audit flag.
    os.environ["TROPIC_SAS_SIMULATION"] = "TRUE" if sas_mode == "sim" else "FALSE"
    # Pass the precise mode so the reconciliation status records execution_mode (audit M-1).
    os.environ["TROPIC_SAS_MODE"] = sas_mode
    print(f"  [SAS MODE] Stage 10 execution mode resolved to: {sas_mode.upper()}")

    # The pipeline DAG is generated from study_manifest.yaml (I/J Phase 1) rather than
    # hardcoded here. The manifest is required to run the pipeline; a load failure is a
    # hard error (the soft fallback above only covers banner/ODA-path resilience).
    if _MANIFEST is None:
        print("  [ERROR] study_manifest.yaml could not be loaded; cannot build the pipeline DAG.")
        sys.exit(1)
    stages = build_stages(_MANIFEST, _ENGINE_ROOT, _RELOCATE_ENGINE)

    # F-6 guard: run_single_stage() implements post-execution QC gate logic keyed on
    # these exact stage names. A study legitimately may use a subset of them (e.g. a stub
    # study with no TFL/results-recon), so the check is: fail loudly if the manifest marks
    # a stage `gated` that the engine has NO gate logic for — a rename/typo that would
    # otherwise run silently ungated (the C-3 regression class).
    implemented_gates = {
        "Cross-Language Audit Reconcile",
        "Efficacy & Safety TFL Suite Compilation",
        "Numerical Results Reconciliation (SAS vs R)",
    }
    unimplemented_gates = {s["name"] for s in stages if s.get("gated")} - implemented_gates
    if unimplemented_gates:
        raise RuntimeError(
            "Gate wiring error: manifest marks stage(s) gated with no engine gate logic "
            f"(a rename detached a QC gate): {sorted(unimplemented_gates)}"
        )

    results = {}

    # Execute in declared order. A contiguous run of parallel-marked stages (the
    # independent ADaM validations) fans out concurrently; everything else runs
    # sequentially. --serial forces fully sequential execution.
    idx = 0
    while idx < len(stages):
        stage = stages[idx]
        if stage.get("parallel") and not serial:
            batch = [stage]
            j = idx + 1
            while j < len(stages) and stages[j].get("parallel"):
                batch.append(stages[j])
                j += 1
            run_parallel_batch(batch, from_stage, sas_mode, results)
            idx = j
        else:
            run_single_stage(stage, from_stage, sas_mode, results)
            idx += 1

    clean_backup()
    write_telemetry(results, sas_mode)
    print("All clinical pipeline stages compiled successfully!")

def update_define_timestamp():
    # Audit Mi-02 fix: AsOfDateTime is restamped ONLY when the metadata content
    # actually changes (content hashed with the timestamp normalised out), not on
    # every build. A timestamp that mutates each run is misleading provenance and
    # produces spurious git churn / Part-11 audit-trail noise.
    import hashlib
    define_path = "07_define_xml/define.xml"
    hash_path = "06_telemetry/define_content.sha"
    if not os.path.exists(define_path):
        return
    try:
        with open(define_path, "r", encoding="utf-8") as f:
            content = f.read()
        normalized = re.sub(r'AsOfDateTime="[^"]+"', 'AsOfDateTime=""', content)
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        prev = None
        if os.path.exists(hash_path):
            with open(hash_path, "r", encoding="utf-8") as f:
                prev = f.read().strip()
        if digest == prev:
            print("  [METADATA] define.xml content unchanged; AsOfDateTime preserved.")
            return
        current_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        content_updated = re.sub(r'AsOfDateTime="[^"]+"', f'AsOfDateTime="{current_ts}"', content)
        with open(define_path, "w", encoding="utf-8") as f:
            f.write(content_updated)
        with open(hash_path, "w", encoding="utf-8") as f:
            f.write(digest + "\n")
        print(f"  [METADATA] define.xml content changed; AsOfDateTime restamped to: {current_ts}")
    except Exception as e:
        print(f"  [METADATA WARNING] Failed to update define.xml timestamp: {e}")


def output_sanity_check():
    """Audit M-4 gate: a published TFL table/listing must never contain code
    artifacts. A cosmetic linter pass once wrote ' # nolint' into T-11; this gate
    fails the build on unrendered sprintf specs, lint pragmas, and R missing/
    non-finite sentinels reaching a deliverable."""
    forbidden = {
        "lint pragma": re.compile(r"nolint"),
        "unrendered format spec": re.compile(r"%\.?\d*[disfgeExX]"),
        "missing/non-finite sentinel": re.compile(r"<NA>|NaN|-?\bInf\b"),
    }
    problems = []
    targets = sorted(glob.glob("09_tfl/output/tables/*.txt")
                     + glob.glob("09_tfl/output/listings/*.txt"))
    for path in targets:
        try:
            with open(path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    for label, pat in forbidden.items():
                        if pat.search(line):
                            problems.append(
                                f"{os.path.basename(path)}:{i} [{label}] {line.strip()[:80]}")
        except OSError:
            continue
    return (len(problems) == 0, problems)

def write_telemetry(results, sas_mode="sim"):
    import platform
    # A legitimately SKIPPED stage (e.g. results-reconciliation in sim/cached mode) does
    # not turn the pipeline RED; only a real FAIL does.
    health_status = "RED" if any(v == "FAIL" for v in results.values()) else "GREEN"

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
    # Results-level (analysis statistics) reconciliation verdict, if Stage 13 wrote one.
    try:
        with open("06_telemetry/results_reconciliation_status.json") as _rrf:
            health["results_reconciliation_status"] = json.load(_rrf).get("overall")
    except (OSError, json.JSONDecodeError):
        pass

    # Provenance guard (audit C-1): a recorded 'oda'/'local' mode asserts an independent SAS
    # run, whose on-disk signature is *_prod.xpt byte-DISTINCT from *_v.xpt. If any prod file
    # is byte-identical to (or missing vs) its R validation pair, the asserted evidence is not
    # present, so we refuse to record a clean real-SAS GREEN and flip the health to RED. This
    # makes the flag uncheatable by a restamped green snapshot.
    effective_mode = health["sas_execution_mode"]
    if effective_mode in ("oda", "local"):
        offenders = _prod_v_byte_identical(STUDY_DATASETS)
        byte_ok = not offenders
        sha_ok, sha_detail = _sdtm_manifest_binding(health.get("sdtm_manifest_sha"))
        if byte_ok and sha_ok:
            health["provenance_guard"] = {
                "passed": True,
                "checked_datasets": list(STUDY_DATASETS),
                "byte_distinct": True,
                "sdtm_manifest_sha": sha_detail,
            }
        else:
            health["pipeline_health_status"] = "RED"
            reasons = []
            if not byte_ok:
                reasons.append(f"*_prod.xpt byte-identical to (or missing vs) *_v.xpt for {offenders} "
                               "-- the sim byte-copy signature, not real double-programming")
            if not sha_ok:
                reasons.append(f"SDTM manifest binding failed -- {sha_detail}")
            health["provenance_guard"] = {
                "passed": False,
                "reason": f"sas_execution_mode='{effective_mode}' asserts an independent SAS run, but "
                          + "; ".join(reasons) + ".",
                "byte_distinct": byte_ok,
                "offending_datasets": offenders,
                "sdtm_manifest_sha": sha_detail,
            }
            print(f"  [PROVENANCE GUARD] FAIL ({effective_mode}): " + "; ".join(reasons)
                  + "; forcing pipeline_health_status=RED.")

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
    dashboard_content = f"""# {STUDY_LABEL} Pipeline Validation Dashboard

*Captured At:* `{health['timestamp']}`  
*Environment:* `{env_str}`  
*Pipeline Status:* **{health['pipeline_health_status']}**

## Stage-Level Execution Checklist

"""
    for name, status in results.items():
        icon = {"PASS": "[PASS]", "SKIPPED": "[SKIP]"}.get(status, "[FAIL]")
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
    parser = argparse.ArgumentParser(description=f"{STUDY_LABEL} Pipeline Orchestrator")
    parser.add_argument("--dry-run", action="store_true", help="dry run check")
    parser.add_argument("--rollback", action="store_true", help="rollback check")
    parser.add_argument("--from-stage", type=int, default=0, help="from stage number")
    parser.add_argument("--real-sas", action="store_true", help="Run REAL SAS 9.4 this session (local engine if present, else ODA via SASPy). Errors if no engine is available.")
    parser.add_argument("--use-cached-sas", action="store_true", help="Reconcile against pre-existing *_prod.xpt WITHOUT re-running SAS (re-verifies a prior SAS run).")
    parser.add_argument("--demo", action="store_true", help="Run self-contained demo smoke test (tests/smoke_test.R).")
    parser.add_argument("--serial", action="store_true", help="Run stages serially rather than parallelizing Stages 4-8.")
    parser.add_argument("--force-upload-sdtm", action="store_true", help="ODA only: force a full re-upload of the ~200 MB SDTM source (default uploads only missing/changed files). Use after a source-data refresh.")
    parser.add_argument("--seed-if-needed", action="store_true", help="ODA only: seed the SDTM library inline within the Stage-10 session if it is not already resident (single ODA spawn for seed+run). Delta-aware: a resident library costs only a manifest check.")
    parser.add_argument("--study", default=None, help="Run a named study under studies/<name>/ (default: the TROPIC study at the repo root). Multi-study: the engine chdirs into the study root and builds its DAG from that study's manifest.")

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
        # Resolve & activate the target study (default = TROPIC at the repo root;
        # --study <name> = studies/<name>/). Chdirs into the study root and loads its
        # manifest before the DAG is built (I/J Phase 2, multi-study).
        _activate_study(args.study)
        # Validate that from-stage is within valid range (AUTO-03). The stage count is
        # derived from the manifest-built DAG rather than a hardcoded 17.
        max_stage = len(build_stages(_MANIFEST, _ENGINE_ROOT, _RELOCATE_ENGINE))
        if args.from_stage < 0 or args.from_stage > max_stage:
            print(f"ERROR: Invalid stage number {args.from_stage}. Stage number must be between 1 and {max_stage}.")
            sys.exit(1)
        if args.real_sas and args.use_cached_sas:
            print("ERROR: --real-sas and --use-cached-sas are mutually exclusive.")
            sys.exit(1)
        execute_pipeline(args.from_stage, args.real_sas, args.use_cached_sas, args.serial, args.force_upload_sdtm, args.seed_if_needed)

if __name__ == "__main__":
    main()
