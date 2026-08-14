#!/usr/bin/env python3
"""Build a strict release-candidate go/no-go checklist.

This consumes the operating-model control reports plus core pipeline telemetry.
It is intentionally conservative: a green local run in simulated SAS mode is not a
release candidate, and unresolved confirmed critical/major findings block release.
"""

import argparse
import csv
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

from validate_ectd_sequence import validate_sequence


PATHS = {
    "source_profile": "platform/source_profile_status.json",
    "tfl_index": "platform/tfl_output_index_status.json",
    "metadata_control": "platform/metadata_control/metadata_control_status.json",
    "validation_strategy": "platform/validation_strategy/validation_strategy_status.json",
    "simulation_operating_characteristics": "platform/simulation_operating_characteristics/simulation_oc_status.json",
    "log_cleanliness": "platform/log_cleanliness/log_cleanliness_status.json",
    "pipeline_health": "platform/pipeline_health.json",
    "reconciliation": "platform/reconciliation_status.json",
    "results_reconciliation": "platform/results_reconciliation_status.json",
    "forest_reconciliation": "platform/forest_reconciliation_status.json",
    "figure_data_reconciliation": "platform/figure_data_reconciliation_status.json",
    "cbzp_bridge": "platform/cbzp_bridge_status.json",
    "admiral": "platform/admiral_reconciliation_status.json",
    "release_run_manifest": "platform/release_run_manifest/release_run_manifest.json",
    "oda_evidence_health": "platform/evidence/pipeline_health.oda-green.json",
    "oda_evidence_recon": "platform/evidence/reconciliation_status.oda-green.json",
    "oda_evidence_results": "platform/evidence/results_reconciliation_status.oda-green.json",
    "findings_register": "06_qc_evidence/audit/findings_register.csv",
    "ectd_index": "08_submission_package/ectd/0000/index.xml",
    "ectd_run_record": "08_submission_package/ectd/RUN_RECORD.md",
}


def _load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _status(ok, warning=False):
    if ok and not warning:
        return "PASS"
    if ok and warning:
        return "WARNING"
    return "BLOCKER"


def _add(rows, gate, check, status, evidence, action):
    rows.append({
        "gate": gate,
        "check": check,
        "status": status,
        "evidence": evidence,
        "required_action": action,
    })


def _audit_counts(rows):
    active = [
        r for r in rows
        if str(r.get("status", "")).upper() not in {"CLOSED", "RESOLVED", "ACCEPTED"}
    ]
    by_sev = Counter(str(r.get("severity", "")).title() for r in active)
    confirmed = [
        r for r in active
        if str(r.get("status", "")).upper() == "CONFIRMED"
        and str(r.get("severity", "")).title() in {"Critical", "Major"}
    ]
    return active, by_sev, confirmed


def _admiral_mtime_current(path, health_timestamp):
    """Fallback when DAG stage map is absent: accept mtime not older than health by >7d."""
    try:
        admiral_mtime = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc)
        health_ts = datetime.fromisoformat(str(health_timestamp).replace("Z", "+00:00"))
        if health_ts.tzinfo is None:
            health_ts = health_ts.replace(tzinfo=timezone.utc)
        # Mid-run evidence is earlier than final health stamp; only flag multi-day drift.
        return admiral_mtime >= (health_ts - timedelta(days=7))
    except (OSError, ValueError, TypeError):
        return False


def build_release_checklist(out_dir, report_path):
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    source = _load_json(PATHS["source_profile"], {})
    tfl = _load_json(PATHS["tfl_index"], {})
    metadata = _load_json(PATHS["metadata_control"], {})
    validation_strategy = _load_json(PATHS["validation_strategy"], {})
    simulation = _load_json(PATHS["simulation_operating_characteristics"], {})
    log_cleanliness = _load_json(PATHS["log_cleanliness"], {})
    health = _load_json(PATHS["pipeline_health"], {})
    recon = _load_json(PATHS["reconciliation"], {})
    results = _load_json(PATHS["results_reconciliation"], {})
    forest = _load_json(PATHS["forest_reconciliation"], {})
    figure_data = _load_json(PATHS["figure_data_reconciliation"], {})
    cbzp = _load_json(PATHS["cbzp_bridge"], {})
    admiral = _load_json(PATHS["admiral"], {})
    release_manifest = _load_json(PATHS["release_run_manifest"], {})
    oda_health = _load_json(PATHS["oda_evidence_health"], {})
    oda_recon = _load_json(PATHS["oda_evidence_recon"], {})
    oda_results = _load_json(PATHS["oda_evidence_results"], {})
    findings_rows = _read_csv(PATHS["findings_register"])
    active_findings, findings_by_severity, confirmed_blockers = _audit_counts(findings_rows)
    try:
        ectd_validation = validate_sequence(require_all_leaves=True)
    except Exception as exc:  # release gate must fail closed on validator faults
        ectd_validation = {"status": "FAIL", "problems": [f"validator exception: {exc}"]}

    rows = []

    _add(
        rows, "G01 source_intake_lock", "Source profile generated and clean",
        _status(source.get("status") == "pass"),
        f"{PATHS['source_profile']} status={source.get('status', 'missing')}; domains={source.get('domains', '')}; DM subjects={source.get('dm_unique_subjects', '')}",
        "Regenerate and resolve source profile findings before ADaM lock." if source.get("status") != "pass" else "",
    )
    _add(
        rows, "G03 metadata_lock", "Metadata control report has no blocking warnings",
        _status(metadata.get("status") == "pass", warning=metadata.get("status") == "warning"),
        f"{PATHS['metadata_control']} status={metadata.get('status', 'missing')}; findings={len(metadata.get('findings', []))}",
        "Resolve/disposition remaining metadata findings: CT traceability gaps, predecessor traceability, and drift register." if metadata.get("status") != "pass" else "",
    )
    _add(
        rows, "G06 qc_signoff", "Risk-based validation strategy is satisfied by current evidence",
        _status(validation_strategy.get("status") == "PASS"),
        f"{PATHS['validation_strategy']} status={validation_strategy.get('status', 'missing')}; blocked={validation_strategy.get('blocked', 'missing')}",
        "Resolve the blocked artifacts in docs/VALIDATION_STRATEGY_CONTROL_REPORT.md before release lock." if validation_strategy.get("status") != "PASS" else "",
    )
    simulation_statuses = simulation.get("statuses") or {}
    simulation_ok = (
        (simulation_statuses.get("execution") or {}).get("status") == "PASS"
        and (simulation_statuses.get("monte_carlo_precision") or {}).get("status") == "PASS"
        and (simulation_statuses.get("design_operating_characteristics") or {}).get("status") == "PASS"
        and (simulation_statuses.get("evidence_qualification") or {}).get("status") == "NOT_QUALIFIED"
    )
    _add(
        rows, "G06 qc_signoff", "Simulation methods evidence is precise, verified, and remains non-qualified",
        _status(simulation_ok),
        (
            f"{PATHS['simulation_operating_characteristics']} "
            f"execution={(simulation_statuses.get('execution') or {}).get('status', 'missing')}; "
            f"precision={(simulation_statuses.get('monte_carlo_precision') or {}).get('status', 'missing')}; "
            f"design={(simulation_statuses.get('design_operating_characteristics') or {}).get('status', 'missing')}; "
            f"qualification={(simulation_statuses.get('evidence_qualification') or {}).get('status', 'missing')}"
        ),
        (
            "Regenerate and independently verify the frozen simulation protocol/results, or restore the "
            "informative non-MIDD/non-confirmatory boundary before release lock."
            if not simulation_ok else ""
        ),
    )
    _add(
        rows, "G06 qc_signoff", "Execution logs have no unapproved warnings, errors, invalid-input notes, or uninitialized-variable findings",
        _status(log_cleanliness.get("status") == "PASS"),
        f"{PATHS['log_cleanliness']} status={log_cleanliness.get('status', 'missing')}; unapproved={log_cleanliness.get('unapproved_findings', 'missing')}; reviewed_exceptions={log_cleanliness.get('reviewed_exceptions', 'missing')}",
        "Fix or formally disposition all unapproved log findings in docs/LOG_CLEANLINESS_REPORT.md before QC signoff." if log_cleanliness.get("status") != "PASS" else "",
    )
    _add(
        rows, "G04 analysis_dataset_promotion", "Current live run uses real independent SAS engine",
        _status(health.get("sas_execution_mode") in {"oda", "local"}),
        f"{PATHS['pipeline_health']} sas_execution_mode={health.get('sas_execution_mode', 'missing')}; pipeline={health.get('pipeline_health_status', 'missing')}",
        "" if health.get("sas_execution_mode") in {"oda", "local"} else "Run `python3 platform/cibuild.py --real-sas` with ODA/local SAS and bind outputs to that run.",
    )
    _add(
        rows, "G04 analysis_dataset_promotion", "Dataset reconciliation is non-simulated",
        _status(recon.get("overall") == "PASS" and not recon.get("simulated")),
        f"{PATHS['reconciliation']} overall={recon.get('overall', 'missing')}; simulated={recon.get('simulated', 'missing')}",
        "" if recon.get("overall") == "PASS" and not recon.get("simulated") else "Re-run reconciliation from a real SAS production track; simulated zero-diff is tautological.",
    )
    f042_recon = (recon.get("endpoint_controls") or {}).get("F042_PAIN_RESPONSE")
    _add(
        rows, "G06 qc_signoff", "F-042 pain-response subject-level SAS/R reconciliation passes",
        _status(f042_recon == "PASS"),
        f"{PATHS['reconciliation']} endpoint_controls.F042_PAIN_RESPONSE={f042_recon or 'missing'}",
        (
            "Run the real-SAS F-042 response extract and reconcile every subject/event date, "
            "confirmation date, component, and date source against the R derivation."
            if f042_recon != "PASS"
            else ""
        ),
    )
    _add(
        rows, "G04 analysis_dataset_promotion", "Committed ODA evidence snapshot exists",
        _status(
            oda_health.get("sas_execution_mode") == "oda"
            and oda_recon.get("overall") == "PASS"
            and oda_results.get("overall") == "PASS"
        ),
        "platform/evidence/*.oda-green.json",
        "Refresh the immutable ODA evidence snapshot after current remediation work." if not oda_health else "Snapshot is evidence of a prior genuine ODA run, not the current live run.",
    )
    # Same-run orchestrated admiral is current when the DAG stage PASSed this health file,
    # even if the status JSON was written mid-run before the final health timestamp stamp.
    admiral_stage = (health.get("stages") or {}).get("Admiral Core Reconciliation")
    admiral_current = admiral.get("overall") == "PASS" and (
        admiral_stage == "PASS"
        or (
            os.path.exists(PATHS["admiral"])
            and health.get("timestamp")
            and _admiral_mtime_current(PATHS["admiral"], health.get("timestamp"))
        )
    )
    _add(
        rows, "G04 analysis_dataset_promotion", "Third-engine admiral reconciliation passes for critical core on current run",
        _status(admiral_current),
        (
            f"{PATHS['admiral']} overall={admiral.get('overall', 'missing')}; "
            f"dag_stage={admiral_stage or 'missing'}; current_with_run={admiral_current}"
        ),
        (
            "Rerun admiral reconciliation for ADSL/OS/PFS in the full DAG; "
            "stale out-of-DAG admiral_reconciliation_status.json is not release evidence."
            if not admiral_current
            else ""
        ),
    )
    controlled = (tfl.get("controlled_catalog") or {})
    _add(
        rows, "G05 output_promotion", "TFL output index is complete for controlled catalog scope",
        _status(tfl.get("status") == "pass" and controlled.get("status", "pass") == "pass"),
        (
            f"{PATHS['tfl_index']} status={tfl.get('status', 'missing')}; "
            f"controlled_catalog={controlled.get('status', 'missing')}; "
            f"in_scope={controlled.get('controlled_in_scope_count', tfl.get('indexed_output_ids', ''))}; "
            f"deferred={controlled.get('deferred_count', '')}; "
            f"stale_sas_companions_nongating={len(tfl.get('stale_sas_companion_figures') or [])}"
        ),
        (
            "Align config/tfl_output_catalog.yaml controlled_in_scope with produced outputs; "
            "disposition every SAP full-catalog ID as in-scope or deferred; fix unindexed/missing primaries."
            if not (tfl.get("status") == "pass" and controlled.get("status", "pass") == "pass")
            else ""
        ),
    )
    _add(
        rows, "G06 qc_signoff", "Results reconciliation available and passing",
        _status(results.get("overall") == "PASS"),
        f"{PATHS['results_reconciliation']} overall={results.get('overall', 'missing')}",
        "" if results.get("overall") == "PASS" else "Produce real SAS vs R numerical results reconciliation for the release candidate.",
    )
    _add(
        rows, "G06 qc_signoff", "Forest HR reconciliation passes",
        _status(forest.get("overall") == "PASS"),
        f"{PATHS['forest_reconciliation']} overall={forest.get('overall', 'missing')}",
        "Resolve forest HR reconciliation mismatches." if forest.get("overall") != "PASS" else "",
    )
    _add(
        rows, "G06 qc_signoff", "Figure-driving data reconciliation passes",
        _status(figure_data.get("overall") == "PASS"),
        f"{PATHS['figure_data_reconciliation']} overall={figure_data.get('overall', 'missing')}",
        "Produce and reconcile all SAS figure-data exports before release promotion."
        if figure_data.get("overall") != "PASS" else "",
    )
    _add(
        rows, "G06 qc_signoff", "Synthetic comparator bridge parity passes",
        _status(cbzp.get("overall") == "PASS"),
        f"{PATHS['cbzp_bridge']} overall={cbzp.get('overall', 'missing')}",
        "Regenerate or reconcile CbzP bridge artifacts." if cbzp.get("overall") != "PASS" else "Still disclose CbzP as synthetic/reconstructed demonstration content.",
    )
    run_scope = (
        (release_manifest.get("run_completeness") or {}).get("run_scope")
        or health.get("run_scope")
        or "missing"
    )
    # The pipeline-health check must judge pipeline_health.json alone (audit MAJOR:
    # manifest run_scope previously leaked into the health check, producing a false
    # full-DAG BLOCKER whenever the manifest was partial/dirty).
    health_run_scope = health.get("run_scope") or "missing"
    _add(
        rows, "G09 release_candidate_lock", "Current release-run manifest is release-candidate grade (full DAG, clean tree)",
        _status(release_manifest.get("status") == "PASS"),
        (
            f"{PATHS['release_run_manifest']} status={release_manifest.get('status', 'missing')}; "
            f"evidence_grade={release_manifest.get('evidence_grade', 'missing')}; "
            f"run_scope={run_scope}; seal={release_manifest.get('manifest_sha256', 'missing')}"
        ),
        (
            "Release manifest must be status=PASS (not REMEDIATION/FAIL): full current DAG, "
            "clean worktree, and current-run binding. REMEDIATION is valid development evidence only."
            if release_manifest.get("status") != "PASS"
            else ""
        ),
    )
    _add(
        rows, "G09 release_candidate_lock", "Pipeline health records a full current DAG run",
        _status(health_run_scope == "full_dag" and health.get("pipeline_health_status") == "GREEN"),
        (
            f"{PATHS['pipeline_health']} run_scope={health_run_scope}; "
            f"stages_recorded={health.get('stages_recorded', len(health.get('stages') or {}))}; "
            f"stages_expected={health.get('stages_expected', 'missing')}; "
            f"stages_not_run={len(health.get('stages_not_run') or [])}"
        ),
        (
            "Run the full DAG from stage 1 (no --from-stage) under --real-sas so pipeline_health "
            "covers every study_manifest stage."
            if health_run_scope != "full_dag"
            else ""
        ),
    )
    _add(
        rows, "G06 qc_signoff", "Audit findings register has no active confirmed Critical/Major blockers",
        _status(len(confirmed_blockers) == 0),
        f"{PATHS['findings_register']} active={len(active_findings)}; confirmed Critical/Major={len(confirmed_blockers)}; severity_counts={dict(findings_by_severity)}",
        "Close, resolve, or formally disposition confirmed Critical/Major findings before any release-ready claim.",
    )
    _add(
        rows, "G08 submission_package_materialization",
        "Complete eCTD sequence inventory, checksums, support files, XML references, and run record validate",
        _status(ectd_validation.get("status") == "PASS"),
        (
            f"platform/validate_ectd_sequence.py status={ectd_validation.get('status', 'FAIL')}; "
            f"leaves={ectd_validation.get('present_leaves', 0)}/"
            f"{ectd_validation.get('checksum_leaves', 0)}; "
            f"unexpected={len(ectd_validation.get('unexpected_files', []))}; "
            f"problems={ectd_validation.get('problems', [])[:3]}"
        ),
        (
            "Rebuild/materialize the sequence, remove unexpected files, restore checksum-pinned "
            "official UTIL support assets, and resolve every validator problem."
            if ectd_validation.get("status") != "PASS"
            else ""
        ),
    )

    blocker_count = sum(1 for r in rows if r["status"] == "BLOCKER")
    warning_count = sum(1 for r in rows if r["status"] == "WARNING")
    pass_count = sum(1 for r in rows if r["status"] == "PASS")
    overall = "BLOCKED" if blocker_count else ("WARNING" if warning_count else "PASS")
    status = {
        "status": overall,
        "generated_at": generated_at,
        "checks": len(rows),
        "pass": pass_count,
        "warning": warning_count,
        "blocker": blocker_count,
        "active_audit_findings": len(active_findings),
        "confirmed_critical_major_findings": len(confirmed_blockers),
        "live_sas_execution_mode": health.get("sas_execution_mode", "missing"),
    }

    csv_path = os.path.join(out_dir, "release_candidate_checklist.csv")
    json_path = os.path.join(out_dir, "release_candidate_status.json")
    os.makedirs(out_dir, exist_ok=True)
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["gate", "check", "status", "evidence", "required_action"])
        writer.writeheader()
        writer.writerows(rows)
    with open(json_path, "w", encoding="utf-8") as f:
        payload = dict(status)
        payload["items"] = rows
        json.dump(payload, f, indent=2)

    def md_table(headers, table_rows):
        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]
        for row in table_rows:
            clean = [str(v).replace("|", "\\|").replace("\n", " ") for v in row]
            lines.append("| " + " | ".join(clean) + " |")
        return "\n".join(lines)

    report_rows = [
        [r["gate"], r["check"], r["status"], r["evidence"], r["required_action"]]
        for r in rows
    ]
    blocker_rows = [
        [r["gate"], r["check"], r["required_action"]]
        for r in rows if r["status"] == "BLOCKER"
    ]
    warning_rows = [
        [r["gate"], r["check"], r["required_action"]]
        for r in rows if r["status"] == "WARNING"
    ]
    lines = [
        "# TROPIC Release-Candidate Checklist",
        "",
        f"Generated: {generated_at}",
        "",
        "> Strict go/no-go checklist for the current working evidence set. "
        "This report is intentionally conservative and does not convert historical evidence into current release readiness.",
        "",
        "## Verdict",
        "",
        md_table(
            ["Item", "Value"],
            [
                ["Overall status", overall],
                ["Checks", len(rows)],
                ["Pass", pass_count],
                ["Warning", warning_count],
                ["Blocker", blocker_count],
                ["Live SAS execution mode", health.get("sas_execution_mode", "missing")],
                ["Confirmed active Critical/Major audit findings", len(confirmed_blockers)],
            ],
        ),
        "",
        "## Blockers",
        "",
    ]
    if blocker_rows:
        lines.append(md_table(["Gate", "Check", "Required action"], blocker_rows))
    else:
        lines.append("No blocking release-candidate findings.")
    lines.extend(["", "## Warnings", ""])
    if warning_rows:
        lines.append(md_table(["Gate", "Check", "Required action"], warning_rows))
    else:
        lines.append("No release-candidate warnings.")
    lines.extend([
        "",
        "## Full Checklist",
        "",
        md_table(["Gate", "Check", "Status", "Evidence", "Required action"], report_rows),
        "",
        "## Interpretation",
        "",
        "- `PASS` means the current evidence satisfies the checklist item.",
        "- `WARNING` means the evidence exists but has unresolved limitations that must be dispositioned.",
        "- `BLOCKER` means no release-ready or submission-ready claim should be made until the item is resolved.",
        "- A prior ODA evidence snapshot proves that genuine SAS/R reconciliation has occurred before; it does not make the current live `sim` telemetry release-ready.",
        "",
        "## Machine-Readable Outputs",
        "",
        "- `platform/release_candidate/release_candidate_status.json`",
        "- `platform/release_candidate/release_candidate_checklist.csv`",
        "",
    ])
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return status


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build release-candidate checklist")
    parser.add_argument("--out-dir", default="platform/release_candidate")
    parser.add_argument("--report", default="docs/RELEASE_CANDIDATE_CHECKLIST.md")
    args = parser.parse_args(argv)
    status = build_release_checklist(args.out_dir, args.report)
    print(f"Release-candidate status: {status['status']}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
