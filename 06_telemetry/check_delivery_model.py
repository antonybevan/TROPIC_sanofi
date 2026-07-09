#!/usr/bin/env python3
"""Validate the machine-readable biometrics delivery operating model."""

import argparse
import os
import sys

try:
    import yaml
except ImportError:
    yaml = None


def _load_yaml(path):
    if yaml is None:
        raise RuntimeError("PyYAML is not importable; install pyyaml to read delivery YAML files")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} did not parse to a YAML mapping")
    return data


def _artifact_exists(root, rel_path):
    return os.path.exists(os.path.join(root, rel_path))


def check_delivery_model(model_path, evidence_path):
    root = os.path.abspath(os.path.dirname(model_path) or ".")
    model = _load_yaml(model_path)
    evidence = _load_yaml(evidence_path)

    problems = []
    warnings = []

    evidence_layers = set((evidence.get("layers") or {}).keys())
    evidence_chain = set(evidence.get("evidence_chain") or [])
    allowed_layers = evidence_layers | evidence_chain

    gates = model.get("gates")
    workstreams = model.get("workstreams")
    if not isinstance(gates, dict) or not gates:
        problems.append("delivery model must declare non-empty gates")
        gates = {}
    if not isinstance(workstreams, dict) or not workstreams:
        problems.append("delivery model must declare non-empty workstreams")
        workstreams = {}

    for gate_id, gate in gates.items():
        if not isinstance(gate, dict):
            problems.append(f"gate {gate_id} must be a mapping")
            continue
        layer = gate.get("layer")
        if layer not in allowed_layers:
            problems.append(f"gate {gate_id} references unknown evidence layer {layer!r}")
        if not gate.get("name"):
            problems.append(f"gate {gate_id} is missing name")

    owned_gates = set()
    for ws_id, workstream in workstreams.items():
        if not isinstance(workstream, dict):
            problems.append(f"workstream {ws_id} must be a mapping")
            continue

        owns = workstream.get("owns_gates") or []
        consumes = workstream.get("consumes_layers") or []
        produces = workstream.get("produces_layers") or []
        required = workstream.get("required_artifacts") or []

        if not owns:
            problems.append(f"workstream {ws_id} owns no gates")
        for gate_id in owns:
            if gate_id not in gates:
                problems.append(f"workstream {ws_id} references unknown gate {gate_id}")
            owned_gates.add(gate_id)

        for layer in list(consumes) + list(produces):
            if layer not in allowed_layers:
                problems.append(f"workstream {ws_id} references unknown layer {layer!r}")

        if not required:
            warnings.append(f"workstream {ws_id} has no required artifacts")
        for rel_path in required:
            if not _artifact_exists(root, rel_path):
                problems.append(f"workstream {ws_id} missing required artifact: {rel_path}")

    unowned = sorted(set(gates) - owned_gates)
    if unowned:
        problems.append(f"gates without owning workstream: {', '.join(unowned)}")

    return problems, warnings, len(gates), len(workstreams)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate delivery_workstreams.yaml")
    parser.add_argument("--model", default="delivery_workstreams.yaml")
    parser.add_argument("--evidence", default="evidence_layers.yaml")
    parser.add_argument("--strict", action="store_true",
                        help="Treat warnings as failures")
    args = parser.parse_args(argv)

    model_path = os.path.abspath(args.model)
    evidence_path = os.path.abspath(args.evidence)
    problems, warnings, gate_count, workstream_count = check_delivery_model(
        model_path, evidence_path
    )

    print("=== Delivery Model Check ===")
    print(f"Model: {model_path}")
    print(f"Evidence index: {evidence_path}")
    print(f"  gates       {gate_count}")
    print(f"  workstreams {workstream_count}")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")

    if problems:
        print("\nFailures:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    if args.strict and warnings:
        print("\nStrict mode failed because warnings were present.")
        return 1

    print("\nDelivery operating model: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
