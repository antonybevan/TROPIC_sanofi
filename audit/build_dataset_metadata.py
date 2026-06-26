#!/usr/bin/env python3
"""Extract non-patient-identifying structural metadata for SAS and XPORT data."""

from __future__ import annotations

import csv
import os
from pathlib import Path

import pyreadstat


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "audit" / "dataset_metadata.csv"


def paths():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        directory = Path(dirpath)
        dirnames[:] = [d for d in dirnames if not (directory == ROOT and d in {".git", "audit"})]
        for name in filenames:
            path = directory / name
            if path.suffix.lower() in {".sas7bdat", ".xpt"}:
                yield path


rows = []
for path in sorted(paths()):
    rel = path.relative_to(ROOT).as_posix()
    reader = pyreadstat.read_xport if path.suffix.lower() == ".xpt" else pyreadstat.read_sas7bdat
    try:
        _, meta = reader(str(path), metadataonly=True)
        sample_method = "metadata-only"
        if rel.startswith(("01_raw_source/", "04_adam/", "11_ectd/", "m5/", ".core_run/sdtm34/")):
            # Execute bounded reads as a readability check; do not emit subject-level values.
            reader(str(path), row_limit=5)
            if (meta.number_rows or 0) > 5:
                reader(str(path), row_offset=max(0, meta.number_rows - 5), row_limit=5)
            sample_method = "metadata + first/last 5-record readability sample (values not reproduced)"
        labels = meta.column_names_to_labels or {}
        missing_labels = [name for name in meta.column_names if not labels.get(name)]
        rows.append({
            "path": rel,
            "format": path.suffix.lower().lstrip("."),
            "rows": meta.number_rows,
            "columns": meta.number_columns,
            "column_names": "|".join(meta.column_names),
            "unlabelled_columns": "|".join(missing_labels),
            "inspection": sample_method,
            "status": "READABLE",
        })
    except Exception as exc:
        rows.append({
            "path": rel, "format": path.suffix.lower().lstrip("."),
            "rows": "", "columns": "", "column_names": "", "unlabelled_columns": "",
            "inspection": "metadata read attempted", "status": f"UNREADABLE: {type(exc).__name__}: {exc}",
        })

with OUT.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print(f"Inspected {len(rows)} SAS/XPORT datasets; failures={sum(r['status'] != 'READABLE' for r in rows)}")
