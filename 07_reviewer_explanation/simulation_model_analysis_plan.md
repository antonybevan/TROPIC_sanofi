# TROPIC Simulation Model Analysis Plan

**Current sealed controlled release:** `v0.3.0-clinical-simulation` · [`docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md`](../docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md)

> **Informative annex boundary.** This plan is a data-free simulation-science methods evaluation layered on the historical sealed clinical-simulation release. It is not MIDD evidence, a filing artifact, confirmatory efficacy evidence, sponsor approval, or evidence of regulator acceptance.

## Document Control

| Item | Governed value |
| --- | --- |
| Protocol identifier | TROPIC-SIM-MAP-001 |
| Protocol version | 1.0.0 |
| Protocol status | FROZEN_MAP |
| Protocol frozen on | 2026-08-14 |
| Full run started after freeze | Yes |
| Prospectively recorded deviations | None |
| Governed protocol SHA-256 | 09798cd52adedd742a10f39266c67df0d9fe40b4c693912e4962b47601446b61 |
| Authoritative result SHA-256 | 768d969176ff611e6f581516772272a77af23151efb05d747a9a5ccecbb42c5b |
| Scientific output SHA-256 | bad4514234456f7749160ea56888867d63fbf60825716783c77a55817fa11c2b |

The result hash above was added by this post-run report build for traceability only. It is not presented as a prospective MAP element; design assumptions, methods, criteria, scenario identities, and seeds are governed by the frozen protocol.

## ICH M15 Context and Model Risk

| Assessment element | Prespecified statement |
| --- | --- |
| Question of interest | Under explicit public-aggregate or stress-test assumptions, what are the rejection probabilities and numerical precision of a one-sided unstratified log-rank test in a simplified TROPIC-like fixed two-arm OS or PFS design? |
| Context of use | Low-influence internal methods evaluation and reviewer training for simulation engineering, numerical precision, and sensitivity to stated design assumptions. |
| Model influence | LOW |
| Consequence of a wrong decision | Misinterpreting numerical operating characteristics as clinical evidence could misstate design performance or treatment benefit; the hard use boundary prevents those decisions from relying on this model. |
| Model risk | MODERATE |
| Model impact | LOW |

### Context and Risk Interpretation

- Scientific assumptions are deliberately simplified and not identifiable from authoritative joint IPD. Consequence severity is potentially high, but model influence is constrained to low by governance and explicit non-use controls.
- No authoritative comparator IPD or joint endpoint/covariate distribution.
- Hazards, dropout, discontinuation, delayed effect, and waning are assumptions.
- No independent organizational statistical or medical review.

## ICH E9(R1) Estimand

| Attribute | Prespecified definition |
| --- | --- |
| Population | Hypothetical randomized participants meeting a simplified TROPIC-like analysis population; fixed public-randomized-design calibration of 377 control and 378 experimental participants. This is distinct from the repository's available real MP cohort of N=371 and does not imply that participant-level data are available. |
| Treatment conditions | control: Synthetic control strategy from randomization through follow-up.; experimental: Synthetic experimental strategy from randomization through follow-up. |
| Variables / endpoints | OS: Time from randomization to death from any cause.; PFS: Time from randomization to progression or death from any cause. |
| Population-level summary | Between-arm survival-distribution contrast evaluated by the one-sided intent-to-treat log-rank statistic; repeated-trial summary is rejection probability. |

### Intercurrent Events

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

Missing observations and administrative censoring are handled according to the governed methods; they are not silently relabelled as intercurrent events.

## ADEMP and OCTAVE Framework

### Objectives and Aims

- Verify a reproducible simulation implementation and characterize operating characteristics; do not reproduce the original TROPIC trial or estimate a clinical treatment effect.
- Estimate Type I error or power and its Monte Carlo uncertainty for the governed scenario grid.
- Verify implementation and characterize fixed-design operating characteristics.

### Characteristics and Data-Generating Mechanisms

- Individual enrollment, piecewise-exponential endpoint time, independent withdrawal, optional treatment discontinuation with post-discontinuation waning, and fixed administrative censoring.
- OS/PFS baseline hazards, treatment-effect shape, withdrawal, and discontinuation assumptions.

### Trial Design and Analysis Methods

| Design element | Governed value |
| --- | --- |
| Allocation Basis | Public randomized design calibration (377 control, 378 experimental), distinct from the repository's available real MP N=371; no authoritative participant-level comparator data are used. |
| Allocation | control: 377; experimental: 378 |
| Alpha One Sided | 0.025 |
| Enrollment Months | 12 |
| Analysis Month | 24 |
| Batch Size | 1000 |
| Analysis Method | ONE_SIDED_UNSTRATIFIED_LOGRANK |
| Omitted Design Feature | Original stratification is not simulated because authoritative joint stratification-factor distributions are unavailable. |
| Endpoint Control Medians Months | OS: 12.7; PFS: 1.4 |

- Fixed parallel two-arm allocation with staggered enrollment and common analysis date.
- One-sided unstratified log-rank test at alpha 0.025.
- Intent-to-treat one-sided log-rank analysis.

### Valuation Metrics and Evidence

- Rejection numerator, denominator, probability, MCSE, and 95% Wilson interval.
- Completed/failed accounting and failure reasons.
- Mean event and censor proportions by randomized arm.
- Type I error or power, Monte Carlo precision, event/censoring rates, and execution failures.
- Protocol/scenario/code hashes, deterministic trials, analytic benchmark, and machine-readable results.

### Parameter Provenance

| Provenance class | Governed assumptions |
| --- | --- |
| Public Aggregate | TROPIC-like arm sizes and aggregate OS/PFS medians are used only as design-calibration assumptions.; Published-effect hazard ratios are public-aggregate scenario inputs, not re-estimated effects. |
| Assumed Stress | Withdrawal, delayed-effect, and discontinuation/waning inputs are engineering stress assumptions. |
| Unavailable | Authoritative joint comparator IPD, endpoint correlations, and intercurrent-event distributions. |

## Scenario Registry

| Scenario | Class | Endpoint | Assumption basis | Varying factors | Replicates | Seed |
| --- | --- | --- | --- | --- | --- | --- |
| OS_NULL_REFERENCE | KEY_NULL | OS | ASSUMED_REFERENCE | treatment hr segments=start month: 0; hazard ratio: 1; withdrawal rate 12m=control: 0.04; experimental: 0.04; discontinuation rate 12m=0; post discontinuation hazard ratio=1 | 100000 | 2026081401 |
| PFS_NULL_HIGH_DROPOUT | KEY_NULL_OPERATIONAL_STRESS | PFS | ASSUMED_STRESS | treatment hr segments=start month: 0; hazard ratio: 1; withdrawal rate 12m=control: 0.25; experimental: 0.25; discontinuation rate 12m=0; post discontinuation hazard ratio=1 | 100000 | 2026081402 |
| OS_PUBLISHED_EFFECT | ALTERNATIVE | OS | PUBLIC_AGGREGATE | treatment hr segments=start month: 0; hazard ratio: 0.7; withdrawal rate 12m=control: 0.04; experimental: 0.04; discontinuation rate 12m=0; post discontinuation hazard ratio=1 | 25000 | 2026081403 |
| PFS_PUBLISHED_EFFECT | ALTERNATIVE | PFS | PUBLIC_AGGREGATE | treatment hr segments=start month: 0; hazard ratio: 0.74; withdrawal rate 12m=control: 0.08; experimental: 0.08; discontinuation rate 12m=0; post discontinuation hazard ratio=1 | 25000 | 2026081404 |
| OS_MEDIAN_CALIBRATED | ALTERNATIVE | OS | PUBLIC_AGGREGATE_CALIBRATION | treatment hr segments=start month: 0; hazard ratio: 0.84106; withdrawal rate 12m=control: 0.04; experimental: 0.04; discontinuation rate 12m=0; post discontinuation hazard ratio=1 | 25000 | 2026081405 |
| PFS_MEDIAN_CALIBRATED | ALTERNATIVE | PFS | PUBLIC_AGGREGATE_CALIBRATION | treatment hr segments=start month: 0; hazard ratio: 0.5; withdrawal rate 12m=control: 0.08; experimental: 0.08; discontinuation rate 12m=0; post discontinuation hazard ratio=1 | 25000 | 2026081406 |
| OS_DELAYED_NON_PH | ALTERNATIVE_STRESS | OS | ASSUMED_STRESS | treatment hr segments=start month: 0; hazard ratio: 1; start month: 4; hazard ratio: 0.65; withdrawal rate 12m=control: 0.04; experimental: 0.04; discontinuation rate 12m=0; post discontinuation hazard ratio=1 | 25000 | 2026081407 |
| PFS_DELAYED_NON_PH | ALTERNATIVE_STRESS | PFS | ASSUMED_STRESS | treatment hr segments=start month: 0; hazard ratio: 1; start month: 1; hazard ratio: 0.6; withdrawal rate 12m=control: 0.08; experimental: 0.08; discontinuation rate 12m=0; post discontinuation hazard ratio=1 | 25000 | 2026081408 |
| OS_WANING_AFTER_DISCONTINUATION | ALTERNATIVE_STRESS | OS | ASSUMED_STRESS | treatment hr segments=start month: 0; hazard ratio: 0.7; withdrawal rate 12m=control: 0.04; experimental: 0.04; discontinuation rate 12m=0.35; post discontinuation hazard ratio=1 | 25000 | 2026081409 |
| PFS_WANING_AFTER_DISCONTINUATION | ALTERNATIVE_STRESS | PFS | ASSUMED_STRESS | treatment hr segments=start month: 0; hazard ratio: 0.74; withdrawal rate 12m=control: 0.08; experimental: 0.08; discontinuation rate 12m=0.45; post discontinuation hazard ratio=1 | 25000 | 2026081410 |

Scenario identifiers, requested replication counts, and seeds are exact governed values. Null, alternative, non-proportional-effect, and operational-stress roles must remain explicit; scenarios are not pooled into an undocumented average.

## Monte Carlo and Operating-Characteristic Methods

- One-sided alpha: 0.025
- Batch size: 1000
- One-sided unstratified log-rank test at alpha 0.025.
- Rejection numerator, denominator, probability, MCSE, and 95% Wilson interval.; Completed/failed accounting and failure reasons.; Mean event and censor proportions by randomized arm.

For every binomial operating characteristic, the report presents the exact numerator and denominator, estimate, Monte Carlo standard error, and Wilson 95% interval supplied by the authoritative scientific JSON.

## Prespecified Acceptance Criteria

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

Execution, Monte Carlo precision, design operating characteristics, and evidence qualification are assessed separately. A successfully executed, precisely estimated unacceptable design remains a design failure or review finding.

## Representative Simulated Trial Path Selection

| Selection element | Governed value |
| --- | --- |
| Scenario Id | OS_NULL_REFERENCE |
| Scenario Seed Binding | 2026081401 |
| Selection Seed | 2026081490 |
| Search Replicates | 5000 |
| Batch Size | 500 |
| Roles | reject: eligibility: one_sided_p_value < alpha; selection rule: first eligible trial in increasing search index; non reject: eligibility: one_sided_p_value >= 0.5; selection rule: first eligible trial in increasing search index; near alpha boundary: eligibility: estimable trial; selection rule: minimum absolute(one_sided_p_value - alpha), tie to smallest search index |

Actual aggregate simulated trial paths are selected deterministically from the governed scenario using a separate selection seed and frozen search rules. They supplement aggregate operating characteristics and do not replace them.

## Deterministic Edge-Case Verification Fixtures

Artificial separated-time and zero-event cases are retained only as software verification fixtures for log-rank direction, decisions, and non-estimable handling.

- Analytic one-sided null rejection probability benchmark.
- Scenario-derived aggregate reject, non-reject, and near-alpha trial examples selected by a frozen seed/search rule.
- Artificial positive, negative, and non-estimable log-rank edge fixtures, labelled as validation fixtures rather than representative trial paths.
- Event-time, censoring, accounting, and parameter-bound invariants.

## Reproducibility, Verification, and Change Control

### Observed Execution Environment

| Component | Recorded identity |
| --- | --- |
| Python | 3.12.13 |
| NumPy | 2.2.6 |
| PyYAML | 6.0.3 |
| Floating-point dtype | float64 |
| Random-number generator | numpy.random.PCG64 |
| Dependency lock | requirements-ci.lock |

The environment above is a post-run traceability record, not a prospective design element. The dependency lock, float64 arithmetic, and PCG64 generator are part of the reproducibility contract.

### Artifact Bindings

| Artifact | Identity |
| --- | --- |
| Governed protocol | config/simulation_protocol.yaml — SHA-256 `09798cd52adedd742a10f39266c67df0d9fe40b4c693912e4962b47601446b61` |
| Authoritative scientific results | platform/simulation_operating_characteristics/simulation_oc_status.json — SHA-256 `768d969176ff611e6f581516772272a77af23151efb05d747a9a5ccecbb42c5b` |
| Scenario registry | da115050f9d3fb69202b7154814c0eb204852efbe99f9b6107e548419f3f7768 |
| Simulation code | 3fb535efdfea04955795619e0d209723aa35f88d70ce9429ae4667adc4ec0da2 |
| Scientific output | bad4514234456f7749160ea56888867d63fbf60825716783c77a55817fa11c2b |

Reproduce with `python3 platform/simulation_precision.py`, then run `python3 platform/build_simulation_report.py`. Identical governed inputs and seeds must reproduce identical scientific JSON and reports.

## Qualification and Claim Boundary

- **Classification:** NON_MIDD_NON_CONFIRMATORY_DATA_FREE_METHODS_EVALUATION
- **Model Influence:** LOW
- **Evidence Status:** INFORMATIONAL_ONLY
- **Authoritative Patient Data Used:** No
- **External Validation Completed:** No

Reconstructed or synthetic CbzP data remain illustrative. This plan does not establish a clinically justified minimum effect, validate virtual patients against source IPD, support a clinical or filing decision, or convert TROPIC into a regulatory submission.

## References and Governing Basis

- [TROPIC simulation-precision research basis](../docs/SIMULATION_PRECISION_RESEARCH.md)
- [ICH M15: General Principles for Model-Informed Drug Development](https://database.ich.org/sites/default/files/ICH_M15_Step4_Final_Guideline_2026_0129.pdf)
- [ICH E9(R1): Estimands and Sensitivity Analysis](https://database.ich.org/sites/default/files/E9-R1_Step4_Guideline_2019_1203.pdf)
- [FDA: Adaptive Designs for Clinical Trials of Drugs and Biologics](https://www.fda.gov/media/78495/download)
- [FDA: Complex Innovative Trial Design Meeting Program](https://www.fda.gov/drugs/development-resources/complex-innovative-trial-design-meeting-program)
- [ADEMP framework](https://doi.org/10.1002/sim.8086)
- [OCTAVE framework](https://doi.org/10.1002/sim.70449)
