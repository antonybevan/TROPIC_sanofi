#!/usr/bin/env python3
"""
materialize_ectd.py — populate the eCTD sequence so every backbone leaf resolves in-place.

`build_ectd_backbone.py` writes `11_ectd/0000/index.xml` with one <leaf> per deliverable —
each carries the canonical sequence-relative `xlink:href` and the real MD5 `checksum` of the
source file in the repo `m5/` tree. This tool reads that manifest and copies each source to its
href location under `11_ectd/0000/`, then re-verifies the copy's MD5 against the recorded
checksum. Backbone components already written in-sequence (us-regional.xml, stf-tropic.xml) are
verified in place. Idempotent: re-running only re-verifies unless a file is missing.

The materialized payload (datasets + report binaries) is a reproducible copy and is git-ignored
(see .gitignore); the backbone XML, STF, regional metadata, and this record stay tracked.

Usage:  python3 06_telemetry/materialize_ectd.py
"""
import os, re, sys, hashlib, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SEQ = os.path.join(ROOT, "11_ectd", "0000")
INDEX = os.path.join(SEQ, "index.xml")

def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    idx = open(INDEX, encoding="utf-8").read()
    leaves = re.findall(
        r'xlink:href="([^"]+)"\s+checksum-type="MD5"\s+checksum="([0-9a-fA-F]+)"', idx)
    if not leaves:
        sys.exit("No leaves with checksums found in index.xml")
    copied = verified = in_place = 0
    missing, mismatch = [], []
    for href, recorded in leaves:
        dest = os.path.join(SEQ, href)
        src = os.path.join(ROOT, href)                # href == repo-relative path of source
        # A dest that already matches the just-recorded checksum stays in place (backbone XML
        # authored in-sequence has no repo source and lands here). Otherwise (missing, or stale
        # from an earlier build whose XPT timestamps differ) re-copy from the repo source; the
        # previous logic trusted any existing dest and so failed verification on every re-run.
        if os.path.exists(dest) and md5(dest) == recorded.lower():
            in_place += 1
            verified += 1
            continue
        if not os.path.exists(src):
            (mismatch if os.path.exists(dest) else missing).append(href)
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest); copied += 1
        if md5(dest) == recorded.lower():
            verified += 1
        else:
            mismatch.append(href)
    print(f"leaves={len(leaves)}  copied={copied}  already-in-place={in_place}  "
          f"MD5-verified={verified}/{len(leaves)}")
    if missing:  print("MISSING SOURCES:", *missing, sep="\n  ")
    if mismatch: print("MD5 MISMATCH:", *mismatch, sep="\n  ")
    if missing or mismatch:
        sys.exit(1)
    print("OK — all leaves materialized and checksum-verified in 11_ectd/0000/")

if __name__ == "__main__":
    main()
