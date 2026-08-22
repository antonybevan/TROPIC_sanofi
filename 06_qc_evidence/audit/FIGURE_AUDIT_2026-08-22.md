# TROPIC Figure, Mathematics, Provenance, and Submission-Surface Audit

**Audit date:** 2026-08-22  
**Scope:** All seven R figures, all six SAS companion figures, the figure gallery, figure-level numerical reconciliation, the Module 5 reviewer surface, and the materialized eCTD sequence 0000.  
**Disposition:** Complete. No open figure defect was found after the final regeneration and verification pass.

## 1. Qualification statement

This repository is a controlled clinical-analysis **demonstration**. The CbzP arm is synthetic and is not patient data; the output is not a real study result, a validated production system, or evidence that could be submitted to FDA without sponsor-specific source traceability, quality-unit review, validation, approvals, and the applicable current standards assessment.

The audit used the current FDA Study Data Technical Conformance Guide (June 2026), FDA study-data/eCTD resources, ICH E3 reporting principles, and the repository's locked analysis and provenance controls as the governing frame. These references informed review expectations; passing this audit is not represented as FDA certification or approval.

## 2. Defects corrected

| Area | Confirmed defect | Correction and control |
|---|---|---|
| Subgroup estimation | Sparse or one-arm subgroups could be displayed as HR 1.00 with CI 1.00–1.00, fabricating a null result. | Both R and SAS now emit missing estimates and display `NE`; source-contract tests prohibit the fabricated fallback. |
| Forest interpretation | The overall row and age label were ambiguous, and within-level CIs could be over-read as evidence of heterogeneity. | The row is now `Intent-to-Treat Population`, the age label is `Age 65 or older`, subgroup N is displayed in SAS, and both tracks warn that no treatment-by-subgroup interaction tests were performed. |
| Population flow | Safety and death counts did not expose all denominators or the seven ITT subjects excluded from safety. | Figure F-01 now reports ITT 749, Safety 742 (99.1%), not in Safety 7 (0.9%), and arm-specific death denominators of 224/371 and 266/371, total 490/742. |
| Colour accessibility | KM and exposure-response treatment groups relied too heavily on colour. | KM curves now use solid/dashed lines and distinct censor marks. Exposure-response plots use circle/triangle points and solid/dashed fitted curves. A final visual pass caught and removed a SAS `SYMBOL=` override that had collapsed both point groups to circles. |
| Exposure-response completeness | The SAS RDI axis could clip a subject above 105%. | The fixed maximum was removed; the final SAS figure includes the observed RDI=106 point. |
| Scientific wording | PSA category wording, measurement units, gallery descriptions, and some interpretation text were imprecise or overclaimed. | Wording now states `at least 50% decrease`, uses professional units, and avoids unsupported efficacy, significance, or tolerability claims. |
| Gallery accessibility | Figure thumbnails did not provide meaningful alternate text. | Each figure now has descriptive alternate text, propagated to the lightbox view and enforced by tests. |
| Track identification | The SAS swimmer figure did not clearly identify its production track. | The title now states `SAS Production Track`. |

## 3. Final artifact generation and provenance

- R figures were regenerated from `05_outputs/tfl/tfl_generation.R` against the governed analysis inputs.
- SAS companion figures and figure-data CSVs were regenerated in a live SAS OnDemand for Academics workspace through `platform/_oda_render_tfl.py --tfl-only`.
- The live ODA connection was nonce-probed before it earned `oda` status. The run uploaded the final SAS source, purged prior remote outputs, rendered all six expected PNGs, downloaded them transactionally, and terminated the session cleanly.
- SASPy 5.107.1 used the three SAS AES client jars required for ODA's SAS 9.4 M7-or-later encryption handshake. No encryption setting was disabled or weakened.
- `04_analysis_datasets/programs/sas/oda_tfl.log` contains the completion marker and zero `ERROR:` or `WARNING:` lines.
- The regenerated source and figure artifacts were copied into Module 5 and then materialized into eCTD sequence 0000.

## 4. Numerical and visual verification

| Verification | Final result |
|---|---|
| SAS forest vs R subgroup estimates | PASS — 13/13 HR rows agree; renamed ITT and age keys reconcile. |
| KM OS and PFS HR/CI | PASS — maximum deltas 0.00040 and 0.00037. |
| KM risk tables | PASS — 32 displayed counts identical. |
| PSA waterfall data | PASS — 690 subjects, values, and categories identical. |
| Swimmer data | PASS — 60 subjects, durations, and death markers identical. |
| Exposure-response data | PASS — 730 joined observations identical. |
| Figure dimensions/opacity | PASS — all 13 PNGs meet the governed 2400-pixel output contracts. |
| Visual QA | PASS — all 13 final PNGs inspected; all six generated reviewer PDFs, 62 pages total, rendered and inspected. |
| Source → Module 5 → eCTD equality | PASS — 15 governed program/figure assets, 45 copies, byte-identical. |
| eCTD sequence integrity | PASS — 99/99 leaves MD5-verified; complete inventory/support/XML/run-record validation passed. |

## 5. Automated regression evidence

- Python suite: **240 passed**.
- R smoke, derivation, lab-shift, figure, population, dashboard, and TFL-statistics suites: **all passed**.
- Figure semantic contracts now cover non-estimable subgroups, ITT naming, explicit population denominators, subgroup interpretation, non-colour cues, data-inclusive RDI axes, SAS marker mapping, subgroup N, and production-track labelling.
- Pipeline manifest DAG: **PASS** — 40 stages, scripts, gate wiring, ordering, and parallel boundaries valid.
- Repository diff whitespace check: **PASS**.

## 6. Package status

The Module 5 reviewer package and eCTD sequence 0000 were rebuilt after the final SAS rendering. The generated CSR, simulation plan, simulation report, ADRG, BDRG, and cSDRG have no observed clipping, overlap, or malformed-glyph defects. The final package preserves the synthetic/non-confirmatory disclosure on the relevant figures.

## 7. Governing references

- FDA, *Study Data Technical Conformance Guide — Technical Specifications Document*, June 2026: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/study-data-technical-conformance-guide-technical-specifications-document
- FDA, *Study Data Standards Resources*: https://www.fda.gov/industry/fda-data-standards-advisory-board/study-data-standards-resources
- FDA, *Electronic Regulatory Submission and Review*: https://www.fda.gov/drugs/forms-submission-requirements/electronic-regulatory-submission-and-review
- ICH, *E3 — Structure and Content of Clinical Study Reports*: https://admin.ich.org/node/603
- SASPy, *Configuration — SAS IOM Client Encryption Jars*: https://sassoftware.github.io/saspy/configuration.html#sas-iom-client-encryption-jars

