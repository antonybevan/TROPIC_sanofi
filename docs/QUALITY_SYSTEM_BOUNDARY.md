# Quality System Boundary

**Document ID:** TROPIC-QSB-001

**Version:** 1.1

**Effective date:** 2026-08-14

**Status:** Controlled

**Applies to:** `v0.3.0-clinical-simulation`

TROPIC is a controlled clinical-submission simulation. It demonstrates engineering and statistical-programming controls that are relevant to regulated delivery. It is not a sponsor quality system, a regulatory filing, or evidence of organizational qualification.

## Control assertions

- `ORGANIZATIONAL_INDEPENDENT_QC=NOT_ESTABLISHED`
- `PART11_VALIDATED_SYSTEM=NOT_ESTABLISHED`
- `LICENSED_PINNACLE21_ENTERPRISE=NOT_EXECUTED`
- `PINNACLE21_COMMUNITY=INFORMATIVE_ONLY`
- `REGULATORY_GATEWAY_ACCEPTANCE=NOT_EXECUTED`
- `ANNOTATED_CRF=NOT_AVAILABLE`

These assertions are machine-checked by `platform/check_regulatory_baseline.py`.

## Evidence status

| Capability | Evidence present | Qualification boundary |
|---|---|---|
| SAS/R double programming | Real MP-arm ADaM was independently implemented in SAS and R and reconciled at record and value level; selected primary analyses also use an admiral track. | Methodological independence is demonstrated. Organizational independence is not established because the work does not have a second accountable human organization or signer. |
| Quality control | Manifest-driven gates, specifications, reconciliation, logs, findings, hashes, and release seals are executable and retained. | These are engineering controls, not independent QC approval. A passing gate cannot approve its own methods or clinical interpretation. |
| Electronic records | Git history, SHA-256 seals, immutable release artifacts, and CI logs provide integrity and reproducibility evidence. | No validated Part 11 system, electronic-signature manifestation, signer identity control, audit-trail review procedure, or qualified infrastructure is claimed. |
| Pinnacle 21 | Pinnacle 21 Community 4.1.0 executed with FDA engine 2508.1 and ADaMIG 1.3 (FDA): 7 datasets, 121,320 records, 0 rejects, and 30 open issue groups / 2,373 occurrences. The hash-bound aggregate evidence is recorded in `06_qc_evidence/conformance/p21_adam_runrecord.md` and `p21_adam_summary.json`. | Informative only. The open findings require qualified disposition; Community is not Enterprise, is not licensed submission clearance, and the generated workbook itself reports an incompatible-CLI condition. |
| CDISC and Define-XML | ADaMIG 1.3, SDTMIG 3.4, Define-XML 2.1, local stylesheets, schema checks, CORE rules, and spec-to-data/Define controls are present. | Alignment and conformance evidence are not equivalent to regulator acceptance. |
| eCTD | A deterministic Module 5-style package and structurally validated example backbone are produced. | No ESG or regulatory gateway submission was executed; application identifiers are simulation values. |
| Simulation methods evaluation | A governed data-free protocol, explicit scenario seeds, high-replication operating characteristics, MCSE/Wilson intervals, analytic null checks, and generated MAP/report are present. | Public aggregate calibration and stress assumptions are not authoritative joint IPD, external validation, a sponsor-approved MCID/design, MIDD qualification, or regulator acceptance. Model influence remains restricted to low, informative engineering use. |
| CRF | The public source blank CRF is retained and classified as study-report body. | It is not an annotated CRF and is never tagged or renamed as `acrf.pdf`. |

## What is required for regulated reuse

### Independent QC

1. Assign a qualified reviewer who is organizationally independent of the production programmer and has no authorship conflict.
2. Approve a risk-based QC plan before review, including critical endpoints, populations, censoring, imputation, safety derivations, and output shells.
3. Reperform critical derivations or review source-to-output traceability using controlled access to the authorized source data.
4. Record findings, responses, retests, residual-risk acceptance, and final approval under attributable identities.
5. Retain the signed QC plan, evidence, issue history, approval, and training records in the sponsor's qualified repository.

### 21 CFR Part 11 execution

1. Define intended use and maintain an inventory and data-flow map for every electronic system in scope.
2. Perform documented risk assessment and supplier assessment, then approve validation plans and acceptance criteria.
3. Execute installation, operational, performance, and user-acceptance testing proportionate to risk; retain deviations and a validation summary report.
4. Qualify access control, identity lifecycle, audit trails, electronic signatures, record linking, time synchronization, backup, recovery, retention, and change control.
5. Operate approved SOPs for use, incident handling, periodic review, training, and decommissioning.

### Licensed Pinnacle 21 validation

1. Run the final locked SDTM, ADaM, and Define-XML package in the sponsor's licensed and qualified Pinnacle 21 Enterprise environment.
2. Record software release, engine, agency configuration, controlled terminology versions, input hashes, run identity, and output hashes.
3. Triage every message against the applicable FDA rule and source context; correct or document each disposition in the cSDRG/ADRG.
4. Obtain independent standards/QC review of the issue dispositions and retain the approved report in the qualified document system.
5. Rerun after every material data, metadata, program, or rule-pack change and bind the final report to the submitted package hash.

### Model/simulation qualification for decision use

1. Define the intended decision, clinical context of use, model influence,
   consequence of error, and risk under ICH M15 with accountable sponsor owners.
2. Replace illustrative aggregate/stress inputs with qualified evidence and assess
   parameter, model-form, intercurrent-event, and joint-distribution uncertainty.
3. Preapprove the estimand-aligned MAP, clinically meaningful effect, design
   acceptance criteria, and complete operating-characteristic scenario grid.
4. Independently verify the simulation and analysis implementations and validate
   applicability against external or otherwise independent evidence proportionate to risk.
5. Obtain qualified statistical/medical review and regulator alignment before any
   pivotal-design, MIDD, labeling, filing, or patient-level decision use.

## Governing references

- [FDA Study Data Technical Conformance Guide, June 2026](https://www.fda.gov/media/153632/download)
- [FDA Electronic Systems, Electronic Records, and Electronic Signatures in Clinical Investigations, October 2024](https://www.fda.gov/media/166215/download)
- [21 CFR Part 11](https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11)
- [ICH E6(R3), Step 4](https://database.ich.org/sites/default/files/ICH_E6%28R3%29_Step4_FinalGuideline_2025_0106.pdf)
- [ICH M15, Step 4 final guideline](https://database.ich.org/sites/default/files/ICH_M15_Step4_Final_Guideline_2026_0129.pdf)
- [Pinnacle 21 Community and Enterprise comparison](https://help.pinnacle21.certara.net/en/articles/10517281-p21-community-vs-p21-enterprise)
