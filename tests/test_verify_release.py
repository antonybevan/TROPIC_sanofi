"""Unit tests for the data-free release-seal verifier."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_release", ROOT / "scripts" / "verify_release.py"
)
verify_release = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(verify_release)

sys.path.insert(0, str(ROOT / "platform"))
import build_release_run_manifest


class TestReleaseSealHelpers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.original_root = verify_release.ROOT
        verify_release.ROOT = Path(self.tmp.name)
        source = verify_release.ROOT / "platform" / "example.py"
        source.parent.mkdir(parents=True)
        source.write_text("print('sealed')\n", encoding="utf-8")
        self.source = source

    def tearDown(self):
        verify_release.ROOT = self.original_root
        self.tmp.cleanup()

    def test_manifest_hash_detects_payload_change(self):
        manifest = {"status": "PASS", "manifest_sha256": ""}
        manifest["manifest_sha256"] = verify_release.manifest_sha256(manifest)
        self.assertEqual(manifest["manifest_sha256"], verify_release.manifest_sha256(manifest))
        manifest["status"] = "FAIL"
        self.assertNotEqual(manifest["manifest_sha256"], verify_release.manifest_sha256(manifest))

    def test_simulation_scientific_hash_excludes_only_its_self_seal(self):
        result = {"schema_version": "1.0.0", "scenarios": [{"id": "S1"}]}
        result["scientific_output_sha256"] = verify_release.simulation_scientific_sha256(result)
        self.assertEqual(
            result["scientific_output_sha256"],
            verify_release.simulation_scientific_sha256(result),
        )
        result["scenarios"][0]["id"] = "CHANGED"
        self.assertNotEqual(
            result["scientific_output_sha256"],
            verify_release.simulation_scientific_sha256(result),
        )

    def test_source_hashes_detect_changed_source(self):
        manifest = {
            "artifacts": {
                "controls": [],
                "programs": [{
                    "path": "platform/example.py",
                    "sha256": verify_release.sha256(self.source),
                }],
            }
        }
        self.assertEqual([], verify_release.sealed_source_problems(manifest))
        self.source.write_text("print('changed')\n", encoding="utf-8")
        self.assertEqual(["platform/example.py"], verify_release.sealed_source_problems(manifest))

    def test_source_tree_digest_detects_changed_source(self):
        manifest = {
            "artifacts": {
                "controls": [],
                "programs": [{
                    "path": "platform/example.py",
                    "sha256": verify_release.sha256(self.source),
                }],
            }
        }
        d_before = verify_release.source_tree_sha256(manifest)
        self.source.write_text("print('changed')\n", encoding="utf-8")
        d_after = verify_release.source_tree_sha256(manifest)
        self.assertNotEqual(d_before, d_after)
        # recomputation is deterministic for an unchanged checkout
        self.assertEqual(d_after, verify_release.source_tree_sha256(manifest))

    def test_artifact_hash_recheck_detects_present_drift(self):
        artifact = verify_release.ROOT / "05_outputs" / "table.csv"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("a,b\n1,2\n", encoding="utf-8")
        manifest = {
            "artifacts": {
                "qc_files": [{
                    "path": "05_outputs/table.csv",
                    "present": True,
                    "sha256": verify_release.sha256(artifact),
                }],
                "tfl_outputs": [],
                "package_files": [],
                "additive_outputs": [],
                "inputs": [],
                "logs": [],
                "review_surface": [],
            },
            "datasets": [],
        }
        problems, verified, skipped = verify_release.sealed_artifact_problems(manifest)
        self.assertEqual([], problems)
        self.assertEqual((1, 0), (verified, skipped))
        artifact.write_text("a,b\n9,9\n", encoding="utf-8")
        problems, _, _ = verify_release.sealed_artifact_problems(manifest)
        self.assertIn("qc_files:05_outputs/table.csv: sha256 mismatch", problems)

    def test_artifact_hash_recheck_allows_missing_untracked_data_row(self):
        manifest = {
            "artifacts": {
                "qc_files": [{
                    "path": "04_analysis_datasets/adam/adsl_prod.xpt",
                    "present": True,
                    "sha256": "a" * 64,
                }],
                "tfl_outputs": [],
                "package_files": [],
                "additive_outputs": [],
                "inputs": [],
                "logs": [],
                "review_surface": [],
            },
            "datasets": [],
        }
        problems, verified, skipped = verify_release.sealed_artifact_problems(manifest)
        self.assertEqual([], problems)
        self.assertEqual((0, 1), (verified, skipped))

    def test_artifact_hash_recheck_rejects_missing_tracked_row(self):
        manifest = {
            "artifacts": {
                "qc_files": [{
                    "path": "tracked.csv",
                    "present": True,
                    "sha256": "b" * 64,
                }],
                "tfl_outputs": [],
                "package_files": [],
                "additive_outputs": [],
                "inputs": [],
                "logs": [],
                "review_surface": [],
            },
            "datasets": [],
        }
        with patch.object(verify_release, "_git_tracked", return_value=True):
            problems, _, _ = verify_release.sealed_artifact_problems(manifest)
        self.assertIn("qc_files:tracked.csv: tracked artifact missing", problems)

    def test_material_worktree_clean_ignores_release_seal_outputs(self):
        with patch.object(verify_release.subprocess, "check_output", return_value=""):
            self.assertTrue(verify_release.git_material_worktree_clean())
        seal_only = " M platform/release_run_manifest/release_run_manifest.json\n"
        with patch.object(verify_release.subprocess, "check_output", return_value=seal_only):
            self.assertTrue(verify_release.git_material_worktree_clean())
        with patch.object(verify_release.subprocess, "check_output", return_value=" M source.py\n"):
            self.assertFalse(verify_release.git_material_worktree_clean())

    def test_secret_scanner_policy_is_bound_as_pipeline_control(self):
        self.assertIn(".gitleaks.toml", build_release_run_manifest.PIPELINE_CONTROL_FILES)


if __name__ == "__main__":
    unittest.main()
