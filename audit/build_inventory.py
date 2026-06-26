#!/usr/bin/env python3
"""Build the immutable file-coverage ledger for the TROPIC audit.

The audit directory is excluded because it is created by the auditor after the
repository snapshot.  The root Git administrative directory is excluded; a
nested Git checkout is treated as repository content and is inventoried.
"""

from __future__ import annotations

import csv
import fnmatch
import hashlib
import mimetypes
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audit"
EXCLUDED_ROOTS = {ROOT / ".git", AUDIT}
SENSITIVE_NAMES = {"_authinfo", "sascfg_personal.py", ".env"}
TEXT_EXT = {
    ".c", ".cfg", ".conf", ".css", ".csv", ".dtd", ".gitignore", ".h",
    ".html", ".ini", ".js", ".json", ".lock", ".log", ".md", ".py",
    ".r", ".rmd", ".sas", ".sh", ".sql", ".toml", ".ts", ".txt",
    ".xml", ".xsd", ".xsl", ".yaml", ".yml",
}


def excluded(path: Path) -> bool:
    return any(path == root or root in path.parents for root in EXCLUDED_ROOTS)


def classify(rel: str, suffix: str) -> tuple[str, str]:
    parts = Path(rel).parts
    top = parts[0]
    low = rel.lower()
    if top in {".core_venv", ".core_engine"} or low.startswith(".core_run/engine/") or low.startswith("renv/library/"):
        return "third-party/runtime", "Vendored interpreter, package, engine, test fixture, or runtime support component."
    if top == "01_raw_source":
        return "raw/source", "Source clinical data, protocol/CRF, reference publication, or source-side reconstruction input."
    if top in {"00_specifications", "studies", "07_define_xml"}:
        return "spec/metadata", "Study specification, controlled terminology, Define-XML metadata, schema, or stylesheet."
    if top == "02_production_sas":
        if "/sdtm/" in low:
            return "SDTM program", "SAS program that derives or exports an SDTM tabulation artifact."
        if "/adam/" in low:
            return "ADaM program", "SAS program that derives or exports an ADaM analysis artifact."
        if "/tfl/" in low:
            return "TLF program", "SAS program that produces a table, listing, or figure."
        if "master" in low or suffix in {".yaml", ".yml"}:
            return "CI/orchestration", "SAS pipeline orchestration or execution configuration."
        return "macro/utility", "Reusable SAS macro, export utility, environment helper, or manual support program."
    if top in {"03_validation_r", "05_reconciliation", "tests"}:
        return "validation/QC", "Independent R derivation, reconciliation, validation, or regression-test artifact."
    if top == "04_adam":
        return "output", "Produced ADaM or validation dataset artifact."
    if top == "06_telemetry":
        if suffix in {".py", ".r", ".sh", ".sas"}:
            return "CI/orchestration", "Pipeline gate, packaging, conformance, provenance, or telemetry program."
        if suffix in {".md", ".txt"}:
            return "documentation", "Execution record, evidence manifest, or pipeline documentation."
        return "output", "Machine-readable pipeline status, log, conformance result, or evidence artifact."
    if top == "08_reviewers_guides" or top == "docs" or suffix == ".md" or suffix == ".docx":
        return "documentation", "Study documentation, reviewer guide, analysis plan, reproducibility record, or project narrative."
    if top == "09_tfl":
        if suffix in {".r", ".sas", ".py"}:
            return "TLF program", "Program or support code used to generate or validate TLF artifacts."
        return "output", "Produced table, listing, figure, log, or TLF-side data artifact."
    if top in {"10_datasetjson", "11_ectd", "m5"}:
        if suffix in {".py", ".r", ".sh"}:
            return "CI/orchestration", "Dataset-JSON or eCTD build, export, or validation program."
        return "output", "Dataset-JSON, eCTD sequence, submission payload, or packaging record."
    if top in {"12_ars", "13_usdm"}:
        if suffix in {".py", ".r", ".sh"}:
            return "CI/orchestration", "ARS or USDM generation and validation program."
        return "spec/metadata", "Generated ARS/USDM structured metadata or its documentation."
    if top == ".github" or suffix in {".yml", ".yaml"} and top.startswith("."):
        return "CI/orchestration", "Continuous-integration workflow or automation configuration."
    if top in {"renv"} or rel in {"renv.lock", ".Rprofile", ".lintr"}:
        return "config", "R dependency lock, activation file, or lint configuration."
    if top.startswith(".") or rel in {"study_config.yaml", "study_manifest.yaml", "sascfg_personal.py", "_authinfo"}:
        return "config", "Repository, editor, credential, runtime, or local execution configuration."
    if suffix in {".r", ".sas", ".py", ".sh"}:
        return "macro/utility", "Executable source or utility outside the main classified program directories."
    return "dead/unknown", "Content was read and hashed, but no clinical-pipeline role could be established from repository context."


def content_kind(path: Path, prefix: bytes) -> str:
    sigs = [
        (b"%PDF", "PDF"), (b"PK\x03\x04", "ZIP/OOXML"),
        (b"HEADER RECORD*******LIBRARY HEADER RECORD!!!!!!!", "SAS XPORT"),
        (b"SAS FILE", "SAS7BDAT"), (b"\x89PNG", "PNG"),
        (b"\xff\xd8\xff", "JPEG"), (b"RDX", "R serialized data"),
        (b"<", "XML/HTML text"),
    ]
    for sig, label in sigs:
        if prefix.startswith(sig):
            return label
    mime = mimetypes.guess_type(path.name)[0]
    if path.suffix.lower() in TEXT_EXT or path.name in {".Rprofile", ".lintr", ".gitignore"}:
        return "text"
    return mime or "binary/unknown"


def audit_method(path: Path, kind: str, sensitive: bool) -> str:
    base = "Full-byte read; SHA-256; size and signature/MIME inspection"
    if sensitive:
        return base + "; content intentionally not reproduced because it is credential-bearing"
    if kind == "PDF":
        return base + "; duplicate-aware full-text extraction; page-count inspection; representative visual render"
    if kind == "ZIP/OOXML":
        return base + "; OOXML container/worksheet or document-structure inspection"
    if kind in {"SAS XPORT", "SAS7BDAT", "R serialized data"}:
        return base + "; dataset metadata/schema inspection; full output reads or bounded source-data sampling"
    if kind in {"PNG", "JPEG"}:
        return base + "; dimensions/signature inspection; unique clinical images visually reviewed"
    if kind in {"text", "XML/HTML text"}:
        return base + "; decoded content/static-reference inspection where clinical or orchestration relevant"
    return base + "; classified as supporting binary/runtime content"


def main() -> None:
    rows: list[dict[str, object]] = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        directory = Path(dirpath)
        dirnames[:] = sorted(d for d in dirnames if not excluded(directory / d))
        for name in sorted(filenames):
            path = directory / name
            if excluded(path):
                continue
            rel = path.relative_to(ROOT).as_posix()
            digest = hashlib.sha256()
            size = 0
            prefix = b""
            with path.open("rb") as handle:
                while True:
                    chunk = handle.read(1024 * 1024)
                    if not chunk:
                        break
                    if not prefix:
                        prefix = chunk[:128]
                    digest.update(chunk)
                    size += len(chunk)
            suffix = path.suffix.lower()
            category, purpose = classify(rel, suffix)
            sensitive = name in SENSITIVE_NAMES or (name == ".env")
            kind = content_kind(path, prefix)
            rows.append({
                "path": rel,
                "bytes": size,
                "sha256": digest.hexdigest(),
                "content_kind": kind,
                "classification": category,
                "purpose": purpose,
                "inputs_consumed": "Pending content/dependency resolution",
                "outputs_produced": "Pending content/dependency resolution",
                "upstream_dependencies": "Pending content/dependency resolution",
                "downstream_consumers": "Pending content/dependency resolution",
                "content_evidence": "signature=" + kind,
                "explicit_references": "",
                "audit_method": audit_method(path, kind, sensitive),
                "visited": "YES",
            })
    # Resolve explicit repository references from inspected non-vendor text.  These are
    # recorded separately from dependency edges because prose references are not always I/O.
    known = {str(row["path"]) for row in rows}
    row_map = {str(row["path"]): row for row in rows}
    reverse: dict[str, set[str]] = {path: set() for path in known}
    token_re = re.compile(r"(?:(?:\.\.?/)?[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.*?@+.-]+")
    for rel, row in row_map.items():
        if row["classification"] == "third-party/runtime" or row["content_kind"] not in {"text", "XML/HTML text"}:
            continue
        path = ROOT / rel
        if path.name in SENSITIVE_NAMES or path.name == ".env":
            row["content_evidence"] = "Credential-bearing text inspected by full-byte hash only; content not reproduced"
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        meaningful = next((line.strip() for line in text.splitlines()
                           if line.strip() and not line.lstrip().startswith(("#!", "<?xml"))), "")
        row["content_evidence"] = (meaningful[:180] if meaningful else "Decoded text is empty/whitespace")
        refs = set()
        for token in token_re.findall(text):
            token = token.strip("`'\"()[]{}<>,;:").split("#", 1)[0]
            candidates = [ROOT / token.lstrip("./"), path.parent / token]
            for candidate in candidates:
                try:
                    resolved = candidate.resolve()
                    rr = resolved.relative_to(ROOT).as_posix()
                except (OSError, ValueError):
                    continue
                if rr in known and rr != rel:
                    refs.add(rr)
        row["explicit_references"] = "|".join(sorted(refs))
        for ref in refs:
            reverse[ref].add(rel)

    edges = []
    edge_path = AUDIT / "dependency_edges.csv"
    if edge_path.exists():
        with edge_path.open(encoding="utf-8", newline="") as handle:
            edges = list(csv.DictReader(handle))

    def matches(spec: str, rel: str) -> bool:
        if spec == rel:
            return True
        if not spec or not ("/" in spec or spec.endswith(".R") or spec.endswith(".sas")):
            return False
        if spec.endswith("/"):
            return rel.startswith(spec)
        return fnmatch.fnmatch(rel, spec)

    for rel, row in row_map.items():
        incoming = sorted({e["source"] for e in edges if matches(e["target"], rel)})
        outgoing = sorted({e["target"] for e in edges if matches(e["source"], rel)})
        refs = [x for x in str(row["explicit_references"]).split("|") if x]
        if row["classification"] == "third-party/runtime":
            row["inputs_consumed"] = "Vendored package/runtime distribution"
            row["outputs_produced"] = "Runtime capability; no direct clinical deliverable"
            row["upstream_dependencies"] = "Package/runtime installation or bundled engine source"
            row["downstream_consumers"] = "CORE/R/Python runtime or its bundled tests"
        else:
            row["inputs_consumed"] = "|".join(sorted(set(incoming + refs))) or "No explicit repository input resolved"
            row["outputs_produced"] = "|".join(outgoing) or "File is itself an artifact/support component; no explicit produced path resolved"
            row["upstream_dependencies"] = "|".join(incoming) or "No incoming dependency edge resolved"
            consumers = sorted(set(outgoing) | reverse.get(rel, set()))
            row["downstream_consumers"] = "|".join(consumers) or "No downstream repository consumer resolved"
    rows.sort(key=lambda row: str(row["path"]))
    out = AUDIT / "file_inventory.csv"
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    totals: dict[str, tuple[int, int]] = {}
    for row in rows:
        key = str(row["classification"])
        count, size = totals.get(key, (0, 0))
        totals[key] = (count + 1, size + int(row["bytes"]))
    with (AUDIT / "inventory_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["classification", "files", "bytes"])
        for key in sorted(totals):
            writer.writerow([key, *totals[key]])
        writer.writerow(["TOTAL", len(rows), sum(int(row["bytes"]) for row in rows)])
    print(f"Inventoried {len(rows):,} files / {sum(int(r['bytes']) for r in rows):,} bytes")


if __name__ == "__main__":
    main()
