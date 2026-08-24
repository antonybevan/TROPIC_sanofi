from __future__ import annotations

import hashlib
import json
import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform"))

from build_ectd_backbone import classify  # noqa: E402
from build_release_run_manifest import (  # noqa: E402
    CONTROL_FILES,
    REVIEW_SURFACE_FILES,
    REVIEW_SURFACE_GLOBS,
)
from check_regulatory_baseline import (  # noqa: E402
    _manifest_stage_names,
    _valid_reseal_chain,
    evaluate,
)
from governance_reseal_policy import (  # noqa: E402
    RESEALABLE_EXACT_PATHS,
    governance_chain_policy_problems,
    is_resealable_path,
)

_RESEAL_SPEC = importlib.util.spec_from_file_location(
    "rebind_governance_seal",
    ROOT / "scripts/rebind_governance_seal.py",
)
assert _RESEAL_SPEC and _RESEAL_SPEC.loader
_RESEAL_MODULE = importlib.util.module_from_spec(_RESEAL_SPEC)
_RESEAL_SPEC.loader.exec_module(_RESEAL_MODULE)
_health_is_valid_prior_reseal = _RESEAL_MODULE._health_is_valid_prior_reseal


def _reseal_health(*, changed_paths: list[str]) -> dict:
    timestamp = "2026-08-23T17:47:35.766117+00:00"
    return {
        "timestamp": timestamp,
        "pipeline_health_status": "GREEN",
        "sas_execution_mode": "oda",
        "run_scope": "full_dag",
        "source_tree_sha256": "b" * 64,
        "governance_reseal_chain": [
            {
                "status": "PASS",
                "base_revision": "1" * 40,
                "clinical_run_timestamp": timestamp,
                "prior_source_tree_sha256": "a" * 64,
                "rebound_source_tree_sha256": "b" * 64,
                "changed_paths": changed_paths,
                "clinical_run_was_not_reexecuted": True,
            }
        ],
    }


def test_current_regulatory_baseline_is_closed():
    result = evaluate(ROOT)
    assert result["status"] == "PASS", result["problems"]


def test_resealable_exact_paths_are_all_hash_sealed_release_surfaces():
    sealed_release_surfaces = set(CONTROL_FILES) | set(REVIEW_SURFACE_FILES)
    assert RESEALABLE_EXACT_PATHS <= sealed_release_surfaces


def test_dashboard_reseal_and_review_hash_surfaces_have_direct_jpg_parity():
    assert REVIEW_SURFACE_GLOBS == [
        "06_qc_evidence/audit/dashboard_evidence/*.[jJ][pP][gG]"
    ]
    for filename in ("reviewer-home.jpg", "reviewer-home.JPG", "reviewer-home.JpG"):
        path = f"06_qc_evidence/audit/dashboard_evidence/{filename}"
        assert is_resealable_path(path), path
    for path in (
        "06_qc_evidence/audit/dashboard_evidence/nested/reviewer-home.jpg",
        "06_qc_evidence/audit/dashboard_evidence/reviewer-home.jpeg",
        "06_qc_evidence/audit/dashboard_evidence/reviewer-home.png",
    ):
        assert not is_resealable_path(path), path


def test_governance_reseal_allowlist_is_reviewer_only():
    for path in (
        "README.md",
        "06_qc_evidence/audit/dashboard_evidence/reviewer-home.jpg",
    ):
        assert _RESEAL_MODULE._is_allowed(path), path

    critical = (
        "platform/cibuild.py",
        "platform/build_release_run_manifest.py",
        "scripts/verify_release.py",
        "scripts/rebind_governance_seal.py",
        ".github/workflows/ci.yml",
        ".github/CODEOWNERS",
        "requirements-ci.lock",
        "requirements-ci-build.lock",
        "requirements-core-build.lock",
        "requirements-core.txt",
        "requirements-core.lock",
        "renv.lock",
        "config/regulatory_baseline.yaml",
        "config/regulatory_source_inventory.yaml",
        "config/study_manifest.yaml",
        "00_governance/REPRODUCIBILITY.md",
        "docs/PRODUCT_CLAIM.md",
        "docs/QUALITY_SYSTEM_BOUNDARY.md",
        "docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md",
        "tests/test_regulatory_baseline.py",
    )
    for path in critical:
        assert not _RESEAL_MODULE._is_allowed(path), path
        assert _RESEAL_MODULE._requires_fresh_run(path), path

    assert not _RESEAL_MODULE._is_allowed("docs/unreviewed_new_claim.md")
    assert not _RESEAL_MODULE._is_allowed(
        "06_qc_evidence/audit/dashboard_evidence/status.json"
    )


def test_governance_reseal_chain_rejects_prior_control_plane_reseal():
    health = _reseal_health(changed_paths=["README.md", "platform/cibuild.py"])
    problems = _RESEAL_MODULE._governance_chain_policy_problems(health)
    assert any("platform/cibuild.py" in problem for problem in problems)


def test_governance_reseal_chain_accepts_reviewer_only_history():
    health = _reseal_health(changed_paths=["README.md"])
    assert _RESEAL_MODULE._governance_chain_policy_problems(health) == []


def test_regulatory_gate_rejects_changed_path_and_timestamp_policy_bypasses():
    changed_path = _reseal_health(changed_paths=["README.md", "platform/cibuild.py"])
    ok, accepted, detail = _valid_reseal_chain(changed_path)
    assert not ok
    assert accepted == []
    assert "platform/cibuild.py" in detail

    wrong_timestamp = _reseal_health(changed_paths=["README.md"])
    wrong_timestamp["governance_reseal_chain"][0]["clinical_run_timestamp"] = (
        "2026-08-23T17:47:36+00:00"
    )
    ok, accepted, detail = _valid_reseal_chain(wrong_timestamp)
    assert not ok
    assert accepted == []
    assert "carried clinical timestamp" in detail


def test_regulatory_gate_accepts_valid_reviewer_only_reseal():
    health = _reseal_health(changed_paths=["README.md"])
    ok, accepted, detail = _valid_reseal_chain(health)
    assert ok, detail
    assert accepted == ["a" * 64, "b" * 64]
    assert governance_chain_policy_problems(health) == []


def test_governance_reseal_requires_clean_committed_snapshot():
    with patch.object(
        _RESEAL_MODULE,
        "_material_worktree_changes",
        return_value=[" M config/study_manifest.yaml"],
    ):
        with pytest.raises(SystemExit, match="dirty source snapshot"):
            _RESEAL_MODULE.main(["base"])


def test_governance_base_cannot_be_head():
    health = {"source_tree_sha256": "a" * 64}
    with patch.object(_RESEAL_MODULE, "_resolve_commit", return_value="f" * 40):
        with pytest.raises(ValueError, match="must predate"):
            _RESEAL_MODULE._authenticated_base_revision("HEAD", health)


def test_governance_base_must_rehash_to_carried_digest():
    health = {"source_tree_sha256": "a" * 64}

    def resolve(revision: str) -> str:
        return "b" * 40 if revision == "base" else "c" * 40

    with (
        patch.object(_RESEAL_MODULE, "_resolve_commit", side_effect=resolve),
        patch.object(_RESEAL_MODULE, "_is_ancestor", return_value=True),
        patch.object(_RESEAL_MODULE, "_git_json", return_value=health),
        patch.object(_RESEAL_MODULE, "_verify_manifest_health_binding"),
        patch.object(_RESEAL_MODULE, "_source_digest_at_revision", return_value="d" * 64),
    ):
        with pytest.raises(ValueError, match="genuine-run digest"):
            _RESEAL_MODULE._authenticated_base_revision("base", health)


def test_governance_base_authenticates_matching_committed_run():
    health = {"source_tree_sha256": "a" * 64}

    def resolve(revision: str) -> str:
        return "b" * 40 if revision == "base" else "c" * 40

    with (
        patch.object(_RESEAL_MODULE, "_resolve_commit", side_effect=resolve),
        patch.object(_RESEAL_MODULE, "_is_ancestor", return_value=True),
        patch.object(_RESEAL_MODULE, "_git_json", return_value=health),
        patch.object(_RESEAL_MODULE, "_verify_manifest_health_binding") as binding,
        patch.object(_RESEAL_MODULE, "_source_digest_at_revision", return_value="a" * 64),
    ):
        assert _RESEAL_MODULE._authenticated_base_revision("base", health) == "b" * 40
    binding.assert_called_once_with("b" * 40, health)


def test_base_source_digest_rehashes_committed_manifest_rows():
    blobs = {
        "control.txt": b"controlled\n",
        "program.py": b"print('sealed')\n",
    }
    controls = [
        {
            "path": "control.txt",
            "present": True,
            "sha256": hashlib.sha256(blobs["control.txt"]).hexdigest(),
        }
    ]
    programs = [
        {
            "path": "program.py",
            "present": True,
            "sha256": hashlib.sha256(blobs["program.py"]).hexdigest(),
        }
    ]
    rows = [(row["path"], row["sha256"]) for row in controls + programs]
    digest = _RESEAL_MODULE._source_rows_sha256(rows)
    manifest = {
        "artifacts": {"controls": controls, "programs": programs},
        "source_control": {"source_tree_sha256": digest},
    }
    manifest["manifest_sha256"] = _RESEAL_MODULE._manifest_sha256(manifest)

    with (
        patch.object(_RESEAL_MODULE, "_git_json", return_value=manifest),
        patch.object(
            _RESEAL_MODULE,
            "_git_blob",
            side_effect=lambda revision, path: blobs[path],
        ),
    ):
        assert _RESEAL_MODULE._source_digest_at_revision("base") == digest

    tampered = dict(blobs)
    tampered["program.py"] = b"print('changed')\n"
    with (
        patch.object(_RESEAL_MODULE, "_git_json", return_value=manifest),
        patch.object(
            _RESEAL_MODULE,
            "_git_blob",
            side_effect=lambda revision, path: tampered[path],
        ),
    ):
        with pytest.raises(ValueError, match="program.py"):
            _RESEAL_MODULE._source_digest_at_revision("base")


def test_governance_reseal_chain_accepts_valid_multi_hop_history():
    timestamp = "2026-08-23T17:47:35.766117+00:00"
    health = {
        "timestamp": timestamp,
        "source_tree_sha256": "c" * 64,
        "governance_reseal_chain": [
            {
                "status": "PASS",
                "base_revision": "1" * 40,
                "clinical_run_timestamp": timestamp,
                "prior_source_tree_sha256": "a" * 64,
                "rebound_source_tree_sha256": "b" * 64,
                "changed_paths": ["README.md"],
                "clinical_run_was_not_reexecuted": True,
            },
            {
                "status": "PASS",
                "base_revision": "2" * 40,
                "clinical_run_timestamp": timestamp,
                "prior_source_tree_sha256": "b" * 64,
                "rebound_source_tree_sha256": "c" * 64,
                "changed_paths": ["CHANGELOG.md"],
                "clinical_run_was_not_reexecuted": True,
            },
        ],
    }
    ok, accepted, detail = _valid_reseal_chain(health)
    assert ok, detail
    assert accepted == ["a" * 64, "b" * 64, "c" * 64]


def test_governance_reseal_chain_rejects_discontinuous_history():
    timestamp = "2026-08-23T17:47:35.766117+00:00"
    health = {
        "timestamp": timestamp,
        "source_tree_sha256": "c" * 64,
        "governance_reseal_chain": [
            {
                "status": "PASS",
                "base_revision": "1" * 40,
                "clinical_run_timestamp": timestamp,
                "prior_source_tree_sha256": "a" * 64,
                "rebound_source_tree_sha256": "b" * 64,
                "changed_paths": ["README.md"],
                "clinical_run_was_not_reexecuted": True,
            },
            {
                "status": "PASS",
                "base_revision": "2" * 40,
                "clinical_run_timestamp": timestamp,
                "prior_source_tree_sha256": "x" * 64,
                "rebound_source_tree_sha256": "c" * 64,
                "changed_paths": ["CHANGELOG.md"],
                "clinical_run_was_not_reexecuted": True,
            },
        ],
    }
    ok, _, _ = _valid_reseal_chain(health)
    assert not ok


def test_current_baseline_requires_completed_exact_byte_rerun():
    result = evaluate(ROOT)
    timestamp_check = next(
        row for row in result["checks"]
        if row["name"] == "p21.pipeline_binding.health_timestamp"
    )
    boundary_check = next(
        row for row in result["checks"]
        if row["name"] == "p21.summary.exact_byte_rerun_boundary"
    )
    stage_check = next(
        row for row in result["checks"]
        if row["name"] == "p21.pipeline_binding.health_stage_contract"
    )
    assert timestamp_check["ok"], timestamp_check
    assert "bound=2026-08-23T17:47:35.766117+00:00" in timestamp_check["detail"]
    assert stage_check["ok"], stage_check
    assert stage_check["detail"] == "manifest=41; expected=41; recorded=41; pass=41"
    assert boundary_check["ok"], boundary_check
    assert boundary_check["detail"] == (
        "exact current production bytes validated under standard submission filenames"
    )


def test_regulatory_stage_contract_is_derived_from_manifest():
    import yaml

    manifest = yaml.safe_load(
        (ROOT / "config/study_manifest.yaml").read_text(encoding="utf-8")
    )
    names = _manifest_stage_names(manifest)
    assert len(names) == 41
    assert len(set(names)) == 41
    assert names[0] == "Governance Scope Lock (G00)"
    assert names[-1] == "Release Run Manifest Binding"


def test_regulatory_stage_contract_fails_closed_on_malformed_sections():
    assert _manifest_stage_names({"infrastructure_stages": []}) == []
    assert _manifest_stage_names({"datasets": {"name": "not-a-list"}}) == []


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
    assert summary["schema_version"] == "1.1"
    assert summary["status"] == "EXECUTED_WITH_OPEN_FINDINGS_AND_COMPATIBILITY_CAVEAT"
    assert summary["use"] == "INFORMATIVE_ONLY"
    assert summary["validation"]["process_completed"] is True
    assert summary["validation"]["compatibility_caveat"] == "Incompatible CLI used"
    assert summary["validation"]["raw_report_sha256"] == (
        "05cf6f82c46ba958fdd659f9f60f41fa5e9fd2bf7f59eba443b83fd428d89cb5"
    )
    assert summary["validation"]["input_content_transformations"] == 0
    assert "standard submission filenames" in summary["validation"]["input_filename_contract"]
    assert totals == {
        "datasets_processed": 7,
        "datasets_rejected": 0,
        "records": 121320,
        "rule_catalog_entries": 388,
        "issue_groups": 30,
        "issue_occurrences": 2373,
    }
    assert totals["records"] == sum(row["records"] for row in summary["datasets"])
    assert {row["validator_filename"] for row in summary["datasets"]} == {
        "adae.xpt",
        "adcm.xpt",
        "adex.xpt",
        "adlb.xpt",
        "adrs.xpt",
        "adsl.xpt",
        "adtte.xpt",
    }
    assert {row["dataset"]: row["sha256"] for row in summary["datasets"]} == {
        "ADAE": "dd3bf9eeb204a7d54e63e2f4c0545e353ee943774be1620071bfe5ded9b33a67",
        "ADCM": "506f7eee97c9fd52df10c9b254b976f0759c32932a54cfb53a783c07b731bbdb",
        "ADEX": "6b6c974ba4fb85c543806fa47502f3f4b0c4d0a4bb88580cbc1f86f1a96889eb",
        "ADLB": "92f2404520923f89f9e680b66f76b078af77098500d6856f00ba9b754d698c02",
        "ADRS": "2a6d97e8add31ffc69b9adebab08a9d69cebb38957cf2488281da495b69a21e1",
        "ADSL": "9a2d00b02e00c0be0f1785df4797a1bc988371f400e9c6114cb0e3e7811ab2d9",
        "ADTTE": "665dd7eeca6854633124764f82f3e8a0f4b880169f92c02a7d19a1bbd0bb53ff",
    }
    assert totals["issue_groups"] == len(summary["issues"])
    assert totals["issue_occurrences"] == sum(row["found"] for row in summary["issues"])
    assert totals["issue_occurrences"] == sum(
        row["occurrences"] for row in summary["residual_families"]
    )
    assert summary["pipeline_binding"] == {
        "health_timestamp": "2026-08-23T17:47:35.766117+00:00",
        "pipeline_health_status": "GREEN",
        "sas_execution_mode": "oda",
        "run_scope": "full_dag",
        "stages_expected": 41,
        "stages_recorded": 41,
        "source_tree_sha256": "6b2e272130b0936f4f2156bf8f4352f4c3428a9c01eb772e29614c14ce970e91",
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
    assert summary["exact_byte_rerun"] == {
        "health_timestamp": "2026-08-23T17:47:35.766117+00:00",
        "completed": True,
        "datasets_validated": 7,
        "input_hashes_match_current_production_xpts": True,
        "standard_filenames_used": True,
        "content_transformations": 0,
        "process_completed": True,
        "report_sha256": (
            "05cf6f82c46ba958fdd659f9f60f41fa5e9fd2bf7f59eba443b83fd428d89cb5"
        ),
    }
