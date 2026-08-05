"""Regression tests for truthful failed-run scope telemetry (F-043)."""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "tropic_cibuild_abort_scope", ROOT / "platform" / "cibuild.py"
)
cibuild = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(cibuild)


class _FakeFuture:
    def __init__(self, stage):
        self.stage = stage

    def result(self):
        return self.stage, 1, "", "synthetic failure"


class _FakeExecutor:
    def __init__(self):
        self.futures = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def submit(self, _worker, stage):
        future = _FakeFuture(stage)
        self.futures.append(future)
        return future


class TestPipelineAbortScope(unittest.TestCase):
    def test_write_telemetry_marks_truncated_run_partial(self):
        expected = ["Stage 1", "Stage 2", "Stage 3"]
        with tempfile.TemporaryDirectory() as tmp:
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                with (
                    patch.object(cibuild, "_source_tree_sha256_for_telemetry", return_value="sha"),
                    patch.object(cibuild, "_r_version", return_value="R"),
                    patch.object(cibuild, "_renv_lock_sha", return_value="lock"),
                ):
                    cibuild.write_telemetry(
                        {"Stage 1": "FAIL"},
                        "sim",
                        expected_stage_names=expected,
                    )
                health = json.loads(
                    Path("platform/pipeline_health.json").read_text(encoding="utf-8")
                )
            finally:
                os.chdir(old_cwd)

        self.assertEqual("RED", health["pipeline_health_status"])
        self.assertEqual("partial_dag", health["run_scope"])
        self.assertEqual(3, health["stages_expected"])
        self.assertEqual(1, health["stages_recorded"])
        self.assertEqual(["Stage 2", "Stage 3"], health["stages_not_run"])

    def test_serial_abort_forwards_complete_stage_map(self):
        stage = {"id": 2, "name": "Stage 2", "cmd": "synthetic"}
        results = {}
        expected = ["Stage 1", "Stage 2", "Stage 3"]
        with (
            patch.object(cibuild, "_cache_dry_run_check"),
            patch.object(cibuild, "run_stage_execution", return_value=(1, "", "synthetic failure")),
            patch.object(cibuild, "_abort_pipeline", side_effect=SystemExit(1)) as abort,
        ):
            with self.assertRaises(SystemExit):
                cibuild.run_single_stage(
                    stage,
                    from_stage=0,
                    sas_mode="sim",
                    results=results,
                    expected_stage_names=expected,
                )

        abort.assert_called_once_with(results, "sim", expected)

    def test_parallel_abort_forwards_complete_stage_map(self):
        stage = {"id": 2, "name": "Stage 2", "cmd": "synthetic", "parallel": True}
        results = {}
        expected = ["Stage 1", "Stage 2", "Stage 3"]

        def fake_as_completed(futures):
            return list(futures)

        with (
            patch.object(cibuild, "_cache_dry_run_check"),
            patch("concurrent.futures.ProcessPoolExecutor", _FakeExecutor),
            patch("concurrent.futures.as_completed", fake_as_completed),
            patch.object(cibuild, "_abort_pipeline", side_effect=SystemExit(1)) as abort,
        ):
            with self.assertRaises(SystemExit):
                cibuild.run_parallel_batch(
                    [stage],
                    from_stage=0,
                    sas_mode="sim",
                    results=results,
                    expected_stage_names=expected,
                )

        abort.assert_called_once_with(results, "sim", expected)
        self.assertEqual({"Stage 2": "FAIL"}, results)


if __name__ == "__main__":
    unittest.main()
