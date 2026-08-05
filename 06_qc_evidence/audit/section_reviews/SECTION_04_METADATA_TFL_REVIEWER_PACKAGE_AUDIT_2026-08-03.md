# Section 4 — Metadata, TFL, and reviewer-package audit

**Review date:** 2026-08-03
**Product claim:** Path A controlled non-submission demonstration
**Authority:** `03_metadata/adam/ADaM_spec.xlsx`, Define-XML 2.1 artifacts, `config/tfl_output_catalog.yaml`, ADRG/SDRG/BDRG, and the Section 3 ADaM audit

> **Historical baseline notice (2026-08-05):** The counts and decision text below preserve the pre-adoption package snapshot. The closure addendum controls the current Path A state and records the corrected 21/18 catalog, 10/18 ARM, regenerated package, release reseal, and CI verification. External qualified statistical/medical review remains required.

## Decision

**PASS for the controlled Path A metadata/output/package surface, subject to the final clean-worktree reseal.**

The metadata contract, controlled TFL catalog, reviewer guides, and eCTD-style materialization connect to the corrected ADTTE factory. The package remains explicitly non-submission: it uses EXAMPLE identifiers, synthetic/reconstructed CbzP content, and no Part 11 claim. The Section 3 pain/supporting-disease decision remains an interpretive residual and is carried into the reviewer-facing documents.

## 1. Metadata contract

- ADaM specification: 7 datasets, 159 variables, 7 value-level records, 10 where-clauses, 60 controlled terms, 46 methods.
- Define-XML ADaM: 7 item groups, 166 items, 7 codelists, 45 methods, 3 value lists, 8 result displays, and 10 analysis results.
- Spec-to-Define and spec-to-data conformance: PASS.
- Metadata lineage: PASS; no unresolved predecessor/method/Define-XML traceability gaps.
- ADTTE remains inside the governed 19-variable specification; component source is exposed through the existing `EVNTDESC` field (`DISEASE PROGRESSION`, `PAIN PROGRESSION`, `DEATH`) and `ADT`, with the S3-04 medical qualification residual documented.

The two controlled CT dispositions remain warnings rather than hidden failures. They do not create an unresolved traceability gap, but a sponsor filing package would require the applicable controlled terminology decisions to be approved and versioned.

## 2. TFL catalog and evidence

| Control | Result |
|---|---:|
| Controlled in-scope IDs | 18 |
| SAP full-catalog IDs | 31 |
| Explicitly deferred IDs | 21 |
| Approved extension IDs | 8 |
| Missing primary files | 0 |
| Missing/stale SAS companions | 0 after final real-SAS run |
| Unindexed physical outputs | 0 |
| Endpoint-semantic problems | 0 |

The historical catalog snapshot retained the SAP `T-11-8` response/TTPAIN collision. The Phase 2 control surface now restores the SAP-native mapping: T-11-3 PSA response, T-11-4 ORR, T-11-5 pain response, T-11-6 TTUMOR, T-11-7 TTPSA and T-11-8 TTPAIN; T-11-8b is an explicit ORR response-evaluable sensitivity. TTUMOR is ITT-primary and the observed-baseline PSA denominator remains MP 329 / CbzP 361.

ARS is present for the controlled survival core (16 AR rows and a reporting event). Full SAP-catalog ARS coverage remains outside Path A and is not implied by the ARS artifact.

## 3. Reviewer guides and traceability

- ADRG, SDRG, and BDRG carry the Path A product claim, explicit “is/is not” boundaries, document control, provenance limits, and known-differences pointer.
- ADRG now states the corrected time origins, PFS last-evaluable/no-post-baseline rule, TTUMOR RECIST-only censor pool, observed-baseline PSA rule, and the S3-04 pain/RT residual.
- `TRACEABILITY_MATRIX.md` maps ADTTE to the corrected programs and describes the component-label and censoring controls.
- The findings register and disposition board carry F-040/F-041 as corrected and F-042 as implemented for Path A with external qualified review still required.

## 4. eCTD-style package integrity

The materialized sequence contains 89 m5 payload files. The eCTD index contains 89 m5 hrefs; checksum/index verification is produced by the package materialization stage. The package includes current factory programs and current rendered output after the final reseal run.

Structural limitations remain intentionally visible:

1. `EXAMPLE/000000` application identifiers and a blank/source CRF placeholder are not a real sponsor filing identity or a complete annotated CRF.
2. CbzP is a synthetic/reconstructed comparator and is TFL-only; it is not patient-level trial IPD.
3. Git/hash controls are reproducibility controls, not a validated Part 11 system or electronic signature.

## Phase 2 closure addendum — 2026-08-04

Following Antony Bevan's ED-01–ED-07 adoption, the controlled catalog contains 21
in-scope IDs and 18 explicitly deferred SAP IDs. The F-042 module and aggregate
event-source evidence are packaged, and the full 34-stage real-SAS run passed
metadata, TFL, package and log gates. The clean committed release-manifest rebind
and CI verification are complete; no independent, sponsor, medical or regulated
approval is claimed.

## 5. Handoff to final reseal

The full DAG has now passed. Commit the intentional factory/document/control changes,
rebind the release manifest against the clean source tree, and run
`scripts/verify_release.py`. A release-candidate PASS is valid only when the current
material worktree is clean and the release manifest is resealed against that exact
source tree.
