# TROPIC

## Controlled clinical-submission simulation

TROPIC is an end-to-end clinical biometrics implementation for Study EFC6193 / NCT00417079. It takes de-identified SDTM through ADaM, statistical outputs, Define-XML, reviewer documentation, and a deterministic FDA Module 5-style package.

The work is designed to be reviewed as a controlled delivery system, not as a themed portfolio. Its evidence includes real SAS execution, an independent R implementation, selected admiral re-derivation, machine reconciliation, schema and metadata checks, a real Pinnacle 21 Community run, package validation, and hash-bound release records.

> TROPIC is a controlled clinical-submission simulation. It is not a regulatory submission, a sponsor-approved reanalysis, a Part 11 validated system, licensed Pinnacle 21 clearance, or independent organizational QC.

The binding claim is [Product and Evidence Claim](docs/PRODUCT_CLAIM.md). The qualification gap is [Quality System Boundary](docs/QUALITY_SYSTEM_BOUNDARY.md).

## Review the package

| Review path | Purpose |
|---|---|
| [Module 5 package](08_submission_package/README.md) | Reviewer-facing datasets, metadata, programs, guides, CSR, and BIMO surface |
| [Analysis Data Reviewer's Guide](07_reviewer_explanation/guides/ADRG.md) | ADaM derivations, traceability, conformance, and known differences |
| [Clinical Study Data Reviewer's Guide](07_reviewer_explanation/guides/SDRG.md) | SDTM source boundary, standards decisions, and data limitations |
| [Traceability matrix](07_reviewer_explanation/guides/TRACEABILITY_MATRIX.md) | Source-to-analysis-to-output lineage |
| [TFL Gallery](05_outputs/tfl/TFL_Gallery.html) | Portable static figure review surface |
| [Dashboard visual QC](06_qc_evidence/audit/DASHBOARD_VISUAL_QC.md) | Five-tab local dashboard acceptance evidence |
| [Simulation Model Analysis Plan](07_reviewer_explanation/simulation_model_analysis_plan.md) | Prospective M15/ADEMP/OCTAVE methods-evaluation protocol, estimand, scenarios, and precision criteria |
| [Simulation Model Analysis Report](07_reviewer_explanation/simulation_report.md) | Generated operating characteristics, Monte Carlo uncertainty, representative trials, and limitations |
| [FDA/ICH readiness research](docs/FDA_READINESS_RESEARCH_2026-08-15.md) | Big-pharma pre-shipment control model, official sources, and current blockers |
| [Scoped official-source inventory](config/regulatory_source_inventory.yaml) | 48 FDA/ICH/CDISC/eCFR entries classified by applicability, final/draft status, evidence, and owner action |
| [Current release note](docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md) | Release evidence and residual limitations |
| [Reviewer guide](docs/INTERVIEWER_GUIDE.md) | A short, evidence-led walkthrough |

**Current controlled release:** tag `v0.3.0-clinical-simulation` · [release note](docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md)

## Evidence at a glance

| Control | Current evidence | Boundary |
|---|---|---|
| Production programming | SAS 9.4 on SAS OnDemand for Academics | A recorded `oda`/`local` provenance guard is required; simulation mode has no double-programming value |
| Validation programming | Independent R implementations for seven MP-arm ADaM datasets | Methodological independence, not organizational independence |
| Third implementation | admiral for ADSL, OS, and PFS | Risk-based corroboration, not full-dataset triple programming |
| Reconciliation | Record and value comparisons plus result-level controls | Applies to the documented populations and tolerances only |
| Standards | ADaMIG 1.3, SDTMIG 3.4, Define-XML 2.1, local stylesheet, CDISC CORE | Alignment and local conformance, not agency acceptance |
| Pinnacle 21 | Community 4.1.0, FDA engine 2508.1, ADaMIG 1.3 (FDA), 7 datasets / 121,320 records / 0 rejects | Informative only; 30 open issue groups (2,373 occurrences) and an incompatible-CLI caveat remain; Enterprise not executed |
| Submission package | Deterministic Module 5-style tree, cSDRG/ADRG, programs, Define, eCTD v3.2.2 example backbone | Structural simulation; no gateway submission |
| Simulation precision | Governed fixed-design TTE methods evaluation with explicit seeds, high-replication null scenarios, MCSE/Wilson intervals, and generated MAP/report | Informative engineering evidence only; public aggregate and stress assumptions are not original-trial IPD, an MCID, or a pivotal design decision |
| Release control | CI, findings, logs, SHA-256 manifests, clean-checkout verification | Integrity controls, not Part 11 electronic signatures |

## Data provenance

| Data | N | Use |
|---|---:|---|
| Real de-identified MP SDTM | 371 | SAS/R ADaM production and validation; not redistributed in Git |
| Reconstructed/synthetic CbzP | 378 | Reporting comparison only; not included in reconciled ADaM |

OS and PFS use published Kaplan-Meier reconstruction methods for the CbzP comparator. Secondary CbzP endpoints are synthetic. Comparative outputs are therefore descriptive demonstrations and must not be described as confirmatory trial results.

The separate simulation-precision workstream is data-free. It uses public
aggregate assumptions and explicitly labelled stress scenarios to evaluate the
numerical behavior of a simplified TROPIC-like fixed two-arm time-to-event
design. It does not simulate authoritative TROPIC patients, validate a clinical
minimum effect, or change the product claim. See the
[current-practice research decision](docs/SIMULATION_PRECISION_RESEARCH.md).

## Controlled pipeline

The study manifest drives a 40-stage evidence chain:

```text
authorized SDTM
  -> controlled staging and source checks
  -> paired SAS/R ADaM plus selected admiral derivation
  -> record, value, and result reconciliation
  -> catalog-controlled tables, figures, and listings
  -> Define-XML, ARM, and specification conformance
  -> governed simulation operating characteristics and generated MAP/report
  -> reviewer guides and CSR
  -> Module 5/eCTD-style materialization
  -> log, finding, manifest, and release seals
```

The package and factory are intentionally separate:

```text
08_submission_package/     reviewer-facing deliverable surface
00_governance/             reproducibility and data-rights controls
01_source_data/            source intake; patient data excluded from Git
02_specifications/         analysis authority and specifications
03_metadata/               ADaM spec, Define-XML, ARM, USDM
04_analysis_datasets/      SAS/R programs and local XPT products
05_outputs/                controlled TFL outputs and ARS
06_qc_evidence/            reconciliation, findings, gates, run records
07_reviewer_explanation/   ADRG, cSDRG source, BDRG, traceability
config/                    study, output, evidence, and regulatory contracts
platform/                  orchestration, validation, packaging, release controls
tests/                     data-free and data-bearing regression checks
```

## Run and verify

Requirements: Python 3.10+, R 4.6.0+, and either SAS 9.4 or configured SAS OnDemand access for a genuine production run.

```bash
# Recheck the committed release without patient data or SAS
python3 scripts/verify_release.py

# Run the data-free smoke path
python3 platform/cibuild.py --demo

# Run the full controlled DAG with genuine SAS execution
python3 platform/cibuild.py --real-sas

# Recheck the current regulatory and qualification boundary
python3 platform/check_regulatory_baseline.py --check-only

# Review the FDA/ICH readiness map; --strict is the release go/no-go mode
python3 platform/check_submission_readiness.py

# Validate the scoped official-source inventory (does not replace legal or center review)
python3 platform/check_regulatory_source_inventory.py
```

The full run requires the authorized local SDTM source and credentials; see [Reproducibility](00_governance/REPRODUCIBILITY.md) and the [ODA runbook](docs/runbooks/ODA_GUIDE.md). A clean clone intentionally does not contain patient-level source or derived XPTs.

For maintainers, [`CONTRIBUTING.md`](CONTRIBUTING.md) defines the review and release workflow;
[`SECURITY.md`](SECURITY.md) defines the private-reporting and data-boundary rules.

For reviewer-facing visuals, open the [TFL Gallery](05_outputs/tfl/TFL_Gallery.html). The [Shiny dashboard visual-QC record](06_qc_evidence/audit/DASHBOARD_VISUAL_QC.md) documents the data-bearing local acceptance capture; a bare clone safely opens the dashboard in disclosed data-free mode because patient-level inputs are not distributed.

## Regulatory baseline

The executable baseline is [config/regulatory_baseline.yaml](config/regulatory_baseline.yaml). It is anchored to the FDA Study Data Technical Conformance Guide (June 2026), FDA electronic-systems guidance (October 2024), 21 CFR Part 11, ICH E6(R3), ADaMIG 1.3, SDTMIG 3.4, and Define-XML 2.1.

Current package controls include:

- `csdrg.pdf` and `adrg.pdf` with FDA STF classification;
- separate ADaM and SDTM Define-XML files and co-located local stylesheets;
- analysis source programs for primary/secondary outputs;
- a source blank CRF that is never presented as `acrf.pdf`;
- explicit non-claims for Part 11, independent QC, Enterprise validation, and gateway acceptance; and
- a CI gate that fails if those boundaries, filenames, or the reconciled Pinnacle 21 evidence regress.

## License and source rights

This repository currently declares **no open-source license**; public visibility does not grant
permission to copy or redistribute it. See [Licensing and source rights](docs/LICENSING.md).
Source clinical data, published materials, standards content, SAS, and Pinnacle 21 remain subject
to their respective access terms and licenses. Nothing in this repository grants redistribution or
regulatory-use rights to those materials.
