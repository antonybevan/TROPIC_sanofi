# Regulatory Workflow Research for a Submission-Grade Biometrics Pipeline

Generated: 2026-07-08

This note translates current regulatory and standards guidance into a practical
department workflow for the TROPIC pipeline. It is intentionally conservative:
where guidance permits flexibility, the workflow records the decision, the risk
basis, and the evidence expected from each function.

## Primary Sources Checked

- FDA Study Data Technical Conformance Guide, June 2026:
  https://www.fda.gov/media/153632/download
- FDA guidance, Providing Regulatory Submissions in Electronic Format -
  Standardized Study Data:
  https://www.fda.gov/regulatory-information/search-fda-guidance-documents/providing-regulatory-submissions-electronic-format-standardized-study-data
- FDA guidance, Electronic Systems, Electronic Records, and Electronic
  Signatures in Clinical Investigations, 2024:
  https://www.fda.gov/media/166215/download
- ICH E6(R3), Guideline for Good Clinical Practice, Step 4, 2025:
  https://database.ich.org/sites/default/files/ICH_E6%28R3%29_Step4_FinalGuideline_2025_0106.pdf
- ICH E8(R1), General Considerations for Clinical Studies:
  https://database.ich.org/sites/default/files/E8-R1_Guideline_Step4_2022_0204%20%281%29.pdf
- ICH E9(R1), Estimands and Sensitivity Analysis:
  https://database.ich.org/sites/default/files/E9-R1_Step4_Guideline_2019_1203.pdf
- CDISC SDTM:
  https://www.cdisc.org/standards/foundational/sdtm
- CDISC ADaM:
  https://www.cdisc.org/standards/foundational/adam
- CDISC Define-XML:
  https://www.cdisc.org/standards/data-exchange/define-xml
- CDISC Analysis Results Standard:
  https://www.cdisc.org/standards/foundational/analysis-results-standard
- ICH MedDRA:
  https://ich.org/page/meddra
- SCDM Risk-Based Clinical Data Management public review chapter, 2025:
  https://scdm.org/wp-content/uploads/2025/09/RB-CDM-Final-Public-Review-Version-9.9.pdf

## Core Interpretation

The current regulatory direction is not "100% double programming." It is
risk-based, traceability-driven, specification-controlled validation.

Double programming remains a valid validation method, especially for critical
derivations and primary efficacy outputs, but it is not the regulatory
requirement by itself. The requirement is that submitted data, metadata,
programs, reviewer guides, systems, and results are reliable, traceable,
reviewable, fit for purpose, and supported by documented quality management.

The FDA Study Data Technical Conformance Guide requires standardized study data,
complete metadata, reviewer orientation, traceability, source code for ADaM
datasets and primary/secondary efficacy tables and figures, and software
version/operating-system disclosure in the ADRG. ICH E6(R3) and E8(R1) push the
operating philosophy further: quality must be built into design, critical-to-
quality factors must be identified prospectively, and controls must be
proportionate to the risk to participant safety and reliability of trial results.

## What Replaces Blanket Double Programming

The preferred current model is a validation strategy with tiers:

| Risk tier | Examples | Expected validation evidence |
|---|---|---|
| Critical | Primary endpoints, key secondary endpoints, ADSL, population flags, censoring logic, treatment exposure, safety analyses used in labeling or major conclusions | Independent reproduction or independently implemented check; source-to-result traceability; unit tests for derivation edge cases; metadata conformance; output/result reconciliation; documented statistical review |
| High | Important supportive endpoints, ISS/ISE inputs, major safety domains, BIMO, exposure-response, subgroup/forest outputs | Independent targeted programming or independently computed result checks; peer code review; dataset/metadata checks; output hash binding; risk-based QC signoff |
| Medium | Standard listings, non-key descriptive summaries, routine derived variables | Peer review; automated tests; conformance checks; metadata/spec review; targeted spot checks based on risk |
| Low | Cosmetic rendering, navigation pages, non-inferential indexes, generated dashboards | Automated generation, checksum/hash checks, smoke tests, visual review where applicable |

This means a professional pipeline should not simply ask, "Was it double
programmed?" It should ask:

1. What decision could this artifact influence?
2. What is the consequence if it is wrong?
3. What independent evidence proves the artifact is correct enough for that use?
4. Is the derivation traceable from protocol/SAP to SDTM to ADaM to result to
   reviewer explanation?
5. Is the system that generated or transferred it fit for purpose and under
   change control?

## Department Workflow Model

### 1. Clinical Governance and Study Leadership

Owns the study intent, scope, and claim discipline.

Workflow:

- Define the clinical objectives and critical-to-quality factors before build.
- Ensure protocol, SAP, estimands, endpoints, populations, safety scope, and
  submission claims are aligned.
- Approve the Study Data Standardization Plan and major standards decisions
  early enough to avoid late conversion risk.
- Maintain the issue/risk register and decide what can be disclosed versus what
  must block release.

Evidence:

- Protocol/SAP authority record.
- CTQ/risk register.
- Decision log for endpoint/population/scope changes.
- Release-readiness statement that refuses unsupported claims.

TROPIC fit:

- `audit/SAP_LOCK_REVIEW_MEMO.md`
- `study_config.yaml`
- `docs/RELEASE_CANDIDATE_CHECKLIST.md`
- `audit/findings_register.csv`

### 2. Clinical Data Management / Clinical Data Science

Owns source data integrity, data flow, database-readiness evidence, and source
data review strategy.

Workflow:

- Define the Data Management Plan and data-flow diagram from source creation to
  final durable storage.
- Identify critical data elements and critical processes based on CTQ factors.
- Apply risk-based source data review, source data verification, edit checks,
  medical review listings, anomaly detection, and query management.
- Maintain audit trails, data originator evidence, transfer specifications, and
  data cutoff/database lock evidence.

Evidence:

- Data Management Plan.
- Source inventory and data-flow map.
- Critical data element register.
- Query/anomaly resolution evidence.
- Transfer reconciliation and lock evidence.

TROPIC fit:

- `01_raw_source/`
- `docs/SOURCE_PROFILING_REPORT.md`
- `06_telemetry/source_profile/`
- future target: add a formal source data flow diagram and data transfer
  reconciliation manifest.

### 3. Medical Coding and Safety Review

Owns clinical meaning of adverse events, medical history, concomitant
medications, seriousness, severity, relationship, and safety signal review.

Workflow:

- Code AEs and medical concepts using controlled medical terminology such as
  MedDRA where applicable.
- Review coding consistency, seriousness/severity consistency, special-interest
  terms, deaths, discontinuations, and laboratory outliers.
- Feed safety review decisions into SDTM/ADaM derivations and reviewer
  explanations.

Evidence:

- Coding dictionary/version.
- Coding review logs.
- Safety review listings and medical signoff.
- AE/SAE reconciliation evidence where applicable.

TROPIC fit:

- `04_adam/adae_*.xpt`
- `09_tfl/output/`
- future target: explicit MedDRA/version and safety medical review signoff.

### 4. Standards and Metadata Governance

Owns SDTM/ADaM/Define-XML/controlled terminology integrity.

Workflow:

- Select standards versions supported by the relevant FDA Data Standards Catalog
  context.
- Maintain SDTM and ADaM metadata as controlled specifications.
- Ensure Define-XML describes datasets, variables, origins, derivations,
  codelists, value-level metadata, methods, and ARM/analysis metadata where
  used.
- Run standards conformance checks and disposition findings.

Evidence:

- SDTM/ADaM specifications.
- Define-XML and stylesheet.
- aCRF mapping to SDTM variables.
- Controlled terminology/dictionary versions.
- Conformance reports and findings disposition.

TROPIC fit:

- `00_specifications/ADaM_spec.xlsx`
- `07_define_xml/define.xml`
- `07_define_xml/define_sdtm.xml`
- `docs/METADATA_CONTROL_REPORT.md`

Current gap:

- Metadata control is still `warning` because CT validation is skipped, ADaM
  conformance has errors, predecessor/source traceability is incomplete, and
  metadata drift findings remain open.

### 5. Biostatistics

Owns estimands, methods, analysis decisions, and interpretation.

Workflow:

- Translate clinical objectives into estimands, endpoints, populations,
  intercurrent-event strategies, sensitivity analyses, and supplementary
  analyses.
- Define statistical methods and windows before programming.
- Review analysis results against SAP intent and clinical interpretation.
- Approve deviations, data-handling assumptions, and sensitivity analysis
  interpretation.

Evidence:

- SAP and estimand specification.
- Analysis decision log.
- Sensitivity/supplementary analysis rationale.
- Statistical review signoff.

TROPIC fit:

- `TROPIC_SAP_v4.0_industry_grade.docx`
- `study_config.yaml`
- `ANALYSIS_REPORT.md`
- future target: explicit estimand register aligned to ADaM/TFL metadata.

### 6. Statistical Programming

Owns implementation of analysis datasets, TFLs, result metadata, and submitted
program source.

Workflow:

- Build ADaM from SDTM according to controlled specifications.
- Generate TFLs and analysis-results metadata from controlled inputs.
- Submit source code for ADaM datasets and primary/secondary efficacy tables and
  figures.
- Apply validation depth according to risk tier, not blanket duplication.
- Bind outputs to program versions, dataset hashes, environment, and run record.

Evidence:

- Production programs.
- Independent validation programs or targeted independent checks.
- Unit tests and edge-case tests for critical derivations.
- Dataset and output reconciliation.
- Program-to-output index.
- Software version/OS disclosure in ADRG.

TROPIC fit:

- `02_production_sas/`
- `03_validation_r/`
- `09_tfl/`
- `docs/TFL_OUTPUT_INDEX.md`
- `06_telemetry/build_delivery_controls.py`

Current gap:

- Current live telemetry is `sas_execution_mode=sim`; therefore the current
  dataset reconciliation is not independent SAS-vs-R proof. A release candidate
  must be bound to `oda` or `local` SAS execution, or another documented
  independent validation method with equivalent risk justification.

### 7. Quality Control and Quality Assurance

Owns the validation strategy, independence of audit, CAPA, and inspection
readiness.

Workflow:

- Define validation plans by artifact risk tier.
- Separate routine QC from independent QA audit.
- Review whether controls are adequate to protect participant safety and result
  reliability.
- Ensure deviations, issues, and CAPA are recorded, triaged, resolved, or
  formally dispositioned before release.

Evidence:

- Risk-based validation plan.
- QC checklists and reconciliation outputs.
- Audit findings register.
- CAPA and disposition records.
- Release go/no-go checklist.

TROPIC fit:

- `08_reviewers_guides/RISK_BASED_VALIDATION.md`
- `05_reconciliation/`
- `audit/findings_register.csv`
- `docs/RELEASE_CANDIDATE_CHECKLIST.md`

Current gap:

- Active confirmed Critical/Major audit findings remain release blockers.

### 8. Platform Engineering / Computerized System Assurance

Owns fit-for-purpose execution systems, automation controls, access/change
control, reproducibility, and run integrity.

Workflow:

- Define intended use of each system/tool in the pipeline.
- Validate systems and custom automation based on risk to trial data and result
  reliability.
- Maintain data-flow diagrams, access controls, audit trails, environment locks,
  dependency locks, change control, and disaster/re-run procedures.
- Prove generated artifacts are reproducible or explain why they are controlled
  snapshots.

Evidence:

- System inventory and intended-use classification.
- Risk-based validation evidence.
- CI logs and release run records.
- Dependency/environment lock.
- Audit trail/change-control evidence.

TROPIC fit:

- `renv.lock`
- `.github/workflows/ci.yml`
- `06_telemetry/cibuild.py`
- `06_telemetry/build_delivery_controls.py`
- `06_telemetry/pipeline_health.json`

### 9. Medical Writing and Reviewer Explanation

Owns human-readable explanation, reviewer orientation, and consistency between
CSR, SAP, datasets, TFLs, and guides.

Workflow:

- Explain analysis data, terminology, conformance findings, derivations,
  imputation, limitations, and package organization in reviewer guides.
- Ensure CSR text, Section 14 outputs, ADaM, ARM/ARS, and submitted programs are
  mutually consistent.
- Make limitations explicit rather than hidden in technical artifacts.

Evidence:

- ADRG, SDRG, BDRG, SDSP.
- CSR/analysis report.
- Traceability matrix.
- Known limitations and conformance explanations.

TROPIC fit:

- `08_reviewers_guides/ADRG.md`
- `08_reviewers_guides/SDRG.md`
- `08_reviewers_guides/BDRG.md`
- `08_reviewers_guides/SDSP.md`
- `08_reviewers_guides/TRACEABILITY_MATRIX.md`

### 10. Regulatory Operations / Submission Publishing

Owns eCTD materialization, package structure, lifecycle, file naming, technical
validation, and final publishing integrity.

Workflow:

- Materialize datasets, programs, reviewer guides, define.xml, stylesheets, and
  package metadata into the required eCTD structure.
- Verify file names, folder placement, zero-byte checks, define-to-folder
  consistency, program placement, STF/backbone metadata, and package freshness.
- Ensure the submission package is generated only from a release candidate whose
  upstream evidence is clean or formally dispositioned.

Evidence:

- eCTD package manifest.
- Backbone/STF validation evidence.
- Package freshness checks.
- Final run record and hashes.

TROPIC fit:

- `m5/`
- `11_ectd/`
- `06_telemetry/package_ectd.py`
- `06_telemetry/build_ectd_backbone.py`
- `06_telemetry/materialize_ectd.py`

## Architecture Consequence for TROPIC

The pipeline should keep the existing execution DAG, but the professional
operating model should be governed by evidence gates:

1. Source intake lock.
2. Analysis specification lock.
3. Metadata lock.
4. Analysis dataset promotion.
5. Output promotion.
6. QC signoff.
7. Reviewer package lock.
8. Submission package materialization.
9. Release candidate lock.

Each gate must declare:

- Owner.
- Inputs consumed.
- Artifacts produced.
- Validation method.
- Known risks.
- Required signoff.
- Machine-readable status.

## Immediate Design Decisions

1. Do not claim 100% double programming as the quality model.
2. Do claim risk-based independent validation, with double programming reserved
   for critical/high-risk artifacts.
3. Treat `sim` SAS mode as useful for local smoke testing only, never as release
   evidence.
4. Require CTQ-to-artifact traceability: protocol/SAP -> specification ->
   metadata -> ADaM -> TFL/ARS -> reviewer explanation.
5. Promote metadata control to a true release gate, not a documentation afterthought.
6. Make platform/system assurance explicit: intended use, environment lock,
   change control, run record, and inspection-ready data-flow evidence.

