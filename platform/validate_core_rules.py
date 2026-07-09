#!/usr/bin/env python3
"""CI gate: validate the executable CDISC CORE ADaM conformance rules are shape-valid.

This is intentionally dependency-light (PyYAML only) and needs NO CDISC Library API key
and NO datasets, so it runs on every push/PR. It checks that each rule under
platform/conformance_rules/ is valid YAML, carries the CORE-required keys, and has
unique Core.Id values, so the rule pack cannot silently rot. This is a fast structural
gate, not a full semantic/executability validation of CORE's Check grammar. The full
conformance RUN (which needs library metadata via CDISC_LIBRARY_API_KEY) is the documented
step in run_core_conformance.sh.
"""
from collections import defaultdict
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
RULE_EXTENSIONS = ("*.yml", "*.yaml")


def rule_paths():
    files = []
    for ext in RULE_EXTENSIONS:
        files.extend(glob.glob(os.path.join(RULES_DIR, "**", ext), recursive=True))
    return sorted(set(files))


def _scope_domains_ok(domains):
    if isinstance(domains, list):
        return bool(domains) and all(isinstance(d, str) and d.strip() for d in domains)
    if isinstance(domains, dict):
        seen = []
        for key in ("Include", "Exclude"):
            vals = domains.get(key)
            if vals is None:
                continue
            if not (isinstance(vals, list) and vals):
                return False
            if not all(isinstance(d, str) and d.strip() for d in vals):
                return False
            seen.extend(vals)
        return bool(seen)
    return False


def core_id(path):
    try:
        with open(path, encoding="utf-8") as f:
            rule = yaml.safe_load(f)
    except yaml.YAMLError:
        return None
    if not isinstance(rule, dict):
        return None
    core = rule.get("Core", {})
    if isinstance(core, dict):
        return core.get("Id")
    return None


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
    if not isinstance(scope, dict):
        errs.append("Scope is not a mapping")
    elif not _scope_domains_ok(scope.get("Domains")):
        errs.append("Scope.Domains is missing or malformed")
    return errs


def main():
    rule_files = rule_paths()
    if not rule_files:
        print(f"No rule files found under {RULES_DIR}")
        sys.exit(1)
    ids = defaultdict(list)
    for path in rule_files:
        rid = core_id(path)
        if rid:
            ids[rid].append(path)
    duplicate_ids = {rid: paths for rid, paths in ids.items() if len(paths) > 1}
    total_errs = 0
    for path in rule_files:
        errs = validate_rule(path)
        rid = core_id(path)
        if rid in duplicate_ids:
            rels = ", ".join(os.path.relpath(p) for p in duplicate_ids[rid])
            errs.append(f"duplicate Core.Id '{rid}' declared in multiple files: {rels}")
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
