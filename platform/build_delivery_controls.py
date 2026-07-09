#!/usr/bin/env python3
"""Run the delivery operating-model control reports as one architecture gate.

This runner is meant for local use and CI. It rebuilds the generated architecture
reports, validates the machine-readable evidence/workstream contracts, and prints
the resulting statuses. It intentionally does not fail merely because the current
release-candidate checklist is BLOCKED or metadata control is WARNING; those are
project-state findings, not architecture-wiring failures.
"""

import argparse
import json
import os
import subprocess
import sys


REPORT_COMMANDS = [
    ["platform/build_source_profile.py"],
    ["platform/build_tfl_output_index.py"],
    ["platform/build_metadata_control_report.py"],
    ["platform/build_ctq_traceability_report.py"],
    ["platform/check_log_cleanliness.py"],
    ["platform/build_validation_strategy_report.py"],
    ["platform/build_release_run_manifest.py"],
    ["platform/build_release_candidate_checklist.py"],
    ["platform/build_orchestrator_gate_map.py"],
    ["platform/build_delivery_dashboard.py"],
]

# These rewrite Path A seal allowlist JSONs. Safe locally after a real run; unsafe in
# data-free CI because they would clobber committed seals before verify_release.
SEAL_MUTATING_REPORTS = {
    "platform/check_log_cleanliness.py",
    "platform/build_release_run_manifest.py",
    "platform/build_release_candidate_checklist.py",
}

CHECK_COMMANDS = [
    ["platform/apply_metadata_lineage.py", "--check"],
    ["platform/check_evidence_layers.py"],
    ["platform/check_delivery_model.py"],
]

COMPILE_TARGETS = [
    "platform/build_delivery_controls.py",
    "platform/build_source_profile.py",
    "platform/build_tfl_output_index.py",
    "platform/build_metadata_control_report.py",
    "platform/build_ctq_traceability_report.py",
    "platform/check_log_cleanliness.py",
    "platform/build_validation_strategy_report.py",
    "platform/build_release_run_manifest.py",
    "platform/build_release_candidate_checklist.py",
    "platform/build_orchestrator_gate_map.py",
    "platform/build_delivery_dashboard.py",
    "platform/apply_metadata_lineage.py",
    "platform/check_evidence_layers.py",
    "platform/check_delivery_model.py",
]

STATUS_FILES = {
    "source_profile": "platform/source_profile_status.json",
    "tfl_output_index": "platform/tfl_output_index_status.json",
    "metadata_control": "platform/metadata_control/metadata_control_status.json",
    "ctq_traceability": "platform/ctq_traceability/ctq_traceability_status.json",
    "log_cleanliness": "platform/log_cleanliness/log_cleanliness_status.json",
    "validation_strategy": "platform/validation_strategy/validation_strategy_status.json",
    "release_run_manifest": "platform/release_run_manifest/release_run_manifest.json",
    "release_candidate": "platform/release_candidate/release_candidate_status.json",
    "orchestrator_gate_map": "platform/orchestrator_gate_map/orchestrator_gate_map_status.json",
}


def _run(cmd, *, hard_fail: bool = True) -> int:
    full_cmd = [sys.executable, *cmd]
    print(f"$ {' '.join(full_cmd)}", flush=True)
    completed = subprocess.run(full_cmd, text=True)
    if completed.returncode != 0 and hard_fail:
        raise SystemExit(completed.returncode)
    if completed.returncode != 0:
        print(
            f"  (report exit {completed.returncode} treated as project-state; "
            "architecture gate continues)",
            flush=True,
        )
    return completed.returncode


def _load_status(path):
    if not os.path.exists(path):
        return "missing"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("status") or data.get("overall") or "missing"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build and validate delivery architecture controls")
    parser.add_argument("--skip-reports", action="store_true",
                        help="Only compile scripts and run structural checks")
    parser.add_argument(
        "--ci",
        action="store_true",
        help=(
            "CI mode: skip seal-mutating report builders so committed Path A "
            "seal JSONs stay intact for scripts/verify_release.py"
        ),
    )
    args = parser.parse_args(argv)
    ci_mode = bool(args.ci or os.environ.get("GITHUB_ACTIONS"))

    print("=== Delivery Architecture Controls ===", flush=True)
    if ci_mode:
        print("(CI mode: seal-mutating reports skipped)", flush=True)
    # Compile + structural checks hard-fail. Report builders write project-state
    # statuses (PASS/WARNING/BLOCKED/not_available) and must not fail CI alone.
    _run(["-m", "py_compile", *COMPILE_TARGETS], hard_fail=True)

    if not args.skip_reports:
        for cmd in REPORT_COMMANDS:
            script = cmd[0]
            if ci_mode and script in SEAL_MUTATING_REPORTS:
                print(f"$ (skipped in CI) {script}", flush=True)
                continue
            _run(cmd, hard_fail=False)

    for cmd in CHECK_COMMANDS:
        _run(cmd, hard_fail=True)

    print("\nControl statuses:")
    for name, path in STATUS_FILES.items():
        print(f"  {name:24} {_load_status(path)}")

    print("\nDelivery architecture controls: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
