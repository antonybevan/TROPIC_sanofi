# WS-6 Reviewer Guide Hardening Checklist

**Workstream:** Regulatory Writing / Reviewer Explanation  
**Gates:** G07 (primary), G08 narrative  
**Product claim:** Path A only  
**As of:** 2026-07-09  
**Current board status:** AMBER  

---

## 1. Goal

Make ADRG / SDRG / BDRG read like **controlled reviewer deliverables**, not engineering notebooks—while staying strictly inside `docs/PRODUCT_CLAIM.md`.

---

## 2. Required front-matter (every guide)

Each of ADRG, SDRG, BDRG must contain—near the top:

- [x] Link to **product claim** Path A (add if missing on next edit pass)  
- [x] Link to tag / release note `v0.1.0-demo-rc.1` (ADRG/SDRG done)  
- [ ] Explicit **document version + date + supersedes** line  
- [ ] One paragraph: **what this package is / is not** (mirror PRODUCT_CLAIM §2)  
- [ ] Pointer to **known-differences memo** `docs/workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md`

---

## 3. ADRG hardening checklist

| Section theme | Required content | Status |
|---|---|---|
| Analysis authority | SAP v4.0 + lock memo; not sponsor filing SAP | Partial |
| Data provenance | MP real / CbzP synthetic; Guyot vs PH | Present |
| Populations | ITT/Safety/MEASDISF consistent with WS-2 table | Partial—cross-check |
| Validation | Dual-lang + admiral + single-author disclosure | Present—must match PRODUCT_CLAIM §6 |
| Residuals | F-003, F-011, F-012, F-014 language | Must cite known-differences memo |
| TFL scope | Controlled catalog 18 IDs; deferred 21 | Must not claim full Appendix D |
| OCCDS | v1.0 + custom episode merge; no OCCDS v1.1 | Present |
| Part 11 | Explicit non-claim | Required |

**Pass criterion:** A hostile reader cannot quote ADRG to claim filing readiness or confirmatory CbzP efficacy.

---

## 4. SDRG hardening checklist

| Section theme | Required content | Status |
|---|---|---|
| Source origin | PDS/Sanofi 2013; MP only | Present |
| Precision | Week offsets / partial ISO (F-017) | Present |
| Conformance | CORE 3.4 run + residual honesty (F-015) | Partial |
| Uplift | 3.1.1 source → 3.4 package layer | Present |
| Redistribution | No patient XPT in git | Present |
| Release pointer | Tag + release note | Present |

**Pass criterion:** Source limitations are complete enough that WS-1 pack and SDRG never conflict.

---

## 5. BDRG hardening checklist

| Section theme | Required content | Status |
|---|---|---|
| clinsite purpose | BIMO site-level rollup | Present |
| Schema | Variables, keys, generation program | Verify depth |
| Validation | Recon with dual-lang | Present if recon includes clinsite |
| Limitations | Demo package boundary | Required |

---

## 6. Traceability matrix

| Check | Status |
|---|---|
| ADCM keys ASTDT | Fixed (F-023) |
| T-17 present | Fixed |
| Stage model 30 + admiral | Fixed |
| Aligns with controlled TFL catalog | Required ongoing |
| No L-01 claim | Fixed |

---

## 7. Editing rules (discipline)

1. **No new scientific claims** without WS-2/WS-4 agreement.  
2. **No “submission-ready”** adjectives. Prefer “submission-style,” “controlled demo,” “Path A.”  
3. Every residual Critical/Major mentioned must appear in the known-differences memo.  
4. Prefer short, definitive sentences over marketing.

---

## 8. Sprint plan (deep work, 2–3 sessions)

| Session | Deliverable |
|---|---|
| S1 | ADRG: insert PRODUCT_CLAIM + known-differences; rewrite validation § to Path A talk track |
| S2 | SDRG: CORE residual honesty + WS-1 pack link; precision § audit |
| S3 | BDRG depth pass + TRACEABILITY_MATRIX catalog alignment |

After S1–S3: file `docs/workstreams/reviews/WS6_review_YYYYMMDD.md` and move board toward GREEN.

---

## 9. Exit criteria for WS-6 GREEN (Path A)

- [ ] All three guides carry Path A non-claim language  
- [ ] Known-differences memo linked  
- [ ] No conflict with PRODUCT_CLAIM  
- [ ] Hostile-reader test passed (peer or self with checklist)  
- [ ] Review note filed  
