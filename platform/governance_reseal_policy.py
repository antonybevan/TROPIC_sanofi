#!/usr/bin/env python3
"""Shared fail-closed policy for governance-only release reseals.

The reseal command, regulatory gate, manifest builder, and independent release
verifier all import this dependency-free module.  Keeping the acceptance rule in
one sealed control prevents a permissive downstream verifier from accepting a
chain that the command which creates new reseals would reject.
"""
from __future__ import annotations

from pathlib import PurePosixPath


HEALTH_REL = "platform/pipeline_health.json"

# Every exact path is hash-sealed either as a clinical control or as a review
# surface in build_release_run_manifest.py.  Changes outside this deliberately
# small set require a fresh genuine SAS run.
RESEALABLE_EXACT_PATHS = frozenset({
    "05_outputs/tfl/TFL_Gallery.html",
    "06_qc_evidence/audit/DASHBOARD_VISUAL_QC.md",
    "06_qc_evidence/audit/FIGURE_AUDIT_2026-08-23.md",
    "06_qc_evidence/audit/PROFESSIONAL_RELEASE_AUDIT_2026-08-24.md",
    "06_qc_evidence/audit/REPO_PROFESSIONAL_BUILD_AUDIT_2026-08-14.md",
    "06_qc_evidence/audit/REPOSITORY_CLEANUP_AUDIT_2026-08-23.md",
    "06_qc_evidence/audit/SIMULATION_PRECISION_IMPLEMENTATION_REPORT_2026-08-14.md",
    "CHANGELOG.md",
    "README.md",
    "docs/INDEX.md",
    "docs/REPO_SURFACE_POLICY.md",
})

DASHBOARD_EVIDENCE_DIR = PurePosixPath("06_qc_evidence/audit/dashboard_evidence")


def _is_lower_sha256(value: object) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(ch in "0123456789abcdef" for ch in text)


def _is_commit_id(value: object) -> bool:
    text = str(value or "")
    return 40 <= len(text) <= 64 and all(ch in "0123456789abcdef" for ch in text)


def is_resealable_path(path: str) -> bool:
    """Return whether a committed path is within the sealed review boundary."""
    if path in RESEALABLE_EXACT_PATHS:
        return True
    try:
        candidate = PurePosixPath(path)
    except (TypeError, ValueError):
        return False
    return (
        not candidate.is_absolute()
        and ".." not in candidate.parts
        and candidate.parent == DASHBOARD_EVIDENCE_DIR
        and candidate.suffix.lower() == ".jpg"
    )


def governance_chain_policy_problems(health: dict) -> list[str]:
    """Validate every carried reseal hop under the current release policy."""
    if not isinstance(health, dict):
        return ["pipeline health is not an object"]

    current = str(health.get("source_tree_sha256") or "")
    if not _is_lower_sha256(current):
        return ["pipeline health source digest is invalid"]

    chain = health.get("governance_reseal_chain")
    legacy = health.get("governance_only_reseal")
    if chain is None:
        chain = [legacy] if isinstance(legacy, dict) else []
    if not isinstance(chain, list) or not all(isinstance(row, dict) for row in chain):
        return ["governance reseal chain is malformed"]
    if not chain and legacy is not None:
        return ["legacy governance reseal is omitted from the explicit chain"]
    if chain and legacy is not None and legacy != chain[-1]:
        return ["legacy governance reseal does not match the final chain hop"]

    problems: list[str] = []
    expected_prior = ""
    timestamp = health.get("timestamp")
    for index, row in enumerate(chain):
        label = f"governance reseal hop {index + 1}"
        prior = str(row.get("prior_source_tree_sha256") or "")
        rebound = str(row.get("rebound_source_tree_sha256") or "")
        if (
            row.get("status") != "PASS"
            or row.get("clinical_run_was_not_reexecuted") is not True
            or not _is_commit_id(row.get("base_revision"))
            or not _is_lower_sha256(prior)
            or not _is_lower_sha256(rebound)
            or (index and prior != expected_prior)
        ):
            problems.append(f"{label} is invalid or discontinuous")
        if not timestamp or row.get("clinical_run_timestamp") != timestamp:
            problems.append(f"{label} does not bind the carried clinical timestamp")

        changed = row.get("changed_paths")
        if (
            not isinstance(changed, list)
            or not changed
            or not all(isinstance(path, str) and path for path in changed)
            or len(changed) != len(set(changed))
        ):
            problems.append(f"{label} has no valid changed-path inventory")
        else:
            forbidden = sorted(
                path
                for path in changed
                if path != HEALTH_REL and not is_resealable_path(path)
            )
            if forbidden:
                problems.append(
                    f"{label} changed fresh-run-required paths: {', '.join(forbidden)}"
                )
        expected_prior = rebound

    if chain and expected_prior != current:
        problems.append("governance reseal chain does not end at the current source digest")
    return problems
