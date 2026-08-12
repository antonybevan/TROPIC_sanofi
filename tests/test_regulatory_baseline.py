from __future__ import annotations

import json
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform"))

from build_ectd_backbone import classify  # noqa: E402
from check_regulatory_baseline import _valid_reseal_chain, evaluate  # noqa: E402

_RESEAL_SPEC = importlib.util.spec_from_file_location(
    "rebind_governance_seal",
    ROOT / "scripts/rebind_governance_seal.py",
)
assert _RESEAL_SPEC and _RESEAL_SPEC.loader
_RESEAL_MODULE = importlib.util.module_from_spec(_RESEAL_SPEC)
_RESEAL_SPEC.loader.exec_module(_RESEAL_MODULE)
_health_is_valid_prior_reseal = _RESEAL_MODULE._health_is_valid_prior_reseal


def test_current_regulatory_baseline_is_closed():
    result = evaluate(ROOT)
    assert result["status"] == "PASS", result["problems"]


def test_governance_reseal_chain_accepts_valid_multi_hop_history():
    health = {
        "source_tree_sha256": "c" * 64,
        "governance_reseal_chain": [
            {
                "status": "PASS",
                "prior_source_tree_sha256": "a" * 64,
                "rebound_source_tree_sha256": "b" * 64,
                "clinical_run_was_not_reexecuted": True,
            },
            {
                "status": "PASS",
                "prior_source_tree_sha256": "b" * 64,
                "rebound_source_tree_sha256": "c" * 64,
                "clinical_run_was_not_reexecuted": True,
            },
        ],
    }
    ok, accepted, detail = _valid_reseal_chain(health)
    assert ok, detail
    assert accepted == ["a" * 64, "b" * 64, "c" * 64]


def test_governance_reseal_chain_rejects_discontinuous_history():
    health = {
        "source_tree_sha256": "c" * 64,
        "governance_reseal_chain": [
            {
                "status": "PASS",
                "prior_source_tree_sha256": "a" * 64,
                "rebound_source_tree_sha256": "b" * 64,
                "clinical_run_was_not_reexecuted": True,
            },
            {
                "status": "PASS",
                "prior_source_tree_sha256": "x" * 64,
                "rebound_source_tree_sha256": "c" * 64,
                "clinical_run_was_not_reexecuted": True,
            },
        ],
    }
    ok, _, _ = _valid_reseal_chain(health)
    assert not ok


def test_current_baseline_accepts_disclosed_later_header_only_rebuild():
    result = evaluate(ROOT)
    timestamp_check = next(
        row for row in result["checks"]
        if row["name"] == "p21.pipeline_binding.health_timestamp"
    )
    boundary_check = next(
        row for row in result["checks"]
        if row["name"] == "p21.summary.exact_byte_rerun_boundary"
    )
    assert timestamp_check["ok"], timestamp_check
    assert "later_rebuild_assessed=True" in timestamp_check["detail"]
    assert boundary_check["ok"], boundary_check


def test_prior_governance_reseal_validation_is_history_independent():
    base = {
        "timestamp": "2026-08-12T10:28:13+00:00",
        "pipeline_health_status": "GREEN",
        "sas_execution_mode": "oda",
        "run_scope": "full_dag",
        "source_tree_sha256": "a" * 64,
    }
    current = {
        **base,
        "source_tree_sha256": "c" * 64,
        "governance_reseal_chain": [
            {
                "status": "PASS",
                "clinical_run_was_not_reexecuted": True,
                "prior_source_tree_sha256": "a" * 64,
                "rebound_source_tree_sha256": "b" * 64,
            },
            {
                "status": "PASS",
                "clinical_run_was_not_reexecuted": True,
                "prior_source_tree_sha256": "b" * 64,
                "rebound_source_tree_sha256": "c" * 64,
            },
        ],
    }
    assert _health_is_valid_prior_reseal(base, current)
    current["governance_reseal_chain"][1]["prior_source_tree_sha256"] = "x" * 64
    assert not _health_is_valid_prior_reseal(base, current)


def test_current_csdrg_filename_receives_the_fda_stf_tag():
    assert classify("m5/datasets/tropic/tabulations/sdtm/csdrg.pdf") == (
        "data-tabulation-data-reviewers-guide",
        "us",
    )
    assert classify("m5/datasets/tropic/tabulations/sdtm/sdrg.pdf") == (None, None)


def test_p21_yes_only_flags_are_derived_as_y_or_null():
    sas_adae = (ROOT / "04_analysis_datasets/programs/sas/A_adae_io_respec.sas").read_text()
    sas_adcm = (ROOT / "04_analysis_datasets/programs/sas/A_adcm_generation.sas").read_text()
    sas_adlb = (ROOT / "04_analysis_datasets/programs/sas/A_adlb_generation.sas").read_text()
    r_adae = (ROOT / "04_analysis_datasets/programs/r/v_adae_io_validation.R").read_text()
    r_adcm = (ROOT / "04_analysis_datasets/programs/r/v_adcm_validation.R").read_text()
    r_adlb = (ROOT / "04_analysis_datasets/programs/r/v_adlb_validation.R").read_text()

    assert "else TRTEMFL = 'N'" not in sas_adae
    assert "else TRTEMFL = 'N'" not in sas_adcm
    assert "else ANL01FL = 'N'" not in sas_adlb
    assert "BASEFL" not in sas_adlb
    assert "if not missing(BASESEQ) and lbseq = BASESEQ then ABLFL = 'Y';" in sas_adlb
    assert "else call missing(ABLFL);" in sas_adlb
    assert 'TRTEMFL == "N"' not in r_adae
    assert 'TRTEMFL = if_else(!is.na(cmstdt) & cmstdt >= TRTSDT, "Y", "N")' not in r_adcm
    assert 'ANL01FL = if_else(AVISITN != 99.0 & row_number() == 1, "Y", "N")' not in r_adlb
    assert "BASEFL" not in r_adlb
    assert 'ABLFL = if_else(!is.na(BASESEQ) & LBSEQ == BASESEQ, "Y", NA_character_)' in r_adlb


def test_definitive_p21_summary_is_self_reconciling_and_non_qualifying():
    summary = json.loads(
        (ROOT / "06_qc_evidence/conformance/p21_adam_summary.json").read_text()
    )
    totals = summary["totals"]
    assert summary["status"] == "EXECUTED_WITH_OPEN_FINDINGS_AND_COMPATIBILITY_CAVEAT"
    assert summary["use"] == "INFORMATIVE_ONLY"
    assert summary["validation"]["process_completed"] is True
    assert summary["validation"]["compatibility_caveat"] == "Incompatible CLI used"
    assert totals == {
        "datasets_processed": 7,
        "datasets_rejected": 0,
        "records": 121320,
        "rule_catalog_entries": 388,
        "issue_groups": 30,
        "issue_occurrences": 2373,
    }
    assert totals["records"] == sum(row["records"] for row in summary["datasets"])
    assert totals["issue_groups"] == len(summary["issues"])
    assert totals["issue_occurrences"] == sum(row["found"] for row in summary["issues"])
    assert totals["issue_occurrences"] == sum(
        row["occurrences"] for row in summary["residual_families"]
    )
    assert summary["pipeline_binding"] == {
        "health_timestamp": "2026-08-12T09:29:59.539074+00:00",
        "pipeline_health_status": "GREEN",
        "sas_execution_mode": "oda",
        "run_scope": "full_dag",
        "stages_expected": 37,
        "stages_recorded": 37,
        "source_tree_sha256": "81dadd3c02bf521bf11fce32f67f30ec4c70913059675cc576c895b8182a605d",
    }
    assert summary["remediation_comparison"]["occurrences_eliminated"] == 84238
    assert summary["remediation_comparison"]["percent_reduction"] == 97.3
    assert not {"AD0269", "AD0127A", "AD0164", "AD0178"} & {
        row["id"] for row in summary["issues"]
    }
    assert summary["qualification"] == {
        "community_informative_only": True,
        "enterprise_executed": False,
        "submission_clearance_claimed": False,
        "independent_qc_approved": False,
    }
    assert summary["subsequent_rebuild_assessment"] == {
        "health_timestamp": "2026-08-12T10:28:13.216075+00:00",
        "comparison_method": "exhaustive_byte_comparison",
        "datasets_compared": 7,
        "payload_differences_after_byte_495": 0,
        "header_timestamp_differences_per_dataset": 2,
        "comparison": (
            "XPT payload byte-identical after byte 495 for all seven datasets; "
            "differences are confined to two SAS XPORT header timestamps per file"
        ),
        "exact_byte_vendor_rerun": False,
        "vendor_rerun_blocker": (
            "Acceptance of vendor application Terms and Conditions requires authorized "
            "human confirmation"
        ),
    }
