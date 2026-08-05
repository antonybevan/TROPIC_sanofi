# TROPIC (Study EFC6193 / XRP6258) Pipeline Validation Dashboard

*Captured At:* `2026-08-05T05:30:34.352508+00:00`  
*Environment:* `Darwin 25.5.0 / Real SAS-R Validation Track (SAS 9.4 executed on ODA via SASPy this run)`  
*Pipeline Status:* **RED**

## Stage-Level Execution Checklist

* [PASS] **Governance Scope Lock (G00)**: `PASS`
* [PASS] **Analysis Specification Lock (G02)**: `PASS`
* [PASS] **ADaM Spec Label/Order Artifacts**: `PASS`
* [PASS] **Real SDTM Staging Ingest**: `PASS`
* [PASS] **R SDTM Validation**: `PASS`
* [PASS] **R ADSL Validation**: `PASS`
* [PASS] **R ADEX Validation**: `PASS`
* [PASS] **R ADCM Validation**: `PASS`
* [PASS] **R ADAE Validation**: `PASS`
* [PASS] **R ADLB Validation**: `PASS`
* [PASS] **R ADRS Validation**: `PASS`
* [PASS] **R ADTTE Validation**: `PASS`
* [PASS] **R BIMO Validation**: `PASS`
* [PASS] **SAS Production (ODA/Real/Simulated)**: `PASS`
* [PASS] **Cross-Language Audit Reconcile**: `PASS`
* [PASS] **Admiral ADSL Re-derivation**: `PASS`
* [PASS] **Admiral ADTTE Re-derivation (OS/PFS)**: `PASS`
* [PASS] **Admiral Core Reconciliation**: `PASS`
* [PASS] **Synthetic Comparator Bridge Parity**: `PASS`
* [PASS] **Efficacy & Safety TFL Suite Compilation**: `PASS`
* [PASS] **Numerical Results Reconciliation (SAS vs R)**: `PASS`
* [PASS] **Forest-HR Reconciliation (SAS vs R)**: `PASS`
* [PASS] **Figure-Data Reconciliation (SAS vs R)**: `PASS`
* [PASS] **ADaM Spec to Define Conformance**: `PASS`
* [PASS] **ADaM Spec to Data Conformance**: `PASS`
* [PASS] **Reviewer Package Lock (G07)**: `PASS`
* [FAIL] **Dataset-JSON Export (v1.1)**: `FAIL`

## Validation Controls

- [x] All ADaM datasets successfully compiled
- [x] Independent R double-programming track reconciled against real SAS output
- [x] Cross-Language diffdf reconciliation result: `[PASS - real SAS vs R]`
- [x] SAS 9.4 executed on ODA this run; *_prod.xpt regenerated and reconciled.
