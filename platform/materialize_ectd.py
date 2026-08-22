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
import os, re, sys, json, hashlib, shutil

from build_ectd_backbone import SUPPORT_FILES

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SEQ = os.path.join(ROOT, "08_submission_package/ectd", "0000")
PACKAGE_ROOT = os.path.join(ROOT, "08_submission_package")
INDEX = os.path.join(SEQ, "index.xml")
CACHE_FILE = os.path.join(HERE, ".materialize_ectd_cache.json")

def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def _require_contained(base, path, href):
    """Refuse to touch a path that resolves outside `base` (roadmap: path-containment guard).
    index.xml is self-generated today, not external input, so this is defense against a future
    bug/hand-edit/merge artifact rather than a live threat -- but os.path.join happily returns an
    absolute href as-is (ignoring `base` entirely) or leaves a '../' traversal unresolved in the
    joined string, and both the copy step and purge_unindexed_sequence_files's os.remove() loop
    would otherwise trust that silently. os.path.commonpath does NOT resolve '..' components on
    its own -- on the raw os.path.join() result it compares path strings lexically, so
    '<base>/../../etc/hosts' lexically still starts with `base` and a naive commonpath check
    would wrongly pass it; os.path.normpath must run first to actually collapse '..' against the
    real preceding components before the comparison means anything. An explicit check (not a bare
    `assert`, which -O strips) turns a hypothetical traversal into an immediate, loud failure."""
    resolved = os.path.normpath(path)
    if os.path.commonpath([base, resolved]) != base:
        sys.exit(f"REFUSING to materialize href outside its tree (path-traversal guard): {href!r}")

def _load_cache(path=CACHE_FILE):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}

def _save_cache(cache, path=CACHE_FILE):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, sort_keys=True)

def _verify_dest(dest, href, recorded, cache):
    """MD5 of `dest`, using a (size, mtime, recorded-checksum) sidecar cache to skip a full
    re-hash when nothing that could change the answer has changed since the last time this exact
    href/recorded pair was verified (roadmap: fast-path re-verification). A change to EITHER the
    on-disk file (size/mtime drift) OR the recorded checksum itself (a new build re-generated
    index.xml with a different value for this href) always falls through to a real re-hash -- the
    cache can only ever save work on a provably-unchanged file verified against the SAME checksum,
    never skip verification on genuine uncertainty."""
    st = os.stat(dest)
    entry = cache.get(href)
    if (entry and entry.get("recorded") == recorded.lower()
            and entry.get("size") == st.st_size and entry.get("mtime_ns") == st.st_mtime_ns):
        return entry["verified_md5"]
    actual = md5(dest)
    cache[href] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns,
                    "recorded": recorded.lower(), "verified_md5": actual}
    return actual

def purge_unindexed_sequence_files(leaves):
    """Remove every sequence file not indexed or explicitly required infrastructure.

    Submission directories commonly acquire ignored Finder/desktop files that Git
    status cannot see. Purging the complete sequence surface, rather than only m5,
    prevents those files and stale UTIL notes from reaching handoff media.
    """
    indexed = {
        os.path.normpath(os.path.join(SEQ, href))
        for href, _recorded in leaves
    }
    infrastructure = {
        os.path.normpath(os.path.join(SEQ, rel))
        for rel in ("index.xml", "index-md5.txt", *SUPPORT_FILES.keys())
    }
    allowed = indexed | infrastructure
    if not os.path.isdir(SEQ):
        return []
    purged = []
    for root, _dirs, files in os.walk(SEQ):
        for name in files:
            path = os.path.normpath(os.path.join(root, name))
            _require_contained(SEQ, path, os.path.relpath(path, SEQ))
            if path not in allowed:
                os.remove(path)
                purged.append(os.path.relpath(path, SEQ))
    parent_finder_file = os.path.join(os.path.dirname(SEQ), ".DS_Store")
    if os.path.isfile(parent_finder_file):
        os.remove(parent_finder_file)
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
    with open(INDEX, encoding="utf-8") as f:
        idx = f.read()
    leaves = indexed_leaves(idx)
    if not leaves:
        sys.exit("No leaves with checksums found in index.xml")
    purged = purge_unindexed_sequence_files(leaves)
    if purged:
        print("REMOVED UNINDEXED SEQUENCE FILES:", *purged, sep="\n  ")
    cache = _load_cache()
    copied = verified = in_place = 0
    missing, mismatch = [], []
    for href, recorded in leaves:
        dest = os.path.join(SEQ, href)
        src = os.path.join(PACKAGE_ROOT, href) if href.startswith("m5/") else os.path.join(SEQ, href)
        _require_contained(SEQ, dest, href)
        _require_contained(PACKAGE_ROOT if href.startswith("m5/") else SEQ, src, href)
        # A dest that already matches the just-recorded checksum stays in place (backbone XML
        # authored in-sequence has no repo source and lands here). Otherwise (missing, or stale
        # from an earlier build whose XPT timestamps differ) re-copy from the repo source; the
        # previous logic trusted any existing dest and so failed verification on every re-run.
        if os.path.exists(dest) and _verify_dest(dest, href, recorded, cache) == recorded.lower():
            if os.path.splitext(dest)[1].lower() in {".xpt", ".sas7bdat"}:
                os.chmod(os.path.dirname(dest), 0o700)
                os.chmod(dest, 0o600)
            in_place += 1
            verified += 1
            continue
        if not os.path.exists(src):
            (mismatch if os.path.exists(dest) else missing).append(href)
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest); copied += 1
        if os.path.splitext(dest)[1].lower() in {".xpt", ".sas7bdat"}:
            # Materialized patient-level transport files are local controlled artifacts, not a
            # public review surface.  Keep both the file and its dataset directory least-privilege.
            os.chmod(os.path.dirname(dest), 0o700)
            os.chmod(dest, 0o600)
        # Always a genuine re-hash here (never routed through the cache lookup): dest was just
        # written, so this is the one place correctness must not lean on a cached value at all.
        actual = md5(dest)
        st = os.stat(dest)
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
    main()
