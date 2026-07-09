#!/usr/bin/env python3
"""Evaluate CTQ/estimand-to-artifact traceability."""

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


TFL_INDEX = "06_telemetry/tfl_output_index/tfl_output_index.csv"
ARS_ARD = "12_ars/tropic_ard.csv"
VALIDATION_STRATEGY = "validation_strategy.yaml"


def _load_yaml(path):
    if yaml is None:
        raise RuntimeError("PyYAML is not importable; install pyyaml to build CTQ report")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} did not parse to a YAML mapping")
    return data


def _read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


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


def build_ctq_report(root, register_path, out_dir, report_path):
    register = _load_yaml(os.path.join(root, register_path))
    validation = _load_yaml(os.path.join(root, VALIDATION_STRATEGY))
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    os.makedirs(os.path.join(root, out_dir), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.join(root, report_path)), exist_ok=True)

    tfl_ids = {r.get("output_id") for r in _read_csv(os.path.join(root, TFL_INDEX))}
    ars_ids = {r.get("analysisId") for r in _read_csv(os.path.join(root, ARS_ARD))}
    validation_ids = {a.get("id") for a in validation.get("artifacts", [])}

    rows = []
    check_rows = []
    payload_items = []
    for item in register.get("ctq_factors", []):
        failures = []
        warnings = []

        for field in ["population", "variable", "intercurrent_events", "summary_measure"]:
            if not item.get("estimand", {}).get(field):
                failures.append(f"estimand.{field} missing")

        for output_id in item.get("outputs", []):
            if output_id not in tfl_ids:
                failures.append(f"output {output_id} missing from TFL index")
        for analysis_id in item.get("ars_analyses", []):
            if analysis_id not in ars_ids:
                failures.append(f"ARS analysis {analysis_id} missing")
        for validation_id in item.get("validation_artifacts", []):
            if validation_id not in validation_ids:
                failures.append(f"validation artifact {validation_id} missing from validation_strategy.yaml")
        for guide in item.get("reviewer_guides", []):
            if not os.path.exists(os.path.join(root, guide)):
                failures.append(f"reviewer guide {guide} missing")

        if item.get("risk_tier") in {"critical", "high"} and not item.get("validation_artifacts"):
            failures.append("high/critical CTQ has no validation artifacts")
        if item.get("risk_tier") == "critical" and not item.get("specification_refs"):
            failures.append("critical CTQ has no specification reference")
        if item.get("domain") in {"efficacy", "safety"} and not item.get("outputs"):
            warnings.append("clinical CTQ has no direct TFL output")
        if item.get("domain") == "efficacy" and item.get("risk_tier") == "critical" and not item.get("ars_analyses"):
            warnings.append("critical efficacy CTQ has no ARS analysis")

        status = "FAIL" if failures else ("WARNING" if warnings else "PASS")
        rows.append([
            item.get("id", ""),
            item.get("domain", ""),
            item.get("risk_tier", ""),
            status,
            ", ".join(item.get("adam_datasets", [])),
            ", ".join(item.get("outputs", [])) or "n/a",
            ", ".join(item.get("validation_artifacts", [])),
        ])
        for message in failures:
            check_rows.append([item.get("id", ""), "FAIL", message])
        for message in warnings:
            check_rows.append([item.get("id", ""), "WARNING", message])
        if not failures and not warnings:
            check_rows.append([item.get("id", ""), "PASS", "CTQ traceability complete"])
        payload_items.append({
            "id": item.get("id", ""),
            "domain": item.get("domain", ""),
            "risk_tier": item.get("risk_tier", ""),
            "status": status,
            "clinical_question": item.get("clinical_question", ""),
            "failures": failures,
            "warnings": warnings,
        })

    fail_count = sum(1 for r in rows if r[3] == "FAIL")
    warning_count = sum(1 for r in rows if r[3] == "WARNING")
    pass_count = sum(1 for r in rows if r[3] == "PASS")
    overall = "FAIL" if fail_count else ("WARNING" if warning_count else "PASS")
    status_payload = {
        "status": overall,
        "generated_at": generated_at,
        "ctq_factors": len(rows),
        "pass": pass_count,
        "warning": warning_count,
        "fail": fail_count,
        "items": payload_items,
    }

    status_path = os.path.join(root, out_dir, "ctq_traceability_status.json")
    csv_path = os.path.join(root, out_dir, "ctq_traceability_checks.csv")
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(status_payload, f, indent=2)
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ctq_id", "status", "message"])
        writer.writerows(check_rows)

    lines = [
        "# TROPIC CTQ and Estimand Traceability Report",
        "",
        f"Generated: {generated_at}",
        "",
        "> This report evaluates `ctq_traceability.yaml`, linking clinical questions "
        "to estimand-style attributes, ADaM inputs, TFL/ARS outputs, reviewer guides, "
        "and validation-strategy artifacts.",
        "",
        "## Verdict",
        "",
        _table(
            ["Item", "Value"],
            [
                ["Overall status", overall],
                ["CTQ factors", len(rows)],
                ["Pass", pass_count],
                ["Warning", warning_count],
                ["Fail", fail_count],
            ],
        ),
        "",
        "## CTQ Traceability Matrix",
        "",
        _table(
            ["CTQ", "Domain", "Risk", "Status", "ADaM datasets", "Outputs", "Validation artifacts"],
            rows,
        ),
        "",
        "## Findings",
        "",
        _table(["CTQ", "Status", "Message"], check_rows),
        "",
        "## Machine-Readable Outputs",
        "",
        "- `06_telemetry/ctq_traceability/ctq_traceability_status.json`",
        "- `06_telemetry/ctq_traceability/ctq_traceability_checks.csv`",
        "",
    ]
    with open(os.path.join(root, report_path), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return status_payload


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build CTQ traceability report")
    parser.add_argument("--register", default="ctq_traceability.yaml")
    parser.add_argument("--out-dir", default="06_telemetry/ctq_traceability")
    parser.add_argument("--report", default="docs/CTQ_TRACEABILITY_REPORT.md")
    args = parser.parse_args(argv)
    status = build_ctq_report(os.getcwd(), args.register, args.out_dir, args.report)
    print(f"CTQ traceability status: {status['status']}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
