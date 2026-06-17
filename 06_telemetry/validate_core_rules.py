#!/usr/bin/env python3
"""CI gate: validate the executable CDISC CORE ADaM conformance rules are well-formed.

This is intentionally dependency-light (PyYAML only) and needs NO CDISC Library API key
and NO datasets, so it runs on every push/PR. It checks that each rule under
06_telemetry/conformance_rules/ is valid YAML and carries the CORE-required keys, so the
rule pack cannot silently rot. The full conformance RUN (which needs library metadata via
CDISC_LIBRARY_API_KEY) is the documented step in run_core_conformance.sh.
"""
import glob
import os
import sys

try:
    import yaml
except ImportError:
    print("PyYAML not installed; `pip install pyyaml`")
    sys.exit(2)

REQUIRED_TOP = ["Authorities", "Check", "Core", "Description", "Rule Type", "Scope", "Sensitivity"]
RULES_DIR = os.path.join(os.path.dirname(__file__), "conformance_rules")


def validate_rule(path):
    errs = []
    try:
        with open(path, encoding="utf-8") as f:
            rule = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return [f"invalid YAML: {e}"]
    if not isinstance(rule, dict):
        return ["top-level YAML is not a mapping"]
    for key in REQUIRED_TOP:
        if key not in rule:
            errs.append(f"missing required key '{key}'")
    core = rule.get("Core", {})
    if not (isinstance(core, dict) and core.get("Id")):
        errs.append("Core.Id is missing")
    check = rule.get("Check", {})
    if not (isinstance(check, dict) and check):
        errs.append("Check block is empty")
    scope = rule.get("Scope", {})
    if not (isinstance(scope, dict) and scope.get("Domains")):
        errs.append("Scope.Domains is missing")
    return errs


def main():
    rule_files = sorted(glob.glob(os.path.join(RULES_DIR, "**", "*.yml"), recursive=True))
    if not rule_files:
        print(f"No rule files found under {RULES_DIR}")
        sys.exit(1)
    total_errs = 0
    for path in rule_files:
        errs = validate_rule(path)
        rel = os.path.relpath(path)
        if errs:
            total_errs += len(errs)
            print(f"[FAIL] {rel}")
            for e in errs:
                print(f"   - {e}")
        else:
            print(f"[OK]   {rel}")
    print(f"\nCORE rule validation: {len(rule_files)} rule(s), {total_errs} error(s).")
    sys.exit(1 if total_errs else 0)


if __name__ == "__main__":
    main()
