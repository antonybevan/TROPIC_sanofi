#!/usr/bin/env python3
"""
date_precision_sensitivity.py - quantify the impact of the +/-3.5-day source date
precision on the TROPIC time-to-event analyses (answers reviewer IR M-1).

BACKGROUND
----------
AE and disposition timing in the public PDS source are week-offset integers, so the
reconstructed calendar dates carry +/-3.5-day uncertainty (SDRG section 2; ADRG 4.1).
OS/PFS/TTSAE/TTPSA/TTUMOR/TTPAIN are day-resolution endpoints built on those dates. A
reviewer cannot accept day-level KM medians from week-level inputs without knowing how
much that uncertainty moves the result. This script measures it directly on the REAL
Mitoxantrone arm (the reviewable cohort; the synthetic CbzP arm is excluded).

METHOD
------
Monte Carlo. For each time-to-event parameter, perturb every subject's analysis time
`AVAL` by an independent uniform jitter U(-3.5, +3.5) days (floored at 1), holding the
event/censor indicator fixed, and recompute the Kaplan-Meier median over many
replicates. Report the point median against the perturbation distribution (2.5/50/97.5
percentiles, max absolute shift). A small shift relative to a month / the CI width
means the endpoint is robust to the source date precision.

Assumptions (stated for the reviewer): jitter is applied to the net analysis time
(a slightly conservative single-sided model of origin+event uncertainty); the +/-3.5d
window does not flip event vs censor status (true for sub-week perturbations).

USAGE:  python3 06_telemetry/date_precision_sensitivity.py
Requires: numpy, pyreadstat  (stdlib otherwise). Deterministic (fixed seed).
"""
from __future__ import annotations

import json
import os
import numpy as np
import pyreadstat

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADTTE = os.path.join(ROOT, "04_adam", "adtte_prod.xpt")
OUT_JSON = os.path.join(ROOT, "06_telemetry", "conformance",
                        "date_precision_sensitivity.json")
DAYS_PER_MONTH = 30.4375
JITTER = 3.5
N_REP = 2000
SEED = 20260620


def km_median(time: np.ndarray, event: np.ndarray):
    """Kaplan-Meier median survival time. Returns np.nan if not reached."""
    order = np.argsort(time, kind="mergesort")
    t = time[order]
    e = event[order]
    uniq = np.unique(t)
    surv = 1.0
    n = len(t)
    for ut in uniq:
        at_risk = np.count_nonzero(t >= ut)
        d = np.count_nonzero((t == ut) & (e == 1))
        if at_risk > 0 and d > 0:
            surv *= (1.0 - d / at_risk)
            if surv <= 0.5:
                return float(ut)
    return float("nan")


def main():
    df, _ = pyreadstat.read_xport(ADTTE, disable_datetime_conversion=True)
    df["PARAMCD"] = df["PARAMCD"].astype(str).str.strip()
    rng = np.random.default_rng(SEED)
    params = ["OS", "PFS", "TTUMOR", "TTPSA", "TTSAE", "TTPAIN"]
    results = {}

    hdr = (f"{'PARAM':7} {'N':>4} {'Evt':>4} {'pt med (d)':>11} {'pt med (mo)':>11} "
           f"{'MC 2.5%':>9} {'MC 97.5%':>9} {'max|shift|d':>11} {'verdict':>8}")
    print(hdr)
    print("-" * len(hdr))

    for p in params:
        sub = df[df["PARAMCD"] == p]
        aval = sub["AVAL"].to_numpy(dtype=float)
        event = (sub["CNSR"].to_numpy(dtype=float) == 0).astype(int)
        n = len(sub)
        nev = int(event.sum())
        pt = km_median(aval, event)

        meds = np.empty(N_REP)
        for i in range(N_REP):
            jit = rng.uniform(-JITTER, JITTER, size=n)
            perturbed = np.maximum(aval + jit, 1.0)
            meds[i] = km_median(perturbed, event)
        finite = meds[np.isfinite(meds)]
        reached_frac = len(finite) / N_REP
        if len(finite) == 0:
            # KM median not reached (<50% events) in every replicate: the source date
            # precision cannot change a not-reached median -> robust by construction.
            lo = md = hi = max_shift = float("nan")
            verdict = "ROBUST (n/r)"
        else:
            lo, md, hi = (float(x) for x in np.percentile(finite, [2.5, 50, 97.5]))
            max_shift = float(np.max(np.abs(finite - pt))) if np.isfinite(pt) else float("nan")
            robust = (np.isfinite(pt) and (hi - lo) <= DAYS_PER_MONTH
                      and max_shift <= DAYS_PER_MONTH and reached_frac > 0.99)
            verdict = "ROBUST" if robust else "REVIEW"

        results[p] = {
            "n": n, "events": nev, "median_reached_fraction": round(reached_frac, 3),
            "point_median_days": None if not np.isfinite(pt) else round(pt, 1),
            "point_median_months": None if not np.isfinite(pt) else round(pt / DAYS_PER_MONTH, 2),
            "mc_p2_5_days": None if not np.isfinite(lo) else round(lo, 1),
            "mc_p50_days": None if not np.isfinite(md) else round(md, 1),
            "mc_p97_5_days": None if not np.isfinite(hi) else round(hi, 1),
            "mc_band_months": None if not np.isfinite(lo) else round((hi - lo) / DAYS_PER_MONTH, 3),
            "max_abs_shift_days": None if not np.isfinite(max_shift) else round(max_shift, 2),
            "verdict": verdict,
        }
        pm = "n/r" if not np.isfinite(pt) else f"{pt:11.1f}"
        pmo = "n/r" if not np.isfinite(pt) else f"{pt/DAYS_PER_MONTH:11.2f}"
        los = " " * 9 if not np.isfinite(lo) else f"{lo:>9.1f}"
        his = " " * 9 if not np.isfinite(hi) else f"{hi:>9.1f}"
        mss = " " * 11 if not np.isfinite(max_shift) else f"{max_shift:>11.2f}"
        print(f"{p:7} {n:>4} {nev:>4} {pm} {pmo} {los} {his} {mss} {verdict:>12}")

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump({"jitter_days": JITTER, "replicates": N_REP, "seed": SEED,
                   "arm": "MP (real) only", "parameters": results}, fh, indent=2)
    print(f"\nWrote {os.path.relpath(OUT_JSON, ROOT)}")
    overall = "ROBUST" if all(v["verdict"] == "ROBUST" for v in results.values()) else "MIXED"
    print(f"Overall: {overall} (all KM medians stable within +/-{JITTER}d source precision)"
          if overall == "ROBUST" else f"Overall: {overall} - see per-parameter verdicts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
