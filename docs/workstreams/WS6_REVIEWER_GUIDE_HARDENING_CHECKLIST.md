# WS-6 Reviewer Guide Hardening Checklist

**Workstream:** Regulatory Writing / Reviewer Explanation  
**Gates:** G07 (primary), G08 narrative  
**Product claim:** Path A only  
**As of:** 2026-08-05
**Current board status:** GREEN for Path A; external qualified review required

**Section 2 review addendum (2026-08-03):** F-011 is resolved for the current PSA response set using observed baseline PSA (MP 61/329; CbzP 145/361). The SAP `T-11-8` TTPAIN/response collision, TTUMOR population wording and pain/RT component decision were handed to WS-2/WS-4 for controlled implementation.

**Section 3/4 review addendum (2026-08-03):** ADRG, SDRG, BDRG, and the traceability matrix were rechecked against the corrected ADTTE derivations. PFS now exposes pain-led versus non-pain component labels, TTUMOR excludes death milestones, and no-post-baseline PFS censoring is explicit.

**Author-decision addendum (2026-08-04):** Antony Bevan adopted ED-01–ED-07 as written under the disclosed single-author Path A governance model. The corrected pain/CM+PR derivation, TTUMOR ITT primary and SAP-native `T-11-3`–`T-11-8` mappings are implemented, internally reconciled and bound by the final full-DAG release seal. Reviewer guides must preserve the Path A boundary and must never imply independent or sponsor approval.

---

## 1. Goal

Make ADRG / SDRG / BDRG read like **controlled reviewer deliverables**, not engineering notebooks—while staying strictly inside `docs/PRODUCT_CLAIM.md`.

---

## 2. Required front-matter (every guide)

Each of ADRG, SDRG, BDRG must contain—near the top:

- [x] Link to **product claim** Path A  
- [x] Link to current tag / release note `v0.2.1-portfolio`
- [x] Explicit **document version + date + supersedes** line — **ADRG + SDRG + BDRG done**  
- [x] **what this package is / is not** — **ADRG + SDRG + BDRG done**  
- [x] Pointer to **known-differences memo** — **ADRG + SDRG + BDRG done**  

---

## 3. ADRG hardening checklist

| Section theme | Required content | Status |
|---|---|---|
| Analysis authority | SAP v4.0 + lock memo; not sponsor filing SAP | **Done (S1)** |
| Data provenance | MP real / CbzP synthetic; Guyot vs PH | **Done (S1)** §1 + §7 |
| Populations | ITT/Safety/MEASDISF consistent with WS-2 table | Present §5.4 — recheck at S2 |
| Validation | Dual-lang + admiral + single-author disclosure | **Done (S1)** §6.0 Path A talk track |
| Residuals | F-003, F-012, F-014 language; F-011 closure | **Updated (S2)** — F-011 closure evidence and the Section 2 SAP/TFL findings are linked; F-003/012 remain in §7 |
| TFL scope | Controlled catalog 21 IDs; deferred 18 | **Done (S1)** §6.0 table |
| OCCDS | v1.0 + custom episode merge; no OCCDS v1.1 | Present |
| Part 11 | Explicit non-claim | **Done (S1)** §0 table |

**Pass criterion:** A hostile reader cannot quote ADRG to claim filing readiness or confirmatory CbzP efficacy.  
**S1 self-check:** Met for ADRG 1.1 (2026-07-09).

---

## 4. SDRG hardening checklist

| Section theme | Required content | Status |
|---|---|---|
| Source origin | PDS/Sanofi 2013; MP only | **Done (S2)** §0–§1 |
| Precision | Week offsets / partial ISO (F-017) | **Done (S2)** §2 / §4.5 / §5.1 |
| Conformance | CORE 3.4 run + residual honesty (F-015) | **Done (S2)** §5.1 class table |
| Uplift | 3.1.1 source → 3.4 package layer | **Done (S2)** §5 |
| Redistribution | No patient XPT in git | **Done (S2)** §0 |
| Release pointer | Tag + release note + WS-1 pack | **Done (S2)** §0 |
| Path A is/is-not | Mirror PRODUCT_CLAIM | **Done (S2)** §0 |

**Pass criterion:** Source limitations are complete enough that WS-1 pack and SDRG never conflict.  
**S2 self-check:** Met for SDRG 1.1 (2026-07-09).

---

## 5. BDRG hardening checklist

| Section theme | Required content | Status |
|---|---|---|
| clinsite purpose | BIMO site-level rollup | **Done (S3)** |
| Schema | Variables, keys, generation program | **Done (S3)** §3 |
| Validation | Dual-lang recon + single-author disclosure | **Done (S3)** §4 |
| Limitations | Demo package / TCG subset boundary | **Done (S3)** §0–§2 |
| Path A is/is-not | Mirror PRODUCT_CLAIM | **Done (S3)** |

---

## 6. Traceability matrix

| Check | Status |
|---|---|
| ADCM keys ASTDT | Fixed (F-023) |
| T-17 present | Fixed |
| Stage model + admiral | Fixed (manifest-derived) |
| Aligns with controlled TFL catalog (21 / deferred 18) | **Done (S3)** §3.1–§3.2 |
| No L-01 claim | Fixed |
| Path A front-matter | **Done (S3)** |

---

## 7. Editing rules (discipline)

1. **No new scientific claims** without WS-2/WS-4 agreement.  
2. **No “submission-ready”** adjectives. Prefer “submission-style,” “controlled demo,” “Path A.”  
3. Every residual Critical/Major mentioned must appear in the known-differences memo.  
4. Prefer short, definitive sentences over marketing.

---

## 8. Sprint plan (deep work, 2–3 sessions)

| Session | Deliverable | Status |
|---|---|---|
| S1 | ADRG: PRODUCT_CLAIM + known-differences; Path A validation talk track | **DONE** (`ADRG.md` v1.1) |
| S2 | SDRG: CORE residual honesty + WS-1 pack link; precision § audit | **DONE** (`SDRG.md` v1.1) |
| S3 | BDRG depth pass + TRACEABILITY_MATRIX catalog alignment | **DONE** (`BDRG.md` + `TRACEABILITY_MATRIX.md` v1.1) |
| S4 | Corrected ADTTE/PSA reviewer-language and package crosswalk | **DONE** (Section 3/4 audit memos, ADRG, WS-5/board updates) |

S1–S4 are complete; review notes are under `docs/workstreams/reviews/WS6_S*_*.md`. The board is **GREEN** for the Path A narrative, and the reviewer-guide PDFs were regenerated into the package during the v0.2.1 audit-closure release.

---

## 9. Exit criteria for WS-6 GREEN (Path A)

- [x] All three guides carry Path A non-claim language  
- [x] Known-differences memo linked  
- [x] No conflict with PRODUCT_CLAIM (self-check S1–S3)  
- [x] Hostile-reader test passed (self with checklist)  
- [x] Review notes filed (S1, S2, S3)  
- [x] Re-package ADRG/SDRG/BDRG PDFs into `m5/` during the v0.2.1 audit-closure run
