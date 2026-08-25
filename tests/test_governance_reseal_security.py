from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "rebind_governance_seal_security",
    ROOT / "scripts/rebind_governance_seal.py",
)
assert SPEC and SPEC.loader
RESEAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RESEAL)


def test_rebound_digest_uses_only_immutable_head_blobs():
    base_rows = [
        ("control.txt", hashlib.sha256(b"old control").hexdigest()),
        ("program.py", hashlib.sha256(b"same program").hexdigest()),
    ]
    head_blobs = {
        "control.txt": b"reviewed control update",
        "program.py": b"same program",
    }
    expected_rows = [
        (path, hashlib.sha256(payload).hexdigest())
        for path, payload in head_blobs.items()
    ]

    def committed_blob(revision: str, path: str) -> bytes:
        assert revision == "head-commit"
        return head_blobs[path]

    with (
        patch.object(RESEAL, "_sealed_source_registry", return_value=({}, base_rows)),
        patch.object(RESEAL, "_git_blob", side_effect=committed_blob) as blob,
    ):
        actual = RESEAL._source_digest_for_committed_head(
            "authenticated-base", "head-commit"
        )

    assert actual == RESEAL._source_rows_sha256(expected_rows)
    assert blob.call_count == len(base_rows)


def test_dashboard_reseal_surface_matches_direct_jpg_contract():
    assert RESEAL._is_allowed(
        "06_qc_evidence/audit/dashboard_evidence/reviewer-home.jpg"
    )
    assert not RESEAL._is_allowed(
        "06_qc_evidence/audit/dashboard_evidence/nested/reviewer-home.jpg"
    )
    assert not RESEAL._is_allowed(
        "06_qc_evidence/audit/dashboard_evidence/reviewer-home.png"
    )
    assert not RESEAL._is_allowed(
        "06_qc_evidence/audit/dashboard_evidence/reviewer-home.jpeg"
    )


def test_committed_head_is_rechecked_before_health_write():
    source = (ROOT / "scripts/rebind_governance_seal.py").read_text(encoding="utf-8")
    assert "_source_digest_for_committed_head(base_revision, head_revision)" in source
    assert "_current_source_tree_sha256" not in source
    assert 'if _resolve_commit("HEAD") != head_revision' in source


def test_explicit_empty_chain_cannot_hide_a_legacy_reseal():
    health = {
        "source_tree_sha256": "a" * 64,
        "governance_reseal_chain": [],
        "governance_only_reseal": {"status": "PASS"},
    }
    problems = RESEAL._governance_chain_policy_problems(health)
    assert problems == ["legacy governance reseal is omitted from the explicit chain"]
