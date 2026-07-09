#!/usr/bin/env python3
"""Evaluate the machine-readable risk-based validation strategy."""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    yaml = None


def _load_yaml(path):
    if yaml is None:
        raise RuntimeError("PyYAML is not importable; install pyyaml to build validation strategy report")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} did not parse to a YAML mapping")
    return data


def _load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _field(data, dotted):
    def walk(cur, parts):
        if not parts:
            return cur
        if not isinstance(cur, dict):
            return None
        for end in range(len(parts), 0, -1):
            key = ".".join(parts[:end])
            if key in cur:
                return walk(cur[key], parts[end:])
        return None

    return walk(data, dotted.split("."))


def _check_op(actual, op, expected):
    if op == "equals":
        return actual == expected
    if op == "not_equals":
        return actual != expected
    if op == "in":
        return actual in expected
    if op == "exists":
        return actual is not None
    raise RuntimeError(f"Unsupported check op: {op}")


def _md_escape(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def _table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_md_escape(cell) for cell in row) + " |")
    return "\n".join(lines)


def _parse_ts(value):
    if not value:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts
    except ValueError:
        return None


def _evaluate_check(root, check_id, check):
    path = check.get("file")
    full_path = os.path.join(root, path)
    data = _load_json(full_path)
    if data is None:
        return {
            "check_id": check_id,
            "status": "FAIL",
            "evidence": check.get("evidence", ""),
            "file": path,
            "field": check.get("field", ""),
            "actual": "missing file",
            "expected": check.get("value", ""),
        }
    actual = _field(data, check.get("field", ""))
    expected = check.get("value")
    ok = _check_op(actual, check.get("op", "equals"), expected)

    # Optional freshness: reject historical side evidence (e.g. June admiral on a July run).
    # In-DAG evidence is written mid-run; pipeline_health is stamped at the end, so mtime
    # predating health.timestamp is normal for orchestrated stages. Prefer pipeline_stage
    # PASS in health.stages, else fall back to mtime vs reference timestamp.
    stale_note = None
    freshness = check.get("require_not_stale_vs") or {}
    if ok and freshness:
        ref_path = os.path.join(root, freshness.get("file", ""))
        ref_data = _load_json(ref_path) or {}
        ref_ts = _parse_ts(_field(ref_data, freshness.get("field", "timestamp")))
        stage_name = freshness.get("pipeline_stage")
        stage_status = (ref_data.get("stages") or {}).get(stage_name) if stage_name else None
        try:
            evidence_mtime = datetime.fromtimestamp(
                os.path.getmtime(full_path), tz=timezone.utc
            )
        except OSError:
            evidence_mtime = None
        if stage_name and stage_status == "PASS":
            # Same-run orchestrated evidence is current even if written before final health stamp.
            pass
        elif ref_ts is None or evidence_mtime is None:
            ok = False
            stale_note = "freshness reference or evidence mtime unavailable"
            actual = f"{actual} ({stale_note})"
        elif evidence_mtime < ref_ts:
            ok = False
            stale_note = (
                f"evidence mtime {evidence_mtime.isoformat()} predates "
                f"{freshness.get('file')} {freshness.get('field')}={ref_ts.isoformat()}"
            )
            actual = f"{actual} (STALE: {stale_note})"

    return {
        "check_id": check_id,
        "status": "PASS" if ok else "FAIL",
        "evidence": check.get("evidence", ""),
        "file": path,
        "field": check.get("field", ""),
        "actual": actual,
        "expected": expected,
        "freshness_failure": stale_note,
    }


def _evaluate_file(root, rel_path):
    return {
        "check_id": f"file:{rel_path}",
        "status": "PASS" if os.path.exists(os.path.join(root, rel_path)) else "FAIL",
        "evidence": "Required reviewer/documentation artifact is present.",
        "file": rel_path,
        "field": "",
        "actual": "present" if os.path.exists(os.path.join(root, rel_path)) else "missing",
        "expected": "present",
    }


def build_validation_strategy_report(root, strategy_path, out_dir, report_path):
    strategy = _load_yaml(os.path.join(root, strategy_path))
    checks = strategy.get("checks", {})
    artifacts = strategy.get("artifacts", [])
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    os.makedirs(os.path.join(root, out_dir), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.join(root, report_path)), exist_ok=True)

    artifact_rows = []
    check_rows = []
    artifact_payload = []
    for artifact in artifacts:
        evaluations = []
        for check_id in artifact.get("required_checks", []):
            if check_id not in checks:
                evaluations.append({
                    "check_id": check_id,
                    "status": "FAIL",
                    "evidence": "Check is referenced but not defined.",
                    "file": "",
                    "field": "",
                    "actual": "undefined",
                    "expected": "defined",
                })
            else:
                evaluations.append(_evaluate_check(root, check_id, checks[check_id]))
        for rel_path in artifact.get("required_files", []):
            evaluations.append(_evaluate_file(root, rel_path))

        failed = [e for e in evaluations if e["status"] != "PASS"]
        status = "PASS" if not failed else "BLOCKED"
        artifact_rows.append([
            artifact.get("id", ""),
            artifact.get("risk_tier", ""),
            artifact.get("gate", ""),
            artifact.get("owner", ""),
            status,
            len(evaluations) - len(failed),
            len(failed),
            artifact.get("decision_impact", ""),
        ])
        for evaluation in evaluations:
            check_rows.append([
                artifact.get("id", ""),
                evaluation["check_id"],
                evaluation["status"],
                evaluation["file"],
                evaluation["field"],
                evaluation["actual"],
                evaluation["expected"],
                evaluation["evidence"],
            ])
        artifact_payload.append({
            "id": artifact.get("id", ""),
            "name": artifact.get("name", ""),
            "risk_tier": artifact.get("risk_tier", ""),
            "gate": artifact.get("gate", ""),
            "owner": artifact.get("owner", ""),
            "status": status,
            "decision_impact": artifact.get("decision_impact", ""),
            "traceability": artifact.get("traceability", ""),
            "checks": evaluations,
        })

    blocker_count = sum(1 for row in artifact_rows if row[4] == "BLOCKED")
    pass_count = len(artifact_rows) - blocker_count
    overall = "BLOCKED" if blocker_count else "PASS"
    status_payload = {
        "status": overall,
        "generated_at": generated_at,
        "artifacts": len(artifact_rows),
        "pass": pass_count,
        "blocked": blocker_count,
        "strategy": strategy_path,
        "items": artifact_payload,
    }

    status_path = os.path.join(root, out_dir, "validation_strategy_status.json")
    csv_path = os.path.join(root, out_dir, "validation_strategy_checks.csv")
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(status_payload, f, indent=2)
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["artifact", "check", "status", "file", "field", "actual", "expected", "evidence"])
        writer.writerows(check_rows)

    lines = [
        "# TROPIC Validation Strategy Control Report",
        "",
        f"Generated: {generated_at}",
        "",
        "> This report evaluates `validation_strategy.yaml`: the machine-readable "
        "risk-based, traceability-driven, specification-controlled validation strategy. "
        "A BLOCKED status means the current evidence set cannot support a release-ready claim.",
        "",
        "## Verdict",
        "",
        _table(
            ["Item", "Value"],
            [
                ["Overall status", overall],
                ["Artifacts assessed", len(artifact_rows)],
                ["Pass", pass_count],
                ["Blocked", blocker_count],
            ],
        ),
        "",
        "## Artifact Strategy Status",
        "",
        _table(
            ["Artifact", "Risk", "Gate", "Owner", "Status", "Checks pass", "Checks fail", "Decision impact"],
            artifact_rows,
        ),
        "",
        "## Evidence Checks",
        "",
        _table(
            ["Artifact", "Check", "Status", "File", "Field", "Actual", "Expected", "Evidence"],
            check_rows,
        ),
        "",
        "## Machine-Readable Outputs",
        "",
        "- `06_telemetry/validation_strategy/validation_strategy_status.json`",
        "- `06_telemetry/validation_strategy/validation_strategy_checks.csv`",
        "",
    ]
    with open(os.path.join(root, report_path), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return status_payload


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build validation strategy control report")
    parser.add_argument("--strategy", default="validation_strategy.yaml")
    parser.add_argument("--out-dir", default="06_telemetry/validation_strategy")
    parser.add_argument("--report", default="docs/VALIDATION_STRATEGY_CONTROL_REPORT.md")
    args = parser.parse_args(argv)
    root = os.getcwd()
    status = build_validation_strategy_report(root, args.strategy, args.out_dir, args.report)
    print(f"Validation strategy status: {status['status']}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
