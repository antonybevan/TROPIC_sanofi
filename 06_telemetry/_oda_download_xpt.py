"""
One-shot: download the 7 *_prod.xpt files from ODA to 04_adam/.
Run after the master driver has executed on ODA.
"""
import os, sys
# Anchor paths to the project root (parent of this file), independent of cwd.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
import saspy

ADAM_ODA  = "/home/u64235016/TROPIC/04_adam"
LOCAL_DIR = os.path.join(PROJECT_ROOT, "04_adam")
DATASETS  = ["adsl", "adex", "adcm", "adae", "adlb", "adrs", "adtte"]
CFG_FILE  = os.path.join(PROJECT_ROOT, "sascfg_personal.py")

sas = saspy.SASsession(cfgname="oda", cfgfile=CFG_FILE)

try:
    # Verify files exist on ODA first
    checks = "\n".join(
        f'%put NOTE: [CHECK] {ds}_prod=%sysfunc(fileexist({ADAM_ODA}/{ds}_prod.xpt));'
        for ds in DATASETS
    )
    r = sas.submit(f"options notes source;\n{checks}")
    for line in r["LOG"].split("\n"):
        s = line.strip()
        if s.startswith("NOTE: [CHECK]"):
            print(s)

    # Download
    print("\nDownloading *_prod.xpt files from ODA...")
    for ds in DATASETS:
        remote = f"{ADAM_ODA}/{ds}_prod.xpt"
        local  = f"{LOCAL_DIR}/{ds}_prod.xpt"
        result = sas.download(local, remote)
        ok = result.get("Success", False)
        size = os.path.getsize(local) if ok and os.path.exists(local) else 0
        print(f"  {ds}_prod.xpt: {'OK' if ok else 'FAILED'} ({size/1024:.0f} KB)")

    print("\nAll downloads complete.")
finally:
    sas.endsas()
