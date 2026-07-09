# WS-1 Source Intake Evidence Pack

**Workstream:** Clinical Data Management / Source Intake  
**Gate:** G01  
**Product claim:** Path A (`docs/PRODUCT_CLAIM.md`)  
**As of:** 2026-07-09  
**Board status:** AMBER (pack exists; CORE residual matrix still open)

---

## 1. Mission

Prove we know **what source data we have**, **what we may redistribute**, **what limitations the source imposes**, and **what structural checks ran**—before anyone treats ADaM as locked.

---

## 2. Owned artifact checklist

| Artifact | Role | Path | Status |
|---|---|---|---|
| Source landing area | Real SDTM + docs (local) | `01_raw_source/` | Required locally; **not** in git |
| Data access boundary | What clone can/cannot run | `REPRODUCIBILITY.md` | Present |
| Staging ingest | SUPP merge / staging RDS | `03_validation_r/v_staging_ingest.R` + SAS `L_staging_ingest.sas` | In DAG |
| SDTM structural validation | Domain checks / warnings | `03_validation_r/v_sdtm_validation.R` + log | In DAG |
| Source profile | Aggregate inventory (patient-safe) | `docs/SOURCE_PROFILING_REPORT.md` · `06_telemetry/source_profile*` | PASS at seal |
| SDTMIG 3.4 uplift | Package source layer | `06_telemetry/uplift_sdtm_34.R` | In package path |
| CORE SDTM 3.4 run | Open conformance evidence | `06_telemetry/conformance/CORE_SDTM34_RUN_RECORD.md` | Present (partial residual story) |
| SDRG | Human source explanation | `08_reviewers_guides/SDRG.md` | Present; hardening continues |
| Disposition | F-015, F-017 | findings register + known-differences memo | ACCEPTED on record |

---

## 3. Source facts (must stay true)

1. **MP arm only** in official PDS release used here (N=371 subjects in DM).  
2. **CbzP is not source SDTM** in this package—reconstructed later for TFLs only.  
3. **Patient-level `*.sas7bdat` must not be committed.**  
4. **Week-offset / partial dates** are source properties; do not invent day precision (F-017).  
5. Package SDTM for submission-style tree is the **uplifted 3.4 layer**, not raw 3.1.1 dump alone.

---

## 4. Machine evidence at Path A seal

| Check | Expected for pack green |
|---|---|
| Source profile status | `pass` |
| DM unique subjects | 371 |
| Staging ingest stage | PASS in full_dag health |
| SDTM validation stage | PASS in full_dag health |
| Metadata drift (SDTM package) | 0 problem rows (F-002 RESOLVED) |

**How to re-read without ODA:**

```bash
python3 -c "import json; print(json.load(open('06_telemetry/source_profile_status.json')))"
python3 -c "import json; h=json.load(open('06_telemetry/pipeline_health.json')); print({k:h['stages'].get(k) for k in h['stages'] if 'SDTM' in k or 'Staging' in k})"
```

---

## 5. Residual matrix (WS-1 owned)

| ID | Issue | Disclosure location | Next work |
|---|---|---|---|
| F-017 | Partial ISO / TSSEQ / week precision | SDRG §2/§5 · known-differences memo | Keep disclosed; no silent “fix” |
| F-015 | CORE residual breadth | CORE run record · known-differences | Build residual disposition spreadsheet by rule/domain |

### CORE residual plan (next engineering task)

Deliverable: `docs/workstreams/WS1_CORE_RESIDUAL_MATRIX.csv` with columns:

`rule_id, domain, severity, n_occurrences, scientific_impact, disposition (fix|accept|waive), sdrg_section, owner, target_date`

Until that file exists, **do not** claim “full CORE clean.”

---

## 6. Handoff contracts

| To | Handoff content |
|---|---|
| **WS-2 Spec** | Subject counts, domain availability, date precision limits |
| **WS-3 Standards** | Uplifted SDTM define pairing, CT version 2026-03-27 posture |
| **WS-4 Programming** | Staging path, SAFFL/ITT populations from source-derived ADSL |
| **WS-5 QC** | SDTM val logs, source profile, F-015/F-017 residuals |
| **WS-6 Writing** | SDRG narrative must match this pack |

**Refuse handoff** if source profile is missing or subject count unexplained.

---

## 7. Workstream review agenda (45 min)

1. Confirm PRODUCT_CLAIM Path A still accepted for source story.  
2. Walk source profile: domains, N=371, missingness highlights.  
3. Open SDTM validation log: classify WARNING vs ERROR.  
4. Read F-017 text aloud from known-differences memo.  
5. Assign owner + date for CORE residual matrix.  
6. No ADaM programming discussion in this review.

---

## 8. Exit criteria for WS-1 GREEN (Path A)

- [x] Source profile PASS  
- [x] Staging + SDTM val in sealed full DAG  
- [x] Redistribution boundary documented  
- [x] F-017 ACCEPTED with SDRG language  
- [ ] CORE residual matrix file exists and is linked from SDRG  
- [ ] WS-1 pack reviewed once with notes filed under `docs/workstreams/reviews/`  

Until the last two boxes are checked, board status remains **AMBER**.
