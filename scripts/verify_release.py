#!/usr/bin/env python3
"""Path A release verification without re-running ODA/SAS.

Rechecks sealed control JSONs, product claim docs, and findings disposition.
Exit 0 only if all hard checks pass.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(rel: str):
    path = ROOT / rel
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    def add(name: str, cond: bool, detail: str = "") -> None:
        checks.append((name, bool(cond), detail))

    h = load("platform/pipeline_health.json") or {}
    stages = h.get("stages") or {}
    add("health.schema_version", h.get("schema_version") == "run_scope_v1", str(h.get("schema_version")))
    add("health.status_GREEN", h.get("pipeline_health_status") == "GREEN", str(h.get("pipeline_health_status")))
    add("health.mode_real_sas", h.get("sas_execution_mode") in {"oda", "local"}, str(h.get("sas_execution_mode")))
    add("health.full_dag", h.get("run_scope") == "full_dag", str(h.get("run_scope")))
    add(
        "health.full_stage_count",
        # Phase-2 DAG is 33 stages (G00/G02/G07 + prior 30). Accept >=30 for forward/back compat.
        int(h.get("stages_expected") or 0) >= 30 and len(stages) >= 30
        and int(h.get("stages_expected") or 0) == len(stages),
        f"expected={h.get('stages_expected')} n={len(stages)}",
    )
    add("health.no_not_run", not (h.get("stages_not_run") or []), str(h.get("stages_not_run")))
    non_pass = [k for k, v in stages.items() if v not in {"PASS", "SKIPPED"}]
    add("health.all_pass_or_skip", not non_pass, str(non_pass[:8]))
    add("health.provenance", (h.get("provenance_guard") or {}).get("passed") is True, "")

    r = load("platform/reconciliation_status.json") or {}
    add("recon.PASS", r.get("overall") == "PASS", str(r.get("overall")))
    add("recon.not_sim", r.get("simulated") is False, str(r.get("simulated")))

    rr = load("platform/results_reconciliation_status.json") or {}
    add("results_recon.PASS", rr.get("overall") == "PASS", str(rr.get("overall")))

    adm = load("platform/admiral_reconciliation_status.json") or {}
    add("admiral.PASS", adm.get("overall") == "PASS", str(adm.get("overall")))
    add(
        "admiral.dag_stage",
        stages.get("Admiral Core Reconciliation") == "PASS",
        str(stages.get("Admiral Core Reconciliation")),
    )

    tfl = load("platform/tfl_output_index_status.json") or {}
    add("tfl.pass", tfl.get("status") == "pass", str(tfl.get("status")))
    cc = tfl.get("controlled_catalog") or {}
    add("tfl.catalog_pass", cc.get("status", "pass") == "pass", str(cc.get("status")))

    vs = load("platform/validation_strategy/validation_strategy_status.json") or {}
    add("validation_strategy.PASS", vs.get("status") == "PASS", str(vs.get("status")))

    lg = load("platform/log_cleanliness/log_cleanliness_status.json") or {}
    add("log_cleanliness.PASS", lg.get("status") == "PASS", str(lg.get("status")))

    rm = load("platform/release_run_manifest/release_run_manifest.json") or {}
    add("release_manifest.PASS", rm.get("status") == "PASS", str(rm.get("status")))
    add(
        "release_manifest.grade",
        rm.get("evidence_grade") == "release_candidate",
        str(rm.get("evidence_grade")),
    )

    rc = load("platform/release_candidate/release_candidate_status.json") or {}
    add("release_candidate.PASS", rc.get("status") == "PASS", str(rc.get("status")))
    add("release_candidate.blockers_0", rc.get("blocker", 1) == 0, str(rc.get("blocker")))

    add("product_claim.exists", (ROOT / "docs/PRODUCT_CLAIM.md").is_file(), "")
    add(
        "known_diff_memo.exists",
        (ROOT / "docs/workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md").is_file(),
        "",
    )
    add(
        "workstream_board.exists",
        (ROOT / "docs/WORKSTREAM_EXECUTION_BOARD.md").is_file(),
        "",
    )

    findings_path = ROOT / "06_qc_evidence/audit/findings_register.csv"
    if findings_path.is_file():
        rows = list(csv.DictReader(findings_path.open(encoding="utf-8")))
        active_conf = [
            r["ID"]
            for r in rows
            if str(r.get("status", "")).upper() == "CONFIRMED"
            and str(r.get("severity", "")).title() in {"Critical", "Major"}
        ]
        add("findings.no_confirmed_crit_major", not active_conf, str(active_conf))
    else:
        add("findings.no_confirmed_crit_major", False, "missing findings_register.csv")

    print("=== TROPIC Path A release verification (no ODA rerun) ===")
    print(f"root: {ROOT}")
    print()
    for name, cond, detail in checks:
        if cond:
            print(f"OK:   {name}")
        else:
            print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))
    passed = sum(1 for _, c, _ in checks if c)
    print("---")
    print(f"summary: {passed}/{len(checks)} checks passed")
    if passed != len(checks):
        print("VERIFY_RELEASE: FAIL")
        return 1
    print("VERIFY_RELEASE: PASS")
    print("Note: Rechecks seals/control JSONs only; does not prove SAS is still reachable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
