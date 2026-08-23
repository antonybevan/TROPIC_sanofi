# Open Work Register — controlled non-submission simulation

**Purpose:** What a principal programmer still treats as **real work**, not “green JSON theater.”  
**As of:** 2026-08-23
**Seals:** The unreleased v0.3.0 candidate may be technically green while external or
scope-conditional items remain open only when they are explicitly dispositioned.

---

## Current endpoint decision handoff and closure (2026-08-04)

The next controlled work item is specification closure, not an unapproved ADTTE rewrite.

| ID | Pri | Owner | Work | Why it matters | Exit |
|---|---|---|---|---|---|
| **W-ENDPOINT-01** | **P0** | WS-2 / WS-4 + accountable author | **Closed for the controlled implementation.** ED-01–ED-07 are adopted and implemented: corrected pain algorithm, cancer-related evidence, CM+PR union, RT sensitivities, SAP-native `T-11-3`–`T-11-8` mappings, TTUMOR ITT population and TTE origins. | Numerical parity does not replace independent clinical review; the pre-rerun pain/TTUMOR records remain historical baseline evidence. | [`EDR-F042-T11-8-2026-08-03.md`](decisions/ENDPOINT_DECISION_RECORD_F042_T11_8_2026-08-03.md) records Antony Bevan's adoption; the complete manifest-driven genuine-SAS DAG and delayed second-pass review are the technical evidence. External statistical/medical review remains required before regulated reuse. |
| **W-ENDPOINT-02** | **P0** | WS-2 / WS-4 / WS-5 | **Conditional closure.** The statistical-governance assessment found `GOV-STAT-01` (SAS T-11-5 initial-visit-only response check), corrected it, and added an exact subject-level endpoint reconciliation gate. | The prior TFL value was correct, but its claimed independent SAS challenge was not. | Current-head real-SAS DAG, `F042_PAIN_RESPONSE=PASS`, reseal and CI; then retain external human review as the regulated-use boundary. |

The author-adopted record, executable specification and impact appendix are now implemented and reconciled. The historical backlog below remains useful evidence, but this handoff supersedes its older “next session” ordering for endpoint work.

---

## Active backlog

### SDTM layer (complete E2E audit first — 2026-07-09)

| ID | Pri | Owner | Work | Why it matters | Exit |
|---|---|---|---|---|---|
| **W-SDTM-01** | **Done** | WS-1/WS-6 | Disclose **F-028**: EXTRT=XRP6258 (1 subj, 10 rows) vs DM all MITOXANTRONE arm | Arm must not be taken from EXTRT | **DONE** — SDRG and the audit pack disclose the source anomaly; no silent re-code |
| **W-SDTM-02** | **P0** | WS-4 | ADaM: any-AE / safety dens use **ADSL N=371** (14 subj have no AE) | Wrong denominator if AE-distinct only | **DONE** — T-20 + dens audit |
| **W-SDTM-03** | P1 | WS-1/WS-6 | Package = **18** analysis-scoped domains vs **34** PDS | Avoid “full SDTM dump” claim | SDRG scope table (done in E2E pack) |
| **W-SDTM-04** | P2 | WS-5 | Optional QC list EXTRT ∉ expected set | Catch arm/exposure drift | Listing or gate |
| **W-AE-01** | P0 | WS-4 / WS-5 | Baseline AE skeleton + TEAE AESER soft QC | TEAE cleanliness | ADRG §4B + ADAE QC (done soft) |
| **W-AE-02** | P1 | WS-4 / WS-6 | Grade 5 / fatal mapping vs CRF grade 1–4 labels | Documented ADRG §4B | Done docs |
| **W-LB-01** | P1 | WS-1 / WS-6 | ALB/LDH Class C | Documented ADRG §5.1 | Done docs |
| **W-AE-03** | P2 | WS-1 / WS-5 | CORE AESER residual | No overwrite | Residual matrix |
| **W-CRF-01** | P2 | WS-6 / WS-7 | Full aCRF + real app IDs | Path B | Deferred |
| **W-PKG-01** | Done | WS-7 | Re-package guide PDFs into `m5/` | Reviewer surface must match controlled sources | **DONE** — package/guides/eCTD presentation artifacts rebuilt and visually audited; the full DAG maintains them |
| **W-PKG-02** | Done | WS-7 | Sync git-tracked **m5 programs** from factory (arm map + dens) | Review face must match the factory | **DONE** — Module 5 program copies are byte-controlled and the package refresh is part of the current DAG |
| **W-CI-01** | Done | WS-7 | Data-free CI green | Done | CI success |
| **W-CI-02** | Done | WS-7 | CI audit closure: wire data-free regression tests (ARM/abort/F-042), gitleaks, workflow hardening, conditional CT enforcement, and conformance-coverage summary | Green CI must not be read as full conformance | Done 2026-08-05 — [`WS7_CI_AUDIT_CLOSURE_2026-08-05.md`](reviews/WS7_CI_AUDIT_CLOSURE_2026-08-05.md); external `CDISC_LIBRARY_API_KEY` configuration tracked as F-047 |

**SDTM E2E audit pack:** `docs/workstreams/reviews/WS1_SDTM_E2E_AUDIT_2026-07-09.md`  
**Verdict:** **GO to ADaM** with residuals dispositioned.

### ADaM phase entry (2026-07-09)

| ID | Pri | Work | Status |
|---|---|---|---|
| **W-ADAM-00** | P0 | Arm from DM; dens ADSL SAFFL; TEAE=TRTEMFL; no EXTRT arm | **PASS** — `WS4_ADAM_PHASE_ENTRY_2026-07-09.md` |
| **W-ADAM-01** | P0 | Dual-lang rebuild ADSL/ADAE + recon after arm map change | **DONE** — the current pipeline evidence authority records genuine SAS production, cross-language audit, and scoped admiral reconciliation; release requires the complete manifest-defined DAG |
| **W-ADAM-02** | P1 | Decide whether to hard-fail the source-fidelity TEAE blank `AESER` residual | **CONDITIONAL POLICY** — soft cap 5, observed approximately 1; do not impute or promote to a hard gate without approved scope |
| **W-ADAM-03** | P1 | ADTTE/ADRS dens audit same ADSL rule | **DONE** — `WS4_ADAM_DENS_AUDIT_2026-07-09.md` |
| **W-ADAM-04** | P2 | ADEX dens SAFFL + ADSL arm docs | **DONE** — dens audit pack |
| **W-ADAM-05** | P2 | Optional: OBJRESP dens = full MEAS in ADaM (now TFL-only) | **DEFERRED** — TFL denominator is correct; ADaM expansion requires approved SAP scope |
| **W-SDTM-02** | P0 | Confirm dens ADSL N=371 | **Verified** T-20 + dens audit |

**Dens audit pack:** `docs/workstreams/reviews/WS4_ADAM_DENS_AUDIT_2026-07-09.md`  
**ORR dens fix:** `tfl_generation.R` left-joins ADSL `MEASDISF='Y'` to OBJRESP (203, not 201).

---

## Explicitly **not** next (unless claim expands)

- Expanding deferred TFL catalog  
- Inventing day-true AE dates  
- Filling blank AESER on baseline rows with guessed Y/N  
- Claiming commercial P21 clean  
- Expanding ADRS OBJRESP to full ITT in ADaM without SAP basis  

---

## Priority order for next session

1. **Governance closure / review handoff** — enforce the
   [statistical governance assessment](reviews/PATH_A_STATISTICAL_GOVERNANCE_ASSESSMENT_2026-08-04.md)
   on every release; obtain external qualified statistical/medical review before
   regulated reuse.
2. **F-047 / external services** — configure the CDISC Library CI secret only through repository governance; do not embed credentials.
3. **W-ADAM-02** — consider promoting TEAE `AESER` soft QC to a hard gate only if the validation scope is formally expanded.
4. Otherwise hold the controlled non-submission boundary with disclosed residuals; do not expand the deferred TFL catalog or claim commercial P21/CORE cleanliness.

**Meta-audit (2026-07-09):** `docs/workstreams/reviews/WS_META_AUDIT_PATH_A_2026-07-09.md`  
Source decision: `WS1_CRF_GROUNDING_D012_2026-07-09.md` · dens: `WS4_ADAM_DENS_AUDIT_2026-07-09.md`
