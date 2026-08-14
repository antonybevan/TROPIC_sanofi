#!/usr/bin/env python3
"""G07 Reviewer Package Lock — executable gate.

Ensures ADRG/cSDRG/BDRG and supporting reviewer packs exist and carry controlled
non-claim / residual-risk pointers before packaging language is trusted.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "06_qc_evidence/gates/g07_reviewer_package_status.json"
CURRENT_RELEASE = "v0.3.0-clinical-simulation"
CURRENT_RELEASE_NOTE = "docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md"

REQUIRED = [
    "07_reviewer_explanation/guides/ADRG.md",
    "07_reviewer_explanation/guides/SDRG.md",
    "07_reviewer_explanation/guides/BDRG.md",
    "07_reviewer_explanation/guides/TRACEABILITY_MATRIX.md",
    "07_reviewer_explanation/simulation_model_analysis_plan.md",
    "07_reviewer_explanation/simulation_report.md",
    "platform/simulation_operating_characteristics/simulation_oc_status.json",
    "docs/PRODUCT_CLAIM.md",
    "docs/workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md",
    CURRENT_RELEASE_NOTE,
    "08_submission_package/README.md",
]

RELEASE_ID_SOURCES = [
    "07_reviewer_explanation/analysis_report.md",
    "07_reviewer_explanation/guides/ADRG.md",
    "07_reviewer_explanation/guides/SDRG.md",
    "07_reviewer_explanation/guides/BDRG.md",
    "07_reviewer_explanation/simulation_model_analysis_plan.md",
    "07_reviewer_explanation/simulation_report.md",
    "08_submission_package/README.md",
]

# Each guide must mention the controlled non-submission boundary.
GUIDE_MARKERS = {
    "07_reviewer_explanation/guides/ADRG.md": [
        r"PRODUCT_CLAIM|non-submission|controlled|v0\.1\.0-demo-rc",
        r"KNOWN_DIFFERENCES|synthetic|CbzP|Guyot|Part 11",
    ],
    "07_reviewer_explanation/guides/SDRG.md": [
        r"PRODUCT_CLAIM|non-submission|controlled|v0\.1\.0-demo-rc",
        r"source|PDS|week|precision|CORE",
    ],
    "07_reviewer_explanation/guides/BDRG.md": [
        r"clinsite|BIMO|site",
    ],
}

SIMULATION_MARKERS = {
    "07_reviewer_explanation/simulation_model_analysis_plan.md": [
        r"(?i)informative annex boundary",
        r"(?i)not MIDD",
        r"ICH M15",
        r"ICH E9\(R1\)",
        r"ADEMP.*OCTAVE|OCTAVE.*ADEMP",
        r"(?i)Monte Carlo.*Wilson",
    ],
    "07_reviewer_explanation/simulation_report.md": [
        r"(?i)informative annex boundary",
        r"(?i)not MIDD",
        r"(?i)no single overall PASS",
        r"(?i)requested.*completed.*failed",
        r"(?i)MCSE",
        r"(?i)authoritative scientific JSON",
    ],
}

# Fail if guide asserts filing readiness without negation in same line-ish window.
OVERCLAIM = re.compile(
    r"(?i)(this package is|we are)\s+(FDA\s+)?submission[- ]ready"
)

REVIEWER_PDFS = [
    "08_submission_package/m5/datasets/tropic/analysis/adam/adrg.pdf",
    "08_submission_package/m5/datasets/tropic/tabulations/sdtm/csdrg.pdf",
    "08_submission_package/m5/datasets/tropic/bimo/datasets/bdrg.pdf",
    "08_submission_package/m5/53-clin-stud-rep/535-rep-effic-safety-stud/mcrpc/5351-stud-rep-contr/tropic/csr.pdf",
    "08_submission_package/m5/53-clin-stud-rep/535-rep-effic-safety-stud/mcrpc/5351-stud-rep-contr/tropic/simulation-model-analysis-plan.pdf",
    "08_submission_package/m5/53-clin-stud-rep/535-rep-effic-safety-stud/mcrpc/5351-stud-rep-contr/tropic/simulation-report.pdf",
]

SECONDARY_TTE_ROWS = {
    "T-11-6": "Time to Tumour Progression",
    "T-11-7": "Time to PSA Progression",
    "T-11-8": "Time to Pain Progression",
}


def _tfl_secondary_metrics(text: str, table_id: str) -> tuple[str, ...]:
    block_match = re.search(
        rf"(?ms)^{re.escape(table_id)}:.*?(?=^T-\d{{2}}-|\Z)",
        text,
    )
    if block_match is None:
        raise ValueError(f"{table_id} block not found")
    block = block_match.group(0)

    def match(pattern: str, label: str) -> tuple[str, ...]:
        found = re.search(pattern, block)
        if found is None:
            raise ValueError(f"{table_id} {label} row not parseable")
        return found.groups()

    events = match(
        r"Number of Events / Total N\s+(\d+/\d+)\s+(\d+/\d+)",
        "event",
    )
    medians = match(
        r"Median Survival Time \(Months\)\s+(\S+)\s+(\S+)",
        "median",
    )
    effect = match(
        r"Stratified Cox HR .*?\s+([0-9.]+) \(95% CI: ([0-9.]+)-([0-9.]+)\)",
        "effect",
    )
    p_value = match(r"Stratified log-rank p-value\s+(\S+)", "p-value")
    return (*medians, *events, *effect, *p_value)


def _report_secondary_metrics(text: str, label: str) -> tuple[str, ...]:
    line = next(
        (
            row
            for row in text.splitlines()
            if row.startswith(f"| {label}")
        ),
        None,
    )
    if line is None:
        raise ValueError(f"analysis-report row not found: {label}")
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if len(cells) < 5:
        raise ValueError(f"analysis-report row malformed: {label}")
    cbzp = re.fullmatch(r"(\S+) mo \((\d+/\d+)\)", cells[1])
    mp = re.fullmatch(r"(\S+)(?: mo)? \((\d+/\d+)\)", cells[2])
    effect = re.search(
        r"HR ([0-9.]+) \(([0-9.]+)[–-]([0-9.]+)\)",
        cells[3],
    )
    if cbzp is None or mp is None or effect is None:
        raise ValueError(f"analysis-report metrics not parseable: {label}")
    return (
        cbzp.group(1),
        mp.group(1),
        cbzp.group(2),
        mp.group(2),
        *effect.groups(),
        cells[4],
    )


def _pdfinfo(path: Path) -> dict[str, str]:
    output = subprocess.check_output(
        ["pdfinfo", str(path)], cwd=ROOT, text=True, stderr=subprocess.STDOUT
    )
    return {
        key.strip(): value.strip()
        for line in output.splitlines()
        if ":" in line
        for key, value in [line.split(":", 1)]
    }


def _fonts_embedded(path: Path) -> tuple[bool, str]:
    output = subprocess.check_output(
        ["pdffonts", str(path)], cwd=ROOT, text=True, stderr=subprocess.STDOUT
    )
    rows = []
    for line in output.splitlines()[2:]:
        match = re.search(r"\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$", line)
        if match:
            rows.append((line.split()[0], match.group(1)))
    if not rows:
        return False, "no fonts reported"
    unembedded = [name for name, embedded in rows if embedded != "yes"]
    return not unembedded, f"fonts={len(rows)}; unembedded={unembedded}"


def _reader_pdf_controls(path: Path) -> dict:
    from pypdf import PdfReader

    reader = PdfReader(path)
    sizes = []
    link_annotations = 0
    letter_pages = 0
    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        if abs(width - 612) <= 1 and abs(height - 792) <= 1:
            letter_pages += 1
        for annotation_ref in page.get("/Annots", []):
            annotation = annotation_ref.get_object()
            if str(annotation.get("/Subtype")) == "/Link":
                link_annotations += 1

        def visit(text, _cm, _tm, _font_dict, font_size):
            if text and text.strip():
                sizes.append(float(font_size))

        page.extract_text(visitor_text=visit)
    root = reader.trailer["/Root"]
    return {
        "pages": len(reader.pages),
        "letter_pages": letter_pages,
        "outlines": len(reader.outline),
        "page_mode": str(root.get("/PageMode", "")),
        "link_annotations": link_annotations,
        "min_font_size": min(sizes) if sizes else 0,
        "title": str((reader.metadata or {}).get("/Title", "")),
    }


def main() -> int:
    check_only = "--check-only" in sys.argv[1:]
    checks = []
    problems = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            problems.append(f"{name}: {detail}" if detail else name)

    for rel in REQUIRED:
        p = ROOT / rel
        add(f"exists:{rel}", p.is_file(), "missing" if not p.is_file() else "present")

    for rel in RELEASE_ID_SOURCES:
        p = ROOT / rel
        if not p.is_file():
            continue
        current_lines = [
            line for line in p.read_text(encoding="utf-8", errors="replace").splitlines()
            if re.search(r"(?i)current (sealed )?(portfolio|controlled) release", line)
        ]
        add(
            f"release_identity:{rel}",
            len(current_lines) == 1
            and CURRENT_RELEASE in current_lines[0]
            and CURRENT_RELEASE_NOTE in current_lines[0],
            f"expected one current-release line binding {CURRENT_RELEASE} to {CURRENT_RELEASE_NOTE}; "
            f"found={current_lines}",
        )

    for rel, patterns in GUIDE_MARKERS.items():
        p = ROOT / rel
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for pat in patterns:
            add(f"marker:{rel}:{pat[:40]}", bool(re.search(pat, text, re.I)), "marker missing")
        if OVERCLAIM.search(text):
            add(f"overclaim:{rel}", False, "positive submission-ready claim found")

    for rel, patterns in SIMULATION_MARKERS.items():
        p = ROOT / rel
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for pat in patterns:
            add(
                f"simulation_marker:{rel}:{pat[:40]}",
                bool(re.search(pat, text, re.I | re.S)),
                "simulation evidence marker missing",
            )
        if OVERCLAIM.search(text):
            add(f"overclaim:{rel}", False, "positive submission-ready claim found")

    # Traceability must not reintroduce removed false listing claim as active deliverable
    tr = ROOT / "07_reviewer_explanation/guides/TRACEABILITY_MATRIX.md"
    if tr.is_file():
        t = tr.read_text(encoding="utf-8", errors="replace")
        # Allow historical mention of L-01 removal; fail if it claims L-01 is produced
        bad_l01 = re.search(r"(?i)L-01[^\n]{0,80}(produced|deliverable|output)", t)
        add("traceability.no_active_L01_claim", not bad_l01, "possible active L-01 claim")

    # Narrative endpoint values must agree with the generated T-11 table that
    # the report identifies as its controlling source. This catches a stale CSR
    # narrative after deterministic synthetic-comparator regeneration.
    analysis_report = ROOT / "07_reviewer_explanation/analysis_report.md"
    efficacy_table = ROOT / "05_outputs/tfl/output/tables/T-11-Efficacy_Tables.txt"
    if analysis_report.is_file() and efficacy_table.is_file():
        report_text = analysis_report.read_text(encoding="utf-8", errors="replace")
        table_text = efficacy_table.read_text(encoding="utf-8", errors="replace")
        for table_id, label in SECONDARY_TTE_ROWS.items():
            try:
                expected = _tfl_secondary_metrics(table_text, table_id)
                observed = _report_secondary_metrics(report_text, label)
                add(
                    f"analysis_report.matches:{table_id}",
                    observed == expected,
                    f"report={observed}; generated_table={expected}",
                )
            except ValueError as exc:
                add(f"analysis_report.matches:{table_id}", False, str(exc))

    # The Markdown sources are converted into the reviewer-facing PDFs during
    # packaging.  Check the rendered text as well: a Latin-1 fallback that
    # turns >=/arrows into '?' or leaves Markdown delimiters in the PDF is a
    # reviewer-facing quality failure, not a source-only lint issue.
    pdftotext = shutil.which("pdftotext")
    pdfinfo = shutil.which("pdfinfo")
    pdffonts = shutil.which("pdffonts")
    add("reviewer_pdf.pdftotext_available", bool(pdftotext), "Poppler pdftotext not found")
    add("reviewer_pdf.pdfinfo_available", bool(pdfinfo), "Poppler pdfinfo not found")
    add("reviewer_pdf.pdffonts_available", bool(pdffonts), "Poppler pdffonts not found")
    try:
        import pypdf  # noqa: F401
        pypdf_available = True
    except ImportError:
        pypdf_available = False
    add("reviewer_pdf.pypdf_available", pypdf_available, "pypdf not installed")
    if pdftotext:
        for rel in REVIEWER_PDFS:
            path = ROOT / rel
            if not path.is_file():
                add(f"reviewer_pdf.exists:{rel}", False, "missing")
                continue
            try:
                text = subprocess.check_output(
                    [pdftotext, str(path), "-"],
                    cwd=ROOT,
                    text=True,
                    stderr=subprocess.STDOUT,
                )
            except (OSError, subprocess.CalledProcessError) as exc:
                add(f"reviewer_pdf.extract:{rel}", False, str(exc))
                continue
            bad_thresholds = re.findall(r"\?[0-9%]", text)
            raw_markdown = re.search(r"\*\*|`", text)
            add(
                f"reviewer_pdf.no_symbol_substitution:{rel}",
                not bad_thresholds,
                f"rendered threshold substitutions: {bad_thresholds[:5]}",
            )
            add(
                f"reviewer_pdf.no_raw_markdown:{rel}",
                raw_markdown is None,
                "raw Markdown delimiter found in rendered text" if raw_markdown else "",
            )
            normalized = re.sub(r"\s+", " ", text)
            add(
                f"reviewer_pdf.release_identity:{rel}",
                CURRENT_RELEASE in normalized,
                f"rendered PDF does not identify current release {CURRENT_RELEASE}",
            )
            if rel.endswith("/bdrg.pdf"):
                add(
                    "reviewer_pdf.bdrg_investigator_expression",
                    '"PI_" || SITEID' in normalized,
                    "BDRG INVNAM expression is not rendered as one intact table cell",
                )

            if pdfinfo:
                try:
                    info = _pdfinfo(path)
                    page_size = info.get("Page size", "")
                    add(
                        f"reviewer_pdf.letter_page_size:{rel}",
                        bool(re.search(r"612(?:\.\d+)? x 792(?:\.\d+)? pts", page_size)),
                        page_size,
                    )
                    add(
                        f"reviewer_pdf.fast_web_view:{rel}",
                        info.get("Optimized", "").lower() == "yes",
                        f"Optimized={info.get('Optimized', 'missing')}",
                    )
                    add(
                        f"reviewer_pdf.not_encrypted:{rel}",
                        info.get("Encrypted", "").lower() == "no",
                        f"Encrypted={info.get('Encrypted', 'missing')}",
                    )
                    add(
                        f"reviewer_pdf.version_1_7:{rel}",
                        info.get("PDF version") == "1.7",
                        f"PDF version={info.get('PDF version', 'missing')}",
                    )
                except (OSError, subprocess.CalledProcessError) as exc:
                    add(f"reviewer_pdf.pdfinfo:{rel}", False, str(exc))

            if pdffonts:
                try:
                    embedded, detail = _fonts_embedded(path)
                    add(f"reviewer_pdf.fonts_embedded:{rel}", embedded, detail)
                except (OSError, subprocess.CalledProcessError) as exc:
                    add(f"reviewer_pdf.fonts_embedded:{rel}", False, str(exc))

            if pypdf_available:
                try:
                    controls = _reader_pdf_controls(path)
                    add(
                        f"reviewer_pdf.all_pages_letter:{rel}",
                        controls["letter_pages"] == controls["pages"],
                        f"letter={controls['letter_pages']}/{controls['pages']}",
                    )
                    add(
                        f"reviewer_pdf.bookmarks:{rel}",
                        controls["outlines"] > 0 and controls["page_mode"] == "/UseOutlines",
                        f"outlines={controls['outlines']}; page_mode={controls['page_mode']}",
                    )
                    add(
                        f"reviewer_pdf.hyperlinks:{rel}",
                        controls["link_annotations"] > 0,
                        f"link_annotations={controls['link_annotations']}",
                    )
                    add(
                        f"reviewer_pdf.minimum_font_size:{rel}",
                        controls["min_font_size"] >= 9,
                        f"minimum rendered text size={controls['min_font_size']}",
                    )
                    add(
                        f"reviewer_pdf.metadata_title:{rel}",
                        bool(controls["title"]),
                        "PDF title metadata is empty",
                    )
                except Exception as exc:
                    add(f"reviewer_pdf.structure:{rel}", False, str(exc))

    status = "PASS" if not problems else "FAIL"
    payload = {
        "gate": "G07",
        "name": "reviewer_package_lock",
        "status": status,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checks": checks,
        "problems": problems,
    }
    if not check_only:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"G07 Reviewer Package Lock: {status}")
    for p in problems:
        print(f"  - {p}")
    if check_only:
        print("Check-only mode: committed G07 status was not rewritten")
    else:
        print(f"Wrote {OUT.relative_to(ROOT)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
