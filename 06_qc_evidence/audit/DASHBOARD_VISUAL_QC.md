# Dashboard Visual QC — local acceptance evidence

**Status:** `PASS — local acceptance capture and live reconfirmation`

**Capture date:** 2026-08-13

**Live reconfirmation date:** 2026-08-23

**Application:** `07_reviewer_explanation/tools/shiny/app.R`

This record documents a visual acceptance pass of the read-only reviewer dashboard against the controlled local production outputs. It is portfolio evidence for rendered behavior and reviewer usability. It is not a Part 11 validation record, an independent organizational QC approval, a licensed Pinnacle 21 Enterprise result, or a submission artifact.

## Scope

The retained capture was performed at a 1440 × 1000 desktop viewport. On
2026-08-23 the current application was then exercised again through the live local
browser surface against the governed production outputs. Each panel was activated,
allowed to settle, and checked for a visible rendered output:

| Panel | Acceptance evidence |
|---|---|
| Overview | KPI cards, subgroup forest plot, provenance and evidence-boundary copy rendered without errors |
| Kaplan–Meier | All six endpoint choices (OS, PFS, TTPAIN, TTPSA, TTSAE, TTUMOR) were exercised twice, forward and reverse; each title, plot alternate text, and source disclosure matched the selection |
| Response | Waterfall and swimmer plots rendered side by side |
| Safety | Treatment-emergent filter was toggled four times; valid bounds 5 and 20 produced exactly 5 and 20 rows; invalid 4, 21, 5.5, and blank inputs failed closed with the governed validation message and no disconnect; value 10 restored 10 rows |
| Reconciliation | Six endpoint rows rendered with `PASS` status; the sort control was exercised three times and changed row order without changing the six PASS results |

The dashboard contract tests also passed:

```text
Rscript tests/test_shiny_dashboard.R
Shiny dashboard contracts: PASS

Rscript tests/test_shiny_dashboard_local.R
Local Shiny dashboard production-data contracts: PASS
```

Interactive acceptance checks also passed: all five tabs were visited twice in forward/reverse
order; every KM endpoint rendered without a visible Shiny error; the KM and Safety sidebars
collapsed while their outputs remained available; the Safety controls survived repeated valid and
invalid input; and the Reconciliation sort remained semantically stable. The Response plots were
also checked after their reactive render settled. Reloading restored a clean Overview state.

The Safari-rendered surface was used for visual acceptance. Chrome exposed the
application accessibility tree and successful resources but its Computer Use
capture returned an unpainted viewport; Safari rendering confirmed this was a
browser-capture/compositor limitation rather than a product rendering failure.
Safari's accessibility tree also retained stale expanded state after the KM sidebar
collapsed even though the visual control changed and reload recovered cleanly. This
tool/library behavior is not represented as proof of conformance; the product's
source contracts and visual result are the controlled evidence.

## Captured evidence

These screenshots contain aggregate or figure-level content only. No subject identifiers or patient-level records are rendered or retained in the evidence files.

| Panel | Evidence |
|---|---|
| Overview | [overview.jpg](dashboard_evidence/overview.jpg) |
| Kaplan–Meier | [kaplan_meier.jpg](dashboard_evidence/kaplan_meier.jpg) |
| Response | [response.jpg](dashboard_evidence/response.jpg) |
| Safety | [safety.jpg](dashboard_evidence/safety.jpg) |
| Reconciliation | [reconciliation.jpg](dashboard_evidence/reconciliation.jpg) |

## Reproduction boundary

The repository intentionally excludes patient-level XPT and derived local production inputs. A bare clone therefore enters the dashboard's disclosed data-free mode and must not invent or display placeholder clinical results. To reproduce the data-bearing capture, use the authorized local workspace, run the local dashboard contract test, start the documented Shiny app, and inspect the five panels at desktop size.

The static [TFL Gallery](../../05_outputs/tfl/TFL_Gallery.html) remains the portable public visual surface. The live dashboard is a local read-only review aid.
