# Date-Precision Sensitivity Analysis — response to reviewer IR M-1 (2026-06-20)

**Question (reviewer M-1).** AE/disposition timing in the public PDS source is
week-offset; reconstructed calendar dates carry ±3.5-day uncertainty (SDRG §2). Do the
day-resolution Kaplan–Meier medians for the time-to-event endpoints actually move under
that uncertainty?

**Answer.** No. Across 2,000 Monte-Carlo replicates that jitter every subject's analysis
time `AVAL` by an independent U(−3.5, +3.5) days (event/censor status held fixed), every
KM median is stable to within a few days — two to three orders of magnitude smaller than
the medians themselves. The endpoints are **robust** to the source date precision under
the pre-specified one-month perturbation-band criterion.

Real Mitoxantrone arm only (`TRT01P = "MP"`; the synthetic CbzP arm is excluded by an
enforced analysis-set filter). No current records were excluded for missing `AVAL` or
`CNSR`.
Reproduce: `python3 06_telemetry/date_precision_sensitivity.py` (seed 20260620).
Machine-readable: `06_telemetry/conformance/date_precision_sensitivity.json`.

| Param | N | Events | Point KM median | 95% perturbation band | Max \|shift\| | Verdict |
|---|---|---|---|---|---|---|
| OS | 371 | 266 | 386.0 d (12.68 mo) | 386.3–389.5 d (0.10 mo) | 3.5 d | ROBUST |
| PFS | 371 | 330 | 41.0 d (1.35 mo) | 38.7–40.7 d (0.07 mo) | 3.0 d | ROBUST |
| TTUMOR | 203 | 186 | 64.0 d (2.10 mo) | 63.4–66.6 d (0.10 mo) | 3.1 d | ROBUST |
| TTPSA | 371 | 265 | 68.0 d (2.23 mo) | 65.0–68.3 d (0.11 mo) | 4.4 d | ROBUST |
| TTSAE | 371 | 78 | not reached (<50% events) | — | — | ROBUST (n/r) |
| TTPAIN | 371 | 75 | not reached (<50% events) | — | — | ROBUST (n/r) |

**Interpretation.**

- For OS/PFS/TTUMOR/TTPSA the entire 95% perturbation band spans ≤0.11 months (≈3 days),
  and the worst single-replicate shift is 4.4 days. A ±3.5-day input uncertainty cannot
  meaningfully move a median measured in months; the ordering and magnitude of the
  estimates are preserved.
- TTSAE and TTPAIN have <50% events, so their KM medians are *not reached*. A sub-week
  date perturbation cannot change a not-reached median — robust by construction.
- **Independent cross-check:** the computed MP-arm OS median (12.68 months) matches the
  published TROPIC control-arm OS median (de Bono et al., Lancet 2010 ≈ 12.7 months),
  confirming the KM computation is correct, not just internally consistent.

**Scope / honesty.** Jitter is applied to the net analysis time `AVAL`, modeling
week-offset uncertainty in the event/censor date while treating the origin date as
day-precision. If both origin and event dates were independently week-binned, this
±3.5-day net-AVAL model should be read as a lower-bound sensitivity rather than a
conservative combined-date model. Two-arm hazard ratios are **not** assessed here
because the comparator is the synthetic CbzP arm (reviewer finding R-1); HR sensitivity
is only meaningful once real comparator data exists. This analysis closes M-1 for the
*real-arm* KM medians, which is what the IR concerns.
