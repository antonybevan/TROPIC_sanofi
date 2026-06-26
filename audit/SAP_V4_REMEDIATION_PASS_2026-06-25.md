# SAP v4.0 Remediation Pass — ADTTE/TFL/Package Alignment

**Date:** 2026-06-25
**Scope:** First implementation pass after `audit/SAP_LOCK_REVIEW_MEMO.md`
**Authority:** `TROPIC_SAP_v4.0_industry_grade.docx`
**Status:** Implemented and verified through the full real-SAS CI pipeline on SAS ODA; not a final submission lock until the sponsor/SAP assumptions and non-confirmatory CbzP limitations are formally accepted.

## Changes made

1. **ADTTE PFS event pool aligned to SAP v4.0 §10.1.**
   - PFS now includes the earliest valid disease progression from tumour, PSA, pain progression, or death.
   - Pain-derived PFS events require at least 5 distinct non-missing diary-value days in the visit window before the visit contributes to progression.
   - New anti-cancer therapy censoring remains applied before progression/death.

2. **Secondary efficacy endpoint populations/origins aligned to SAP v4.0 §10.**
   - `TTPSA` now uses ITT (`ITTFL='Y'`) and randomization origin (`RANDDT`), not safety/from-first-dose.
   - `TTUMOR` now uses ITT measurable-disease subjects (`ITTFL='Y' & MEASDISF='Y'`) and randomization origin (`RANDDT`).
   - `TTPAIN` now uses ITT subjects with diary evaluability, not safety population.

3. **Dual-language implementation updated.**
   - Production SAS: `02_production_sas/A_adtte_generation.sas`.
   - R validation: `03_validation_r/v_adtte_validation.R`.
   - R validation was executed successfully and wrote `04_adam/adtte_v.xpt`.
   - Real SAS production was executed on SAS ODA and wrote fresh `04_adam/*_prod.xpt`.
   - Resolved one confirmed dual-language defect: SAS counted diary dates with missing values toward the 5-of-7 diary evaluability rule, while R counted non-missing diary values. Subject `006193-530-002-601` TTPAIN now reconciles as a pain-progression event rather than a last-assessment censor.
   - Cleaned SAS hygiene notes from PROC TRANSPOSE, BIMO CASE expressions, ADCM export labels, and PFS missing-date arithmetic; the remaining SAS warnings are only explicit ADTTE date-origin flooring audit messages.

4. **TFLs regenerated from updated ADTTE.**
   - `Rscript 09_tfl/tfl_generation.R` completed successfully.
   - SAS production figures were re-rendered on SAS ODA after the SAP v4.0 ADTTE fix and downloaded to `09_tfl/output/figures/sas/` on 2026-06-26.
   - R figures were left-anchor normalized against the SAS visual standard; the KM plot/risk-table layout now frees the risk-table label space so it no longer pushes the main KM panel right and creates a large y-axis-title-to-axis gap.
   - Figure QC passed for both R and SAS-rendered figure files.
   - R-to-SAS figure-driving data reconciliation passed for KM OS/PFS, KM risk tables, waterfall, swimmer, exposure-response, and forest HR data.

5. **Documentation/metadata pointers updated.**
   - Updated SAP references from v3.0 to SAP v4.0 controlled draft where applicable.
   - Updated traceability wording for ADTTE endpoint populations/origins and PFS component logic.
   - Updated ARS reference document pointer to `TROPIC_SAP_v4.0_industry_grade.docx`.

6. **Package/eCTD refreshed.**
   - `python3 06_telemetry/package_ectd.py --preview` completed successfully.
   - `python3 06_telemetry/build_ectd_backbone.py` completed successfully.
   - `python3 06_telemetry/materialize_ectd.py` completed successfully with `MD5-verified=47/47`.

## Local checks run

| Check | Result |
|---|---:|
| R parse: ADTTE validation, config, TFL generation, TFL stats | PASS |
| R ADTTE validation execution | PASS; warnings surfaced known date-origin anomalies |
| Real SAS production execution on ODA | PASS; 39 SAS warnings, all explicit ADTTE date-origin flooring messages |
| SAS/R cross-language reconciliation | PASS; zero cell-level differences across ADSL, ADEX, ADCM, ADAE, ADLB, ADRS, ADTTE, CLINSITE |
| R TFL generation | PASS |
| Results-level reconciliation and forest-HR reconciliation | PASS |
| SAS TFL figure render on ODA | PASS; six SAS production PNGs refreshed on 2026-06-26 |
| R/SAS figure-data reconciliation | PASS |
| ADaM spec-to-Define and spec-to-data conformance | PASS |
| Dataset-JSON, ARS, and USDM exports | PASS |
| Figure output QC | PASS |
| eCTD materialization checksum verification | PASS |

## Key ADTTE result snapshot after full real-SAS/R reconciliation

| PARAMCD | N | Events |
|---|---:|---:|
| OS | 371 | 266 |
| PFS | 371 | 330 |
| TTPAIN | 371 | 75 |
| TTPSA | 371 | 265 |
| TTSAE | 371 | 78 |
| TTUMOR | 203 | 186 |

## Remaining limitations

1. Comparative CbzP outputs remain non-confirmatory because CbzP is reconstructed/synthetic.
2. The SAP remains a project-controlled draft, not an official sponsor SAP; sponsor/statistical sign-off is still required before submission-style claims.
3. SAS log warnings remain visible in `02_production_sas/oda_master_driver.log`; all 39 are expected ADTTE date-origin flooring warnings and should remain traceable as an explicit data-precision convention.
4. Define-XML/ARM metadata passed current automated conformance gates, but final reviewer guide text should be re-read after any further SAP edits.

## Next remediation step

1. Re-read the strengthened SAP v4.0 against reviewer guides/Define-XML after any final wording edits.
2. Keep CbzP comparative outputs clearly labelled as reconstructed/non-confirmatory.
3. If sponsor-style acceptance is desired, add a formal SAP assumptions appendix and sign-off checklist.
