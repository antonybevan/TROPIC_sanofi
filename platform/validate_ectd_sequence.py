#!/usr/bin/env python3
"""Validate the complete eCTD v3.2.2 sequence surface.

Unlike a leaf-only checksum check, this validator also rejects unexpected files,
verifies the official UTIL support assets, resolves XML stylesheet/DTD references,
validates the three backbone XML documents against their local DTDs, and binds the
human run-record counts to the machine-readable index.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

from build_ectd_backbone import SUPPORT_FILES
from safe_filesystem import (
    UnsafePathError,
    canonical_posix_relative,
    contained_path,
    digest_file,
    open_regular,
    read_text as safe_read_text,
    regular_file_exists,
    require_directory,
    require_regular_file,
    require_tree_no_symlinks,
    walk_regular_files,
)


ROOT = Path(__file__).resolve().parents[1]
ECTD_ROOT = ROOT / "08_submission_package/ectd"
SEQ = ECTD_ROOT / "0000"
INDEX = SEQ / "index.xml"
INDEX_MD5 = SEQ / "index-md5.txt"
RUN_RECORD = ROOT / "08_submission_package/ectd/RUN_RECORD.md"
CONTROL_FILES = {"index.xml", "index-md5.txt"}
BACKBONE_XML = (
    "index.xml",
    "m1/us/us-regional.xml",
    "m5/53-clin-stud-rep/535-rep-effic-safety-stud/mcrpc/"
    "5351-stud-rep-contr/tropic/stf-tropic.xml",
)
INVENTORY_RE = re.compile(
    r"source_package_files=(\d+);\s*indexed_m5_leaves=(\d+);\s*checksum_leaves=(\d+)"
)


def _digest(path: Path, algorithm: str, root: Path = SEQ) -> str:
    return digest_file(path, root, algorithm)


def _safe_sequence_path(rel: str) -> Path | None:
    try:
        rel = canonical_posix_relative(rel)
        target = contained_path(SEQ, rel, allow_missing=True)
    except UnsafePathError:
        return None
    return target if target != SEQ else None


def indexed_leaves(index_path: Path = INDEX) -> list[dict[str, str]]:
    with open_regular(index_path, SEQ, binary=True) as stream:
        tree = ET.parse(stream)
    leaves = []
    for element in tree.iter():
        if element.tag.rsplit("}", 1)[-1] != "leaf":
            continue
        href = next(
            (value for key, value in element.attrib.items() if key.rsplit("}", 1)[-1] == "href"),
            "",
        )
        leaves.append({
            "id": element.attrib.get("ID", ""),
            "href": href,
            "checksum_type": element.attrib.get("checksum-type", ""),
            "checksum": element.attrib.get("checksum", ""),
        })
    return leaves


def _validate_xml_reference_targets(xml_path: Path, problems: list[str]) -> None:
    try:
        require_regular_file(xml_path, SEQ)
        text = safe_read_text(xml_path, SEQ, errors="replace")
    except UnsafePathError as exc:
        problems.append(f"unsafe XML file path: {xml_path}: {exc}")
        return
    references = re.findall(r"<\?xml-stylesheet\b[^?]*\bhref=[\"']([^\"']+)[\"']", text)
    references.extend(re.findall(r"<!DOCTYPE\b[^>]*\bSYSTEM\s+[\"']([^\"']+)[\"']", text))
    for reference in references:
        if urlparse(reference).scheme:
            problems.append(f"external XML support reference is not sequence-local: {xml_path}: {reference}")
            continue
        candidate = Path(os.path.abspath(os.fspath(xml_path.parent / reference)))
        try:
            rel = candidate.relative_to(SEQ).as_posix()
            target = contained_path(SEQ, rel, allow_missing=True)
        except (UnsafePathError, ValueError):
            problems.append(f"XML support reference escapes sequence: {xml_path}: {reference}")
        else:
            try:
                exists = regular_file_exists(target, SEQ)
            except UnsafePathError as exc:
                problems.append(
                    f"unsafe XML support reference: {xml_path}: {reference}: {exc}"
                )
                continue
            if exists:
                continue
            problems.append(
                f"missing XML support reference: {xml_path.relative_to(SEQ)} -> {reference}"
            )


def _validate_backbone_dtds(problems: list[str]) -> None:
    try:
        from lxml import etree
    except ImportError:
        problems.append("lxml unavailable; cannot execute local eCTD DTD validation")
        return
    parser = etree.XMLParser(
        load_dtd=True,
        dtd_validation=True,
        no_network=True,
        resolve_entities=False,
    )
    for rel in BACKBONE_XML:
        path = SEQ / rel
        try:
            if not regular_file_exists(path, SEQ):
                continue
        except UnsafePathError as exc:
            problems.append(f"unsafe backbone XML path {rel}: {exc}")
            continue
        try:
            etree.parse(str(path), parser)
        except (etree.XMLSyntaxError, OSError) as exc:
            problems.append(f"DTD-invalid backbone XML {rel}: {exc}")


def validate_sequence(require_all_leaves: bool = True, validate_dtd: bool = True) -> dict:
    problems: list[str] = []
    try:
        require_directory(SEQ, ECTD_ROOT)
        require_tree_no_symlinks(SEQ, ECTD_ROOT)
    except UnsafePathError as exc:
        return {"status": "FAIL", "problems": [f"unsafe sequence directory: {exc}"]}
    for rel in CONTROL_FILES:
        try:
            present = regular_file_exists(SEQ / rel, SEQ)
        except UnsafePathError as exc:
            problems.append(f"unsafe sequence control file {rel}: {exc}")
            present = False
        if not present:
            problems.append(f"missing sequence control file: {rel}")
    try:
        index_present = regular_file_exists(INDEX, SEQ)
    except UnsafePathError as exc:
        problems.append(f"unsafe index.xml path: {exc}")
        index_present = False
    if not index_present:
        return {"status": "FAIL", "problems": problems}

    try:
        leaves = indexed_leaves()
    except (ET.ParseError, OSError, UnsafePathError) as exc:
        return {"status": "FAIL", "problems": problems + [f"cannot parse index.xml: {exc}"]}
    if not leaves:
        problems.append("index.xml contains no leaves")

    ids = [row["id"] for row in leaves]
    hrefs = [row["href"] for row in leaves]
    duplicates = sorted({value for value in ids if value and ids.count(value) > 1})
    if duplicates:
        problems.append(f"duplicate leaf IDs: {duplicates}")
    duplicate_hrefs = sorted({value for value in hrefs if value and hrefs.count(value) > 1})
    if duplicate_hrefs:
        problems.append(f"duplicate leaf hrefs: {duplicate_hrefs}")

    allowed = set(CONTROL_FILES) | set(SUPPORT_FILES) | set(hrefs)
    try:
        actual = {path.relative_to(SEQ).as_posix() for path in walk_regular_files(SEQ)}
    except UnsafePathError as exc:
        return {"status": "FAIL", "problems": problems + [f"unsafe sequence entry: {exc}"]}
    ectd_root_extras = []
    for path in SEQ.parent.iterdir():
        info = os.lstat(path)
        if stat.S_ISLNK(info.st_mode):
            ectd_root_extras.append(f"../{path.name} (symlink)")
        elif stat.S_ISREG(info.st_mode) and path.name != "RUN_RECORD.md":
            ectd_root_extras.append(f"../{path.name}")
    ectd_root_extras.sort()
    extras = sorted(actual - allowed) + ectd_root_extras
    if extras:
        problems.append(f"unexpected/unindexed sequence files: {extras}")

    for rel, metadata in SUPPORT_FILES.items():
        path = SEQ / rel
        try:
            present = regular_file_exists(path, SEQ)
        except UnsafePathError as exc:
            problems.append(f"unsafe official support-file path {rel}: {exc}")
            continue
        if not present:
            problems.append(f"missing official support file: {rel}")
        elif _digest(path, "sha256", SEQ) != metadata["sha256"]:
            problems.append(f"official support-file checksum mismatch: {rel}")

    try:
        index_md5_present = regular_file_exists(INDEX_MD5, SEQ)
    except UnsafePathError as exc:
        problems.append(f"unsafe index-md5.txt path: {exc}")
        index_md5_present = False
    if index_md5_present:
        recorded = safe_read_text(
            INDEX_MD5, SEQ, encoding="ascii", errors="replace"
        ).strip().lower()
        actual_index_md5 = _digest(INDEX, "md5", SEQ)
        if recorded != actual_index_md5:
            problems.append(
                f"index-md5.txt mismatch: expected {actual_index_md5}, recorded {recorded}"
            )

    present_leaves = 0
    missing_leaves = []
    for leaf in leaves:
        href = leaf["href"]
        target = _safe_sequence_path(href)
        if target is None:
            problems.append(f"leaf href escapes sequence or is invalid: {href!r}")
            continue
        if leaf["checksum_type"].upper() != "MD5" or not re.fullmatch(
            r"[0-9a-fA-F]{32}", leaf["checksum"]
        ):
            problems.append(f"invalid MD5 declaration for leaf {leaf['id']}: {href}")
            continue
        try:
            target_present = regular_file_exists(target, SEQ)
        except UnsafePathError as exc:
            problems.append(f"unsafe leaf path {href}: {exc}")
            continue
        if not target_present:
            missing_leaves.append(href)
            continue
        present_leaves += 1
        actual_md5 = _digest(target, "md5", SEQ)
        if actual_md5 != leaf["checksum"].lower():
            problems.append(
                f"leaf checksum mismatch {href}: expected {leaf['checksum'].lower()}, got {actual_md5}"
            )
    if require_all_leaves and missing_leaves:
        problems.append(f"missing indexed leaf files: {missing_leaves}")

    for rel in sorted(actual):
        if rel.lower().endswith(".xml"):
            _validate_xml_reference_targets(SEQ / rel, problems)
    if validate_dtd:
        _validate_backbone_dtds(problems)

    m5_leaves = [href for href in hrefs if href.startswith("m5/")]
    source_package_files = [href for href in m5_leaves if not href.endswith("/stf-tropic.xml")]
    expected_counts = (len(source_package_files), len(m5_leaves), len(leaves))
    try:
        run_record_present = regular_file_exists(RUN_RECORD, ECTD_ROOT)
    except UnsafePathError as exc:
        problems.append(f"unsafe eCTD RUN_RECORD.md path: {exc}")
        run_record_present = False
    if not run_record_present:
        problems.append("missing eCTD RUN_RECORD.md")
    else:
        match = INVENTORY_RE.search(safe_read_text(RUN_RECORD, ECTD_ROOT, errors="replace"))
        if not match:
            problems.append("RUN_RECORD.md lacks the machine-checkable current inventory line")
        elif tuple(map(int, match.groups())) != expected_counts:
            problems.append(
                "RUN_RECORD.md inventory drift: "
                f"recorded={tuple(map(int, match.groups()))}, expected={expected_counts}"
            )

    return {
        "status": "PASS" if not problems else "FAIL",
        "require_all_leaves": require_all_leaves,
        "dtd_validation_executed": validate_dtd,
        "source_package_files": expected_counts[0],
        "indexed_m5_leaves": expected_counts[1],
        "checksum_leaves": expected_counts[2],
        "present_leaves": present_leaves,
        "missing_leaves": len(missing_leaves),
        "sequence_files": len(actual),
        "unexpected_files": extras,
        "problems": problems,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-missing-payload",
        action="store_true",
        help="Permit absent ignored leaf payloads in a data-free checkout; present files are still verified.",
    )
    parser.add_argument("--json", action="store_true", help="Emit the result as JSON.")
    args = parser.parse_args(argv)
    result = validate_sequence(require_all_leaves=not args.allow_missing_payload)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(
            "eCTD sequence validation: " + result["status"]
            + f" (leaves={result.get('present_leaves', 0)}/{result.get('checksum_leaves', 0)}, "
            + f"unexpected={len(result.get('unexpected_files', []))})"
        )
        for problem in result.get("problems", []):
            print(f"  - {problem}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
