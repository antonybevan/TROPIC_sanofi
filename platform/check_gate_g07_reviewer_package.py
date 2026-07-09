#!/usr/bin/env python3
"""G07 Reviewer Package Lock — executable gate.

Ensures ADRG/SDRG/BDRG and supporting reviewer packs exist and carry Path A
non-claim / residual-risk pointers before packaging language is trusted.
"""
from __future__ import annotations

import json
import re
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
