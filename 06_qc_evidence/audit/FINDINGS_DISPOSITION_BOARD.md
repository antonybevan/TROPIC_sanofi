# TROPIC Findings Disposition Board

**Date:** 2026-08-03
**Product claim:** Controlled **non-submission demonstration** programming pipeline  
**Authority:** SAP v4.0 locked for remediation (`06_qc_evidence/audit/SAP_LOCK_REVIEW_MEMO.md`); not sponsor-approved for filing  

> Purpose: classify every active Critical/Major finding before and after a full ODA seal run, so the DAG proves a stable release scope rather than rediscovering open science/scope debt.

> **2026-08-03 remediation update:** The corrected full real-SAS DAG completed 34/34 stages GREEN. F-011 now excludes the one ADSL fallback baseline PSA (MP 61/329; CbzP 145/361). Section 3 corrected TTUMOR death-milestone censoring, PFS last-evaluable/no-post-baseline censoring, and ADTTE composite event labels. The PFS pain/supporting-disease and palliative-RT decision remains an explicitly accepted Path A residual. F-012 remains an explicit non-submission demonstration limit: combined N=749 is not protocol ITT N=755.

## Disposition classes

| Class | Meaning | Register status |
|---|---|---|
| `resolve_now` | Inside controlled release claim; correct or regenerate evidence before seal | → `RESOLVED` when fixed |
| `scope_out_with_disclosure` | Real residual, but outside this product cut; must stay visible in ADRG/SDRG/README | → `ACCEPTED` |
| `external_dependency` | Needs sponsor IDs, P21 license, full IPD, org Part 11 program, etc. | → `ACCEPTED` |
| `non_submission_demo_limit` | Structural to portfolio demo provenance; cannot become submission-grade in this repo | → `ACCEPTED` |

## Board (Critical / Major active set)

| ID | Sev | Class | Decision | Rationale |
|---|---|---|---|---|
| **F-003** | Critical | `non_submission_demo_limit` | **ACCEPTED** | Synthetic/Guyot CbzP is TFL-only by design; comparative claims are non-confirmatory. Controlled by README/ADRG/TFL banners/`config/tfl_output_catalog.yaml`. |
| **F-005** | Critical | `external_dependency` + `non_submission_demo_limit` | **ACCEPTED** | EXAMPLE app IDs; **source CRF PDF exists** but full **aCRF** package not claimed. eCTD remains structure demo. CRF domain grounding = D-012 (separate). |
| **F-026** | Major | `scope_out_with_disclosure` | **ACCEPTED** | ~1134 BASELINE AE rows are skeleton (terms present, AESER/AEREL/AEOUT blank). TEAE blank AESER ≈0–1. Documented ADRG §4B; soft QC in ADAE. Do not invent AESER. |
| **F-027** | Minor | `scope_out_with_disclosure` | **ACCEPTED** | ALB/LDH not on Sanofi CRF LABH/LABB panels and not in PDS LB — Class C; ADSL placeholders remain Assigned (not “PDS stripped collected labs”). |
| **F-028** | Major | `scope_out_with_disclosure` | **ACCEPTED** | One subject has EXTRT=XRP6258 (10 cycles) while DM.ARM is MITOXANTRONE for all 371. Arm authority = DM/ADSL; do not re-code EX. SDTM E2E 2026-07-09. |
| **F-011** | Major | `resolve_now` | **RESOLVED** | T-11-8 now uses observed baseline PSA >=20 (excluding `PSABLIF='Y'` fallback values; CbzP 145/361; MP 61/329); the set is shared by the R output, SAS companion, and regression contract. |
| **F-039** | Major | `resolve_now` | **RESOLVED** | Stage-14 SAS companions are current-run evidence: UTC health timestamps plus bounded same-run mtime ordering produce a PASS index with zero stale/missing companions. |
| **F-012** | Major | `non_submission_demo_limit` | **ACCEPTED** | N=749 = real MP 371 + synthetic CbzP 378; protocol ITT 755 needs full two-arm IPD. Figures must not be read as original-trial ITT. |
| **F-014** | Major | `scope_out_with_disclosure` | **ACCEPTED** | ARM has 8 displays/10 analyses for controlled TFL core; full ADSL covariate declarations and every deferred SAP display remain backlog. Controlled catalog limits the claim. |
| **F-015** | Major | `external_dependency` + `scope_out_with_disclosure` | **ACCEPTED** | Full CORE breadth on every SDTM domain + residual issue disposition is a conformance program beyond current targeted SDTMIG 3.4 run. Known residuals stay in CORE run records/SDRG. |
| **F-016** | Major | `external_dependency` | **ACCEPTED** (was UNVERIFIED) | Official P21/ADaM commercial rule pack not available in-repo. Local CORE ADaM rules + spec→data gates are the controlled substitute; not claimed as full P21. |
| **F-017** | Major | `scope_out_with_disclosure` | **ACCEPTED** | Partial ISO dates and TSSEQ are **source PDS precision** limitations (SDRG §2/§5), not silent programming bugs. Carried as known data limitation. |
| **F-019** | Major | `resolve_now` + residual demo | **RESOLVED** (docs) / SAP signatures **ACCEPTED** | Guyot vs PH language reconciled in REPRODUCIBILITY/ADRG; OCCDS is v1.0 + custom extension (no OCCDS v1.1). Blank SAP signature blocks = non-submission demo limit. |
| **F-020** | Major | `resolve_now` + `scope_out_with_disclosure` | **RESOLVED** (hardening) / residual **ACCEPTED** | Dataset-JSON hardened for zero-input fail + key/MDV fixes where applicable; layer remains **exploratory exchange**, not eCTD consumer. |
| **F-021** | Major | `resolve_now` + `scope_out_with_disclosure` | **RESOLVED** (deterministic CT) / residual **ACCEPTED** | USDM uses deterministic IDs + declared CT version; still **exploratory**, not packaged for submission. |
| **F-022** | Major | `scope_out_with_disclosure` | **ACCEPTED** | ARS covers controlled primary/secondary survival displays; full SAP/TFL ARS coverage and eCTD consumer deferred with controlled TFL catalog. |
| **F-023** | Major | `resolve_now` | **RESOLVED** | TRACEABILITY_MATRIX corrected (ADCM keys, T-17, stage count/orchestration). |
| **F-025** | Major | `non_submission_demo_limit` | **ACCEPTED** (was UNVERIFIED) | Hash seals ≠ Part 11. Product is explicitly non-Part-11 until org CSV program exists. |
| **F-040** | Major | `resolve_now` | **RESOLVED** | ADTTE TTUMOR censoring now excludes DS death milestones and baseline-only records; final output has zero death-date TTUMOR censors. Evidence: `SECTION_03_ADAM_DERIVATION_AUDIT_2026-08-03.md`. |
| **F-041** | Major | `resolve_now` | **RESOLVED** | PFS now uses the latest valid post-baseline RECIST/PSA/evaluable-pain assessment, or randomization when none exists; NACT remains priority. SAS/R/admiral agree after the final 34-stage run. |
| **F-042** | Major | `scope_out_with_disclosure` | **ACCEPTED** | The sealed pain rule is reproducible but non-conforming in thresholds, AS summary, confirmation, event dating and CM/PR use. The ED-01–ED-07 package specifies the corrected pain rule, CM+PR union, sensitivities, TTUMOR ITT and SAP-native T-11 mapping. Under the disclosed one-person Path A model, implementation requires accountable-author sign-off, separately programmed SAS/R reconciliation, delayed second-pass review and reseal. This is not independent, sponsor, medical, or regulated approval. |

## Minor (not RC Crit/Major gate)

| ID | Decision |
|---|---|
| **F-024** | Keep CONFIRMED as living orphan register hygiene; not a G06 Crit/Major blocker. |

## Release-candidate implication

After this board:

- **No active `CONFIRMED` Critical/Major** remain for the RC findings gate (they are `RESOLVED` or `ACCEPTED`).
- **ACCEPTED ≠ fixed for filing** — they are formal scope decisions for the demo product.
- Full ODA DAG may proceed as a **proof run** of the orchestrator against this frozen disposition, not as discovery of open Crit/Major science.

## Required on-record disclosures (must remain true)

1. CbzP comparative outputs are synthetic/reconstructed, non-confirmatory.  
2. eCTD uses EXAMPLE identifiers and is not a real FDA sequence.  
3. No Part 11 validated system claim.  
4. Controlled TFL catalog is the release output universe (`config/tfl_output_catalog.yaml`).  
5. P21 commercial ADaM pack and full SDTM CORE residual disposition are external/backlog.  

## Next after board

1. Keep register and board synchronized with every remediation cut.
2. Preserve the explicit non-submission disclosures (especially F-003/F-005/F-012/F-025).
3. Rebuild the RC checklist and release-run manifest after the clean commit; a dirty worktree remains the only current seal blocker.
