# TROPIC Pipeline Architecture Redesign

> Status: proposed target operating model. This document is a controlled blueprint
> for redesigning the repository around a submission-style evidence flow before any
> physical file migration is attempted.

## 1. Objective

The current TROPIC repository already has many submission-style controls: a
manifest-driven orchestrator, independent SAS and R tracks, ADaM specifications,
Define-XML, reviewer guides, eCTD-style packaging, and machine-readable telemetry.
The weakness is architectural readability. The numbered folders describe execution
history more than they describe how a biometrics programming function thinks about
evidence.

The redesigned architecture should make this chain obvious:

```text
source data
-> specification
-> metadata
-> analysis dataset
-> output
-> QC evidence
-> reviewer explanation
```

The goal is not to overclaim a regulatory submission. The goal is to make the
repository behave like a disciplined, reviewer-oriented clinical programming
package: specification controlled, metadata governed, traceable, reproducible, and
honest about data/source limitations.

The companion delivery model is
[BIOMETRICS_DELIVERY_OPERATING_MODEL.md](BIOMETRICS_DELIVERY_OPERATING_MODEL.md).
That document describes the professional functions, controlled inputs, outputs,
handoff gates, and current TROPIC gaps. This document describes how those
functions map to repository architecture.

## 2. Source-Backed Design Principles

These principles are grounded in current FDA, CDISC, and ICH expectations rather
than invented folder aesthetics.

| Principle | Source-backed rationale | Architecture consequence |
|---|---|---|
| Use supported clinical study data standards where applicable | FDA lists SDTM, ADaM, and Define-XML as supported study data standards for clinical study submissions, with versions governed by the Data Standards Catalog. | Keep SDTM/ADaM/Define-XML as first-class package assets, not incidental outputs. |
| Treat Define-XML and ADRG as complementary, not interchangeable | FDA's Study Data Technical Conformance Guide says ADRG orients reviewers to analysis datasets and conformance findings, but does not replace complete define.xml metadata. | Separate machine-readable metadata from reviewer explanation, and gate both. |
| Preserve traceability from results to analysis data to source | FDA notes ADaM features promote traceability from analysis results to ADaM datasets and from ADaM datasets to SDTM, and recommends complete metadata for ADaM contents. | Make traceability a core pipeline object, not an appendix. |
| Keep metadata central | CDISC describes ADaM as data plus metadata, and Define-XML as metadata for SDTM, SEND, and ADaM tabular datasets. | Specifications and metadata must be controlled before ADaM build and output generation. |
| Apply risk-proportionate validation | ICH E6(R3) emphasizes quality by design, critical-to-quality factors, and proportionate risk-based approaches. | Critical scientific derivations get independent reproduction; lower-risk items get automated conformance, code/log review, and checklist controls. |

References:

- FDA Study Data for CDER and CBER: https://www.fda.gov/industry/study-data-standards-resources/study-data-submission-cder-and-cber
- FDA Study Data Technical Conformance Guide, June 2026: https://www.fda.gov/media/153632/download
- CDISC ADaM: https://www.cdisc.org/standards/foundational/adam
- CDISC Define-XML: https://www.cdisc.org/standards/data-exchange/define-xml
- ICH E6(R3): https://database.ich.org/sites/default/files/ICH_E6%28R3%29_Step4_FinalGuideline_2025_0106.pdf

## 3. Target Repository Model

The target layout separates controlled clinical evidence layers from reusable
platform machinery.

```text
TROPIC/
├── 00_governance/
│   ├── project_charter.md
│   ├── scope_statement.md
│   ├── decision_log.md
│   ├── issue_log.md
│   ├── assumption_log.md
│   └── known_limitations.md
│
├── 01_source_data/
│   ├── data_use_statement.md
│   ├── source_data_inventory.xlsx
│   ├── source_variable_catalog.xlsx
│   ├── source_profile_report.md
│   ├── source_to_analysis_mapping.xlsx
│   └── real_sdtm/
│
├── 02_specifications/
│   ├── sap_authority/
│   ├── derived_analysis_spec.md
│   ├── population_definitions.md
│   ├── endpoint_definitions.md
│   ├── model_specification.md
│   └── sensitivity_analysis_spec.md
│
├── 03_metadata/
│   ├── adam/
│   │   ├── ADaM_spec.xlsx
│   │   ├── value_level_metadata.xlsx
│   │   └── controlled_terms.xlsx
│   ├── define/
│   │   ├── define.xml
│   │   ├── define.pdf
│   │   └── conformance/
│   ├── arm/
│   └── traceability_matrix.xlsx
│
├── 04_analysis_datasets/
│   ├── adam/
│   ├── sdtm_uplift/
│   ├── datasetjson/
│   └── logs/
│
├── 05_outputs/
│   ├── shells/
│   ├── output_index.xlsx
│   ├── tables/
│   ├── figures/
│   ├── listings/
│   └── analysis_results_metadata/
│
├── 06_qc_evidence/
│   ├── qc_plan.md
│   ├── risk_based_validation_matrix.xlsx
│   ├── reconciliation/
│   ├── conformance/
│   ├── logs/
│   ├── manifests/
│   └── final_qc_signoff.md
│
├── 07_reviewer_explanation/
│   ├── adrg.md
│   ├── sdrg.md
│   ├── bdrg.md
│   ├── reviewer_readme.md
│   ├── published_concordance_report.md
│   └── known_differences_log.md
│
├── 08_submission_package/
│   ├── m5/
│   └── ectd/
│
├── platform/
│   ├── cibuild.py
│   ├── package_ectd.py
│   ├── build_ectd_backbone.py
│   ├── materialize_ectd.py
│   └── status_emitters/
│
└── studies/
    └── DEMO02/
```

This is now the physical operating model. The repository root is organized by
evidence ownership; remaining substructure changes should be made only when they
reduce real handoff ambiguity or validation risk.

## 4. Current-to-Target Mapping

| Current asset | Target layer | Notes |
|---|---|---|
| `config/study_manifest.yaml` | `config/` plus platform consumers | Keep as a governed control source; split only if the multi-study engine needs a reusable package boundary. |
| `config/study_config.yaml` | `config/` | Clinical parameters remain a governed control source consumed by programs and metadata checks. |
| `03_metadata/adam/ADaM_spec.xlsx` | `03_metadata/adam/ADaM_spec.xlsx` | The ADaM spec is metadata control, even though it is specification-adjacent. |
| `01_source_data/` | `01_source_data/` | Preserve raw data exclusion rules and data-use documentation. |
| `04_analysis_datasets/programs/sas/` | `04_analysis_datasets/programs/sas/` | Production programs are owned by the analysis-dataset layer. |
| `04_analysis_datasets/programs/r/` | `04_analysis_datasets/programs/r/` | Independent validation programs are owned beside the dataset layer they validate. |
| `04_analysis_datasets/adam/` | `04_analysis_datasets/adam/` | Build outputs only; should remain regenerable. |
| `06_qc_evidence/reconciliation/` | `06_qc_evidence/reconciliation/` | Reconciliation programs and their records are QC evidence. |
| `platform/` | `platform/` | Platform is now reserved for orchestration/build logic and machine status emitters. |
| `03_metadata/define/` | `03_metadata/define/` | Define-XML is the machine-readable metadata delivery layer. |
| `07_reviewer_explanation/guides/` | `07_reviewer_explanation/` | ADRG/SDRG/BDRG explain, contextualize, and disclose limitations. |
| `05_outputs/tfl/` | `05_outputs/` | Separate output source programs, output shells, rendered tables, figures, and listings. |
| `04_analysis_datasets/datasetjson/` | `04_analysis_datasets/datasetjson/` | Dataset-JSON is an exchange representation of datasets. |
| `08_submission_package/ectd/`, `08_submission_package/m5/` | `08_submission_package/` | Package materialization belongs after reviewer explanation and QC gates. |
| `05_outputs/ars/` | `05_outputs/analysis_results_metadata/` | ARS/ARM belongs to output traceability. |
| `03_metadata/usdm/` | `03_metadata/` or `08_submission_package/` | Keep as study-level structured metadata until submission use is clearer. |
| `07_reviewer_explanation/tools/shiny/` | `platform/reviewer_tools/` or `07_reviewer_explanation/tools/` | Treat as optional review aid, not a source of record. |
| `06_qc_evidence/audit/` | `06_qc_evidence/audit/` | Audit files are evidence and should be indexed by run/version. |

## 5. Gated Orchestration Model

The orchestration should make the control points explicit. A professional run is not
"execute files in folder order"; it is a gated evidence pipeline.

```text
Gate 0  environment and data-access preflight
Gate 1  source data inventory and profiling
Gate 2  specification authority and assumptions lock
Gate 3  metadata completeness and conformance
Gate 4  analysis dataset build
Gate 5  dataset-level reconciliation
Gate 6  output generation
Gate 7  results-level reconciliation and output QC
Gate 8  reviewer documentation build
Gate 9  submission package materialization
Gate 10 release manifest, checksums, and final signoff
```

Each gate should emit:

```text
status: pass | fail | warning | not_applicable
inputs: files, hashes, manifest version
programs: source code and versions
outputs: artifacts produced
checks: conformance, reconciliation, log review, or checklist
known_limitations: explicit reviewer-facing disclosures
```

## 6. Evidence Flow Contract

Every clinically meaningful output should be traceable across seven objects:

| Evidence object | Required content |
|---|---|
| Source data | dataset, source variable, source document, data limitation |
| Specification | population, endpoint, method, censoring/imputation rule, model |
| Metadata | dataset, variable, label, type, origin, derivation, codelist, value-level rule |
| Analysis dataset | ADaM dataset, parameter, flags, source carry-through variables |
| Output | table/figure/listing number, title, population, analysis dataset, program |
| QC evidence | risk tier, QC method, reconciliation result, log review, known differences |
| Reviewer explanation | ADRG/SDRG/BDRG section explaining source, methods, conformance, limitations |

This contract should eventually be represented in a machine-readable manifest, not
only prose. The existing `config/study_manifest.yaml`, `06_qc_evidence/audit/adam_variable_traceability.csv`,
and `07_reviewer_explanation/guides/TRACEABILITY_MATRIX.md` are the starting point.

## 7. Risk-Based Validation Model

The redesign keeps the current validation philosophy, but places it in the
architecture:

| Artifact class | Risk | Preferred QC |
|---|---:|---|
| Treatment arm, population flags, ADSL anchors | Critical | Independent recomputation, count reconciliation, reviewer explanation |
| OS/PFS ADTTE and headline KM/Cox results | Critical | Independent dataset derivation, independent survival run, benchmark comparison |
| TEAE, grade >=3, SAE flags | High | Independent flag checks, count reconciliation, listing spot checks |
| AE SOC/PT summaries and supporting efficacy | High | Frequency/result reconciliation, output review |
| Baseline/disposition summaries | Medium | Count/range checks, code review, log review |
| Metadata labels, codelists, formats | Medium | Automated conformance, spec-to-data checks |
| Titles, layout, cosmetic output formatting | Low | Visual review checklist |

The key doctrine remains:

```text
Critical bespoke logic -> independent reproduction
Reusable transformation -> validated function/macro plus tests and metadata checks
Standard table from stable ADaM -> independent counts/results and log review
Formatting -> checklist review
All deliverables -> traceability to source, spec, metadata, program, QC, reviewer guide
```

## 8. Migration Plan

### Phase 0: Blueprint and index, no behavior change

- Add this architecture document.
- Add README pointer from the existing pipeline architecture section.
- Create an inventory of current assets mapped to the seven evidence layers.
- No file moves, no orchestrator changes.

Verification:

```bash
git diff -- docs/PIPELINE_ARCHITECTURE_REDESIGN.md README.md
```

### Phase 1: Introduce evidence-layer manifests

- Add `config/evidence_layers.yaml` describing source, specification, metadata, datasets,
  outputs, QC evidence, reviewer docs, and submission package assets. **Initial
  index implemented.**
- Link existing files without moving them.
- Add a lightweight check that all referenced artifacts exist or are explicitly
  marked generated, external, optional, or planned. **Initial verifier
  implemented as `platform/check_evidence_layers.py`.**

Verification:

```bash
python3 platform/check_evidence_layers.py
```

### Phase 2: Split code from evidence

- Keep `config/study_manifest.yaml` as the execution source of truth.
- Move or alias reusable code from `platform/` and `06_qc_evidence/reconciliation/` into
  `platform/`.
- Move produced run evidence into `06_qc_evidence/` or generate an indexed view
  there.
- Preserve backward-compatible paths until the build is green with both layouts.

Verification:

```bash
python3 platform/cibuild.py --demo
python3 platform/verify_evidence.py
```

### Phase 3: Align deliverable folders

- Create target folders for source, specifications, metadata, analysis datasets,
  outputs, QC evidence, reviewer explanation, and submission package.
- Move assets in small batches with redirects or compatibility shims where needed.
- Update packaging scripts only after source and output paths are stable.

Verification:

```bash
python3 platform/cibuild.py --dry-run
python3 platform/cibuild.py --demo
```

### Phase 4: Submission package hardening

- Generate final reviewer-facing artifact index.
- Bind output manifests to checksums.
- Produce final known-limitations and known-differences summaries.
- Ensure eCTD-style package materializes only after metadata, output, QC, and
  reviewer gates pass.

Verification:

```bash
python3 platform/cibuild.py --use-cached-sas
python3 platform/verify_evidence.py
```

## 9. Non-Overclaiming Rules

Use these phrases:

```text
submission-style biometrics programming pipeline
ADaM/SDTM/Define-XML-oriented demonstration package
risk-based validation
reviewer-oriented documentation
synthetic/reconstructed comparator arm
not submission-ready
not independent clinical evidence
single-author methodological reconciliation
```

Avoid these phrases unless a future validated sponsor process actually supports
them:

```text
FDA-ready submission
regulatory submission package
GxP validated system
official SAP implementation
full CDISC conformance
100% double programmed
independent clinical re-analysis
```

## 10. Immediate Next Decision

The no-move architecture report is now implemented as
[DELIVERY_EVIDENCE_DASHBOARD.md](DELIVERY_EVIDENCE_DASHBOARD.md), generated by
`platform/build_delivery_dashboard.py` from `config/evidence_layers.yaml` and
`config/delivery_workstreams.yaml`. The next implementation step should be to add
domain-specific control reports under this same model, starting with:

```text
1. CI integration decision
2. physical code/evidence split plan
3. orchestrator integration of architecture reports
```

After those reports are stable, the project can decide whether to add the
architecture checks to CI.
