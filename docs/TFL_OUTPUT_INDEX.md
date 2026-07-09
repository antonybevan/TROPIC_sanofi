# TROPIC TFL Output Index

Generated: 2026-07-09 14:50:43 UTC

> Structured index for rendered tables, figures, listings, and companion SAS figures. This is output-control evidence, not a claim that every output is submission-ready. **Controlled scope authority:** `tfl_output_catalog.yaml` (SAP authority: TROPIC_SAP_v4.0_industry_grade.docx). SAS companion figures are **out-of-DAG capability demos** (`_oda_render_tfl.py`); presence/hash is inventory only and does **not** gate controlled-scope completeness.

## Summary

| Item | Value |
| --- | --- |
| Generated | 2026-07-09 14:50:43 UTC |
| Overall status | see Machine-Readable status JSON |
| Controlled catalog | tfl_output_catalog.yaml |
| Controlled catalog status | pass |
| Controlled in-scope IDs | 18 |
| SAP full-catalog IDs | 31 |
| Deferred (not in release scope) | 21 |
| Approved extensions | 8 |
| Indexed output IDs | 18 |
| Figure IDs | 7 |
| Table IDs | 11 |
| Missing primary files | 0 |
| Missing SAS companion figures | 0 |
| Stale/historical SAS companions (out-of-DAG, non-gating) | 6 |
| Unindexed physical files | 0 |
| Table IDs in text but not catalog | 0 |
| Catalog table IDs not found in text | 0 |

## Controlled Scope (release-in-scope outputs)

| ID | Class | Title | Disposition | Basis |
| --- | --- | --- | --- | --- |
| F-01-1 | figure | Analysis Population and Mortality Overview | approved_extension | SAP v4.0 §3 populations; analysis-population overview required for package narrative |
| F-11-1 | figure | Kaplan-Meier Overall Survival | sap_full_catalog | SAP v4.0 §9 / Appendix D |
| F-11-2 | figure | Kaplan-Meier Progression-Free Survival | sap_full_catalog | SAP v4.0 §10.1 / Appendix D |
| F-12-1 | figure | Overall Survival Subgroup Forest Plot | sap_full_catalog | SAP v4.0 §8.2 / Appendix D |
| F-13-1 | figure | PSA Best Percentage Change from Baseline Waterfall | approved_extension | SAP v4.0 §5.2 PSA response display; not a separate historical Table-21 ID |
| F-14-1 | figure | Treatment Exposure Duration Swimmer Plot | approved_extension | SAP v4.0 §7.8 exposure display |
| F-17-1 | figure | Project Optimus Exposure-Response Scatter | sap_full_catalog | SAP v4.0 §10 / Appendix D (methodological demonstration) |
| T-11-6 | table | KM Analysis of Time to PSA Progression | sap_full_catalog | SAP v4.0 §§4.3–5.3 / Appendix D |
| T-11-7 | table | KM Analysis of Time to Tumor Progression | sap_full_catalog | SAP v4.0 §§4.3–5.3 / Appendix D |
| T-11-8 | table | Best Clinical Response Endpoints | sap_full_catalog | SAP v4.0 §§4.3–5.3 / Appendix D |
| T-11-8b | table | Objective Response Rate - Response-Evaluable Denominator | approved_extension | Review-board SR-1 sensitivity; companion to T-11-8, not a silent extra |
| T-17-1 | table | Relative Dose Intensity Category Distribution | sap_full_catalog | SAP v4.0 Appendix D Optimus tables (demonstration) |
| T-17-2 | table | Worst Cycle ANC Nadir Grade by G-CSF Usage | sap_full_catalog | SAP v4.0 Appendix D Optimus tables (demonstration) |
| T-17-4 | table | Benefit-Risk Summary by RDI Tertile | sap_full_catalog | SAP v4.0 Appendix D Optimus tables (demonstration) |
| T-20-1 | table | Treatment-Emergent Adverse Events Summary | approved_extension | SAP v4.0 §7 safety TEAE; safety programming deliverable for controlled scope |
| T-20-2 | table | Grade >=3 TEAEs by System Organ Class | approved_extension | SAP v4.0 §7 safety TEAE by SOC |
| T-21-1 | table | Baseline to Worst CTCAE Grade Shift - MP Arm | approved_extension | SAP v4.0 §7.5 lab shift; real MP arm only for confirmatory read |
| T-21-2 | table | Baseline to Worst CTCAE Grade Shift - CbzP Arm | approved_extension | SAP v4.0 §7.5 lab shift; synthetic comparator demonstration only |

## Deferred SAP Full-Catalog IDs (not in this release scope)

| ID | Disposition reason |
| --- | --- |
| F-12-2 | Not implemented; subgroup sensitivity forest deferred pending approved shell + QC |
| T-11-1 | Primary OS table shell not separately programmed; OS evidence delivered via F-11-1 + results recon |
| T-11-2 | Primary PFS table shell not separately programmed; PFS evidence delivered via F-11-2 + results recon |
| T-11-3 | TTPAIN standalone table deferred; parameter exists in ADTTE |
| T-11-4 | SAP catalog secondary table not programmed in current release scope |
| T-11-5 | SAP catalog secondary table not programmed in current release scope |
| T-12-1 | Subgroup efficacy tables deferred; F-12-1 forest is the controlled subgroup display |
| T-12-2 | Subgroup efficacy tables deferred |
| T-13-1 | Additional response/PSA tables deferred; F-13-1 + T-11-8 cover controlled PSA/response displays |
| T-13-2 | Deferred pending approved shells |
| T-13-3 | Deferred pending approved shells |
| T-14-1 | Exposure/disposition table set deferred; F-14-1 swimmer is controlled exposure display |
| T-14-2 | Deferred pending approved shells |
| T-14-3 | Deferred pending approved shells |
| T-14-4 | Deferred pending approved shells |
| T-14-5 | Deferred pending approved shells |
| T-14-6 | Deferred pending approved shells |
| T-15-1 | Safety overview table deferred; T-20 TEAE summaries are controlled safety tables |
| T-16-1 | Safety detail tables deferred |
| T-16-2 | Safety detail tables deferred |
| T-17-3 | Optimus intermediate table not programmed; T-17-1/2/4 are controlled Optimus set |

## Output Traceability Index

| ID | Class | Title | Primary file | Presence | Spec/SAP ref | ADaM inputs | ARM/ARS link | QC evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F-01-1 | figure | Analysis Population and Mortality Overview | 09_tfl/output/figures/F-01-1_CONSORT_Disposition.png | present | SAP v4.0 section 3 | ADSL | out of ARM scope (flow diagram) | ADSL reconciliation; TFL generation gate; output hash |
| F-11-1 | figure | Kaplan-Meier Overall Survival | 09_tfl/output/figures/F-11-1_KM_OS.png | present | SAP v4.0 section 9 | ADTTE (OS), ADSL | RD.EFFICACY.SURVIVAL | ADTTE reconciliation; numerical results reconciliation; R primary output hash; SAS companion is out-of-DAG inventory only |
| F-11-2 | figure | Kaplan-Meier Progression-Free Survival | 09_tfl/output/figures/F-11-2_KM_PFS.png | present | SAP v4.0 section 10.1 | ADTTE (PFS), ADSL | RD.EFFICACY.SURVIVAL | ADTTE reconciliation; numerical results reconciliation; R primary output hash; SAS companion is out-of-DAG inventory only |
| F-12-1 | figure | Overall Survival Subgroup Forest Plot | 09_tfl/output/figures/F-12-1_Subgroup_Forest.png | present | SAP v4.0 section 8.2 | ADTTE (OS), ADSL covariates | RD.EFFICACY.SUBGROUP | ADTTE/ADSL reconciliation; forest HR reconciliation; R primary output hash; SAS companion is out-of-DAG inventory only |
| F-13-1 | figure | PSA Best Percentage Change from Baseline Waterfall | 09_tfl/output/figures/F-13-1_PSA_Waterfall.png | present | SAP v4.0 section 5.2 | ADLB (PSA), ADSL | RD.EFFICACY.PSA.RESPONSE | ADLB/ADSL reconciliation; R primary output hash; SAS companion is out-of-DAG inventory only |
| F-14-1 | figure | Treatment Exposure Duration Swimmer Plot | 09_tfl/output/figures/F-14-1_Swimmer_Plot.png | present | SAP v4.0 section 7.8 | ADEX, ADSL | RD.SAFETY.EXPOSURE | ADEX/ADSL reconciliation; R primary output hash; SAS companion is out-of-DAG inventory only |
| F-17-1 | figure | Project Optimus Exposure-Response Scatter | 09_tfl/output/figures/F-17-1_Optimus_Scatter.png | present | SAP v4.0 section 10 | ADEX (RDI), ADLB (ANC nadir) | RD.OPTIMUS.ER | ADEX/ADLB reconciliation; R primary output hash; SAS companion is out-of-DAG inventory only |
| T-11-6 | table | KM Analysis of Time to PSA Progression | 09_tfl/output/tables/T-11-Efficacy_Tables.txt | present | SAP v4.0 sections 4.3-5.3 | ADTTE | RD.EFFICACY.SECONDARY | ADTTE reconciliation; TFL generation gate; output hash |
| T-11-7 | table | KM Analysis of Time to Tumor Progression | 09_tfl/output/tables/T-11-Efficacy_Tables.txt | present | SAP v4.0 sections 4.3-5.3 | ADTTE, ADSL | RD.EFFICACY.SECONDARY | ADTTE/ADSL reconciliation; TFL generation gate; output hash |
| T-11-8 | table | Best Clinical Response Endpoints | 09_tfl/output/tables/T-11-Efficacy_Tables.txt | present | SAP v4.0 sections 4.3-5.3 | ADRS, ADLB, ADSL | RD.EFFICACY.SECONDARY | ADRS/ADLB/ADSL reconciliation; TFL generation gate; output hash |
| T-11-8b | table | Objective Response Rate - Response-Evaluable Denominator | 09_tfl/output/tables/T-11-Efficacy_Tables.txt | present | review-board SR-1 sensitivity trace | ADRS, ADSL | not currently mapped in ARM | ADRS/ADSL reconciliation; TFL generation gate; output hash |
| T-17-1 | table | Relative Dose Intensity Category Distribution | 09_tfl/output/tables/T-17-Optimus_Tables.txt | present | Project Optimus demonstration (program comments); not in current traceability table | ADEX, ADSL | not currently mapped in ARM | ADEX/ADSL reconciliation; TFL generation gate; output hash |
| T-17-2 | table | Worst Cycle ANC Nadir Grade by G-CSF Usage | 09_tfl/output/tables/T-17-Optimus_Tables.txt | present | Project Optimus demonstration (program comments); not in current traceability table | ADLB, ADSL | not currently mapped in ARM | ADLB/ADSL reconciliation; TFL generation gate; output hash |
| T-17-4 | table | Benefit-Risk Summary by RDI Tertile | 09_tfl/output/tables/T-17-Optimus_Tables.txt | present | Project Optimus demonstration (program comments); not in current traceability table | ADEX, ADLB, ADTTE | not currently mapped in ARM | ADEX/ADLB/ADTTE reconciliation; TFL generation gate; output hash |
| T-20-1 | table | Treatment-Emergent Adverse Events Summary | 09_tfl/output/tables/T-20-AE_Summary_Tables.txt | present | SAP v4.0 section 7 | ADAE, ADSL | RD.SAFETY.TEAE | ADAE/ADSL reconciliation; TFL generation gate; output hash |
| T-20-2 | table | Grade >=3 TEAEs by System Organ Class | 09_tfl/output/tables/T-20-AE_Summary_Tables.txt | present | SAP v4.0 section 7 | ADAE, ADSL | RD.SAFETY.TEAE | ADAE/ADSL reconciliation; TFL generation gate; output hash |
| T-21-1 | table | Baseline to Worst CTCAE Grade Shift - MP Arm | 09_tfl/output/tables/T-21-Lab_Shift_Tables.txt | present | SAP v4.0 section 7.5 | ADLB, ADSL | RD.SAFETY.LABSHIFT | ADLB/ADSL reconciliation; TFL generation gate; output hash |
| T-21-2 | table | Baseline to Worst CTCAE Grade Shift - CbzP Arm | 09_tfl/output/tables/T-21-Lab_Shift_Tables.txt | present | SAP v4.0 section 7.5; synthetic comparator demonstration | ADLB, ADSL | not currently mapped in ARM | TFL generation gate; output hash; comparator is synthetic |

## Table IDs Extracted From Bundled Text Outputs

| File | Detected IDs |
| --- | --- |
| 09_tfl/output/tables/T-11-Efficacy_Tables.txt | T-11-6, T-11-7, T-11-8, T-11-8b |
| 09_tfl/output/tables/T-17-Optimus_Tables.txt | T-17-1, T-17-2, T-17-4 |
| 09_tfl/output/tables/T-20-AE_Summary_Tables.txt | T-20-1, T-20-2 |
| 09_tfl/output/tables/T-21-Lab_Shift_Tables.txt | T-21-1, T-21-2 |

## SAS Companion Figures (out-of-DAG inventory)

| ID | SAS companion file | Presence | Scope | Freshness | mtime UTC | SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| F-11-1 | 09_tfl/output/figures/sas/F-11-1_KM_OS_SAS.png | present | out_of_dag_capability_demo | stale_or_historical | 2026-07-05T13:34:06.208066+00:00 | 7406c29293a13c35679a08b6bfc964aba0d61a73a76b8384e49705f4664d6d20 |
| F-11-2 | 09_tfl/output/figures/sas/F-11-2_KM_PFS_SAS.png | present | out_of_dag_capability_demo | stale_or_historical | 2026-07-05T13:34:09.839750+00:00 | 2f848c65eb63aab245854c35e311096108af3ebda9fc19bb0d138c02f47bfe8b |
| F-12-1 | 09_tfl/output/figures/sas/F-12-1_Subgroup_Forest_SAS.png | present | out_of_dag_capability_demo | stale_or_historical | 2026-07-05T13:34:13.463488+00:00 | bf1638c789be3a67eb792ee8c6fbab62244778c887eadd2c9c3d404fb303df1e |
| F-13-1 | 09_tfl/output/figures/sas/F-13-1_PSA_Waterfall_SAS.png | present | out_of_dag_capability_demo | stale_or_historical | 2026-07-05T13:34:17.309513+00:00 | b5d6404b20d52e22c914f16528f1b821fe76451131bcf3470ab73b009714a189 |
| F-14-1 | 09_tfl/output/figures/sas/F-14-1_Swimmer_Plot_SAS.png | present | out_of_dag_capability_demo | stale_or_historical | 2026-07-05T13:34:21.047489+00:00 | b45ab94962c6ada32fdf6c9c42d313d3d88840ec720965ec748f5026d18bee3b |
| F-17-1 | 09_tfl/output/figures/sas/F-17-1_Optimus_Scatter_SAS.png | present | out_of_dag_capability_demo | stale_or_historical | 2026-07-05T13:34:24.574427+00:00 | 9dd9956ac9512af691e688767a8dae4bf056c5151b6ec9accaa3cbd1c0db1320 |

## Primary Output Hashes

| ID | File | SHA-256 |
| --- | --- | --- |
| F-01-1 | 09_tfl/output/figures/F-01-1_CONSORT_Disposition.png | bb6be311604e1ebf5f4c98c4fd6abeeb6177d149b7ba84d323f8442c35631b29 |
| F-11-1 | 09_tfl/output/figures/F-11-1_KM_OS.png | 18d41117d0187692c5d81a4c892794509cb75533a07f96d6c61ea5cd2b7e212e |
| F-11-2 | 09_tfl/output/figures/F-11-2_KM_PFS.png | a0c8bf8ec86ee5101af604a633376bdae5698d69e5b94f3c9cf2939675f4a3ae |
| F-12-1 | 09_tfl/output/figures/F-12-1_Subgroup_Forest.png | 7a61cc2fcda86bcb1787f045597973d436972df1cc6ec3ae1a7ca0662682d0ab |
| F-13-1 | 09_tfl/output/figures/F-13-1_PSA_Waterfall.png | ba1a25947a9db79dd714d285237ce1f3f7befac412b1c7e9cf6545f3f1c1a79c |
| F-14-1 | 09_tfl/output/figures/F-14-1_Swimmer_Plot.png | 0a4b230c0cc57b8f3762c1f8e5aaf8140779a525459b020885420ec1d24146b6 |
| F-17-1 | 09_tfl/output/figures/F-17-1_Optimus_Scatter.png | d579a8d94aff6ec9829c172f15d6f15a7b36327569ff00fcd9d0dcc8510978cc |
| T-11-6 | 09_tfl/output/tables/T-11-Efficacy_Tables.txt | 604d9d447b1ec148c19d3266ce3e36b8afeb70a04135f8788cf5c826e70c252c |
| T-11-7 | 09_tfl/output/tables/T-11-Efficacy_Tables.txt | 604d9d447b1ec148c19d3266ce3e36b8afeb70a04135f8788cf5c826e70c252c |
| T-11-8 | 09_tfl/output/tables/T-11-Efficacy_Tables.txt | 604d9d447b1ec148c19d3266ce3e36b8afeb70a04135f8788cf5c826e70c252c |
| T-11-8b | 09_tfl/output/tables/T-11-Efficacy_Tables.txt | 604d9d447b1ec148c19d3266ce3e36b8afeb70a04135f8788cf5c826e70c252c |
| T-17-1 | 09_tfl/output/tables/T-17-Optimus_Tables.txt | 7c290565a964082d5ae40a31879725da904e540c98b6284464a0f8a0523fcfe2 |
| T-17-2 | 09_tfl/output/tables/T-17-Optimus_Tables.txt | 7c290565a964082d5ae40a31879725da904e540c98b6284464a0f8a0523fcfe2 |
| T-17-4 | 09_tfl/output/tables/T-17-Optimus_Tables.txt | 7c290565a964082d5ae40a31879725da904e540c98b6284464a0f8a0523fcfe2 |
| T-20-1 | 09_tfl/output/tables/T-20-AE_Summary_Tables.txt | f37d6417825f58e95aaacf9d28bd5efcdf6ec9f4a5dd7c3c0c244baa52c98651 |
| T-20-2 | 09_tfl/output/tables/T-20-AE_Summary_Tables.txt | f37d6417825f58e95aaacf9d28bd5efcdf6ec9f4a5dd7c3c0c244baa52c98651 |
| T-21-1 | 09_tfl/output/tables/T-21-Lab_Shift_Tables.txt | 0aae63086e20c0d6905908542d979d5cebe3f89f0213ce3113a7ce56fe78ca92 |
| T-21-2 | 09_tfl/output/tables/T-21-Lab_Shift_Tables.txt | 0aae63086e20c0d6905908542d979d5cebe3f89f0213ce3113a7ce56fe78ca92 |

## Control Exceptions

No unindexed physical output files were detected.


No table IDs were detected in text outputs without catalog coverage.


All catalog table IDs were detected in their bundled text files.

## Disclosure

Comparative CbzP output content is synthetic/reconstructed demonstration content where applicable. The index preserves that disclosure by linking output control to ADRG/README limitations rather than representing comparative outputs as independent clinical evidence. Deferred SAP full-catalog IDs are **not** silent gaps: they are explicit non-commitments in `tfl_output_catalog.yaml` until implemented under approved shells and QC.

## Machine-Readable Outputs

- `tfl_output_catalog.yaml` (controlled scope authority)
- `06_telemetry/tfl_output_index/tfl_output_index.csv`
- `06_telemetry/tfl_output_index/tfl_output_index.json`
- `06_telemetry/tfl_output_index_status.json`
