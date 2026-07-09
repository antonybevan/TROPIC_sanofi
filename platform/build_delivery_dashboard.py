#!/usr/bin/env python3
"""Build a reviewer-facing dashboard from the delivery architecture controls."""

import argparse
import glob
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    yaml = None


def _load_yaml(path):
    if yaml is None:
        raise RuntimeError("PyYAML is not importable; install pyyaml to build the dashboard")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} did not parse to a YAML mapping")
    return data


def _rel(path, root):
    return os.path.relpath(path, root)


def _artifact_matches(root, artifact):
    if "path" in artifact:
        path = os.path.join(root, artifact["path"])
        return [path] if os.path.exists(path) else []
    if "glob" in artifact:
        return glob.glob(os.path.join(root, artifact["glob"]), recursive=True)
    return []


def _artifact_label(artifact):
    return artifact.get("path") or artifact.get("glob") or "<undefined>"


def _artifact_presence(root, artifact):
    matches = _artifact_matches(root, artifact)
    if matches:
        return "present", len(matches)
    return "not present", 0


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


def _layer_summary(root, layers):
    rows = []
    details = {}
    for layer_name, layer in layers.items():
        artifacts = layer.get("artifacts", [])
        counts = Counter()
        missing_required = []
        not_present_nonrequired = []
        for artifact in artifacts:
            status = artifact.get("status", "required")
            if status == "external":
                presence, match_count = "declared/excluded", "n/a"
            else:
                presence, match_count = _artifact_presence(root, artifact)
            counts[(status, presence)] += 1
            if status == "required" and presence != "present":
                missing_required.append(_artifact_label(artifact))
            elif status != "required" and presence != "present":
                not_present_nonrequired.append(f"{status}: {_artifact_label(artifact)}")
        rows.append([
            layer_name,
            layer.get("objective", ""),
            sum(v for (status, presence), v in counts.items() if status == "required" and presence == "present"),
            len(missing_required),
            sum(v for (status, presence), v in counts.items() if status != "required" and presence == "present"),
            len(not_present_nonrequired),
        ])
        details[layer_name] = {
            "missing_required": missing_required,
            "not_present_nonrequired": not_present_nonrequired,
        }
    return rows, details


def _workstream_rows(workstreams):
    rows = []
    for ws_id, workstream in workstreams.items():
        rows.append([
            ws_id,
            workstream.get("function", ""),
            ", ".join(workstream.get("owns_gates", [])),
            ", ".join(workstream.get("consumes_layers", [])),
            ", ".join(workstream.get("produces_layers", [])),
        ])
    return rows


def _gate_rows(gates):
    rows = []
    for gate_id, gate in gates.items():
        rows.append([
            gate_id,
            gate.get("name", ""),
            gate.get("layer", ""),
            gate.get("description", ""),
        ])
    return rows


def _required_artifact_rows(root, workstreams):
    rows = []
    for ws_id, workstream in workstreams.items():
        for artifact in workstream.get("required_artifacts", []):
            path = os.path.join(root, artifact)
            rows.append([
                ws_id,
                artifact,
                "present" if os.path.exists(path) else "missing",
            ])
    return rows


def _nonrequired_rows(root, layers):
    rows = []
    for layer_name, layer in layers.items():
        for artifact in layer.get("artifacts", []):
            status = artifact.get("status", "required")
            if status == "required":
                continue
            if status == "external":
                presence, match_count = "declared/excluded", "n/a"
            else:
                presence, match_count = _artifact_presence(root, artifact)
            rows.append([
                layer_name,
                status,
                _artifact_label(artifact),
                presence,
                match_count,
                artifact.get("role", ""),
            ])
    return rows


def build_dashboard(root, evidence, delivery):
    layers = evidence.get("layers", {})
    gates = delivery.get("gates", {})
    workstreams = delivery.get("workstreams", {})
    layer_rows, layer_details = _layer_summary(root, layers)
    required_rows = _required_artifact_rows(root, workstreams)
    missing_required = [row for row in required_rows if row[2] == "missing"]

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# TROPIC Delivery Evidence Dashboard",
        "",
        f"Generated: {generated_at}",
        "",
        "> This dashboard is generated from `config/evidence_layers.yaml` and "
        "`config/delivery_workstreams.yaml`. It is an architecture and evidence-control "
        "view, not a claim that the package is submission-ready.",
        "",
        "## Readiness Snapshot",
        "",
        _table(
            ["Check", "Status"],
            [
                ["Required workstream artifacts", "PASS" if not missing_required else "FAIL"],
                ["Evidence layers", len(layers)],
                ["Delivery workstreams", len(workstreams)],
                ["Handoff gates", len(gates)],
            ],
        ),
        "",
        "## Evidence Layers",
        "",
        _table(
            [
                "Layer",
                "Objective",
                "Required present",
                "Required missing",
                "Other present",
                "Other not present",
            ],
            layer_rows,
        ),
        "",
        "## Delivery Workstreams",
        "",
        _table(
            ["Workstream", "Function", "Owns gates", "Consumes", "Produces"],
            _workstream_rows(workstreams),
        ),
        "",
        "## Handoff Gates",
        "",
        _table(
            ["Gate", "Name", "Evidence layer", "Description"],
            _gate_rows(gates),
        ),
        "",
        "## Workstream Required Artifacts",
        "",
        _table(
            ["Workstream", "Artifact", "Presence"],
            required_rows,
        ),
        "",
        "## Generated, External, Optional, and Planned Artifacts",
        "",
        _table(
            ["Layer", "Status", "Artifact", "Presence", "Matches", "Role"],
            _nonrequired_rows(root, layers),
        ),
        "",
        "## Missing Required Artifacts",
        "",
    ]
    if missing_required:
        lines.append(_table(["Workstream", "Artifact"], [[r[0], r[1]] for r in missing_required]))
    else:
        lines.append("No required workstream artifacts are missing.")

    layer_missing = []
    for layer_name, detail in layer_details.items():
        for artifact in detail["missing_required"]:
            layer_missing.append([layer_name, artifact])
    lines.extend(["", "## Missing Required Evidence-Layer Artifacts", ""])
    if layer_missing:
        lines.append(_table(["Layer", "Artifact"], layer_missing))
    else:
        lines.append("No required evidence-layer artifacts are missing.")

    lines.extend([
        "",
        "## Interpretation Rules",
        "",
        "- `required` artifacts must exist for the architecture check to pass.",
        "- `generated` artifacts may be absent in a clean clone and should be produced by the pipeline.",
        "- `external` artifacts are intentionally excluded from git, usually because they are patient data, governed inputs, or credentials.",
        "- `optional` artifacts are useful but not required for the architecture check.",
        "- `planned` artifacts document target-state work that is not yet implemented.",
        "",
    ])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build TROPIC delivery evidence dashboard")
    parser.add_argument("--evidence", default="config/evidence_layers.yaml")
    parser.add_argument("--delivery", default="config/delivery_workstreams.yaml")
    parser.add_argument("--output", default="docs/DELIVERY_EVIDENCE_DASHBOARD.md")
    args = parser.parse_args(argv)

    root = os.getcwd()
    evidence_path = os.path.abspath(args.evidence)
    delivery_path = os.path.abspath(args.delivery)
    output_path = os.path.abspath(args.output)

    evidence = _load_yaml(evidence_path)
    delivery = _load_yaml(delivery_path)
    dashboard = build_dashboard(root, evidence, delivery)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(dashboard)

    print(f"Wrote {_rel(output_path, root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
