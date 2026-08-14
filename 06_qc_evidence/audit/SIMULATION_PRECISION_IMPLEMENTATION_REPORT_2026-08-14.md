# TROPIC Maximal Simulation Precision — Implementation and Verification Report

**Report date:** 2026-08-14

**Workstream:** data-free simulation methods evaluation

**Decision:** computational evidence accepted; clinical/filing qualification not accepted

**Authoritative result:** `platform/simulation_operating_characteristics/simulation_oc_status.json`

> This work is a controlled, data-free methods evaluation. It is not MIDD
> evidence, confirmatory efficacy evidence, sponsor approval, regulator
> acceptance, or a substitute for authoritative TROPIC participant-level data.

## 1. Executive outcome

The repository now contains a prospective, frozen simulation protocol; a
deterministic individual-level time-to-event engine; an independent evidence
checker; generated Model Analysis Plan and Model Analysis Report sources; and a
Module 5-style PDF package. Ten governed scenarios requested 400,000 replicates.
All 400,000 completed and none failed.

The four deliberately separate conclusions are:

| Assessment | Result | Interpretation |
| --- | --- | --- |
| Execution | PASS | Requested, completed, and failed accounting reconciles exactly. |
| Monte Carlo precision | PASS | Every scenario met its governed replication, failure-rate, and MCSE rules. |
| Design operating characteristics | PASS | The two null benchmarks and prespecified software edge checks passed. |
| Evidence qualification | NOT_QUALIFIED | Results are informative, non-MIDD, non-confirmatory, and unsuitable for clinical or filing decisions. |

There is intentionally no single overall PASS. A precise computation is not the
same as a qualified model or an acceptable clinical design.

## 2. Research and design review

The implementation was designed after a current-practice review recorded in
[`docs/SIMULATION_PRECISION_RESEARCH.md`](../../docs/SIMULATION_PRECISION_RESEARCH.md).
The review used the final 2026 ICH M15 guideline, ICH E9(R1), FDA adaptive-design
and Complex Innovative Trial Design materials, ADEMP, OCTAVE, a 2026
simulation-guided-trials review, and the Guyot/IPDfromKM reconstruction methods.

The resulting controls are:

- a decision-focused question, context of use, model influence, consequence,
  risk, and impact assessment;
- an E9(R1)-style population, treatments, endpoints, intercurrent-event
  strategies, censoring rules, and population summary;
- a frozen ADEMP/OCTAVE scenario registry with exact assumptions and seeds;
- 100,000 completed replicates for each key null and 25,000 for every
  alternative or stress scenario;
- numerator, denominator, estimate, MCSE, and 95% Wilson interval for every
  reported probability;
- analytic null acceptance only when the Wilson interval contains alpha and
  absolute deviation is no greater than `max(0.001, 3*MCSE)`;
- exact failure accounting with a 0.1% key-scenario failure cap; and
- independent recomputation of hashes, accounting, MCSE, Wilson intervals,
  statuses, representative-trial bindings, reports, and package sidecars.

## 3. Implemented evidence chain

| Layer | Controlled artifact |
| --- | --- |
| Prospective protocol and MAP | `config/simulation_protocol.yaml` |
| Simulation engine | `platform/simulation_precision.py` |
| Authoritative machine result | `platform/simulation_operating_characteristics/simulation_oc_status.json` |
| Clean-checkout parity views | `scenario_results.csv`; `representative_trials.json` (aggregate rows only) |
| Reviewer-source generator | `platform/build_simulation_report.py` |
| Independent checker | `platform/check_simulation_evidence.py` |
| Human MAP/MAR | `07_reviewer_explanation/simulation_model_analysis_plan.md`; `simulation_report.md` |
| Submission PDFs | `08_submission_package/m5/53-clin-stud-rep/535-rep-effic-safety-stud/mcrpc/5351-stud-rep-contr/tropic/` |
| Packaged executable sources | `08_submission_package/m5/datasets/tropic/analysis/adam/programs/` |
| Orchestration | Stages 29–31 of the manifest-driven 40-stage DAG |

The human reports are generated from the frozen YAML and authoritative JSON;
result numbers are not manually transcribed. Program and protocol sources in
Module 5 are byte-for-byte copies of their repository authorities.

## 4. Governed results

| Scenario | Class | Rejections / analyzed | Estimate | MCSE |
| --- | --- | ---: | ---: | ---: |
| OS_NULL_REFERENCE | Key null | 2,525 / 100,000 | 2.525% | 0.000496109 |
| PFS_NULL_HIGH_DROPOUT | Key null stress | 2,504 / 100,000 | 2.504% | 0.000494095 |
| OS_PUBLISHED_EFFECT | Alternative | 23,688 / 25,000 | 94.752% | 0.00141033 |
| PFS_PUBLISHED_EFFECT | Alternative | 24,581 / 25,000 | 98.324% | 0.000811889 |
| OS_MEDIAN_CALIBRATED | Alternative | 10,919 / 25,000 | 43.676% | 0.00313688 |
| PFS_MEDIAN_CALIBRATED | Alternative | 25,000 / 25,000 | 100.000% | 0 |
| OS_DELAYED_NON_PH | Alternative stress | 20,166 / 25,000 | 80.664% | 0.00249777 |
| PFS_DELAYED_NON_PH | Alternative stress | 24,564 / 25,000 | 98.256% | 0.000827909 |
| OS_WANING_AFTER_DISCONTINUATION | Alternative stress | 19,647 / 25,000 | 78.588% | 0.00259440 |
| PFS_WANING_AFTER_DISCONTINUATION | Alternative stress | 24,036 / 25,000 | 96.144% | 0.00121775 |

The null estimates are consistent with one-sided alpha 0.025 under the
prespecified analytic rule. Alternative estimates remain descriptive because no
sponsor-approved minimum power criterion or clinically important effect was
available prospectively.

## 5. Defects found and corrected during adversarial review

1. **NumPy 2.2 large-batch variance reduction.** A cross-version regression
   could produce a negative pseudo-variance when a large temporary product was
   reduced. The engine now explicitly materializes float64 intermediates. A
   1,000-replicate by 755-participant regression test passes on Python 3.12.13
   and Python 3.14.6 with NumPy 2.2.6.
2. **Fail-open evidence risk.** The final bundle is checked by an implementation
   that does not import the simulation engine. It independently recomputes the
   scenario order, seed mapping, hashes, accounting, uncertainty, null rules,
   representative-trial selections, edge fixtures, qualification boundary,
   sidecars, and report parity. Malformed-fixture tests exercise every rejection
   path.
3. **Representative-trial ambiguity.** Scenario-derived reject, non-reject, and
   near-alpha paths are separated from deliberately artificial positive,
   negative, and zero-variance software fixtures. No subject rows are retained.
4. **Cross-version traceability.** Results record Python 3.12.13, NumPy 2.2.6,
   PyYAML 6.0.3, float64, PCG64, the dependency lock, unique seeds, scenario
   hashes, and code/protocol/scientific hashes.
5. **Dense reviewer tables.** Wide execution and operating-characteristic tables
   were split into narrower accounting, decision, and rationale tables.
6. **PDF orphan heading.** A second page-by-page inspection found
   `Representative Simulated Trial Paths` stranded above the page-11 footer
   while its table began on page 12. The renderer now reserves 40 mm for a
   heading plus its first content row. A PDF-text regression requires the heading
   and first table row to remain together.

## 6. Verification record

| Check | Result |
| --- | --- |
| Pinned full simulation | PASS — 400,000/400,000 completed, 0 failed; 25.33 s wall clock |
| Full Python suite | PASS — 198 tests |
| R contract suite | PASS — 8/8 scripts, including Shiny local/data-free, figures, TFL populations, survival statistics, laboratory shifts, F-042 boundaries, and smoke tests |
| Independent simulation checker | PASS — default CLI exits 0 with no findings |
| G07 reviewer package lock | PASS |
| Dataset-JSON | PASS — 26/26 schema-valid exports |
| ARS / USDM | PASS — referential and local-reference validation |
| eCTD materialization | PASS — 99/99 leaves checksum verified; zero unexpected leaves |
| G08 sequence validation | PASS |
| Regulatory baseline / validation strategy / log cleanliness | PASS / PASS / PASS |
| PDF structural QA | PASS — 13-page MAP, 15-page MAR, 7-page CSR; US Letter, PDF 1.7, web optimized, embedded Arial |
| PDF visual QA | PASS — all 35 pages rendered and inspected; no clipping or orphaned table headings after correction |
| Computer Use QA | PASS — Preview page 12 inspected at Actual Size and progressive zoom levels; high-zoom horizontal navigation reached the decision/evidence column |
| Release verifier | EXPECTED FAIL — 39/43 because this uncommitted, source-changing build cannot match the prior real-SAS release seal |

The PDFs are not tagged PDFs. Their Markdown sources are retained as the
accessible textual authority; no tagged-PDF accessibility claim is made.

## 7. Reproducibility bindings

| Binding | SHA-256 |
| --- | --- |
| Protocol | `09798cd52adedd742a10f39266c67df0d9fe40b4c693912e4962b47601446b61` |
| Scenario registry | `da115050f9d3fb69202b7154814c0eb204852efbe99f9b6107e548419f3f7768` |
| Simulation code | `3fb535efdfea04955795619e0d209723aa35f88d70ce9429ae4667adc4ec0da2` |
| Scientific content | `bad4514234456f7749160ea56888867d63fbf60825716783c77a55817fa11c2b` |

The pinned rerun reproduced all four bindings exactly. The JSON file hash is
reported separately from the scientific-content hash so self-seal fields do not
create a circular identity.

## 8. Fresh-SAS execution limitation

A fresh 40-stage `--real-sas` run passed stages 1–16 and then failed repeatedly
while opening the SAS OnDemand session at stage 17. Nine orchestrated attempts
and a later bounded six-attempt/180-second broker probe all returned the same
upstream error: encryption-key exchange failed and the SAS process terminated.
No simulation or package code caused that failure.

The orchestrator correctly refuses to promote cached SAS evidence as a fresh
release-candidate run. That control was not weakened. The development bundle was
instead rechecked component-by-component against the prior genuine SAS outputs,
while this report and the draft pull request disclose that a new release seal
must wait for ODA recovery and a clean full-DAG rerun. `--demo` smoke tests also
passed, but are not represented as a full-DAG execution.

## 9. Residual limitations and next promotion actions

- The design uses public 377/378 randomized-count calibration, not the available
  real MP N=371 and not authoritative original-trial IPD.
- The analysis is a one-sided unstratified log-rank test and omits the original
  stratification because its joint distribution is unavailable.
- Correlation structure, informative withdrawal, model form, discontinuation,
  delayed effects, and waning remain explicit assumptions.
- No sponsor-approved MCID, power target, external model validation,
  independent organizational statistical/medical approval, regulator alignment,
  validated-system controls, or Part 11 controls exist.
- Promotion requires ODA recovery, a clean fresh 40-stage real-SAS run, a new
  hash seal, clean-checkout release verification, and green GitHub CI.

Until those actions complete, the correct delivery state is **tested draft
submission project; not promotion-ready**.
