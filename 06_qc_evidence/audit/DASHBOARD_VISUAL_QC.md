# Dashboard Visual QC — local acceptance evidence

**Status:** `PASS — local acceptance capture`

**Capture date:** 2026-08-13

**Application:** `07_reviewer_explanation/tools/shiny/app.R`

This record documents a visual acceptance pass of the read-only reviewer dashboard against the controlled local production outputs. It is portfolio evidence for rendered behavior and reviewer usability. It is not a Part 11 validation record, an independent organizational QC approval, a licensed Pinnacle 21 Enterprise result, or a submission artifact.

## Scope

The capture was performed at a 1440 × 1000 desktop viewport after the local production-data dashboard loaded successfully. Each panel was activated, allowed to settle, checked for a visible rendered output, and then captured:

| Panel | Acceptance evidence |
|---|---|
| Overview | KPI cards, subgroup forest plot, provenance and evidence-boundary copy rendered without errors |
| Kaplan–Meier | OS survival curve rendered; all six endpoint choices (OS, PFS, TTPAIN, TTPSA, TTSAE, TTUMOR) were exercised and the source disclosure remained visible |
| Response | Waterfall and swimmer plots rendered side by side |
| Safety | Treatment-emergent filter, system-organ-class slider (5 and restored to 10), preferred-term plot, and aggregate table rendered |
| Reconciliation | Six endpoint rows rendered with `PASS` status and the single-author methodological boundary visible |

The dashboard contract tests also passed:

```text
Rscript tests/test_shiny_dashboard.R
Shiny dashboard contracts: PASS

Rscript tests/test_shiny_dashboard_local.R
Local Shiny dashboard production-data contracts: PASS

Interactive acceptance checks also passed: the KM endpoint selector rendered a curve for every
endpoint without a visible Shiny error; the KM/Safety sidebars collapsed and restored; the Safety
filter was unchecked and restored; the Safety slider was moved to 5 and restored to 10; and the
Reconciliation table sort control responded while all six rows remained `PASS`. Browser console
error/warning logs were empty during the pass.
```

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
