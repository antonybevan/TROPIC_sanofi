"""Fail-closed tests for the FDA/ICH readiness evidence map."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform"))
from check_submission_readiness import evaluate_profile  # noqa: E402


PROFILE = ROOT / "config/fda_readiness_profile.yaml"


def _profile_data() -> dict:
    return yaml.safe_load(PROFILE.read_text(encoding="utf-8"))


def _write_profile(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "config" / "fda_readiness_profile.yaml"
    path.parent.mkdir()
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def test_checked_in_profile_is_structurally_valid_and_explicitly_bounded() -> None:
    result = evaluate_profile(PROFILE)
    assert result["assessment"] == "BLOCKED"
    assert result["problems"] == []
    assert result["scope"]["release_claim"] == "NOT_FOR_REGULATORY_SUBMISSION"
    assert {"SUB-002", "STAT-004", "SYSTEM-001", "QC-001"}.issubset(result["blockers"])
    assert result["counts"]["PASS"] >= 1
    assert result["counts"]["PARTIAL"] >= 1


def test_default_cli_reports_but_does_not_hide_known_blockers() -> None:
    command = [sys.executable, str(ROOT / "platform/check_submission_readiness.py"), "--json"]
    result = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["assessment"] == "BLOCKED"
    assert "SUB-002" in payload["blockers"]


def test_strict_cli_is_red_until_owner_actions_are_complete() -> None:
    command = [sys.executable, str(ROOT / "platform/check_submission_readiness.py"), "--strict"]
    result = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    assert result.returncode == 1
    assert "BLOCKED" in result.stdout


def test_pass_control_with_missing_required_evidence_fails_closed(tmp_path: Path) -> None:
    data = _profile_data()
    control = copy.deepcopy(data["controls"][0])
    control["evidence"] = [{"path": "does/not/exist.txt", "required": True}]
    data["controls"] = [control]
    result = evaluate_profile(_write_profile(tmp_path, data))
    assert result["assessment"] == "MALFORMED"
    assert any("missing required evidence" in item for item in result["problems"])


def test_unsafe_release_claim_fails_closed(tmp_path: Path) -> None:
    data = _profile_data()
    data["scope"]["release_claim"] = "FDA_READY"
    result = evaluate_profile(_write_profile(tmp_path, data))
    assert result["assessment"] == "MALFORMED"
    assert any("unsafe release claim" in item for item in result["problems"])


def test_unknown_status_and_path_escape_fail_closed(tmp_path: Path) -> None:
    data = _profile_data()
    data["controls"] = [copy.deepcopy(data["controls"][0])]
    data["controls"][0]["status"] = "GREEN_BADGE"
    data["controls"][0]["evidence"] = [{"path": "../outside.txt", "required": True}]
    result = evaluate_profile(_write_profile(tmp_path, data))
    assert result["assessment"] == "MALFORMED"
    assert any("unknown status" in item for item in result["problems"])
    assert any("must stay inside" in item for item in result["problems"])


def test_absolute_evidence_path_is_rejected_without_allowing_escape(tmp_path: Path) -> None:
    data = _profile_data()
    data["controls"] = [copy.deepcopy(data["controls"][0])]
    data["controls"][0]["evidence"] = [{"path": str(ROOT / "README.md"), "required": True}]
    result = evaluate_profile(_write_profile(tmp_path, data))
    assert result["assessment"] == "MALFORMED"
    assert any("must stay inside" in item for item in result["problems"])
