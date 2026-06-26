#!/usr/bin/env python3
"""Compare Define-XML metadata with the actual sequence XPORT datasets."""

from __future__ import annotations

import csv
from pathlib import Path
import xml.etree.ElementTree as ET

import pyreadstat


ROOT = Path(__file__).resolve().parents[1]
ODM = "{http://www.cdisc.org/ns/odm/v1.3}"
DEF = "{http://www.cdisc.org/ns/def/v2.1}"


def define_model(path: Path):
    root = ET.parse(path).getroot()
    itemdefs = {x.get("OID"): x for x in root.iter(ODM + "ItemDef")}
    result = {}
    for group in root.iter(ODM + "ItemGroupDef"):
        name = (group.get("Name") or "").upper()
        refs = sorted(group.findall(ODM + "ItemRef"), key=lambda x: int(x.get("OrderNumber", "0")))
        variables = []
        derived_no_method = []
        for ref in refs:
            item = itemdefs.get(ref.get("ItemOID"))
            if item is None:
                continue
            var = item.get("Name")
            variables.append(var)
            origin = item.find(DEF + "Origin")
            if origin is not None and origin.get("Type") == "Derived" and not ref.get("MethodOID"):
                derived_no_method.append(var)
        if variables:
            result[name] = {"variables": variables, "derived_no_method": derived_no_method}
    return result


def compare(standard, define_path, data_dir, suffix=".xpt"):
    model = define_model(define_path)
    actual_files = {p.stem.upper(): p for p in Path(data_dir).glob(f"*{suffix}")}
    rows = []
    for name in sorted(set(model) | set(actual_files)):
        expected = model.get(name, {}).get("variables", [])
        actual = []
        labels_missing = []
        if name in actual_files:
            _, meta = pyreadstat.read_xport(str(actual_files[name]), metadataonly=True)
            actual = list(meta.column_names)
            labels = meta.column_names_to_labels or {}
            labels_missing = [v for v in actual if not labels.get(v)]
        rows.append({
            "standard": standard,
            "dataset": name,
            "define_present": "YES" if name in model else "NO",
            "data_present": "YES" if name in actual_files else "NO",
            "define_variables": len(expected),
            "data_variables": len(actual),
            "missing_from_data": "|".join(v for v in expected if v not in actual),
            "not_in_define": "|".join(v for v in actual if v not in expected),
            "order_match": "YES" if expected == actual and expected else "NO",
            "unlabelled_data_variables": "|".join(labels_missing),
            "derived_variables_without_method": "|".join(model.get(name, {}).get("derived_no_method", [])),
        })
    return rows


rows = []
rows += compare("ADaM", ROOT / "07_define_xml/define.xml", ROOT / "04_adam", "_prod.xpt")
# normalize ADaM stems such as ADSL_PROD after the initial comparison
for row in rows:
    if row["standard"] == "ADaM" and row["dataset"].endswith("_PROD"):
        row["dataset"] = row["dataset"].removesuffix("_PROD")

# Rebuild ADaM correctly against normalized names.
adam_model = define_model(ROOT / "07_define_xml/define.xml")
adam_actual = {p.stem.removesuffix("_prod").upper(): p for p in (ROOT / "04_adam").glob("*_prod.xpt")}
rows = []
for name in sorted(set(adam_model) | set(adam_actual)):
    exp = adam_model.get(name, {}).get("variables", [])
    act, missing_labels = [], []
    if name in adam_actual:
        _, meta = pyreadstat.read_xport(str(adam_actual[name]), metadataonly=True)
        act = list(meta.column_names)
        labels = meta.column_names_to_labels or {}
        missing_labels = [v for v in act if not labels.get(v)]
    rows.append({
        "standard": "ADaM", "dataset": name,
        "define_present": "YES" if name in adam_model else "NO",
        "data_present": "YES" if name in adam_actual else "NO",
        "define_variables": len(exp), "data_variables": len(act),
        "missing_from_data": "|".join(v for v in exp if v not in act),
        "not_in_define": "|".join(v for v in act if v not in exp),
        "order_match": "YES" if exp == act and exp else "NO",
        "unlabelled_data_variables": "|".join(missing_labels),
        "derived_variables_without_method": "|".join(adam_model.get(name, {}).get("derived_no_method", [])),
    })

rows += compare(
    "SDTM", ROOT / "07_define_xml/define_sdtm.xml",
    ROOT / "11_ectd/0000/m5/datasets/tropic/tabulations/sdtm/datasets"
)

out = ROOT / "audit/metadata_data_drift.csv"
with out.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print(f"Wrote {len(rows)} dataset comparisons")
