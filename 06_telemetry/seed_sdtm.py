"""
seed_sdtm.py — Job A: idempotent, integrity-checked SDTM seeding to ODA.

Why a separate job: re-streaming ~200 MB of SDTM over a loaded IOM link every run is itself a
timeout magnet, and a presence-only check lets a half-uploaded library masquerade as "resident".

Design (brief §4):
  1. Compute a LOCAL manifest: per dataset {sha256 (of bytes), nrows (best-effort)}.
  2. If a matching manifest is already on ODA -> ZERO upload, exit 0 (idempotent).
  3. Otherwise upload, RE-READ row counts back from ODA, verify, and only THEN write the manifest
     sentinel LAST (transactional: a partial upload leaves no/old manifest, so it fails verify).

The pure manifest logic (compute/compare) is independent of saspy so it is unit-testable; the ODA
I/O (download/submit/upload) is reached only through a session object and is injectable.

CLI:
    python3 06_telemetry/seed_sdtm.py            # idempotent: uploads only if manifest mismatches
    python3 06_telemetry/seed_sdtm.py --force    # override: re-upload regardless of manifest
"""
import os
import sys
import json
import glob
import hashlib
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, ".."))
SDTM_LOCAL = os.path.join(PROJECT_ROOT, "01_raw_source", "real_sdtm")
# ODA-side SDTM directory. No developer account id is hard-coded (roadmap #10): defaults to a
# ~/TROPIC layout resolved against the connecting account's $HOME; override via env if needed.
SDTM_ODA = os.environ.get(
    "TROPIC_ODA_SDTM_DIR",
    os.environ.get("TROPIC_ODA_PROJ_ROOT", "~/TROPIC") + "/01_raw_source/real_sdtm")
MANIFEST_NAME = "_tropic_sdtm_manifest.json"


def _resolve_oda_home(sas, path):
    """Expand a leading '~' against the connected ODA account's $HOME so no per-user absolute
    path is committed. Returns path unchanged if already absolute or $HOME cannot be read."""
    if "~" not in path:
        return path
    try:
        log = sas.submit("%put TROPIC_ODA_HOME=%sysget(HOME);").get("LOG", "")
        for line in log.splitlines():
            if "TROPIC_ODA_HOME=" in line and "%put" not in line and "%sysget" not in line:
                home = line.split("TROPIC_ODA_HOME=", 1)[1].strip()
                if home:
                    return path.replace("~", home, 1)
    except Exception:
        pass
    return path


def _ensure_remote_dir(sas, remote_dir):
    """mkdir -p the ODA target tree before any upload. SASPy's IOM upload to a NONEXISTENT
    remote directory spins on CPU indefinitely instead of erroring — and the dir genuinely is
    absent on a fresh account / after an ODA home-region change. ODA blocks the shell (X / CALL
    SYSTEM), so we build the tree level-by-level with the DCREATE function. Returns True on done."""
    segs = [s for s in remote_dir.split("/") if s]
    lines = ["options notes source;", "data _null_;"]
    parent = ""
    for s in segs:
        full = f"{parent}/{s}"
        lines.append(f'  if fileexist("{full}")=0 then _rc=dcreate("{s}","{parent}/");')
        parent = full
    lines.append(f'  _exist = fileexist("{remote_dir}");')
    lines.append(f'  put "TROPIC_MKDIR|" "{remote_dir}|" _exist;')
    lines.append("run;")
    log = sas.submit("\n".join(lines)).get("LOG", "")
    ok = any(l.strip().startswith("TROPIC_MKDIR|") and l.strip().endswith("|1")
               for l in log.splitlines())
    if not ok:
        print("--- MKDIR LOG START ---")
        print(log)
        print("--- MKDIR LOG END ---")
    return ok


def _sha256(path, _buf=1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(_buf), b""):
            h.update(chunk)
    return h.hexdigest()


def _local_nrows(path):
    """Best-effort row count via pyreadstat metadata (no full read). None if unavailable."""
    try:
        import pyreadstat
        _, meta = pyreadstat.read_sas7bdat(path, metadataonly=True)
        return int(meta.number_rows) if meta.number_rows is not None else None
    except Exception:
        return None


def compute_local_manifest(sdtm_dir=SDTM_LOCAL):
    """{'datasets': {name: {sha256, nrows}}, 'manifest_sha': <sha over dataset hashes>}."""
    datasets = {}
    for p in sorted(glob.glob(os.path.join(sdtm_dir, "*.sas7bdat"))):
        name = os.path.basename(p)
        datasets[name] = {"sha256": _sha256(p), "nrows": _local_nrows(p)}
    return {"version": 1, "datasets": datasets, "manifest_sha": manifest_sha(datasets)}


def manifest_sha(datasets):
    """Deterministic digest over the per-dataset sha256 values (order-independent)."""
    blob = ";".join(f"{n}:{d['sha256']}" for n, d in sorted(datasets.items()))
    return hashlib.sha256(blob.encode()).hexdigest()


def manifests_match(local, remote):
    """True iff every dataset sha256 matches (the remote library was seeded from THIS source)."""
    if not remote or "datasets" not in remote:
        return False
    lh = {n: d["sha256"] for n, d in local["datasets"].items()}
    rh = {n: d.get("sha256") for n, d in remote["datasets"].items()}
    return lh == rh and bool(lh)


def read_remote_manifest(sas, remote_dir=SDTM_ODA):
    """Download the ODA manifest sentinel and parse it. None if absent/unreadable."""
    remote_dir = _resolve_oda_home(sas, remote_dir)
    remote = f"{remote_dir}/{MANIFEST_NAME}"
    tmp = os.path.join(tempfile.gettempdir(), MANIFEST_NAME)
    try:
        sas.download(tmp, remote)
        with open(tmp, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def verify_resident(sas, sdtm_dir=SDTM_LOCAL, remote_dir=SDTM_ODA, local=None):
    """(ok, local_manifest_sha, reason). ok only if the ODA manifest matches the local source."""
    local = local or compute_local_manifest(sdtm_dir)
    if not local["datasets"]:
        return False, local["manifest_sha"], "no local SDTM found"
    remote = read_remote_manifest(sas, remote_dir)
    if remote is None:
        return False, local["manifest_sha"], "no manifest on ODA (library not seeded)"
    if not manifests_match(local, remote):
        return False, local["manifest_sha"], "ODA manifest mismatches local source (stale/partial)"
    return True, local["manifest_sha"], "resident and verified"


def _remote_nobs(sas, remote_dir=SDTM_ODA):
    """Re-read observation counts per member from ODA (post-upload integrity). {name: nobs}."""
    remote_dir = _resolve_oda_home(sas, remote_dir)
    code = f"""
libname _seed "{remote_dir}";
proc sql noprint;
  create table _nobs as select memname, nobs from dictionary.tables
    where libname='_SEED' and memtype='DATA';
quit;
data _null_; set _nobs; put "SEEDNOBS|" memname "|" nobs; run;
"""
    out = {}
    try:
        log = sas.submit(code).get("LOG", "")
    except Exception:
        return out
    for line in log.splitlines():
        if line.strip().startswith("SEEDNOBS|"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3 and parts[2].isdigit():
                out[parts[1].lower() + ".sas7bdat"] = int(parts[2])
    return out


def stale_members(local, remote, force=False):
    """Members whose sha256 differs from the ODA manifest (force / absent manifest => all).
    The ~200 MB IOM transfer is the pipeline's dominant cost, so a partial source refresh must
    ship only the changed datasets, not the whole library."""
    remote_sha = {} if (force or not remote) else {
        n: d.get("sha256") for n, d in remote.get("datasets", {}).items()}
    return sorted(n for n, d in local["datasets"].items() if remote_sha.get(n) != d["sha256"])


def seed(sas, sdtm_dir=SDTM_LOCAL, remote_dir=SDTM_ODA, force=False):
    """Idempotently ensure the SDTM library on ODA matches local, uploading ONLY the members
    whose sha256 differs from the ODA manifest (force => all). Returns a result dict."""
    remote_dir = _resolve_oda_home(sas, remote_dir)
    local = compute_local_manifest(sdtm_dir)
    if not local["datasets"]:
        return {"uploaded": 0, "skipped": 0,
                "manifest_sha": local["manifest_sha"], "status": "no-local-sdtm"}

    remote = None if force else read_remote_manifest(sas, remote_dir)
    if not force and manifests_match(local, remote):
        return {"uploaded": 0, "skipped": len(local["datasets"]),
                "manifest_sha": local["manifest_sha"], "status": "already-resident"}

    stale = stale_members(local, remote, force=force)
    if not _ensure_remote_dir(sas, remote_dir):
        return {"uploaded": 0, "status": "MKDIR_FAILED", "remote_dir": remote_dir,
                "manifest_sha": local["manifest_sha"]}
    up_mb = sum(os.path.getsize(os.path.join(sdtm_dir, n)) for n in stale) / 1_048_576
    print(f"  [SEED] Uploading {len(stale)}/{len(local['datasets'])} changed SDTM file(s) "
          f"({up_mb:.0f} MB) to ODA — IOM ~0.4 MB/s...", flush=True)
    for i, name in enumerate(stale, 1):
        f = os.path.join(sdtm_dir, name)
        print(f"  [SEED]   ({i}/{len(stale)}) {name} ({os.path.getsize(f)/1_048_576:.1f} MB)...",
              flush=True)
        sas.upload(f, f"{remote_dir}/{name}")

    # Integrity re-read: confirm row counts across the FULL library where known locally
    # (covers resident members too, not just this run's delta).
    nobs = _remote_nobs(sas, remote_dir)
    mismatches = []
    for name, d in local["datasets"].items():
        if d.get("nrows") is not None and name in nobs and nobs[name] != d["nrows"]:
            mismatches.append(f"{name}: local {d['nrows']} != ODA {nobs[name]}")
    if mismatches:
        return {"uploaded": len(stale), "status": "VERIFY_FAILED",
                "manifest_sha": local["manifest_sha"], "mismatches": mismatches}

    # Write the manifest sentinel LAST (transactional completeness marker).
    tmp = os.path.join(tempfile.gettempdir(), MANIFEST_NAME)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(local, f, indent=2)
    sas.upload(tmp, f"{remote_dir}/{MANIFEST_NAME}")
    try:
        os.remove(tmp)
    except OSError:
        pass
    return {"uploaded": len(stale), "skipped": len(local["datasets"]) - len(stale),
            "manifest_sha": local["manifest_sha"], "status": "seeded"}


def main(argv=None):
    import oda_broker
    argv = argv if argv is not None else sys.argv[1:]
    force = "--force" in argv or "--force-upload-sdtm" in argv
    if not glob.glob(os.path.join(SDTM_LOCAL, "*.sas7bdat")):
        print("  [SEED] No local SDTM (*.sas7bdat) found — nothing to seed.")
        return 1
    print("  [SEED] Connecting to ODA via broker (rides spawner timeouts)...")
    try:
        conn = oda_broker.connect(max_wait_s=int(os.environ.get("TROPIC_ODA_MAX_WAIT", 3600)))
    except oda_broker.OdaFatal as e:
        print(f"  [SEED] FATAL ({e.error_class}): {e}. Fix and re-run.")
        return 2
    except oda_broker.OdaExhausted as e:
        win = oda_broker.recommend_window()
        print(f"  [SEED] ODA unavailable after {e.attempts} attempts. "
              f"Try window: {win or 'unknown'}.")
        return 3
    try:
        res = seed(conn.sas, force=force)
        print(f"  [SEED] {res['status']}: {json.dumps(res)}")
        return 0 if res["status"] in ("seeded", "already-resident") else 4
    finally:
        oda_broker.teardown(conn.sas)


if __name__ == "__main__":
    sys.path.insert(0, HERE)  # allow `import oda_broker` when run as a script
    sys.exit(main())
