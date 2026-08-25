#!/usr/bin/env python3
"""
export_datasetjson.py - SAS Transport (XPT v5) -> CDISC Dataset-JSON v1.1 exporter.

WHY THIS EXISTS
---------------
The TROPIC pipeline ships analysis/tabulation data only as SAS Transport v5 (XPT)
via 04_analysis_datasets/programs/sas/U_xpt_export.sas. XPT v5 is the legacy floor (8-char names,
40-char labels, 200-char text) and FDA/PMDA are transitioning to CDISC Dataset-JSON
v1.1 as the modern exchange format. This script ADDS a Dataset-JSON v1.1 export path
alongside (not replacing) the XPT one. It is additive: it reads the existing
*_prod.xpt / SDTM *.xpt and writes *.json. It never modifies source data.

OUTPUT
------
  04_analysis_datasets/datasetjson/adam/<name>.json   (from 04_analysis_datasets/adam/<name>_prod.xpt)
  04_analysis_datasets/datasetjson/sdtm/<name>.json   (from 08_submission_package/m5/.../tabulations/sdtm/datasets/<name>.xpt)

CONFORMANCE
-----------
Each emitted file is validated in-process against the CDISC Dataset-JSON schema
bundled with the project's CORE engine
(.core_run/engine/resources/schema/dataset.schema.json, draft 2019-09) - the same
schema CORE's DatasetJSONReader enforces. Emitted files are then read back and
reconciled to the source XPT for record count, column order, and canonical cell
values.

USAGE
-----
  python3 platform/export_datasetjson.py            # ADaM + SDTM
  python3 platform/export_datasetjson.py --adam     # ADaM only
  python3 platform/export_datasetjson.py --sdtm     # SDTM only

Requires: pyreadstat, jsonschema>=4  (pip install pyreadstat 'jsonschema>=4')

Author: generated for Antony Bevan, Clinical Programming
Standard: CDISC Dataset-JSON v1.1
"""
from __future__ import annotations

import argparse
import datetime as _dt
import glob
import json
import math
import os
import sys
from typing import Any

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

# Business keys per config/study_manifest.yaml (drives keySequence).
KEYS = {
    "adsl": ["USUBJID"],
    "adex": ["USUBJID", "PARAMCD", "AVISIT"],
    "adcm": ["USUBJID", "CMDECOD", "ASTDT"],
    "adae": ["USUBJID", "AESEQ"],
    "adlb": ["USUBJID", "PARAMCD", "AVISITN", "LBDY"],
    "adrs": ["USUBJID", "PARAMCD", "AVISIT"],
    "adtte": ["USUBJID", "PARAMCD"],
    "clinsite": ["STUDYID", "SITEID"],
    # SDTM standard keys (subset; --SEQ where present added dynamically).
    "dm": ["STUDYID", "USUBJID"],
}

ADAM_MDV = "MDV.TROPIC_NCT00417079.ADAM.1.3"
# Package SDTM layer is the uplifted 3.4 deliverable (define_sdtm.xml / Module 5 tabulations).
SDTM_MDV = "MDV.TROPIC_NCT00417079.SDTM.3.4"

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
    if hasattr(v, "item"):
        v = v.item()
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    return v


def _read_xpt(xpt_path: str):
    # disable_datetime_conversion: keep SAS date/time variables as their raw stored
    # numeric (days/seconds since 1960-01-01) rather than Python date objects. This is
    # lossless and round-trips through XPT; the SAS format is carried in displayFormat.
    return pyreadstat.read_xport(xpt_path, disable_datetime_conversion=True)


def _format_map(meta, names: list[str]) -> dict[str, str]:
    """Return SAS display formats from pyreadstat metadata or fail loudly."""
    raw = getattr(meta, "original_variable_types", None)
    if isinstance(raw, dict):
        return {n: (raw.get(n) or "") for n in names}
    raw = getattr(meta, "variable_format", None)
    if isinstance(raw, (list, tuple)) and len(raw) == len(names):
        return dict(zip(names, (fmt or "" for fmt in raw)))
    raw = getattr(meta, "variable_formats", None)
    if isinstance(raw, dict):
        return {n: (raw.get(n) or "") for n in names}
    raise RuntimeError("pyreadstat metadata did not expose SAS variable formats")


def _derive_key_sequence(ds_name: str, names: list[str], mdv_oid: str) -> dict[str, int]:
    declared = KEYS.get(ds_name.lower())
    if declared is None and mdv_oid == SDTM_MDV:
        ds = ds_name.upper()
        if ds.startswith("SUPP"):
            declared = ["STUDYID", "RDOMAIN", "USUBJID", "IDVAR", "IDVARVAL", "QNAM"]
        elif f"{ds}SEQ" in names and "USUBJID" in names:
            declared = ["STUDYID", "USUBJID", f"{ds}SEQ"]
        elif f"{ds}SEQ" in names:
            declared = ["STUDYID", f"{ds}SEQ"]
        elif ds == "TA":
            declared = ["STUDYID", "ARMCD", "TAETORD", "ETCD"]
        else:
            declared = [n for n in ("STUDYID", "DOMAIN", "USUBJID") if n in names]
    declared = declared or []
    missing = [k for k in declared if k not in names]
    if missing:
        raise RuntimeError(
            f"{ds_name.upper()} keySequence references missing variable(s): "
            + ", ".join(missing)
        )
    return {k: i + 1 for i, k in enumerate(declared)}


def _canonical_rows(df, names: list[str]) -> tuple[dict[str, list[Any]], list[list[Any]]]:
    col_vals = {n: [_clean_cell(v) for v in df[n].tolist()] for n in names}
    rows = [[col_vals[n][i] for n in names] for i in range(len(df))]
    return col_vals, rows


def build_dataset_json(xpt_path: str, ds_name: str, mdv_oid: str,
                       meta_ref: str) -> tuple[dict[str, Any], int, int]:
    df, meta = _read_xpt(xpt_path)
    ds = ds_name.upper()
    names = list(meta.column_names)
    labels = dict(zip(meta.column_names, meta.column_labels))
    rtypes = dict(zip(meta.column_names, meta.readstat_variable_types))
    widths = dict(zip(meta.column_names,
                      getattr(meta, "variable_storage_width", [None] * len(names))))
    formats = _format_map(meta, names)
    keyseq = _derive_key_sequence(ds_name, names, mdv_oid)

    col_vals, rows = _canonical_rows(df, names)

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
            col["dataType"] = "double"
            fmt = (formats.get(n) or "").strip()
            if _is_temporal_format(fmt):
                col["displayFormat"] = fmt
        if n in keyseq:
            col["keySequence"] = keyseq[n]
        columns.append(col)

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
    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)
    validator_cls(schema).validate(doc)


def _write_ndjson(doc, path, ndjson_schema):
    """Dataset-NDJSON: line 1 = metadata (the doc without 'rows'), then one JSON
    array per row. Matches CORE's DatasetNDJSONReader."""
    meta = {k: v for k, v in doc.items() if k != "rows"}
    if ndjson_schema is not None:
        _validate(meta, ndjson_schema)  # raises on non-conformance
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(meta, ensure_ascii=False, allow_nan=False,
                            separators=(",", ":")) + "\n")
        for row in doc["rows"]:
            fh.write(json.dumps(row, ensure_ascii=False, allow_nan=False,
                                separators=(",", ":")) + "\n")
    os.chmod(path, 0o600)


def _read_dataset_output(path: str, ndjson: bool) -> dict[str, Any]:
    if not ndjson:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    with open(path, encoding="utf-8") as fh:
        first = fh.readline()
        if not first:
            raise RuntimeError(f"{path} is empty")
        doc = json.loads(first)
        doc["rows"] = [json.loads(line) for line in fh if line.strip()]
        return doc


def _prepare_output_dir(out_dir: str, expected_names: list[str], ndjson: bool) -> list[str]:
    """Make the generated output directory represent exactly this export.

    Dataset-JSON outputs are ignored, regenerated artifacts rather than a source
    of record.  Earlier runs could leave retired SDTM domains (or the alternate
    JSON/NDJSON format) beside the current export, which made the directory look
    like a mixed-version data package.  The selected format is therefore rebuilt
    as a clean set on every invocation; the other format is removed rather than
    being mistaken for current evidence.
    """
    os.makedirs(out_dir, exist_ok=True)
    os.chmod(out_dir, 0o700)
    expected = {str(name).lower() for name in expected_names}
    active_suffix = ".ndjson" if ndjson else ".json"
    removed: list[str] = []
    for suffix in (".json", ".ndjson"):
        for path in glob.glob(os.path.join(out_dir, f"*{suffix}")):
            stem = os.path.splitext(os.path.basename(path))[0].lower()
            if suffix != active_suffix or stem not in expected:
                os.remove(path)
                removed.append(path)
    return removed


def _reconcile_output(path: str, xpt_path: str, ndjson: bool) -> None:
    out_doc = _read_dataset_output(path, ndjson)
    df, meta = _read_xpt(xpt_path)
    source_names = list(meta.column_names)
    _, source_rows = _canonical_rows(df, source_names)
    output_names = [col["name"] for col in out_doc.get("columns", [])]
    if out_doc.get("records") != len(df):
        raise RuntimeError(
            f"{os.path.basename(path)} record mismatch: "
            f"{out_doc.get('records')} != {len(df)}"
        )
    if output_names != source_names:
        raise RuntimeError(f"{os.path.basename(path)} column order does not match source XPT")
    if out_doc.get("rows") != source_rows:
        raise RuntimeError(f"{os.path.basename(path)} row values do not reconcile to source XPT")


def convert_set(items, out_dir, mdv_oid, meta_ref, schema, ndjson_schema=None):
    removed = _prepare_output_dir(
        out_dir,
        [ds_name for _xpt_path, ds_name in items],
        ndjson=ndjson_schema is not None,
    )
    if removed:
        print(f"  [CLEAN] Removed {len(removed)} stale Dataset-JSON output(s) from {out_dir}.")
    results = []
    for xpt_path, ds_name in items:
        if not os.path.exists(xpt_path):
            results.append((ds_name, "MISSING", 0, 0, os.path.basename(xpt_path)))
            continue
        doc, nrec, ncol = build_dataset_json(xpt_path, ds_name, mdv_oid, meta_ref)
        _validate(doc, schema)  # raises on non-conformance
        if ndjson_schema is not None:
            out_path = os.path.join(out_dir, f"{ds_name.lower()}.ndjson")
            _write_ndjson(doc, out_path, ndjson_schema)
        else:
            out_path = os.path.join(out_dir, f"{ds_name.lower()}.json")
            with open(out_path, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, ensure_ascii=False, allow_nan=False,
                          separators=(",", ":"))
            os.chmod(out_path, 0o600)
        _reconcile_output(out_path, xpt_path, ndjson_schema is not None)
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
        adam_dir = os.path.join(ROOT, "04_analysis_datasets/adam")
        adam_names = ["adsl", "adex", "adcm", "adae", "adlb", "adrs", "adtte", "clinsite"]
        items = [(os.path.join(adam_dir, f"{n}_prod.xpt"), n) for n in adam_names]
        out = os.path.join(ROOT, "04_analysis_datasets/datasetjson", "adam")
        res = convert_set(items, out, ADAM_MDV, "../../03_metadata/define/define.xml",
                          schema, ndjson_schema)
        all_results += [("ADaM", *r) for r in res]

    if do_sdtm:
        sdtm_dir = os.path.join(
            ROOT, "08_submission_package", "m5", "datasets", "tropic", "tabulations", "sdtm", "datasets"
        )
        sdtm_names = []
        if os.path.isdir(sdtm_dir):
            sdtm_names = sorted(
                os.path.splitext(f)[0]
                for f in os.listdir(sdtm_dir) if f.endswith(".xpt")
            )
        if not sdtm_names:
            # Fail closed: an empty Module 5 SDTM folder must not report a green 0/0 export.
            raise SystemExit(
                "ERROR: no SDTM XPT inputs under "
                "08_submission_package/m5/datasets/tropic/tabulations/sdtm/datasets/ — refuse empty Dataset-JSON export"
            )
        items = [(os.path.join(sdtm_dir, f"{n}.xpt"), n) for n in sdtm_names]
        out = os.path.join(ROOT, "04_analysis_datasets/datasetjson", "sdtm")
        res = convert_set(items, out, SDTM_MDV, "../../03_metadata/define/define_sdtm.xml",
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
    if not all_results:
        print("ERROR: no datasets selected for export")
        return 1
    if ok == 0:
        print("ERROR: zero VALID Dataset-JSON exports (refusing green empty run)")
        return 1
    return 0 if ok == len(all_results) else 1


if __name__ == "__main__":
    sys.exit(main())
