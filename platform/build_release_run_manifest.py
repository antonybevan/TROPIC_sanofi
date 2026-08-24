#!/usr/bin/env python3
"""Build a current release-run manifest with file hashes and QC verdict binding.

This is a hash-sealed run record, not an electronic signature or Part 11
attestation. It binds the current workspace state, runtime telemetry, programs,
datasets, outputs, logs, package files, and QC status files into one machine
readable record so stale evidence cannot be mistaken for the current run.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import stat
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Iterator

from governance_reseal_policy import governance_chain_policy_problems

try:
    import yaml
except ImportError:  # pragma: no cover - CI/runtime dependency check catches this
    yaml = None


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "platform/release_run_manifest"
REPORT = ROOT / "docs/RELEASE_RUN_MANIFEST.md"
BINDING_CSV = ROOT / "06_qc_evidence/audit/output_hash_binding.csv"


QC_FILES = {
    "pipeline_health": "platform/pipeline_health.json",
    "reconciliation": "platform/reconciliation_status.json",
    "results_reconciliation": "platform/results_reconciliation_status.json",
    "forest_reconciliation": "platform/forest_reconciliation_status.json",
    "figure_data_reconciliation": "platform/figure_data_reconciliation_status.json",
    "cbzp_bridge": "platform/cbzp_bridge_status.json",
    "spec_define": "platform/conformance/spec_define_conformance.json",
    "spec_data": "platform/conformance/spec_data_conformance.json",
    "metadata_control": "platform/metadata_control/metadata_control_status.json",
    "log_cleanliness": "platform/log_cleanliness/log_cleanliness_status.json",
    "tfl_output_index": "platform/tfl_output_index_status.json",
    "validation_strategy": "platform/validation_strategy/validation_strategy_status.json",
    "simulation_operating_characteristics": "platform/simulation_operating_characteristics/simulation_oc_status.json",
    "regulatory_baseline": "06_qc_evidence/gates/regulatory_baseline_status.json",
}

CONTROL_FILES = [
    "00_governance/REPRODUCIBILITY.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "config/study_manifest.yaml",
    "config/study_config.yaml",
    "config/tfl_output_catalog.yaml",
    "config/validation_strategy.yaml",
    "config/ctq_traceability.yaml",
    "config/delivery_workstreams.yaml",
    "config/evidence_layers.yaml",
    "config/metadata_lineage.yaml",
    "config/log_cleanliness.yaml",
    "config/regulatory_baseline.yaml",
    "config/fda_readiness_profile.yaml",
    "config/regulatory_source_inventory.yaml",
    "config/simulation_protocol.yaml",
    "docs/PRODUCT_CLAIM.md",
    "docs/QUALITY_SYSTEM_BOUNDARY.md",
    "docs/FDA_READINESS_RESEARCH_2026-08-15.md",
    "docs/SIMULATION_PRECISION_RESEARCH.md",
    "docs/runbooks/ENVIRONMENT_BOOTSTRAP.md",
    "docs/runbooks/RELEASE_PROMOTION.md",
    "docs/workstreams/decisions/PYTHON_RUNTIME_MIGRATION_2026-08-24.md",
    "06_qc_evidence/conformance/p21_adam_runrecord.md",
    "06_qc_evidence/conformance/p21_adam_summary.json",
    "platform/conformance_rules/adam/RULES.lock",
    "platform/conformance/core_cache_manifest.json",
    "platform/conformance/CORE_RUN_RECORD.md",
    "platform/conformance/CORE_SDTM34_RUN_RECORD.md",
    "03_metadata/adam/ADaM_spec.xlsx",
    "03_metadata/define/define.xml",
    "03_metadata/define/define_sdtm.xml",
    "04_analysis_datasets/programs/sas/U_xpt_export.sas",
    "04_analysis_datasets/programs/sas/_adam_labels.sas",
    "04_analysis_datasets/programs/r/config_study.R",
    "04_analysis_datasets/programs/r/adam_var_labels.csv",
    "04_analysis_datasets/programs/r/spec_data_checks.R",
    "06_qc_evidence/reconciliation/cross_lang_audit.R",
    "06_qc_evidence/reconciliation/results_reconcile.R",
    "06_qc_evidence/reconciliation/forest_reconcile.R",
    "06_qc_evidence/reconciliation/figure_data_reconcile.R",
    "06_qc_evidence/audit/build_variable_traceability.py",
    "06_qc_evidence/audit/build_metadata_drift.py",
    "06_qc_evidence/audit/build_orphan_register.py",
    "06_qc_evidence/audit/findings_register.csv",
    "06_qc_evidence/audit/FINDINGS_DISPOSITION_BOARD.md",
    "06_qc_evidence/audit/orphans_dangling_deadcode.csv",
    "platform/cibuild.py",
    "platform/check_log_cleanliness.py",
    "platform/package_ectd.py",
    "platform/stage_p21_adam_inputs.py",
    "platform/build_ectd_backbone.py",
    "platform/materialize_ectd.py",
    "05_outputs/tfl/tfl_generation.R",
    "05_outputs/tfl/lab_shift_table.R",
    "05_outputs/tfl/tfl_stats.R",
]

# Pipeline controls have their own integrity digest and are also part of the
# genuine-run source-tree digest.  A runtime, dependency, cache-authority, or
# release-control change therefore requires a fresh genuine run even when that
# file is not otherwise included in the control/program inventories.
PIPELINE_CONTROL_FILES = [
    ".gitignore",
    ".python-version",
    ".github/CODEOWNERS",
    ".github/dependabot.yml",
    ".github/workflows/ci.yml",
    ".gitleaks.toml",
    ".pre-commit-config.yaml",
    "requirements-core-build.lock",
    "requirements-core.txt",
    "requirements-core.lock",
    "requirements-ci-build.lock",
    "requirements-ci.txt",
    "requirements-ci.lock",
    "renv.lock",
    "platform/conformance_rules/adam/RULES.lock",
    "platform/conformance/core_cache_manifest.json",
    "platform/run_core_conformance.sh",
    "platform/run_core_update_cache.py",
    "platform/verify_core_cache.py",
    "platform/verify_core_source.py",
    "platform/governance_reseal_policy.py",
    "scripts/rebind_governance_seal.py",
    "scripts/verify_release.py",
]

# Reviewer-facing narrative and visual surfaces are release material too. Keep
# them in a dedicated artifact group so a corrected table, claim, or acceptance
# screenshot cannot drift after the clinical run while the seal still passes.
REVIEW_SURFACE_FILES = [
    "CHANGELOG.md",
    "README.md",
    "08_submission_package/README.md",
    "docs/INDEX.md",
    "docs/BIOMETRICS_DELIVERY_OPERATING_MODEL.md",
    "docs/PIPELINE_ARCHITECTURE_REDESIGN.md",
    "docs/REPO_SURFACE_POLICY.md",
    "docs/WORKSTREAM_EXECUTION_BOARD.md",
    "docs/INTERVIEWER_GUIDE.md",
    "docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md",
    "05_outputs/tfl/TFL_Gallery.html",
    "06_qc_evidence/audit/DASHBOARD_VISUAL_QC.md",
    "06_qc_evidence/audit/FIGURE_AUDIT_2026-08-23.md",
    "06_qc_evidence/audit/PROFESSIONAL_RELEASE_AUDIT_2026-08-24.md",
    "06_qc_evidence/audit/REPO_PROFESSIONAL_BUILD_AUDIT_2026-08-14.md",
    "06_qc_evidence/audit/SIMULATION_PRECISION_IMPLEMENTATION_REPORT_2026-08-14.md",
    "06_qc_evidence/audit/REPOSITORY_CLEANUP_AUDIT_2026-08-23.md",
    "07_reviewer_explanation/simulation_model_analysis_plan.md",
    "07_reviewer_explanation/simulation_report.md",
    "platform/simulation_operating_characteristics/scenario_results.csv",
    "platform/simulation_operating_characteristics/representative_trials.json",
]
REVIEW_SURFACE_GLOBS = [
    "06_qc_evidence/audit/dashboard_evidence/*.[jJ][pP][gG]",
]

# Keep the source inventory in one place.  The same digest is written into
# pipeline_health.json at run time and recomputed here during release sealing;
# this prevents a green health snapshot from being paired with later-edited
# programs or controls.
PROGRAM_GLOBS = [
    "04_analysis_datasets/programs/sas/**/*.sas",
    "04_analysis_datasets/programs/r/**/*.R",
    "06_qc_evidence/reconciliation/**/*.R",
    "platform/*.py",
    "platform/*.R",
    "03_metadata/define/*.py",
    "03_metadata/define/*.R",
    "05_outputs/tfl/**/*.R",
    "07_reviewer_explanation/tools/shiny/**/*.R",
]

# These Git-tracked governing surfaces are intentionally discovered instead of
# maintained as a hand-written file list.  Tests, conformance rules, and
# workflows enter the clinical source digest, so adding one requires a fresh
# genuine run. Workflows are also bound as pipeline controls.
TRACKED_INVENTORY_ROOTS = (
    "tests",
    ".github/workflows",
    "platform/conformance_rules/adam",
)

# Generated configuration is consumed by the local/ODA run but is intentionally
# ignored by Git. It must not enter a release source seal that a clean checkout
# cannot reproduce; the authoritative YAML/config generator is sealed instead.
GENERATED_SOURCE_EXCLUDES = {
    "04_analysis_datasets/programs/sas/00_config_generated.sas",
}


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


class UnsafeReleaseFileError(RuntimeError):
    """A release input was not a stable repository-contained regular file."""


def _release_path_parts(rel_path: str) -> tuple[str, ...]:
    """Validate a repository-relative POSIX path without resolving symlinks."""
    candidate = PurePosixPath(rel_path)
    if (
        not rel_path
        or candidate.is_absolute()
        or not candidate.parts
        or any(part in {"", ".", ".."} for part in candidate.parts)
    ):
        raise UnsafeReleaseFileError(f"unsafe release path: {rel_path!r}")
    return candidate.parts


def _stable_metadata(st: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        st.st_dev,
        st.st_ino,
        st.st_mode,
        st.st_size,
        st.st_mtime_ns,
        st.st_ctime_ns,
    )


@contextmanager
def _open_stable_regular(rel_path: str) -> Iterator[tuple[int, os.stat_result]]:
    """Open a stable regular file through a pinned, no-follow directory chain.

    Every path component is checked with the descriptor-relative equivalent of
    lstat and then opened with O_NOFOLLOW.  Keeping all ancestor descriptors
    open and rechecking their identities after the read prevents an ancestor or
    leaf rename/symlink swap from changing which object is sealed.
    """
    parts = _release_path_parts(rel_path)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    if not nofollow or not directory:
        raise UnsafeReleaseFileError(
            "release hashing requires O_NOFOLLOW and O_DIRECTORY support"
        )

    descriptors: list[int] = []
    directory_checks: list[tuple[int, str, tuple[int, int]]] = []
    leaf_fd: int | None = None
    try:
        root_before = os.stat(ROOT, follow_symlinks=False)
        if not stat.S_ISDIR(root_before.st_mode):
            raise UnsafeReleaseFileError("release repository root is not a directory")
        root_fd = os.open(ROOT, os.O_RDONLY | directory | nofollow)
        root_opened = os.fstat(root_fd)
        if (
            not stat.S_ISDIR(root_opened.st_mode)
            or (root_before.st_dev, root_before.st_ino)
            != (root_opened.st_dev, root_opened.st_ino)
        ):
            os.close(root_fd)
            raise UnsafeReleaseFileError("release repository root changed during open")
        descriptors.append(root_fd)
        parent_fd = root_fd
        for component in parts[:-1]:
            before = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
            if not stat.S_ISDIR(before.st_mode):
                raise UnsafeReleaseFileError(
                    f"release path ancestor is not a directory: {rel_path}"
                )
            child_fd = os.open(
                component,
                os.O_RDONLY | directory | nofollow,
                dir_fd=parent_fd,
            )
            opened = os.fstat(child_fd)
            if (
                not stat.S_ISDIR(opened.st_mode)
                or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino)
            ):
                os.close(child_fd)
                raise UnsafeReleaseFileError(
                    f"release path ancestor changed during open: {rel_path}"
                )
            directory_checks.append(
                (parent_fd, component, (opened.st_dev, opened.st_ino))
            )
            descriptors.append(child_fd)
            parent_fd = child_fd

        leaf = parts[-1]
        before = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode):
            raise UnsafeReleaseFileError(
                f"release input is not a regular file: {rel_path}"
            )
        leaf_fd = os.open(leaf, os.O_RDONLY | nofollow, dir_fd=parent_fd)
        opened = os.fstat(leaf_fd)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise UnsafeReleaseFileError(
                f"release input changed during open: {rel_path}"
            )

        yield leaf_fd, opened

        after = os.fstat(leaf_fd)
        try:
            current = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        except OSError as exc:
            raise UnsafeReleaseFileError(
                f"release input changed during hashing: {rel_path}"
            ) from exc
        if (
            not stat.S_ISREG(current.st_mode)
            or _stable_metadata(opened) != _stable_metadata(after)
            or (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino)
        ):
            raise UnsafeReleaseFileError(
                f"release input changed during hashing: {rel_path}"
            )
        try:
            root_current = os.stat(ROOT, follow_symlinks=False)
        except OSError as exc:
            raise UnsafeReleaseFileError(
                "release repository root changed during hashing"
            ) from exc
        if (
            not stat.S_ISDIR(root_current.st_mode)
            or (root_opened.st_dev, root_opened.st_ino)
            != (root_current.st_dev, root_current.st_ino)
        ):
            raise UnsafeReleaseFileError(
                "release repository root changed during hashing"
            )
        for ancestor_fd, component, identity in directory_checks:
            try:
                current_dir = os.stat(
                    component, dir_fd=ancestor_fd, follow_symlinks=False
                )
            except OSError as exc:
                raise UnsafeReleaseFileError(
                    f"release path ancestor changed during hashing: {rel_path}"
                ) from exc
            if (
                not stat.S_ISDIR(current_dir.st_mode)
                or (current_dir.st_dev, current_dir.st_ino) != identity
            ):
                raise UnsafeReleaseFileError(
                    f"release path ancestor changed during hashing: {rel_path}"
                )
    finally:
        if leaf_fd is not None:
            os.close(leaf_fd)
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _run_git(args: list[str]) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).rstrip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _tracked_governing_inventory() -> tuple[list[str], list[str]]:
    """Return tracked fresh-run programs/rules and pipeline workflows."""
    try:
        raw = subprocess.check_output(
            ["git", "ls-files", "-z", "--", *TRACKED_INVENTORY_ROOTS],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("cannot derive tracked release-control inventory") from exc
    paths = [
        item.decode("utf-8")
        for item in raw.split(b"\0")
        if item
    ]
    programs = sorted(
        path
        for path in paths
        if (
            path.startswith("tests/")
            and (path.endswith(".py") or path.endswith(".R"))
        )
        or (
            path.startswith("platform/conformance_rules/adam/")
            and (path.endswith(".yml") or path.endswith(".yaml"))
        )
        or (
            path.startswith(".github/workflows/")
            and (path.endswith(".yml") or path.endswith(".yaml"))
        )
    )
    workflows = sorted(
        path
        for path in paths
        if path.startswith(".github/workflows/")
        and (path.endswith(".yml") or path.endswith(".yaml"))
    )
    return programs, workflows


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source_tree_sha256(*row_groups: list) -> str:
    """Digest of all run-affecting sealed source, without seal outputs.

    Replaces HEAD-based staleness binding: committing the tracked seal advances
    HEAD past the recorded head, so a committed manifest can never satisfy a
    current_HEAD equality check (audit CRITICAL). The source-tree digest attests
    to the exact source/config/program/pipeline-control tree the seal was built
    from, is stable across the seal commit (seal outputs are in no input group),
    and is recomputable in a bare clone. Identical paths shared by inventories
    are intentionally deduplicated.
    """
    rows = sorted(
        {
            (row["path"], row["sha256"])
            for group in row_groups
            for row in group
            if row.get("sha256")
        }
    )
    return _sha256_bytes(b"\n".join(f"{p}\0{s}".encode("utf-8") for p, s in rows))


def _current_source_tree_sha256() -> str:
    """Recompute the run binding from all current run-affecting controls."""
    controls = _hash_existing(CONTROL_FILES, required=True)
    tracked_programs, tracked_workflows = _tracked_governing_inventory()
    programs = _merge_hash_rows(
        _hash_globs(PROGRAM_GLOBS, exclude_paths=GENERATED_SOURCE_EXCLUDES),
        _hash_existing(tracked_programs, required=True),
    )
    pipeline_controls = _merge_hash_rows(
        _hash_existing(PIPELINE_CONTROL_FILES, required=True),
        _hash_existing(tracked_workflows, required=True),
    )
    return _source_tree_sha256(controls, programs, pipeline_controls)


def _hash_file(path: Path) -> dict:
    rel_path = _rel(path)
    h256 = hashlib.sha256()
    hmd5 = hashlib.md5()  # identity checksum for SAS/XPT parity, not a security use
    try:
        with _open_stable_regular(rel_path) as (fd, opened):
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                h256.update(chunk)
                hmd5.update(chunk)
    except FileNotFoundError:
        return {
            "path": rel_path,
            "present": False,
            "size_bytes": None,
            "sha256": "",
            "md5": "",
        }
    return {
        "path": rel_path,
        "present": True,
        "size_bytes": opened.st_size,
        "sha256": h256.hexdigest(),
        "md5": hmd5.hexdigest(),
    }


def _read_regular_bytes(rel_path: str) -> bytes:
    chunks: list[bytes] = []
    with _open_stable_regular(rel_path) as (fd, _):
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)


def _load_json(rel_path: str) -> dict:
    try:
        raw = _read_regular_bytes(rel_path)
    except FileNotFoundError:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}


def _load_manifest() -> dict:
    if yaml is None:
        return {}
    try:
        raw = _read_regular_bytes("config/study_manifest.yaml")
    except FileNotFoundError:
        return {}
    data = yaml.safe_load(raw.decode("utf-8"))
    return data if isinstance(data, dict) else {}


def _dataset_names(manifest: dict) -> list[str]:
    datasets = manifest.get("datasets", [])
    names = [str(d.get("name", "")).lower() for d in datasets if d.get("name")]
    return names or ["adsl", "adex", "adcm", "adae", "adlb", "adrs", "adtte", "clinsite"]


def _expected_stage_names(manifest: dict) -> list[str]:
    """Mirror cibuild.build_stages() naming so partial runs are detectable."""
    infra = manifest.get("infrastructure_stages", {}) or {}
    names: list[str] = []
    for stage in infra.get("pre", []) or []:
        if stage.get("name"):
            names.append(str(stage["name"]))
    for dataset in manifest.get("datasets", []) or []:
        if not dataset.get("name"):
            continue
        names.append(str(dataset.get("val_stage") or f"R {str(dataset['name']).upper()} Validation"))
    for stage in infra.get("pre_sas", []) or []:
        if stage.get("name"):
            names.append(str(stage["name"]))
    names.append("SAS Production (ODA/Real/Simulated)")
    for stage in infra.get("post", []) or []:
        if stage.get("name"):
            names.append(str(stage["name"]))
    return names


def _parse_iso_ts(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _file_mtime_utc(path: Path):
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _sas_companion_freshness(health: dict) -> dict:
    """SAS companion figures are rendered by the real-SAS stage; flag stale files."""
    pattern = "05_outputs/tfl/output/figures/sas/*"
    health_ts = _parse_iso_ts(health.get("timestamp"))
    files = []
    stale = []
    for path in sorted(ROOT.glob(pattern)):
        if not path.is_file():
            continue
        mtime = _file_mtime_utc(path)
        current = False
        if health_ts and mtime:
            ht = health_ts if health_ts.tzinfo else health_ts.replace(tzinfo=timezone.utc)
            mt = mtime if mtime.tzinfo else mtime.replace(tzinfo=timezone.utc)
            # 1h skew tolerance for clock differences between ODA render and local health write
            current = mt >= (ht - timedelta(hours=1))
        row = {
            "path": _rel(path),
            "mtime_utc": mtime.isoformat() if mtime else None,
            "current_with_pipeline_health": current,
        }
        if not current:
            stale.append(row["path"])
        files.append(row)
    return {
        "generation_scope": "in_dag_real_sas_companion",
        "file_count": len(files),
        "files": files,
        "stale_paths": stale,
        "all_current_with_pipeline_health": bool(files) and not stale,
        "note": (
            "SAS companion figures are rendered by the manifest-named SAS Production stage and "
            "their figure-driving CSVs are reconciled before release sealing."
        ),
    }


def _run_completeness(health: dict, expected_stages: list[str]) -> dict:
    recorded = health.get("stages") or {}
    # While this stage is executing, health may have been written immediately upstream
    # and therefore omit "Release Run Manifest Binding". Require every other DAG stage.
    required = [n for n in expected_stages if n != "Release Run Manifest Binding"]
    missing = [n for n in required if n not in recorded]
    not_run = [n for n in required if recorded.get(n) == "NOT_RUN"]
    failed = [n for n in required if recorded.get(n) == "FAIL"]
    # Legitimate SKIPPED (e.g. results recon not_available) is allowed in non-release grades;
    # for release-candidate full_dag we still allow SKIPPED only when overall health is GREEN
    # and mode is not asserting full real-SAS results evidence... keep simple: PASS or SKIPPED ok.
    non_success = [
        n for n in required
        if recorded.get(n) not in {"PASS", "SKIPPED", "NOT_RUN", None} and n in recorded
    ]
    health_scope = health.get("run_scope")
    complete = not missing and not not_run and not failed
    # Prefer structural completeness of required upstream stages over an intermediate
    # health.run_scope label written mid-pipeline (which can be partial only because
    # the release-manifest stage itself had not yet run).
    scope = "full_dag" if complete else "partial_dag"
    return {
        "run_scope": scope,
        "stages_expected": len(expected_stages),
        "expected_stage_names": list(expected_stages),
        "stages_required_for_release": len(required),
        "stages_recorded_in_health": len(recorded),
        "missing_from_health": missing,
        "not_run": not_run,
        "failed": failed,
        "non_success": non_success,
        "health_run_scope": health_scope,
    }


# Paths this seal (and the sibling RC checklist) rewrites on every run. They must
# not self-trip the dirty-worktree remediation gate or a PASS seal can never land
# on a clean tree.
_SEAL_SELF_PATH_PREFIXES = (
    "platform/release_run_manifest/",
    "platform/release_candidate/",
    "docs/RELEASE_RUN_MANIFEST.md",
    "docs/RELEASE_CANDIDATE_CHECKLIST.md",
    "06_qc_evidence/audit/output_hash_binding.csv",
)


def _porcelain_path(line: str) -> str:
    # porcelain v1: "XY path" or "XY orig -> path" (renames)
    body = line[3:] if len(line) >= 4 else line
    if " -> " in body:
        body = body.split(" -> ", 1)[1]
    return body.strip()


def _is_seal_self_path(path: str) -> bool:
    return any(path == p or path.startswith(p) for p in _SEAL_SELF_PATH_PREFIXES)


def _git_state() -> dict:
    status = _run_git(["status", "--porcelain=v1"])
    tracked_diff_names = _run_git(["diff", "--name-only", "HEAD", "--"])
    staged_diff_names = _run_git(["diff", "--cached", "--name-only"])
    all_lines = [x for x in status.splitlines() if x]
    material_lines = [ln for ln in all_lines if not _is_seal_self_path(_porcelain_path(ln))]
    return {
        "head": _run_git(["rev-parse", "HEAD"]),
        "branch": _run_git(["branch", "--show-current"]),
        "dirty": bool(material_lines),
        "dirty_including_seal_outputs": bool(all_lines),
        "status_porcelain_sha256": _sha256_bytes("\n".join(material_lines).encode("utf-8")) if material_lines else "",
        "tracked_diff_paths": [x for x in tracked_diff_names.splitlines() if x and not _is_seal_self_path(x)],
        "staged_diff_paths": [x for x in staged_diff_names.splitlines() if x and not _is_seal_self_path(x)],
        "status_porcelain": material_lines,
        "status_porcelain_all": all_lines,
    }


def _hash_existing(paths: list[str], *, required: bool = False) -> list[dict]:
    """Hash a fixed path list, optionally failing closed on missing paths.

    Review surfaces are intentionally optional in a data-free checkout, but the
    fixed control and pipeline-control registries are part of the release
    identity. Silently dropping one of those files would make the source-tree
    digest incomplete and could allow an unsealed control change.
    """
    rows = []
    missing = []
    for rel_path in paths:
        row = _hash_file(ROOT / rel_path)
        if row["present"]:
            rows.append(row)
        else:
            missing.append(rel_path)
    if required and missing:
        raise RuntimeError(
            "required release-control file(s) missing: " + ", ".join(missing)
        )
    return rows


def _hash_globs(patterns: list[str], exclude_paths: set[str] | None = None) -> list[dict]:
    rows = []
    seen: set[str] = set()
    exclude_paths = exclude_paths or set()
    for pattern in patterns:
        for path in sorted(ROOT.glob(pattern)):
            rel_path = _rel(path)
            if rel_path in seen or rel_path in exclude_paths:
                continue
            # Recursive globs naturally yield real directory containers.  They
            # are not file leaves; every other matching type is passed to the
            # secure hasher, which rejects symlinks, FIFOs, devices, and sockets.
            try:
                leaf_lstat = path.lstat()
            except FileNotFoundError as exc:
                raise UnsafeReleaseFileError(
                    f"release glob entry changed during enumeration: {rel_path}"
                ) from exc
            if stat.S_ISDIR(leaf_lstat.st_mode):
                continue
            seen.add(rel_path)
            row = _hash_file(path)
            if not row["present"]:
                raise UnsafeReleaseFileError(
                    f"release glob entry disappeared during hashing: {rel_path}"
                )
            rows.append(row)
    return rows


def _merge_hash_rows(*groups: list[dict]) -> list[dict]:
    """Merge independently derived inventories without duplicate seal rows."""
    rows: dict[str, dict] = {}
    for group in groups:
        for row in group:
            rel_path = row.get("path")
            if not rel_path:
                raise RuntimeError(f"release inventory contains an invalid row: {row!r}")
            prior = rows.get(rel_path)
            if prior is not None and prior != row:
                raise RuntimeError(f"release inventory changed while merging: {rel_path}")
            rows[rel_path] = row
    return [rows[path] for path in sorted(rows)]


def _expected_program_paths(tracked_programs: list[str]) -> set[str]:
    """Derive the exact current program/source membership used by the builder."""
    static_rows = _hash_globs(
        PROGRAM_GLOBS, exclude_paths=GENERATED_SOURCE_EXCLUDES
    )
    return {row["path"] for row in static_rows} | set(tracked_programs)


def _inventory_membership_problems(
    group: str, rows: object, expected: set[str]
) -> list[str]:
    if not isinstance(rows, list):
        return [f"{group}: seal inventory is not a list"]
    raw_paths = [row.get("path") if isinstance(row, dict) else None for row in rows]
    paths = [path for path in raw_paths if isinstance(path, str) and path]
    actual = set(paths)
    duplicates = sorted(path for path in actual if paths.count(path) > 1)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    problems: list[str] = []
    if duplicates:
        problems.append(f"{group}: duplicate entries: " + ", ".join(duplicates))
    if missing:
        problems.append(f"{group}: seal incomplete: " + ", ".join(missing))
    if unexpected:
        problems.append(f"{group}: unexpected entries: " + ", ".join(unexpected))
    if len(paths) != len(raw_paths):
        problems.append(f"{group}: seal contains entries without valid paths")
    return problems


def _dataset_hashes(datasets: list[str]) -> tuple[list[dict], list[dict]]:
    rows = []
    binding = []
    for ds in datasets:
        prod = ROOT / f"04_analysis_datasets/adam/{ds}_prod.xpt"
        val = ROOT / f"04_analysis_datasets/adam/{ds}_v.xpt"
        if ds == "clinsite":
            package = ROOT / "08_submission_package/m5/datasets/tropic/bimo/datasets/clinsite.xpt"
            sequence = ROOT / "08_submission_package/ectd/0000/m5/datasets/tropic/bimo/datasets/clinsite.xpt"
        else:
            package = ROOT / f"08_submission_package/m5/datasets/tropic/analysis/adam/datasets/{ds}.xpt"
            sequence = ROOT / f"08_submission_package/ectd/0000/m5/datasets/tropic/analysis/adam/datasets/{ds}.xpt"

        prod_h = _hash_file(prod)
        val_h = _hash_file(val)
        pkg_h = _hash_file(package)
        seq_h = _hash_file(sequence)
        distinct = bool(prod_h["md5"] and val_h["md5"] and prod_h["md5"] != val_h["md5"])
        pkg_match = bool(prod_h["md5"] and pkg_h["md5"] and prod_h["md5"] == pkg_h["md5"])
        seq_match = bool(prod_h["md5"] and seq_h["md5"] and prod_h["md5"] == seq_h["md5"])

        rows.append({
            "dataset": ds.upper(),
            "prod": prod_h,
            "validation": val_h,
            "package_copy": pkg_h,
            "sequence_copy": seq_h,
            "prod_vs_validation_distinct": distinct,
            "package_matches_prod": pkg_match,
            "sequence_matches_prod": seq_match,
        })
        binding.append({
            "dataset": ds.upper(),
            "current_prod_md5": prod_h["md5"],
            "current_v_md5": val_h["md5"],
            "package_md5": pkg_h["md5"],
            "sequence_md5": seq_h["md5"],
            "release_manifest_prod_md5": prod_h["md5"],
            "prod_vs_validation_distinct": "YES" if distinct else "NO",
            "current_matches_package": "YES" if pkg_match else "NO",
            "current_matches_sequence": "YES" if seq_match else "NO",
            "current_matches_release_manifest": "YES" if prod_h["md5"] else "NO",
        })
    return rows, binding


def _qc_statuses() -> tuple[dict, list[dict]]:
    statuses = {}
    hashes = []
    for name, rel_path in QC_FILES.items():
        data = _load_json(rel_path)
        if name == "simulation_operating_characteristics":
            simulation_statuses = data.get("statuses") or {}
            required = (
                (simulation_statuses.get("execution") or {}).get("status") == "PASS"
                and (simulation_statuses.get("monte_carlo_precision") or {}).get("status") == "PASS"
                and (simulation_statuses.get("design_operating_characteristics") or {}).get("status") == "PASS"
                and (simulation_statuses.get("evidence_qualification") or {}).get("status") == "NOT_QUALIFIED"
            )
            status = "PASS" if required else "FAIL"
        else:
            status = (
                data.get("overall")
                or data.get("status")
                or data.get("pipeline_health_status")
                or "missing"
            )
        statuses[name] = {
            "path": rel_path,
            "status": status,
            "detail": {
                "sas_execution_mode": data.get("sas_execution_mode"),
                "simulated": data.get("simulated"),
                "provenance_guard_passed": (data.get("provenance_guard") or {}).get("passed"),
            },
        }
        row = _hash_file(ROOT / rel_path)
        if row["present"]:
            hashes.append(row)
    return statuses, hashes


def _metadata_control_pass(status: dict) -> bool:
    return str(status.get("status", "")).lower() == "pass"


def _binding_problems(payload: dict) -> list[str]:
    """Hard binding failures (package/data/QC integrity). These always force FAIL."""
    problems = []
    health = _load_json(QC_FILES["pipeline_health"])

    expected_source_tree = payload["source_control"].get("source_tree_sha256", "")
    recorded_source_tree = health.get("source_tree_sha256", "")
    if not recorded_source_tree:
        problems.append(
            "pipeline_health.json has no source_tree_sha256 run binding; "
            "health is not attributable to the current control/program tree"
        )
    elif recorded_source_tree != expected_source_tree:
        problems.append(
            "pipeline_health.json source_tree_sha256 does not match the current "
            "control/program tree"
        )
    recon = _load_json(QC_FILES["reconciliation"])
    results = _load_json(QC_FILES["results_reconciliation"])
    forest = _load_json(QC_FILES["forest_reconciliation"])
    figure_data = _load_json(QC_FILES["figure_data_reconciliation"])
    spec_define = _load_json(QC_FILES["spec_define"])
    spec_data = _load_json(QC_FILES["spec_data"])
    metadata_control = _load_json(QC_FILES["metadata_control"])
    log_cleanliness = _load_json(QC_FILES["log_cleanliness"])
    regulatory_baseline = _load_json(QC_FILES["regulatory_baseline"])
    simulation = _load_json(QC_FILES["simulation_operating_characteristics"])

    if health.get("pipeline_health_status") != "GREEN":
        problems.append("pipeline_health.json is not GREEN")
    if health.get("sas_execution_mode") not in {"oda", "local"}:
        problems.append("live run is not bound to a real SAS execution mode")
    if not (health.get("provenance_guard") or {}).get("passed"):
        problems.append("pipeline provenance_guard did not pass")
    if recon.get("overall") != "PASS" or recon.get("simulated"):
        problems.append("dataset reconciliation is not non-simulated PASS")
    if (recon.get("endpoint_controls") or {}).get("F042_PAIN_RESPONSE") != "PASS":
        problems.append("F-042 pain-response SAS/R reconciliation is not PASS")
    if results.get("overall") != "PASS":
        problems.append("results reconciliation is not PASS")
    if forest.get("overall") != "PASS":
        problems.append("forest reconciliation is not PASS")
    if figure_data.get("overall") != "PASS":
        problems.append("figure-data reconciliation is not PASS")
    if spec_define.get("status") != "PASS":
        problems.append("spec-to-Define conformance is not PASS")
    if spec_data.get("status") != "PASS":
        problems.append("spec-to-data conformance is not PASS")
    if not _metadata_control_pass(metadata_control):
        problems.append("metadata control evidence refresh is not PASS")
    if log_cleanliness.get("status") != "PASS":
        problems.append("log cleanliness gate is not PASS")
    if regulatory_baseline.get("status") != "PASS":
        problems.append("regulatory baseline and validator-evidence gate is not PASS")
    simulation_statuses = simulation.get("statuses") or {}
    for key in ("execution", "monte_carlo_precision", "design_operating_characteristics"):
        if (simulation_statuses.get(key) or {}).get("status") != "PASS":
            problems.append(f"simulation {key} status is not PASS")
    if (simulation_statuses.get("evidence_qualification") or {}).get("status") != "NOT_QUALIFIED":
        problems.append("simulation evidence qualification boundary is not NOT_QUALIFIED")

    governance_problems = governance_chain_policy_problems(health)
    problems.extend(
        f"governance reseal policy: {problem}"
        for problem in governance_problems
    )

    pipeline_controls = payload.get("artifacts", {}).get("pipeline_controls") or []
    tracked_programs, tracked_workflows = _tracked_governing_inventory()
    expected_programs = _expected_program_paths(tracked_programs)
    problems.extend(
        _inventory_membership_problems(
            "programs",
            (payload.get("artifacts") or {}).get("programs"),
            expected_programs,
        )
    )
    problems.extend(
        _inventory_membership_problems(
            "pipeline_controls",
            pipeline_controls,
            set(PIPELINE_CONTROL_FILES) | set(tracked_workflows),
        )
    )

    for row in payload["datasets"]:
        ds = row["dataset"]
        if not row["prod"]["present"]:
            problems.append(f"{ds}: current production XPT missing")
        if not row["validation"]["present"]:
            problems.append(f"{ds}: current validation XPT missing")
        if not row["prod_vs_validation_distinct"]:
            problems.append(f"{ds}: production and validation XPT hashes are not distinct")
        if not row["package_matches_prod"]:
            problems.append(f"{ds}: m5 package copy does not match current production XPT")
        if not row["sequence_matches_prod"]:
            problems.append(f"{ds}: materialized sequence copy does not match current production XPT")

    required_package_files = [
        "08_submission_package/ectd/0000/index.xml",
        "08_submission_package/ectd/0000/index-md5.txt",
        "08_submission_package/ectd/0000/m1/us/us-regional.xml",
        "08_submission_package/ectd/0000/m5/53-clin-stud-rep/535-rep-effic-safety-stud/mcrpc/5351-stud-rep-contr/tropic/stf-tropic.xml",
    ]
    for rel_path in required_package_files:
        if not (ROOT / rel_path).exists():
            problems.append(f"required package artifact missing: {rel_path}")

    return problems


def _remediation_reasons(payload: dict) -> list[str]:
    """Conditions that keep a hash-sealed remediation run but block release-candidate PASS."""
    reasons = []
    completeness = payload.get("run_completeness") or {}
    if completeness.get("run_scope") != "full_dag":
        missing = completeness.get("missing_from_health") or []
        not_run = completeness.get("not_run") or []
        reasons.append(
            "pipeline_health does not cover a full current DAG run "
            f"({completeness.get('stages_recorded_in_health')} recorded in health / "
            f"{completeness.get('stages_required_for_release')} release-required upstream stages; "
            f"missing={len(missing)}; not_run={len(not_run)}). "
            "Acceptable as targeted remediation evidence only."
        )
        if missing:
            preview = ", ".join(missing[:8])
            extra = "" if len(missing) <= 8 else f" (+{len(missing) - 8} more)"
            reasons.append(f"stages missing from pipeline_health: {preview}{extra}")
        if not_run:
            preview = ", ".join(not_run[:8])
            extra = "" if len(not_run) <= 8 else f" (+{len(not_run) - 8} more)"
            reasons.append(f"stages marked NOT_RUN (partial --from-stage): {preview}{extra}")

    if payload.get("source_control", {}).get("dirty"):
        n = len(payload.get("source_control", {}).get("status_porcelain") or [])
        reasons.append(
            f"git worktree is dirty ({n} porcelain entries); "
            "release-candidate lock requires a clean committed state"
        )

    return reasons


def _seal_payload(payload: dict) -> str:
    unsigned = dict(payload)
    unsigned.pop("manifest_sha256", None)
    data = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_report(payload: dict) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    dataset_lines = [
        "| Dataset | Prod MD5 | Validation MD5 | Distinct | Package match | Sequence match |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["datasets"]:
        dataset_lines.append(
            "| {dataset} | {prod} | {val} | {distinct} | {pkg} | {seq} |".format(
                dataset=row["dataset"],
                prod=row["prod"]["md5"],
                val=row["validation"]["md5"],
                distinct="yes" if row["prod_vs_validation_distinct"] else "no",
                pkg="yes" if row["package_matches_prod"] else "no",
                seq="yes" if row["sequence_matches_prod"] else "no",
            )
        )
    qc_lines = [
        "| Check | Status | Source |",
        "| --- | --- | --- |",
    ]
    for name, detail in payload["qc_statuses"].items():
        qc_lines.append(f"| {name} | {detail['status']} | {detail['path']} |")

    completeness = payload.get("run_completeness") or {}
    sas_comp = payload.get("sas_companion_figures") or {}
    lines = [
        "# TROPIC Release-Run Manifest",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "> Hash-sealed run manifest for current artifacts. This is not an electronic signature or Part 11 attestation.",
        "",
        "## Verdict",
        "",
        f"- Status: `{payload['status']}`",
        f"- Evidence grade: `{payload.get('evidence_grade', '')}`",
        f"- Manifest SHA-256 seal: `{payload['manifest_sha256']}`",
        f"- SAS execution mode: `{payload['environment'].get('sas_execution_mode', '')}`",
        f"- Pipeline health: `{payload['qc_statuses'].get('pipeline_health', {}).get('status', '')}`",
        f"- Run scope: `{completeness.get('run_scope', '')}` "
        f"({completeness.get('stages_recorded_in_health', '')} recorded / "
        f"{completeness.get('stages_required_for_release', '')} release-required upstream stages)",
        f"- Git HEAD: `{payload['source_control'].get('head', '')}`",
        f"- Worktree dirty: `{payload['source_control'].get('dirty')}`",
        f"- SAS companion figures: `{sas_comp.get('generation_scope', '')}`; "
        f"current with health=`{sas_comp.get('all_current_with_pipeline_health')}`",
        "",
        "## Status meanings",
        "",
        "- `PASS` — full current DAG + clean worktree + current-run binding; release-candidate grade.",
        "- `REMEDIATION` — hard QC/package bindings hold, but run is partial, dirty, or carries stale companion artifacts; development/remediation evidence only.",
        "- `FAIL` — package/data/QC binding integrity failed.",
        "",
        "## Problems",
        "",
    ]
    if payload["problems"]:
        lines.extend(f"- {p}" for p in payload["problems"])
    else:
        lines.append("No release-run binding problems detected.")
    if payload.get("remediation_reasons"):
        lines.extend(["", "## Remediation reasons (block release-candidate PASS)", ""])
        lines.extend(f"- {r}" for r in payload["remediation_reasons"])
    lines.extend([
        "",
        "## Dataset Binding",
        "",
        *dataset_lines,
        "",
        "## QC Verdicts",
        "",
        *qc_lines,
        "",
        "## Machine-Readable Outputs",
        "",
        "- `platform/release_run_manifest/release_run_manifest.json`",
        "- `platform/release_run_manifest/release_run_files.csv`",
        "- `06_qc_evidence/audit/output_hash_binding.csv`",
        "",
    ])
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def build_release_run_manifest(out_dir: Path = OUT_DIR) -> dict:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    manifest = _load_manifest()
    datasets = _dataset_names(manifest)
    dataset_rows, binding_rows = _dataset_hashes(datasets)
    qc_statuses, qc_hashes = _qc_statuses()
    health = _load_json(QC_FILES["pipeline_health"])

    tfl_outputs = _hash_globs([
        "05_outputs/tfl/output/tables/*",
        "05_outputs/tfl/output/figures/*",
        "05_outputs/tfl/output/figures/sas/*",
        "05_outputs/tfl/output/listings/*",
    ])
    # Seal the complete package/sequence surfaces, including programs, workbooks,
    # Define stylesheets, and official eCTD UTIL support files. Extension allowlists
    # previously omitted exactly the support/program files G08 is meant to control.
    package_hashes = _hash_globs([
        "08_submission_package/ectd/0000/**/*",
        "08_submission_package/m5/**/*",
    ])
    logs = _hash_globs([
        "04_analysis_datasets/programs/sas/oda_master_driver.log",
        "04_analysis_datasets/programs/r/*.log",
        "06_qc_evidence/reconciliation/*.log",
        "05_outputs/tfl/*.log",
    ])
    inputs = _hash_globs([
        "01_source_data/real_sdtm/**/*.sas7bdat",
        "01_source_data/cbzp_reconstructed/*.rds",
        "01_source_data/cbzp_reconstructed/*.xpt",
        ".core_run/sdtm34/*.xpt",
    ])
    additive_outputs = _hash_globs([
        "03_metadata/usdm/*.json",
        "04_analysis_datasets/datasetjson/**/*.json",
        "04_analysis_datasets/datasetjson/**/*.ndjson",
        "05_outputs/ars/**/*.csv",
        "05_outputs/ars/**/*.json",
        "05_outputs/ars/**/*.ndjson",
    ])
    review_surface = _hash_existing(REVIEW_SURFACE_FILES, required=True) + _hash_globs(
        REVIEW_SURFACE_GLOBS
    )
    tracked_programs, tracked_workflows = _tracked_governing_inventory()
    programs = _merge_hash_rows(
        _hash_globs(PROGRAM_GLOBS, exclude_paths=GENERATED_SOURCE_EXCLUDES),
        _hash_existing(tracked_programs, required=True),
    )
    controls = _hash_existing(CONTROL_FILES, required=True)
    pipeline_controls = _merge_hash_rows(
        _hash_existing(PIPELINE_CONTROL_FILES, required=True),
        _hash_existing(tracked_workflows, required=True),
    )

    expected_stages = _expected_stage_names(manifest)
    run_completeness = _run_completeness(health, expected_stages)
    sas_companion_figures = _sas_companion_freshness(health)

    git_state = _git_state()
    git_state["source_tree_sha256"] = _source_tree_sha256(
        controls, programs, pipeline_controls
    )
    git_state["pipeline_control_sha256"] = _source_tree_sha256(pipeline_controls, [])

    payload = {
        "status": "PENDING",
        "evidence_grade": "pending",
        "generated_at": generated_at,
        "source_control": git_state,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "r_version": health.get("r_version"),
            "renv_lock_sha256": health.get("renv_lock_sha256"),
            "sas_execution_mode": health.get("sas_execution_mode"),
            "sas_version": health.get("sas_version"),
            "oda_endpoint": health.get("oda_endpoint"),
            "sdtm_manifest_sha": health.get("sdtm_manifest_sha"),
            "pipeline_run_scope": health.get("run_scope"),
        },
        "run_completeness": run_completeness,
        "sas_companion_figures": sas_companion_figures,
        "datasets": dataset_rows,
        "qc_statuses": qc_statuses,
        "artifacts": {
            "controls": controls,
            "pipeline_controls": pipeline_controls,
            "inputs": inputs,
            "programs": programs,
            "qc_files": qc_hashes,
            "tfl_outputs": tfl_outputs,
            "logs": logs,
            "package_files": package_hashes,
            "additive_outputs": additive_outputs,
            "review_surface": review_surface,
        },
    }
    payload["problems"] = _binding_problems(payload)
    payload["remediation_reasons"] = _remediation_reasons(payload)
    if payload["problems"]:
        payload["status"] = "FAIL"
        payload["evidence_grade"] = "failed_binding"
    elif payload["remediation_reasons"]:
        payload["status"] = "REMEDIATION"
        payload["evidence_grade"] = "remediation_partial_or_dirty"
    else:
        payload["status"] = "PASS"
        payload["evidence_grade"] = "release_candidate"
    payload["manifest_sha256"] = _seal_payload(payload)

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "release_run_manifest.json"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    file_rows = []
    for group_name, group_rows in payload["artifacts"].items():
        for row in group_rows:
            file_rows.append({
                "group": group_name,
                "path": row["path"],
                "present": row["present"],
                "size_bytes": row["size_bytes"],
                "sha256": row["sha256"],
                "md5": row["md5"],
            })
    _write_csv(
        out_dir / "release_run_files.csv",
        file_rows,
        ["group", "path", "present", "size_bytes", "sha256", "md5"],
    )
    _write_csv(
        BINDING_CSV,
        binding_rows,
        [
            "dataset", "current_prod_md5", "current_v_md5", "package_md5", "sequence_md5",
            "release_manifest_prod_md5", "prod_vs_validation_distinct",
            "current_matches_package", "current_matches_sequence", "current_matches_release_manifest",
        ],
    )
    _write_report(payload)
    return payload


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build current release-run manifest and hash binding")
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    parser.add_argument("--allow-fail", action="store_true",
                        help="Write manifest but do not exit non-zero when binding checks fail")
    args = parser.parse_args(argv)
    payload = build_release_run_manifest(Path(args.out_dir))
    print(f"Release-run manifest status: {payload['status']}")
    print(f"Evidence grade: {payload.get('evidence_grade')}")
    print(f"Run scope: {(payload.get('run_completeness') or {}).get('run_scope')}")
    print(f"Manifest SHA-256 seal: {payload['manifest_sha256']}")
    print(f"Wrote {Path(args.out_dir) / 'release_run_manifest.json'}")
    print(f"Wrote {BINDING_CSV.relative_to(ROOT)}")
    if payload["problems"]:
        for problem in payload["problems"]:
            print(f"  [BINDING] {problem}")
    if payload.get("remediation_reasons"):
        for reason in payload["remediation_reasons"]:
            print(f"  [REMEDIATION] {reason}")
    # FAIL always non-zero. REMEDIATION exits 0 so development/partial DAG stages can
    # continue, but release-candidate checklist only accepts status == PASS.
    if payload["status"] == "FAIL" and not args.allow_fail:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
