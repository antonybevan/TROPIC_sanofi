# Section 0 — Governance and SAP Consistency Audit

**Audit date:** 2026-08-03  
**Audit scope:** product claim, SAP authority, findings disposition, release evidence, workstream control surfaces  
**Audit baseline:** `d32b04d` on `codex/submission-pipeline-rc`  
**Product path:** Path A — controlled non-submission demonstration  
**Decision:** **PASS WITH DOCUMENTED LIMITATIONS** — the analytical release baseline is green, current control documents have been synchronized, and a successor Path A release is still gated on the remaining section audits.

## 1. Authority order

The following order controls conflicts during the section-by-section audit:

| Rank | Authority | Decision rule |
|---:|---|---|
| 1 | [`docs/PRODUCT_CLAIM.md`](../../../docs/PRODUCT_CLAIM.md) | Defines what this repository may claim publicly. |
| 2 | [`02_specifications/sap/TROPIC_SAP_v4.0_industry_grade.docx`](../../../02_specifications/sap/TROPIC_SAP_v4.0_industry_grade.docx) | Governs programming intent for remediation; it is not sponsor-approved filing SAP. |
| 3 | [`SAP_LOCK_REVIEW_MEMO.md`](../SAP_LOCK_REVIEW_MEMO.md) | Confirms SAP v4.0 is usable as remediation authority and records its submission limitations. |
| 4 | [`FINDINGS_DISPOSITION_BOARD.md`](../FINDINGS_DISPOSITION_BOARD.md) | Defines which residuals are resolved, accepted, external, or outside Path A. |
| 5 | `config/study_manifest.yaml`, `config/study_config.yaml`, and `config/tfl_output_catalog.yaml` | Define executable scope and the controlled output universe. |
| 6 | Machine evidence (`platform/pipeline_health.json`, reconciliation/QC status, release manifest) | Proves the current run of the controlled scope; it does not expand the product claim. |
| 7 | Reviewer guides and presentation documents | Explain the package and must not exceed ranks 1–6. |

Historical release notes remain historical records. They are not rewritten to make a later run look as if it occurred on the historical tag.

## 2. Baseline facts checked

| Control | Observed value | Verdict |
|---|---|---|
| Branch | `codex/submission-pipeline-rc` | PASS |
| Baseline commit | `d32b04d` | PASS |
| SAS execution | `oda` | PASS |
| Pipeline scope | `full_dag` | PASS |
| Stage completeness | 34 expected / 34 recorded / 0 not run | PASS |
| Pipeline health | `GREEN` | PASS |
| Release-run manifest | `PASS`, `release_candidate`, generated 2026-08-01 17:54:46 UTC | PASS |
| Release-candidate checklist | 17 checks / 17 pass / 0 warning / 0 blocker | PASS after synchronization |
| Static release verification | 30/30 checks passed | PASS |
| Confirmed active Critical/Major findings | 0; accepted residuals remain on record | PASS for Path A; not filing closure |
| Product boundary | Controlled non-submission demo; synthetic CbzP; EXAMPLE eCTD; non-Part-11 | PASS |
| SAP status | Remediation authority, not sponsor-approved submission SAP | PASS |

The 34-stage count is taken from the current `platform/pipeline_health.json` stage map, which includes the G00 governance lock, G02 specification lock, G07 reviewer-package lock, and release-manifest binding.

## 3. Dot-connection matrix

| Connection | Evidence checked | Verdict | Follow-up |
|---|---|---|---|
| Product claim → README / reviewer-facing language | `PRODUCT_CLAIM.md`, `README.md`, package README, known-differences memo | PASS with factual count correction | Keep Path A wording; do not use “submission-ready”. |
| SAP v4.0 → lock memo → executable G00/G02 controls | SAP lock memo, `config/study_manifest.yaml`, current health stage map | PASS | Section 2 will test individual population/endpoint rules. |
| Real MP vs reconstructed CbzP boundary → package/TFL disclosures | Product claim, findings board, ADRG/SDRG and TFL catalog | PASS for Path A | Re-check in the source/provenance and TFL sections. |
| Findings register → disposition board → release gate | `findings_register.csv`, disposition board, RC checklist | PASS for Path A | Accepted is not equivalent to filing closure. |
| Full run → release manifest → RC checklist → verifier | Current health and manifest; regenerated RC status/checklist; verifier | PASS after synchronization | RC status now points to manifest seal `070232617a258217662d056a7471b28bd3c4e081d612ae509518a76696f67230`. |
| Workstream Markdown board → YAML board → CI reality | `docs/WORKSTREAM_EXECUTION_BOARD.md`, `config/workstream_execution_board.yaml`, `.github/workflows/ci.yml` | PASS after synchronization | Current branch/count and gate wiring agree; substantive scope risks remain for later section audits. |
| Historical tag note → historical tag | `docs/RELEASE_NOTE_v0.1.0-demo-rc.1.md` | PASS as historical record | Do not rewrite; issue a successor release note after the audit. |

## 4. Corrective actions in this slice

1. **DONE** — Correct current 30-stage references to 34 stages where the document describes the present pipeline.
2. **DONE** — Record the current audit baseline and current release facts in the workstream board.
3. **DONE** — Remove obsolete statements that G02, G07, or CI release verification are unwired; retain substantive scope limitations for later section audits.
4. **DONE** — Regenerate the current release-candidate checklist and status after the control-document edits. The regenerated status is 17/17 PASS and points to manifest seal `070232617a258217662d056a7471b28bd3c4e081d612ae509518a76696f67230`.
5. **DONE** — Preserve the historical `v0.1.0-demo-rc.1` release note and historical dated review records.

## 5. Section 0 exit criteria

Section 0 is complete for this audit cut:

- [x] Current control surfaces agree on Path A and the non-submission boundary.
- [x] Current stage count, branch/baseline, verification count, and RC evidence are synchronized.
- [x] The current RC status references the current release manifest rather than an earlier seal.
- [x] No historical record has been rewritten.
- [x] `python3 scripts/verify_release.py` remains PASS.
- [x] The authority order is explicit for the later population, endpoint, dataset, output, and disclosure audits.

The next section audit is Section 1 (source intake, SDTM provenance, and CORE residuals).

This audit does **not** approve the SAP for filing, close accepted findings, create sponsor approvals, or convert the repository to Path B/C.
