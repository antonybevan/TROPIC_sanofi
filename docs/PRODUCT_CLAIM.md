# Product and Evidence Claim

**Document ID:** TROPIC-PEC-001

**Version:** 2.0

**Effective date:** 2026-08-12

**Status:** Active

**Current controlled release:** `v0.3.0-clinical-simulation`

**Regulatory baseline:** `config/regulatory_baseline.yaml`

## Binding statement

TROPIC is a **controlled clinical-submission simulation** for clinical data engineering, statistical programming, metadata, quality control, and Module 5 assembly. It is **not a regulatory submission**, a sponsor-approved reanalysis, a validated Part 11 system, or evidence of FDA acceptance.

This document controls every claim made in the README, reviewer guides, package, release note, and interview narrative. When another artifact conflicts with this document, this document governs.

## Demonstrated scope

TROPIC may be described as demonstrating:

1. A manifest-driven SDTM-to-ADaM-to-TFL-to-Define-to-eCTD-style pipeline.
2. Paired SAS and R implementations and value-level reconciliation for the real de-identified MP arm when the recorded execution mode is `oda` or `local`.
3. A risk-based third implementation using admiral for ADSL and the primary OS/PFS analyses.
4. ADaMIG 1.3, SDTMIG 3.4, Define-XML 2.1 with a local stylesheet, and executable schema/specification controls.
5. Deterministic reviewer-guide, CSR, and Module 5-style package generation using current FDA cSDRG naming.
6. Hash-bound run evidence, CI controls, findings disposition, and reproducible release verification.
7. A real Pinnacle 21 Community validation run recorded as informative evidence with its compatibility caveat.

## Evidence grades

| Evidence | Grade | Permitted interpretation |
|---|---|---|
| Real SAS ODA plus independent R derivation | Verified execution | Technical double-programming evidence for the MP-arm datasets in scope |
| admiral re-derivation | Risk-based corroboration | Third-method evidence for ADSL and primary TTE only |
| Reconciliation and conformance gates | Executable control | Evidence that specified machine checks passed for the recorded run |
| Release hashes and Git/CI history | Integrity evidence | Reproducibility and change-detection controls |
| Pinnacle 21 Community 4.1.0 / FDA 2508.1 | Informative only | Issue discovery; not licensed Enterprise clearance |
| eCTD-style backbone validation | Structural simulation | Package engineering evidence; not gateway acceptance |

## Prohibited claims

| Do not claim | Reason |
|---|---|
| FDA submission-ready, NDA-ready, or regulator approved | No sponsor authorization, submission identifiers, gateway acceptance, licensed final validation, or complete filing content |
| Part 11 compliant or validated | Git, hashes, and CI do not establish a validated system or compliant electronic-signature process |
| Independent organizational QC complete | Implementations are methodologically separate but do not have an independent accountable human reviewer and signer |
| Licensed Pinnacle 21 clearance | Community was executed; Enterprise was not |
| Full two-arm IPD reanalysis | The public source data used here contains the MP arm only |
| Confirmatory comparative efficacy | The CbzP comparator is reconstructed/synthetic and is used only in reporting outputs |
| Annotated CRF delivered | The package contains a source blank CRF, not an annotated CRF |
| FDA validation or certification | FDA does not certify this repository; local validation is not agency acceptance |

## Data and analysis boundary

| Component | Population | Status | Repository treatment |
|---|---:|---|---|
| Source SDTM | MP, N=371 | Real de-identified data obtained under the source-data access terms | Not redistributed in Git |
| Reconciled ADaM | MP, N=371 | SAS/R production and validation scope | XPT payloads are not redistributed in a clean public clone |
| CbzP comparator | N=378 | Reconstructed OS/PFS and synthetic secondary endpoints | TFL-only; never represented as source or reconciled package ADaM |
| Comparative results | MP plus reconstructed/synthetic CbzP | Descriptive simulation | Non-confirmatory and not submission evidence |

The programming authority is `02_specifications/sap/TROPIC_SAP_v4.0_industry_grade.docx`. It is an author-developed control specification, not a sponsor-approved SAP.

## Qualification boundary

The authoritative gap and closure model is `docs/QUALITY_SYSTEM_BOUNDARY.md`.

- Organizationally independent QC: **not established**.
- Part 11 validated execution environment: **not established**.
- Licensed Pinnacle 21 Enterprise validation: **not executed**.
- Regulatory gateway acceptance: **not executed**.
- Annotated CRF: **not available**.

These are external qualification activities. They cannot be manufactured by adding templates, signatures, or badges to a public repository.

## Release rule

A controlled release may be promoted only when:

1. the full recorded DAG completes with real SAS execution;
2. SAS/R reconciliation, critical analysis controls, metadata checks, PDF checks, and package controls pass;
3. all confirmed critical or major findings are closed or the release is blocked;
4. validator findings and residual limitations are truthfully dispositioned;
5. the material tree is hash-bound and `scripts/verify_release.py` passes from a clean checkout; and
6. the release note does not exceed this claim.

A passing release is fit for portfolio review as a controlled simulation. It is not fit for regulatory submission without the external qualification work above.

## Authority order

1. This product and evidence claim.
2. `config/regulatory_baseline.yaml` and `docs/QUALITY_SYSTEM_BOUNDARY.md`.
3. The controlled SAP and lock memo.
4. Specifications, output catalog, study configuration, and manifest.
5. Machine evidence and release seals.
6. Reviewer guides and presentation materials.
