"""Fail-closed tests for the scoped official-source inventory."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform"))
from check_regulatory_source_inventory import evaluate_inventory  # noqa: E402


INVENTORY = ROOT / "config/regulatory_source_inventory.yaml"


def _inventory_data() -> dict:
    return yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))


def _write_inventory(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "config" / "regulatory_source_inventory.yaml"
    path.parent.mkdir()
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def test_checked_in_inventory_is_structurally_valid_and_scoped() -> None:
    result = evaluate_inventory(INVENTORY)
    assert result["assessment"] == "PASS"
    assert result["problems"] == []
    assert result["source_count"] >= 40
    assert set(result["counts"]) == {
        "APPLICABLE",
        "PARTIALLY_APPLICABLE",
        "OUT_OF_SCOPE",
        "WATCH_NOT_FINAL",
        "NEEDS_OWNER_CONFIRMATION",
    }
    assert result["scope"]["intended_use"] == "interview and technical-review demonstration"


def test_inventory_cli_passes_and_reports_all_status_buckets() -> None:
    command = [
        sys.executable,
        str(ROOT / "platform/check_regulatory_source_inventory.py"),
        "--json",
    ]
    result = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["assessment"] == "PASS"
    assert payload["counts"]["WATCH_NOT_FINAL"] >= 1


def test_unknown_status_and_path_escape_fail_closed(tmp_path: Path) -> None:
    data = _inventory_data()
    data["sources"] = [copy.deepcopy(data["sources"][0])]
    data["sources"][0]["status"] = "GREEN_BADGE"
    data["sources"][0]["repo_evidence"] = ["../outside.txt"]
    result = evaluate_inventory(_write_inventory(tmp_path, data))
    assert result["assessment"] == "MALFORMED"
    assert any("unknown status" in item for item in result["problems"])
    assert any("must stay inside" in item for item in result["problems"])


def test_duplicate_source_id_and_incomplete_bucket_fail_closed(tmp_path: Path) -> None:
    data = _inventory_data()
    data["sources"] = [copy.deepcopy(data["sources"][0]), copy.deepcopy(data["sources"][0])]
    result = evaluate_inventory(_write_inventory(tmp_path, data))
    assert result["assessment"] == "MALFORMED"
    assert any("duplicate source id" in item for item in result["problems"])
    assert any("every status bucket" in item for item in result["problems"])


def test_applicable_source_without_local_evidence_fails_closed(tmp_path: Path) -> None:
    data = _inventory_data()
    data["sources"] = [copy.deepcopy(data["sources"][0])]
    data["sources"][0]["repo_evidence"] = []
    result = evaluate_inventory(_write_inventory(tmp_path, data))
    assert result["assessment"] == "MALFORMED"
    assert any("applicable sources must name local evidence" in item for item in result["problems"])
