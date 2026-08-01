"""Unit tests for the data-free release-seal verifier."""

from __future__ import annotations

import importlib.util
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

    def test_material_worktree_clean_ignores_release_seal_outputs(self):
        with patch.object(verify_release.subprocess, "check_output", return_value=""):
            self.assertTrue(verify_release.git_material_worktree_clean())
        seal_only = " M platform/release_run_manifest/release_run_manifest.json\n"
        with patch.object(verify_release.subprocess, "check_output", return_value=seal_only):
            self.assertTrue(verify_release.git_material_worktree_clean())
        with patch.object(verify_release.subprocess, "check_output", return_value=" M source.py\n"):
            self.assertFalse(verify_release.git_material_worktree_clean())


if __name__ == "__main__":
    unittest.main()
