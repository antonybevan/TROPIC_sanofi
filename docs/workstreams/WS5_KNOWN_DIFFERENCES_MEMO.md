# WS-5 Known Differences & Residual Risk Memo

**Workstream:** WS-5 QC / Validation (G06)  
**Audience:** Reviewer, hiring manager, audit challenge  
**Product claim:** Path A — controlled non-submission demo (`docs/PRODUCT_CLAIM.md`)  
**Source of truth for IDs:** `06_qc_evidence/audit/findings_register.csv` · `06_qc_evidence/audit/FINDINGS_DISPOSITION_BOARD.md`  
**As of:** 2026-07-09  
**Machine QC grade at seal:** validation_strategy PASS · recon PASS (non-sim) · admiral PASS · log cleanliness PASS · RC PASS  

---

## 1. Purpose

Machine gates can be green while **residual risks** remain. This memo is the human QC product:

- What we still know is imperfect, limited, or out of scope  
- Why that does **not** invalidate the Path A seal  
- What would be required to close each item for a harder product claim  

**Rule:** ACCEPTED ≠ ignored. ACCEPTED = on-record residual owned by a workstream.

---

## 2. How to read QC on this package

| What green means | What green does **not** mean |
|---|---|
| Dual-lang recon under real SAS for MP ADaM | Organizational two-programmer GxP |
| Admiral zero-diff on scoped ADSL/OS/PFS core | Full ADaM re-derived in admiral |
| Controlled TFL catalog complete | Full SAP Appendix D TFL set |
| Findings dispositioned | Scientific CbzP confirmation |
| Release-candidate PASS (Path A) | FDA submission readiness |

---

## 3. Residual risk register (Critical / Major ACCEPTED)

### 3.1 Scientific / data provenance

#### F-003 — Synthetic / reconstructed CbzP (Critical) · **ACCEPTED**  
**Class:** `non_submission_demo_limit` · **Owner:** WS-0 + WS-4 + WS-6  

| | |
|---|---|
| **Difference** | Comparative TFLs include Cabazitaxel-like arm that is **not** patient-level trial IPD. OS/PFS use Guyot reconstruction from published KM; secondary TTE may be PH-scaled; non-TTE domains use fixed-seed sampling from published marginals. |
| **Where visible** | ADRG §7 · README data provenance · TFL banners · TRACEABILITY_MATRIX · PRODUCT_CLAIM §5 |
| **Impact if ignored** | False clinical claim; career-ending misrepresentation |
| **Why Path A still holds** | MP ADaM recon is real; CbzP is explicitly non-confirmatory demonstration |
| **Close condition (Path B/C)** | Authoritative CbzP IPD + re-derive + independent QC |

#### F-012 — N=749 vs protocol ITT 755 (Major) · **ACCEPTED**  
**Class:** `non_submission_demo_limit` · **Owner:** WS-2 + WS-4 + WS-6  

| | |
|---|---|
| **Difference** | Figures may show combined N=749 (371 real MP + 378 synthetic CbzP). Protocol/publication ITT is 755. |
| **Impact if ignored** | Mislabeling package cohort as original trial ITT |
| **Why Path A holds** | Disclosed; package never claims full protocol ITT reproduction |
| **Close condition** | Full two-arm source + disposition reconciliation |

---

### 3.2 Package / regulatory structure

#### F-005 — EXAMPLE eCTD metadata / incomplete aCRF package (Critical) · **ACCEPTED**  
**Class:** `external_dependency` + `non_submission_demo_limit` · **Owner:** WS-7 + WS-6  

| | |
|---|---|
| **Difference** | `us-regional.xml` uses EXAMPLE/000000 (not a real FDA application). **Source CRF PDF exists** and is packaged as `blankcrf.pdf`, but Path A does **not** claim a complete annotated CRF (aCRF) with page-level define origins for every variable. |
| **Impact if ignored** | “We built a real FDA sequence / full aCRF package” overclaim — or the opposite error of saying “we have no CRF” |
| **Why Path A holds** | Structure + source CRF copy demonstrated; filing identity and full aCRF annotation not claimed |
| **Close condition** | Assigned application IDs + true aCRF + origin links |
| **Related** | CRF **domain grounding** for programming honesty is D-012 (`WS1_CRF_GROUNDING_D012_2026-07-09.md`) — separate from aCRF package completeness |

#### F-025 — Part 11 controls (Major) · **ACCEPTED**  
**Class:** `non_submission_demo_limit` · **Owner:** WS-0 + WS-7  

| | |
|---|---|
| **Difference** | Git + hash seals ≠ validated system, access control, e-signature, audit trail as 21 CFR 11. |
| **Impact if ignored** | Illegal / unethical Part 11 assertion |
| **Why Path A holds** | Explicit non-Part-11; release manifest documents “not electronic signature” |
| **Close condition** | Organizational CSV / validated platform program |

---

### 3.3 Analysis / population / outputs

#### F-011 — PSA response population shell (Major) · **RESOLVED 2026-08-03**
**Class:** `resolve_now` (closed for the current Path A response output) · **Owner:** WS-2 + WS-4

| | |
|---|---|
| **Difference** | The controlled TFL joins `PSARESP` to ADSL baseline PSA, excludes the ADSL controlled fallback (`PSABLIF='Y'`), and applies a duplicate-subject guard. Synthetic rows without the flag are treated as observed for the demonstration arm. |
| **Impact if ignored** | Population mismatch under SAP challenge |
| **Why Path A holds** | The same eligible set drives the hierarchy gate, response TFL, SAS companion evidence, and regression contract; current counts are CbzP 145/361 and MP 61/329 (690 unique eligible subjects). |
| **Close evidence** | `05_outputs/tfl/tfl_generation.R`, `tests/test_tfl_population_contract.R`, `06_qc_evidence/audit/section_reviews/SECTION_02_POPULATIONS_ENDPOINTS_AUDIT_2026-08-03.md` plus its Section 3 correction addendum, and the post-correction rerun evidence. |

#### F-014 — ARM completeness (Major) · **ACCEPTED**  
**Class:** `scope_out_with_disclosure` · **Owner:** WS-3  

| | |
|---|---|
| **Difference** | ARM covers controlled statistical TFL core (order of 8 displays / 10 analyses), not every deferred SAP analysis or full ADSL covariate declarations everywhere. |
| **Impact if ignored** | Metadata completeness overclaim |
| **Why Path A holds** | Bound to controlled TFL catalog |
| **Close condition** | Expand ARM with every promoted output |

#### F-042 — PFS pain component/supporting disease evidence (Major) · **ACCEPTED FOR PATH A**
**Class:** `scope_out_with_disclosure` · **Owner:** WS-2 + WS-4 + medical/statistical reviewer

| | |
|---|---|
| **Difference** | SAP v4.0 requires pain progression in PFS to have supporting disease evidence and to account for palliative radiotherapy. The current staging layer does not ingest PR, and no approved source-precedence or qualification rule exists. The corrected ADTTE labels 37 pain-led PFS candidate events rather than hiding them in a generic disease-progression label. |
| **Impact if ignored** | PFS event composition could be challenged as over-inclusive or insufficiently traceable. Numerical SAS/R/admiral parity would not prove the clinical rule. |
| **Why Path A holds** | The residual is explicit in the Section 3 audit, findings register, board, and reviewer-facing guide posture; no filing or SAP-complete claim is made. |
| **Close condition** | Sponsor/statistician decision on supporting-disease qualification, PR staging/source precedence, and a palliative-RT-only sensitivity analysis, followed by rerun and independent QC. |

---

### 3.4 Conformance / standards tooling

#### F-015 — CORE residual / domain breadth (Major) · **ACCEPTED**  
**Disposition matrix:** [`docs/workstreams/WS1_CORE_RESIDUAL_MATRIX.csv`](WS1_CORE_RESIDUAL_MATRIX.csv) (filed 2026-07-09; rule/domain/disposition)  
**Class:** `external_dependency` + `scope_out_with_disclosure` · **Owner:** WS-1 + WS-3 + WS-5  

| | |
|---|---|
| **Difference** | Documented CORE SDTMIG 3.4 run exists; not every residual occurrence is closed as a full commercial conformance program. |
| **Impact if ignored** | “Zero CORE findings” overclaim |
| **Why Path A holds** | Run record + SDRG §5.1 + residual matrix; no zero-finding claim |
| **Close condition (harder claim)** | Commercial validator program + residual closure beyond Path A accept/waive classes; matrix already filed for Path A honesty |

#### F-016 — Commercial P21 ADaM (Major) · **ACCEPTED**  
**Class:** `external_dependency` · **Owner:** WS-3 + WS-5  

| | |
|---|---|
| **Difference** | No commercial Pinnacle 21 ADaM pack run in-repo. Substitutes: local CORE ADaM rules, spec→define, spec→data, dual-lang. |
| **Impact if ignored** | False “P21 clean” claim |
| **Why Path A holds** | Explicitly not claimed |
| **Close condition** | Tool access + full report + disposition |

#### F-017 — Partial ISO dates / week-offset AE timing (Major) · **ACCEPTED**  
**Class:** `scope_out_with_disclosure` · **Owner:** WS-1  

| | |
|---|---|
| **Difference** | **CRF collected calendar dates** (day/month/year on AE and lab forms). Public PDS extract reduces AE timing to **week offsets** (`AESTWK`/`AEENWK`) and shows partial ISO on some other domains — Class B extract reduction (D-012), not “trial never collected dates.” Reconstruction ±3.5 days for week-based AE timing. |
| **Impact if ignored** | Treated as programming bug rather than source limitation |
| **Why Path A holds** | SDRG documents source precision; analysis does not invent day precision |
| **Close condition** | Only with better source dates (usually impossible on PDS) or formal imputation SAP |

---

### 3.5 Documentation / exploratory layers

#### F-019 — Document / approval gaps (Major) · **ACCEPTED**  
**Class:** partial resolve + `non_submission_demo_limit` · **Owner:** WS-6 + WS-0  

| | |
|---|---|
| **Difference** | Reconstruction language reconciled (Guyot/PH); OCCDS = v1.0 + custom extension (no OCCDS v1.1). SAP signature blocks blank by design under Path A. |
| **Impact if ignored** | Fake sponsor approval |
| **Why Path A holds** | Unsigned remediation SAP disclosed in lock memo |
| **Close condition** | Real sponsor document control |

#### F-020 — Dataset-JSON lifecycle (Major) · **ACCEPTED**  
**Class:** partial hardening + exploratory · **Owner:** WS-3  

| | |
|---|---|
| **Difference** | Dataset-JSON hardened (keys/MDV/empty fail-closed) but **not** an eCTD consumer; exploratory exchange layer. |
| **Close condition** | Defined delivery route + full row recon program |

#### F-021 — USDM reproducibility (Major) · **ACCEPTED**  
**Class:** partial fix (deterministic IDs + CT version) + exploratory · **Owner:** WS-3  

| | |
|---|---|
| **Difference** | USDM now deterministic; still not packaged as submission study definition deliverable. |
| **Close condition** | Official schema gate + packaging decision |

#### F-022 — ARS completeness (Major) · **ACCEPTED**  
**Class:** `scope_out_with_disclosure` · **Owner:** WS-3 + WS-4  

| | |
|---|---|
| **Difference** | ARS covers controlled survival/core displays, not full deferred SAP catalog. |
| **Close condition** | Expand ARS with each promoted TFL |

---

## 4. Closed items that matter for confidence (RESOLVED)

These are **not** residuals; cite them when challenged on quality culture:

| ID | Topic | Why it matters |
|---|---|---|
| F-001 | eCTD index/payload parity | Package integrity |
| F-002 | SDTM 3.4 uplift drift | Package source control |
| F-004 | False listing removed | Data integrity culture |
| F-006 | Lab shift arithmetic | Safety TFL correctness |
| F-007 | Dual-lang ADEX AVALC | Recon honesty |
| F-008 | Spec-driven labels/order | Metadata↔data |
| F-009 | Release-run hash seal | Provenance (not Part 11) |
| F-010 | TFL catalog control | Output universe governance |
| F-013 | Variable lineage | Traceability |
| F-018 | Log cleanliness gate | Execution hygiene |
| F-023 | Traceability matrix fix | Doc integrity |
| F-040 | TTUMOR censor pool | Death milestones excluded from tumor censor dates |
| F-041 | PFS censoring hierarchy | Last-evaluable/no-post-baseline branches now match SAP |

---

## 5. Independence limitation (always state)

All production, validation, and admiral tracks were implemented under a **single programmer of record**.  

- **Present:** multi-engine methodological challenge (SAS / R / admiral), automated gates, disposition discipline.  
- **Absent:** second human organization, independent QC unit, sponsor medical review.  

This is structural to a portfolio demo—not a temporary bug.

---

## 6. Log cleanliness residual (operational)

Log cleanliness **PASS** means: configured **persisted** logs are clean under `config/log_cleanliness.yaml`, with reviewed ADTTE time-origin exceptions capped.  

It does **not** mean every rscript/python stdout line from all 30 stages is archived and scanned. Coverage is explicit: `configured_persisted_logs_only`.

---

## 7. QC sign-off statement (Path A)

Under `docs/PRODUCT_CLAIM.md` Path A and the residual register above:

1. Critical scientific comparators are disclosed as non-confirmatory.  
2. Package structural placeholders are disclosed.  
3. Validation engines appropriate to risk were run under real SAS for the sealed proof.  
4. Residuals are named, owned, and close-conditioned.  
5. No Part 11 or filing claim is made.

**Therefore:** Path A release-candidate PASS is **compatible** with this residual stack.  
**Path B/C is not** until the close conditions in §3 are met.

---

## 8. Workstream actions derived from this memo

| Residual cluster | Next pack owner |
|---|---|
| F-003, F-012 | WS-6 language consistency every guide revision |
| F-005, F-025 | WS-7 package + PRODUCT_CLAIM enforcement |
| F-015, F-016, F-017 | WS-1/WS-3 external validation evidence index |
| F-011, F-014, F-022, F-042 | WS-2/WS-4 and medical/statistical review before any filing-facing expansion |
| F-020, F-021 | WS-3 exploratory inventory in standards pack |

---

## 9. Document control

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-07-09 | Initial residual memo for Path A / v0.1.0-demo-rc.1 train |
| 1.1 | 2026-08-03 | Section 3 corrections, F-011 observed-baseline update, and F-042 pain/RT residual |
