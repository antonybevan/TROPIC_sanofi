# TROPIC Simulation Precision — Current-Practice Research and Implementation Decision

**Research cut-off:** 2026-08-14

**Status:** controlled methods-evaluation basis; not clinical or regulatory evidence

**Applies to:** the TROPIC simulation-science workstream only

> TROPIC remains a controlled clinical-submission simulation. The work described
> here does not convert reconstructed or synthetic CbzP records into trial IPD,
> confirmatory efficacy evidence, sponsor approval, or an FDA/EMA submission.

## 1. Decision

Current practice does not define simulation precision as a large replication
count alone. A credible simulation requires a chain of controls:

1. decision-focused question and context of use;
2. model influence, consequence of a wrong decision, and model risk;
3. an estimand-aligned data-generating mechanism;
4. prospective scenario and analysis specification;
5. parameter, assumption, and Monte Carlo uncertainty;
6. verification, validation, and applicability assessment; and
7. reproducible code, seeds, reports, and reviewer evidence.

TROPIC will implement a **data-free methods-evaluation vertical slice** using
public aggregate assumptions and explicitly labelled stress scenarios. It will
measure operating characteristics of a simplified TROPIC-like fixed two-arm
time-to-event design. It will not claim that the simulated virtual patients are
the original trial population or that the design results reproduce the original
trial.

## 2. Current authorities and practice

| Source | Current-practice implication for TROPIC |
|---|---|
| [ICH M15 final guideline (2026)](https://database.ich.org/sites/default/files/ICH_M15_Step4_Final_Guideline_2026_0129.pdf) | State the question of interest, context of use, model influence, consequence of a wrong decision, model risk, and model impact. Predefine technical criteria. Verify code and calculations; validate performance, robustness, and applicability; account for parameter and assumption uncertainty; retain a Model Analysis Plan (MAP) and Model Analysis Report (MAR). |
| [ICH E9(R1)](https://database.ich.org/sites/default/files/E9-R1_Step4_Guideline_2019_1203.pdf) | Define the population, treatment conditions, variable, intercurrent-event strategies, and population summary before selecting the estimator and sensitivity analyses. Do not conflate intercurrent events with missing data. |
| [FDA Adaptive Designs guidance](https://www.fda.gov/media/78495/download) | Evaluate Type I error, power, sample size, duration, bias, and interval coverage as relevant; justify scenarios and replication counts; report representative trials, software, readable code, and random seeds. FDA gives 100,000 iterations per scenario as a generally sufficient Type I-error precision example. |
| [FDA Complex Innovative Trial Design program](https://www.fda.gov/drugs/development-resources/complex-innovative-trial-design-meeting-program) | Make design, analysis, assumptions, scenario configurations, operating characteristics, and conclusions reviewable; retain the evolution and rationale for candidate designs. |
| [ADEMP](https://doi.org/10.1002/sim.8086) | Prospectively structure aims, data-generating mechanisms, estimands, methods, and performance measures, and report Monte Carlo standard errors. |
| [OCTAVE (2026)](https://doi.org/10.1002/sim.70449) | Specify objectives, characteristics of underlying factors, trial designs, analyses, valuation metrics, and evidence. Validate components, edge cases, complete trial flow, and analytical special cases before full-scale runs. |
| [Simulation-guided clinical trials review (2026)](https://doi.org/10.1038/s41573-026-01481-9) | Examine both aggregate operating characteristics and individual simulated trial paths; keep studies valid, transparent, thorough, efficient, and comparable. |
| [Guyot reconstruction](https://doi.org/10.1186/1471-2288-12-9) and [IPDfromKM](https://doi.org/10.1186/s12874-021-01308-8) | Validate reconstruction against digitised curves, risk tables, events, survival probabilities, medians, and effect summaries. Reconstructed IPD remains secondary evidence with uncertainty; it is not authoritative source IPD. |

## 3. Prespecified house controls

These are TROPIC engineering acceptance criteria, not claims that regulators
mandate the exact numerical cut-offs.

| Control | Prespecified criterion |
|---|---|
| Probability precision | Report numerator, denominator, estimate, Monte Carlo standard error `sqrt(p(1-p)/R)`, and a 95% Wilson interval. |
| Key null scenarios | At least 100,000 completed replicates and target MCSE no greater than 0.0005 near one-sided alpha 0.025. |
| Alternative/stress scenarios | At least 25,000 completed replicates unless the MAP contains a prospective precision justification. |
| Type I analytic benchmark | The 95% Monte Carlo interval contains the analytically expected alpha and the absolute deviation is no more than `max(0.001, 3*MCSE)`. A simulation-only strict upper-bound claim would require separate conservative calibration and is not made here. |
| Failure accounting | Requested = completed + failed; failures are never silently removed. A key-scenario failure rate above 0.1% blocks precision acceptance. |
| Seeds | One explicit, unique seed per scenario; the mapping is reported and hash-bound. |
| Reproducibility | Identical protocol, software, and seed inputs reproduce identical scientific JSON content. |
| Scenario coverage | Include reference null, operational-stress null, published-effect, median-calibrated, delayed/non-proportional, and treatment-discontinuation/waning assumptions. |
| Status separation | Execution, Monte Carlo precision, design operating characteristics, and evidence qualification receive separate statuses. A precise unacceptable result cannot be labelled overall PASS. |

## 4. Scope selected for implementation

The controlled implementation will provide:

- an ICH M15 assessment and machine-readable MAP;
- a complete E9(R1)-style estimand and intercurrent-event statement for the
  methods-evaluation question;
- an ADEMP/OCTAVE scenario registry with rationale and explicit assumptions;
- individual-level fixed-design time-to-event simulation with enrolment,
  administrative censoring, independent withdrawal, and selected non-proportional
  or post-discontinuation effect scenarios;
- one-sided log-rank operating characteristics with MCSE and Wilson intervals;
- analytical null checks, invariant tests, malformed-control rejection, and
  deterministic representative trial summaries;
- scenario, protocol, code, and output hashes; and
- generated MAP/MAR reviewer documents plus a clearly labelled Module 5-style
  informational appendix.

## 5. Qualification boundary and remaining gaps

This implementation cannot close the following gaps without new authoritative
evidence or organizational authority:

- authoritative CbzP subject-level source data;
- externally validated correlations among exposure, safety, response,
  progression, and survival;
- a sponsor-approved clinical minimum effect and pivotal decision rule;
- a complete filing-grade estimand package for every TROPIC endpoint;
- independent organizational statistical/medical review;
- regulator alignment or acceptance; and
- validated-system, access-control, electronic-signature, and Part 11 controls.

Accordingly, the model influence is intentionally low: results may demonstrate
simulation engineering and numerical precision, but they must not determine a
clinical, labeling, filing, or patient-level decision.
