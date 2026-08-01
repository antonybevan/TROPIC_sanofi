#!/usr/bin/env python3
"""G07 Reviewer Package Lock — executable gate.

Ensures ADRG/SDRG/BDRG and supporting reviewer packs exist and carry Path A
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

REQUIRED = [
    "07_reviewer_explanation/guides/ADRG.md",
    "07_reviewer_explanation/guides/SDRG.md",
    "07_reviewer_explanation/guides/BDRG.md",
    "07_reviewer_explanation/guides/TRACEABILITY_MATRIX.md",
    "docs/PRODUCT_CLAIM.md",
    "docs/workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md",
    "docs/RELEASE_NOTE_v0.1.0-demo-rc.1.md",
]

# Each guide must mention product claim or non-submission / demo boundary.
GUIDE_MARKERS = {
    "07_reviewer_explanation/guides/ADRG.md": [
        r"PRODUCT_CLAIM|non-submission|demonstration|v0\.1\.0-demo-rc",
        r"KNOWN_DIFFERENCES|synthetic|CbzP|Guyot|Part 11",
    ],
    "07_reviewer_explanation/guides/SDRG.md": [
        r"PRODUCT_CLAIM|non-submission|demonstration|v0\.1\.0-demo-rc",
        r"source|PDS|week|precision|CORE",
    ],
    "07_reviewer_explanation/guides/BDRG.md": [
        r"clinsite|BIMO|site",
    ],
}

# Fail if guide asserts filing readiness without negation in same line-ish window.
OVERCLAIM = re.compile(
    r"(?i)(this package is|we are)\s+(FDA\s+)?submission[- ]ready"
)

REVIEWER_PDFS = [
    "08_submission_package/m5/datasets/tropic/analysis/adam/adrg.pdf",
    "08_submission_package/m5/datasets/tropic/tabulations/sdtm/sdrg.pdf",
    "08_submission_package/m5/datasets/tropic/bimo/datasets/bdrg.pdf",
    "08_submission_package/m5/53-clin-stud-rep/535-rep-effic-safety-stud/mcrpc/5351-stud-rep-contr/tropic/csr.pdf",
]


def main() -> int:
    checks = []
    problems = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            problems.append(f"{name}: {detail}" if detail else name)

    for rel in REQUIRED:
        p = ROOT / rel
        add(f"exists:{rel}", p.is_file(), "missing" if not p.is_file() else "present")

    for rel, patterns in GUIDE_MARKERS.items():
        p = ROOT / rel
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for pat in patterns:
            add(f"marker:{rel}:{pat[:40]}", bool(re.search(pat, text, re.I)), "marker missing")
        if OVERCLAIM.search(text):
            add(f"overclaim:{rel}", False, "positive submission-ready claim found")

    # Traceability must not reintroduce removed false listing claim as active deliverable
    tr = ROOT / "07_reviewer_explanation/guides/TRACEABILITY_MATRIX.md"
    if tr.is_file():
        t = tr.read_text(encoding="utf-8", errors="replace")
        # Allow historical mention of L-01 removal; fail if it claims L-01 is produced
        bad_l01 = re.search(r"(?i)L-01[^\n]{0,80}(produced|deliverable|output)", t)
        add("traceability.no_active_L01_claim", not bad_l01, "possible active L-01 claim")

    # The Markdown sources are converted into the reviewer-facing PDFs during
    # packaging.  Check the rendered text as well: a Latin-1 fallback that
    # turns >=/arrows into '?' or leaves Markdown delimiters in the PDF is a
    # reviewer-facing quality failure, not a source-only lint issue.
    pdftotext = shutil.which("pdftotext")
    add("reviewer_pdf.pdftotext_available", bool(pdftotext), "Poppler pdftotext not found")
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

    status = "PASS" if not problems else "FAIL"
    payload = {
        "gate": "G07",
        "name": "reviewer_package_lock",
        "status": status,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checks": checks,
        "problems": problems,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"G07 Reviewer Package Lock: {status}")
    for p in problems:
        print(f"  - {p}")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
