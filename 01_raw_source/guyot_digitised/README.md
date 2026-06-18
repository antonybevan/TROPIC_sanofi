# Guyot reconstruction inputs — digitised KM coordinates

These files feed `reconstruct_cbzp_guyot.R`, which runs the genuine Guyot (2012)
IPD reconstruction via the `IPDfromKM` package. The reconstruction is only as
good as the digitised coordinates, so this directory is the quality-critical
input.

## Files

| File | Columns | Source | Status |
|---|---|---|---|
| `os_cbzp_digitised.csv`  | `time` (months), `surv` (0–1) | de Bono 2010 **Fig 2A**, CbzP curve | **must digitise** |
| `pfs_cbzp_digitised.csv` | `time` (months), `surv` (0–1) | de Bono 2010 **Fig 3**, CbzP curve | **must digitise** |
| `os_cbzp_nrisk.csv`      | `time`, `nrisk` | Fig 2A at-risk row | transcribed (genuine) |
| `pfs_cbzp_nrisk.csv`     | `time`, `nrisk` | Fig 3 at-risk row | transcribed (genuine) |
| `PROVENANCE`             | first line `DIGITISED` or `PLACEHOLDER` | — | flips to `DIGITISED` when done |

## Digitisation procedure (WebPlotDigitizer)

The source figure is in the repo: `../reference_literature/de_bono_lancet_2010.pdf`.

1. Open <https://automeris.io/WebPlotDigitizer/> (or the desktop build).
2. Load the figure image (export the OS / PFS panel from the PDF at high zoom).
3. **Calibrate axes** — 2D (X-Y) plot:
   - X axis: time in **months** (e.g. 0 and 24 for OS; 0 and 12 for PFS).
   - Y axis: survival probability **0 to 1.0** (the panel may print 0–100%; if so
     calibrate 0 and 100 and divide by 100 on export, or set `maxy` accordingly).
4. Trace the **CbzP arm curve only** (not MP). Use manual point mode and place
   **80–100 points**, densely around each visible step/drop.
5. Export → CSV. Rename to `os_cbzp_digitised.csv` / `pfs_cbzp_digitised.csv`
   with headers exactly `time,surv`. Ensure `surv` is on the **0–1** scale.
6. (Recommended) Save the WebPlotDigitizer project JSON here as
   `webplotdigitizer_project.json` for reproducibility.
7. Set the first line of `PROVENANCE` to `DIGITISED`.

## Notes / gotchas

- The script enforces monotonic non-increasing `surv` in [0,1] (`cummin`), so
  small digitisation jitter is tolerated — but a curve that visibly *rises* means
  you traced across both arms; re-trace.
- The OS curve has a steep drop between months 6 and 9 (at-risk 231 → 90).
  Sample that region densely or the reconstruction will smooth it out.
- After digitising, run the validation report (`guyot_validation_report.R`) and
  confirm the median, event-count, and **HR-vs-real-MP** gates pass before the
  result is used in the pipeline.
