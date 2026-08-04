"""
Render the SAS production-track TFL figures on ODA.

Steps (all paths anchored to the project root, independent of cwd):
  1. Upload all SAS programs (incl. T_tfl_generation.sas) + the 6 bridged
     *_cbzp.xpt synthetic-comparator files.
  2. Run 00_master_driver.sas (regenerates adam.* + *_prod.xpt).
  3. Run T_tfl_generation.sas (renders the publication figures to ODA).
  4. Download the *_prod.xpt and the SAS *.png figures to 05_outputs/tfl/output/sas/.

Run:  python3 -u platform/_oda_render_tfl.py
Exit 0 only if the SAS runs are ERROR-free and all figures download.
"""
import os
import sys
import glob
import shutil
import subprocess
import re

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # platform/, for oda_broker

import oda_broker  # noqa: E402 — governed helper for ODA connect/teardown (slot hygiene)
import seed_sdtm  # noqa: E402 — reuses ODA mkdir helper before uploads

# No developer account id is hard-coded (roadmap #10): default to a ~/TROPIC layout that is
# resolved against the connected account's $HOME after login; override via TROPIC_ODA_PROJ_ROOT.
PROJ_ROOT_ODA = os.environ.get("TROPIC_ODA_PROJ_ROOT", "~/TROPIC")
CFG_FILE      = os.path.join(PROJECT_ROOT, "sascfg_personal.py")


def _oda_paths(root):
    return (f"{root}/04_analysis_datasets/programs/sas", f"{root}/01_source_data/cbzp_reconstructed",
            f"{root}/04_analysis_datasets/adam", f"{root}/05_outputs/tfl/output/figures/sas")


PGMDIR_ODA, CBZ_ODA, ADAM_ODA, SASFIG_ODA = _oda_paths(PROJ_ROOT_ODA)

# Reconciled datasets come from the study manifest (governed control source shared
# with cibuild.py); fall back to the legacy TROPIC list if the manifest is absent.
try:
    import manifest as _manifest_mod  # noqa: E402 — platform/ already on sys.path
    DATASETS = _manifest_mod.dataset_names(_manifest_mod.load_manifest())
except Exception:  # noqa: BLE001
    DATASETS = ["adsl", "adex", "adcm", "adae", "adlb", "adrs", "adtte", "clinsite"]
CBZ_DOMS = ["adsl", "adtte", "adae", "adlb", "adex", "adrs"]
FIGURES  = [
    "F-11-1_KM_OS_SAS", "F-11-2_KM_PFS_SAS", "F-12-1_Subgroup_Forest_SAS",
    "F-13-1_PSA_Waterfall_SAS", "F-14-1_Swimmer_Plot_SAS", "F-17-1_Optimus_Scatter_SAS",
]
FIGURE_DATA_FILES = [
    "forest_hr_prod.csv", "figure_km_stats_prod.csv",
    "figure_km_risk_prod.csv", "figure_waterfall_prod.csv",
    "figure_swimmer_prod.csv", "figure_er_prod.csv",
]

TFL_ONLY = False


def errors_in(log):
    """SAS log error signatures that should make this renderer fail closed."""
    out = []
    for line in log.splitlines():
        s = line.strip()
        if re.match(r"^ERROR(?::|\s+\d|-)", s):
            out.append(s)
        elif re.search(r"\b_ERROR_\s*=\s*1\b", s):
            out.append(s)
        elif s.startswith("NOTE: The SAS System stopped processing"):
            out.append(s)
    return out


def _download_checked(sas, local, remote, label):
    """Download into .part and promote only after a successful, nonempty transfer."""
    tmp = local + ".part"
    for p in (tmp, local):
        try:
            os.remove(p)
        except OSError:
            pass
    try:
        res = sas.download(tmp, remote)
    except Exception as e:
        return False, f"{label}: download exception: {e}"
    ok = bool(isinstance(res, dict) and res.get("Success", False)) and os.path.exists(tmp)
    size = os.path.getsize(tmp) if ok else 0
    if not ok or size <= 0:
        try:
            os.remove(tmp)
        except OSError:
            pass
        return False, f"{label}: download failed ({res})"
    os.replace(tmp, local)
    return True, f"{label}: OK ({size/1024:.0f} KB)"


def _purge_remote_outputs(sas):
    """Remove expected ODA-side render outputs so downloads prove this run regenerated them."""
    targets = [f"{SASFIG_ODA}/{fig}.png" for fig in FIGURES]
    targets += [f"{ADAM_ODA}/{name}" for name in FIGURE_DATA_FILES]
    lines = ["data _null_;"]
    for i, target in enumerate(targets, 1):
        lines.append(f'  filename _t{i} "{target}";')
        lines.append(f'  if fexist("_t{i}") then _rc=fdelete("_t{i}");')
        lines.append(f'  filename _t{i} clear;')
    lines.append('  put "TROPIC_PURGE_TFL|DONE";')
    lines.append("run;")
    log = sas.submit("\n".join(lines)).get("LOG", "")
    if "TROPIC_PURGE_TFL|DONE" not in log:
        sys.exit("ERROR: failed to purge prior ODA TFL outputs before render.")


def main(argv=None):
    global PROJ_ROOT_ODA, PGMDIR_ODA, CBZ_ODA, ADAM_ODA, SASFIG_ODA, TFL_ONLY
    argv = sys.argv[1:] if argv is None else argv
    TFL_ONLY = "--tfl-only" in argv
    os.chdir(PROJECT_ROOT)

    if not os.path.exists(CFG_FILE):
        sys.exit(f"ERROR: SAS config not found: {CFG_FILE}")

    programs = sorted(glob.glob(os.path.join(PROJECT_ROOT, "04_analysis_datasets/programs/sas", "*.sas")))
    cbz_xpts = [
        os.path.join(PROJECT_ROOT, "01_source_data", "cbzp_reconstructed", f"{d}_cbzp.xpt")
        for d in CBZ_DOMS
    ]

    if any(not os.path.exists(p) for p in cbz_xpts):
        rscript = shutil.which("Rscript") or "Rscript"
        print("CbzP XPT bridge files missing -> running 01_source_data/export_cbzp_xpt.R ...",
              flush=True)
        for p in cbz_xpts:
            try:
                os.remove(p)
            except OSError:
                pass
        try:
            subprocess.run([rscript, os.path.join(PROJECT_ROOT, "01_source_data",
                                                  "export_cbzp_xpt.R")],
                           cwd=PROJECT_ROOT, check=True)
        except FileNotFoundError:
            sys.exit("ERROR: Rscript not found; cannot regenerate missing CbzP XPT bridge files.")
        except subprocess.CalledProcessError as e:
            sys.exit(f"ERROR: CbzP XPT bridge export failed with rc={e.returncode}.")
    missing = [p for p in cbz_xpts if not os.path.exists(p)]
    if missing:
        sys.exit(f"ERROR: missing CbzP XPT bridge files after export attempt: {missing}.\n"
                 f"       Ensure the reconstructed RDS exist "
                 f"(run 01_source_data/reconstruct_cbzp_arm.R).")
    if not programs:
        sys.exit("ERROR: no SAS programs found to upload.")

    print("Connecting to ODA (via broker)...", flush=True)
    try:
        conn = oda_broker.connect(max_wait_s=int(os.environ.get("TROPIC_ODA_MAX_WAIT", "3600")))
    except oda_broker.OdaFatal as e:
        sys.exit(f"ERROR: ODA fatal ({e.error_class}): {e}")
    except oda_broker.OdaExhausted as e:
        sys.exit(f"ERROR: ODA unavailable after {e.attempts} attempt(s) (last: {e.last_class}).")
    sas = conn.sas
    print(f"Connected via broker (endpoint={conn.endpoint}, attempts={conn.attempts}).", flush=True)

    exec_timeout = int(os.environ.get("TROPIC_ODA_EXEC_TIMEOUT", "1800"))
    force_td = False

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
        upload_pgms = [
            f for f in programs
            if (not TFL_ONLY) or os.path.basename(f) in ("T_tfl_generation.sas", "00_config.sas")
        ]
        print(f"Uploading {len(upload_pgms)} SAS programs...", flush=True)
        if not seed_sdtm._ensure_remote_dir(sas, PGMDIR_ODA):
            sys.exit(f"ERROR: could not create ODA SAS program directory: {PGMDIR_ODA}")
        for f in upload_pgms:
            sas.upload(f, f"{PGMDIR_ODA}/{os.path.basename(f)}")
        if not TFL_ONLY:
            print(f"Uploading {len(cbz_xpts)} CbzP bridge XPTs...", flush=True)
            if not seed_sdtm._ensure_remote_dir(sas, CBZ_ODA):
                sys.exit(f"ERROR: could not create ODA CbzP bridge directory: {CBZ_ODA}")
            if not seed_sdtm._ensure_remote_dir(sas, ADAM_ODA):
                sys.exit(f"ERROR: could not create ODA ADaM directory: {ADAM_ODA}")
            if not seed_sdtm._ensure_remote_dir(sas, f"{ADAM_ODA}/sdtm_mapped"):
                sys.exit(f"ERROR: could not create ODA mapped SDTM directory: {ADAM_ODA}/sdtm_mapped")
            sas.submit(f"""
data _null_;
  if fileexist("{PROJ_ROOT_ODA}/01_source_data/cbzp_reconstructed") = 0 then
     rc = dcreate('cbzp_reconstructed', "{PROJ_ROOT_ODA}/01_source_data");
run;
""")
            for f in cbz_xpts:
                sas.upload(f, f"{CBZ_ODA}/{os.path.basename(f)}")
        print("  uploads complete.", flush=True)

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
""", timeout_s=exec_timeout)
            except oda_broker.OdaExecTimeout as e:
                force_td = True
                sys.exit(f"RESULT: master driver TIMED OUT after {e.timeout_s}s "
                         f"(workspace presumed hung; session force-reaped).")
            with open(os.path.join(PROJECT_ROOT, "04_analysis_datasets/programs/sas", "oda_master_driver.log"),
                      "w") as fh:
                fh.write(r["LOG"])
            errs = errors_in(r["LOG"])
            if errs:
                print(f"RESULT: master driver FAILED — {len(errs)} ERROR line(s):", flush=True)
                for e in errs[:20]:
                    print("  ", e, flush=True)
                print("  See 04_analysis_datasets/programs/sas/oda_master_driver.log", flush=True)
                sys.exit(1)
            print("  master driver clean.", flush=True)
        else:
            print("\n=== Skipping master driver (--tfl-only); using existing adam.* on ODA ===",
                  flush=True)

        if not seed_sdtm._ensure_remote_dir(sas, SASFIG_ODA):
            sys.exit(f"ERROR: could not create ODA SAS figure directory: {SASFIG_ODA}")
        print("Purging prior ODA TFL outputs before render...", flush=True)
        _purge_remote_outputs(sas)
        print("\n=== Running T_tfl_generation.sas ===", flush=True)
        try:
            r2 = oda_broker.submit_timed(sas, f"""
options notes source;
%global PROJ_ROOT PGMDIR;
%let PROJ_ROOT = {PROJ_ROOT_ODA};
%let PGMDIR    = {PGMDIR_ODA};
filename tfl "{PGMDIR_ODA}/T_tfl_generation.sas";
%include tfl;
""", timeout_s=exec_timeout)
        except oda_broker.OdaExecTimeout as e:
            force_td = True
            sys.exit(f"RESULT: T_tfl_generation TIMED OUT after {e.timeout_s}s "
                     f"(workspace presumed hung; session force-reaped).")
        with open(os.path.join(PROJECT_ROOT, "04_analysis_datasets/programs/sas", "oda_tfl.log"), "w") as fh:
            fh.write(r2["LOG"])
        errs2 = errors_in(r2["LOG"])
        for line in r2["LOG"].split("\n"):
            s = line.strip()
            if s.startswith("ERROR") or "[TFL-SAS]" in s:
                print("  ", s, flush=True)
        if errs2:
            print(f"RESULT: T_tfl_generation had {len(errs2)} ERROR line(s) — "
                  f"see 04_analysis_datasets/programs/sas/oda_tfl.log", flush=True)
            sys.exit(2)

        os.makedirs(os.path.join(PROJECT_ROOT, "04_analysis_datasets/adam"), exist_ok=True)
        os.makedirs(os.path.join(PROJECT_ROOT, "05_outputs/tfl", "output", "figures", "sas"),
                    exist_ok=True)
        if not TFL_ONLY:
            print("\nDownloading *_prod.xpt...", flush=True)
            xpt_fail = []
            for ds in DATASETS:
                local = os.path.join(PROJECT_ROOT, "04_analysis_datasets/adam", f"{ds}_prod.xpt")
                ok, msg = _download_checked(sas, local, f"{ADAM_ODA}/{ds}_prod.xpt",
                                            f"{ds}_prod.xpt")
                print(f"  {msg}", flush=True)
                if not ok:
                    xpt_fail.append(ds)
            if xpt_fail:
                sys.exit(f"RESULT: XPT download FAILED for {xpt_fail}")

        print("Downloading SAS figures...", flush=True)
        fig_fail = []
        for fig in FIGURES:
            local = os.path.join(PROJECT_ROOT, "05_outputs/tfl", "output", "figures", "sas",
                                 f"{fig}.png")
            ok, msg = _download_checked(sas, local, f"{SASFIG_ODA}/{fig}.png", f"{fig}.png")
            if not ok:
                fig_fail.append(fig)
            print(f"  {msg}", flush=True)

        data_fail = []
        for name in FIGURE_DATA_FILES:
            ok, msg = _download_checked(sas, os.path.join(PROJECT_ROOT, "04_analysis_datasets/adam", name),
                                        f"{ADAM_ODA}/{name}", name)
            print(f"  {msg}", flush=True)
            if not ok:
                data_fail.append(name)

        if fig_fail or data_fail:
            print(f"\nRESULT: PARTIAL — missing figs={fig_fail}, "
                  f"missing figure data={data_fail}", flush=True)
            sys.exit(2)
        print("\nSAS TFL RENDER COMPLETE — all figures downloaded to "
              "05_outputs/tfl/output/figures/sas/.", flush=True)
    finally:
        oda_broker.teardown(sas, force=force_td)


if __name__ == "__main__":
    main()
