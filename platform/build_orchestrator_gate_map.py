#!/usr/bin/env python3
"""Map the manifest-driven pipeline DAG to delivery operating-model gates."""

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    yaml = None


STAGE_GATE_RULES = [
    ("ADaM Spec Label/Order Artifacts", ["G03", "G06"], "spec-derived metadata export contract"),
    ("Real SDTM Staging Ingest", ["G01"], "source intake/staging"),
    ("R SDTM Validation", ["G01", "G06"], "source structural validation"),
    ("R ADSL Validation", ["G04", "G06"], "ADaM validation track"),
    ("R ADEX Validation", ["G04", "G06"], "ADaM validation track"),
    ("R ADCM Validation", ["G04", "G06"], "ADaM validation track"),
    ("R ADAE Validation", ["G04", "G06"], "ADaM validation track"),
    ("R ADLB Validation", ["G04", "G06"], "ADaM validation track"),
    ("R ADRS Validation", ["G04", "G06"], "ADaM validation track"),
    ("R ADTTE Validation", ["G04", "G06"], "ADaM validation track"),
    ("R BIMO Validation", ["G04", "G06"], "BIMO validation track"),
    ("SAS Production (ODA/Real/Simulated)", ["G04"], "production analysis dataset build"),
    ("Cross-Language Audit Reconcile", ["G04", "G06"], "dataset-level reconciliation gate"),
    ("Admiral ADSL Re-derivation", ["G04", "G06"], "third-engine T1 ADSL re-derivation (admiral)"),
    ("Admiral ADTTE Re-derivation (OS/PFS)", ["G04", "G06"], "third-engine T1 OS/PFS re-derivation (admiral)"),
    ("Admiral Core Reconciliation", ["G04", "G06"], "third-engine scoped core reconciliation gate"),
    ("Synthetic Comparator Bridge Parity", ["G05", "G06"], "synthetic comparator bridge control before TFLs"),
    ("Efficacy & Safety TFL Suite Compilation", ["G05"], "TFL output generation gate"),
    ("Numerical Results Reconciliation (SAS vs R)", ["G06"], "results-level reconciliation gate"),
    ("Forest-HR Reconciliation (SAS vs R)", ["G06"], "figure-driving statistic reconciliation"),
    ("ADaM Spec to Define Conformance", ["G03", "G06"], "metadata spec-to-define conformance"),
    ("ADaM Spec to Data Conformance", ["G03", "G04", "G06"], "metadata spec-to-data conformance"),
    ("Dataset-JSON Export (v1.1)", ["G04", "G08"], "dataset exchange layer"),
    ("Analysis Results Standard (ARS v1.0)", ["G05", "G08"], "analysis results metadata/export layer"),
    ("USDM Study Definition (v3.0)", ["G03", "G08"], "study definition metadata/export layer"),
    ("eCTD Final Package", ["G08"], "Module 5 package assembly"),
    ("eCTD Backbone + STF (sequence 0000)", ["G08"], "eCTD backbone and STF assembly"),
    ("Materialize eCTD Sequence", ["G08", "G09"], "sequence materialization and checksum verification"),
    ("Log Cleanliness Gate", ["G06", "G09"], "execution-log scan for unapproved warnings/errors and reviewed exception caps"),
    ("Release Run Manifest Binding", ["G09"], "current run hash binding and QC verdict seal"),
]


def _load_yaml(path):
    if yaml is None:
        raise RuntimeError("PyYAML is not importable; install pyyaml to build the gate map")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} did not parse to a YAML mapping")
    return data


def _stage_rows(manifest):
    stages = []
    for s in (manifest.get("infrastructure_stages") or {}).get("pre", []):
        stages.append({
            "name": s["name"],
            "script": s.get("script", ""),
            "runner": s.get("runner", "logrx"),
            "parallel": False,
            "manifest_gated": bool(s.get("gated")),
            "source": "manifest.infrastructure_stages.pre",
        })
    for d in manifest.get("datasets", []):
        name = d.get("val_stage", f"R {d['name'].upper()} Validation")
        stages.append({
            "name": name,
            "script": f"04_analysis_datasets/programs/r/{d['val']}",
            "runner": "logrx",
            "parallel": "parallel_group" in d,
            "manifest_gated": False,
            "source": f"manifest.datasets.{d['name']}",
        })
    stages.append({
        "name": "SAS Production (ODA/Real/Simulated)",
        "script": "SIMULATE sentinel / SAS production resolver",
        "runner": "sas_mode",
        "parallel": False,
        "manifest_gated": False,
        "source": "cibuild.py sentinel",
    })
    for s in (manifest.get("infrastructure_stages") or {}).get("post", []):
        stages.append({
            "name": s["name"],
            "script": s.get("script", ""),
            "runner": s.get("runner", "logrx"),
            "parallel": False,
            "manifest_gated": bool(s.get("gated")),
            "source": "manifest.infrastructure_stages.post",
        })
    for i, stage in enumerate(stages, start=1):
        stage["stage_id"] = i
    return stages


def _mapping_for(stage_name):
    for name, gates, rationale in STAGE_GATE_RULES:
        if stage_name == name:
            return gates, rationale
    return [], "no mapping rule"


def _md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        clean = [str(v).replace("|", "\\|").replace("\n", " ") for v in row]
        lines.append("| " + " | ".join(clean) + " |")
    return "\n".join(lines)


def build_gate_map(manifest_path, delivery_path, out_dir, report_path):
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    manifest = _load_yaml(manifest_path)
    delivery = _load_yaml(delivery_path)
    gates = delivery.get("gates", {})
    stages = _stage_rows(manifest)

    rows = []
    gate_to_stages = defaultdict(list)
    unmapped_stages = []
    for stage in stages:
        mapped_gates, rationale = _mapping_for(stage["name"])
        if not mapped_gates:
            unmapped_stages.append(stage["name"])
        for gate in mapped_gates:
            gate_to_stages[gate].append(stage["name"])
        rows.append({
            "stage_id": stage["stage_id"],
            "stage_name": stage["name"],
            "script": stage["script"],
            "runner": stage["runner"],
            "parallel": stage["parallel"],
            "manifest_gated": stage["manifest_gated"],
            "delivery_gates": ",".join(mapped_gates),
            "mapping_rationale": rationale,
            "source": stage["source"],
        })

    uncovered_gates = [gate for gate in gates if gate not in gate_to_stages]
    status_value = "pass"
    if unmapped_stages:
        status_value = "fail"
    elif uncovered_gates:
        status_value = "warning"

    status = {
        "status": status_value,
        "generated_at": generated_at,
        "manifest": manifest_path,
        "delivery_model": delivery_path,
        "stages": len(stages),
        "mapped_stages": len(stages) - len(unmapped_stages),
        "unmapped_stages": unmapped_stages,
        "gates": len(gates),
        "stage_covered_gates": sorted(gate_to_stages),
        "not_currently_stage_gated": uncovered_gates,
    }

    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(os.path.join(out_dir, "orchestrator_gate_map.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "stage_id", "stage_name", "script", "runner", "parallel",
                "manifest_gated", "delivery_gates", "mapping_rationale", "source",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    with open(os.path.join(out_dir, "orchestrator_gate_map_status.json"), "w", encoding="utf-8") as f:
        payload = dict(status)
        payload["stage_rows"] = rows
        json.dump(payload, f, indent=2)

    stage_table = [
        [
            r["stage_id"], r["stage_name"], r["script"], r["runner"],
            "yes" if r["parallel"] else "no",
            "yes" if r["manifest_gated"] else "no",
            r["delivery_gates"] or "UNMAPPED",
            r["mapping_rationale"],
        ]
        for r in rows
    ]
    gate_table = [
        [
            gate_id,
            gate.get("name", ""),
            gate.get("layer", ""),
            ", ".join(gate_to_stages.get(gate_id, [])) or "not currently stage-gated",
        ]
        for gate_id, gate in gates.items()
    ]

    lines = [
        "# TROPIC Orchestrator Gate Map",
        "",
        f"Generated: {generated_at}",
        "",
        "> Maps the actual `config/study_manifest.yaml` pipeline stages to the professional delivery gates in `config/delivery_workstreams.yaml`. "
        "This report shows what the runtime DAG controls directly and which delivery gates remain document/control-report governed.",
        "",
        "## Summary",
        "",
        _md_table(
            ["Item", "Value"],
            [
                ["Status", status_value],
                ["Manifest stages", len(stages)],
                ["Mapped stages", len(stages) - len(unmapped_stages)],
                ["Unmapped stages", len(unmapped_stages)],
                ["Delivery gates", len(gates)],
                ["Stage-covered gates", ", ".join(sorted(gate_to_stages))],
                ["Not currently stage-gated", ", ".join(uncovered_gates) if uncovered_gates else "none"],
            ],
        ),
        "",
        "## Stage-to-Gate Map",
        "",
        _md_table(
            ["Stage", "Name", "Script", "Runner", "Parallel", "Manifest gated", "Delivery gates", "Rationale"],
            stage_table,
        ),
        "",
        "## Gate Coverage",
        "",
        _md_table(["Gate", "Name", "Layer", "Runtime stage coverage"], gate_table),
        "",
        "## Interpretation",
        "",
        "- `Manifest gated` means `cibuild.py` has name-keyed post-stage gate logic or the stage exits non-zero on failure.",
        "- `Delivery gates` are the professional operating-model gates the stage supports.",
        "- `Not currently stage-gated` means the gate is controlled by documentation or generated evidence reports today, not by a first-class runtime DAG stage.",
        "",
        "## Machine-Readable Outputs",
        "",
        "- `platform/orchestrator_gate_map/orchestrator_gate_map_status.json`",
        "- `platform/orchestrator_gate_map/orchestrator_gate_map.csv`",
        "",
    ]
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return status


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build orchestrator-to-delivery-gate map")
    parser.add_argument("--manifest", default="config/study_manifest.yaml")
    parser.add_argument("--delivery", default="config/delivery_workstreams.yaml")
    parser.add_argument("--out-dir", default="platform/orchestrator_gate_map")
    parser.add_argument("--report", default="docs/ORCHESTRATOR_GATE_MAP.md")
    args = parser.parse_args(argv)
    status = build_gate_map(args.manifest, args.delivery, args.out_dir, args.report)
    print(f"Orchestrator gate map status: {status['status']}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
