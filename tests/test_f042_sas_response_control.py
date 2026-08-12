from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SAS_SOURCE = ROOT / "04_analysis_datasets/programs/sas/F042_phase2_pain_derivation.sas"
TRACKED_M5_COPY = (
    ROOT / "08_submission_package/m5/datasets/tropic/analysis/adam/programs/F042_phase2_pain_derivation.sas"
)
ECTD_M5_COPY = (
    ROOT / "08_submission_package/ectd/0000/m5/datasets/tropic/analysis/adam/programs/F042_phase2_pain_derivation.sas"
)


def test_sas_pain_response_requires_confirming_visit_response():
    text = SAS_SOURCE.read_text(encoding="utf-8")
    candidate = text.split(
        "create table work.f042_pain_response_candidates as", 1
    )[1].split("create table work.f042_pain_response_events as", 1)[0]
    events = text.split(
        "create table work.f042_pain_response_events as", 1
    )[1].split("quit;", 1)[0]

    assert "y.ppi_evaluable = 1 and y.as_evaluable = 1" in candidate
    assert "x.base_ppi - y.ppi_value >= 2" in candidate
    assert "(x.base_an - y.as_value) / x.base_an >= 0.5" in candidate
    assert "calculated ppi_response_confirming = 1" in candidate
    assert "calculated as_response_confirming = 1" in candidate
    assert "where ppi_confirmed = 1 or as_confirmed = 1" in events


def test_sas_endpoint_extract_and_release_gate_are_wired():
    sas = SAS_SOURCE.read_text(encoding="utf-8")
    cross_lang = (
        ROOT / "06_qc_evidence/reconciliation/cross_lang_audit.R"
    ).read_text(encoding="utf-8")
    orchestrator = (ROOT / "platform/cibuild.py").read_text(encoding="utf-8")
    verifier = (ROOT / "scripts/verify_release.py").read_text(encoding="utf-8")

    assert "f042_pain_response_prod.csv" in sas
    assert "endpoint_controls" in cross_lang
    assert "F042_PAIN_RESPONSE" in cross_lang
    assert "identical(sas_cmp, r_cmp)" in cross_lang
    assert "SAS_ENDPOINT_CONTROL_FILES" in orchestrator
    assert 'add("recon.F042_PAIN_RESPONSE"' in verifier


def test_tracked_m5_copy_matches_controlled_source():
    # The governed m5 program copy is tracked, so this assertion always runs,
    # including on a fresh data-free CI checkout.
    assert TRACKED_M5_COPY.read_bytes() == SAS_SOURCE.read_bytes()


@pytest.mark.skipif(
    not ECTD_M5_COPY.exists(),
    reason="materialized eCTD m5 copy is gitignored and absent on a fresh checkout",
)
def test_materialized_ectd_copy_matches_controlled_source():
    # The eCTD sequence's m5 subtree is produced by materialize_ectd.py during a
    # data-bearing packaging run; when it is present it must match the source.
    assert ECTD_M5_COPY.read_bytes() == SAS_SOURCE.read_bytes()
