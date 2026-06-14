#!/usr/bin/env python3
"""adam_conf_parse_define.py — flatten define.xml into a metadata JSON for the ADaM
conformance checker (adam_conf_check.R). Namespace-agnostic (matches on local element
names) so it works on the ODM/def: namespaced Define-XML 2.1 without lxml/xml2.

Output: 06_telemetry/adam_conf_define_meta.json
  { "datasets": { "<NAME>": {"structure": str,
                             "variables": [{name,label,type,length,mandatory,order,codelist}]}},
    "codelists": { "<OID>": ["<CodedValue>", ...] } }
"""
import json, os, sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
DEFINE = os.path.join(HERE, "..", "07_define_xml", "define.xml")
OUT = os.path.join(HERE, "adam_conf_define_meta.json")


def ln(tag):  # local name, drop namespace
    return tag.split("}")[-1]


def first_text(el, want):
    """First descendant TranslatedText under an element named `want` (e.g. Description/Decode)."""
    for child in el.iter():
        if ln(child.tag) == "TranslatedText" and child.text:
            return child.text.strip()
    return None


def map_type(dt):
    dt = (dt or "").lower()
    if dt in ("integer", "float"):
        return "numeric"
    return "character"  # text, datetime, date, partialDate, etc. land as character in XPT


def main():
    tree = ET.parse(DEFINE)
    root = tree.getroot()

    # ---- ItemDefs: OID -> {name,label,type,length,codelist}
    items = {}
    for el in root.iter():
        if ln(el.tag) != "ItemDef":
            continue
        oid = el.get("OID")
        label, codelist = None, None
        for ch in el:
            t = ln(ch.tag)
            if t == "Description":
                label = first_text(ch, "Description")
            elif t == "CodeListRef":
                codelist = ch.get("CodeListOID")
        items[oid] = {
            "name": el.get("Name"),
            "label": label,
            "type": map_type(el.get("DataType")),
            "length": int(el.get("Length")) if el.get("Length") else None,
            "codelist": codelist,
        }

    # ---- CodeLists: OID -> [coded values]
    codelists = {}
    for el in root.iter():
        if ln(el.tag) != "CodeList":
            continue
        vals = []
        for ch in el.iter():
            if ln(ch.tag) in ("CodeListItem", "EnumeratedItem"):
                cv = ch.get("CodedValue")
                if cv is not None:
                    vals.append(cv)
        codelists[el.get("OID")] = vals

    # ---- ItemGroupDefs: dataset name -> ordered resolved variables
    datasets = {}
    for el in root.iter():
        if ln(el.tag) != "ItemGroupDef":
            continue
        name = el.get("Name")
        structure = el.get("{http://www.cdisc.org/ns/def/v2.1}Structure") \
            or el.get("def:Structure") or ""
        if not structure:  # namespace-agnostic fallback
            for k, v in el.attrib.items():
                if ln(k) == "Structure":
                    structure = v
        vars_ = []
        for ch in el:
            if ln(ch.tag) != "ItemRef":
                continue
            d = items.get(ch.get("ItemOID"))
            if not d:
                continue
            vars_.append({**d,
                          "mandatory": (ch.get("Mandatory") == "Yes"),
                          "order": int(ch.get("OrderNumber")) if ch.get("OrderNumber") else None})
        datasets[name] = {"structure": structure, "variables": vars_}

    meta = {"datasets": datasets, "codelists": codelists}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    nv = sum(len(d["variables"]) for d in datasets.values())
    print(f"[parse] {len(datasets)} datasets, {nv} variables, {len(codelists)} codelists -> {OUT}")


if __name__ == "__main__":
    sys.exit(main())
