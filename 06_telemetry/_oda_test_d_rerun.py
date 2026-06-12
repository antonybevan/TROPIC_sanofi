"""
Targeted ODA rerun: upload the (already-fixed) SAS programs, execute the master
driver on ODA, and download the 7 *_prod.xpt in the same session **only if the run
is clean**. Use this to regenerate production XPTs after editing SAS programs
WITHOUT re-uploading the ~200 MB SDTM source (assumed already present on ODA).

Run from anywhere:
    python3 -u 06_telemetry/_oda_test_d_rerun.py
    python3 -u 06_telemetry/_oda_test_d_rerun.py --upload-sdtm   # also push SDTM

Exit code is 0 only if the SAS run had no ERRORs AND all 7 XPTs downloaded.
"""
import os
import sys
import glob

# ---------------------------------------------------------------------------
# Anchor every local path to the PROJECT ROOT derived from this file's location,
# NOT the current working directory. The previous version used cwd-relative paths
# (glob("02_production_sas/*.sas"), cfgfile="sascfg_personal.py", ...); when this
# script was launched from any directory other than the project root, the glob
# silently matched nothing, ZERO programs were uploaded, and the master driver
# then ran stale code on ODA with no warning. Anchoring to __file__ fixes that.
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(PROJECT_ROOT)               # makes saspy's relative SAS paths resolve too
sys.path.insert(0, PROJECT_ROOT)

import saspy  # noqa: E402  (import after sys.path setup is intentional)

ODA_HOME      = "/home/u64235016"
PROJ_ROOT_ODA = f"{ODA_HOME}/TROPIC"
PGMDIR_ODA    = f"{PROJ_ROOT_ODA}/02_production_sas"
SDTM_ODA      = f"{PROJ_ROOT_ODA}/01_raw_source/real_sdtm"
ADAM_ODA      = f"{PROJ_ROOT_ODA}/04_adam"
DATASETS      = ["adsl", "adex", "adcm", "adae", "adlb", "adrs", "adtte"]
CFG_FILE      = os.path.join(PROJECT_ROOT, "sascfg_personal.py")
LOG_OUT       = os.path.join(PROJECT_ROOT, "02_production_sas", "oda_master_driver.log")
PGM_GLOB      = os.path.join(PROJECT_ROOT, "02_production_sas", "*.sas")
UPLOAD_SDTM   = "--upload-sdtm" in sys.argv

if not os.path.exists(CFG_FILE):
    sys.exit(f"ERROR: SAS config not found: {CFG_FILE}")

programs = sorted(glob.glob(PGM_GLOB))
if not programs:
    sys.exit(f"ERROR: no SAS programs matched {PGM_GLOB} — refusing to run a no-op upload.")

print("Connecting to ODA...", flush=True)
sas = saspy.SASsession(cfgname="oda", cfgfile=CFG_FILE)
print("Connected.", flush=True)

try:
    # 1. Upload the fixed SAS programs
    print(f"Uploading {len(programs)} SAS programs...", flush=True)
    for f in programs:
        sas.upload(f, f"{PGMDIR_ODA}/{os.path.basename(f)}")
        print(f"  {os.path.basename(f)}", flush=True)

    # 1b. Optionally (re)upload SDTM source (only needed on a fresh ODA workspace)
    if UPLOAD_SDTM:
        sdtm_files = sorted(glob.glob(os.path.join(PROJECT_ROOT, "01_raw_source", "real_sdtm", "*.sas7bdat")))
        print(f"Uploading {len(sdtm_files)} SDTM files (this may take several minutes)...", flush=True)
        for f in sdtm_files:
            sas.upload(f, f"{SDTM_ODA}/{os.path.basename(f)}")
        print("  SDTM upload complete.", flush=True)

    # 2. Execute master driver
    print("\n=== Submitting 00_master_driver.sas on ODA ===", flush=True)
    r = sas.submit(f"""
options notes source;
%global PROJ_ROOT PGMDIR;
%let PROJ_ROOT = {PROJ_ROOT_ODA};
%let PGMDIR    = {PGMDIR_ODA};
filename drv "{PGMDIR_ODA}/00_master_driver.sas";
%include drv;
""")
    log = r.get("LOG", "")

    with open(LOG_OUT, "w") as fh:
        fh.write(log)
    print(f"Full log saved: {LOG_OUT} ({len(log)} bytes)", flush=True)

    print("\nKEY LOG LINES:", flush=True)
    error_lines = []
    for line in log.split("\n"):
        s = line.strip()
        if s.startswith("ERROR"):
            error_lines.append(s)
        if (s.startswith("NOTE: [") or s.startswith("ERROR")
                or "PIPELINE" in s or "EXPORT" in s or "CONFIG" in s):
            print(" ", s, flush=True)

    if error_lines:
        print(f"\nRESULT: FAILED — {len(error_lines)} ERROR line(s). Not downloading XPTs.", flush=True)
        sys.exit(1)

    # 3. Clean run: download XPTs in the same session
    print("\nRESULT: CLEAN. Downloading *_prod.xpt files...", flush=True)
    failures = []
    for ds in DATASETS:
        remote = f"{ADAM_ODA}/{ds}_prod.xpt"
        local  = os.path.join(PROJECT_ROOT, "04_adam", f"{ds}_prod.xpt")
        try:
            res = sas.download(local, remote)   # saspy: download(localfile, remotefile)
        except Exception as e:                  # network/transfer error -> treat as failure
            res = {"Success": False, "ERR": str(e)}
        ok = bool(isinstance(res, dict) and res.get("Success", False)) and os.path.exists(local)
        size = os.path.getsize(local) if ok else 0
        if not ok:
            failures.append(ds)
        print(f"  {ds}_prod.xpt: {'OK' if ok else 'FAILED'} ({size/1024:.0f} KB)", flush=True)

    if failures:
        print(f"\nRESULT: DOWNLOAD INCOMPLETE — failed: {', '.join(failures)}", flush=True)
        sys.exit(2)

    print("\nTEST D RERUN COMPLETE — all 7 *_prod.xpt downloaded.", flush=True)
finally:
    sas.endsas()
