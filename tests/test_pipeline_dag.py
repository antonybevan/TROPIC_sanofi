"""Data-free regression checks for manifest-to-executor DAG wiring."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import mock_open, patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("cibuild", ROOT / "platform" / "cibuild.py")
cibuild = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(cibuild)

GATE_MAP_SPEC = importlib.util.spec_from_file_location(
    "build_orchestrator_gate_map",
    ROOT / "platform" / "build_orchestrator_gate_map.py",
)
gate_map = importlib.util.module_from_spec(GATE_MAP_SPEC)
assert GATE_MAP_SPEC and GATE_MAP_SPEC.loader
GATE_MAP_SPEC.loader.exec_module(gate_map)


def test_manifest_dag_wiring_is_complete_and_gated():
    stages, problems = cibuild.validate_pipeline_dag(
        cibuild._MANIFEST,
        cibuild._ENGINE_ROOT,
        cibuild._RELOCATE_ENGINE,
    )
    assert not problems, problems
    assert len(stages) == 41
    assert stages[0]["name"] == "Governance Scope Lock (G00)"
    assert [s["name"] for s in stages[-13:-9]] == [
        "Simulation Operating Characteristics",
        "Simulation MAP and Report",
        "Simulation Evidence Independent Verification",
        "Reviewer Package Lock (G07)",
    ]
    assert stages[-1]["name"] == "Release Run Manifest Binding"
    assert [s["name"] for s in stages[-3:]] == [
        "Metadata Control Evidence Refresh",
        "Log Cleanliness Gate",
        "Release Run Manifest Binding",
    ]


def test_demo_mode_performs_dag_validation_before_smoke_tests():
    source = (ROOT / "platform" / "cibuild.py").read_text(encoding="utf-8")
    assert "--validate-dag" in source
    assert "Manifest DAG validated" in source


def test_every_manifest_stage_maps_to_delivery_gates(tmp_path):
    status = gate_map.build_gate_map(
        str(ROOT / "config" / "study_manifest.yaml"),
        str(ROOT / "config" / "delivery_workstreams.yaml"),
        str(tmp_path / "gate-map"),
        str(tmp_path / "ORCHESTRATOR_GATE_MAP.md"),
    )
    assert status["status"] == "pass"
    assert status["stages"] == 41
    assert status["mapped_stages"] == 41
    assert status["unmapped_stages"] == []
    assert gate_map._mapping_for("Metadata Control Evidence Refresh") == (
        ["G03", "G06"],
        "fail-closed variable traceability and metadata-drift evidence refresh",
    )


def test_release_binding_refreshes_tfl_index_before_manifest():
    stage = {
        "name": "Release Run Manifest Binding",
        "cmd": ["python", "platform/build_release_run_manifest.py"],
    }
    with (
        patch.object(
            cibuild,
            "run_command",
            side_effect=[(0, "index refreshed", ""), (0, "manifest built", "")],
        ) as run,
        patch("builtins.open", mock_open(read_data='{"status": "pass"}')),
    ):
        assert cibuild.run_stage_execution(stage, "oda") == (0, "manifest built", "")

    assert run.call_args_list[0].args[0] == [
        cibuild.sys.executable,
        "platform/build_tfl_output_index.py",
    ]
    assert run.call_args_list[1].args[0] == stage["cmd"]


def test_release_binding_fails_closed_on_tfl_index_status():
    stage = {
        "name": "Release Run Manifest Binding",
        "cmd": ["python", "platform/build_release_run_manifest.py"],
    }
    with (
        patch.object(
            cibuild,
            "run_command",
            return_value=(0, "index refreshed", ""),
        ) as run,
        patch("builtins.open", mock_open(read_data='{"status": "fail"}')),
    ):
        rc, stdout, stderr = cibuild.run_stage_execution(stage, "oda")

    assert rc == 1
    assert stdout == "index refreshed"
    assert "did not pass" in stderr
    assert run.call_count == 1
