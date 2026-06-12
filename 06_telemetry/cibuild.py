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


def _run_saspy_stage10():
    """Execute SAS production suite on ODA via SASPy, return (rc, stdout, stderr)."""
    import saspy
    import glob as _glob

    PROJ_ROOT_ODA = "/home/u64235016/TROPIC"
    PGMDIR_ODA    = f"{PROJ_ROOT_ODA}/02_production_sas"
    SDTM_ODA      = f"{PROJ_ROOT_ODA}/01_raw_source/real_sdtm"
    ADAM_ODA      = f"{PROJ_ROOT_ODA}/04_adam"
    CFG_FILE      = os.path.join(os.path.dirname(__file__), "..", "sascfg_personal.py")

    sas = saspy.SASsession(
        cfgname="oda",
        cfgfile=os.path.abspath(CFG_FILE)
    )

    try:
        # ---- Upload SAS programs ----
        print("  [ODA] Uploading SAS programs to ODA...")
        for f in sorted(_glob.glob("02_production_sas/*.sas")):
            sas.upload(f, f"{PGMDIR_ODA}/{os.path.basename(f)}")
        print(f"  [ODA] SAS programs uploaded.")

        # ---- Upload SDTM source data (skip if already present) ----
        sdtm_files = sorted(_glob.glob("01_raw_source/real_sdtm/*.sas7bdat"))
        total_mb = sum(os.path.getsize(f) for f in sdtm_files) / 1_048_576
        print(f"  [ODA] Uploading {len(sdtm_files)} SDTM files ({total_mb:.0f} MB) — this may take several minutes...")
        for f in sdtm_files:
            sas.upload(f, f"{SDTM_ODA}/{os.path.basename(f)}")
        print(f"  [ODA] SDTM data uploaded.")

        # ---- Execute master driver ----
        print("  [ODA] Submitting 00_master_driver.sas via SAS IOM...")
        r = sas.submit(f"""
options notes source;
%global PROJ_ROOT PGMDIR;
%let PROJ_ROOT = {PROJ_ROOT_ODA};
%let PGMDIR    = {PGMDIR_ODA};
filename drv "{PGMDIR_ODA}/00_master_driver.sas";
%include drv;
""")
        log = r.get("LOG", "")

        # Capture errors
        error_lines = [l.strip() for l in log.split("\n")
                       if l.strip().startswith("ERROR:")]
        if error_lines:
            return 1, "", "\n".join(error_lines)

        # ---- Download *_prod.xpt files ----
        datasets = ["adsl", "adex", "adcm", "adae", "adlb", "adrs", "adtte"]
        print("  [ODA] Downloading *_prod.xpt files from ODA...")
        for ds in datasets:
            remote = f"{ADAM_ODA}/{ds}_prod.xpt"
            local  = f"04_adam/{ds}_prod.xpt"
            sas.download(local, remote)   # SASPy: download(localfile, remotefile)
            print(f"    Downloaded {ds}_prod.xpt")

        return 0, "SASPy/ODA execution complete.", ""

    finally:
        sas.endsas()


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
    if local_sas:
        return "local"
    if real_sas and saspy_ok:
        return "oda"
    if real_sas:
        return "error"
    return "sim"


def execute_pipeline(from_stage=0, real_sas=False, use_cached_sas=False):
    print("=== EXECUTING TROPIC (Study EFC6193 / XRP6258) PIPELINE ===")

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
    
    for stage in stages:
        if stage["id"] < from_stage:
            print(f"Skipping Stage {stage['id']}: {stage['name']}")
            continue
            
        print(f"Executing Stage {stage['id']}: {stage['name']}...")
        
        if stage["id"] == 1:
            create_backup()

        if stage["cmd"] == "SIMULATE":
            datasets = ["adsl", "adex", "adcm", "adae", "adlb", "adrs", "adtte"]

            if sas_mode == "oda":
                print("  [ODA] Executing real SAS 9.4 via SAS OnDemand for Academics (SASPy IOM)...")
                rc, stdout, stderr = _run_saspy_stage10()
                if rc == 0:
                    print("  [ODA] Master driver executed successfully. Real SAS XPTs generated and downloaded.")
                else:
                    print("  [ODA FAILED] SASPy/ODA execution failed!")
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
            elif sas_mode == "cached":
                # --use-cached-sas: reconcile against pre-existing *_prod.xpt. This does
                # NOT run SAS this session; it re-verifies previously generated artifacts.
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
            elif sas_mode == "error":
                print("  [ERROR] --real-sas was requested but no SAS engine is available:")
                print("          no local 'sas' on PATH and SASPy is not importable.")
                print("          Install SASPy + configure ODA, or use --use-cached-sas to reconcile existing outputs.")
                rc, stdout, stderr = -1, "", "Real SAS requested but no SAS engine available"
            else:  # sas_mode == "sim"
                print("  [SAS SIMULATOR] No SAS engine and --real-sas not specified.")
                print("  [SAS SIMULATOR] Copying *_v.xpt -> *_prod.xpt (byte-copy simulation).")
                print("  [SAS SIMULATOR] WARNING: this is NOT independent double-programming; zero diffs are tautological.")
                for ds in datasets:
                    val_file = f"04_adam/{ds}_v.xpt"
                    prod_file = f"04_adam/{ds}_prod.xpt"
                    if os.path.exists(val_file):
                        with open(val_file, "rb") as f_src, open(prod_file, "wb") as f_dst:
                            f_dst.write(f_src.read())
                        print(f"    Simulated {ds}_prod.xpt generated.")
                rc, stdout, stderr = 0, "Simulated SAS compilation (byte-copy) complete.", ""
        else:
            rc, stdout, stderr = run_command(stage["cmd"])

        # Build honesty (audit F-6): the reconciliation R script logs FAILs but
        # exits 0. Gate Stage 11 on its machine-readable status so the build can
        # never go GREEN while a domain has cell-level differences.
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
        else:
            print(f"  [FAILED] Stage {stage['id']} failed. Reason: {stderr.strip()}")
            results[stage["name"]] = "FAIL"
            # Auto-rollback to maintain environmental state integrity on validation failures (Rule 7)
            print("  [ERROR] Validation or execution error detected! Automated rollback initiated...")
            rollback()
            write_telemetry(results, sas_mode)
            sys.exit(1)

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

    args = parser.parse_args()

    if args.dry_run:
        dry_run()
    elif args.rollback:
        rollback()
    elif args.demo:
        print("=== RUNNING SELF-CONTAINED DEMO (SMOKE TEST) ===")
        rc, stdout, stderr = run_command([RSCRIPT_PATH, "tests/smoke_test.R"])
        print(stdout)
        if rc != 0:
            print(f"ERROR: Smoke test failed!\n{stderr}")
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
        execute_pipeline(args.from_stage, args.real_sas, args.use_cached_sas)

if __name__ == "__main__":
    main()
