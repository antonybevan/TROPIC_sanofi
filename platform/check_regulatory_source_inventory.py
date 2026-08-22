#!/usr/bin/env python3
"""Validate the scoped official-source inventory used by TROPIC readiness gates.

This checker validates the local inventory contract only.  It does not assert
that a web page is current, grant legal advice, or replace a center-specific
regulatory review.  Every source is intentionally classified as applicable,
partially applicable, out of scope, watch-only, or awaiting owner confirmation.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import yaml
except ImportError:  # pragma: no cover - exercised by the dependency gate
    yaml = None


KNOWN_STATUSES = {
    "APPLICABLE",
    "PARTIALLY_APPLICABLE",
    "OUT_OF_SCOPE",
    "WATCH_NOT_FINAL",
    "NEEDS_OWNER_CONFIRMATION",
}
REQUIRED_SCOPE_KEYS = {
    "product_class",
    "intended_use",
    "included_surfaces",
    "excluded_surfaces",
    "boundary",
}
REQUIRED_STATUS_BUCKETS = set(KNOWN_STATUSES)


class InventoryError(ValueError):
    """Raised when the source inventory is malformed or unsafe."""


def _load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise InventoryError("PyYAML is not importable; install requirements-ci.txt")
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except OSError as exc:
        raise InventoryError(f"cannot read inventory {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise InventoryError(f"{path} must parse to a YAML mapping")
    return data


def _safe_repo_path(root: Path, raw_path: Any, source_id: str) -> Path:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise InventoryError(f"{source_id}: repo_evidence path must be a non-empty string")
    candidate = Path(raw_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise InventoryError(f"{source_id}: repo_evidence path must stay inside the repository: {raw_path!r}")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise InventoryError(f"{source_id}: repo_evidence path escapes repository: {raw_path!r}") from exc
    return resolved


def evaluate_inventory(inventory_path: str | os.PathLike[str]) -> dict[str, Any]:
    """Return a deterministic, JSON-serialisable inventory assessment."""

    path = Path(inventory_path).resolve()
    root = path.parent.parent if path.parent.name == "config" else path.parent
    data = _load_yaml(path)
    problems: list[str] = []
    warnings: list[str] = []

    if data.get("schema_version") != "1.0":
        problems.append("schema_version must be '1.0'")
    inventory_id = data.get("inventory_id")
    if not isinstance(inventory_id, str) or not inventory_id.strip():
        problems.append("inventory_id must be a non-empty string")
    assessed_on = data.get("assessed_on")
    if not isinstance(assessed_on, str) or not assessed_on.strip():
        problems.append("assessed_on must be a non-empty string")

    scope = data.get("scope")
    if not isinstance(scope, dict):
        problems.append("scope must be a mapping")
        scope = {}
    missing_scope = sorted(REQUIRED_SCOPE_KEYS - set(scope))
    if missing_scope:
        problems.append(f"scope missing keys: {', '.join(missing_scope)}")
    for key in ("included_surfaces", "excluded_surfaces"):
        if key in scope and (
            not isinstance(scope[key], list)
            or not scope[key]
            or not all(isinstance(item, str) and item.strip() for item in scope[key])
        ):
            problems.append(f"scope.{key} must be a non-empty list of strings")

    definitions = data.get("status_definitions")
    if not isinstance(definitions, dict):
        problems.append("status_definitions must be a mapping")
    else:
        missing_definitions = sorted(REQUIRED_STATUS_BUCKETS - set(definitions))
        if missing_definitions:
            problems.append(f"status_definitions missing: {', '.join(missing_definitions)}")

    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        problems.append("sources must be a non-empty list")
        sources = []
    source_ids: set[str] = set()
    counts: Counter[str] = Counter()
    assessed_sources: list[dict[str, Any]] = []
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            problems.append(f"source {index} must be a mapping")
            continue
        source_id = source.get("id")
        label = str(source_id or index)
        if not isinstance(source_id, str) or not source_id.strip():
            problems.append(f"source {index} has no non-empty id")
        elif source_id in source_ids:
            problems.append(f"duplicate source id: {source_id}")
        else:
            source_ids.add(source_id)
        for key in ("authority", "title", "version_or_status", "decision", "owner_action"):
            if not isinstance(source.get(key), str) or not source[key].strip():
                problems.append(f"source {label} missing {key}")
        status = source.get("status")
        if status not in KNOWN_STATUSES:
            problems.append(f"source {label}: unknown status {status!r}")
            status = "OUT_OF_SCOPE"
        counts[status] += 1
        url = source.get("url")
        parsed = urlparse(url) if isinstance(url, str) else None
        if parsed is None or parsed.scheme != "https" or not parsed.netloc:
            problems.append(f"source {label}: url must be an absolute https URL")
        evidence = source.get("repo_evidence", [])
        if not isinstance(evidence, list):
            problems.append(f"source {label}: repo_evidence must be a list")
            evidence = []
        evidence_results: list[dict[str, Any]] = []
        for raw_path in evidence:
            try:
                resolved = _safe_repo_path(root, raw_path, label)
            except InventoryError as exc:
                problems.append(str(exc))
                continue
            exists = resolved.exists()
            evidence_results.append({"path": str(raw_path), "exists": exists})
            if not exists:
                warnings.append(f"{label}: repo_evidence path is not present: {raw_path}")
        if status in {"APPLICABLE", "PARTIALLY_APPLICABLE"} and not evidence_results:
            problems.append(f"{label}: applicable sources must name local evidence")
        assessed_sources.append(
            {
                "id": source_id,
                "authority": source.get("authority"),
                "status": status,
                "url": url,
                "evidence": evidence_results,
            }
        )

    missing_buckets = sorted(REQUIRED_STATUS_BUCKETS - set(counts))
    if missing_buckets:
        problems.append(f"inventory must demonstrate every status bucket: {', '.join(missing_buckets)}")

    return {
        "inventory_id": inventory_id,
        "inventory_path": str(path),
        "source_count": len(sources),
        "counts": dict(sorted(counts.items())),
        "sources": assessed_sources,
        "scope": scope,
        "problems": problems,
        "warnings": warnings,
        "assessment": "MALFORMED" if problems else "PASS",
    }


def _print_report(result: dict[str, Any]) -> None:
    print("=== Scoped Official Regulatory Source Inventory ===")
    print(f"Inventory: {result.get('inventory_id')}")
    print(f"Assessment: {result['assessment']}")
    print(f"Sources: {result.get('source_count', 0)}")
    print(f"Statuses: {result.get('counts', {})}")
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
    parser.add_argument("--inventory", default="config/regulatory_source_inventory.yaml")
    parser.add_argument("--json", action="store_true", help="emit the assessment as JSON")
    args = parser.parse_args(argv)
    try:
        result = evaluate_inventory(args.inventory)
    except InventoryError as exc:
        if args.json:
            print(json.dumps({"assessment": "MALFORMED", "problems": [str(exc)]}, indent=2, sort_keys=True))
        else:
            print(f"Regulatory source inventory error: {exc}")
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        _print_report(result)
    return 0 if not result["problems"] else 1


if __name__ == "__main__":
    sys.exit(main())
