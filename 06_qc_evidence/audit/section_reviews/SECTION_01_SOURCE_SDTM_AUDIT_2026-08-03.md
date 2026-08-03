# Section 1 — Source Intake, SDTM Provenance, and CORE Residual Audit

**Audit date:** 2026-08-03  
**Audit baseline:** `458060c` on `codex/submission-pipeline-rc`  
**Scope:** local source inventory → staging → SDTM validation → SDTMIG 3.4 uplift → package/Define scope  
**Product path:** Path A — controlled non-submission demonstration  
**Decision:** **PASS WITH DISCLOSED SOURCE LIMITATIONS** for the Path A handoff to ADaM. This is not filing-grade SDTM clearance.

## 1. Independent source recheck

The local source directory was read independently with `pyreadstat` and compared with the committed aggregate profile and the current ODA source-manifest binding.

| Check | Independent result | Verdict |
|---|---:|---|
| Real source files | 34 `.sas7bdat` domains | PASS |
| Total source records | 458,333 | PASS; matches `platform/source_profile_status.json` |
| DM unique subjects | 371 | PASS |
| DM treatment arm | 371/371 `MITOXANTRONE/PREDNISONE` | PASS |
| DM sex | 371/371 `M` | PASS; source/protocol boundary documented |
| Source manifest | `329430f6361e8bd0ec019a692ea856a8025b20b572a28a5d30a714ca5cf0d007` | PASS; matches `pipeline_health.json` |
| ODA provenance binding | Health records `sdtm_manifest_sha` matching local source | PASS |
| Patient-data Git policy | Source `.sas7bdat` and package `.xpt` are ignored and untracked | PASS; intentional privacy/data-rights boundary |

## 2. Staging and validation handoff

The staged RDS layer was checked for the nine analysis-scoped source domains. Row counts and subject coverage match the source validation record:

| Domain | Rows | Subjects | Result |
|---|---:|---:|---|
| DM | 371 | 371 | PASS |
| AE | 5,428 | 357 | PASS; 14 DM subjects have no AE records |
| EX | 3,485 | 371 | PASS |
| CM | 24,534 | 371 | PASS |
| LB | 80,788 | 371 | PASS |
| DS | 2,842 | 371 | PASS |
| VS | 18,388 | 371 | PASS |
| LS | 5,774 | 371 | PASS |
| PN | 26,982 | 358 | PASS; 13 subjects have no PN records |

`v_sdtm_validation.log` reports zero errors. Its warnings are source-precision warnings, not suppressed failures: CM, LB, LS and PN contain partial/dirty date values and the programs carry them forward rather than inventing precision.

## 3. Source limitations that must remain explicit

### 3.1 Exposure treatment-name anomaly (F-028)

The source contains 10 EX rows for subject `006193-530-002-603` with `EXTRT=XRP6258`, while every DM subject is `MITOXANTRONE/PREDNISONE`. The SAS and R ADSL programs explicitly derive `TRT01P`/`TRT01A` from DM arm fields and use EX only for exposure timing. This is the correct conservative treatment for Path A; EX must not be silently recoded.

### 3.2 Baseline AE skeleton (F-026)

There are 1,137 AE rows with blank `AESER`; 1,134 are `VISIT=BASELINE` and three are outside that visit. The documented residual is therefore correctly described as approximately 1,134 baseline skeleton rows, not as a missing AE domain. No AESER values are invented. Any TEAE analysis must use its ADSL/ADAE population logic.

### 3.3 Date precision (F-017)

Independent counts of non-empty source date fields that are not full `YYYY-MM-DD` (or datetime) are:

| Domain/variable | Non-full precision or dirty values |
|---|---:|
| CM/CMSTDTC | 1,891 |
| LB/LBDTC | 17 |
| LS/LSDTC | 4 |
| PN/PNDTC | 24 |
| CX/CXDTC | 4 |

The existing sensitivity record supports the separate ±3.5-day analysis-time robustness assessment for MP OS/PFS and other scoped TTE parameters. These values remain source limitations; they are not corrected in this audit.

## 4. Package scope and uplift

`define_sdtm.xml` contains 18 ItemGroupDefs: DM, AE, EX, CM, LB, DS, VS, LS, PN, SUPPDM, SUPPAE, SUPPEX, SUPPCM, SUPPLB, SUPPDS, SUPPLS, TS and TA. The local package directory contains 18 ignored XPT datasets. The package is therefore analysis-scoped; it is not a claim that all 34 source domains are delivered.

The uplift program documents that the pristine 3.1.1 source is not modified. The package layer derives SDTMIG 3.4-aligned metadata/variables, including AGE, AESOC, EPOCH, EXENDY, SUPP relocation, TA and TS enrichment. This is a derived package layer, not sponsor-provided raw SDTM.

## 5. CORE residual decision

The committed CORE v0.16.0 SDTMIG 3.4 record reports 20 distinct issues / 13,010 occurrences with **zero structural-fixable residuals**. The residual matrix classifies each remaining class as cross-domain N/A, engine-internal, inherent de-identification, real-source quality, or source precision. That is sufficient for the Path A handoff when the “not CORE clean / not commercial P21” boundary stays visible.

## 6. Section 1 verdict and handoff

| Handoff | Verdict |
|---|---|
| Source profile → G01 | PASS |
| Source → staging → R validation | PASS; zero validation errors |
| Source → ODA provenance guard | PASS; manifest SHA matches |
| Source → SDTMIG 3.4 package | PASS with uplift disclosure |
| SDTM → ADaM handoff | **GO for Path A** |
| Filing-grade SDTM/P21/aCRF claim | **NO-GO** |

The next audit is Section 2: populations, endpoints, estimands, and SAP/config/TFL control.
