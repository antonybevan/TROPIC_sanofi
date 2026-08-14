# FDA/ICH pre-shipment readiness research

**Assessment date:** 2026-08-15

**Repository scope:** TROPIC controlled clinical-submission simulation

**Machine profile:** [`config/fda_readiness_profile.yaml`](../config/fda_readiness_profile.yaml)

**Checker:** [`platform/check_submission_readiness.py`](../platform/check_submission_readiness.py)

## Executive conclusion

Large-pharma submission readiness is a controlled release process, not a final
polish pass. The common pattern is to lock the intended question and data
standards, qualify the analysis systems, validate critical outputs with
risk-proportionate independent evidence, reconcile and explain findings, build
the eCTD package from controlled sources, and obtain documented statistical,
clinical, data-management, programming, quality, and submission-owner review.

TROPIC now exposes that pattern as a machine-readable readiness profile. The
profile is deliberately **blocked** for regulatory use: the public repository
does not contain a genuine final SAS/ODA seal, organizationally independent QC,
Part 11/CSV qualification, sponsor-approved simulation thresholds, or the
licensed/data-owner approvals needed for a filing. That is the professional
answer in an interview: the controls are visible, and the boundary is not
hand-waved.

## What FDA/ICH sources make explicit

The following are the governing expectations translated into operating
controls. They are not a claim that every internal pharmaceutical SOP is
written identically.

| Evidence area | Current official signal | Practical pre-shipment control |
|---|---|---|
| Quality by design and risk | ICH E6(R3) asks sponsors to identify critical-to-quality factors prospectively, use risk-proportionate processes, and maintain fit-for-purpose validated computerized systems. | Maintain a CTQ/risk register, assign control owners, and scale QC to the decision risk. |
| Estimand and sensitivity | FDA/ICH E9(R1) provides a structured framework for the treatment effect of interest, objectives, design, conduct, analysis, and interpretation. | Freeze the estimand, intercurrent-event strategy, populations, and sensitivity set before programming. |
| Standardized study data | FDA technical-conformance material expects supported standards, Define-XML, reviewer orientation, and conformance findings with explanations. | Produce SDTM/ADaM/Define-XML, ADRG/SDRG, traceability, validator output, and a disposition for every open issue. |
| Reviewer guides and source | FDA’s technical guide recommends ADRG placement with analysis data and identifies source code, metadata, software, and execution context as review aids. | Make the reviewer package self-explanatory and bind each result to source, version, environment, and run record. |
| eCTD mechanics | FDA publishes versioned eCTD specifications, validation criteria, transmission rules, and file-format requirements; the applicable version depends on center and submission context. | Check the current center-specific rules immediately before filing; never treat a historical v3.2.2 example as universal. |
| Data-standard sample | FDA’s standardized-data sample process is technical conformance feedback, not scientific review; findings should be resolved or explained in reviewer documentation. | Run the applicable validator/sample process, preserve the report and run record, and obtain owner disposition. |
| Simulation / innovative design | FDA’s complex-innovative-design materials ask for parameter configurations, justification, example trials, type I error, power, expected sample size/duration, and estimation properties over plausible scenarios. | Use a frozen ADEMP/OCTAVE-style protocol, null and stress scenarios, operating characteristics, MCSE/failure accounting, and a signed interpretation boundary. |
| Model/simulation delivery | FDA’s model/data format page describes data, Define, reviewer-guide, dependency, execution-order, input/output, model-code, and simulation-code expectations. | Package the data/code/configuration/dependency graph and make replay deterministic from a clean checkout. |
| Electronic records | FDA Part 11 guidance keeps validation and audit-trail decisions risk-based; computerized-systems guidance emphasizes secure timestamped audit trails, accuracy, completeness, and reliability. | For regulated use, add approved CSV/CSA evidence, access roles, audit-trail review, backup/restore, change control, retention, and qualified signatures. |

## Big-pharma operating model translated to this repository

| Workstream | Industry pre-shipment question | TROPIC evidence / current state |
|---|---|---|
| Governance | What may be claimed, by whom, and under which intended use? | `PRODUCT_CLAIM`, quality-system boundary, regulatory baseline, and release profile. **Pass for the simulation claim; blocked for regulated use.** |
| Statistical design | Is the estimand and analysis strategy approved and traceable? | SAP, simulation MAP, E9(R1)-aligned protocol, scenario registry, generated report. **Partial for a real sponsor study.** |
| Simulation precision | Are results numerically reproducible and their uncertainty visible? | 400,000 governed replicates, fixed seeds, analytic null checks, Wilson/MCSE, independent verifier, representative trials. **Pass for this bounded methods evaluation.** |
| Model qualification | Does the model cover the assumptions needed for the intended decision? | Explicitly labelled public-aggregate/stress assumptions and qualification boundary. **Not qualified for MIDD, confirmatory, or filing use.** |
| Data and standards | Are data, metadata, terminology, and traceability submission-reviewable? | Define-XML, ADRG/SDRG/BDRG, conformance records, traceability matrix. **Partial until authorized data-bearing checks and findings disposition are complete.** |
| Programming/QC | Is critical output correctness supported independently and risk-proportionately? | SAS/R/admiral/reconciliation architecture plus tests. **Not organizationally independent QC.** |
| Computerized systems | Is the environment validated, secure, controlled, and auditable? | Repository hardening, least-privilege local controls, and explicit non-Part-11 claim. **Not qualified as a regulated system.** |
| Submission operations | Is the package current, complete, validated, and owner-approved? | Deterministic Module 5/eCTD-style package and package checks. **Partial; current-version confirmation, owner approvals, and final seal remain.** |

## Simulation-specific professional precision checklist

Before a simulation result can influence a real design or filing, add and
approve the following controls rather than silently extending the current
engine:

1. Confirm the estimand, intercurrent-event strategy, target estimand
   population, decision threshold, and clinically meaningful effect with the
   statistician and clinical team.
2. Build a scenario grid covering the null, plausible alternatives, delayed or
   non-proportional effects, dropout/missingness mechanisms, treatment
   discontinuation, recruitment/calendar effects, and joint endpoint/covariate
   dependence relevant to the decision.
3. Quantify type I error, power, bias, variability, coverage, convergence,
   expected sample size, duration, and failure rates. Report Monte Carlo
   standard errors and stop/precision rules rather than only point estimates.
4. Use deterministic, auditable seed streams with an explicit replay contract;
   verify invariance across approved batch/parallel execution modes and retain
   per-scenario/per-replicate lineage sufficient to investigate a failure.
5. Compare the production engine to an independent implementation or analytic
   reference for critical estimators, including edge cases and deliberately
   adversarial fixtures.
6. Separate representative examples and synthetic stress fixtures from actual
   scenario-derived trials, and never present them as patient evidence.
7. Freeze code, dependencies, compiler/interpreter identity, protocol,
   scenario registry, and outputs under a change-control record; document every
   deviation and unresolved issue with an owner and disposition.

The current TROPIC engine implements the deterministic, high-replication,
analytic-benchmark, independent-verifier portion of this list. It does not
claim the joint-dependence, missing-not-at-random, outer-loop uncertainty,
stratified-estimator reproduction, or organizationally independent validation
needed for a broader regulatory simulation claim.

## Interview-ready answer

> “Before shipping, I would treat the analysis as a controlled submission
> product: lock the estimand and SAP, map critical-to-quality risks, validate
> critical datasets and TFLs with independent evidence, run standards and
> package checks, preserve reviewer guides and traceability, and require a
> clean-checkout seal plus accountable statistical, clinical, programming,
> quality, and submission-owner review. In this repository I implemented that
> evidence map and fail-closed checker, but I would not call it FDA-ready until
> the real SAS/ODA run, independent QC, system qualification, data/rights
> approvals, current eCTD validation, and final owner signoffs are complete.”

## References

- [FDA Study Data Technical Conformance Guide](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/study-data-technical-conformance-guide-technical-specifications-document)
- [FDA eCTD submission standards and validation criteria](https://www.fda.gov/drugs/electronic-regulatory-submission-and-review/ectd-submission-standards-ectd-v322-and-regional-m1)
- [FDA Electronic Common Technical Document](https://www.fda.gov/drugs/electronic-regulatory-submission-and-review/electronic-common-technical-document-ectd)
- [FDA Electronic Common Technical Document v4.0](https://www.fda.gov/drugs/electronic-regulatory-submission-and-review/electronic-common-technical-document-ectd-v40)
- [FDA Study Data Standards Resources](https://www.fda.gov/industry/fda-data-standards-advisory-board/study-data-standards-resources)
- [FDA Data Standards Catalog](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/data-standards-catalog)
- [FDA Submit Standardized Data Sample](https://www.fda.gov/drugs/electronic-regulatory-submission-and-review/submit-standardized-data-sample-fda)
- [FDA Complex Innovative Trial Design Meeting Program](https://www.fda.gov/drugs/development-resources/complex-innovative-trial-design-meeting-program)
- [FDA Model | Data Format](https://www.fda.gov/about-fda/center-drug-evaluation-and-research-cder/model-data-format)
- [FDA Computerized Systems Used in Clinical Trials](https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/fda-bioresearch-monitoring-information/guidance-industry-computerized-systems-used-clinical-trials)
- [FDA Part 11, Electronic Records; Electronic Signatures](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/part-11-electronic-records-electronic-signatures-scope-and-application)
- [FDA E9(R1) Statistical Principles](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/e9r1-statistical-principles-clinical-trials-addendum-estimands-and-sensitivity-analysis-clinical)
- [ICH E6(R3) Good Clinical Practice](https://database.ich.org/sites/default/files/ICH_E6%28R3%29_Step4_FinalGuideline_2025_0106_ErrorCorrections_2025_1024.pdf)
