#!/usr/bin/env python3
"""Check the FDA/ICH submission-readiness evidence map.

This is a data-free governance check.  It does not validate a submission, run
SAS/ODA, call FDA/CDISC services, or turn an intentionally bounded simulation
into regulatory evidence.  The profile is an auditable map of local evidence
and owner actions.  Default mode reports the assessment; ``--strict`` is the
go/no-go mode and fails while any BLOCKED or NOT_QUALIFIED control remains.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised by the dependency gate
    yaml = None


KNOWN_STATUSES = {"PASS", "PARTIAL", "BLOCKED", "NOT_APPLICABLE", "NOT_QUALIFIED"}
UNSAFE_RELEASE_CLAIMS = {
    "FDA_READY",
    "FILING_READY",
    "REGULATORY_SUBMISSION_READY",
    "SUBMISSION_READY",
}
REQUIRED_SCOPE_KEYS = {"product_class", "intended_use", "release_claim", "clinical_claim"}


class ReadinessError(ValueError):
    """Raised when a readiness profile is malformed or unsafe."""


def _load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise ReadinessError("PyYAML is not importable; install requirements-ci.txt")
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except OSError as exc:
        raise ReadinessError(f"cannot read profile {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ReadinessError(f"{path} must parse to a YAML mapping")
    return data


def _safe_evidence_path(root: Path, raw_path: Any, control_id: str) -> Path:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ReadinessError(f"{control_id}: evidence path must be a non-empty string")
    candidate = Path(raw_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ReadinessError(f"{control_id}: evidence path must stay inside the repository: {raw_path!r}")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ReadinessError(f"{control_id}: evidence path escapes repository: {raw_path!r}") from exc
    return resolved


def evaluate_profile(profile_path: str | os.PathLike[str]) -> dict[str, Any]:
    """Return a deterministic, JSON-serialisable readiness assessment."""

    path = Path(profile_path).resolve()
    root = path.parent.parent if path.parent.name == "config" else path.parent
    data = _load_yaml(path)
    problems: list[str] = []
    warnings: list[str] = []

    if data.get("schema_version") != "1.0":
        problems.append("schema_version must be '1.0'")
    profile_id = data.get("profile_id")
    if not isinstance(profile_id, str) or not profile_id.strip():
        problems.append("profile_id must be a non-empty string")

    scope = data.get("scope")
    if not isinstance(scope, dict):
        problems.append("scope must be a mapping")
        scope = {}
    missing_scope = sorted(REQUIRED_SCOPE_KEYS - set(scope))
    if missing_scope:
        problems.append(f"scope missing keys: {', '.join(missing_scope)}")
    release_claim = scope.get("release_claim")
    if release_claim in UNSAFE_RELEASE_CLAIMS:
        problems.append(f"unsafe release claim is prohibited: {release_claim}")
    if release_claim != "NOT_FOR_REGULATORY_SUBMISSION":
        warnings.append(f"release claim is {release_claim!r}; verify the claim boundary before sharing")

    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        problems.append("sources must be a non-empty list")
        sources = []
    source_ids: set[str] = set()
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            problems.append(f"source {index} must be a mapping")
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id.strip():
            problems.append(f"source {index} has no non-empty id")
        elif source_id in source_ids:
            problems.append(f"duplicate source id: {source_id}")
        else:
            source_ids.add(source_id)
        for key in ("authority", "title", "version", "checked_on", "url"):
            if not isinstance(source.get(key), str) or not source[key].strip():
                problems.append(f"source {source_id or index} missing {key}")

    controls = data.get("controls")
    if not isinstance(controls, list) or not controls:
        problems.append("controls must be a non-empty list")
        controls = []
    control_ids: set[str] = set()
    assessed: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for index, control in enumerate(controls, start=1):
        if not isinstance(control, dict):
            problems.append(f"control {index} must be a mapping")
            continue
        control_id = control.get("id")
        label = str(control_id or index)
        if not isinstance(control_id, str) or not control_id.strip():
            problems.append(f"control {index} has no non-empty id")
        elif control_id in control_ids:
            problems.append(f"duplicate control id: {control_id}")
        else:
            control_ids.add(control_id)
        status = control.get("status")
        if status not in KNOWN_STATUSES:
            problems.append(f"{label}: unknown status {status!r}")
            status = "BLOCKED"
        counts[status] += 1
        if not isinstance(control.get("domain"), str) or not control["domain"].strip():
            problems.append(f"{label}: domain must be a non-empty string")
        if not isinstance(control.get("expectation"), str) or not control["expectation"].strip():
            problems.append(f"{label}: expectation must be a non-empty string")
        if not isinstance(control.get("owner_action"), str) or not control["owner_action"].strip():
            problems.append(f"{label}: owner_action must be a non-empty string")

        evidence = control.get("evidence", [])
        if not isinstance(evidence, list):
            problems.append(f"{label}: evidence must be a list")
            evidence = []
        evidence_results: list[dict[str, Any]] = []
        for evidence_item in evidence:
            if not isinstance(evidence_item, dict):
                problems.append(f"{label}: each evidence item must be a mapping")
                continue
            raw_path = evidence_item.get("path")
            try:
                resolved = _safe_evidence_path(root, raw_path, label)
            except ReadinessError as exc:
                problems.append(str(exc))
                continue
            exists = resolved.exists()
            required = evidence_item.get("required", True)
            if not isinstance(required, bool):
                problems.append(f"{label}: evidence required must be boolean")
                required = True
            result = {
                "path": str(raw_path),
                "required": required,
                "exists": exists,
            }
            evidence_results.append(result)
            if required and not exists:
                message = f"{label}: missing required evidence {raw_path}"
                if status == "PASS":
                    problems.append(message)
                else:
                    warnings.append(message)
        if status == "PASS" and not evidence_results:
            problems.append(f"{label}: PASS controls must name evidence")
        assessed.append(
            {
                "id": control_id,
                "domain": control.get("domain"),
                "status": status,
                "expectation": control.get("expectation"),
                "owner_action": control.get("owner_action"),
                "evidence": evidence_results,
            }
        )

    blockers = [
        item["id"]
        for item in assessed
        if item["status"] in {"BLOCKED", "NOT_QUALIFIED"}
    ]
    return {
        "profile_id": profile_id,
        "profile_path": str(path),
        "scope": scope,
        "source_count": len(sources),
        "controls": assessed,
        "counts": dict(sorted(counts.items())),
        "blockers": blockers,
        "problems": problems,
        "warnings": warnings,
        "assessment": "MALFORMED" if problems else ("BLOCKED" if blockers else "PASS"),
    }


def _print_report(result: dict[str, Any]) -> None:
    print("=== FDA/ICH Submission Readiness Profile ===")
    print(f"Profile: {result.get('profile_id')}")
    print(f"Assessment: {result['assessment']}")
    print(f"Scope: {result.get('scope', {}).get('release_claim', 'MISSING')}")
    print(f"Controls: {result.get('counts', {})}")
    if result["blockers"]:
        print("Blockers:")
        for control_id in result["blockers"]:
            print(f"  - {control_id}")
    if result["warnings"]:
        print("Warnings:")
        for warning in result["warnings"]:
            print(f"  - {warning}")
    if result["problems"]:
        print("Failures:")
        for problem in result["problems"]:
            print(f"  - {problem}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="config/fda_readiness_profile.yaml")
    parser.add_argument("--strict", action="store_true", help="fail on malformed profiles or intentional blockers")
    parser.add_argument("--json", action="store_true", help="emit the assessment as JSON")
    args = parser.parse_args(argv)
    try:
        result = evaluate_profile(args.profile)
    except ReadinessError as exc:
        if args.json:
            print(json.dumps({"assessment": "MALFORMED", "problems": [str(exc)]}, indent=2, sort_keys=True))
        else:
            print(f"Readiness profile error: {exc}")
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        _print_report(result)
    if result["problems"]:
        return 1
    if args.strict and result["blockers"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
