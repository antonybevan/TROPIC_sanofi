# TROPIC Release Note — `v0.2.0-portfolio`

**Product:** Controlled clinical-biometrics programming portfolio  
**Study:** EFC6193 / XRP6258 (TROPIC, NCT00417079)  
**Release class:** Path A controlled non-submission demonstration  
**Release date:** 2026-08-04  
**Regulated-use status:** **NO-GO**

## Verdict

`v0.2.0-portfolio` is the professionally reviewed successor to the historical
`v0.1.0-demo-rc.1` baseline. It is suitable for portfolio and interview review
within the binding Path A claim. It is not an FDA submission, sponsor-approved
analysis, independent clinical confirmation, validated Part 11 system, or source
of patient-care evidence.

The release is valid only at a commit where:

- the 34-stage DAG is GREEN under real SAS (`oda` or local);
- SAS/R, admiral, results, forest, and figure-data reconciliations pass;
- the exact subject-level `F042_PAIN_RESPONSE` control passes;
- metadata, Define-XML/ARM, TFL catalog, log, package, and reviewer gates pass;
- the release-run manifest has `release_candidate` evidence grade; and
- `python3 scripts/verify_release.py` passes on the committed seal set.

## Material improvements since `v0.1.0-demo-rc.1`

1. Endpoint governance was brought onto SAP v4.0, including the native
   `T-11-3` through `T-11-8` mapping, ITT-primary TTUMOR, and the adopted
   component-specific pain algorithm.
2. A major SAS T-11-5 validation defect was found by governance review and
   corrected. Exact subject-level SAS/R pain-response parity is now release
   blocking; the correct real-MP result is 43/153 (28.1%).
3. Define-XML/ARM now represents every controlled analysis output except the
   non-analysis F-01-1 flow diagram: 10 ResultDisplays and 18 AnalysisResults.
   TTPAIN, response and Optimus results, survival covariates, TFL bindings, and
   Path A limitations are machine checked.
4. The ADaM specification workbook received a professional presentation pass
   and expanded endpoint where-clause coverage without changing the 7-dataset,
   159-variable governed model.
5. The controlled catalog now contains 21 in-scope outputs and 18 explicitly
   deferred SAP outputs. All four table bundles and seven primary figures were
   audited; clipped titles/disclosures and non-estimable/p-value formatting
   were corrected.
6. Reviewer-facing traceability, findings dispositions, workstream records, and
   package artifacts were synchronized to the current implementation.

## Evidence anchors

| Artifact | Review purpose |
|---|---|
| `platform/pipeline_health.json` | Current real-SAS run identity and 34-stage result |
| `platform/release_run_manifest/release_run_manifest.json` | Hash-bound release evidence |
| `platform/release_candidate/release_candidate_status.json` | Path A release checklist |
| `scripts/verify_release.py` | Offline verification of the committed seals |
| `platform/define_arm_contract.py` | Executable Define-XML/ARM claim contract |
| `docs/TFL_OUTPUT_INDEX.md` | 21-output controlled physical/index trace |
| `06_qc_evidence/audit/section_reviews/SECTION_05_PORTFOLIO_FINALIZATION_AUDIT_2026-08-04.md` | Final section-by-section technical disposition |
| `docs/workstreams/reviews/PATH_A_STATISTICAL_GOVERNANCE_ASSESSMENT_2026-08-04.md` | Statistical-governance assessment and authority boundary |

## Honesty boundary

- The MP arm is real de-identified source-derived data; patient data are not
  redistributed in Git.
- The CbzP arm is synthetic/reconstructed and TFL-only. OS/PFS use digitized
  Guyot reconstruction; secondary TTE comparisons are PH-scaled and circular by
  construction.
- Combined N=749 is a demonstration cohort, not the protocol ITT N=755.
- EXAMPLE application identifiers and a source CRF do not constitute a real
  filing identity or complete aCRF package.
- Commercial P21 ADaM validation, organizational two-programmer QC, sponsor
  document control, medical approval, Part 11 validation, and electronic
  signatures are not claimed.

## Reviewer re-check

```bash
python3 scripts/verify_release.py
python3 platform/define_arm_contract.py
python3 -m pytest -q
```

The annotated tag `v0.2.0-portfolio` is created only after the PR head and the
committed release seal pass CI.
