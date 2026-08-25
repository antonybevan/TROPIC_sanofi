#!/usr/bin/env python3
"""
materialize_ectd.py — populate the eCTD sequence so every backbone leaf resolves in-place.

`build_ectd_backbone.py` writes `08_submission_package/ectd/0000/index.xml` with one <leaf> per deliverable —
each carries the canonical sequence-relative `xlink:href` and the real MD5 `checksum` of the
source file in the repo `08_submission_package/m5/` tree. This tool reads that manifest and copies each source to its
href location under `08_submission_package/ectd/0000/`, then re-verifies the copy's MD5 against the recorded
checksum. Backbone components already written in-sequence (us-regional.xml, stf-tropic.xml) are
verified in place. Idempotent: re-running only re-verifies unless a file is missing.

The materialized payload (datasets + report binaries) is a reproducible copy and is git-ignored
(see .gitignore); the backbone XML, STF, regional metadata, and this record stay tracked.

Usage:  python3 platform/materialize_ectd.py
"""
import os, re, sys, json
from pathlib import Path

from build_ectd_backbone import SUPPORT_FILES
from safe_filesystem import (
    UnsafePathError,
    atomic_write_json,
    canonical_posix_relative,
    contained_path,
    digest_file,
    read_text as safe_read_text,
    regular_file_exists,
    require_directory,
    require_regular_file,
    require_tree_no_symlinks,
    safe_chmod,
    safe_copy_file,
    safe_makedirs,
    safe_stat,
    safe_unlink,
    walk_regular_files,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PACKAGE_ROOT = ROOT / "08_submission_package"
M5_ROOT = PACKAGE_ROOT / "m5"
ECTD_ROOT = PACKAGE_ROOT / "ectd"
SEQ = ECTD_ROOT / "0000"
INDEX = SEQ / "index.xml"
CACHE_FILE = HERE / ".materialize_ectd_cache.json"

def md5(path, root=SEQ):
    return digest_file(path, root, "md5")

def _require_contained(base, path, href):
    """Refuse lexical escapes and any linked root, ancestor, or leaf before use."""
    try:
        base_path = require_directory(base, base)
        candidate = Path(os.path.abspath(os.fspath(path)))
        relative = candidate.relative_to(base_path).as_posix()
        canonical_posix_relative(relative)
        contained_path(base_path, relative, allow_missing=True)
    except (UnsafePathError, ValueError) as exc:
        sys.exit(
            "REFUSING to materialize href outside its tree or through a link "
            f"(path-containment guard): {href!r}: {exc}"
        )

def _load_cache(path=None, root=None):
    path = Path(path) if path is not None else Path(CACHE_FILE)
    root = Path(root) if root is not None else Path(HERE)
    try:
        if not regular_file_exists(path, root):
            return {}
        return json.loads(safe_read_text(path, root))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}

def _save_cache(cache, path=None, root=None):
    path = Path(path) if path is not None else Path(CACHE_FILE)
    root = Path(root) if root is not None else Path(HERE)
    atomic_write_json(path, cache, root, mode=0o600)

def _verify_dest(dest, href, recorded, cache, root=SEQ):
    """MD5 of `dest`, using a (size, mtime, recorded-checksum) sidecar cache to skip a full
    re-hash when nothing that could change the answer has changed since the last time this exact
    href/recorded pair was verified (roadmap: fast-path re-verification). A change to EITHER the
    on-disk file (size/mtime drift) OR the recorded checksum itself (a new build re-generated
    index.xml with a different value for this href) always falls through to a real re-hash -- the
    cache can only ever save work on a provably-unchanged file verified against the SAME checksum,
    never skip verification on genuine uncertainty."""
    st = safe_stat(dest, root)
    entry = cache.get(href)
    if (entry and entry.get("recorded") == recorded.lower()
            and entry.get("size") == st.st_size and entry.get("mtime_ns") == st.st_mtime_ns):
        return entry["verified_md5"]
    actual = md5(dest, root)
    cache[href] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns,
                    "recorded": recorded.lower(), "verified_md5": actual}
    return actual

def purge_unindexed_sequence_files(leaves):
    """Remove every sequence file not indexed or explicitly required infrastructure.

    Submission directories commonly acquire ignored Finder/desktop files that Git
    status cannot see. Purging the complete sequence surface, rather than only m5,
    prevents those files and stale UTIL notes from reaching handoff media.
    """
    require_directory(SEQ, ECTD_ROOT)
    # Reject the root, ancestor, file, and directory link cases before the first
    # destructive operation.  os.walk(followlinks=False) alone is insufficient
    # when its starting path or an ancestor is linked.
    require_tree_no_symlinks(SEQ, ECTD_ROOT)
    indexed = {
        contained_path(SEQ, canonical_posix_relative(href), allow_missing=True)
        for href, _recorded in leaves
    }
    infrastructure = {
        contained_path(SEQ, rel, allow_missing=True)
        for rel in ("index.xml", "index-md5.txt", *SUPPORT_FILES.keys())
    }
    allowed = indexed | infrastructure
    purged = []
    for path in walk_regular_files(SEQ):
        _require_contained(SEQ, path, path.relative_to(SEQ).as_posix())
        if path not in allowed:
            safe_unlink(path, SEQ)
            purged.append(path.relative_to(SEQ).as_posix())
    parent_finder_file = ECTD_ROOT / ".DS_Store"
    if regular_file_exists(parent_finder_file, ECTD_ROOT):
        safe_unlink(parent_finder_file, ECTD_ROOT)
        purged.append("../.DS_Store")
    return sorted(purged)

def indexed_leaves(index_xml):
    """Return (href, checksum) for every indexed leaf with an MD5 checksum.

    Leaf attributes are not ordered in the eCTD backbone.  In particular, the
    Study Tagging File leaf carries a `version` attribute between `xlink:href`
    and `checksum-type`; parsing each leaf block avoids silently missing that
    sequence-authored file.
    """
    leaves = []
    for attrs in re.findall(r"<leaf\b([^>]*)>", index_xml, flags=re.S):
        href = re.search(r'xlink:href="([^"]+)"', attrs)
        ctype = re.search(r'checksum-type="MD5"', attrs)
        checksum = re.search(r'checksum="([0-9a-fA-F]+)"', attrs)
        if href and ctype and checksum:
            leaves.append((href.group(1), checksum.group(1)))
    return leaves


def main():
    require_regular_file(INDEX, SEQ)
    idx = safe_read_text(INDEX, SEQ)
    leaves = indexed_leaves(idx)
    if not leaves:
        sys.exit("No leaves with checksums found in index.xml")
    normalized_leaves = []
    for href, recorded in leaves:
        try:
            href = canonical_posix_relative(href)
        except UnsafePathError as exc:
            sys.exit(f"REFUSING non-canonical eCTD leaf href {href!r}: {exc}")
        if not re.fullmatch(r"[0-9a-fA-F]{32}", recorded):
            sys.exit(f"REFUSING invalid MD5 declaration for eCTD leaf {href!r}")
        normalized_leaves.append((href, recorded))
    leaves = normalized_leaves
    purged = purge_unindexed_sequence_files(leaves)
    if purged:
        print("REMOVED UNINDEXED SEQUENCE FILES:", *purged, sep="\n  ")
    cache = _load_cache()
    copied = verified = in_place = 0
    missing, mismatch = [], []
    for href, recorded in leaves:
        dest = contained_path(SEQ, href, allow_missing=True)
        if href.startswith("m5/"):
            src = contained_path(M5_ROOT, href[len("m5/"):], allow_missing=True)
            source_root = M5_ROOT
        else:
            src = dest
            source_root = SEQ
        _require_contained(SEQ, dest, href)
        _require_contained(source_root, src, href)
        # A dest that already matches the just-recorded checksum stays in place (backbone XML
        # authored in-sequence has no repo source and lands here). Otherwise (missing, or stale
        # from an earlier build whose XPT timestamps differ) re-copy from the repo source; the
        # previous logic trusted any existing dest and so failed verification on every re-run.
        destination_exists = regular_file_exists(dest, SEQ)
        if destination_exists and _verify_dest(dest, href, recorded, cache, SEQ) == recorded.lower():
            if dest.suffix.lower() in {".xpt", ".sas7bdat"}:
                safe_chmod(dest.parent, 0o700, SEQ, directory=True)
                safe_chmod(dest, 0o600, SEQ)
            in_place += 1
            verified += 1
            continue
        if not regular_file_exists(src, source_root):
            (mismatch if destination_exists else missing).append(href)
            continue
        safe_makedirs(dest.parent, SEQ)
        safe_copy_file(
            src,
            dest,
            source_root=source_root,
            destination_root=SEQ,
        )
        copied += 1
        if dest.suffix.lower() in {".xpt", ".sas7bdat"}:
            # Materialized patient-level transport files are local controlled artifacts, not a
            # public review surface.  Keep both the file and its dataset directory least-privilege.
            safe_chmod(dest.parent, 0o700, SEQ, directory=True)
            safe_chmod(dest, 0o600, SEQ)
        # Always a genuine re-hash here (never routed through the cache lookup): dest was just
        # written, so this is the one place correctness must not lean on a cached value at all.
        actual = md5(dest, SEQ)
        st = safe_stat(dest, SEQ)
        cache[href] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns,
                        "recorded": recorded.lower(), "verified_md5": actual}
        if actual == recorded.lower():
            verified += 1
        else:
            mismatch.append(href)
    _save_cache(cache)
    print(f"leaves={len(leaves)}  copied={copied}  already-in-place={in_place}  "
          f"MD5-verified={verified}/{len(leaves)}")
    if missing:  print("MISSING SOURCES:", *missing, sep="\n  ")
    if mismatch: print("MD5 MISMATCH:", *mismatch, sep="\n  ")
    if missing or mismatch:
        sys.exit(1)
    # G08 is a complete sequence-surface gate, not only a copy/checksum gate.
    # Import here to keep the materializer's leaf parser independently testable.
    from validate_ectd_sequence import validate_sequence
    sequence_result = validate_sequence(require_all_leaves=True)
    if sequence_result.get("status") != "PASS":
        print("eCTD COMPLETE-SURFACE VALIDATION FAILED:")
        for problem in sequence_result.get("problems", []):
            print(f"  - {problem}")
        sys.exit(1)
    print("OK — all leaves materialized and checksum-verified in 08_submission_package/ectd/0000/")
    print("OK — complete sequence inventory/support/XML/run-record validation passed (G08)")

if __name__ == "__main__":
    try:
        main()
    except UnsafePathError as exc:
        raise SystemExit(f"REFUSING unsafe eCTD materialization path: {exc}") from exc
