#!/usr/bin/env python3
"""Validate the evidence-layer architecture index.

This is deliberately lighter than the build orchestrator. It checks that the
control file is parseable, that every declared evidence-chain layer exists, and
that required artifacts are present. Generated, external, optional, and planned
artifacts are reported but do not fail the check.
"""

import argparse
import glob
import os
import sys
from collections import Counter

try:
    import yaml
except ImportError:
    yaml = None


PASS_STATUSES = {"required"}
KNOWN_STATUSES = {"required", "generated", "external", "optional", "planned"}


def _load_yaml(path):
    if yaml is None:
        raise RuntimeError("PyYAML is not importable; install pyyaml to read config/evidence_layers.yaml")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} did not parse to a YAML mapping")
    return data


def _matches(root, artifact):
    if "path" in artifact:
        path = os.path.join(root, artifact["path"])
        return [path] if os.path.exists(path) else []
    if "glob" in artifact:
        return glob.glob(os.path.join(root, artifact["glob"]), recursive=True)
    return []


def check_evidence_layers(path):
    root = os.path.abspath(os.path.join(os.path.dirname(path), ".."))
    data = _load_yaml(path)
    problems = []
    warnings = []
    counts = Counter()

    chain = data.get("evidence_chain")
    layers = data.get("layers")
    if not isinstance(chain, list) or not chain:
        problems.append("evidence_chain must be a non-empty list")
        chain = []
    if not isinstance(layers, dict):
        problems.append("layers must be a mapping")
        layers = {}

    for layer in chain:
        if layer not in layers:
            problems.append(f"evidence_chain layer {layer!r} has no layers entry")

    for layer_name, layer in layers.items():
        if layer_name not in chain and layer_name != "submission_package":
            warnings.append(f"layer {layer_name!r} is not listed in evidence_chain")
        artifacts = layer.get("artifacts") if isinstance(layer, dict) else None
        if not isinstance(artifacts, list) or not artifacts:
            problems.append(f"layer {layer_name!r} must declare at least one artifact")
            continue
        for i, artifact in enumerate(artifacts, start=1):
            if not isinstance(artifact, dict):
                problems.append(f"layer {layer_name!r} artifact {i} must be a mapping")
                continue
            status = artifact.get("status", "required")
            counts[status] += 1
            if status not in KNOWN_STATUSES:
                problems.append(f"layer {layer_name!r} artifact {i} has unknown status {status!r}")
            if ("path" in artifact) == ("glob" in artifact):
                problems.append(f"layer {layer_name!r} artifact {i} must declare exactly one of path/glob")
                continue

            matches = _matches(root, artifact)
            label = artifact.get("path") or artifact.get("glob")
            if status in PASS_STATUSES and not matches:
                problems.append(f"missing required artifact for {layer_name}: {label}")
            elif status not in PASS_STATUSES and not matches:
                warnings.append(f"{status} artifact not present for {layer_name}: {label}")

    return problems, warnings, counts


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate config/evidence_layers.yaml")
    parser.add_argument("--path", default="config/evidence_layers.yaml",
                        help="Path to the evidence-layer index")
    parser.add_argument("--strict", action="store_true",
                        help="Treat warnings as failures")
    args = parser.parse_args(argv)

    path = os.path.abspath(args.path)
    problems, warnings, counts = check_evidence_layers(path)

    print("=== Evidence Layer Check ===")
    print(f"Index: {path}")
    for status in sorted(counts):
        print(f"  {status:9} {counts[status]}")

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

    print("\nEvidence-layer required artifacts: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
