# Historical GREEN ODA Run — Committed Evidence Badge

These files are an **immutable snapshot** of a genuine SAS↔R double-programming run executed
against a **real SAS 9.4 engine on SAS OnDemand for Academics (ODA)**. They are committed here
*separately* from the live telemetry (`platform/pipeline_health.json`) so that a later
`sim`/`--demo` run — which legitimately overwrites the live file — can **never clobber the proof**
(audit finding C‑1).

> **Snapshot provenance:** refreshed **2026-06-18** (endpoint `odaws01-apse1-2.oda.sas.com`,
> SDTM manifest `329430f6…`). This is immutable **historical evidence**, not certification of
> the current working tree. It records the then-current integrated RECIST response and exploratory
> bone 2+2 (`BSGRESP`) implementation, plus the `AVALC $100` length fix that the real-SAS
> reconciliation itself surfaced (the SET
> concatenation was truncating `'PROGRESSION UNCONFIRMED'` to `'PROGRESSION UNCONFIR'`; 5
> `BSGRESP` cells). All 8 domains + 6 results parameters reconciled against that snapshot revision.

| File | What it proves |
|---|---|
| `pipeline_health.oda-green.json` | `sas_execution_mode = "oda"` (earned via live workspace probe), pipeline GREEN, all stages PASS, `probe_nonce_echoed` + ODA endpoint/attempts recorded. |
| `reconciliation_status.oda-green.json` | All **8** ADaM/BIMO domains reconciled cell-by-cell SAS↔R: ADSL, ADEX, ADCM, ADAE, ADLB, ADRS, ADTTE, **CLINSITE**. |
| `results_reconciliation_status.oda-green.json` | **Analysis-results** reconciliation (SAS `PROC LIFETEST` vs R `survival::survfit`), 6/6 PASS: OS, PFS, TTPAIN, TTPSA, TTSAE, TTUMOR (KM medians agree within 1 day). |
| `xpt_md5_manifest.txt` | For every domain the SAS-produced `*_prod.xpt` and the R-produced `*_v.xpt` are **byte-distinct** (independent engines/headers) yet reconcile **cell-identical** — i.e. genuine independent double-programming, not a copy. |

## Why this matters

Only `sas_execution_mode` ∈ {`oda`, `local`} is genuine double-programming. The default no-engine
run is `sim` (a byte-copy whose zero-difference reconciliation is tautological) and is honestly
labelled as such. The badge above is the canonical demonstration that the SAS and R tracks were
produced **independently** and **agree** — at both the dataset layer and the analysis-results layer.

## Reproducing

```bash
python3 platform/cibuild.py --real-sas    # requires JRE + saspy + ODA credentials
```

The run that produced this historical snapshot surfaced 39 `ADTTE` week-precision time-origin
anomalies and retained them by flooring durations to one day. That behavior is **superseded** in
the current implementation: missing or pre-origin dates are release-blocking and are never silently
floored. Current-run evidence is the live `platform/pipeline_health.json` plus reconciliation and
release-manifest artifacts, not this frozen badge.
