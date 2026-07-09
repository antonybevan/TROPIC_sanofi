"""Shared time-to-event utilities for reviewer-facing telemetry artifacts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

ARM_VAR = "TRT01P"
ARM_VALUE = "MP"


@dataclass(frozen=True)
class AnalysisSetCounts:
    source_n: int
    analyzed_n: int
    excluded_missing: int
    excluded_nonmatching: int


def km_median_days(time: np.ndarray, event: np.ndarray) -> float:
    """Kaplan-Meier median survival time. Returns NaN if not reached."""
    order = np.argsort(time, kind="mergesort")
    t = time[order]
    e = event[order]
    surv = 1.0
    for ut in np.unique(t):
        at_risk = np.count_nonzero(t >= ut)
        d = np.count_nonzero((t == ut) & (e == 1))
        if at_risk > 0 and d > 0:
            surv *= 1.0 - d / at_risk
            if surv <= 0.5:
                return float(ut)
    return float("nan")


def _condition_mask(df, condition: dict[str, Any]):
    variable = condition["variable"]
    comparator = condition.get("comparator", "EQ")
    values = [str(v).strip() for v in condition.get("value", [])]
    if variable not in df.columns:
        raise ValueError(f"ADTTE missing required variable: {variable}")
    if comparator != "EQ":
        raise ValueError(f"Unsupported condition comparator: {comparator}")
    return df[variable].astype(str).str.strip().isin(values)


def apply_conditions(df, conditions: list[dict[str, Any]]):
    """Apply ARS-style EQ conditions to a DataFrame and return the filtered rows."""
    mask = np.ones(len(df), dtype=bool)
    for condition in conditions:
        mask &= _condition_mask(df, condition).to_numpy()
    return df[mask].copy()


def tte_analysis_set(df, paramcd: str, conditions: list[dict[str, Any]]):
    """Return complete-case TTE records plus counts for declared conditions."""
    required = {"PARAMCD", "AVAL", "CNSR"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"ADTTE missing required variable(s): {', '.join(missing)}")
    param = df["PARAMCD"].astype(str).str.strip()
    param_df = df[param == paramcd].copy()
    if param_df.empty:
        raise ValueError(f"No records found for PARAMCD={paramcd}")
    filtered = apply_conditions(param_df, conditions)
    if filtered.empty:
        raise ValueError(f"No records remain for PARAMCD={paramcd} after declared conditions")
    clean = filtered.dropna(subset=["AVAL", "CNSR"]).copy()
    cnsr = clean["CNSR"].to_numpy(dtype=float)
    bad_cnsr = sorted(set(cnsr[~np.isin(cnsr, [0.0, 1.0])].tolist()))
    if bad_cnsr:
        raise ValueError(f"{paramcd} has invalid CNSR value(s): {bad_cnsr}")
    counts = AnalysisSetCounts(
        source_n=int(len(filtered)),
        analyzed_n=int(len(clean)),
        excluded_missing=int(len(filtered) - len(clean)),
        excluded_nonmatching=int(len(param_df) - len(filtered)),
    )
    return clean, counts
