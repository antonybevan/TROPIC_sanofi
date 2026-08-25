"""Fail-closed contracts for regenerated metadata-control prerequisites."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "platform/build_metadata_control_report.py"
SPEC = importlib.util.spec_from_file_location("tropic_metadata_control", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_missing_required_metadata_inputs_are_critical() -> None:
    findings = MODULE._required_input_findings([], [])
    assert {item["finding"] for item in findings} == {
        "adam_variable_traceability_missing_or_empty",
        "metadata_data_drift_missing_or_empty",
    }
    assert {item["severity"] for item in findings} == {"critical"}


def test_malformed_required_metadata_inputs_are_critical() -> None:
    findings = MODULE._required_input_findings([{"dataset": "ADSL"}], [{"dataset": "ADSL"}])
    assert {item["finding"] for item in findings} == {
        "adam_variable_traceability_schema_invalid",
        "metadata_data_drift_schema_invalid",
    }
    assert {item["severity"] for item in findings} == {"critical"}
