# TROPIC Release Note — `v0.3.0-clinical-simulation`

**Release class:** Controlled clinical-submission simulation

**Claim authority:** `docs/PRODUCT_CLAIM.md` version 2.1

**Regulatory baseline:** `TROPIC-FDA-2026-08-12`

**Status:** `PROMOTE_ONLY_AFTER_ALL_RELEASE_GATES_PASS`

## Release intent

This release replaces portfolio-style presentation and ambiguous compliance language with a controlled evidence model. It aligns package naming to the FDA Study Data Technical Conformance Guide dated June 2026, records a real Pinnacle 21 Community execution without inflating it into licensed clearance, and makes the quality-system boundary executable in CI.

## Material changes

1. Reframed the product as a controlled clinical-submission simulation with one binding evidence claim.
2. Added an official-source regulatory baseline and a fail-closed package/claim gate.
3. Added a quality-system boundary for independent QC, Part 11, Enterprise validation, gateway acceptance, and aCRF status.
4. Renamed the packaged Clinical Study Data Reviewer's Guide from `sdrg.pdf` to the current FDA convention `csdrg.pdf`.
5. Preserved the source blank CRF as `blankcrf.pdf` and explicitly prohibited a false `acrf.pdf` alias.
6. Recorded a definitive Pinnacle 21 Community 4.1.0 / FDA 2508.1 ADaM run: 7 datasets, 121,320 records, 0 rejects, 30 open issue groups, and 2,373 aggregate occurrences. The raw workbook is retained outside Git because it contains record-level identifiers; its SHA-256 and a de-identified, self-reconciling aggregate inventory are retained in-repository.
7. Corrected standard one-sided ADaM flags in paired SAS/R derivations: ADAE/ADCM `TRTEMFL`, ADLB `ANL01FL`, and ADLB `ABLFL` now use `Y`/null; the nonstandard ADLB `BASEFL` variable was removed across data, metadata, and reporting logic.
8. Replaced promotional PDF header language with a neutral controlled-simulation identity.
9. Added a local dashboard visual-QC record and sanitized five-panel screenshots; retained the static TFL gallery as the portable public visual surface.
10. Added fail-closed dashboard input-domain checks so malformed numeric, arm, event, and exposure values disable affected outputs with an actionable load issue instead of surfacing a rendering error.
11. Added a governed, data-free simulation methods annex: a frozen ICH M15/E9-aligned MAP, ten ADEMP/OCTAVE scenarios, 400,000 fixed-seed replicates, MCSE/Wilson uncertainty, deterministic representative trials and edge fixtures, independent evidence verification, and generated reviewer/PDF surfaces. The annex remains explicitly non-MIDD, non-confirmatory, and `NOT_QUALIFIED` for clinical or filing use.

## Qualification decision

The repository does not claim:

- organizationally independent QC approval;
- a validated 21 CFR Part 11 execution environment;
- licensed Pinnacle 21 Enterprise clearance;
- regulatory gateway acceptance;
- an annotated CRF; or
- confirmatory comparative efficacy.

Those gaps are explicit controls, not missing decoration. Their closure requirements are in `docs/QUALITY_SYSTEM_BOUNDARY.md`.

## Promotion evidence contract

The release tag may be created only after all of the following are true:

- the full 40-stage DAG completed with recorded real SAS execution, including simulation generation, report rendering, and independent verification;
- paired reconciliation passed at controlled tolerances;
- metadata, TFL, PDF, cSDRG, eCTD, log, and finding gates passed;
- the post-correction Community run was executed and every residual family was recorded without a clearance claim;
- the committed tree passed the clean-checkout release verifier and release-candidate seal; and
- GitHub CI was green for the published commit and merged default branch.

The existence of tag `v0.3.0-clinical-simulation` is the promotion record for this conditional note. The tag must not be created or retained if any item above is unmet.
