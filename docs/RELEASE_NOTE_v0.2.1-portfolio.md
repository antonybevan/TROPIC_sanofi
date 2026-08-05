# TROPIC Release Note — `v0.2.1-portfolio`

**Product:** Controlled clinical-biometrics programming portfolio
**Study:** EFC6193 / XRP6258 (TROPIC, NCT00417079)
**Release class:** Path A controlled non-submission demonstration
**Release date:** 2026-08-05
**Predecessor:** `v0.2.0-portfolio` (immutable historical release)
**Regulated-use status:** **NO-GO**

## Verdict

`v0.2.1-portfolio` is the audit-closure successor to `v0.2.0-portfolio`. It is
suitable for portfolio and interview review within the binding Path A claim. It
is not an FDA submission, sponsor-approved analysis, independent clinical
confirmation, validated Part 11 system, or source of patient-care evidence.

The release is valid only at a commit where:

- the 34-stage DAG is GREEN under real SAS (`oda` or local);
- SAS/R, admiral, results, forest, and figure-data reconciliations pass;
- the exact subject-level `F042_PAIN_RESPONSE` control passes (43 records / 43
  subjects; 43/153 response-evaluable MP set; ITT N=371);
- metadata, Define-XML/ARM, TFL catalog, log, package, and reviewer gates pass;
- the release-run manifest has `release_candidate` evidence grade; and
- `python3 scripts/verify_release.py` passes on the committed seal set.

## Audit-closure changes since `v0.2.0-portfolio`

1. Current-facing scope and release references were synchronized to the
   authoritative catalog: **21 controlled output IDs / 18 explicitly deferred
   SAP IDs**. The binding product claim, reviewer guides, traceability matrix,
   workstream board, package README, and navigation index now agree.
2. Define-XML/ARM wording was corrected to the live contract: **10
   ResultDisplays / 18 AnalysisResults**. The reviewer-guide and CSR PDFs were
   regenerated from their controlled Markdown sources and repackaged.
3. The pre-adoption Section 2–4 and F-042 decision records now carry explicit
   historical-baseline notices. Their closure addenda remain the current
   implementation authority; no historical evidence was silently rewritten.
4. F-042 is synchronized across the findings register, disposition board, and
   reviewer-facing records: the adopted CM+PR/pain implementation, full ODA
   rerun, delayed second pass, exact subject-level gate, release reseal, and CI
   verification are complete for Path A. External qualified statistical/medical
   review remains required.
5. F-043 is resolved: abort telemetry now preserves the complete manifest stage
   map and reports `partial_dag` with `stages_not_run` for truncated runs; the
   historical failed-run record is retained.
6. Release identity is explicit. `v0.2.1-portfolio` remains immutable at its
   original tag; the post-release pipeline-integrity and governance closure is
   recorded by the successor `v0.2.2-portfolio` note. No prior tag is moved.

## Evidence anchors

| Artifact | Review purpose |
|---|---|
| `platform/pipeline_health.json` | Current real-SAS run identity and 34-stage result |
| `platform/release_run_manifest/release_run_manifest.json` | Hash-bound release evidence |
| `platform/release_candidate/release_candidate_status.json` | Path A release checklist |
| `scripts/verify_release.py` | Offline verification of the committed seals |
| `platform/define_arm_contract.py` | Executable Define-XML/ARM claim contract |
| `docs/TFL_OUTPUT_INDEX.md` | 21-output controlled physical/index trace |
| `06_qc_evidence/audit/FINDINGS_DISPOSITION_BOARD.md` | F-042/F-043 dispositions and residual boundary |
| `06_qc_evidence/audit/section_reviews/SECTION_05_PORTFOLIO_FINALIZATION_AUDIT_2026-08-04.md` | Section-by-section technical disposition |
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

The annotated tag `v0.2.1-portfolio` remains an immutable historical release.
The subsequent governance-hardening release is `v0.2.2-portfolio`; predecessor
tags are not moved.
