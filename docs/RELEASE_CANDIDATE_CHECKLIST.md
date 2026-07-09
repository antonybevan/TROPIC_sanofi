# TROPIC Release-Candidate Checklist

Generated: 2026-07-09 16:42:02 UTC

> Strict go/no-go checklist for the current working evidence set. This report is intentionally conservative and does not convert historical evidence into current release readiness.

## Verdict

| Item | Value |
| --- | --- |
| Overall status | PASS |
| Checks | 16 |
| Pass | 16 |
| Warning | 0 |
| Blocker | 0 |
| Live SAS execution mode | oda |
| Confirmed active Critical/Major audit findings | 0 |

## Blockers

No blocking release-candidate findings.

## Warnings

No release-candidate warnings.

## Full Checklist

| Gate | Check | Status | Evidence | Required action |
| --- | --- | --- | --- | --- |
| G01 source_intake_lock | Source profile generated and clean | PASS | platform/source_profile_status.json status=pass; domains=34; DM subjects=371 |  |
| G03 metadata_lock | Metadata control report has no blocking warnings | PASS | platform/metadata_control/metadata_control_status.json status=pass; findings=0 |  |
| G06 qc_signoff | Risk-based validation strategy is satisfied by current evidence | PASS | platform/validation_strategy/validation_strategy_status.json status=PASS; blocked=0 |  |
| G06 qc_signoff | Execution logs have no unapproved warnings, errors, invalid-input notes, or uninitialized-variable findings | PASS | platform/log_cleanliness/log_cleanliness_status.json status=PASS; unapproved=0; reviewed_exceptions=39 |  |
| G04 analysis_dataset_promotion | Current live run uses real independent SAS engine | PASS | platform/pipeline_health.json sas_execution_mode=oda; pipeline=GREEN |  |
| G04 analysis_dataset_promotion | Dataset reconciliation is non-simulated | PASS | platform/reconciliation_status.json overall=PASS; simulated=False |  |
| G04 analysis_dataset_promotion | Committed ODA evidence snapshot exists | PASS | platform/evidence/*.oda-green.json | Snapshot is evidence of a prior genuine ODA run, not the current live run. |
| G04 analysis_dataset_promotion | Third-engine admiral reconciliation passes for critical core on current run | PASS | platform/admiral_reconciliation_status.json overall=PASS; dag_stage=PASS; current_with_run=True |  |
| G05 output_promotion | TFL output index is complete for controlled catalog scope | PASS | platform/tfl_output_index_status.json status=pass; controlled_catalog=pass; in_scope=18; deferred=21; stale_sas_companions_nongating=6 |  |
| G06 qc_signoff | Results reconciliation available and passing | PASS | platform/results_reconciliation_status.json overall=PASS |  |
| G06 qc_signoff | Forest HR reconciliation passes | PASS | platform/forest_reconciliation_status.json overall=PASS |  |
| G06 qc_signoff | Synthetic comparator bridge parity passes | PASS | platform/cbzp_bridge_status.json overall=PASS | Still disclose CbzP as synthetic/reconstructed demonstration content. |
| G09 release_candidate_lock | Current release-run manifest is release-candidate grade (full DAG, clean tree) | PASS | platform/release_run_manifest/release_run_manifest.json status=PASS; evidence_grade=release_candidate; run_scope=full_dag; seal=dfacf2893da1bc90eb9b1a91ee78c1b5350ce20e2382a352943e50e65c89d611 |  |
| G09 release_candidate_lock | Pipeline health records a full current DAG run | PASS | platform/pipeline_health.json run_scope=full_dag; stages_recorded=33; stages_expected=33; stages_not_run=0 |  |
| G06 qc_signoff | Audit findings register has no active confirmed Critical/Major blockers | PASS | 06_qc_evidence/audit/findings_register.csv active=0; confirmed Critical/Major=0; severity_counts={} | Close, resolve, or formally disposition confirmed Critical/Major findings before any release-ready claim. |
| G08 submission_package_materialization | eCTD backbone/run record present | PASS | 08_submission_package/ectd/0000/index.xml present=True; 08_submission_package/ectd/RUN_RECORD.md present=True | Rebuild/materialize eCTD sequence after upstream release candidate is clean. |

## Interpretation

- `PASS` means the current evidence satisfies the checklist item.
- `WARNING` means the evidence exists but has unresolved limitations that must be dispositioned.
- `BLOCKER` means no release-ready or submission-ready claim should be made until the item is resolved.
- A prior ODA evidence snapshot proves that genuine SAS/R reconciliation has occurred before; it does not make the current live `sim` telemetry release-ready.

## Machine-Readable Outputs

- `platform/release_candidate/release_candidate_status.json`
- `platform/release_candidate/release_candidate_checklist.csv`
