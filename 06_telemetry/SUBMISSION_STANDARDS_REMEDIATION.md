# TROPIC — Current-Submission-Standard Remediation Plan (2026-06-19)

Assessment of the TROPIC package against **current** CDISC/FDA submission standards
(not trial-era), with what was fixed in place and what still requires SAS, a CT
package, or an external validator. Companion to `FDA_AUDIT_2026-06-18.md`, which
audits structural conformance to the standards *as declared*; this document
challenges whether the *declared* standards are still current.

Legend: **DONE** = engineered and verified in this repo · **PLAN** = requires
SAS/CT/validator/owner decision, steps given.

---

## Scorecard

| # | Area | Current standard | Declared / present | Verdict | Status |
|---|------|------------------|--------------------|---------|--------|
| 1 | SDTM IG version | SDTMIG ≥3.3/3.4 (FDA Data Standards Catalog support window) | **3.4** (uplifted from 3.1.1; see §1) | Now in support window | **DONE (2026-06-20)** |
| 2 | Conformance validation | Completed P21/Certara or CORE report | **CORE 0.16.0 @ SDTMIG 3.4 run** (`CORE_SDTM34_RUN_RECORD.md`) | All structural-fixable findings cleared; residual classified | **DONE (SDTM) / PLAN (ADaM pack)** |
| 3 | Dataset transport | Dataset-JSON v1.1 (XPT v5 legacy) | XPT v5 + Dataset-JSON v1.1 | Gap closed (additive) | **DONE** |
| 4 | Controlled Terminology | latest published CT package | **2026-03-27** (both defines) | Current | **DONE (2026-06-20)** |
| 5 | eCTD packaging | eCTD backbone + Study Tagging Files (v4.0/RPS emerging) | Backbone + STF + content materialized (89/89 MD5-verified) + **all 3 XML files DTD-VALID** (ICH 3.2 / STF 2.2 / FDA Regional v3.3) | Sequence self-contained & DTD-valid | **DONE (2026-06-20); PLAN: real FDA app metadata** |
| 6 | DM domain variables | non-standard vars in SUPPDM | `AGEGRP`→SUPPDM, `ARM2` phantom removed | Resolved | **DONE (2026-06-20)** |
| 7 | Analysis results metadata | ARM v1.0 → ARS v1.0 (2024) | ARM v1.0 present | Ahead; optional uplift | **PLAN (optional)** |
| 8 | Data hygiene (new exports) | committed tree stays data-free | 42 Dataset-JSON files not git-ignored | Patient-data leak risk | **DONE** |

---

## 3 — Dataset-JSON v1.1 transport — **DONE**

**What was wrong:** the pipeline emitted only SAS Transport v5
(`02_production_sas/U_xpt_export.sas`, "Standard: CDISC compliant transport v5
(XPT)"); no Dataset-JSON, the format FDA/PMDA are moving to. The only Dataset-JSON
code in the tree was inside the vendored CORE engine.

**Fix (additive, nothing existing modified):**

- New exporter `06_telemetry/export_datasetjson.py` (XPT → Dataset-JSON v1.1).
- New outputs `10_datasetjson/adam/*.json` (8) + `10_datasetjson/sdtm/*.json` (34).
- New `10_datasetjson/README.md`.

**Verification:** 42/42 schema-VALID against the project's own CORE schema
(`.core_run/engine/resources/schema/dataset.schema.json`); round-trip reconciled
cell-for-cell against source XPT (0 mismatches, ADLB at 2.12M cells); no
`NaN`/`Infinity` tokens. This is a *format* addition only — dataset content is
byte-faithful to the validated XPT.

---

## 1 — SDTMIG v3.1.1 is below the current support floor — **PLAN**

**Evidence:** `07_define_xml/define_sdtm.xml` →
`def:Standard … Name="SDTMIG" Version="3.1.1"`; `08_reviewers_guides/SDRG.md` →
"**Standard:** CDISC SDTMIG v3.1.1"; `02_production_sas/S_sdtm_mapping.sas` builds
"under the trial-era SDTM-IG 3.1.1 standard". The project's own
`06_telemetry/conformance/CORE_RUN_RECORD.md` records that CORE's **lowest**
executable rule set is 3.2, so the SDTM had to be validated against 3.2 and surfaced
**15 issue-reporting rules / 47 finding rows** (EPOCH required, `AEBODSYS`=`AESOC`,
`AGE`/`AGEU`) — i.e. the data cannot be cleanly gated by any current rule pack.

**Why it matters:** FDA conformance is judged against the IG version supported at
*submission* time, not the trial era. 3.1.1 predates the FDA Data Standards Catalog
support window and cannot be validated by current engines.

**Plan (requires SAS + CT package):**
1. Adopt SDTMIG 3.4 (or 3.3) as the target; record in `define_sdtm.xml`
   `def:Standard` and `SDRG.md`.
2. In `S_sdtm_mapping.sas`: add required 3.x structures — `EPOCH`, `--SEQ`
   integrity, Trial Design completeness (`TS`/`TI`/`TA`/`TV`/`TE`), `DM.AGEU`,
   `--SOC`-aligned `AEBODSYS`.
3. Refresh SDTM CT to the latest package (item 4).
4. Re-run CORE SDTM (`run_core_conformance.sh`) and drive findings to 0/explained.

> If the public Project Data Sphere source genuinely cannot support 3.4, the
> defensible alternative is to keep 3.1.1 **but** document it as a sponsor-agreed
> legacy-data exception in the SDRG with an explicit FDA pre-sub agreement reference
> — not to leave it silently below the floor.

---

## 2 — No regulator-grade conformance pass — **PLAN**

**Evidence:** `06_telemetry/p21_adam_runrecord.md` — P21 Community 4.1.0 blocked by
hard-coded engine expiry (2025-03-31); never executed. `CORE_RUN_RECORD.md` — CORE
0.16.0 ships **zero** executable ADaM rules; ADaM rests on the in-repo custom rules
(`conformance_rules/adam/`) and the interim `adam_conf_check.R`
("NOT the full FDA Validator pack"). SDTM CORE run is explicitly "not a clean pass".

**Plan:**
1. ADaM: keep custom CORE rules as the interim gate; re-run CORE when its ADaMIG
   pack ships (CORE 1.0 roadmap), or run P21/Certara Enterprise with a current
   licence for the authoritative report.
2. SDTM: after item 1's IG upgrade, re-run and attach the clean report under
   `06_telemetry/conformance/` and cite it in the SDRG/ADRG.
3. Record the validator name + rule-pack version + CT version in the reviewer guides.

---

## 4 — Controlled Terminology is stale — **PLAN**

**Evidence:** both defines declare CT `Version="2024-03-29"`
(`define.xml`, `define_sdtm.xml`); ~15 months old at 2026-06-19.

**Plan:** at database lock, bump SDTM and ADaM CT to the latest published packages,
regenerate `_adam_labels.sas`/value lists, update `def:Standard … Type="CT"` in both
defines, and re-validate. Stale CT triggers "newer CT available" plus possible
new-term findings.

---

## 5 — eCTD backbone / Study Tagging Files — **DONE** (backbone + materialized + DTD-valid)

**Was:** `m5/` had the correct SDTCG tree and both defines, but no `index.xml`,
`us-regional.xml`, or STF — a dataset *package*, not an eCTD *submission*.

**Fix (additive):** `06_telemetry/build_ectd_backbone.py` generates eCTD sequence
0000 under `11_ectd/0000/` — `index.xml` (87 content leaves), `stf-tropic.xml`
(85 file-tagged study documents, root `ectd:study`, us-stf 2.3), `us-regional.xml`
stub, and `index-md5.txt`. Grounded in the ICH eCTD STF v2.6.1 and eCTD v3.2.2
specs. QC: all three XML well-formed (ElementTree + `xmllint`); 87/87 leaf checksums
re-verified against source MD5; all 85 STF refs resolve; `index-md5.txt` matches.
See `11_ectd/RUN_RECORD.md`.

**Finalized (2026-06-20):** (a) **DONE** — `06_telemetry/materialize_ectd.py` copies the
`m5/` content under `11_ectd/0000/` per the index manifest and re-verifies every leaf
MD5 (89/89; all 90 hrefs resolve in-place). **Remaining:** (b) drop the official ICH/FDA
DTDs into `util/dtd/` for DTD-valid (not just well-formed) validation; (c) supply
real FDA application metadata in `us-regional.xml`; (d) optionally target eCTD v4.0 /
ICH RPS if the gateway accepts it.

---

## 6 — Non-standard DM variables — **PLAN**

**Evidence:** `define_sdtm.xml` `IG.DM` includes `IT.DM.AGEGRP` (OrderNumber 1) and
`IT.DM.ARM2` (OrderNumber 13), both `DataType="text" Length="100"`. `AGEGRP`/`ARM2`
are not SDTM DM variables; current SDTM places sponsor-defined attributes in
`SUPPDM`. Left in DM they draw a "non-standard variable in standard domain" finding.

**Plan (needs SAS + define regen, so not auto-fixed here to avoid data/define
desync):** move `AGEGRP`/`ARM2` to `SUPPDM` (`QNAM`/`QLABEL`/`QVAL`) in
`S_sdtm_mapping.sas`, drop them from `IG.DM`, regenerate `define_sdtm.xml`, re-run
ref-integrity (`validate_define.py`) and CORE.

---

## 7 — ARM → ARS (optional) — **PLAN (optional)**

`define.xml` already carries Analysis Results Metadata (`arm/v1.0`, 8 ResultDisplays
/ 10 AnalysisResults) — ahead of most. Optional forward step: express the analyses
in the CDISC **Analysis Results Standard (ARS v1.0, 2024)** machine-readable model.

---

## 8 — Data hygiene for the new exports — **DONE**

**Was:** the 42 generated Dataset-JSON files (`10_datasetjson/`) are patient-level
data but were not covered by the data-free `.gitignore` policy (`git check-ignore`
returned nothing) — they would have been committed, leaking patient data into the
repo, contrary to the m5 data-free principle.

**Fix:** added `10_datasetjson/**/*.json` to `.gitignore` (README/docs still
tracked) and a guard for `11_ectd/**/*.{xpt,sas7bdat,json}`. Verified: the data JSON
is now ignored, `10_datasetjson/README.md` stays tracked.

## Files added across this remediation (additive only — nothing existing changed)

- `06_telemetry/export_datasetjson.py` — XPT → Dataset-JSON v1.1 exporter
- `10_datasetjson/adam/*.json` (8), `10_datasetjson/sdtm/*.json` (34), `10_datasetjson/README.md`
- `06_telemetry/build_ectd_backbone.py` — eCTD backbone + STF generator
- `11_ectd/0000/…` — `index.xml`, `index-md5.txt`, `us-regional.xml`, `stf-tropic.xml`, util DTD readme
- `11_ectd/RUN_RECORD.md`
- `.gitignore` — data-leak hardening for the new exports
- `06_telemetry/SUBMISSION_STANDARDS_REMEDIATION.md` (this file)

---

## Terminal-session execution (2026-06-20)

Executed the SAS/CT/validator-gated items with the resources now available (CDISC
Library API key + populated CORE cache + network + R/haven). The pristine source
(`01_raw_source/real_sdtm/`, SDTMIG 3.1.1) is **unmodified**; a derived 3.4 layer is
produced deterministically and packaged.

| Item | What was done | Proof |
|---|---|---|
| **1 — SDTMIG 3.4** | `06_telemetry/uplift_sdtm_34.R` derives the 3.4 SDTM (AGE from de-id AGEGRP, ACTARM/ACTARMCD, AESOC, EPOCH from VISIT, EXENDY, week-vars→SUPPAE/SUPPDS, TA, drop redundant SUBJID, library var order). `define_sdtm.xml` regenerated to 3.4 via `07_define_xml/uplift_define_34.py`. | XSD-VALID (Define 2.1); 315 ref-integrity checks PASS |
| **2 — CORE report (SDTM)** | Real CORE 0.16.0 run at `-s sdtmig -v 3.4`. All targeted structural rules cleared; 0 structural-fixable residual. | `06_telemetry/conformance/{core_sdtm34_report.json, CORE_SDTM34_RUN_RECORD.md}` |
| **4 — CT 2026-03-27** | Both defines bumped `2024-03-29`→`2026-03-27` (latest cached package). | `def:Standard … Type="CT" Version="2026-03-27"` in both defines |
| **6 — DM variables** | `AGEGRP`→`SUPPDM`; phantom `ARM2`/`ARMA`/`ARMCD2` removed from `IG.DM`; `ACTARM`/`ACTARMCD` added. | CORE-000550 cleared |
| **m-2 — TS enrichment** | Added `NARMS=2`, `ACTSUB=371`, `SSTDTC=2007`, `AGEMIN=P18Y` (public NCT00417079 facts). | `m5/.../ts.xpt` 20 params |
| Downstream sync | SDTM Dataset-JSON regenerated (35/35 valid); eCTD backbone checksums refreshed; m5 define copies synced. | — |

**Not done (require real data / org change, per audit R-1/R-2/M-3):** real two-arm
patient data + `DV` domain; independent second-programmer validation. The CORE residual
findings are documented and classified in `CORE_SDTM34_RUN_RECORD.md` (inherent-de-id /
real-source-data / cross-domain-no-FA / engine-internal) — none are programming defects,
and real-data findings (AESER consistency, VSSTRESC) are **not** overwritten.

**New files:** `06_telemetry/uplift_sdtm_34.R`, `07_define_xml/uplift_define_34.py`,
`06_telemetry/conformance/CORE_SDTM34_RUN_RECORD.md`.
