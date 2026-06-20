# TROPIC — Independent Reviewer Audit (FDA-reviewer perspective, 2026-06-20)

**Reviewer stance.** This audit reads the submission the way an FDA reviewer would on
receipt: read the reviewer's guides (ADRG/SDRG/BDRG) and traceability matrix first,
then *independently verify* the data and metadata rather than accept the package's own
`FDA_AUDIT_2026-06-18.md` "12/12 PASS." Findings are graded with FDA review constructs:
**FILE-RISK** (Refuse-to-File / non-reviewable if this were a real marketing
application), **TRC** (Technical Rejection Criteria — gateway auto-reject),
**MAJOR** (would generate an Information Request), **MINOR** (review comment).

**One-line conclusion.** As a *methodological demonstration* this is exemplary and
unusually honest engineering. As a *fileable efficacy submission* it is **not
reviewable**, for two independent reasons that no amount of conformance tooling can
remedy: the comparator arm is **synthetic** and the tabulation data is on an
**unsupported SDTMIG version built from week-precision dates**. Most issues below are
disclosed in the reviewer's guides; the reviewer's job is to confirm they hold and
judge materiality — which I did.

---

## What I independently verified (not taken on trust)

| Claim in the package | Verification | Result |
|---|---|---|
| SAS↔R reconciliation is a real ODA run, not a `sim` byte-copy | read `pipeline_health.json` | `sas_execution_mode=oda`, `probe_nonce_echoed=true`, 8/8 domains PASS — **genuine**, not tautological |
| ADaM define declares the datasets that exist | `IG.*` in `define.xml` vs `04_adam/*_prod.xpt` | 7 ADaM match; `clinsite` correctly BIMO-only (BDRG), not in ADaM define |
| ALBBL/LDHBL are flagged placeholders | `def:Origin` in define | `Type="Assigned" Source="Sponsor"` — metadata-honest; data still 100% null |
| Two-arm efficacy depends on the synthetic arm | `T-11-Efficacy_Tables.txt` | `CbzP (N=378)` vs `MP (N=371)`, HR 0.85 — synthetic arm carries half of every comparison; table self-labels "SYNTHETIC" |
| AE dates carry week precision | ADAE `ASTDT` vs source | reconstructed `RFSTDTC + (wk−1)×7` per SDRG §2 — confirmed |
| Standards versions | define headers | SDTMIG **3.1.1**; ADaMIG 1.3; Define-XML 2.1; CT **2024-03-29** (both) |

---

## FILE-RISK (non-reviewable as a marketing application)

**R-1 — The comparator arm is synthetic.** The reconciled ADaM contains the real
Mitoxantrone arm only (N=371); the Cabazitaxel arm (N=378) is reconstructed from the
published Kaplan–Meier curves (Guyot IPD for OS/PFS; PH-scaling for secondary
endpoints, which the ADRG itself labels "circular… no evidentiary weight"). Every
two-arm HR, p-value, and the entire Project Optimus exposure-response rests partly on
simulated patients. **An efficacy/safety comparison cannot be reviewed off
reconstructed data.** This is fine for the stated demonstration purpose and is
disclosed on the face of the tables — but in a real application it is an automatic
Refuse-to-File for the comparison.

**R-2 — Single treatment arm with no source-derived populations.** `ITTFL`, `SAFFL`,
`PPROTFL` are all `Y` for all 371 subjects (carried from the de-identified PDS source,
not re-derived); there is **no SDTM `DV` domain**, so no per-protocol *exclusion* is
ever exercised. Population-based subsetting (including BIMO `N_ITT/N_PPROT`) is a
structurally-correct placeholder, not a demonstrated filter. Verified all-`Y` and
disclosed (ADRG §5.4).

---

## TRC / gateway (would be auto-rejected before review)

**T-1 — SDTMIG v3.1.1 is below the FDA-supported version floor.** Declared in
`define_sdtm.xml`, `SDRG`, and `S_sdtm_mapping.sas`. FDA validates tabulation data
against the supported versions in the Data Standards Catalog; 3.1.1 (2005) is outside
that window and below CORE's lowest rule pack (3.2) — the package's own CORE SDTM run
could only execute 3.2 rules and surfaced 15 issue-rules / 47 rows (EPOCH required,
`AEBODSYS`=`AESOC`, AGE/AGEU). Remap to ≥3.3/3.4 or obtain an explicit, pre-agreed
legacy-data exception. *(Engineering plan in `SUBMISSION_STANDARDS_REMEDIATION.md` #1.)*

**T-2 — Controlled Terminology ~15 months stale (2024-03-29).** Refresh SDTM/ADaM CT
to the current package at lock; stale CT triggers "newer CT available" and possible
new-term findings at the gateway.

---

## MAJOR (Information Requests)

**M-1 — Time-to-event endpoints inherit ±3.5-day date precision. — ADDRESSED
(2026-06-20).** AE/disposition timing is week-offset and reconstructed to calendar
dates (`RFSTDTC + (wk−1)×7`). A date-precision sensitivity analysis was performed
(`06_telemetry/date_precision_sensitivity.py`, 2,000 MC replicates, ±3.5-day jitter on
every analysis time): **all real-arm KM medians are robust** — 95% perturbation band
≤0.11 months and max shift ≤4.4 days for OS/PFS/TTUMOR/TTPSA; TTSAE/TTPAIN medians
not reached (robust by construction). The MP-arm OS median (12.68 mo) matches the
published control-arm value (~12.7 mo), validating the computation. See
`DATE_PRECISION_SENSITIVITY_2026-06-20.md`. *Residual:* two-arm HR sensitivity still
cannot be assessed (synthetic comparator, R-1).

**M-2 — No completed authoritative conformance run.** Pinnacle 21 Community is
engine-expired (never executed); CORE ships **zero** executable ADaM rules, so ADaM
rests on the project's own custom CORE rules + interim `adam_conf_check.R`; the CORE
SDTM run is explicitly "not a clean pass." There is no regulator-grade validation
report for either standard. **IR: supply a current P21/Certara (or CORE-when-available)
report with an explanation of every remaining finding in the guides.**

**M-3 — Validation lacks producer/validator independence.** The SAS production and R
validation tracks are both authored by one programmer (disclosed, ADRG §6). The
cross-language reconciliation is real and passing, but it is *implementation*
reconciliation, **not** GxP double programming. For a submission, the independent
validator must be a different person/organization.

**M-4 — Key prognostic baselines are non-informative constants.** Baseline **LDH** and
**albumin** — both Halabi-nomogram prognostic factors in mCRPC — are single constants
for all subjects (`def:Origin=Assigned`; data 100% null pre-assignment). The guides
correctly state they are not used as model covariates (stratification is ECOG +
measurable disease only), but their presence as "values" in ADSL is a transparency
hazard; any prognostic adjustment a reviewer might request cannot be performed.

**M-5 — Endpoint definitions mix eras and one is non-functional.** Response uses RECIST
**v1.0** (trial-era) while PSA/bone progression use **PCWG3** (2016, post-trial,
labeled a demonstration). The PCWG3 bone-progression 2+2 rule yields **5 unconfirmed /
0 confirmed** events on the real arm — i.e. the endpoint contributes nothing on this
data. Acceptable as a labeled demonstration; not acceptable as a primary analysis.

---

## MINOR (review comments)

- **m-1 — Non-standard DM variables.** `AGEGRP` and `ARM2` sit directly in SDTM `DM`
  (`define_sdtm.xml`); these belong in `SUPPDM`. Expect an SD-rule finding.
- **m-2 — Trial Summary (TS) is thin.** 16 `TSPARMCD` present; FDA-expected parameters
  such as `SSTDTC`, `NARMS`, `ACTSUB`, `AGEMIN/AGEMAX`, `STOPRULE` appear absent.
- **m-3 — Geography is placeholder.** `COUNTRY='IND'`, `REGION='REST OF WORLD'` for all
  subjects (no source); geographic subgroups not reportable. Disclosed (SDRG §4.3).
- **m-4 — eCTD packaging.** Backbone/STF were absent; now scaffolded in `11_ectd/0000/`
  (well-formed, MD5-accurate) but still need official DTDs, content materialization,
  and real application metadata before a gateway submission.
- **m-5 — BIMO `clinsite` outside the define.** Acceptable per FDA BIMO TCG (documented
  via BDRG), but a minimal BIMO define would aid the reviewer.

---

## Strengths a fair reviewer would record

- The real ODA SAS run is **verifiable and verified** (mode/nonce in
  `pipeline_health.json`); 8-domain dataset reconciliation **and** results-level KM
  reconciliation (PROC LIFETEST vs survfit) both PASS on the real arm.
- `define.xml` is XSD-valid, parses in the CORE reference engine, and carries ARM v1.0
  (8 ResultDisplays / 10 AnalysisResults) with result→method→dataset traceability.
- Bidirectional spec governance (`spec→define` and `spec→data` gates) is genuine and
  non-circular.
- The reviewer's guides are exceptionally candid — nearly every finding above is
  pre-disclosed. **Independent verification confirmed the disclosures are accurate**,
  which materially raises reviewer confidence in the package's integrity.

---

## Disposition

| If the intent is… | Verdict |
|---|---|
| A methodological / Project-Optimus demonstration (its stated purpose) | **Strong, submission-grade engineering**; address MINORs at leisure |
| A real marketing application (NDA/BLA) | **Not fileable** — R-1/R-2 (synthetic arm, single real arm) are dispositive; T-1/T-2 gate at the door; M-1…M-3 are pre-review IRs |

Top three to move the needle, in order: **(1)** real two-arm patient data (removes
R-1/R-2), **(2)** SDTM remap to a supported IG + CT refresh (clears T-1/T-2), **(3)** a
completed independent validation with an authoritative conformance report (clears
M-2/M-3). Items M-1, M-4, M-5 and the MINORs are then ordinary review correspondence.

*Verification artifacts: `pipeline_health.json`, `reconciliation_status.json`,
`results_reconciliation_status.json`, `07_define_xml/define{,_sdtm}.xml`,
`04_adam/*_prod.xpt`, `09_tfl/.../T-11-Efficacy_Tables.txt`. Reviewer inputs:
`08_reviewers_guides/{ADRG,SDRG,BDRG,TRACEABILITY_MATRIX}.md`.*

---

## Remediation status (2026-06-20)

**Terminal session executed (2026-06-20) — engineering-addressable items now DONE:**

| Item | Resolution | Proof |
|---|---|---|
| **T-1** SDTMIG 3.1.1 → **3.4** | Derived 3.4 uplift (`06_telemetry/uplift_sdtm_34.R`): AGE from de-id AGEGRP, ACTARM/ACTARMCD, AESOC, EPOCH (VISIT-based), EXENDY, week-vars→SUPPAE/SUPPDS, TA; define regenerated (`uplift_define_34.py`). Source stays pristine. | XSD-VALID; 315 ref checks PASS |
| **T-2** CT → **2026-03-27** | Both defines bumped from 2024-03-29 (latest cached package). | both defines |
| **m-1** `AGEGRP`→SUPPDM, `ARM2` removed | `AGEGRP` non-standard var moved; `ARM2`/`ARMA`/`ARMCD2` phantoms dropped from `IG.DM`. | CORE-000550 cleared |
| **m-2** TS enrichment | `NARMS=2`, `ACTSUB=371`, `SSTDTC=2007`, `AGEMIN=P18Y` (public NCT00417079 facts). | `ts.xpt` 20 params |
| **M-2** authoritative conformance (SDTM) | Real CDISC **CORE 0.16.0 @ SDTMIG 3.4** run. All targeted structural rules cleared; residual classified (inherent-de-id / real-source-data / cross-domain-no-FA / engine-internal). | `CORE_SDTM34_RUN_RECORD.md` |
| **M-1** date-precision sensitivity | 2,000-replicate MC; all KM medians robust. | `DATE_PRECISION_SENSITIVITY_2026-06-20.md` |
| **m-4** eCTD packaging | Backbone + STF + **content materialized** (89/89 leaves MD5-verified) and **all 3 XML files DTD-VALID** (ICH eCTD 3.2 / ICH STF 2.2 / FDA Regional v3.3). | `11_ectd/RUN_RECORD.md` |

**Genuinely remaining — data / organizational, not code (cannot be fabricated):**

| Item | Why it cannot be done here |
|---|---|
| **R-1 / R-2** real two-arm patient data + `DV` domain | Requires sponsor/PDS data-access; only the single MP arm is public, comparator stays reconstructed. |
| **M-3** independent (2-programmer) GxP validation | Organizational — needs a second programmer/organization (SAS vs R tracks are one author). |
| **Real FDA application metadata** in `us-regional.xml` | Assigned only on actual FDA submission; the eCTD carries clearly-labelled **EXAMPLE** identifiers. |

Honest note: the CORE residual at 3.4 is dominated by findings that are **not** programming
defects — real source-data quality (AESER/VSSTRESC, **not** overwritten), a cross-domain
RELREC rule needing an `FA` domain not in this analysis package, and variables the PDS
de-identification removed (`SITEID`/`COUNTRY`/MedDRA codes). See `CORE_SDTM34_RUN_RECORD.md`.
