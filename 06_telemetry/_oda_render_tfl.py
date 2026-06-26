"""
Render the SAS production-track TFL figures on ODA.

Steps (all paths anchored to the project root, independent of cwd):
  1. Upload all SAS programs (incl. T_tfl_generation.sas) + the 6 bridged
     *_cbzp.xpt synthetic-comparator files.
  2. Run 00_master_driver.sas (regenerates adam.* + *_prod.xpt).
  3. Run T_tfl_generation.sas (renders the publication figures to ODA).
  4. Download the *_prod.xpt and the SAS *.png figures to 09_tfl/output/sas/.

Run:  python3 -u 06_telemetry/_oda_render_tfl.py
Exit 0 only if the SAS runs are ERROR-free and all figures download.
"""
import os
import sys
import glob
import shutil
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # 06_telemetry/, for oda_broker

import oda_broker  # noqa: E402 — governed helper for ODA connect/teardown (slot hygiene)

# No developer account id is hard-coded (roadmap #10): default to a ~/TROPIC layout that is
# resolved against the connected account's $HOME after login; override via TROPIC_ODA_PROJ_ROOT.
PROJ_ROOT_ODA = os.environ.get("TROPIC_ODA_PROJ_ROOT", "~/TROPIC")
CFG_FILE      = os.path.join(PROJECT_ROOT, "sascfg_personal.py")


def _oda_paths(root):
    return (f"{root}/02_production_sas", f"{root}/01_raw_source/cbzp_reconstructed",
            f"{root}/04_adam", f"{root}/09_tfl/output/figures/sas")


PGMDIR_ODA, CBZ_ODA, ADAM_ODA, SASFIG_ODA = _oda_paths(PROJ_ROOT_ODA)

# Reconciled datasets come from the study manifest (governed control source shared
# with cibuild.py); fall back to the legacy TROPIC list if the manifest is absent.
try:
    import manifest as _manifest_mod  # noqa: E402 — 06_telemetry/ already on sys.path
    DATASETS = _manifest_mod.dataset_names(_manifest_mod.load_manifest())
except Exception:  # noqa: BLE001
    DATASETS = ["adsl", "adex", "adcm", "adae", "adlb", "adrs", "adtte", "clinsite"]
CBZ_DOMS = ["adsl", "adtte", "adae", "adlb", "adex", "adrs"]
FIGURES  = [
    "F-11-1_KM_OS_SAS", "F-11-2_KM_PFS_SAS", "F-12-1_Subgroup_Forest_SAS",
    "F-13-1_PSA_Waterfall_SAS", "F-14-1_Swimmer_Plot_SAS", "F-17-1_Optimus_Scatter_SAS",
]

TFL_ONLY = "--tfl-only" in sys.argv   # skip master driver; adam.* + CbzP xpt already on ODA

if not os.path.exists(CFG_FILE):
    sys.exit(f"ERROR: SAS config not found: {CFG_FILE}")

programs = sorted(glob.glob(os.path.join(PROJECT_ROOT, "02_production_sas", "*.sas")))
cbz_xpts = [os.path.join(PROJECT_ROOT, "01_raw_source", "cbzp_reconstructed", f"{d}_cbzp.xpt") for d in CBZ_DOMS]

# Self-sufficient bridge: if the CbzP XPTs are absent, generate them from the
# reconstructed RDS via the committed export program (idempotent).
if any(not os.path.exists(p) for p in cbz_xpts):
    rscript = shutil.which("Rscript") or "Rscript"
    print("CbzP XPT bridge files missing -> running 01_raw_source/export_cbzp_xpt.R ...", flush=True)
    subprocess.run([rscript, os.path.join(PROJECT_ROOT, "01_raw_source", "export_cbzp_xpt.R")],
                   cwd=PROJECT_ROOT)
missing = [p for p in cbz_xpts if not os.path.exists(p)]
if missing:
    sys.exit(f"ERROR: missing CbzP XPT bridge files after export attempt: {missing}.\n"
             f"       Ensure the reconstructed RDS exist (run 01_raw_source/reconstruct_cbzp_arm.R).")
if not programs:
    sys.exit("ERROR: no SAS programs found to upload.")


def errors_in(log):
    return [l.strip() for l in log.split("\n") if l.strip().startswith("ERROR")]


print("Connecting to ODA (via broker)...", flush=True)
try:
    conn = oda_broker.connect(max_wait_s=int(os.environ.get("TROPIC_ODA_MAX_WAIT", "3600")))
except oda_broker.OdaFatal as e:
    sys.exit(f"ERROR: ODA fatal ({e.error_class}): {e}")
except oda_broker.OdaExhausted as e:
    sys.exit(f"ERROR: ODA unavailable after {e.attempts} attempt(s) (last: {e.last_class}).")
sas = conn.sas
print(f"Connected via broker (endpoint={conn.endpoint}, attempts={conn.attempts}).", flush=True)

EXEC_TIMEOUT = int(os.environ.get("TROPIC_ODA_EXEC_TIMEOUT", "1800"))  # per-submit deadline
force_td = False  # set True if a submit times out -> finally force-reaps the wedged session

# Resolve a leading '~' in the ODA root against the connected account's $HOME, so no per-user
# absolute path is committed (roadmap #10).
if "~" in PROJ_ROOT_ODA:
    _log = sas.submit("%put TROPIC_ODA_HOME=%sysget(HOME);").get("LOG", "")
    for _line in _log.splitlines():
        if "TROPIC_ODA_HOME=" in _line and "%put" not in _line and "%sysget" not in _line:
            _home = _line.split("TROPIC_ODA_HOME=", 1)[1].strip()
            if _home:
                PROJ_ROOT_ODA = PROJ_ROOT_ODA.replace("~", _home, 1)
                PGMDIR_ODA, CBZ_ODA, ADAM_ODA, SASFIG_ODA = _oda_paths(PROJ_ROOT_ODA)
            break

try:
    # 1. Upload programs (+ CbzP bridge XPTs unless tfl-only)
    upload_pgms = [f for f in programs if (not TFL_ONLY) or os.path.basename(f) in ("T_tfl_generation.sas", "00_config.sas")]
    print(f"Uploading {len(upload_pgms)} SAS programs...", flush=True)
    for f in upload_pgms:
        sas.upload(f, f"{PGMDIR_ODA}/{os.path.basename(f)}")
    if not TFL_ONLY:
        print(f"Uploading {len(cbz_xpts)} CbzP bridge XPTs...", flush=True)
        sas.submit(f"""
data _null_;
  if fileexist("{PROJ_ROOT_ODA}/01_raw_source/cbzp_reconstructed") = 0 then
     rc = dcreate('cbzp_reconstructed', "{PROJ_ROOT_ODA}/01_raw_source");
run;
""")
        for f in cbz_xpts:
            sas.upload(f, f"{CBZ_ODA}/{os.path.basename(f)}")
    print("  uploads complete.", flush=True)

    # 2. Master driver (ADaM + XPT) — skipped in --tfl-only mode
    if not TFL_ONLY:
        print("\n=== Running 00_master_driver.sas ===", flush=True)
        try:
            r = oda_broker.submit_timed(sas, f"""
options notes source;
%global PROJ_ROOT PGMDIR;
%let PROJ_ROOT = {PROJ_ROOT_ODA};
%let PGMDIR    = {PGMDIR_ODA};
filename drv "{PGMDIR_ODA}/00_master_driver.sas";
%include drv;
""", timeout_s=EXEC_TIMEOUT)
        except oda_broker.OdaExecTimeout as e:
            force_td = True
            sys.exit(f"RESULT: master driver TIMED OUT after {e.timeout_s}s "
                     f"(workspace presumed hung; session force-reaped).")
        errs = errors_in(r["LOG"])
        if errs:
            print(f"RESULT: master driver FAILED — {len(errs)} ERROR line(s):", flush=True)
            for e in errs[:20]:
                print("  ", e, flush=True)
            sys.exit(1)
        print("  master driver clean.", flush=True)
    else:
        print("\n=== Skipping master driver (--tfl-only); using existing adam.* on ODA ===", flush=True)

    # 3. SAS TFL figures
    print("\n=== Running T_tfl_generation.sas ===", flush=True)
    try:
        r2 = oda_broker.submit_timed(sas, f"""
options notes source;
%global PROJ_ROOT PGMDIR;
%let PROJ_ROOT = {PROJ_ROOT_ODA};
%let PGMDIR    = {PGMDIR_ODA};
filename tfl "{PGMDIR_ODA}/T_tfl_generation.sas";
%include tfl;
""", timeout_s=EXEC_TIMEOUT)
    except oda_broker.OdaExecTimeout as e:
        force_td = True
        sys.exit(f"RESULT: T_tfl_generation TIMED OUT after {e.timeout_s}s "
                 f"(workspace presumed hung; session force-reaped).")
    with open(os.path.join(PROJECT_ROOT, "02_production_sas", "oda_tfl.log"), "w") as fh:
        fh.write(r2["LOG"])
    errs2 = errors_in(r2["LOG"])
    for line in r2["LOG"].split("\n"):
        s = line.strip()
        if s.startswith("ERROR") or "[TFL-SAS]" in s:
            print("  ", s, flush=True)
    if errs2:
        print(f"RESULT: T_tfl_generation had {len(errs2)} ERROR line(s) — see 02_production_sas/oda_tfl.log", flush=True)

    # 4. Download prod XPT + SAS figures
    os.makedirs(os.path.join(PROJECT_ROOT, "04_adam"), exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT, "09_tfl", "output", "figures", "sas"), exist_ok=True)
    if not TFL_ONLY:
        print("\nDownloading *_prod.xpt...", flush=True)
        for ds in DATASETS:
            sas.download(os.path.join(PROJECT_ROOT, "04_adam", f"{ds}_prod.xpt"), f"{ADAM_ODA}/{ds}_prod.xpt")

    print("Downloading SAS figures...", flush=True)
    fig_fail = []
    for fig in FIGURES:
        local = os.path.join(PROJECT_ROOT, "09_tfl", "output", "figures", "sas", f"{fig}.png")
        try:
            res = sas.download(local, f"{SASFIG_ODA}/{fig}.png")
        except Exception as e:
            res = {"Success": False, "ERR": str(e)}
        ok = bool(isinstance(res, dict) and res.get("Success", False)) and os.path.exists(local)
        size = os.path.getsize(local) if ok else 0
        if not ok:
            fig_fail.append(fig)
        print(f"  {fig}.png: {'OK' if ok else 'FAILED'} ({size/1024:.0f} KB)", flush=True)

    # Download the exact figure-driving datasets/statistics for numerical
    # R<->SAS reconciliation. These are outputs of the SAS figure program itself.
    figure_data_files = [
        "forest_hr_prod.csv", "figure_km_stats_prod.csv",
        "figure_km_risk_prod.csv", "figure_waterfall_prod.csv",
        "figure_swimmer_prod.csv", "figure_er_prod.csv",
    ]
    for name in figure_data_files:
        try:
            sas.download(os.path.join(PROJECT_ROOT, "04_adam", name),
                         f"{ADAM_ODA}/{name}")
            print(f"  {name}: OK", flush=True)
        except Exception as e:
            print(f"  {name}: download FAILED ({e})", flush=True)

    if errs2 or fig_fail:
        print(f"\nRESULT: PARTIAL — fig errors={bool(errs2)}, missing figs={fig_fail}", flush=True)
        sys.exit(2)
    print("\nSAS TFL RENDER COMPLETE — all figures downloaded to 09_tfl/output/figures/sas/.", flush=True)
finally:
    oda_broker.teardown(sas, force=force_td)
