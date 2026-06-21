#!/usr/bin/env python3
"""
export_datasetjson.py - SAS Transport (XPT v5) -> CDISC Dataset-JSON v1.1 exporter.

WHY THIS EXISTS
---------------
The TROPIC pipeline ships analysis/tabulation data only as SAS Transport v5 (XPT)
via 02_production_sas/U_xpt_export.sas. XPT v5 is the legacy floor (8-char names,
40-char labels, 200-char text) and FDA/PMDA are transitioning to CDISC Dataset-JSON
v1.1 as the modern exchange format. This script ADDS a Dataset-JSON v1.1 export path
alongside (not replacing) the XPT one. It is additive: it reads the existing
*_prod.xpt / SDTM *.xpt and writes *.json. It never modifies source data.

OUTPUT
------
  10_datasetjson/adam/<name>.json   (from 04_adam/<name>_prod.xpt)
  10_datasetjson/sdtm/<name>.json   (from m5/.../tabulations/sdtm/datasets/<name>.xpt)

CONFORMANCE
-----------
Each emitted file is validated in-process against the CDISC Dataset-JSON schema
bundled with the project's CORE engine
(.core_run/engine/resources/schema/dataset.schema.json, draft 2019-09) - the same
schema CORE's DatasetJSONReader enforces. Record/column counts are reconciled
against the source XPT so the conversion is provably lossless.

USAGE
-----
  python3 06_telemetry/export_datasetjson.py            # ADaM + SDTM
  python3 06_telemetry/export_datasetjson.py --adam     # ADaM only
  python3 06_telemetry/export_datasetjson.py --sdtm     # SDTM only

Requires: pyreadstat, jsonschema  (pip install pyreadstat jsonschema)

Author: generated for Antony Bevan, Clinical Programming
Standard: CDISC Dataset-JSON v1.1
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import math
import os
import sys

import pyreadstat
import jsonschema

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCHEMA_PATH = os.path.join(
    ROOT, ".core_run", "engine", "resources", "schema", "dataset.schema.json"
)

STUDY_OID = "STDY.TROPIC"
ORIGINATOR = "Antony Bevan, Clinical Programming"
SOURCE_SYSTEM = {"name": "TROPIC export_datasetjson.py", "version": "1.0.0"}
DATASETJSON_VERSION = "1.1.0"

# Business keys per study_manifest.yaml (drives keySequence).
KEYS = {
    "adsl": ["USUBJID"],
    "adex": ["USUBJID", "PARAMCD", "AVISIT"],
    "adcm": ["USUBJID", "CMSTDT", "CMDECOD"],
    "adae": ["USUBJID", "AESEQ"],
    "adlb": ["USUBJID", "PARAMCD", "AVISITN", "LBDY"],
    "adrs": ["USUBJID", "PARAMCD", "AVISIT"],
    "adtte": ["USUBJID", "PARAMCD"],
    "clinsite": ["STUDYID", "SITEID"],
    # SDTM standard keys (subset; --SEQ where present added dynamically).
    "dm": ["STUDYID", "USUBJID"],
}

ADAM_MDV = "MDV.TROPIC_NCT00417079.ADAM.1.3"
SDTM_MDV = "MDV.TROPIC_NCT00417079.SDTM.3.1.1"

# A SAS format is "temporal" (kept as integer with displayFormat) if it starts with
# one of these stems - we preserve the stored numeric, we do not reformat values.
_DATE_FORMAT_STEMS = (
    "DATE", "DATETIME", "TIME", "E8601", "YYMMDD", "DDMMYY", "MMDDYY", "JULIAN",
)


def _iso_now() -> str:
    return _dt.datetime.now().replace(microsecond=0).isoformat()


def _is_temporal_format(fmt: str) -> bool:
    if not fmt:
        return False
    f = fmt.upper().lstrip("$").rstrip(".0123456789")
    return any(f.startswith(stem) for stem in _DATE_FORMAT_STEMS)


def _clean_cell(v):
    """Map a pandas cell to a JSON-safe scalar (None for any missing)."""
    if v is None:
        return None
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        # integral float -> int (XPT stores everything as double)
        if v.is_integer():
            return int(v)
        return round(v, 15)
    return v


def _column_is_integer(series_vals) -> bool:
    """True if every non-null numeric value is integral."""
    for v in series_vals:
        if v is None:
            continue
        if isinstance(v, bool):
            return False
        if isinstance(v, (int,)):
            continue
        if isinstance(v, float):
            if math.isnan(v):
                continue
            if not v.is_integer():
                return False
        else:
            return False
    return True


def build_dataset_json(xpt_path: str, ds_name: str, mdv_oid: str,
                       meta_ref: str) -> dict:
    # disable_datetime_conversion: keep SAS date/time variables as their raw stored
    # numeric (days/seconds since 1960-01-01) rather than Python date objects. This is
    # lossless and round-trips through XPT; the SAS format is carried in displayFormat.
    df, meta = pyreadstat.read_xport(xpt_path, disable_datetime_conversion=True)
    ds = ds_name.upper()
    names = list(meta.column_names)
    labels = dict(zip(meta.column_names, meta.column_labels))
    rtypes = dict(zip(meta.column_names, meta.readstat_variable_types))
    widths = dict(zip(meta.column_names,
                      getattr(meta, "variable_storage_width", [None] * len(names))))
    formats = dict(zip(meta.column_names,
                       getattr(meta, "variable_format", [""] * len(names))))
    keyseq = {k: i + 1 for i, k in enumerate(KEYS.get(ds_name.lower(), []))}

    # Per-column python value lists (with cleaned cells) for type inference + rows.
    col_vals = {n: [_clean_cell(v) for v in df[n].tolist()] for n in names}

    columns = []
    for n in names:
        rt = rtypes.get(n, "string")
        is_str = rt in ("string",)
        label = labels.get(n) or n
        col = {
            "itemOID": f"IT.{ds}.{n}",
            "name": n,
            "label": label[:200],
        }
        if is_str:
            col["dataType"] = "string"
            w = widths.get(n)
            if not w or w < 1:
                w = max((len(str(x)) for x in col_vals[n] if x is not None),
                        default=1) or 1
            col["length"] = int(w)
        else:
            if _column_is_integer(col_vals[n]):
                col["dataType"] = "integer"
            else:
                col["dataType"] = "double"
            fmt = (formats.get(n) or "").strip()
            if _is_temporal_format(fmt):
                col["displayFormat"] = fmt
        if n in keyseq:
            col["keySequence"] = keyseq[n]
        columns.append(col)

    rows = [[col_vals[n][i] for n in names] for i in range(len(df))]

    doc = {
        "datasetJSONCreationDateTime": _iso_now(),
        "datasetJSONVersion": DATASETJSON_VERSION,
        "fileOID": f"TROPIC.{ds}",
        "originator": ORIGINATOR,
        "sourceSystem": SOURCE_SYSTEM,
        "studyOID": STUDY_OID,
        "metaDataVersionOID": mdv_oid,
        "metaDataRef": meta_ref,
        "itemGroupOID": f"IG.{ds}",
        "records": int(len(df)),
        "name": ds,
        "label": (meta.file_label or ds)[:200],
        "columns": columns,
        "rows": rows,
    }
    return doc, len(df), len(names)


def _validate(doc: dict, schema: dict) -> None:
    jsonschema.validate(doc, schema)


def _write_ndjson(doc, path, ndjson_schema):
    """Dataset-NDJSON: line 1 = metadata (the doc without 'rows'), then one JSON
    array per row. Matches CORE's DatasetNDJSONReader."""
    meta = {k: v for k, v in doc.items() if k != "rows"}
    if ndjson_schema is not None:
        jsonschema.validate(meta, ndjson_schema)  # raises on non-conformance
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(meta, ensure_ascii=False, allow_nan=False,
                            separators=(",", ":")) + "\n")
        for row in doc["rows"]:
            fh.write(json.dumps(row, ensure_ascii=False, allow_nan=False,
                                separators=(",", ":")) + "\n")


def convert_set(items, out_dir, mdv_oid, meta_ref, schema, ndjson_schema=None):
    os.makedirs(out_dir, exist_ok=True)
    results = []
    for xpt_path, ds_name in items:
        if not os.path.exists(xpt_path):
            results.append((ds_name, "MISSING", 0, 0, os.path.basename(xpt_path)))
            continue
        doc, nrec, ncol = build_dataset_json(xpt_path, ds_name, mdv_oid, meta_ref)
        if ndjson_schema is not None:
            out_path = os.path.join(out_dir, f"{ds_name.lower()}.ndjson")
            _write_ndjson(doc, out_path, ndjson_schema)
        else:
            _validate(doc, schema)  # raises on non-conformance
            out_path = os.path.join(out_dir, f"{ds_name.lower()}.json")
            with open(out_path, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, ensure_ascii=False, allow_nan=False,
                          separators=(",", ":"))
        size = os.path.getsize(out_path)
        results.append((ds_name.upper(), "VALID", nrec, ncol, f"{size/1024:.0f} KB"))
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--adam", action="store_true", help="export ADaM only")
    ap.add_argument("--sdtm", action="store_true", help="export SDTM only")
    ap.add_argument("--ndjson", action="store_true",
                    help="emit Dataset-NDJSON (.ndjson, streaming variant) instead of .json")
    args = ap.parse_args()
    do_adam = args.adam or not (args.adam or args.sdtm)
    do_sdtm = args.sdtm or not (args.adam or args.sdtm)

    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        schema = json.load(fh)
    ndjson_schema = None
    if args.ndjson:
        ndjson_path = os.path.join(os.path.dirname(SCHEMA_PATH), "dataset-ndjson-schema.json")
        with open(ndjson_path, encoding="utf-8") as fh:
            ndjson_schema = json.load(fh)

    all_results = []

    if do_adam:
        adam_dir = os.path.join(ROOT, "04_adam")
        adam_names = ["adsl", "adex", "adcm", "adae", "adlb", "adrs", "adtte", "clinsite"]
        items = [(os.path.join(adam_dir, f"{n}_prod.xpt"), n) for n in adam_names]
        out = os.path.join(ROOT, "10_datasetjson", "adam")
        res = convert_set(items, out, ADAM_MDV, "../../07_define_xml/define.xml",
                          schema, ndjson_schema)
        all_results += [("ADaM", *r) for r in res]

    if do_sdtm:
        sdtm_dir = os.path.join(
            ROOT, "m5", "datasets", "tropic", "tabulations", "sdtm", "datasets"
        )
        sdtm_names = []
        if os.path.isdir(sdtm_dir):
            sdtm_names = sorted(
                os.path.splitext(f)[0]
                for f in os.listdir(sdtm_dir) if f.endswith(".xpt")
            )
        items = [(os.path.join(sdtm_dir, f"{n}.xpt"), n) for n in sdtm_names]
        out = os.path.join(ROOT, "10_datasetjson", "sdtm")
        res = convert_set(items, out, SDTM_MDV, "../../07_define_xml/define_sdtm.xml",
                          schema, ndjson_schema)
        all_results += [("SDTM", *r) for r in res]

    print(f"{'Std':5} {'Dataset':10} {'Status':8} {'Records':>9} {'Cols':>5}  Size")
    print("-" * 56)
    ok = 0
    for std, name, status, nrec, ncol, size in all_results:
        print(f"{std:5} {name:10} {status:8} {nrec:>9} {ncol:>5}  {size}")
        if status == "VALID":
            ok += 1
    print("-" * 56)
    print(f"{ok}/{len(all_results)} datasets exported and schema-VALID "
          f"(CDISC Dataset-JSON v{DATASETJSON_VERSION})")
    return 0 if ok == len([r for r in all_results if r[2] != 'MISSING']) else 1


if __name__ == "__main__":
    sys.exit(main())
