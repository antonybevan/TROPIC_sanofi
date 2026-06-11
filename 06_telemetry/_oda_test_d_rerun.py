"""
Test D rerun: upload fixed SAS programs, execute master driver on ODA,
download *_prod.xpt in the same session if clean.
Run with: python3 -u 06_telemetry/_oda_test_d_rerun.py   (from project root)
"""
import os, sys, glob

sys.path.insert(0, os.getcwd())
import saspy

ODA_HOME      = "/home/u64235016"
PROJ_ROOT_ODA = f"{ODA_HOME}/TROPIC"
PGMDIR_ODA    = f"{PROJ_ROOT_ODA}/02_production_sas"
ADAM_ODA      = f"{PROJ_ROOT_ODA}/04_adam"
DATASETS      = ["adsl", "adex", "adcm", "adae", "adlb", "adrs", "adtte"]
LOG_OUT       = "02_production_sas/oda_master_driver.log"

print("Connecting to ODA...", flush=True)
sas = saspy.SASsession(cfgname="oda", cfgfile=os.path.abspath("sascfg_personal.py"))
print("Connected.", flush=True)

try:
    # 1. Upload the 12 fixed SAS programs (SDTM data already on ODA)
    print("Uploading fixed SAS programs...", flush=True)
    for f in sorted(glob.glob("02_production_sas/*.sas")):
        sas.upload(f, f"{PGMDIR_ODA}/{os.path.basename(f)}")
        print(f"  {os.path.basename(f)}", flush=True)

    # 2. Execute master driver
    print("\n=== TEST D (rerun): Submitting 00_master_driver.sas ===", flush=True)
    r = sas.submit(f"""
options notes source;
%global PROJ_ROOT PGMDIR;
%let PROJ_ROOT = {PROJ_ROOT_ODA};
%let PGMDIR    = {PGMDIR_ODA};
filename drv "{PGMDIR_ODA}/00_master_driver.sas";
%include drv;
""")
    log = r["LOG"]

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
    for ds in DATASETS:
        remote = f"{ADAM_ODA}/{ds}_prod.xpt"
        local  = f"04_adam/{ds}_prod.xpt"
        res = sas.download(local, remote)   # saspy: download(localfile, remotefile)
        ok = bool(res.get("Success", False)) and os.path.exists(local)
        size = os.path.getsize(local) if ok else 0
        print(f"  {ds}_prod.xpt: {'OK' if ok else 'FAILED'} ({size/1024:.0f} KB)", flush=True)

    print("\nTEST D RERUN COMPLETE.", flush=True)
finally:
    sas.endsas()
