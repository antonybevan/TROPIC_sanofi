#!/usr/bin/env python3
"""Summarize which conformance gates actually executed in data-free CI.

CI is intentionally data-free: real XPTs, the CDISC Library key/offline cache, and
the CDISC CORE engine are not present on a fresh runner. Gates that need them
report SKIPPED/not-run rather than fabricating PASS. This script makes those skips
explicit in the job log so a green CI cannot be mistaken for full conformance.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(rel: str):
    path = ROOT / rel
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": f"unparseable: {rel}"}


def main() -> int:
    print("=== Data-free CI conformance coverage ===")

    adam = _load("06_qc_evidence/conformance/adam_conformance_status.json") or {}
    spec_define = _load("platform/conformance/spec_define_conformance.json") or {}
    spec_data = _load("platform/conformance/spec_data_conformance.json") or {}
    ct = _load("platform/conformance/ct_cross_validation.json") or {}

    def row(label: str, status: str) -> None:
        print(f"  {label:38} {status}")

    row("ADaM conformance (in-repo)", adam.get("status") or "not generated")
    row("Spec -> Define", spec_define.get("status") or "not generated")
    row("Spec -> Data", spec_data.get("status") or "not generated")
    datasets = spec_data.get("datasets")
    if datasets is not None:
        n_skip = sum(1 for r in datasets if r.get("status") == "SKIPPED")
        row("Spec -> Data (dataset-level)", f"{n_skip}/{len(datasets)} datasets SKIPPED (no *_prod.xpt)")
    row("CT cross-validation", ((ct.get("summary") or {}).get("status")) or "not generated")
    row("CDISC CORE engine (full run)", "NOT RUN IN CI — data-bearing local gate (run_core_conformance.sh)")

    print("  Note: a green CI verifies seals, smoke tests, and data-free gates only;")
    print("        it does not re-run SAS/ODA or the full CDISC CORE conformance suite.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
