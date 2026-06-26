# Study Data Standardization Plan (SDSP) — TROPIC

**Study:** TROPIC (EFC6193 / XRP6258) · NCT00417079
**Compound:** Cabazitaxel (XRP6258) vs Mitoxantrone, mCRPC post-docetaxel
**Plan version / date:** 1.1 · 2026-06-25
**Basis:** SAP v4.0 lock review; current FDA Study Data Technical Conformance Guide and CDISC standards.

> **Current lock status:** `TROPIC_SAP_v4.0_industry_grade.docx` is the programming authority.
> This SDSP is a remediation-control plan, not a final submission plan. The SAP lock memo
> (`audit/SAP_LOCK_REVIEW_MEMO.md`) still blocks submission release until SDTM package-source
> drift, eCTD stale-payload controls, CRF provenance, and final conformance evidence are closed.

The SDSP describes the data standards, versions, and conformance approach used for the
study's tabulation and analysis data, and discloses planned exceptions — the single
document an FDA reviewer reads to understand *what* standards were applied and *where*
they deviate. It consolidates declarations otherwise spread across the SDRG/ADRG, the
two Define-XML files, and the traceability matrix.

## 1. Standards and versions

| Layer | Standard | Version | Source of truth |
|---|---|---|---|
| Tabulation (SDTM) | SDTMIG | **3.4** (uplifted from 3.1.1 source — see §3) | `07_define_xml/define_sdtm.xml` |
| Analysis (ADaM) | ADaMIG | 1.3 | `07_define_xml/define.xml` |
| Occurrence (AE) | OCCDS | 1.0 (+ documented episode-merging extension) | ADRG §2 |
| Metadata | Define-XML | 2.1.0 (+ ARM 1.0) | both define files |
| Analysis results metadata | Analysis Results Standard (ARS) | 1.0 | `12_ars/tropic_reporting_event.json` |
| Controlled Terminology | CDISC/NCI CT | **2026-03-27** (SDTM + ADaM) | both define files |
| Study definition | USDM (DDF) | 3.0.0 | `13_usdm/tropic_usdm.json` |
| Transport | SAS Transport v5 (XPT) **and** CDISC Dataset-JSON | v5 + 1.1.0 | `04_adam/*.xpt`, `10_datasetjson/` |
| Submission packaging | eCTD | ICH 3.2 backbone + STF 2.2 + FDA Regional v3.3 (**all DTD-valid**) | `11_ectd/0000/` |

## 2. Conformance / validation approach

- **Define-XML:** XSD-valid (CDISC 2.1 + ARM schema) and parses in the CDISC CORE
  reference engine; referential integrity gated by `validate_define.py`.
- **Spec governance:** `ADaM_spec.xlsx` (metacore) is the intended metadata control source;
  `spec→define` and `spec→data` gates are release gates and must be rerun after SAP v4.0
  remediation.
- **SDTM:** target package standard is **SDTMIG 3.4** (CT 2026-03-27). The full package must
  use the uplifted SDTM 3.4 XPT layer described by `define_sdtm.xml`; raw SDTMIG 3.1.1
  conversion is not acceptable for a release package.
- **ADaM:** CORE ships no executable ADaM rules yet; interim coverage via project custom
  CORE rules (`conformance_rules/adam/`) + `adam_conf_check.R`.
- **Pinnacle 21 / Certara:** the authoritative business-rule run remains **pending** a
  non-expired engine licence (terminal-session item).
- **Dataset-JSON:** treated as an auxiliary machine-readable layer. Schema and round-trip
  evidence must be regenerated after the final SAP v4.0 data/metadata lock.

## 3. Declared exceptions and deviations

1. **SDTMIG version — RESOLVED (2026-06-20).** The PDS source is SDTMIG 3.1.1 (below the
   FDA support floor). A derived **3.4** layer was produced (EPOCH, Trial Design TA, AGE
   from de-id AGEGRP, AGEU, AESOC, week-vars→SUPPAE/SUPPDS) and CORE-validated at 3.4; the
   pristine source (`01_raw_source/real_sdtm/`) is unchanged. See SDRG §5.
2. **Controlled Terminology — RESOLVED (2026-06-20).** Both defines refreshed from
   2024-03-29 to the current CDISC/NCI CT package **2026-03-27**.
3. **Synthetic comparator arm.** The reconciled ADaM is the real Mitoxantrone arm
   (N=371) only; the Cabazitaxel arm is reconstructed (Guyot IPD / PH-scaling) for TFL
   demonstration and is **not** part of the conformed deliverables. The submission is a
   methodological re-analysis, not a marketing application (see FDA-reviewer audit R-1).
4. **Source date precision.** AE/disposition timing is week-offset (±3.5 days); a
   sensitivity analysis (`date_precision_sensitivity.py`) shows the KM medians are robust
   to this precision.
5. **Single-author validation.** SAS production and R validation are independently coded
   but by one programmer — implementation reconciliation, not two-programmer GxP.
6. **Non-discriminating population flags / no DV domain;** placeholder baseline
   albumin/LDH; placeholder geography — all disclosed in the ADRG/SDRG.

## 4. Deliverables index

SDTM + SUPP (`m5/.../tabulations/sdtm`), ADaM 7 + BIMO clinsite (`04_adam/`,
`m5/.../analysis/adam`), both Define-XML + stylesheets, ADRG/SDRG/BDRG + traceability
matrix, TFLs (`09_tfl/`), ARS ReportingEvent + ARD (`12_ars/`), USDM study definition
(`13_usdm/`), Dataset-JSON (`10_datasetjson/`), eCTD backbone + STF (`11_ectd/`).

## 5. Standards governance

Pipeline structure and dataset/program/validation wiring are declared once in
`study_manifest.yaml`; clinical parameters in `study_config.yaml`. Reproducibility is
pinned (`renv.lock`; `REPRODUCIBILITY.md`).
