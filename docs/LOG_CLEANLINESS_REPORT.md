# TROPIC Log Cleanliness Report

Generated: 2026-07-09 15:00:32 UTC

> Automated scan of **configured persisted** SAS/R execution logs. Reviewed exceptions remain visible and capped; unapproved issues fail the gate. This gate does **not** scan ephemeral rscript/python stage stdout/stderr (those streams are not persisted by `cibuild.py`).

## Verdict

| Item | Value |
| --- | --- |
| Status | PASS |
| Coverage | configured_persisted_logs_only |
| Logs scanned | 13 |
| Unapproved findings | 0 |
| Reviewed exceptions | 39 |
| Missing required logs | 0 |

## Reviewed Exception Caps

| Exception | Count | Max | Status | Rationale |
| --- | --- | --- | --- | --- |
| ADTTE_TIME_ORIGIN_FLOORING | 39 | 39 | PASS | Known source-date/time-origin anomaly retained as an explicit, capped QC exception; source timing remediation remains tracked under F-017. |

## Excluded Logs

| Log | Rationale |
| --- | --- |
| 02_production_sas/oda_tfl.log | Manual SAS-figure renderer log from _oda_render_tfl.py; out-of-DAG/manual artifact tracked separately under F-024, not active release-run evidence. |

## Unapproved Findings

No unapproved log findings.

## Machine-Readable Outputs

- `06_telemetry/log_cleanliness/log_cleanliness_status.json`
- `06_telemetry/log_cleanliness/log_findings.csv`
