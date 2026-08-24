# Professional release audit — 2026-08-24

## Decision

The remediated candidate is **not promoted** in this source-control cut. The
implementation and preflight audits are complete, but the fresh genuine SAS/ODA run
was blocked by a sustained external encryption-handshake failure. The pipeline
recorded a partial RED run and rolled back clinical outputs. Promotion still requires
a fresh genuine SAS/ODA 41-stage DAG, clean release seal, clean-checkout replay, and
green pull-request checks.

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
| Regenerated simulation bundle and independent verifier | **PASS; 400,000/400,000 completed, 0 failed; qualification remains NOT_QUALIFIED** |
| Draft eCTD materialization | **PASS; 99/99 leaves, 0 unexpected files** |
| Generated PDF review | **PASS; 6 PDFs / 62 pages, all fonts embedded, no visual or bounds defect; 6/6 byte-identical on rebuild** |
| Integrated Python collection after regeneration | **258 passed; 2 deliberate current-baseline failures while run status is RED** |
| Clean-checkout functional replay | **257 passed, 1 data-dependent skip, 2 current-production qualification checks explicitly separated** |
| Pull-request CI at `eabfd0a7` | **Functional/conformance PASS; CodeQL Python PASS; CodeQL Actions PASS; qualification/seal FAIL as designed; dependency review blocked by repository setting** |

The mathematical source change initially made the checked-in simulation/package
hashes stale. Those mismatches were not waived: the 400,000-replicate bundle, reports,
program copy, PDFs, and eCTD indexes were regenerated and independently reverified.
That data-free work does not substitute for the missing genuine SAS run.

## Controlled execution evidence and blocker

- Reviewed source/control commit: `dca97dd0c659bf1fab781c7f073ea1a7397ff884`.
- Run terminal timestamp: `2026-08-24T09:50:24.291968+00:00`.
- ODA preflight: **PASS**, including Java, SASPy, stable owner-only configuration,
  auth-file presence/mode, and complete regional failover host configuration.
- ODA connection result: **44 attempts across the 3,600-second budget; 0 live probe
  successes**. Every SAS process terminated during the encryption-key exchange before
  program upload or submit.
- Regression diagnosis: a separate one-shot launch using the untouched original
  `sascfg_personal.py` failed with the same exchange error. The verified private-copy
  hardening did not cause the outage.
- DAG result: stages 1-16 passed. Stage 17 truthfully labelled the exhausted path as a
  simulated fallback; Stage 18 rejected the resulting `F042_PAIN_RESPONSE` mismatch.
  Final state is **RED, partial_dag, 18/41 recorded, 23 not run**.
- Rollback: **PASS** for controlled ADaM XPT, TFL-output, and sequence surfaces covered
  by the run backup. No simulated result was accepted as double programming.
- Release verifier: **24/43 checks passed; FAIL**. No new release manifest, candidate
  checklist, governance reseal, tag, or promotion was created.
- Recommended retry window from the existing successful-connect ledger:
  **19:00-22:00 local**. This is an operational hint, not a service guarantee.

The correct disposition is **external blocker, retry required**. Skipping the SAS gate,
using cached output, or rebinding the 2026-08-23 genuine run would contradict the
current source identity and is prohibited by the new release policy.

## Continuous-integration disposition

The pull-request run at
`https://github.com/antonybevan/TROPIC_sanofi/actions/runs/32716139620`
demonstrated the intended separation of concerns. `Run Tests & Conformance Gates`,
`CodeQL SAST (python)`, and `CodeQL SAST (actions)` passed. The independently required
`Path A seal verify (verify_release)` and the explicit current-external-run
qualification job failed because the genuine SAS/ODA baseline is RED and stale; those
failures must not be bypassed.

`Dependency review (PR delta)` reached the pinned GitHub action with the correct
read-only contents permission, but GitHub rejected it because the repository's
Dependency graph is disabled. This is an administrative prerequisite, not a workflow
or dependency defect. Enable **Settings -> Advanced Security -> Dependency graph**,
wait for initial graph population, and rerun the failed job. Do not use `warn-only` or
`continue-on-error` as a substitute. After the first successful run, add dependency
review and the explicit qualification context to protected-branch required checks;
CodeQL contexts should also be required for the professional release branch.

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
