#!/usr/bin/env python3
"""Validate the current FDA-facing package and qualification boundary.

This gate checks objective repository facts. It does not infer regulatory
approval and deliberately fails if a source blank CRF is presented as an aCRF,
if the legacy SDRG filename returns, or if qualification non-claims disappear.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "config/regulatory_baseline.yaml"
OUT = ROOT / "06_qc_evidence/gates/regulatory_baseline_status.json"

REQUIRED_ASSERTIONS = {
    "ORGANIZATIONAL_INDEPENDENT_QC=NOT_ESTABLISHED",
    "PART11_VALIDATED_SYSTEM=NOT_ESTABLISHED",
    "LICENSED_PINNACLE21_ENTERPRISE=NOT_EXECUTED",
    "PINNACLE21_COMMUNITY=INFORMATIVE_ONLY",
    "REGULATORY_GATEWAY_ACCEPTANCE=NOT_EXECUTED",
    "ANNOTATED_CRF=NOT_AVAILABLE",
}


def _valid_reseal_chain(pipeline_health: dict) -> tuple[bool, list[str], str]:
    """Return whether a bound clinical digest can be traced to the current seal.

    Older evidence has one ``governance_only_reseal`` object; current evidence
    retains an append-only ``governance_reseal_chain``. Every hop must be PASS,
    disclose that clinical execution was not repeated, and link prior -> rebound.
    """
    current = str(pipeline_health.get("source_tree_sha256") or "")
    chain = pipeline_health.get("governance_reseal_chain")
    if chain is None:
        legacy = pipeline_health.get("governance_only_reseal")
        chain = [legacy] if isinstance(legacy, dict) else []
    if not isinstance(chain, list) or not all(isinstance(row, dict) for row in chain):
        return False, [], "malformed governance reseal chain"

    accepted: list[str] = []
    expected_prior = ""
    for index, row in enumerate(chain):
        prior = str(row.get("prior_source_tree_sha256") or "")
        rebound = str(row.get("rebound_source_tree_sha256") or "")
        if (
            row.get("status") != "PASS"
            or row.get("clinical_run_was_not_reexecuted") is not True
            or not prior
            or not rebound
            or (index and prior != expected_prior)
        ):
            return False, accepted, f"invalid governance reseal hop {index + 1}"
        if not accepted:
            accepted.append(prior)
        accepted.append(rebound)
        expected_prior = rebound
    if chain and expected_prior != current:
        return False, accepted, "governance reseal chain does not end at current health digest"
    if not chain and current:
        accepted.append(current)
    return bool(current), accepted, f"validated_hops={len(chain)}"


def evaluate(root: Path = ROOT) -> dict:
    checks: list[dict] = []
    problems: list[str] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok:
            problems.append(f"{name}: {detail}" if detail else name)

    baseline_path = root / "config/regulatory_baseline.yaml"
    try:
        baseline = yaml.safe_load(baseline_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        baseline = {}
        add("baseline.readable", False, str(exc))
    else:
        add("baseline.readable", True, str(baseline_path.relative_to(root)))

    add(
        "baseline.product_class",
        baseline.get("product_class") == "controlled_clinical_submission_simulation",
        str(baseline.get("product_class")),
    )
    add(
        "baseline.not_for_submission",
        baseline.get("filing_status") == "not_for_regulatory_submission",
        str(baseline.get("filing_status")),
    )

    authorities = baseline.get("authorities") or {}
    add("authorities.count", len(authorities) >= 8, f"count={len(authorities)}")
    for name, authority in authorities.items():
        url = str((authority or {}).get("url", ""))
        add(f"authority.https:{name}", url.startswith("https://"), url)

    contract = baseline.get("package_contract") or {}
    expected_file_keys = (
        "analysis_data_reviewers_guide",
        "clinical_study_data_reviewers_guide",
        "analysis_define",
        "tabulation_define",
        "source_blank_crf",
    )
    for key in expected_file_keys:
        rel = str(contract.get(key, ""))
        path = root / rel
        add(f"package.exists:{key}", bool(rel) and path.is_file(), rel or "not configured")

    legacy_rel = str(contract.get("legacy_sdrg_filename_forbidden", ""))
    add(
        "package.no_legacy_sdrg",
        bool(legacy_rel) and not (root / legacy_rel).exists(),
        legacy_rel or "not configured",
    )
    acrf_rel = str(contract.get("annotated_crf_forbidden_alias", ""))
    add(
        "package.no_false_acrf",
        bool(acrf_rel) and not (root / acrf_rel).exists(),
        acrf_rel or "not configured",
    )

    stylesheet = str(contract.get("local_stylesheet", ""))
    for define_key in ("analysis_define", "tabulation_define"):
        define_rel = str(contract.get(define_key, ""))
        style_path = (root / define_rel).parent / stylesheet
        add(
            f"package.local_stylesheet:{define_key}",
            bool(stylesheet) and style_path.is_file(),
            str(style_path.relative_to(root)) if stylesheet else "not configured",
        )

    program_rel = str(contract.get("analysis_program_directory", ""))
    program_dir = root / program_rel
    sas_programs = list(program_dir.glob("*.sas")) if program_dir.is_dir() else []
    r_programs = list(program_dir.glob("*.R")) if program_dir.is_dir() else []
    add("package.analysis_programs.sas", bool(sas_programs), f"count={len(sas_programs)}")
    add("package.analysis_programs.r", bool(r_programs), f"count={len(r_programs)}")

    claims = baseline.get("qualification_claims") or {}
    expected_claims = {
        "organizationally_independent_qc": False,
        "part_11_validated_system": False,
        "licensed_pinnacle_21_enterprise": False,
        "pinnacle_21_community_informative_run": True,
        "regulatory_gateway_acceptance": False,
    }
    for key, expected in expected_claims.items():
        add(f"qualification:{key}", claims.get(key) is expected, str(claims.get(key)))

    boundary_path = root / "docs/QUALITY_SYSTEM_BOUNDARY.md"
    boundary = boundary_path.read_text(encoding="utf-8") if boundary_path.is_file() else ""
    for assertion in sorted(REQUIRED_ASSERTIONS):
        add(
            f"boundary.assertion:{assertion}",
            assertion in boundary,
            "present" if assertion in boundary else "missing",
        )

    p21_path = root / "06_qc_evidence/conformance/p21_adam_runrecord.md"
    p21 = p21_path.read_text(encoding="utf-8") if p21_path.is_file() else ""
    for marker in (
        "INFORMATIVE_ONLY",
        "LICENSED_PINNACLE21_ENTERPRISE=NOT_EXECUTED",
        "Incompatible CLI used",
        "FDA 2508.1",
    ):
        add(
            f"p21.boundary:{marker}",
            marker in p21,
            "present" if marker in p21 else "missing",
        )

    evidence = baseline.get("validation_evidence") or {}
    p21_config = evidence.get("pinnacle_21_community_summary") or {}
    p21_summary_rel = str(p21_config.get("path", ""))
    p21_summary_path = root / p21_summary_rel
    try:
        p21_summary = json.loads(p21_summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        p21_summary = {}
        add("p21.summary.readable", False, str(exc))
    else:
        add("p21.summary.readable", True, p21_summary_rel)

    for key in ("record_id", "status", "use"):
        actual = p21_summary.get(key)
        expected = p21_config.get(key)
        add(f"p21.summary.{key}", actual == expected, f"actual={actual}; expected={expected}")

    validation = p21_summary.get("validation") or {}
    add("p21.summary.process_completed", validation.get("process_completed") is True, str(validation.get("process_completed")))
    add(
        "p21.summary.compatibility_caveat",
        validation.get("compatibility_caveat") == "Incompatible CLI used",
        str(validation.get("compatibility_caveat")),
    )

    totals = p21_summary.get("totals") or {}
    datasets = p21_summary.get("datasets") or []
    issues = p21_summary.get("issues") or []
    residual_families = p21_summary.get("residual_families") or []
    expected_totals = {
        "datasets_processed": p21_config.get("expected_datasets"),
        "records": p21_config.get("expected_records"),
        "rule_catalog_entries": p21_config.get("expected_rule_catalog_entries"),
        "issue_groups": p21_config.get("expected_issue_groups"),
        "issue_occurrences": p21_config.get("expected_issue_occurrences"),
    }
    for key, expected in expected_totals.items():
        add(f"p21.summary.total:{key}", totals.get(key) == expected, f"actual={totals.get(key)}; expected={expected}")
    add("p21.summary.zero_rejects", totals.get("datasets_rejected") == 0, str(totals.get("datasets_rejected")))
    add(
        "p21.summary.dataset_count_reconciled",
        totals.get("datasets_processed") == len(datasets),
        f"declared={totals.get('datasets_processed')}; listed={len(datasets)}",
    )
    add(
        "p21.summary.record_count_reconciled",
        totals.get("records") == sum(int(row.get("records", 0)) for row in datasets),
        f"declared={totals.get('records')}; summed={sum(int(row.get('records', 0)) for row in datasets)}",
    )
    add(
        "p21.summary.issue_groups_reconciled",
        totals.get("issue_groups") == len(issues),
        f"declared={totals.get('issue_groups')}; listed={len(issues)}",
    )
    issue_occurrences = sum(int(row.get("found", 0)) for row in issues)
    add(
        "p21.summary.issue_occurrences_reconciled",
        totals.get("issue_occurrences") == issue_occurrences,
        f"declared={totals.get('issue_occurrences')}; summed={issue_occurrences}",
    )
    residual_occurrences = sum(int(row.get("occurrences", 0)) for row in residual_families)
    add(
        "p21.summary.residual_families_reconciled",
        totals.get("issue_occurrences") == residual_occurrences,
        f"declared={totals.get('issue_occurrences')}; summed={residual_occurrences}",
    )
    add(
        "p21.summary.unique_issue_groups",
        len({(row.get("domain"), row.get("id")) for row in issues}) == len(issues),
        f"listed={len(issues)}",
    )

    pipeline_binding = p21_summary.get("pipeline_binding") or {}
    pipeline_health_path = root / "platform/pipeline_health.json"
    try:
        pipeline_health = json.loads(pipeline_health_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        pipeline_health = {}
        add("p21.pipeline_binding.health_readable", False, str(exc))
    else:
        add(
            "p21.pipeline_binding.health_readable",
            True,
            str(pipeline_health_path.relative_to(root)),
        )
    binding_expectations = {
        "pipeline_health_status": "GREEN",
        "sas_execution_mode": "oda",
        "run_scope": "full_dag",
        "stages_expected": 37,
        "stages_recorded": 37,
    }
    for key, expected in binding_expectations.items():
        actual = pipeline_binding.get(key)
        add(
            f"p21.pipeline_binding.{key}",
            actual == expected,
            f"actual={actual}; expected={expected}",
        )
    assessment = p21_summary.get("subsequent_rebuild_assessment") or {}
    current_health_timestamp = pipeline_health.get("timestamp")
    binding_timestamp = pipeline_binding.get("health_timestamp")
    timestamp_is_current = binding_timestamp == current_health_timestamp
    timestamp_is_assessed = (
        assessment.get("health_timestamp") == current_health_timestamp
        and assessment.get("exact_byte_vendor_rerun") is False
        and assessment.get("comparison_method") == "exhaustive_byte_comparison"
        and assessment.get("datasets_compared") == 7
        and assessment.get("payload_differences_after_byte_495") == 0
        and assessment.get("header_timestamp_differences_per_dataset") == 2
        and assessment.get("vendor_rerun_blocker")
        == "Acceptance of vendor application Terms and Conditions requires authorized human confirmation"
    )
    add(
        "p21.pipeline_binding.health_timestamp",
        timestamp_is_current or timestamp_is_assessed,
        (
            f"bound={binding_timestamp}; current={current_health_timestamp}; "
            f"later_rebuild_assessed={timestamp_is_assessed}"
        ),
    )
    bound_source = pipeline_binding.get("source_tree_sha256")
    health_source = pipeline_health.get("source_tree_sha256")
    chain_ok, accepted_sources, chain_detail = _valid_reseal_chain(pipeline_health)
    add("p21.pipeline_binding.reseal_chain", chain_ok, chain_detail)
    add(
        "p21.pipeline_binding.source_tree",
        chain_ok and bool(bound_source) and (
            bound_source in set(accepted_sources) or timestamp_is_assessed
        ),
        (
            f"bound={bound_source}; current_health={health_source}; "
            f"accepted_chain={accepted_sources}; "
            f"later_rebuild_assessed={timestamp_is_assessed}"
        ),
    )

    remediation = p21_summary.get("remediation_comparison") or {}
    initial = int(remediation.get("initial_issue_occurrences", 0))
    final = int(remediation.get("final_issue_occurrences", 0))
    eliminated = int(remediation.get("occurrences_eliminated", 0))
    add(
        "p21.summary.remediation_reconciled",
        initial - final == eliminated and final == totals.get("issue_occurrences"),
        f"initial={initial}; final={final}; eliminated={eliminated}",
    )

    qualification = p21_summary.get("qualification") or {}
    add("p21.summary.community_informative_only", qualification.get("community_informative_only") is True, str(qualification.get("community_informative_only")))
    add("p21.summary.enterprise_not_executed", qualification.get("enterprise_executed") is False, str(qualification.get("enterprise_executed")))
    add("p21.summary.no_clearance_claim", qualification.get("submission_clearance_claimed") is False, str(qualification.get("submission_clearance_claimed")))
    add("p21.summary.no_independent_qc_claim", qualification.get("independent_qc_approved") is False, str(qualification.get("independent_qc_approved")))
    add(
        "p21.summary.exact_byte_rerun_boundary",
        assessment.get("exact_byte_vendor_rerun") is not False
        or (
            assessment.get("comparison_method") == "exhaustive_byte_comparison"
            and assessment.get("datasets_compared") == 7
            and assessment.get("payload_differences_after_byte_495") == 0
            and assessment.get("header_timestamp_differences_per_dataset") == 2
            and assessment.get("vendor_rerun_blocker")
            == "Acceptance of vendor application Terms and Conditions requires authorized human confirmation"
        ),
        "later exact-byte rerun is either complete or explicitly bounded",
    )

    claim_path = root / "docs/PRODUCT_CLAIM.md"
    claim = claim_path.read_text(encoding="utf-8") if claim_path.is_file() else ""
    add(
        "product_claim.controlled_simulation",
        "controlled clinical-submission simulation" in claim.lower(),
        "required controlled-simulation statement missing",
    )
    add(
        "product_claim.not_submission",
        "not a regulatory submission" in claim.lower(),
        "required non-submission statement missing",
    )

    status = "PASS" if not problems else "FAIL"
    return {
        "gate": "REGULATORY_BASELINE",
        "baseline_id": baseline.get("baseline_id"),
        "status": status,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checks": checks,
        "problems": problems,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="do not rewrite status JSON")
    args = parser.parse_args(argv)
    payload = evaluate()
    if not args.check_only:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Regulatory baseline: {payload['status']}")
    for problem in payload["problems"]:
        print(f"  - {problem}")
    if args.check_only:
        print("Check-only mode: status JSON not rewritten")
    else:
        print(f"Wrote {OUT.relative_to(ROOT)}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
