"""Unit tests for the data-free release-seal verifier."""

from __future__ import annotations

import io
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
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
from governance_reseal_policy import is_resealable_path


def _reseal_health(*, changed_paths: list[str]) -> dict:
    timestamp = "2026-08-23T17:47:35.766117+00:00"
    return {
        "timestamp": timestamp,
        "pipeline_health_status": "GREEN",
        "sas_execution_mode": "oda",
        "run_scope": "full_dag",
        "provenance_guard": {"passed": True},
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
                "pipeline_controls": [],
                "review_surface": [],
            }
        }
        with patch.multiple(
            verify_release,
            FIXED_CONTROL_FILES=(),
            FIXED_REVIEW_SURFACE_FILES=(),
            REVIEW_SURFACE_GLOBS=(),
            PIPELINE_CONTROL_FILES=(),
            _tracked_governing_inventory=lambda: (set(), set()),
        ):
            self.assertEqual([], verify_release.sealed_source_problems(manifest))
        self.source.write_text("print('changed')\n", encoding="utf-8")
        with patch.multiple(
            verify_release,
            FIXED_CONTROL_FILES=(),
            FIXED_REVIEW_SURFACE_FILES=(),
            REVIEW_SURFACE_GLOBS=(),
            PIPELINE_CONTROL_FILES=(),
            _tracked_governing_inventory=lambda: (set(), set()),
        ):
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

    def test_source_tree_digest_binds_pipeline_only_control(self):
        pipeline = verify_release.ROOT / ".python-version"
        pipeline.write_text("3.12.13\n", encoding="utf-8")
        manifest = {
            "artifacts": {
                "controls": [],
                "programs": [],
                "pipeline_controls": [{
                    "path": ".python-version",
                    "sha256": verify_release.sha256(pipeline),
                }],
            }
        }
        before = verify_release.source_tree_sha256(manifest)
        self.assertEqual(
            before,
            build_release_run_manifest._source_tree_sha256(
                [], [], manifest["artifacts"]["pipeline_controls"]
            ),
        )
        pipeline.write_text("3.12.14\n", encoding="utf-8")
        self.assertNotEqual(before, verify_release.source_tree_sha256(manifest))

    def test_source_tree_digest_deduplicates_overlapping_inventory_rows(self):
        row = {"path": "shared.py", "sha256": "d" * 64}
        self.assertEqual(
            build_release_run_manifest._source_tree_sha256([row]),
            build_release_run_manifest._source_tree_sha256(
                [row], [dict(row)], [dict(row)]
            ),
        )

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
        self.assertIn("qc_files:tracked.csv: required artifact missing", problems)

    def test_missing_review_surface_is_required_even_after_tracked_deletion(self):
        manifest = {
            "artifacts": {
                "qc_files": [],
                "tfl_outputs": [],
                "package_files": [],
                "additive_outputs": [],
                "inputs": [],
                "logs": [],
                "review_surface": [{
                    "path": "CHANGELOG.md",
                    "present": True,
                    "sha256": "c" * 64,
                }],
            },
            "datasets": [],
        }
        with patch.object(verify_release, "_git_tracked", return_value=False):
            problems, verified, skipped = verify_release.sealed_artifact_problems(
                manifest
            )
        self.assertIn(
            "review_surface:CHANGELOG.md: required artifact missing", problems
        )
        self.assertEqual((0, 0), (verified, skipped))

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

    def test_dependency_update_policy_is_bound_as_pipeline_control(self):
        self.assertIn(
            ".github/dependabot.yml",
            build_release_run_manifest.PIPELINE_CONTROL_FILES,
        )
        self.assertIn(".github/dependabot.yml", verify_release.PIPELINE_CONTROL_FILES)

    def test_ci_build_dependency_lock_is_bound_as_pipeline_control(self):
        self.assertIn(
            "requirements-ci-build.lock",
            build_release_run_manifest.PIPELINE_CONTROL_FILES,
        )
        self.assertIn("requirements-ci-build.lock", verify_release.PIPELINE_CONTROL_FILES)

    def test_core_dependency_locks_are_bound_as_pipeline_controls(self):
        expected = {
            "requirements-core-build.lock",
            "requirements-core.txt",
            "requirements-core.lock",
        }
        self.assertTrue(
            expected.issubset(build_release_run_manifest.PIPELINE_CONTROL_FILES)
        )
        self.assertTrue(expected.issubset(verify_release.PIPELINE_CONTROL_FILES))

    def test_runtime_and_repository_surface_policies_are_sealed(self):
        pipeline = {".gitignore", ".python-version"}
        fixed = {
            "CONTRIBUTING.md",
            "SECURITY.md",
            "docs/runbooks/ENVIRONMENT_BOOTSTRAP.md",
            "docs/runbooks/RELEASE_PROMOTION.md",
            "docs/workstreams/decisions/PYTHON_RUNTIME_MIGRATION_2026-08-24.md",
        }
        self.assertTrue(
            pipeline.issubset(build_release_run_manifest.PIPELINE_CONTROL_FILES)
        )
        self.assertTrue(pipeline.issubset(verify_release.PIPELINE_CONTROL_FILES))
        self.assertTrue(fixed.issubset(build_release_run_manifest.CONTROL_FILES))
        self.assertTrue(fixed.issubset(verify_release.FIXED_CONTROL_FILES))

    def test_adam_rules_lock_is_a_fresh_run_control(self):
        path = "platform/conformance_rules/adam/RULES.lock"
        self.assertIn(path, build_release_run_manifest.CONTROL_FILES)
        self.assertIn(path, verify_release.FIXED_CONTROL_FILES)
        self.assertIn(path, build_release_run_manifest.PIPELINE_CONTROL_FILES)
        self.assertIn(path, verify_release.PIPELINE_CONTROL_FILES)
        self.assertFalse(is_resealable_path(path))

    def test_core_cache_authority_is_bound_as_a_fresh_run_control(self):
        fixed = "platform/conformance/core_cache_manifest.json"
        records = {
            "platform/conformance/CORE_RUN_RECORD.md",
            "platform/conformance/CORE_SDTM34_RUN_RECORD.md",
        }
        pipeline = {
            fixed,
            "platform/run_core_conformance.sh",
            "platform/run_core_update_cache.py",
            "platform/verify_core_cache.py",
            "platform/verify_core_source.py",
        }
        self.assertIn(fixed, build_release_run_manifest.CONTROL_FILES)
        self.assertIn(fixed, verify_release.FIXED_CONTROL_FILES)
        self.assertTrue(records.issubset(build_release_run_manifest.CONTROL_FILES))
        self.assertTrue(records.issubset(verify_release.FIXED_CONTROL_FILES))
        self.assertTrue(
            pipeline.issubset(build_release_run_manifest.PIPELINE_CONTROL_FILES)
        )
        self.assertTrue(pipeline.issubset(verify_release.PIPELINE_CONTROL_FILES))
        for path in pipeline:
            self.assertFalse(is_resealable_path(path))

    def test_governance_policy_is_bound_as_pipeline_control(self):
        self.assertIn(
            "platform/governance_reseal_policy.py",
            build_release_run_manifest.PIPELINE_CONTROL_FILES,
        )
        self.assertIn(
            "platform/governance_reseal_policy.py",
            verify_release.PIPELINE_CONTROL_FILES,
        )

    def test_review_surface_hashing_matches_direct_jpg_reseal_boundary(self):
        dashboard = (
            Path(self.tmp.name)
            / "06_qc_evidence"
            / "audit"
            / "dashboard_evidence"
        )
        nested = dashboard / "nested"
        nested.mkdir(parents=True)
        candidates = (
            dashboard / "one.jpg",
            dashboard / "two.JPG",
            dashboard / "three.JpG",
            dashboard / "four.jpeg",
            dashboard / "five.png",
            nested / "six.jpg",
        )
        for path in candidates:
            path.write_bytes(b"synthetic review evidence")

        with patch.object(build_release_run_manifest, "ROOT", Path(self.tmp.name)):
            rows = build_release_run_manifest._hash_globs(
                build_release_run_manifest.REVIEW_SURFACE_GLOBS
            )

        hashed = {row["path"] for row in rows}
        policy_allowed = {
            path.relative_to(self.tmp.name).as_posix()
            for path in candidates
            if is_resealable_path(path.relative_to(self.tmp.name).as_posix())
        }
        self.assertEqual(policy_allowed, hashed)

    def test_manifest_gate_rejects_invalid_reseal_path_and_timestamp(self):
        def binding_problems(health: dict) -> list[str]:
            good_statuses = {
                build_release_run_manifest.QC_FILES["reconciliation"]: {
                    "overall": "PASS",
                    "simulated": False,
                    "endpoint_controls": {"F042_PAIN_RESPONSE": "PASS"},
                },
                build_release_run_manifest.QC_FILES["results_reconciliation"]: {
                    "overall": "PASS"
                },
                build_release_run_manifest.QC_FILES["forest_reconciliation"]: {
                    "overall": "PASS"
                },
                build_release_run_manifest.QC_FILES["figure_data_reconciliation"]: {
                    "overall": "PASS"
                },
                build_release_run_manifest.QC_FILES["spec_define"]: {"status": "PASS"},
                build_release_run_manifest.QC_FILES["spec_data"]: {"status": "PASS"},
                build_release_run_manifest.QC_FILES["metadata_control"]: {
                    "status": "PASS"
                },
                build_release_run_manifest.QC_FILES["log_cleanliness"]: {
                    "status": "PASS"
                },
                build_release_run_manifest.QC_FILES["regulatory_baseline"]: {
                    "status": "PASS"
                },
                build_release_run_manifest.QC_FILES[
                    "simulation_operating_characteristics"
                ]: {
                    "statuses": {
                        "execution": {"status": "PASS"},
                        "monte_carlo_precision": {"status": "PASS"},
                        "design_operating_characteristics": {"status": "PASS"},
                        "evidence_qualification": {"status": "NOT_QUALIFIED"},
                    }
                },
            }

            def load(rel: str) -> dict:
                if rel == build_release_run_manifest.QC_FILES["pipeline_health"]:
                    return health
                return good_statuses.get(rel, {})

            payload = {
                "source_control": {
                    "source_tree_sha256": health["source_tree_sha256"]
                },
                "artifacts": {
                    "pipeline_controls": [
                        {"path": path, "present": True}
                        for path in build_release_run_manifest.PIPELINE_CONTROL_FILES
                    ]
                },
                "datasets": [],
            }
            with patch.object(
                build_release_run_manifest, "_load_json", side_effect=load
            ):
                return build_release_run_manifest._binding_problems(payload)

        legitimate = binding_problems(_reseal_health(changed_paths=["README.md"]))
        self.assertFalse(
            any(problem.startswith("governance reseal policy:") for problem in legitimate)
        )

        forbidden = binding_problems(
            _reseal_health(changed_paths=["README.md", "platform/cibuild.py"])
        )
        self.assertTrue(any("platform/cibuild.py" in problem for problem in forbidden))

        wrong_timestamp = _reseal_health(changed_paths=["README.md"])
        wrong_timestamp["governance_reseal_chain"][0]["clinical_run_timestamp"] = (
            "2026-08-23T17:47:36+00:00"
        )
        timestamp_problems = binding_problems(wrong_timestamp)
        self.assertTrue(
            any("carried clinical timestamp" in problem for problem in timestamp_problems)
        )

    def test_independent_verifier_gate_rejects_invalid_reseal_chain(self):
        def verifier_output(health: dict) -> str:
            def load(rel: str) -> dict:
                return health if rel == "platform/pipeline_health.json" else {}

            output = io.StringIO()
            with patch.object(verify_release, "load", side_effect=load):
                with redirect_stdout(output):
                    self.assertEqual(1, verify_release.main())
            return output.getvalue()

        legitimate = verifier_output(_reseal_health(changed_paths=["README.md"]))
        self.assertIn("OK:   health.governance_reseal_policy", legitimate)

        forbidden = verifier_output(
            _reseal_health(changed_paths=["README.md", "platform/cibuild.py"])
        )
        self.assertIn("FAIL: health.governance_reseal_policy", forbidden)
        self.assertIn("platform/cibuild.py", forbidden)

        wrong_timestamp = _reseal_health(changed_paths=["README.md"])
        wrong_timestamp["governance_reseal_chain"][0]["clinical_run_timestamp"] = (
            "2026-08-23T17:47:36+00:00"
        )
        timestamp_output = verifier_output(wrong_timestamp)
        self.assertIn("FAIL: health.governance_reseal_policy", timestamp_output)
        self.assertIn("carried clinical timestamp", timestamp_output)

    def test_verifier_and_builder_fixed_control_registries_match(self):
        self.assertEqual(
            set(verify_release.FIXED_CONTROL_FILES),
            set(build_release_run_manifest.CONTROL_FILES),
        )
        self.assertEqual(
            set(verify_release.PIPELINE_CONTROL_FILES),
            set(build_release_run_manifest.PIPELINE_CONTROL_FILES),
        )
        self.assertEqual(
            set(verify_release.FIXED_REVIEW_SURFACE_FILES),
            set(build_release_run_manifest.REVIEW_SURFACE_FILES),
        )
        self.assertEqual(
            set(verify_release.REVIEW_SURFACE_GLOBS),
            set(build_release_run_manifest.REVIEW_SURFACE_GLOBS),
        )

    def test_missing_fixed_control_is_a_seal_failure(self):
        manifest = {
            "artifacts": {
                "controls": [{
                    "path": "platform/example.py",
                    "sha256": verify_release.sha256(self.source),
                }],
                "programs": [],
                "pipeline_controls": [],
            }
        }
        with patch.multiple(
            verify_release,
            FIXED_CONTROL_FILES=("platform/example.py", "missing.md"),
            PIPELINE_CONTROL_FILES=(),
            _tracked_governing_inventory=lambda: (set(), set()),
        ):
            problems = verify_release.sealed_source_problems(manifest)
        self.assertTrue(any("controls: seal incomplete" in item for item in problems))

    def test_builder_required_hashes_fail_closed(self):
        with patch.object(build_release_run_manifest, "ROOT", Path(self.tmp.name)):
            with self.assertRaisesRegex(RuntimeError, "required release-control"):
                build_release_run_manifest._hash_existing(["missing-control.md"], required=True)

    def test_clean_committed_governing_additions_cannot_evade_exact_inventory(self):
        root = Path(self.tmp.name)

        def write(rel: str, content: str) -> None:
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        def git(*args: str) -> None:
            subprocess.run(
                ["git", *args],
                cwd=root,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        git("init", "-q")
        git("config", "user.email", "release-test@example.invalid")
        git("config", "user.name", "Release Test")
        baseline = {
            "tests/base.py": "def test_base(): pass\n",
            "tests/base.R": "stopifnot(TRUE)\n",
            ".github/workflows/ci.yml": "name: baseline\n",
            "platform/conformance_rules/adam/base.yml": "id: baseline\n",
        }
        for rel, content in baseline.items():
            write(rel, content)
        git("add", ".")
        git("commit", "-qm", "baseline")

        with patch.object(build_release_run_manifest, "ROOT", root):
            tracked_programs, tracked_workflows = (
                build_release_run_manifest._tracked_governing_inventory()
            )
            program_rows = build_release_run_manifest._hash_existing(
                tracked_programs, required=True
            )
            pipeline_rows = build_release_run_manifest._hash_existing(
                tracked_workflows, required=True
            )

        manifest = {
            "artifacts": {
                "controls": [],
                "programs": program_rows,
                "pipeline_controls": pipeline_rows,
                "review_surface": [],
            }
        }
        with patch.multiple(
            verify_release,
            FIXED_CONTROL_FILES=(),
            FIXED_REVIEW_SURFACE_FILES=(),
            REVIEW_SURFACE_GLOBS=(),
            PIPELINE_CONTROL_FILES=(),
            PROGRAM_GLOBS=(),
        ):
            self.assertEqual([], verify_release.sealed_source_problems(manifest))

        additions = {
            "tests/nested/new_test.py": "def test_new(): pass\n",
            "tests/nested/new_test.R": "stopifnot(TRUE)\n",
            ".github/workflows/alternate.yaml": "name: alternate\n",
            "platform/conformance_rules/adam/new_rule.yaml": "id: new\n",
        }
        for rel, content in additions.items():
            write(rel, content)
        git("add", ".")
        git("commit", "-qm", "add governing surfaces")

        with patch.multiple(
            verify_release,
            FIXED_CONTROL_FILES=(),
            FIXED_REVIEW_SURFACE_FILES=(),
            REVIEW_SURFACE_GLOBS=(),
            PIPELINE_CONTROL_FILES=(),
            PROGRAM_GLOBS=(),
        ):
            problems = verify_release.sealed_source_problems(manifest)
        rendered = "\n".join(problems)
        for rel in additions:
            self.assertIn(rel, rendered)
        self.assertIn("programs: seal incomplete", rendered)
        self.assertIn("pipeline_controls: seal incomplete", rendered)

    def test_program_and_pipeline_membership_reject_duplicates_and_extras(self):
        extra = verify_release.ROOT / "docs" / "extra.txt"
        extra.parent.mkdir(parents=True)
        extra.write_text("extra\n", encoding="utf-8")
        source_row = {
            "path": "platform/example.py",
            "sha256": verify_release.sha256(self.source),
        }
        extra_row = {
            "path": "docs/extra.txt",
            "sha256": verify_release.sha256(extra),
        }
        manifest = {
            "artifacts": {
                "controls": [],
                "programs": [source_row, dict(source_row), extra_row],
                "pipeline_controls": [extra_row, dict(extra_row)],
                "review_surface": [],
            }
        }
        with patch.multiple(
            verify_release,
            FIXED_CONTROL_FILES=(),
            FIXED_REVIEW_SURFACE_FILES=(),
            REVIEW_SURFACE_GLOBS=(),
            PIPELINE_CONTROL_FILES=(),
            PROGRAM_GLOBS=("platform/*.py",),
            _tracked_governing_inventory=lambda: (set(), set()),
        ):
            problems = verify_release.sealed_source_problems(manifest)
        rendered = "\n".join(problems)
        self.assertIn("programs: duplicate entries: platform/example.py", rendered)
        self.assertIn("programs: unexpected entries: docs/extra.txt", rendered)
        self.assertIn("pipeline_controls: duplicate entries: docs/extra.txt", rendered)
        self.assertIn("pipeline_controls: unexpected entries: docs/extra.txt", rendered)

    def test_source_and_artifact_symlinks_are_rejected(self):
        link = verify_release.ROOT / "platform" / "linked.py"
        link.symlink_to(self.source.name)
        with patch.object(build_release_run_manifest, "ROOT", verify_release.ROOT):
            with self.assertRaisesRegex(
                build_release_run_manifest.UnsafeReleaseFileError,
                "not a regular file",
            ):
                build_release_run_manifest._hash_file(link)
            with self.assertRaisesRegex(
                build_release_run_manifest.UnsafeReleaseFileError,
                "not a regular file",
            ):
                build_release_run_manifest._hash_globs(["platform/linked.py"])

        manifest = {
            "artifacts": {
                "qc_files": [{
                    "path": "platform/linked.py",
                    "present": True,
                    "sha256": verify_release.sha256(self.source),
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
        self.assertEqual((0, 0), (verified, skipped))
        self.assertTrue(any("unsafe artifact" in problem for problem in problems))

    def test_symlinked_ancestor_is_rejected(self):
        outside = Path(self.tmp.name).parent / (Path(self.tmp.name).name + "-outside")
        outside.mkdir()
        try:
            (outside / "source.py").write_text("external\n", encoding="utf-8")
            link = verify_release.ROOT / "linked_directory"
            link.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(
                verify_release.UnsafeReleaseFileError,
                "ancestor is not a directory",
            ):
                verify_release.sha256(link / "source.py")
        finally:
            (outside / "source.py").unlink()
            outside.rmdir()

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO creation is unavailable")
    def test_matching_nonregular_glob_entry_is_rejected(self):
        fifo = Path(self.tmp.name) / "platform" / "named_pipe.py"
        os.mkfifo(fifo)
        with patch.object(build_release_run_manifest, "ROOT", Path(self.tmp.name)):
            with self.assertRaisesRegex(
                build_release_run_manifest.UnsafeReleaseFileError,
                "not a regular file",
            ):
                build_release_run_manifest._hash_globs(["platform/*.py"])

    def test_leaf_swap_between_lstat_and_open_is_rejected(self):
        root = Path(self.tmp.name)
        victim = root / "platform" / "victim.py"
        replacement = root / "platform" / "replacement.tmp"
        victim.write_text("original\n", encoding="utf-8")
        replacement.write_text("replacement\n", encoding="utf-8")
        real_open = build_release_run_manifest.os.open
        swapped = False

        def swapping_open(path, flags, mode=0o600, *, dir_fd=None):
            nonlocal swapped
            if path == "victim.py" and dir_fd is not None and not swapped:
                swapped = True
                os.replace(replacement, victim)
            return real_open(path, flags, mode, dir_fd=dir_fd)

        with patch.object(build_release_run_manifest, "ROOT", root):
            with patch.object(build_release_run_manifest.os, "open", side_effect=swapping_open):
                with self.assertRaisesRegex(
                    build_release_run_manifest.UnsafeReleaseFileError,
                    "changed during open",
                ):
                    build_release_run_manifest._hash_file(victim)
        self.assertTrue(swapped)

    def test_ancestor_swap_between_lstat_and_open_is_rejected(self):
        root = Path(self.tmp.name)
        sealed_dir = root / "platform" / "sealed"
        replacement_dir = root / "platform" / "replacement"
        displaced_dir = root / "platform" / "displaced"
        sealed_dir.mkdir()
        replacement_dir.mkdir()
        victim = sealed_dir / "victim.py"
        victim.write_text("original\n", encoding="utf-8")
        (replacement_dir / "victim.py").write_text("replacement\n", encoding="utf-8")
        real_open = build_release_run_manifest.os.open
        swapped = False

        def swapping_open(path, flags, mode=0o600, *, dir_fd=None):
            nonlocal swapped
            if path == "sealed" and dir_fd is not None and not swapped:
                swapped = True
                os.replace(sealed_dir, displaced_dir)
                os.replace(replacement_dir, sealed_dir)
            return real_open(path, flags, mode, dir_fd=dir_fd)

        with patch.object(build_release_run_manifest, "ROOT", root):
            with patch.object(build_release_run_manifest.os, "open", side_effect=swapping_open):
                with self.assertRaisesRegex(
                    build_release_run_manifest.UnsafeReleaseFileError,
                    "ancestor changed during open",
                ):
                    build_release_run_manifest._hash_file(victim)
        self.assertTrue(swapped)

    def test_release_binding_requires_metadata_control_pass(self):
        self.assertTrue(build_release_run_manifest._metadata_control_pass({"status": "pass"}))
        self.assertTrue(build_release_run_manifest._metadata_control_pass({"status": "PASS"}))
        for status in ({}, {"status": "missing"}, {"status": "warning"}, {"status": "FAIL"}):
            self.assertFalse(build_release_run_manifest._metadata_control_pass(status))


if __name__ == "__main__":
    unittest.main()
