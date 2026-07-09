# TROPIC Biometrics Delivery Operating Model

> Status: controlled delivery model, not a claim of submission readiness.
> This document translates the repository from "a pipeline that runs" into a
> cross-functional clinical programming delivery system.

## 1. Why This Exists

The project should not be judged by whether scripts can produce files. In modern
clinical programming, the meaningful product is an evidence system:

```text
source data
-> specification
-> metadata
-> analysis dataset
-> output
-> QC evidence
-> reviewer explanation
-> submission package
```

Each layer has a different professional owner, a different failure mode, and a
different type of evidence. A serious submission-style pipeline makes those
handoffs explicit. This operating model is therefore written in terms of
functions and gates, not folders.

This does not simulate departments. One person may implement the package, but the
work still has to respect real ownership boundaries: statistics owns the
scientific question, standards owns metadata contracts, programming owns
derivation implementation, QC challenges the evidence, regulatory writing
explains it, and platform engineering proves the run is reproducible.

## 2. Research Baseline

The model below is grounded in external expectations and standards:

| Source | What it establishes for this project |
|---|---|
| FDA Study Data for CDER/CBER | Supported clinical study data standards include SDTM, ADaM, and Define-XML; supported versions are governed through the FDA Data Standards Catalog. |
| FDA Study Data Technical Conformance Guide, June 2026 | Analysis files help FDA understand how study-report analyses were created; Define-XML is central metadata; ADRG gives reviewer context and does not replace Define-XML; source code for ADaM and primary/secondary efficacy tables and figures should be provided. |
| CDISC ADaM | ADaM is both dataset and metadata standardization supporting generation, replication, review, and traceability among results, analysis data, and SDTM. |
| CDISC Define-XML | Define-XML transmits metadata for tabular datasets and is required by FDA/PMDA to identify datasets, variables, controlled terms, and other metadata. |
| CDISC Analysis Results Standard | Analysis results metadata supports automation, reproducibility, reusability, and traceability to Protocol/SAP and input ADaM. |
| ICH E6(R3) | Quality should be designed into clinical trials, critical-to-quality factors identified, and effort applied using a proportionate risk-based approach. |
| ICH E9(R1) | Estimands connect the clinical question to population, treatment, endpoint, intercurrent-event strategy, and summary measure; analyses and sensitivity analyses should align to that target. |
| ICH MedDRA | Medical coding terminology supports registration, documentation, and safety monitoring of medical products. |

References are listed in section 8.

## 3. Operating Doctrine

TROPIC will use this doctrine:

```text
1. No analysis output exists without a specification anchor.
2. No specification is executable until represented in metadata.
3. No analysis dataset is trusted until reconciled or justified by risk tier.
4. No TFL is complete until its analysis result, input data, program, and QC evidence are linked.
5. No package is reviewer-ready until limitations and known differences are explained.
6. No run is evidence unless its inputs, code, environment, outputs, and checksums are recorded.
```

This is intentionally stricter than "the code works." It treats every generated
file as a claim that must be backed by evidence.

## 4. Delivery Functions and Handoffs

### 4.1 Governance and Scope Control

**Purpose:** define what the package can claim, what it cannot claim, which source
material is authoritative, and what limitations must be carried to reviewers.

**Controlled inputs:**

- Study identity and public trial documentation.
- SAP v4.0 and SAP lock memo.
- Audit findings register.
- Reproducibility and data-access boundaries.

**Controlled outputs:**

- Scope statement.
- Decision log.
- Assumption log.
- Issue and known-differences log.
- Release readiness statement.

**Current TROPIC assets:**

- `TROPIC_SAP_v4.0_industry_grade.docx`
- `audit/SAP_LOCK_REVIEW_MEMO.md`
- `audit/findings_register.csv`
- `REPRODUCIBILITY.md`
- `README.md`

**Gate:** a build cannot be described as reviewer-ready unless the governing SAP,
data limitations, synthetic comparator status, unresolved findings, and execution
mode are all consistent across README, ADRG, reproducibility docs, and telemetry.

### 4.2 Data Access, Privacy, and Source Intake

**Purpose:** ensure patient-level source data is handled as governed clinical
data, not as a public sample dataset.

**Controlled inputs:**

- PDS/Sanofi source SDTM files.
- Protocol, CRF, data dictionary, and source documentation.
- Data-use restrictions and exclusion rules.

**Controlled outputs:**

- Source data inventory.
- Source variable catalog.
- Subject and domain reconciliation.
- Data anomaly log.
- Source profiling report.

**Current TROPIC assets:**

- `01_raw_source/`
- `REPRODUCIBILITY.md`
- `03_validation_r/v_staging_ingest.R`
- `03_validation_r/v_sdtm_validation.R`
- `06_telemetry/conformance/core_sdtm34_report.json`

**Gate:** ADaM programming should not be treated as locked until source inventory,
subject counts, source-domain availability, missingness, date precision limits,
and source exclusions are documented.

### 4.3 Statistical and Analysis Specification

**Purpose:** translate protocol/SAP/publication rules into implementation-ready
analysis definitions before programming.

**Controlled inputs:**

- SAP authority.
- Protocol and clinical study report/publication evidence.
- Study parameters in `study_config.yaml`.
- Estimand and endpoint decisions.

**Controlled outputs:**

- Population definitions.
- Endpoint definitions.
- Model specifications.
- Sensitivity analysis specifications.
- Analysis assumptions and benchmark hierarchy.

**Current TROPIC assets:**

- `study_config.yaml`
- `TROPIC_SAP_v4.0_industry_grade.docx`
- `ANALYSIS_REPORT.md`
- `08_reviewers_guides/TRACEABILITY_MATRIX.md`

**Gate:** every ADaM parameter, population flag, censoring rule, and TFL result
must reference a specification section or a documented assumption.

### 4.4 Standards and Metadata Governance

**Purpose:** convert the specification into a machine-readable contract that
programs, conformance checks, Define-XML, and reviewers can inspect.

**Controlled inputs:**

- Analysis specification.
- ADaMIG/OCCDS expectations applicable to the dataset structure.
- Controlled terminology and value-level metadata.

**Controlled outputs:**

- ADaM specification workbook.
- Define-XML and stylesheet.
- ARM/ARS result metadata.
- Traceability matrix.
- Spec-to-define and spec-to-data conformance evidence.

**Current TROPIC assets:**

- `00_specifications/ADaM_spec.xlsx`
- `07_define_xml/define.xml`
- `07_define_xml/define_sdtm.xml`
- `07_define_xml/check_define_conformance.R`
- `03_validation_r/spec_data_checks.R`
- `12_ars/`
- `audit/adam_variable_traceability.csv`

**Gate:** analysis datasets and TFL outputs cannot be promoted unless the metadata
contract is internally consistent and the known metadata gaps are explained.

### 4.5 ADaM and BIMO Programming

**Purpose:** implement analysis-ready datasets from controlled source and metadata,
with independent validation proportional to scientific risk.

**Controlled inputs:**

- Source/staging data.
- Analysis specifications.
- Metadata contract.
- Study manifest.

**Controlled outputs:**

- ADaM XPT datasets.
- BIMO `clinsite` dataset.
- Production logs.
- Validation logs.
- Program-to-dataset traceability.

**Current TROPIC assets:**

- `02_production_sas/`
- `03_validation_r/`
- `04_adam/`
- `study_manifest.yaml`
- `06_telemetry/cibuild.py`

**Gate:** datasets require cell-level reconciliation or a documented risk-based QC
alternative. A simulated SAS mode cannot be represented as independent
double-programming evidence.

### 4.6 Efficacy, Safety, and TFL Production

**Purpose:** express the analysis evidence as reviewer-facing tables, figures, and
listings with traceability to analysis datasets and specifications.

**Controlled inputs:**

- Reconciled analysis datasets.
- Output shells and numbering conventions.
- Analysis results metadata.

**Controlled outputs:**

- TFL output index.
- Tables, figures, and listings.
- Statistical result objects behind figures.
- Program map from output to source code.

**Current TROPIC assets:**

- `09_tfl/tfl_generation.R`
- `09_tfl/tfl_stats.R`
- `09_tfl/output/`
- `09_tfl/TFL_Gallery.html`
- `12_ars/tropic_ard.csv`

**Gate:** outputs are not complete when files render. They are complete when the
rendered result, analysis dataset, program, metadata, QC method, and reviewer
explanation are all linked.

### 4.7 Risk-Based QC and Validation

**Purpose:** challenge the evidence with effort scaled to consequence of error.

**Controlled inputs:**

- Risk tier by artifact.
- Production datasets and outputs.
- Independent validation programs.
- Conformance rules and checks.

**Controlled outputs:**

- Dataset reconciliation.
- Results reconciliation.
- Conformance reports.
- Log review status.
- Known differences and final QC signoff.

**Current TROPIC assets:**

- `08_reviewers_guides/RISK_BASED_VALIDATION.md`
- `05_reconciliation/`
- `06_telemetry/reconciliation_status.json`
- `06_telemetry/results_reconciliation_status.json`
- `06_telemetry/conformance/`
- `06_telemetry/ADMIRAL_RECONCILIATION.md`
- `06_telemetry/verify_evidence.py`

**Gate:** critical outputs require independent reproduction or a documented reason
why independent reproduction is not possible. Supporting and structural artifacts
require automated conformance, code/log review, or checklist evidence appropriate
to risk.

### 4.8 Reviewer Explanation and Regulatory Package

**Purpose:** make the package understandable to a reviewer who did not build it.

**Controlled inputs:**

- Metadata.
- TFL outputs.
- QC evidence.
- Known limitations and known differences.
- Data provenance and execution mode.

**Controlled outputs:**

- ADRG, SDRG, and BDRG.
- Reviewer README.
- Published concordance report.
- Release notes.
- eCTD-style Module 5 package and sequence.

**Current TROPIC assets:**

- `08_reviewers_guides/ADRG.md`
- `08_reviewers_guides/SDRG.md`
- `08_reviewers_guides/BDRG.md`
- `ANALYSIS_REPORT.md`
- `m5/`
- `11_ectd/0000/`
- `06_telemetry/package_ectd.py`
- `06_telemetry/build_ectd_backbone.py`
- `06_telemetry/materialize_ectd.py`

**Gate:** reviewer documentation must explain what was built, what data were used,
which outputs are synthetic or reconstructed, what QC was performed, which
conformance findings remain, and why the package is or is not release-ready.

### 4.9 Platform Engineering and Release Control

**Purpose:** make execution reproducible, inspectable, and resistant to stale or
misrepresented evidence.

**Controlled inputs:**

- Study manifest.
- Environment locks.
- Pipeline stage definitions.
- Credential/data availability.

**Controlled outputs:**

- Run record.
- Pipeline health telemetry.
- Environment capture.
- Checksums and manifests.
- Rollback and evidence verification controls.

**Current TROPIC assets:**

- `06_telemetry/cibuild.py`
- `06_telemetry/pipeline_health.json`
- `06_telemetry/pipeline_health_log.jsonl`
- `renv.lock`
- `06_telemetry/verify_evidence.py`
- `evidence_layers.yaml`
- `06_telemetry/check_evidence_layers.py`

**Gate:** a release candidate must be bound to one run, one code state, one
environment record, one output manifest, and one reviewer-facing limitation set.

## 5. Handoff Matrix

| Handoff | Producer function | Consumer function | Required evidence |
|---|---|---|---|
| Source intake lock | Data access/source intake | Statistics, standards, programming | Source inventory, subject/domain counts, source limitations, data-use exclusion statement |
| Specification lock | Statistics | Standards, ADaM, TFL, QC | Population, endpoint, model, censoring, sensitivity, assumptions |
| Metadata lock | Standards/metadata | ADaM, TFL, reviewer package | ADaM spec, Define-XML, CT, value-level metadata, traceability |
| ADaM promotion | ADaM/BIMO programming | TFL, QC, reviewer package | XPTs, logs, reconciliation, spec-to-data checks |
| Output promotion | TFL programming | QC, reviewer package | Output files, output index, result metadata, program map |
| QC signoff | QC/validation | Reviewer package, release control | Reconciliation, conformance, log review, known differences |
| Reviewer package lock | Reviewer documentation | Release control | ADRG/SDRG/BDRG, limitation disclosures, concordance narrative |
| Release candidate | Platform/release control | Final reviewer | Run record, hashes, package manifest, evidence verification |

## 6. Current Gap Register

This is not a full audit replacement. It is the operating-model gap list that
should guide the next build steps.

| Gap | Why it matters | Next control |
|---|---|---|
| Evidence layers now exist, but workstream ownership is not machine-readable. | The chain is visible, but the team/function handoffs are still prose. | Add `delivery_workstreams.yaml` and validate it against `evidence_layers.yaml`. |
| Source profiling now has an initial aggregate report, but it is not yet wired as an orchestrator gate. | Source intake should be a distinct gate before ADaM build. | Promote `docs/SOURCE_PROFILING_REPORT.md` / `source_profile_status.json` into the DAG or CI once the report scope is stable. |
| Specification lock exists, but executable spec references are not uniformly enforced per output. | Outputs can drift from SAP/spec without a clear broken link. | Add output-to-spec references to a structured output index. |
| Metadata now has a generated control report, but the report currently records unresolved major findings. | Reviewers need a single metadata control story with honest gaps. | Resolve or explicitly disposition findings in `docs/METADATA_CONTROL_REPORT.md`, especially skipped CT cross-validation, ADaM label errors, and predecessor traceability gaps. |
| TFL completion now has a structured generated index, but it is not yet an orchestrator gate. | Rendered files alone do not prove result traceability. | Promote `docs/TFL_OUTPUT_INDEX.md` / `tfl_output_index_status.json` into the DAG or CI once the report scope is stable. |
| QC evidence is extensive but not yet tied to every handoff gate. | A reviewer should see which gate each QC artifact satisfies. | Extend evidence index with gate ids and workstream ids. |
| Release readiness is intentionally not claimed. | That honesty is good, but the next readiness criteria should be explicit. | Add a release-candidate checklist with blocking vs nonblocking criteria. |

## 7. Implementation Roadmap

### Step 1: Make workstreams executable as metadata

Create `delivery_workstreams.yaml` with functions, required inputs, outputs,
handoff gates, and evidence-layer references.

### Step 2: Build an evidence dashboard

Generate a Markdown or HTML dashboard from `evidence_layers.yaml` and
`delivery_workstreams.yaml`, showing what is present, generated, external,
optional, planned, or missing.

### Step 3: Add gate ids to the orchestrator

Map each `study_manifest.yaml` stage to one or more operating-model gates:
source, spec, metadata, ADaM, output, QC, reviewer, package, release.

### Step 4: Decide CI and orchestrator integration

Add the remaining high-value reports before doing any folder migration:

- CI integration decision record.
- Orchestrator integration plan for architecture reports.

### Step 5: Migrate physical layout only after reports pass

Move files only after compatibility checks exist. The first real migration should
separate code from evidence, not rename folders for appearance.

## 8. References

- FDA Study Data for Submission to CDER and CBER: https://www.fda.gov/industry/study-data-standards-resources/study-data-submission-cder-and-cber
- FDA Study Data Technical Conformance Guide, June 2026: https://www.fda.gov/media/153632/download
- CDISC ADaM: https://www.cdisc.org/standards/foundational/adam
- CDISC Define-XML: https://www.cdisc.org/standards/data-exchange/define-xml
- CDISC Analysis Results Standard: https://www.cdisc.org/standards/foundational/analysis-results-standard
- ICH E6(R3): https://database.ich.org/sites/default/files/ICH_E6%28R3%29_Step4_FinalGuideline_2025_0106.pdf
- ICH E9(R1) training material: https://database.ich.org/sites/default/files/E9%28R1%29%20Training%20Material%20-%20PDF_0.pdf
- ICH MedDRA: https://ich.org/page/meddra
- R Consortium R Submissions Working Group: https://rconsortium.github.io/submissions-wg/
