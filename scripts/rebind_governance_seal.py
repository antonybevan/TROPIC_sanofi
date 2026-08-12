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
    "platform/build_release_run_manifest.py",
    "platform/check_regulatory_baseline.py",
    "platform/cibuild.py",
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

    health["source_tree_sha256"] = rebound
    health["governance_only_reseal"] = {
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
            "external-validator-evidence, and test controls changed; clinical derivation "
            "programs, study parameters, datasets, and statistical results did not."
        ),
    }
    HEALTH.write_text(json.dumps(health, indent=2) + "\n", encoding="utf-8")
    print(f"Rebound {HEALTH.relative_to(ROOT)} from {previous} to {rebound}")
    print("Disclosure: governance-only seal update; SAS/clinical stages were not re-executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
