from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform"))

from build_ectd_backbone import classify  # noqa: E402
from check_regulatory_baseline import evaluate  # noqa: E402


def test_current_regulatory_baseline_is_closed():
    result = evaluate(ROOT)
    assert result["status"] == "PASS", result["problems"]


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
        "rule_catalog_entries": 387,
        "checks_reported": 5546,
        "issue_groups": 30,
        "issue_occurrences": 2373,
    }
    assert totals["records"] == sum(row["records"] for row in summary["datasets"])
    assert totals["issue_groups"] == len(summary["issues"])
    assert totals["issue_occurrences"] == sum(row["found"] for row in summary["issues"])
    assert totals["issue_occurrences"] == sum(
        row["occurrences"] for row in summary["residual_families"]
    )
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
