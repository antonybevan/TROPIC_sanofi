"""Data-free regression checks for manifest-to-executor DAG wiring."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("cibuild", ROOT / "platform" / "cibuild.py")
cibuild = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(cibuild)


def test_manifest_dag_wiring_is_complete_and_gated():
    stages, problems = cibuild.validate_pipeline_dag(
        cibuild._MANIFEST,
        cibuild._ENGINE_ROOT,
        cibuild._RELOCATE_ENGINE,
    )
    assert not problems, problems
    assert len(stages) == 34
    assert stages[0]["name"] == "Governance Scope Lock (G00)"
    assert stages[-1]["name"] == "Release Run Manifest Binding"


def test_demo_mode_performs_dag_validation_before_smoke_tests():
    source = (ROOT / "platform" / "cibuild.py").read_text(encoding="utf-8")
    assert "--validate-dag" in source
    assert "Manifest DAG validated" in source
