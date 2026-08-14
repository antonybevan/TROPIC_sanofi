# TROPIC Simulation Model Analysis Report

**Current sealed controlled release:** `v0.3.0-clinical-simulation` · [`docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md`](../docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md)

> **Informative annex boundary.** These deterministic simulation results are a data-free methods evaluation layered on the historical sealed clinical-simulation release. They are not MIDD evidence, a filing artifact, confirmatory efficacy evidence, sponsor approval, or evidence of regulator acceptance.

## Reviewer Status Snapshot

| Assessment | Status | Authoritative rationale | Meaning |
| --- | --- | --- | --- |
| Execution | PASS | Every run executed and requested/completed/failed accounting is complete. | Did requested replicates complete with failures explicitly accounted for? |
| Monte Carlo precision | PASS | Every scenario met its prespecified replication, failure-rate, and MCSE controls. | Were prespecified replication, failure-rate, and uncertainty criteria met? |
| Design operating characteristics | PASS | Analytic null, scenario-derived trial selection, and log-rank edge checks passed. | Did the design meet the scenario-specific scientific acceptance criteria? |
| Evidence qualification | NOT_QUALIFIED | Informational, data-free, non-MIDD, non-confirmatory methods evaluation only. | What decisions may these results support? |

There is deliberately no single overall PASS. Execution and precision statuses describe the reliability of the computation; the design status describes the operating characteristics. Precision does not rescue an unacceptable design result.

## Question, Context, and Model Risk

| ICH M15 element | Assessed value |
| --- | --- |
| Question of interest | Under explicit public-aggregate or stress-test assumptions, what are the rejection probabilities and numerical precision of a one-sided unstratified log-rank test in a simplified TROPIC-like fixed two-arm OS or PFS design? |
| Context of use | Low-influence internal methods evaluation and reviewer training for simulation engineering, numerical precision, and sensitivity to stated design assumptions. |
| Model influence | LOW |
| Consequence of a wrong decision | Misinterpreting numerical operating characteristics as clinical evidence could misstate design performance or treatment benefit; the hard use boundary prevents those decisions from relying on this model. |
| Model risk | MODERATE |
| Model impact | LOW |

## Estimand and Intercurrent Events

| ICH E9(R1) attribute | Implemented definition |
| --- | --- |
| Population | Hypothetical randomized participants meeting a simplified TROPIC-like analysis population; fixed public-randomized-design calibration of 377 control and 378 experimental participants. This is distinct from the repository's available real MP cohort of N=371 and does not imply that participant-level data are available. |
| Treatment conditions | control: Synthetic control strategy from randomization through follow-up.; experimental: Synthetic experimental strategy from randomization through follow-up. |
| Variables / endpoints | OS: Time from randomization to death from any cause.; PFS: Time from randomization to progression or death from any cause. |
| Population-level summary | Between-arm survival-distribution contrast evaluated by the one-sided intent-to-treat log-rank statistic; repeated-trial summary is rejection probability. |

### Intercurrent-Event Handling

| Intercurrent event | Strategy | Simulation / analysis handling |
| --- | --- | --- |
| permanent_treatment_discontinuation | TREATMENT_POLICY | Follow-up and endpoint ascertainment continue. Reference scenarios retain the assigned-arm hazard; stress scenarios explicitly allow effect waning after discontinuation without censoring the endpoint. |
| subsequent_anticancer_therapy | TREATMENT_POLICY | Endpoint follow-up would continue regardless of subsequent therapy; a separate therapy process is not generated in this bounded implementation. |
| death | OS: OUTCOME_EVENT_NOT_INTERCURRENT; PFS: COMPOSITE | Death is the OS event and is included in the PFS composite event. |

### Missing Data and Censoring

| Mechanism | Classification | Handling |
| --- | --- | --- |
| Independent Withdrawal | MISSING_ENDPOINT_OBSERVATION_NOT_INTERCURRENT_EVENT | Independently generated withdrawal censors at last observation. High-dropout scenarios stress this assumption; informative withdrawal is not modeled. |
| Administrative Censoring | Censoring | Censor at the fixed common analysis date after staggered enrollment. |

## Implemented ADEMP and OCTAVE Methods

| Framework element | Implemented method |
| --- | --- |
| ADEMP aims | Estimate Type I error or power and its Monte Carlo uncertainty for the governed scenario grid. |
| ADEMP data-generating mechanism | Individual enrollment, piecewise-exponential endpoint time, independent withdrawal, optional treatment discontinuation with post-discontinuation waning, and fixed administrative censoring. |
| ADEMP methods | One-sided unstratified log-rank test at alpha 0.025. |
| ADEMP performance measures | Rejection numerator, denominator, probability, MCSE, and 95% Wilson interval.; Completed/failed accounting and failure reasons.; Mean event and censor proportions by randomized arm. |
| OCTAVE characteristics | OS/PFS baseline hazards, treatment-effect shape, withdrawal, and discontinuation assumptions. |
| OCTAVE trial design | Fixed parallel two-arm allocation with staggered enrollment and common analysis date. |
| OCTAVE analyses | Intent-to-treat one-sided log-rank analysis. |
| OCTAVE valuation metrics | Type I error or power, Monte Carlo precision, event/censoring rates, and execution failures. |
| OCTAVE evidence | Protocol/scenario/code hashes, deterministic trials, analytic benchmark, and machine-readable results. |

## Scenario Coverage

| Scenario | Endpoint | Class | Assumption basis | Varying factors |
| --- | --- | --- | --- | --- |
| OS_NULL_REFERENCE | OS | KEY_NULL | ASSUMED_REFERENCE | treatment hr segments=start month: 0; hazard ratio: 1; withdrawal rate 12m=control: 0.04; experimental: 0.04; discontinuation rate 12m=0; post discontinuation hazard ratio=1 |
| PFS_NULL_HIGH_DROPOUT | PFS | KEY_NULL_OPERATIONAL_STRESS | ASSUMED_STRESS | treatment hr segments=start month: 0; hazard ratio: 1; withdrawal rate 12m=control: 0.25; experimental: 0.25; discontinuation rate 12m=0; post discontinuation hazard ratio=1 |
| OS_PUBLISHED_EFFECT | OS | ALTERNATIVE | PUBLIC_AGGREGATE | treatment hr segments=start month: 0; hazard ratio: 0.7; withdrawal rate 12m=control: 0.04; experimental: 0.04; discontinuation rate 12m=0; post discontinuation hazard ratio=1 |
| PFS_PUBLISHED_EFFECT | PFS | ALTERNATIVE | PUBLIC_AGGREGATE | treatment hr segments=start month: 0; hazard ratio: 0.74; withdrawal rate 12m=control: 0.08; experimental: 0.08; discontinuation rate 12m=0; post discontinuation hazard ratio=1 |
| OS_MEDIAN_CALIBRATED | OS | ALTERNATIVE | PUBLIC_AGGREGATE_CALIBRATION | treatment hr segments=start month: 0; hazard ratio: 0.84106; withdrawal rate 12m=control: 0.04; experimental: 0.04; discontinuation rate 12m=0; post discontinuation hazard ratio=1 |
| PFS_MEDIAN_CALIBRATED | PFS | ALTERNATIVE | PUBLIC_AGGREGATE_CALIBRATION | treatment hr segments=start month: 0; hazard ratio: 0.5; withdrawal rate 12m=control: 0.08; experimental: 0.08; discontinuation rate 12m=0; post discontinuation hazard ratio=1 |
| OS_DELAYED_NON_PH | OS | ALTERNATIVE_STRESS | ASSUMED_STRESS | treatment hr segments=start month: 0; hazard ratio: 1; start month: 4; hazard ratio: 0.65; withdrawal rate 12m=control: 0.04; experimental: 0.04; discontinuation rate 12m=0; post discontinuation hazard ratio=1 |
| PFS_DELAYED_NON_PH | PFS | ALTERNATIVE_STRESS | ASSUMED_STRESS | treatment hr segments=start month: 0; hazard ratio: 1; start month: 1; hazard ratio: 0.6; withdrawal rate 12m=control: 0.08; experimental: 0.08; discontinuation rate 12m=0; post discontinuation hazard ratio=1 |
| OS_WANING_AFTER_DISCONTINUATION | OS | ALTERNATIVE_STRESS | ASSUMED_STRESS | treatment hr segments=start month: 0; hazard ratio: 0.7; withdrawal rate 12m=control: 0.04; experimental: 0.04; discontinuation rate 12m=0.35; post discontinuation hazard ratio=1 |
| PFS_WANING_AFTER_DISCONTINUATION | PFS | ALTERNATIVE_STRESS | ASSUMED_STRESS | treatment hr segments=start month: 0; hazard ratio: 0.74; withdrawal rate 12m=control: 0.08; experimental: 0.08; discontinuation rate 12m=0.45; post discontinuation hazard ratio=1 |

The scenario registry is reported without pooling so reviewers can distinguish null, alternative, non-proportional-effect, and operational-stress behavior.

## Exact Execution and Failure Accounting

| Scenario | Requested | Completed | Failed | Failure rate | Failure detail |
| --- | --- | --- | --- | --- | --- |
| OS_NULL_REFERENCE | 100000 | 100000 | 0 | 0.000% | Not applicable |
| PFS_NULL_HIGH_DROPOUT | 100000 | 100000 | 0 | 0.000% | Not applicable |
| OS_PUBLISHED_EFFECT | 25000 | 25000 | 0 | 0.000% | Not applicable |
| PFS_PUBLISHED_EFFECT | 25000 | 25000 | 0 | 0.000% | Not applicable |
| OS_MEDIAN_CALIBRATED | 25000 | 25000 | 0 | 0.000% | Not applicable |
| PFS_MEDIAN_CALIBRATED | 25000 | 25000 | 0 | 0.000% | Not applicable |
| OS_DELAYED_NON_PH | 25000 | 25000 | 0 | 0.000% | Not applicable |
| PFS_DELAYED_NON_PH | 25000 | 25000 | 0 | 0.000% | Not applicable |
| OS_WANING_AFTER_DISCONTINUATION | 25000 | 25000 | 0 | 0.000% | Not applicable |
| PFS_WANING_AFTER_DISCONTINUATION | 25000 | 25000 | 0 | 0.000% | Not applicable |

| Aggregate requested | Aggregate completed | Aggregate failed | Reconciliation |
| --- | --- | --- | --- |
| 400000 | 400000 | 0 | PASS |

### Execution Status Rationale

| Scenario | Execution status | Execution rationale |
| --- | --- | --- |
| OS_NULL_REFERENCE | PASS | Run executed and all replicates are accounted: requested=100000, completed=100000, failed=0. |
| PFS_NULL_HIGH_DROPOUT | PASS | Run executed and all replicates are accounted: requested=100000, completed=100000, failed=0. |
| OS_PUBLISHED_EFFECT | PASS | Run executed and all replicates are accounted: requested=25000, completed=25000, failed=0. |
| PFS_PUBLISHED_EFFECT | PASS | Run executed and all replicates are accounted: requested=25000, completed=25000, failed=0. |
| OS_MEDIAN_CALIBRATED | PASS | Run executed and all replicates are accounted: requested=25000, completed=25000, failed=0. |
| PFS_MEDIAN_CALIBRATED | PASS | Run executed and all replicates are accounted: requested=25000, completed=25000, failed=0. |
| OS_DELAYED_NON_PH | PASS | Run executed and all replicates are accounted: requested=25000, completed=25000, failed=0. |
| PFS_DELAYED_NON_PH | PASS | Run executed and all replicates are accounted: requested=25000, completed=25000, failed=0. |
| OS_WANING_AFTER_DISCONTINUATION | PASS | Run executed and all replicates are accounted: requested=25000, completed=25000, failed=0. |
| PFS_WANING_AFTER_DISCONTINUATION | PASS | Run executed and all replicates are accounted: requested=25000, completed=25000, failed=0. |

Every failed replicate remains in the denominator accounting above; failures are not silently deleted from the evidence surface.

## Operating Characteristics and Monte Carlo Precision

| Scenario | Class | Rejections / analyzed | Estimate | MCSE | Wilson 95% interval |
| --- | --- | --- | --- | --- | --- |
| OS_NULL_REFERENCE | KEY_NULL | 2525 / 100000 | 2.525% | 0.000496109 | 2.430% to 2.624% |
| PFS_NULL_HIGH_DROPOUT | KEY_NULL_OPERATIONAL_STRESS | 2504 / 100000 | 2.504% | 0.000494095 | 2.409% to 2.603% |
| OS_PUBLISHED_EFFECT | ALTERNATIVE | 23688 / 25000 | 94.752% | 0.00141033 | 94.469% to 95.022% |
| PFS_PUBLISHED_EFFECT | ALTERNATIVE | 24581 / 25000 | 98.324% | 0.000811889 | 98.157% to 98.476% |
| OS_MEDIAN_CALIBRATED | ALTERNATIVE | 10919 / 25000 | 43.676% | 0.00313688 | 43.062% to 44.292% |
| PFS_MEDIAN_CALIBRATED | ALTERNATIVE | 25000 / 25000 | 100.000% | 0 | 99.985% to 100.000% |
| OS_DELAYED_NON_PH | ALTERNATIVE_STRESS | 20166 / 25000 | 80.664% | 0.00249777 | 80.170% to 81.149% |
| PFS_DELAYED_NON_PH | ALTERNATIVE_STRESS | 24564 / 25000 | 98.256% | 0.000827909 | 98.086% to 98.411% |
| OS_WANING_AFTER_DISCONTINUATION | ALTERNATIVE_STRESS | 19647 / 25000 | 78.588% | 0.0025944 | 78.075% to 79.092% |
| PFS_WANING_AFTER_DISCONTINUATION | ALTERNATIVE_STRESS | 24036 / 25000 | 96.144% | 0.00121775 | 95.898% to 96.376% |

### Precision and Design Decisions

| Scenario | Precision status | Precision rationale | Design status | Design rationale |
| --- | --- | --- | --- | --- |
| OS_NULL_REFERENCE | PASS | Completed 100000 >= 100000; failure rate 0 <= 0.001; MCSE 0.000496109 <= 0.0005. | PASS | Wilson contains alpha=True; absolute deviation 0.00025 <= tolerance 0.00148833 is True. |
| PFS_NULL_HIGH_DROPOUT | PASS | Completed 100000 >= 100000; failure rate 0 <= 0.001; MCSE 0.000494095 <= 0.0005. | PASS | Wilson contains alpha=True; absolute deviation 4e-05 <= tolerance 0.00148229 is True. |
| OS_PUBLISHED_EFFECT | PASS | Completed 25000 >= 25000; failure rate 0 <= 0.001. | NOT_PREDEFINED | No minimum power criterion was prespecified; estimate is descriptive. |
| PFS_PUBLISHED_EFFECT | PASS | Completed 25000 >= 25000; failure rate 0 <= 0.001. | NOT_PREDEFINED | No minimum power criterion was prespecified; estimate is descriptive. |
| OS_MEDIAN_CALIBRATED | PASS | Completed 25000 >= 25000; failure rate 0 <= 0.001. | NOT_PREDEFINED | No minimum power criterion was prespecified; estimate is descriptive. |
| PFS_MEDIAN_CALIBRATED | PASS | Completed 25000 >= 25000; failure rate 0 <= 0.001. | NOT_PREDEFINED | No minimum power criterion was prespecified; estimate is descriptive. |
| OS_DELAYED_NON_PH | PASS | Completed 25000 >= 25000; failure rate 0 <= 0.001. | NOT_PREDEFINED | No minimum power criterion was prespecified; estimate is descriptive. |
| PFS_DELAYED_NON_PH | PASS | Completed 25000 >= 25000; failure rate 0 <= 0.001. | NOT_PREDEFINED | No minimum power criterion was prespecified; estimate is descriptive. |
| OS_WANING_AFTER_DISCONTINUATION | PASS | Completed 25000 >= 25000; failure rate 0 <= 0.001. | NOT_PREDEFINED | No minimum power criterion was prespecified; estimate is descriptive. |
| PFS_WANING_AFTER_DISCONTINUATION | PASS | Completed 25000 >= 25000; failure rate 0 <= 0.001. | NOT_PREDEFINED | No minimum power criterion was prespecified; estimate is descriptive. |

Probability estimates, numerators, denominators, Monte Carlo standard errors, and Wilson intervals above are rendered directly from the authoritative scientific JSON. No result number is manually transcribed into this report.

## Prespecified Criteria and Interpretation

| Control | Criterion | Scope |
| --- | --- | --- |
| Key Null Min Completed | 100000 | All applicable scenarios |
| Alternative Min Completed | 25000 | All applicable scenarios |
| Alternative Precision Justification | At 25,000 completed replicates the worst-case binomial MCSE is no greater than sqrt(0.25/25000)=0.003163. Alternative and stress-scenario probabilities are descriptive because no sponsor-approved performance threshold or MCID is available. | All applicable scenarios |
| Target Mcse Key Null | 0.0005 | All applicable scenarios |
| Max Failure Rate | 0.001 | All applicable scenarios |
| Analytic Null Probability | 0.025 | All applicable scenarios |
| Analytic Null Abs Tolerance Floor | 0.001 | All applicable scenarios |
| Analytic Null Mcse Multiplier | 3 | All applicable scenarios |
| Wilson Confidence Level | 0.95 | All applicable scenarios |
| Null Acceptance | Wilson interval contains alpha and absolute deviation is no greater than max(0.001, 3*MCSE); upper Wilson bound is not required to be below alpha. | All applicable scenarios |

Design conclusions are scenario-specific. Null scenarios assess error control; alternatives and stress cases characterize behavior under their stated assumptions. Published effects, reconstructed comparators, or calibration values are not promoted to clinically justified target effects or minimum clinically important differences.

## Representative Simulated Trial Paths

| Role | Scenario | Search index | Seed binding | Events | Censors | Z statistic | One-sided p-value | Decision and selection evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reject | OS_NULL_REFERENCE | 6 | scenario=2026081401; selection=2026081490 | control=235; experimental=211 | control=142; experimental=167 | -2.30637 | 0.0105451 | REJECT — First eligible trial in governed search order |
| non_reject | OS_NULL_REFERENCE | 1 | scenario=2026081401; selection=2026081490 | control=232; experimental=235 | control=145; experimental=143 | 0.0638509 | 0.525456 | DO_NOT_REJECT — First eligible trial in governed search order |
| near_alpha_boundary | OS_NULL_REFERENCE | 2945 | scenario=2026081401; selection=2026081490 | control=232; experimental=211 | control=145; experimental=167 | -1.96066 | 0.0249594 | REJECT — absolute distance from alpha=4.05688e-05 |

These are actual aggregate paths selected from the governed OS null scenario using the frozen scenario binding, independent selection seed, and deterministic search rules. They are simulated trials, not original TROPIC participants, and they do not substitute for aggregate operating-characteristic estimates.

## Deterministic Edge-Case Verification Fixtures

| Fixture | Role | Seed | Analysis status | Failure reason | Z statistic | One-sided p-value | Reject | Events | Expected | Validation status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| POSITIVE_FAVORABLE | positive | 2026081491 | COMPLETED | Not applicable | -7.51381 | 2.87157e-14 | Yes | 48 | COMPLETED_REJECT | PASS |
| NEGATIVE_UNFAVORABLE | negative | 2026081492 | COMPLETED | Not applicable | 7.51381 | 1 | No | 48 | COMPLETED_DO_NOT_REJECT | PASS |
| BOUNDARY_NO_EVENTS | boundary_non_estimable | 2026081493 | FAILED | zero_logrank_variance | Not applicable — non-estimable | Not applicable — non-estimable | Not applicable — non-estimable | 0 | FAILED_ZERO_VARIANCE | PASS |

These deliberately artificial separated-time and zero-event fixtures verify sign, decision, and non-estimable boundary handling. They are software-validation cases, not representative simulated trial paths and not scientific operating-characteristic results.

## Change Control and Deviations

| Item | Final result |
| --- | --- |
| Deviations from the frozen MAP | None |

## Verification and Validation Evidence

| Check | Evidence / result |
| --- | --- |
| Analytic Null Benchmark | status: PASS; rule: Wilson interval contains alpha and absolute deviation is no greater than max(0.001, 3*MCSE); upper Wilson bound is not required to be below alpha.; scenario ids: OS_NULL_REFERENCE; PFS_NULL_HIGH_DROPOUT |
| Representative Trial Selection | status: PASS; roles found: reject; non_reject; near_alpha_boundary; note: Scenario-derived aggregate trial examples; no subject rows are retained. |
| Logrank Edge Fixture Status | status: PASS; note: Artificial positive, negative, and non-estimable fixtures; not simulated trial paths. |
| Accounting Identity | status: PASS; rule: requested = completed + failed for every scenario |

## Seeds, Hashes, and Reproduction

### Observed Execution Environment

| Component | Recorded identity |
| --- | --- |
| Python | 3.12.13 |
| NumPy | 2.2.6 |
| PyYAML | 6.0.3 |
| Floating-point dtype | float64 |
| Random-number generator | numpy.random.PCG64 |
| Dependency lock | requirements-ci.lock |

### Scenario Seed Ledger

| Scenario | Seed | Scenario SHA-256 |
| --- | --- | --- |
| OS_NULL_REFERENCE | 2026081401 | 7adc14f9810532d962c09ca7dbff26c177370ed9eed7e45ee1a5a23042d450a7 |
| PFS_NULL_HIGH_DROPOUT | 2026081402 | 8107f34d985c617abd9c505588fb5735f7f5602216420ec9e083024101c6183e |
| OS_PUBLISHED_EFFECT | 2026081403 | 4aa624a9495fc3c5ea0f3fd41650e539618761281efcb710c71b13d68bd2f615 |
| PFS_PUBLISHED_EFFECT | 2026081404 | abf18d3af342404d347c4f3efc140af77f51b988d4c2efdc13d31e8417b9edf5 |
| OS_MEDIAN_CALIBRATED | 2026081405 | 0b9c86fe0ad86e93cd56d2084cf4b5d31e775668efcae0aed188366e06bfaf70 |
| PFS_MEDIAN_CALIBRATED | 2026081406 | 61fc45f12ce1db4b691c82d8252f5263cc8ed225a5d2d482c9e985e1b5017028 |
| OS_DELAYED_NON_PH | 2026081407 | 8f4757706e1587997cc40bc36ecc5e7fe1a45a42744fe38c8be9a0eb8a2a10cb |
| PFS_DELAYED_NON_PH | 2026081408 | b857a9a989abae48810e5718eca46519c3bccdbba7929fa74a68bfce23b31727 |
| OS_WANING_AFTER_DISCONTINUATION | 2026081409 | b24e9201196c430248db4ed62b7dd0b078d2afdd4f91a77682802c47c3e30374 |
| PFS_WANING_AFTER_DISCONTINUATION | 2026081410 | ee4aae8c9cdb8db3d8898e754b3dcd55f4f1fd7f5646a0808b95cef13ccd33fd |

### Artifact Bindings

| Artifact | SHA-256 |
| --- | --- |
| Governed protocol | 09798cd52adedd742a10f39266c67df0d9fe40b4c693912e4962b47601446b61 |
| Authoritative result file | 768d969176ff611e6f581516772272a77af23151efb05d747a9a5ccecbb42c5b |
| Protocol recorded by result | 09798cd52adedd742a10f39266c67df0d9fe40b4c693912e4962b47601446b61 |
| Scenario registry | da115050f9d3fb69202b7154814c0eb204852efbe99f9b6107e548419f3f7768 |
| Simulation code | 3fb535efdfea04955795619e0d209723aa35f88d70ce9429ae4667adc4ec0da2 |
| Scientific output | bad4514234456f7749160ea56888867d63fbf60825716783c77a55817fa11c2b |

Reproduce the scientific JSON with `python3 platform/simulation_precision.py`; rebuild both reviewer documents with `python3 platform/build_simulation_report.py`. Identical governed inputs and seeds must reproduce byte-identical scientific content and reviewer reports.

## Limitations and Qualification Boundary

- **Classification:** NON_MIDD_NON_CONFIRMATORY_DATA_FREE_METHODS_EVALUATION
- **Model Influence:** LOW
- **Evidence Status:** INFORMATIONAL_ONLY
- **Authoritative Patient Data Used:** No
- **External Validation Completed:** No

This evidence surface does not establish authoritative CbzP subject-level data, a clinically justified minimum effect, external model validation, independent organizational review, sponsor approval, or regulator alignment. It must not be used for clinical, labeling, filing, or patient-level decisions.

## References and Governing Basis

- [TROPIC simulation-precision research basis](../docs/SIMULATION_PRECISION_RESEARCH.md)
- [ICH M15: General Principles for Model-Informed Drug Development](https://database.ich.org/sites/default/files/ICH_M15_Step4_Final_Guideline_2026_0129.pdf)
- [ICH E9(R1): Estimands and Sensitivity Analysis](https://database.ich.org/sites/default/files/E9-R1_Step4_Guideline_2019_1203.pdf)
- [FDA: Adaptive Designs for Clinical Trials of Drugs and Biologics](https://www.fda.gov/media/78495/download)
- [FDA: Complex Innovative Trial Design Meeting Program](https://www.fda.gov/drugs/development-resources/complex-innovative-trial-design-meeting-program)
- [ADEMP framework](https://doi.org/10.1002/sim.8086)
- [OCTAVE framework](https://doi.org/10.1002/sim.70449)
