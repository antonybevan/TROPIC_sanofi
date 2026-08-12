# TROPIC Release Note — `v0.3.0-clinical-simulation`

**Release class:** Controlled clinical-submission simulation

**Claim authority:** `docs/PRODUCT_CLAIM.md` version 2.0

**Regulatory baseline:** `TROPIC-FDA-2026-08-12`

**Status:** Release evidence pending final rebuild and CI promotion

## Release intent

This release replaces portfolio-style presentation and ambiguous compliance language with a controlled evidence model. It aligns package naming to the FDA Study Data Technical Conformance Guide dated June 2026, records a real Pinnacle 21 Community execution without inflating it into licensed clearance, and makes the quality-system boundary executable in CI.

## Material changes

1. Reframed the product as a controlled clinical-submission simulation with one binding evidence claim.
2. Added an official-source regulatory baseline and a fail-closed package/claim gate.
3. Added a quality-system boundary for independent QC, Part 11, Enterprise validation, gateway acceptance, and aCRF status.
4. Renamed the packaged Clinical Study Data Reviewer's Guide from `sdrg.pdf` to the current FDA convention `csdrg.pdf`.
5. Preserved the source blank CRF as `blankcrf.pdf` and explicitly prohibited a false `acrf.pdf` alias.
6. Recorded a real Pinnacle 21 Community 4.1.0 / FDA 2508.1 ADaM run, its hashes, aggregate findings, and its built-in incompatible-CLI caveat.
7. Corrected standard one-sided ADaM flags in paired SAS/R derivations: ADAE/ADCM `TRTEMFL`, ADLB `ANL01FL`, and ADLB `ABLFL` now use `Y`/null; the nonstandard ADLB `BASEFL` variable was removed across data, metadata, and reporting logic.
8. Replaced promotional PDF header language with a neutral controlled-simulation identity.

## Qualification decision

The repository does not claim:

- organizationally independent QC approval;
- a validated 21 CFR Part 11 execution environment;
- licensed Pinnacle 21 Enterprise clearance;
- regulatory gateway acceptance;
- an annotated CRF; or
- confirmatory comparative efficacy.

Those gaps are explicit controls, not missing decoration. Their closure requirements are in `docs/QUALITY_SYSTEM_BOUNDARY.md`.

## Evidence required before promotion

- full 37-stage DAG with recorded real SAS execution;
- zero-difference paired reconciliation at controlled tolerances;
- metadata, TFL, PDF, cSDRG, eCTD, log, and finding gates passing;
- post-correction Pinnacle 21 Community rerun and disposition update;
- clean release manifest and release-candidate seal;
- GitHub CI green from the published commit.

Until those checks complete, this note remains a release candidate narrative and must not be represented as a completed tag.
