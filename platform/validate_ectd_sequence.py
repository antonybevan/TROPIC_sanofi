#!/usr/bin/env python3
"""Validate the complete eCTD v3.2.2 sequence surface.

Unlike a leaf-only checksum check, this validator also rejects unexpected files,
verifies the official UTIL support assets, resolves XML stylesheet/DTD references,
validates the three backbone XML documents against their local DTDs, and binds the
human run-record counts to the machine-readable index.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

from build_ectd_backbone import SUPPORT_FILES


ROOT = Path(__file__).resolve().parents[1]
SEQ = ROOT / "08_submission_package/ectd/0000"
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


def _digest(path: Path, algorithm: str) -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_sequence_path(rel: str) -> Path | None:
    if not rel or Path(rel).is_absolute():
        return None
    target = (SEQ / rel).resolve()
    base = SEQ.resolve()
    return target if target != base and base in target.parents else None


def indexed_leaves(index_path: Path = INDEX) -> list[dict[str, str]]:
    tree = ET.parse(index_path)
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
    text = xml_path.read_text(encoding="utf-8", errors="replace")
    references = re.findall(r"<\?xml-stylesheet\b[^?]*\bhref=[\"']([^\"']+)[\"']", text)
    references.extend(re.findall(r"<!DOCTYPE\b[^>]*\bSYSTEM\s+[\"']([^\"']+)[\"']", text))
    for reference in references:
        if urlparse(reference).scheme:
            problems.append(f"external XML support reference is not sequence-local: {xml_path}: {reference}")
            continue
        target = (xml_path.parent / reference).resolve()
        if SEQ.resolve() not in target.parents:
            problems.append(f"XML support reference escapes sequence: {xml_path}: {reference}")
        elif not target.is_file():
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
        if not path.is_file():
            continue
        try:
            etree.parse(str(path), parser)
        except (etree.XMLSyntaxError, OSError) as exc:
            problems.append(f"DTD-invalid backbone XML {rel}: {exc}")


def validate_sequence(require_all_leaves: bool = True, validate_dtd: bool = True) -> dict:
    problems: list[str] = []
    if not SEQ.is_dir():
        return {"status": "FAIL", "problems": [f"missing sequence directory: {SEQ}"]}
    for rel in CONTROL_FILES:
        if not (SEQ / rel).is_file():
            problems.append(f"missing sequence control file: {rel}")
    if not INDEX.is_file():
        return {"status": "FAIL", "problems": problems}

    try:
        leaves = indexed_leaves()
    except (ET.ParseError, OSError) as exc:
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
    actual = {
        path.relative_to(SEQ).as_posix()
        for path in SEQ.rglob("*")
        if path.is_file()
    }
    ectd_root_extras = sorted(
        f"../{path.name}"
        for path in SEQ.parent.iterdir()
        if path.is_file() and path.name != "RUN_RECORD.md"
    )
    extras = sorted(actual - allowed) + ectd_root_extras
    if extras:
        problems.append(f"unexpected/unindexed sequence files: {extras}")

    for rel, metadata in SUPPORT_FILES.items():
        path = SEQ / rel
        if not path.is_file():
            problems.append(f"missing official support file: {rel}")
        elif _digest(path, "sha256") != metadata["sha256"]:
            problems.append(f"official support-file checksum mismatch: {rel}")

    if INDEX_MD5.is_file():
        recorded = INDEX_MD5.read_text(encoding="ascii", errors="replace").strip().lower()
        actual_index_md5 = _digest(INDEX, "md5")
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
        if not target.is_file():
            missing_leaves.append(href)
            continue
        present_leaves += 1
        actual_md5 = _digest(target, "md5")
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
    if not RUN_RECORD.is_file():
        problems.append("missing eCTD RUN_RECORD.md")
    else:
        match = INVENTORY_RE.search(RUN_RECORD.read_text(encoding="utf-8", errors="replace"))
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
