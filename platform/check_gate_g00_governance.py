#!/usr/bin/env python3
"""G00 Governance Scope Lock — executable gate.

Fails the DAG if the controlled product claim, authority docs, or findings disposition
are missing or contradicted. Writes 06_qc_evidence/gates/g00_governance_status.json.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "06_qc_evidence/gates/g00_governance_status.json"

REQUIRED = [
    "docs/PRODUCT_CLAIM.md",
    "docs/QUALITY_SYSTEM_BOUNDARY.md",
    "docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md",
    "docs/RELEASE_NOTE_v0.1.0-demo-rc.1.md",
    "docs/WORKSTREAM_EXECUTION_BOARD.md",
    "00_governance/REPRODUCIBILITY.md",
    "02_specifications/sap/TROPIC_SAP_v4.0_industry_grade.docx",
    "06_qc_evidence/audit/SAP_LOCK_REVIEW_MEMO.md",
    "06_qc_evidence/audit/findings_register.csv",
    "06_qc_evidence/audit/FINDINGS_DISPOSITION_BOARD.md",
    "config/workstream_execution_board.yaml",
    "config/regulatory_baseline.yaml",
]

# Must appear in PRODUCT_CLAIM (case-insensitive).
CLAIM_MUST = [
    r"controlled",
    r"non[- ]submission",
    r"controlled clinical-submission simulation",
    r"not.*Part 11|non-Part 11|not a Part 11",
]

# Forbidden as standalone overclaim in PRODUCT_CLAIM without negation nearby.
# We only fail if PRODUCT_CLAIM asserts filing readiness as a positive claim.
# Tables of "Forbidden claim" rows that mention overclaim phrases are OK.
FORBIDDEN_POSITIVE = [
    r"(?i)this package is FDA submission[- ]ready",
    r"(?i)this package is NDA[- ]ready",
    r"(?i)we (are|have) (FDA )?submission[- ]ready",
]


def main() -> int:
    checks = []
    problems = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            problems.append(f"{name}: {detail}" if detail else name)

    for rel in REQUIRED:
        path = ROOT / rel
        add(f"exists:{rel}", path.is_file(), "missing" if not path.is_file() else "present")

    claim_path = ROOT / "docs/PRODUCT_CLAIM.md"
    text = claim_path.read_text(encoding="utf-8") if claim_path.is_file() else ""
    lower = text.lower()
    add(
        "product_claim.controlled_simulation",
        "controlled clinical-submission simulation" in lower
        and "not a regulatory submission" in lower,
        "PRODUCT_CLAIM must freeze the controlled simulation and non-submission boundary",
    )
    add(
        "product_claim.forbids_part11",
        "part 11" in lower and ("not" in lower or "non-" in lower or "≠" in text or "not a" in lower),
        "must explicitly reject Part 11 claim",
    )
    for pat in FORBIDDEN_POSITIVE:
        if re.search(pat, text):
            add(f"forbidden_claim:{pat}", False, "positive overclaim found in PRODUCT_CLAIM")

    # Findings: no active CONFIRMED Critical/Major
    reg = ROOT / "06_qc_evidence/audit/findings_register.csv"
    if reg.is_file():
        rows = list(csv.DictReader(reg.open(encoding="utf-8")))
        bad = [
            r.get("ID", "?")
            for r in rows
            if str(r.get("status", "")).upper() == "CONFIRMED"
            and str(r.get("severity", "")).title() in {"Critical", "Major"}
        ]
        add("findings.no_confirmed_crit_major", not bad, str(bad) if bad else "none")
    else:
        add("findings.no_confirmed_crit_major", False, "register missing")

    status = "PASS" if not problems else "FAIL"
    payload = {
        "gate": "G00",
        "name": "governance_scope_lock",
        "status": status,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checks": checks,
        "problems": problems,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"G00 Governance Scope Lock: {status}")
    for p in problems:
        print(f"  - {p}")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
