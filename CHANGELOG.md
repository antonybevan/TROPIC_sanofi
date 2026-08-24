# Changelog

Notable changes to TROPIC are recorded here. This is an engineering release
summary, not a validated 21 CFR Part 11 audit trail or electronic-signature
record. Detailed remediation history remains available in Git and in
`06_qc_evidence/audit/`.

The project uses its actual `0.x` portfolio tags. Historical draft `2.x`/`3.x`
headings were never the public tag line and have been removed from this summary
to avoid implying releases that did not exist.

## [Unreleased] — target `v0.3.0-clinical-simulation`

### Security

- Harden governance resealing so historical genuine-SAS evidence cannot be
  rebound to arbitrary source, a dirty working-tree snapshot, or modified
  release-authority controls without a fresh genuine run.
- Fail closed on symbolic links and escaping filesystem roots throughout Module
  5 packaging, eCTD backbone generation, materialization, validation, cleanup,
  and runtime-cache writes.
- Validate ownership, type, link status, and mode of the personal ODA
  configuration before evaluating it.
- Strengthen Python dependency integrity and isolate credential loading from
  dependency installation.

### Added

- Current 2026-08-24 FDA/ICH/CDISC currency review, including the FDA eCTD
  v3.2.2/v4.0 transition boundary and ICH E20 draft status.
- Repository-wide security review with regression tests for release provenance,
  credential trust, dependency supply chain, and eCTD filesystem boundaries.
- Submission-style final audit evidence covering mathematics, provenance,
  figures, reviewer interactions, clean-checkout reproducibility, and CI.

### Changed

- Clarified that a green portfolio release seal and a regulatory-shipment
  readiness decision are different gates; the latter remains blocked.
- Normalized the changelog to the repository's real tag history and retained
  detailed historical changes in the controlled audit records.
- Tightened repository conventions and dependency-maintenance automation for a
  smaller, more professional public surface.

### Fixed

- Closed validated release-provenance and link-resolution defects found during
  the final production-grade security pass.
- Reconciled current official-source statuses and removed stale future-version
  wording from the regulatory inventory.

## [0.2.2-portfolio] — 2026-08-05

### Changed

- Closed the pipeline-integrity and governance audit workstream.
- Added truthful full/partial-DAG failure telemetry and expanded CI coverage for
  abort paths, ARM, eCTD package-copy checks, CT boundaries, secret scanning,
  dependency locking, permissions, concurrency, and timeouts.
- Preserved the non-submission, non-Part-11, non-Enterprise, and external-review
  boundaries as explicit release controls.

## [0.2.1-portfolio] — 2026-08-05

### Changed

- Published the Path A audit-closure documentation and synchronized findings,
  traceability, reviewer narratives, and release evidence.
- Corrected endpoint, censoring, response, and TFL semantics while retaining the
  accepted need for qualified external statistical and medical review.

## [0.2.0-portfolio] — 2026-08-04

### Added

- Established the manifest-driven portfolio release, source-to-output
  traceability, risk-based QC, reviewer guides, Module 5/eCTD-style package,
  and clean-checkout release seal.
- Added paired SAS/R production-validation evidence with selected admiral
  corroboration and machine-readable reconciliation.

## [0.1.0-demo-rc.1] — 2026-07-09

### Added

- First controlled demonstration release candidate with a genuine ODA full-DAG
  run, release manifest, reviewer surface, and explicit non-regulatory boundary.

[Unreleased]: https://github.com/antonybevan/TROPIC_sanofi/compare/v0.2.2-portfolio...HEAD
[0.2.2-portfolio]: https://github.com/antonybevan/TROPIC_sanofi/releases/tag/v0.2.2-portfolio
[0.2.1-portfolio]: https://github.com/antonybevan/TROPIC_sanofi/releases/tag/v0.2.1-portfolio
[0.2.0-portfolio]: https://github.com/antonybevan/TROPIC_sanofi/releases/tag/v0.2.0-portfolio
[0.1.0-demo-rc.1]: https://github.com/antonybevan/TROPIC_sanofi/releases/tag/v0.1.0-demo-rc.1
