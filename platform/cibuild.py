import os
import sys
import json
import glob
import subprocess
import argparse
import shutil
import getpass
import re
import signal
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

def _env_int(name, default):
    """int(os.environ[name]) with a safe fallback + warning on a malformed override, so a typo
    (e.g. TROPIC_ODA_MAX_WAIT=foo) surfaces as a clear message instead of an uncaught ValueError
    crashing the run before it starts."""
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"  [WARNING] {name}={raw!r} is not a valid integer; using default {default}.")
        return default


# Wall-clock cap for a single stage's subprocess (a hung logrx::axecute/Rscript otherwise blocks
# the whole pipeline, or one parallel-pool worker, forever -- the local-stage counterpart to the
# ODA side's OdaExecTimeout/force-reap discipline).
STAGE_TIMEOUT_S = _env_int("TROPIC_STAGE_TIMEOUT", 3600)

BACKUP_DIR = "backup_adam"
TFL_OUTPUT_DIR = "05_outputs/tfl/output"
TFL_BACKUP_DIR = "backup_tfl_output"
ECTD_SEQ_DIR = "08_submission_package/ectd/0000"
ECTD_BACKUP_DIR = "backup_ectd_backbone"

# Scope of the pre-run snapshot (deliberately narrow, stated here once so every caller-facing
# message below can quote it instead of implying broader coverage than actually exists): the
# ADaM production XPTs, the TFL suite's rendered tables/figures/listings, and the eCTD backbone
# (index.xml, index-md5.txt, us-regional.xml, the STF) EXCLUDING 08_submission_package/ectd/0000/m5/ -- that payload
# subtree is materialize_ectd.py's own responsibility, with its own purge_unindexed_m5_payloads()
# staleness mechanism, and can hold large XPT copies that would be wasteful to snapshot twice.
    # NOT covered: 03_metadata/define/ metadata, or 08_submission_package/m5/ -- package_ectd.py already
# does its own shutil.rmtree(m5_root) before every rebuild, so a fresh successful run self-heals
# that tree regardless of what this backup covers.
BACKUP_SCOPE = "04_analysis_datasets/adam/*.xpt, 05_outputs/tfl/output/, and 08_submission_package/ectd/0000/ (excl. its m5/ payload)"

def create_backup():
    """Snapshot 04_analysis_datasets/adam/*.xpt, 05_outputs/tfl/output/, and 08_submission_package/ectd/0000/ (excl. m5/) before a run. TFL
    output and the eCTD backbone matter here because tfl_generation.R and build_ectd_backbone.py
    both overwrite a fixed set of named files rather than wiping their directory first, so a run
    that fails its own gate can leave a corrupted/partial file sitting on disk, indistinguishable
    from a good one, until the next successful run happens to overwrite that exact filename
    again."""
    if os.path.exists(BACKUP_DIR):
        shutil.rmtree(BACKUP_DIR)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if os.path.exists("04_analysis_datasets/adam"):
        for f in os.listdir("04_analysis_datasets/adam"):
            if f.endswith(".xpt"):
                shutil.copy(os.path.join("04_analysis_datasets/adam", f), os.path.join(BACKUP_DIR, f))

    if os.path.exists(TFL_BACKUP_DIR):
        shutil.rmtree(TFL_BACKUP_DIR)
    if os.path.exists(TFL_OUTPUT_DIR):
        shutil.copytree(TFL_OUTPUT_DIR, TFL_BACKUP_DIR)

    if os.path.exists(ECTD_BACKUP_DIR):
        shutil.rmtree(ECTD_BACKUP_DIR)
    if os.path.exists(ECTD_SEQ_DIR):
        shutil.copytree(ECTD_SEQ_DIR, ECTD_BACKUP_DIR, ignore=shutil.ignore_patterns("m5"))

def restore_backup():
    """Restore 04_analysis_datasets/adam/*.xpt, 05_outputs/tfl/output/, and 08_submission_package/ectd/0000/ (excl. m5/) -- see BACKUP_SCOPE
    -- from the pre-run snapshot. Returns True if ANY backup existed and was restored, False if
    there was nothing to restore at all -- callers must not report success on False, since no
    snapshot existing means nothing was reverted, not that there was nothing to revert. The TFL
    and eCTD-backbone restores are a full wipe-then-copy-back (not a per-file merge like the
    ADaM restore below them): a corrupted run may have written files that were never part of the
    original snapshot at all, and those must not survive a rollback either."""
    restored = False
    if os.path.exists(BACKUP_DIR):
        for f in os.listdir(BACKUP_DIR):
            if f.endswith(".xpt"):
                shutil.copy(os.path.join(BACKUP_DIR, f), os.path.join("04_analysis_datasets/adam", f))
        shutil.rmtree(BACKUP_DIR)
        restored = True
    if os.path.exists(TFL_BACKUP_DIR):
        if os.path.exists(TFL_OUTPUT_DIR):
            shutil.rmtree(TFL_OUTPUT_DIR)
        shutil.copytree(TFL_BACKUP_DIR, TFL_OUTPUT_DIR)
        shutil.rmtree(TFL_BACKUP_DIR)
        restored = True
    if os.path.exists(ECTD_BACKUP_DIR):
        # m5/ is excluded from this snapshot (materialize_ectd.py owns its own staleness), so
        # it is left untouched here rather than wiped along with the rest of the sequence dir.
        os.makedirs(ECTD_SEQ_DIR, exist_ok=True)
        for entry in os.listdir(ECTD_SEQ_DIR):
            if entry == "m5":
                continue
            full = os.path.join(ECTD_SEQ_DIR, entry)
            shutil.rmtree(full) if os.path.isdir(full) else os.remove(full)
        for entry in os.listdir(ECTD_BACKUP_DIR):
            src = os.path.join(ECTD_BACKUP_DIR, entry)
            dst = os.path.join(ECTD_SEQ_DIR, entry)
            shutil.copytree(src, dst) if os.path.isdir(src) else shutil.copy2(src, dst)
        shutil.rmtree(ECTD_BACKUP_DIR)
        restored = True
    return restored

def clean_backup():
    if os.path.exists(BACKUP_DIR):
        shutil.rmtree(BACKUP_DIR)
    if os.path.exists(TFL_BACKUP_DIR):
        shutil.rmtree(TFL_BACKUP_DIR)
    if os.path.exists(ECTD_BACKUP_DIR):
        shutil.rmtree(ECTD_BACKUP_DIR)

def run_command(cmd, cwd=None, timeout=None):
    """Run `cmd`, returning (returncode, stdout, stderr). On a timeout, kills the WHOLE process
    GROUP, not just the immediate child: subprocess.run()'s own built-in timeout handling only
    ever kills the one process it directly spawned, so a wedged `Rscript -e "logrx::axecute(...)"`
    that itself forked a descendant (R's own parallel workers, a shelled-out subprocess) would
    otherwise survive as an orphan after the timeout fires -- the exact zombie-process failure
    mode oda_broker.py's own force-reap discipline exists to prevent on the ODA side."""
    try:
        popen_kwargs = {"cwd": cwd, "stdout": subprocess.PIPE, "stderr": subprocess.PIPE,
                        "text": True}
        if sys.platform != "win32":
            # New session/process group so a timeout can signal the whole tree via killpg,
            # not just this one PID. Windows has no equivalent POSIX process-group model here;
            # falls back to single-process kill below (matching the prior behavior on Windows).
            popen_kwargs["start_new_session"] = True
        proc = subprocess.Popen(cmd, **popen_kwargs)
    except Exception as e:
        return -1, "", str(e)
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        return proc.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        if sys.platform != "win32":
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                pass
        else:
            proc.kill()
        proc.communicate()  # reap the now-killed process; avoid leaving a zombie
        return -9, "", (f"Stage exceeded its {timeout}s wall-clock timeout and was killed "
                        f"as a process group (set TROPIC_STAGE_TIMEOUT to adjust).")
    except Exception as e:
        return -1, "", str(e)

def dry_run():
    print("=== PIPELINE ENVIRONMENT DRY-RUN ===")
    
    # Check Directories
    dirs = ["01_source_data", "04_analysis_datasets/programs/sas", "04_analysis_datasets/programs/r", "04_analysis_datasets/adam", 
            "06_qc_evidence/reconciliation", "platform", "03_metadata/define", "07_reviewer_explanation/guides", "05_outputs/tfl"]
    for d in dirs:
        status = "OK" if os.path.isdir(d) else "MISSING (Will be created)"
        print(f"  Directory: {d:20} -> {status}")
        
    # Check Rscript Executable. os.path.exists() alone is wrong for a bare command name like
    # "Rscript" (the PATH-reliant fallback) -- it checks cwd-relative existence, not PATH
    # resolution, so shutil.which() must be tried first.
    if shutil.which(RSCRIPT_PATH) or os.path.exists(RSCRIPT_PATH):
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
    print(f"Reverting {BACKUP_SCOPE} to pre-run backup state...")
    try:
        if restore_backup():
            print(f"Rollback executed successfully ({BACKUP_SCOPE} reverted). "
                  "NOTE: this does not cover 03_metadata/define/ or 08_submission_package/m5/ -- "
                  "package_ectd.py rebuilds that package tree from scratch on its next successful run "
                  "regardless of what this backup covers.")
        else:
            print(f"  [WARNING] No backup snapshot found; nothing to restore. {BACKUP_SCOPE} "
                  "are UNCHANGED from before this call, NOT reverted to a prior state -- "
                  "this is not the same as a successful rollback.")
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
# config/study_manifest.yaml declares the reconciled datasets and the study identity so
# they are no longer hardcoded here. A missing/malformed manifest falls back to the
# legacy TROPIC values, so the engine never hard-fails on a manifest problem.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# The engine lives at the repo root (parent of platform/). The default study IS
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
    root so the engine's relative paths (04_analysis_datasets/adam/, 04_analysis_datasets/programs/r/, config/study_config.yaml,
    config/study_manifest.yaml) resolve per-study, and set _RELOCATE_ENGINE so shared engine
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


def _probe_sas_version(sas):
    """Resolved SAS version string via &sysvlong, the same %put-probe pattern as
    _resolve_oda_root right below. sas.submit()'s LOG only ever contains the output of the
    code just submitted, never the session's own startup banner -- so a log-banner regex (as
    used for 'local' mode, where SAS is launched fresh as a subprocess and the banner genuinely
    appears in its own log) can never work for an already-open 'oda' session. This is the only
    reliable way to capture the SAS version actually used for an oda run (roadmap item 5)."""
    log = sas.submit("%put TROPIC_SAS_VER=&sysvlong.;").get("LOG", "")
    for line in log.splitlines():
        if "TROPIC_SAS_VER=" in line and "%put" not in line and "&sysvlong" not in line:
            ver = line.split("TROPIC_SAS_VER=", 1)[1].strip()
            if ver:
                return ver
    return None


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
        val_file, prod_file = f"04_analysis_datasets/adam/{ds}_v.xpt", f"04_analysis_datasets/adam/{ds}_prod.xpt"
        if os.path.exists(val_file):
            tmp_file = prod_file + ".part"
            with open(val_file, "rb") as fs, open(tmp_file, "wb") as fd:
                fd.write(fs.read())
            os.replace(tmp_file, prod_file)  # atomic promotion: never leave a truncated *_prod.xpt
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
        val_file, prod_file = f"04_analysis_datasets/adam/{ds}_v.xpt", f"04_analysis_datasets/adam/{ds}_prod.xpt"
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
    wall-clock budget (~60 s expected/attempt); TROPIC_ODA_MAX_WAIT sets it directly. A malformed
    override falls back to TROPIC_ODA_MAX_WAIT/default with a warning, not an uncaught crash."""
    retries_raw = os.environ.get("TROPIC_ODA_RETRIES")
    if retries_raw:
        try:
            return max(60, int(retries_raw) * 60)
        except ValueError:
            print(f"  [WARNING] TROPIC_ODA_RETRIES={retries_raw!r} is not a valid integer; "
                  "ignoring and falling back to TROPIC_ODA_MAX_WAIT/default.")
    return _env_int("TROPIC_ODA_MAX_WAIT", 3600)


def _atomic_download(sas, local_path, remote_path):
    """sas.download() into a .part sibling, then os.replace() into local_path (roadmap Move 3).

    saspy's .download() writes directly to local_path; a killed transfer (network drop, exec
    timeout, SIGKILL teardown) can leave a truncated file there that the provenance guard's
    byte-distinctness check cannot tell apart from a genuine, complete download. os.replace() is
    atomic on both POSIX and Windows, so local_path only ever exists as the old file or the
    complete new one, never a partial write."""
    tmp_path = local_path + ".part"
    sas.download(tmp_path, remote_path)
    os.replace(tmp_path, local_path)


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

    preflight = oda_broker.preflight()
    if not preflight["oda_preflight_ok"]:
        missing = ", ".join(preflight["oda_preflight_missing"])
        return 1, "", f"ODA preflight failed: {missing}", {
            "oda_last_error_class": "PREFLIGHT", "reconciliation": "none", **preflight}

    # ---- Resilient, probe-verified connect (broker rides spawner timeouts) ----
    try:
        conn = oda_broker.connect(max_wait_s=_oda_max_wait())
    except oda_broker.OdaFatal as e:
        return 1, "", f"ODA fatal ({e.error_class}): {e}", {
            "oda_last_error_class": e.error_class, "reconciliation": "none"}
    except oda_broker.OdaExhausted as e:
        meta = {
            "fell_back_to_sim": True, "oda_last_error_class": e.last_class,
            "oda_attempts": e.attempts,
            "next_recommended_window": oda_broker.recommend_window(),
            "reconciliation": "sim_only"}
        meta.update(preflight)
        return 0, "ODA exhausted; honest sim fallback", "", meta

    sas = conn.sas
    proj_root_oda = _resolve_oda_root(sas, PROJ_ROOT_ODA)
    sas_version = _probe_sas_version(sas)  # roadmap item 5; best-effort, never gates the run
    PGMDIR_ODA = f"{proj_root_oda}/04_analysis_datasets/programs/sas"
    ADAM_ODA = f"{proj_root_oda}/04_analysis_datasets/adam"
    # Execution-phase deadline: connect()'s budget only covers the spawn; a wedged server-side
    # workspace would otherwise block submit() forever. On a hit we force-reap (SIGKILL) the
    # local gateway instead of leaking a CPU-burning zombie. Default 30 min for the full suite.
    exec_timeout = _env_int("TROPIC_ODA_EXEC_TIMEOUT", 1800)
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
                               f"python3 platform/seed_sdtm.py  — or re-run with "
                               f"--seed-if-needed for a single-session seed+run."), {
                    "reconciliation": "none"}
            print(f"  [ODA] SDTM verified resident (manifest {manifest_sha[:12]}).")

        # ---- Upload SAS programs (tiny; always ship the latest code) ----
        print("  [ODA] Uploading SAS programs...")
        for remote_dir in (PGMDIR_ODA, ADAM_ODA, f"{ADAM_ODA}/sdtm_mapped"):
            if not seed_sdtm._ensure_remote_dir(sas, remote_dir):
                return 2, "", f"Could not create required ODA directory: {remote_dir}", {
                    "oda_endpoint": conn.endpoint, "reconciliation": "none"}
        for f in sorted(_glob.glob("04_analysis_datasets/programs/sas/*.sas")):
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
            with open("04_analysis_datasets/programs/sas/oda_master_driver.log", "w", encoding="utf-8") as _lf:
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
            _atomic_download(sas, f"04_analysis_datasets/adam/{ds}_prod.xpt", f"{ADAM_ODA}/{ds}_prod.xpt")

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
            if os.path.exists("04_analysis_datasets/adam/tte_stats_prod.csv"):
                os.remove("04_analysis_datasets/adam/tte_stats_prod.csv")
        else:
            _atomic_download(sas, "04_analysis_datasets/adam/tte_stats_prod.csv", f"{ADAM_ODA}/tte_stats_prod.csv")
            print("  [ODA] Downloaded SAS analysis statistics (tte_stats_prod.csv).")

        meta_out = {
            "oda_endpoint": conn.endpoint, "oda_attempts": conn.attempts,
            "oda_total_wait_s": conn.total_wait_s, "sdtm_manifest_sha": manifest_sha,
            "reconciliation": "SAS_vs_R", "probe_nonce_echoed": conn.probe_nonce_echoed,
            "sas_version": sas_version}
        meta_out.update(preflight)
        meta_out.update(conn.failover_status)
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
    rc, stdout, stderr = run_command(stage["cmd"], timeout=STAGE_TIMEOUT_S)
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
            print("  [REAL SAS] Compiling SAS production master suite (04_analysis_datasets/programs/sas/00_master_driver.sas)...")
            sas_cmd = [sas_exe, "-sysin", "04_analysis_datasets/programs/sas/00_master_driver.sas", "-log", "04_analysis_datasets/programs/sas/00_master_driver.log", "-print", "04_analysis_datasets/programs/sas/00_master_driver.lst"]
            rc, stdout, stderr = run_command(sas_cmd, timeout=STAGE_TIMEOUT_S)
            if rc == 0:
                print("  [REAL SAS] Master driver executed successfully. Actual SAS XPTs generated.")
            else:
                print("  [REAL SAS FAILED] SAS master execution failed! Check log: 04_analysis_datasets/programs/sas/00_master_driver.log")
            return rc, stdout, stderr
        elif sas_mode == "cached":
            print("  [CACHED SAS] Reconciling against PRE-EXISTING *_prod.xpt (SAS not re-run this session).")
            missing_prod = [f"{ds}_prod.xpt" for ds in datasets
                            if not os.path.exists(f"04_analysis_datasets/adam/{ds}_prod.xpt")]
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
        return run_command(stage["cmd"], timeout=STAGE_TIMEOUT_S)

def run_single_stage(stage, from_stage, sas_mode, results):
    if stage["id"] < from_stage:
        # Record explicitly: omitted stages must never look like "not part of the DAG".
        # NOT_RUN = --from-stage skip (partial evidence). Distinct from SKIPPED
        # (stage ran, legitimately nothing to do, e.g. results recon in sim mode).
        print(f"Skipping Stage {stage['id']}: {stage['name']}")
        results[stage["name"]] = "NOT_RUN"
        return True

    print(f"Executing Stage {stage['id']}: {stage['name']}...")
    _cache_dry_run_check(stage)

    rc, stdout, stderr = run_stage_execution(stage, sas_mode)

    # Post-execution gates are keyed by stage NAME, not by a positional id, so
    # inserting/renumbering a stage can never silently detach a gate from the step it
    # guards (audit C-3: the M-4 sanity gate had drifted off the TFL stage onto packaging).
    stage_status_override = None

    # Document/control locks promoted to runtime stages (phase 2).
    for gate_name, status_path in (
        ("Governance Scope Lock (G00)", "06_qc_evidence/gates/g00_governance_status.json"),
        ("Analysis Specification Lock (G02)", "06_qc_evidence/gates/g02_specification_status.json"),
        ("Reviewer Package Lock (G07)", "06_qc_evidence/gates/g07_reviewer_package_status.json"),
    ):
        if stage["name"] == gate_name and rc == 0:
            try:
                with open(status_path) as sf:
                    gate = json.load(sf)
                if gate.get("status") != "PASS":
                    rc = 1
                    stderr = (
                        f"{gate_name} status is {gate.get('status')!r}; "
                        f"problems={gate.get('problems', [])[:5]}"
                    )
            except (FileNotFoundError, json.JSONDecodeError) as exc:
                rc = 1
                stderr = f"{gate_name} status unreadable at {status_path}: {exc}"

    if stage["name"] == "Cross-Language Audit Reconcile" and rc == 0:
        status_path = "platform/reconciliation_status.json"
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

    # T1 third-engine gate: admiral must reconcile the scoped ADSL/OS/PFS core to SAS prod.
    # not_available is a FAIL when this stage is in the DAG (no silent skip of T1 evidence).
    if stage["name"] == "Admiral Core Reconciliation" and rc == 0:
        status_path = "platform/admiral_reconciliation_status.json"
        try:
            with open(status_path) as sf:
                adm = json.load(sf)
            overall = adm.get("overall")
            if overall != "PASS":
                rc = 1
                stderr = (
                    f"Admiral reconciliation did not pass (overall='{overall}'). "
                    "T1 third-engine evidence is required when this stage is orchestrated."
                )
        except (FileNotFoundError, json.JSONDecodeError):
            rc = 1
            stderr = "Admiral reconciliation status file missing or unreadable."

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
            with open("platform/results_reconciliation_status.json") as sf:
                overall = json.load(sf).get("overall")
            if overall == "not_available":
                stage_status_override = "SKIPPED"
            elif overall not in ("PASS", None):
                rc = 1
                stderr = f"Results reconciliation did not pass (overall='{overall}')."
        except (FileNotFoundError, json.JSONDecodeError):
            stage_status_override = "SKIPPED"

    # Figure-data reconciliation requires the SAS figure exports. Keep a data-free or
    # incomplete figure-render run visible as SKIPPED rather than recording a false PASS;
    # the release manifest independently requires an actual PASS for release promotion.
    if stage["name"] == "Figure-Data Reconciliation (SAS vs R)" and rc == 0:
        try:
            with open("platform/figure_data_reconciliation_status.json") as sf:
                overall = json.load(sf).get("overall")
            if overall == "not_available":
                stage_status_override = "SKIPPED"
            elif overall != "PASS":
                rc = 1
                stderr = f"Figure-data reconciliation did not pass (overall='{overall}')."
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
        script_path = f"04_analysis_datasets/programs/r/{d['val']}"
        stages.append({"name": label,
                       "cmd": _stage_cmd(script_path, "logrx"),
                       "parallel": "parallel_group" in d, "gated": False,
                       "script": script_path})  # roadmap Move 4: dry-run cache key input
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
        results[s["name"]] = "NOT_RUN"
    parallel_stages = [s for s in batch if s["id"] >= from_stage]
    if not parallel_stages:
        return
    print(f"Fanning out Stage(s) {', '.join(str(s['id']) for s in parallel_stages)} in parallel...")
    for s in parallel_stages:
        print(f"Executing Stage {s['id']}: {s['name']} (parallel)...")
        # Computed in the PARENT process: ProcessPoolExecutor workers are separate processes,
        # so a cache key recorded inside the worker would never reach _STAGE_CACHE_KEYS here.
        _cache_dry_run_check(s)
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

    # The pipeline DAG is generated from config/study_manifest.yaml (I/J Phase 1) rather than
    # hardcoded here. The manifest is required to run the pipeline; a load failure is a
    # hard error (the soft fallback above only covers banner/ODA-path resilience). Computed
    # here, ahead of the stale-file check below, so that check can use the SAS Production
    # stage's REAL id instead of a hardcoded number that silently drifts for any manifest
    # whose pre-infra/dataset count differs from the default TROPIC layout.
    if _MANIFEST is None:
        print("  [ERROR] config/study_manifest.yaml could not be loaded; cannot build the pipeline DAG.")
        sys.exit(1)
    stages = build_stages(_MANIFEST, _ENGINE_ROOT, _RELOCATE_ENGINE)

    # M-1: a stale SAS analysis-stats file must not pollute a non-ODA run's results
    # reconciliation; it is (re)produced only by a real ODA Stage-10 execution. Compared
    # against the SAS Production stage's actual id (not a hardcoded 10, which predates
    # build_stages() and silently compares against the wrong number for any --study whose
    # manifest has a different pre-infra/dataset count than the default TROPIC layout).
    sas_stage_id = next(s["id"] for s in stages if s["cmd"] == "SIMULATE")
    if from_stage <= sas_stage_id and os.path.exists("04_analysis_datasets/adam/tte_stats_prod.csv"):
        os.remove("04_analysis_datasets/adam/tte_stats_prod.csv")

    # Engine scripts (lint, config-gen) are invoked by absolute engine-root path so they
    # run regardless of the active study's CWD; both scan/emit relative to the CWD (the
    # active study root), so they remain per-study correct.
    lint_py = os.path.join(_ENGINE_ROOT, "platform", "lint_sas.py")
    config_py = os.path.join(_ENGINE_ROOT, "platform", "generate_config.py")
    renv_check_py = os.path.join(_ENGINE_ROOT, "platform", "check_renv_lock.py")

    # Run SAS static-analysis pre-flight gate (advisory; blocks only on hardcoded paths).
    print("  [LINT] Running SAS static analysis...")
    rc_lint, stdout_lint, stderr_lint = run_command([sys.executable, lint_py])
    if rc_lint != 0:
        print(f"  [LINT FAILED] Blocking SAS static-analysis error(s):\n{stdout_lint}\n{stderr_lint}")
        sys.exit(1)
    else:
        print("  [LINT] SAS static analysis passed (no blocking errors).")

    # Run the renv.lock version-drift gate (blocking; activate_renv.R only installs a MISSING
    # package, so it never catches a locally-installed package silently drifting from renv.lock).
    print("  [RENV] Checking installed R packages against renv.lock...")
    rc_renv, stdout_renv, stderr_renv = run_command([sys.executable, renv_check_py, RSCRIPT_PATH])
    print(stdout_renv, end="")
    if rc_renv != 0:
        print(f"  [RENV FAILED] {stderr_renv}")
        sys.exit(1)

    # Run the configuration generator
    print("  [CONFIG] Generating configuration from config/study_config.yaml...")
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

    # F-6 guard: run_single_stage() implements post-execution QC gate logic keyed on
    # these exact stage names. A study legitimately may use a subset of them (e.g. a stub
    # study with no TFL/results-recon), so the check is: fail loudly if the manifest marks
    # a stage `gated` that the engine has NO gate logic for — a rename/typo that would
    # otherwise run silently ungated (the C-3 regression class).
    implemented_gates = {
        "Governance Scope Lock (G00)",
        "Analysis Specification Lock (G02)",
        "Cross-Language Audit Reconcile",
        "Admiral Core Reconciliation",
        "Efficacy & Safety TFL Suite Compilation",
        "Numerical Results Reconciliation (SAS vs R)",
        "Reviewer Package Lock (G07)",
    }
    unimplemented_gates = {s["name"] for s in stages if s.get("gated")} - implemented_gates
    if unimplemented_gates:
        raise RuntimeError(
            "Gate wiring error: manifest marks stage(s) gated with no engine gate logic "
            f"(a rename detached a QC gate): {sorted(unimplemented_gates)}"
        )

    # run_parallel_batch() has NONE of run_single_stage()'s name-keyed post-execution gate
    # logic, so a stage marked BOTH gated and parallel would run through the pool and its gate
    # would silently never fire -- exactly the C-3 regression class the check above guards
    # against, from the other direction.
    gated_and_parallel = sorted(s["name"] for s in stages if s.get("gated") and s.get("parallel"))
    if gated_and_parallel:
        raise RuntimeError(
            "Gate wiring error: stage(s) marked BOTH gated and parallel -- run_parallel_batch() "
            f"has no gate logic to run them through, so the gate would silently never fire: "
            f"{gated_and_parallel}"
        )

    # Taken unconditionally, regardless of --from-stage: a backup keyed to "only if stage 1
    # actually runs" silently never fires on a partial (--from-stage N>1) run, so a later
    # failure's rollback finds no BACKUP_DIR and no-ops -- the worst failure mode, a control
    # that reports success while doing nothing.
    create_backup()

    results = {}
    expected_stage_names = [s["name"] for s in stages]

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
            if stage["name"] == "Release Run Manifest Binding" and stage["id"] >= from_stage:
                # The release manifest hashes pipeline_health.json as a current-run QC
                # verdict. Write telemetry for completed UPSTREAM stages only — exclude
                # this stage from expected so run_scope is full_dag when 1..(N-1) all ran
                # (otherwise the not-yet-run release stage forces partial_dag and the
                # seal incorrectly self-blocks).
                upstream_expected = [
                    n for n in expected_stage_names
                    if n != "Release Run Manifest Binding"
                ]
                write_telemetry(results, sas_mode, expected_stage_names=upstream_expected)
            run_single_stage(stage, from_stage, sas_mode, results)
            idx += 1

    clean_backup()
    # Always seal the full stage map (PASS / SKIPPED / NOT_RUN / FAIL), including the
    # release-manifest stage itself. Partial --from-stage runs are therefore visible
    # rather than silently under-counted as a "15-stage green" pipeline.
    write_telemetry(results, sas_mode, expected_stage_names=expected_stage_names)
    # Re-bind the release manifest against FINAL full_dag health. Stage 30 itself ran
    # against pre-stage health; without this re-seal, a green full DAG still seals as
    # REMEDIATION(partial) from the intermediate write.
    if results.get("Release Run Manifest Binding") in {"PASS", "REMEDIATION"} or (
        any(s["name"] == "Release Run Manifest Binding" and s["id"] >= from_stage for s in stages)
        and results.get("Release Run Manifest Binding") != "FAIL"
        and results.get("Release Run Manifest Binding") != "NOT_RUN"
    ):
        rc_rm, out_rm, err_rm = run_command(
            ["python3", "platform/build_release_run_manifest.py"],
            timeout=STAGE_TIMEOUT_S,
        )
        if rc_rm == 0:
            print("  [RELEASE SEAL] Release-run manifest re-bound against final pipeline_health.")
        else:
            # Non-zero is OK for REMEDIATION (dirty tree); FAIL binding is not.
            # build_release_run_manifest exits 0 on REMEDIATION and 1 only on FAIL.
            print(f"  [RELEASE SEAL] Re-bind finished with exit {rc_rm}: {(err_rm or out_rm).strip()[:200]}")
    print("All clinical pipeline stages compiled successfully!")

def update_define_timestamp():
    # Audit Mi-02 fix: AsOfDateTime is restamped ONLY when the metadata content
    # actually changes (content hashed with the timestamp normalised out), not on
    # every build. A timestamp that mutates each run is misleading provenance and
    # produces spurious git churn / Part-11 audit-trail noise.
    import hashlib
    define_path = "03_metadata/define/define.xml"
    hash_path = "platform/define_content.sha"
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


_STAGE_CACHE_FILE = "platform/stage_cache.json"
_STAGE_CACHE_STAGING_DIR = "01_source_data/real_sdtm/staging"
_STAGE_CACHE_KEYS = {}   # this run's computed keys, merged into _STAGE_CACHE_FILE by write_telemetry
_PRIOR_STAGE_CACHE = None  # lazily loaded once per process; see _get_prior_stage_cache()


def _stage_cache_key(script_path):
    """SHA256 over a validation script's own source + every staged SDTM .rds file it could read
    + the shared config every validation script sources (roadmap Move 4, dry-run only).

    Deliberately broad rather than parsing each script's own readRDS() calls to enumerate its
    true inputs: any staging file changing invalidates every dataset's key. A false cache MISS
    (a stage that would report unchanged, but doesn't, so it just re-runs) is always safe in a
    regulated pipeline; a false cache HIT never is, so the key is over- not under-inclusive."""
    import hashlib
    h = hashlib.sha256()
    paths = [script_path, "04_analysis_datasets/programs/r/config_study.R"]
    if os.path.isdir(_STAGE_CACHE_STAGING_DIR):
        paths += sorted(os.path.join(_STAGE_CACHE_STAGING_DIR, f)
                        for f in os.listdir(_STAGE_CACHE_STAGING_DIR))
    for p in paths:
        if os.path.exists(p):
            with open(p, "rb") as f:
                h.update(f.read())
        else:
            h.update(b"MISSING:" + p.encode("utf-8"))
    return h.hexdigest()


def _get_prior_stage_cache(path=_STAGE_CACHE_FILE):
    """Cache keys recorded for stages that PASSED on a previous run. Loaded once per process
    (module-level, mirroring the _ODA_OUTCOME pattern already used in this file)."""
    global _PRIOR_STAGE_CACHE
    if _PRIOR_STAGE_CACHE is None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                _PRIOR_STAGE_CACHE = json.load(f)
        except (OSError, json.JSONDecodeError):
            _PRIOR_STAGE_CACHE = {}
    return _PRIOR_STAGE_CACHE


def _cache_dry_run_check(stage):
    """Roadmap Move 4 (DRY-RUN ONLY): report whether this stage's inputs are unchanged since its
    last GREEN run, without skipping execution -- the stage always still runs. This only adds a
    '[CACHE]' log line and records this run's key so a future authoritative mode has an accurate
    baseline to validate against before it is ever allowed to actually skip a stage."""
    script_path = stage.get("script")
    if not script_path:
        return
    key = _stage_cache_key(script_path)
    _STAGE_CACHE_KEYS[stage["name"]] = key
    if _get_prior_stage_cache().get(stage["name"]) == key:
        print(f"  [CACHE] Stage {stage['id']}: {stage['name']} -- inputs unchanged since last "
              "GREEN run (dry-run only; executing anyway).")


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
    targets = sorted(glob.glob("05_outputs/tfl/output/tables/*.txt")
                     + glob.glob("05_outputs/tfl/output/listings/*.txt"))
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

HEALTH_LOG = "platform/pipeline_health_log.jsonl"


def _append_health_log(record, log_path=HEALTH_LOG):
    """Append a hash-chained entry to the append-only run log (roadmap Move 1).

    pipeline_health.json is overwritten every run, so it carries no run history, and git log is
    not a tamper-evident audit trail (a rebase/force-push can rewrite it). Each entry here embeds
    sha256 of the previous entry's exact bytes, so editing or deleting any prior line breaks every
    chain hash after it. Reuses the sha256 primitive already used by update_define_timestamp() and
    the append-only JSONL pattern already used by oda_broker.log_attempt().
    """
    import hashlib
    prev_hash = "0" * 64
    try:
        with open(log_path, "rb") as f:
            for line in f:
                line = line.strip()
                if line:
                    prev_hash = hashlib.sha256(line).hexdigest()
    except OSError:
        pass
    entry = dict(record)
    entry["prev_hash"] = prev_hash
    line_bytes = json.dumps(entry, sort_keys=True).encode("utf-8")
    with open(log_path, "ab") as f:
        f.write(line_bytes + b"\n")


def _r_version(rscript=None):
    """Best-effort R version string via Rscript itself (roadmap item 5). R runs every session
    regardless of sas_mode, so this is always available, unlike the SAS version below. Never
    raises -- telemetry writing must not fail because the environment probe did."""
    try:
        out = subprocess.run([rscript or RSCRIPT_PATH, "-e", "cat(R.version.string)"],
                             capture_output=True, text=True, timeout=30)
        return out.stdout.strip() or None
    except Exception:
        return None


def _renv_lock_sha(path="renv.lock"):
    """SHA256 of the committed renv.lock content, so a per-run telemetry record can be checked
    against a specific locked environment without re-parsing/re-diffing the whole file."""
    import hashlib
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


def _sas_version_from_log(log_path):
    """Best-effort SAS version extraction from the standard startup NOTE banner SAS itself
    writes at the top of every log (e.g. 'NOTE: SAS (r) Proprietary Software Release 9.4
    (TS1M8)'), so this works uniformly for both the oda and local execution logs without a
    separate ODA round-trip. Returns None if the log is absent or the banner isn't found --
    never raises."""
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            head = f.read(4000)  # the banner is always in the first few lines
    except OSError:
        return None
    m = re.search(r"SAS \(r\) Proprietary Software Release ([^\r\n]+)", head)
    return m.group(1).strip() if m else None


def write_telemetry(results, sas_mode="sim", expected_stage_names=None):
    import platform
    # A legitimately SKIPPED stage (e.g. results-reconciliation in sim/cached mode) does
    # not turn the pipeline RED; only a real FAIL does. NOT_RUN (partial --from-stage)
    # also keeps GREEN so remediation runs remain usable, but run_scope marks incompleteness.
    health_status = "RED" if any(v == "FAIL" for v in results.values()) else "GREEN"

    # Update define.xml timestamp if the build succeeds (Mi-02)
    if health_status == "GREEN":
        update_define_timestamp()

    expected = list(expected_stage_names) if expected_stage_names else list(results.keys())
    not_run = [n for n in expected if results.get(n) == "NOT_RUN" or n not in results]
    run_scope = "full_dag" if not not_run else "partial_dag"

    health = {
        "timestamp": datetime.now().isoformat(),
        "runner": f"{getpass.getuser()} (System Agent)",
        "pipeline_health_status": health_status,
        "sas_execution_mode": sas_mode,
        "schema_version": "run_scope_v1",
        "run_scope": run_scope,
        "stages_expected": len(expected),
        "stages_recorded": len(results),
        "stages_not_run": not_run,
        "stages": results
    }

    # Environment capture (roadmap item 5): a reviewer's first question about any validation
    # pipeline is "reproducible on what?". R runs every session, so its version + the locked
    # environment's hash are always recorded here; sas_version is filled in below once the
    # effective sas_mode (post ODA-fallback) is known.
    health["r_version"] = _r_version()
    health["renv_lock_sha256"] = _renv_lock_sha()

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
        with open("platform/reconciliation_status.json") as _rf:
            health["reconciliation_status"] = json.load(_rf).get("overall")
    except (OSError, json.JSONDecodeError):
        pass
    # Results-level (analysis statistics) reconciliation verdict, if Stage 13 wrote one.
    try:
        with open("platform/results_reconciliation_status.json") as _rrf:
            health["results_reconciliation_status"] = json.load(_rrf).get("overall")
    except (OSError, json.JSONDecodeError):
        pass

    # Provenance guard (audit C-1): a recorded 'oda'/'local' mode asserts an independent SAS
    # run, whose on-disk signature is *_prod.xpt byte-DISTINCT from *_v.xpt. If any prod file
    # is byte-identical to (or missing vs) its R validation pair, the asserted evidence is not
    # present, so we refuse to record a clean real-SAS GREEN and flip the health to RED. This
    # makes the flag uncheatable by a restamped green snapshot.
    #
    # NOTE (audit F-14): this is a RUNTIME control, evaluated against the on-disk XPT produced by
    # THIS run. On a data-free clone (no 04_analysis_datasets/adam/*_prod.xpt or *_v.xpt present) the byte-distinct
    # check skips every dataset and _sdtm_manifest_binding accepts "not recomputable", so the guard
    # passes VACUOUSLY. It therefore is not a re-verifiable static attestation of an already-committed
    # pipeline_health.json; the durable, independently-checkable artifact is the committed
    # platform/evidence/xpt_md5_manifest.txt (per-dataset md5 of the proved byte-distinct run).
    effective_mode = health["sas_execution_mode"]

    # SAS version (roadmap item 5): only obtainable when SAS actually ran this session.
    # 'oda' mode already has it via _probe_sas_version() -> _ODA_OUTCOME -> merged above --
    # do NOT touch it here, since sas.submit()'s LOG never contains the session's startup
    # banner (that clobbered a correct value with None until this was caught on a real run).
    # 'local' mode genuinely can use the log-banner approach: a fresh subprocess SAS writes
    # its own startup banner into its own -log file from the first line.
    if effective_mode == "local":
        health["sas_version"] = _sas_version_from_log("04_analysis_datasets/programs/sas/00_master_driver.log")

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

    os.makedirs("platform", exist_ok=True)
    with open("platform/pipeline_health.json", "w", encoding="utf-8") as f:
        json.dump(health, f, indent=2)
    _append_health_log(health)

    # Roadmap Move 4 (dry-run only): carry forward this run's cache key ONLY for stages that
    # actually PASSed. A FAILed stage's key is dropped, never carried forward -- a stale/failed
    # key must never later read as "unchanged since last GREEN run".
    if _STAGE_CACHE_KEYS:
        stage_cache = _get_prior_stage_cache()
        for name, key in _STAGE_CACHE_KEYS.items():
            if results.get(name) == "PASS":
                stage_cache[name] = key
            else:
                stage_cache.pop(name, None)
        with open(_STAGE_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(stage_cache, f, indent=2, sort_keys=True)

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
    with open("platform/health_dashboard.md", "w", encoding="utf-8") as f:
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
