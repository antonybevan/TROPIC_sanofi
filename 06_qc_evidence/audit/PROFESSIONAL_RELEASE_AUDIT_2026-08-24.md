# Professional release audit — 2026-08-24

## Decision

The remediated candidate is **not yet promoted** in this source-control cut. The
implementation and preflight audits are complete; promotion additionally requires a
fresh genuine SAS/ODA 41-stage DAG, regenerated evidence, a clean release seal,
clean-checkout replay, and green pull-request checks. Exact completion evidence is
recorded in this document before the final seal is built.

This is a professional engineering and clinical-programming demonstration. It is not
an FDA submission, sponsor approval, medical approval, independent statistical QC,
Pinnacle 21 Enterprise clearance, or a validated 21 CFR Part 11 computerized system.

## Audited scope

- Whole tracked repository, ignored runtime/data/credential boundaries, dependency
  locks, CI workflows, and release authority.
- Statistical logic, simulation assumptions, numerical boundaries, provenance,
  source-to-output traceability, package integrity, and reviewer claims.
- Seven R-rendered and six genuine-SAS figures at original resolution, their data
  reconciliation, and the static TFL gallery.
- Static gallery and Shiny reviewer dashboard interactions, including keyboard use,
  modal focus, filters, sorting, endpoint switching, and responsive widths.
- Current FDA, ICH, eCFR, and CDISC sources screened for this repository's declared
  product, data, standards, simulation, and submission-operations scope.

## Research and standards result

The scoped official-source inventory contains 50 entries: 18 applicable, 17
partially applicable, 5 out of scope, 7 watch/not-final, and 3 requiring owner
confirmation. The review distinguishes current requirements from drafts and roadmap
material, including ICH E20 Step 2, CDISC Controlled Terminology Package 62 public
review, and incomplete CDISC CORE rule coverage. FDA eCTD v3.2.2 and v4.0 are treated
as center/application-specific implementation choices, not interchangeable labels.

The durable conclusion is **BLOCKED for regulatory shipment**. The repository can
demonstrate controlled engineering, but the filing decision remains outside this
project until accountable sponsor, statistics, clinical, quality, data-owner, system
qualification, validator, and submission-operations evidence exists.

## Remediation result

| Area | Implemented control |
|---|---|
| Release provenance | A shared fail-closed reseal policy requires an authenticated committed predecessor, immutable Git blobs, exact change inventory, clean worktree, and continuous chain. |
| Release inventory | Git-tracked tests, workflows, and ADaM CORE rules are discovered independently and enter the source seal; duplicate, missing, extra, malformed, symlinked, or non-regular rows fail. |
| Filesystem safety | Module 5/eCTD reads, copies, replaces, permissions, enumeration, and cleanup are descriptor-relative and no-follow, with stable identity checks and parent-swap rejection. |
| Credentials | The personal ODA configuration and CDISC key file must be stable, bounded, current-UID regular files with exact restrictive mode before use; credentials are scoped only to the child that needs them. |
| Supply chain | CI and CORE Python runtime/build inputs are version-and-artifact-hash locked; build isolation is disabled; GitHub Actions are commit pinned; dependency review, CodeQL, and Gitleaks are CI controls. |
| Numerical logic | Piecewise-hazard inversion boundaries, annual-probability conversion, log-rank direction, tied/not-reached KM medians, analytic null behavior, Wilson intervals, MCSE, replicate accounting, and invalid inputs have executable checks. |
| Reviewer surfaces | The TFL gallery is self-contained and keyboard accessible; current audit, navigation, claim, simulation, and figure surfaces are release-hash bound. |

## Preflight evidence

| Check | Result |
|---|---|
| Focused security/math/repository tests | **99 passed** |
| ODA broker security and orchestration unit suite | **99 passed** |
| R endpoint, lab-shift, figure, population, and dashboard contracts | **PASS** |
| Figure contract | **13/13 PNGs passed** (7 R, 6 SAS; 2400 px wide, opaque) |
| SAS static analysis | **0 errors, 0 warnings across 17 files** |
| CORE custom-rule structure and independent lock | **7/7 rules valid and locked** |
| Manifest DAG wiring | **41 stages valid** |
| Define-XML internal checks | **522 ADaM + 351 SDTM checks passed** |
| ADaM in-repo conformance | **0 findings at this check level** |
| R lint / dependency state | **0 issues across 41 files; `renv` consistent** |
| Official-source inventory | **PASS; 50 entries** |
| Submission-readiness profile | **BLOCKED as designed; 4 named blockers** |
| Gitleaks v8.30.1, pinned archive checksum, full Git history | **322 commits scanned; no leaks found** |

The preflight full Python collection intentionally reports stale simulation/package
hashes after the mathematical source hardening. Those mismatches are not waived: the
fresh full DAG must regenerate and independently reverify the evidence before this
audit can record a final PASS.

## Final controlled execution evidence

Pending the fresh genuine SAS/ODA run and final release-seal build. This section is
replaced with the exact run timestamp, SAS version, stage count, test counts,
reconciliation tolerances, package result, seal result, clean-checkout result, commit,
and pull-request checks before promotion.

## Residual boundaries

1. The public project does not contain full authorized two-arm IPD and does not
   reproduce the protocol ITT population of 755.
2. Cabazitaxel comparative material remains synthetic/reconstructed and
   non-confirmatory.
3. The eCTD tree uses example identifiers and has not been accepted through an FDA
   gateway.
4. Pinnacle 21 Community findings remain for disposition; licensed qualified
   Enterprise execution and independent approval are external.
5. CDISC CORE is not comprehensive and the project uses seven transparent custom ADaM
   rules in addition to its other checks.
6. No Git/CI/ODA artifact is presented as an electronic signature, organizational
   validation, or Part 11 audit trail.
7. Python 3.10 remains supported only through October 2026; a controlled runtime
   migration must be qualified before that deadline.
