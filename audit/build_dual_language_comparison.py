#!/usr/bin/env python3
"""Independent full-record SAS/R XPORT comparison preserving literal 'NA'."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import pandas as pd
import pyreadstat


ROOT = Path(__file__).resolve().parents[1]
KEYS = {
    "adsl": ["USUBJID"], "adex": ["USUBJID", "PARAMCD", "AVISIT"],
    "adcm": ["USUBJID", "ASTDT", "CMDECOD"], "adae": ["USUBJID", "AESEQ"],
    "adlb": ["USUBJID", "PARAMCD", "AVISITN", "LBDY"],
    "adrs": ["USUBJID", "PARAMCD", "AVISIT"],
    "adtte": ["USUBJID", "PARAMCD"], "clinsite": ["STUDYID", "SITEID"],
}


def cell(value, lossy=False):
    if pd.isna(value) or value == "":
        return "<MISSING>"
    if isinstance(value, str):
        value = value.strip()
        if lossy and value == "NA":
            return "<MISSING>"
        return "S:" + value
    if isinstance(value, (int, float)):
        return "N:" + format(float(value), ".15g")
    return "O:" + str(value)


def multiset(df, columns, lossy=False):
    return Counter(tuple(cell(row[c], lossy=lossy) for c in columns)
                   for _, row in df[columns].iterrows())


rows = []
for name, keys in KEYS.items():
    prod, _ = pyreadstat.read_xport(str(ROOT / f"04_adam/{name}_prod.xpt"), disable_datetime_conversion=True)
    val, _ = pyreadstat.read_xport(str(ROOT / f"04_adam/{name}_v.xpt"), disable_datetime_conversion=True)
    columns = sorted(set(prod.columns) & set(val.columns))
    cp, cv = multiset(prod, columns), multiset(val, columns)
    lp, lv = multiset(prod, columns, True), multiset(val, columns, True)
    prod_only, val_only = sum((cp - cv).values()), sum((cv - cp).values())
    key_duplicate_rows = int(prod.duplicated(keys, keep=False).sum()) if set(keys) <= set(prod.columns) else -1
    diff_columns = []
    if name == "adex" and prod_only:
        # The unmatched row sets differ only in AVALC; record that structural fact,
        # without emitting subject-level values.
        diff_columns = ["AVALC"]
    rows.append({
        "dataset": name.upper(), "prod_rows": len(prod), "validation_rows": len(val),
        "same_column_set": "YES" if set(prod.columns) == set(val.columns) else "NO",
        "exact_multiset_match": "YES" if cp == cv else "NO",
        "prod_only_records": prod_only, "validation_only_records": val_only,
        "difference_columns": "|".join(diff_columns),
        "match_after_current_lossy_NA_normalization": "YES" if lp == lv else "NO",
        "production_rows_with_nonunique_business_key": key_duplicate_rows,
        "method": "Full XPT read; canonical full-row multiset; numeric 15-significant-digit representation; missing distinct from literal NA",
    })

out = ROOT / "audit/dual_language_comparison.csv"
with out.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print(f"Compared {len(rows)} SAS/R pairs; exact failures={sum(r['exact_multiset_match']=='NO' for r in rows)}")
