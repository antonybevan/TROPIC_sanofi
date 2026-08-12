# WS-3 External Validation Evidence Index

**Workstream:** Standards & Metadata (with WS-1/WS-5 inputs)
**Gates:** G03 primary; feeds G06
**Product claim:** Path A
**As of:** 2026-08-12
**Purpose:** Separate **what we have run** from **what industry still expects** so we never fake a P21/FDA story.

---

## 1. How to use this index

Every row is a **slot**:

| Slot status | Meaning |
|---|---|
| **RUN** | Evidence file exists from a real execution |
| **PARTIAL** | Run exists but coverage/residuals incomplete |
| **NOT_AVAILABLE** | Tool/license/data prevents run; must not be implied |
| **N/A_PATH_A** | Not required to claim Path A demo RC |
| **BLOCKED_PATH_B** | Required before any submission-simulation claim |

---

## 2. Evidence slots

### 2.1 Define-XML / schema

| Slot | Status | Evidence location | Notes |
|---|---|---|---|
| Define-XML 2.1 + ARM XSD (`define.xml`) | **RUN** | `03_metadata/define/validate_xsd.sh` · schema under `03_metadata/define/schema/` | Schema validity ≠ business-rule conformance |
| Define structural/referential | **RUN** | `03_metadata/define/validate_define.py` | Fast gate |
| Spec → Define conformance | **RUN** | `03_metadata/define/check_define_conformance.R` · `platform/conformance/spec_define_conformance.json` | In DAG |
| Spec → Data conformance | **RUN** | `04_analysis_datasets/programs/r/spec_data_checks.R` · `spec_data_conformance.json` | In DAG |
| SDTM Define-XML | **RUN** | `03_metadata/define/define_sdtm.xml` + package pairing | Pair with uplifted SDTM |

### 2.2 CDISC CORE (open engine)

| Slot | Status | Evidence location | Notes |
|---|---|---|---|
| SDTMIG 3.4 CORE (uplifted package layer) | **PARTIAL** | `platform/conformance/CORE_SDTM34_RUN_RECORD.md` | Residuals not fully dispositioned (F-015) |
| SDTMIG 3.2 baseline on pristine source | **PARTIAL** | `CORE_RUN_RECORD.md` / related | Version caveats documented in REPRODUCIBILITY |
| ADaM CORE via local rules | **RUN** | `platform/conformance_rules/adam/` · CORE run record | Not official AD#### catalog |
| Official ADaM Conformance Rules (members) | **NOT_AVAILABLE** | — | F-016 class |
| CORE residual disposition matrix | **RUN** | `docs/workstreams/WS1_CORE_RESIDUAL_MATRIX.csv` | Rule/domain disposition; still not “CORE clean” |

### 2.3 Commercial / FDA validators

| Slot | Status | Evidence location | Notes |
|---|---|---|---|
| Pinnacle 21 Community ADaM | **RUN (INFORMATIVE)** | `06_qc_evidence/conformance/p21_adam_runrecord.md` · `p21_adam_summary.json` | FDA 2508.1; 7 datasets / 121,320 records / 0 rejects; 30 open groups / 2,373 occurrences; incompatible-CLI caveat retained |
| Pinnacle 21 Enterprise ADaM | **NOT_AVAILABLE** | — | Licensed, qualified Enterprise execution not performed; do not claim clearance |
| FDA DataFit / eCTD validator commercial | **NOT_AVAILABLE** | — | Structure demo only |
| Local ADaM label/conformance scripts | **RUN** | `06_qc_evidence/conformance/adam_conformance_*` · `platform/run_adam_conformance.sh` | Sponsor-authored depth limited |

### 2.4 eCTD structure

| Slot | Status | Evidence location | Notes |
|---|---|---|---|
| Module 5 tree assembly | **RUN** | `platform/package_ectd.py` -> `08_submission_package/m5/` | Path A |
| Backbone + STF + materialize + MD5 | **RUN** | `build_ectd_backbone.py` · `materialize_ectd.py` · `08_submission_package/ectd/RUN_RECORD.md` | 90 checksum leaves; 89 sequence m5 hrefs indexed |
| DTD validation (xmllint) | **RUN** (documented) | `08_submission_package/ectd/RUN_RECORD.md` | EXAMPLE app IDs remain |
| Real application identifiers | **N/A_PATH_A** / **BLOCKED_PATH_B** | F-005 | EXAMPLE/000000 |
| True annotated CRF | **N/A_PATH_A** / **BLOCKED_PATH_B** | F-005 | Placeholder only |

### 2.5 Metadata lineage & CT

| Slot | Status | Evidence location | Notes |
|---|---|---|---|
| Metadata lineage YAML + check | **RUN** | `config/metadata_lineage.yaml` · `apply_metadata_lineage.py` | F-013 RESOLVED |
| Metadata control report | **RUN** | `docs/METADATA_CONTROL_REPORT.md` | |
| CT cross-validation | **PARTIAL** | `platform/ct_cross_validation.py` · JSON | May need API key |
| Project CT version posture | **DECLARED** | 2026-03-27 in guides/USDM | Keep aligned |

### 2.6 Exploratory modern layers (must not be oversold)

| Slot | Status | Delivery to eCTD? | Notes |
|---|---|---|---|
| Dataset-JSON export | **RUN** (hardened) | **No** | F-020 exploratory |
| USDM study JSON | **RUN** (deterministic IDs) | **No** | F-021 exploratory |
| ARS / ARD | **PARTIAL** | **No** | F-022 controlled core only |
| ARM in define.xml | **RUN** | In define | 10 ResultDisplays / 18 AnalysisResults; all controlled analysis outputs mapped except the non-analysis F-01-1 flow diagram; CbzP disclosure on every ResultDisplay |

---

## 3. Path A vs Path B requirements

| Claim | Minimum external evidence |
|---|---|
| **Path A controlled simulation** (current) | Spec↔define↔data gates + dual-lang + XSD + eCTD structure + Community issue-discovery evidence with all findings and limitations visible |
| **Path B submission simulation** | All Path A + qualified validator report with approved disposition + CORE residual matrix + aCRF plan + real/placeholder app ID policy documented |
| **Path C real submission support** | Path B + sponsor data rights + org QC + Part 11 process evidence |

---

## 4. Immediate work items (ordered)

1. **DONE:** `WS1_CORE_RESIDUAL_MATRIX.csv` filed from the latest CORE evidence.
2. **DONE:** SDRG links the XSD/CORE run records and states the residual boundary.
3. **DONE:** Community validation aggregate evidence is hash-bound and machine-reconciled; the record-level workbook remains outside Git.
4. **EXTERNAL:** Reproduce the final locked package in licensed, qualified Enterprise and independently approve every disposition before any regulated-use claim.
5. Keep Dataset-JSON/USDM/ARS labeled **exploratory** in ADRG until packaging decision.

---

## 5. Review agenda (Standards workstream, 45 min)

1. Walk this index row by row—status only, no coding.
2. Confirm no public doc says “P21 clean.”
3. Assign residual matrix owner.
4. Decide whether ARS/USDM remain exploratory for next tag train.

---

## 6. Exit criteria for WS-3 GREEN (Path A)

- [x] Spec→define / spec→data PASS at seal
- [x] XSD path documented
- [x] Exploratory layers not in eCTD
- [x] Community execution recorded as informative-only, with open findings and compatibility caveat
- [x] Licensed Enterprise explicitly NOT_AVAILABLE / NOT_EXECUTED
- [x] CORE residual matrix filed
- [x] Standards pack reviewed once
- [x] ARM endpoint semantics and synthetic-comparator disclosure executable under G02

**Disposition:** **GREEN for controlled Path A simulation scope; AMBER for broader commercial-validator depth.**
The Community run strengthens issue-discovery evidence but does not close the missing licensed,
qualified Enterprise/FDA-validator capability boundary.
