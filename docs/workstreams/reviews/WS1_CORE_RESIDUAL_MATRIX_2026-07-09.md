# WS-1 Review Note — CORE Residual Matrix

**Date:** 2026-07-09  
**Workstream:** WS-1 Source Intake (with WS-3)  
**Product claim:** Path A  

## Deliverable

[`docs/workstreams/WS1_CORE_RESIDUAL_MATRIX.csv`](../WS1_CORE_RESIDUAL_MATRIX.csv)

Source of residual CORE rows: [`platform/conformance/CORE_SDTM34_RUN_RECORD.md`](../../../platform/conformance/CORE_SDTM34_RUN_RECORD.md) (2026-06-20 run).

## Disposition summary

| disposition | Meaning | Row classes |
|---|---|---|
| **fix** | Structural uplift targets cleared | CORE-000264/453/701/776/550 + structural batch |
| **accept** | Cannot or must not “fix” for Path A | inherent de-id · real source data · engine-internal · SOURCE week/partial dates (F-017) |
| **waive** | Out of package scope | CORE-000767 RELREC/FA without FA domain |

**Headline (unchanged science):** structural-fixable residual = **0**.  
**Headline (honesty):** total issue occurrences remain high → **not** “CORE clean.”

## Finding linkage

| Finding | Matrix coverage |
|---|---|
| F-015 | All CORE-* residual and cleared rows |
| F-017 | SOURCE-WEEK-OFFSET · SOURCE-PARTIAL-ISO rows |

## Forbidden claims (still)

- Full commercial Pinnacle 21 clearance (F-016)  
- Zero CORE findings  
- Day-true AE dates  

## Linked updates

- WS-1 pack §5  
- WS-3 external validation index slot → **RUN**  
- WS-5 known-differences F-015 pointer  
- SDRG §5.1 matrix link  
- Execution board WS-1 row  

## Next

- Re-run matrix only when CORE is re-executed  
- WS-7 CI wire for `verify_release`  
