# SAP Lock Review Memo

**Project:** TROPIC / EFC6193 clinical programming pipeline
**SAP reviewed:** `TROPIC_SAP_v4.0_industry_grade.docx`
**Review date:** 2026-06-25
**Reviewer posture:** clinical programming / data standards lock-gate review

## 1. Lock verdict

| Decision | Verdict | Rationale |
|---|---:|---|
| Use SAP v4.0 as internal remediation authority | **PASS** | The SAP contains the required control spine for remediation: source hierarchy, real-vs-synthetic data separation, estimands, populations, endpoint algorithms, TFL catalog control, CDISC metadata requirements, dual-programming gates, release gates and audit closure checklist. |
| Treat SAP v4.0 as sponsor-approved / regulatory-submission SAP | **FAIL** | The document is a controlled draft, not signed by sponsor/statistician/QC/clinical/data-standards owners. Critical audit findings remain open, including eCTD integrity, SDTM metadata drift, synthetic-comparator claim risk, false listing and placeholder submission metadata. |
| Proceed with audit remediation using SAP v4.0 | **PASS WITH CONDITIONS** | Proceed if all downstream fixes explicitly cite SAP v4.0 sections and maintain the rule that reconstructed CbzP data are non-confirmatory until complete authoritative two-arm IPD and approval exist. |

Bottom line: **lock SAP v4.0 for remediation execution, not for submission use.**

## 2. Evidence checked

| Evidence item | Result |
|---|---|
| SAP file exists | `/Users/apple/Desktop/TROPIC/TROPIC_SAP_v4.0_industry_grade.docx` |
| Reproducible builder exists | `/Users/apple/Desktop/TROPIC/audit/build_industry_sap_v4.py` |
| Rendered QA evidence exists | `audit/sap_v40_render/TROPIC_SAP_v4.0_industry_grade.pdf`; `audit/sap_v40_render/contact_sheet.png` |
| Rendered page count | 22 pages |
| Structural content | 239 paragraphs, 40 tables, 59 headings |
| Required control language | Present: controlled draft, not original Sanofi SAP, synthetic/non-confirmatory policy, real MP layer, estimands, TFL catalog, dual-programming, release gates, Part 11 caveat, Critical audit checklist |
| Audit register status | 25 findings: 5 Critical, 19 Major, 1 Minor |

## 3. Remaining SAP assumptions to carry forward

1. **Authority status:** SAP v4.0 is an internal controlled programming SAP draft. It is not sponsor-approved until signatures and document-control evidence exist.
2. **Data availability:** the repository’s executable real patient-level layer is MP/control-arm only. CbzP is reconstructed/synthetic unless complete authoritative CbzP IPD is supplied.
3. **Inference status:** comparative CbzP-vs-MP outputs using reconstructed CbzP are demonstration/non-confirmatory outputs only.
4. **Trial target:** original TROPIC ITT remains 755 subjects: 377 MP and 378 CbzP. Repo combined N=749 must not be labeled original trial ITT.
5. **Standards posture:** SAP v4.0 references current 2026 FDA/CDISC/ICH expectations, but conformance is not proven until final package validation is rerun and issues are dispositioned.
6. **Part 11 posture:** Git provenance is not enough. The pipeline remains non-Part-11 for regulated claims until validated-system, access-control, audit-trail, e-signature and SOP evidence exists.

## 4. Audit finding to SAP control map

| Finding | Severity | SAP v4.0 control section(s) | Lock disposition |
|---|---:|---|---|
| F-001 eCTD integrity | Critical | 16, 18, Appendix J | Must fix before any package/submission claim. |
| F-002 SDTM metadata/data drift | Critical | 15, 16, 18, Appendix J | Must fix before Define/SDTM release. |
| F-003 synthetic data validity | Critical | 4, 7, 17, 18 | SAP now controls this; outputs must be relabeled or replaced. |
| F-004 false clinical listing | Critical | 11.4, 17, Appendix J | Current listing must be removed/regenerated from source. |
| F-005 submission placeholders | Critical | 16, 18, Appendix J | Must replace real submission metadata/CRF or block package generation. |
| F-006 TLF numerical correctness | Major | 11.3, 14, 16, 17 | Fix lab shift selection and arithmetic gates. |
| F-007 dual-programming validity | Major | 6.3, 16, 16.1 | Remove lossy normalization and rerun exact SAS/R reconciliation. |
| F-008 ADaM metadata/data drift | Major | 15, 16, Appendix C/I | Rebuild metadata and XPT/Define alignment. |
| F-009 provenance / audit trail | Major | 6.3, 16, 16.1 | Build signed/hash-bound run manifest. |
| F-010 SAP/TFL scope | Major | 17, 17.1, Appendix D | Implement missing outputs or amend catalog. |
| F-011 analysis population | Major | 5, 10.2, 17 | Apply PSA eligibility denominator. |
| F-012 population inconsistency | Major | 4, 5, 17 | Stop labeling synthetic N=749 as trial ITT. |
| F-013 variable traceability | Major | 15, Appendix C/I | Populate predecessor/method/document references. |
| F-014 ARM traceability | Major | 15, 17 | Fix ResultDisplay/analysis dataset-variable links. |
| F-015 conformance coverage | Major | 15, 16 | Run final supported rules across all delivered datasets. |
| F-016 ADaM conformance | Major | 15, 16 | Run current supported ADaM validator/P21 profile. |
| F-017 SDTM timing / sequence | Major | 14, 15 | Correct partial/dirty date and sequence handling. |
| F-018 log cleanliness | Major | 6.3, 16, 16.1 | Fail build on unapproved log issues. |
| F-019 document contradiction / approval | Major | 1, 2, 4, 18 | SAP v4 resolves policy; reviewer guides must be regenerated. |
| F-020 Dataset-JSON lifecycle | Major | 15, 16 | Align/remove Dataset-JSON layer before release. |
| F-021 USDM reproducibility / CT | Major | 15, 16 | Stabilize IDs/schema/CT or classify exploratory. |
| F-022 ARS completeness | Major | 15, 17 | Complete or remove ARS regulatory delivery claim. |
| F-023 traceability matrix defects | Major | 15, 16, 17 | Regenerate from authoritative manifests. |
| F-024 dead/orphan artifacts | Minor | 16, 17 | Remove/archive/integrate orphaned artifacts. |
| F-025 Part 11 controls | Major | 1, 6.3, 16, 18 | Remains unverified until governed execution evidence exists. |

## 5. Remediation order

### Phase 0 - Lock baseline

1. Mark SAP v4.0 as the working remediation authority.
2. Add document-control note in README/reviewer guides: SAP v4.0 is approved for remediation execution only, not submission use.
3. Freeze existing audit outputs and retain current SAP builder/render evidence.

### Phase 1 - Close Critical blockers

1. **F-003 synthetic data validity:** relabel or segregate every reconstructed CbzP comparative output as non-confirmatory; prevent any reviewer guide/TFL/eCTD language from implying real two-arm clinical evidence.
2. **F-004 false listing:** remove the fabricated discontinuation listing from package outputs; regenerate only from ADSL/DS/EX with independent QC.
3. **F-002 SDTM drift:** make the packaged SDTM layer match declared SDTMIG/Define metadata; rerun metadata/data comparison.
4. **F-001 eCTD integrity:** rebuild eCTD atomically; fail on unindexed payloads or missing leaves.
5. **F-005 placeholders:** replace placeholder regional/submission metadata and annotated CRF or block package generation.

### Phase 2 - Repair analysis correctness and catalog control

1. Fix lab-shift denominator logic and arithmetic assertions (F-006).
2. Fix PSA response eligible population (F-011).
3. Correct ITT/population displays and synthetic N=749 labeling (F-012).
4. Reconcile SAP/TFL catalog: implement missing planned outputs or formally amend catalog; remove extras not cataloged (F-010).

### Phase 3 - Repair metadata, traceability and validation spine

1. Populate ADaM predecessor/method/document metadata (F-013).
2. Rebuild ADaM spec -> XPT -> Define-XML concordance (F-008).
3. Fix ARM display/dataset/variable links (F-014).
4. Regenerate traceability matrix from authoritative manifests (F-023).
5. Fix dual-language comparison so SAS/R divergence cannot be hidden by normalization (F-007).

### Phase 4 - Rebuild conformance and provenance gates

1. Add signed/hash-bound run manifest and package hash binding (F-009).
2. Enforce clean SAS/R logs (F-018).
3. Run final SDTM/ADaM/Define validators and disposition issues (F-015, F-016).
4. Decide whether Dataset-JSON, USDM and ARS are in validated scope or exploratory only (F-020, F-021, F-022).
5. Resolve orphan/dead artifacts (F-024).

### Phase 5 - Regulated-process evidence

1. Define Part 11 posture and evidence requirements (F-025).
2. Add SOP/process evidence, role-based approval, audit-trail retention and electronic-signature controls before any regulated claim.
3. Obtain human owner approvals for SAP and reviewer guides.

## 6. Final lock recommendation

Proceed with remediation using SAP v4.0 as the controlling analysis/programming baseline.

Do **not** proceed to submission-readiness claims, package release, or “validated pipeline” language until:

- all Critical findings are closed,
- open Major findings are closed or formally risk-accepted,
- SAP v4.0 has human approvals,
- final conformance and dual-programming evidence are regenerated from a clean run,
- and package integrity is rebuilt from current outputs with hash-bound evidence.
