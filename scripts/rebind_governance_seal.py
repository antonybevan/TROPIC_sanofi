#!/usr/bin/env python3
"""Rebind an existing real-SAS health snapshot after governance-only changes.

This does not rerun SAS, regenerate datasets, or change a clinical result. It is
only valid when the supplied base revision differs from HEAD in pipeline-control,
executor-validation, dependency, or test files. The resulting disclosure remains
inside pipeline_health.json and is required by the release-manifest builder.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HEALTH = ROOT / "platform/pipeline_health.json"

ALLOWED_PATHS = (
    ".github/",
    ".gitleaks.toml",
    ".hermes.md",
    ".pre-commit-config.yaml",
    "08_submission_package/README.md",
    "CHANGELOG.md",
    "README.md",
    "TROPIC_PIPELINE_AUDIT_CLOSURE_2026-08-10.md",
    "config/evidence_layers.yaml",
    "config/regulatory_baseline.yaml",
    "docs/PRODUCT_CLAIM.md",
    "docs/QUALITY_SYSTEM_BOUNDARY.md",
    "docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md",
    "docs/WORKSTREAM_EXECUTION_BOARD.md",
    "docs/workstreams/WS1_SOURCE_INTAKE_PACK.md",
    "docs/workstreams/WS3_EXTERNAL_VALIDATION_EVIDENCE_INDEX.md",
    "docs/workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md",
    "docs/workstreams/reviews/PATH_A_STATISTICAL_GOVERNANCE_ASSESSMENT_2026-08-04.md",
    "06_qc_evidence/audit/AUDIT_REPORT.md",
    "06_qc_evidence/audit/FINDINGS_DISPOSITION_BOARD.md",
    "06_qc_evidence/audit/findings_register.csv",
    "06_qc_evidence/audit/run_records/FDA_REVIEWER_AUDIT_2026-06-20.md",
    "06_qc_evidence/audit/run_records/SUBMISSION_STANDARDS_REMEDIATION.md",
    "06_qc_evidence/audit/section_reviews/SECTION_05_PORTFOLIO_FINALIZATION_AUDIT_2026-08-04.md",
    "06_qc_evidence/conformance/p21_adam_runrecord.md",
    "06_qc_evidence/conformance/p21_adam_summary.json",
    "06_qc_evidence/gates/regulatory_baseline_status.json",
    "07_reviewer_explanation/tools/shiny/",
    "platform/build_release_run_manifest.py",
    "platform/check_regulatory_baseline.py",
    "platform/cibuild.py",
    "platform/pipeline_health.json",
    "platform/stage_p21_adam_inputs.py",
    "requirements-ci.txt",
    "requirements-ci.lock",
    "scripts/rebind_governance_seal.py",
    "scripts/verify_release.py",
    "tests/",
)


def _changed_paths(base: str) -> list[str]:
    output = subprocess.check_output(
        ["git", "diff", "--name-only", f"{base}..HEAD", "--"],
        cwd=ROOT,
        text=True,
    )
    return [line.strip() for line in output.splitlines() if line.strip()]


def _is_allowed(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in ALLOWED_PATHS)


def _health_change_is_prior_reseal_only(base: str) -> bool:
    """Allow health.json only when HEAD carries a valid prior reseal hop.

    A governance reseal necessarily updates pipeline_health.json. A second
    governance commit can therefore compare against a base before that hop and
    legitimately see the health file in the diff. Do not allow arbitrary health
    edits: the clinical timestamp/mode/status must match the base revision, the
    current chain must validate, and the last hop must end at the recorded source
    digest.
    """
    try:
        raw = subprocess.check_output(
            ["git", "show", f"{base}:platform/pipeline_health.json"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        base_health = json.loads(raw)
        current_health = json.loads(HEALTH.read_text(encoding="utf-8"))
    except (subprocess.CalledProcessError, json.JSONDecodeError, OSError):
        return False
    return _health_is_valid_prior_reseal(base_health, current_health)


def _health_is_valid_prior_reseal(base_health: dict, current_health: dict) -> bool:
    """Validate a carried-forward health seal without requiring Git history."""
    for key in ("timestamp", "pipeline_health_status", "sas_execution_mode", "run_scope"):
        if current_health.get(key) != base_health.get(key):
            return False
    chain = current_health.get("governance_reseal_chain")
    if not isinstance(chain, list) or not chain or not all(isinstance(row, dict) for row in chain):
        return False
    expected = str(base_health.get("source_tree_sha256") or "")
    for row in chain:
        if (
            row.get("status") != "PASS"
            or row.get("clinical_run_was_not_reexecuted") is not True
            or row.get("prior_source_tree_sha256") != expected
        ):
            return False
        expected = str(row.get("rebound_source_tree_sha256") or "")
    return bool(expected) and expected == current_health.get("source_tree_sha256")


def _chain_from_base_revision(reseal: dict) -> list[dict]:
    """Recover an older append-only/legacy chain from the reseal's recorded base."""
    base = str(reseal.get("base_revision") or "")
    prior = str(reseal.get("prior_source_tree_sha256") or "")
    if not base or not prior:
        return []
    try:
        raw = subprocess.check_output(
            ["git", "show", f"{base}:platform/pipeline_health.json"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        base_health = json.loads(raw)
    except (subprocess.CalledProcessError, json.JSONDecodeError, OSError):
        return []
    if base_health.get("source_tree_sha256") != prior:
        return []
    chain = base_health.get("governance_reseal_chain")
    if chain is None:
        legacy = base_health.get("governance_only_reseal")
        chain = [legacy] if isinstance(legacy, dict) else []
    if not isinstance(chain, list) or not all(isinstance(row, dict) for row in chain):
        return []
    if chain and chain[-1].get("rebound_source_tree_sha256") != prior:
        return []
    return chain


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_revision", help="last release/run revision before governance-only changes")
    args = parser.parse_args(argv)

    if not HEALTH.is_file():
        raise SystemExit(f"missing {HEALTH.relative_to(ROOT)}")
    health = json.loads(HEALTH.read_text(encoding="utf-8"))
    if health.get("pipeline_health_status") != "GREEN":
        raise SystemExit("refusing to rebind a non-GREEN health snapshot")
    if health.get("sas_execution_mode") not in {"oda", "local"}:
        raise SystemExit("refusing to rebind a non-real-SAS health snapshot")
    changed = _changed_paths(args.base_revision)
    disallowed = [path for path in changed if not _is_allowed(path)]
    if "platform/pipeline_health.json" in changed and not _health_change_is_prior_reseal_only(args.base_revision):
        disallowed.append("platform/pipeline_health.json (not a valid prior governance reseal)")
    if disallowed:
        raise SystemExit("clinical/non-governance paths changed: " + ", ".join(disallowed))

    # Import the exact inventory implementation used by the release seal.
    import sys
    sys.path.insert(0, str(ROOT / "platform"))
    from build_release_run_manifest import _current_source_tree_sha256

    previous = health.get("source_tree_sha256") or ""
    rebound = _current_source_tree_sha256()
    if not previous or previous == rebound:
        raise SystemExit("source-tree rebind was unnecessary or had no prior digest")

    prior_reseal = health.get("governance_only_reseal")
    chain = health.get("governance_reseal_chain")
    if chain is None:
        chain = _chain_from_base_revision(prior_reseal) if isinstance(prior_reseal, dict) else []
        if isinstance(prior_reseal, dict):
            chain.append(prior_reseal)
    elif not isinstance(chain, list) or not all(isinstance(row, dict) for row in chain):
        raise SystemExit("refusing malformed governance_reseal_chain")
    if chain and chain[-1].get("rebound_source_tree_sha256") != previous:
        raise SystemExit("refusing discontinuous governance reseal chain")

    reseal = {
        "status": "PASS",
        "rebound_at": datetime.now(timezone.utc).isoformat(),
        "base_revision": args.base_revision,
        "clinical_run_timestamp": health.get("timestamp"),
        "prior_source_tree_sha256": previous,
        "rebound_source_tree_sha256": rebound,
        "changed_paths": changed,
        "clinical_run_was_not_reexecuted": True,
        "reason": (
            "Pipeline integrity, dependency, executor-validation, regulatory-claim, "
            "external-validator-evidence, reviewer-presentation, and test controls "
            "changed; clinical derivation programs, study parameters, datasets, and "
            "statistical results did not."
        ),
    }
    chain.append(reseal)
    health["source_tree_sha256"] = rebound
    health["governance_only_reseal"] = reseal
    health["governance_reseal_chain"] = chain
    HEALTH.write_text(json.dumps(health, indent=2) + "\n", encoding="utf-8")
    print(f"Rebound {HEALTH.relative_to(ROOT)} from {previous} to {rebound}")
    print("Disclosure: governance-only seal update; SAS/clinical stages were not re-executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
