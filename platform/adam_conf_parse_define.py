#!/usr/bin/env python3
"""adam_conf_parse_define.py — flatten define.xml into a metadata JSON for the ADaM
conformance checker (adam_conf_check.R). Namespace-agnostic (matches on local element
names) so it works on the ODM/def: namespaced Define-XML 2.1 without lxml/xml2.

Output: platform/adam_conf_define_meta.json
  { "datasets": { "<NAME>": {"structure": str,
                             "variables": [{name,label,type,length,mandatory,order,
                                            codelist,valuelist}]}},
    "codelists": { "<OID>": {"values": ["<CodedValue>", ...],
                             "external": bool, "dictionary": str|null} },
    "value_lists": { "<OID>": {"items": [{name,codelist,where_clauses,...}]} } }
"""
import json
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
DEFINE = os.path.join(HERE, "..", "03_metadata/define", "define.xml")
OUT = os.path.join(HERE, "adam_conf_define_meta.json")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def ln(tag):  # local name, drop namespace
    return tag.split("}")[-1]


def first_translated_text(el, preferred_lang="en"):
    """First descendant TranslatedText under `el`, preferring English."""
    fallback = None
    for child in el.iter():
        if ln(child.tag) == "TranslatedText" and child.text:
            text = child.text.strip()
            if child.get(XML_LANG) == preferred_lang:
                return text
            if fallback is None:
                fallback = text
    return fallback


def attr_local(el, want, default=None):
    """Namespace-agnostic attribute lookup by local name."""
    for key, val in el.attrib.items():
        if ln(key) == want:
            return val
    return default


def int_attr(el, name):
    val = el.get(name)
    if val in (None, ""):
        return None
    try:
        return int(val)
    except ValueError as exc:
        raise ValueError(f"{ln(el.tag)} has non-integer {name}={val!r}") from exc


def ref_attr(el, name):
    """Namespace-agnostic reference attribute, e.g. def:ItemOID."""
    return attr_local(el, name)


def map_type(dt):
    dt = (dt or "").lower()
    if dt in ("integer", "float"):
        return "numeric"
    return "character"  # text, datetime, date, partialDate, etc. land as character in XPT


def parse_define(path):
    tree = ET.parse(path)
    root = tree.getroot()
    errors = []

    # ---- ItemDefs: OID -> {name,label,type,length,codelist,valuelist}
    items = {}
    for el in root.iter():
        if ln(el.tag) != "ItemDef":
            continue
        oid = el.get("OID")
        if not oid:
            errors.append("ItemDef without OID")
            continue
        if oid in items:
            errors.append(f"Duplicate ItemDef OID {oid}")
            continue
        label, codelist, valuelist = None, None, None
        for ch in el:
            t = ln(ch.tag)
            if t == "Description":
                label = first_translated_text(ch)
            elif t == "CodeListRef":
                codelist = ch.get("CodeListOID")
            elif t == "ValueListRef":
                valuelist = ch.get("ValueListOID")
        items[oid] = {
            "oid": oid,
            "name": el.get("Name"),
            "label": label,
            "type": map_type(el.get("DataType")),
            "length": int_attr(el, "Length"),
            "codelist": codelist,
            "valuelist": valuelist,
        }
        if codelist and not codelist.strip():
            errors.append(f"{oid} has blank CodeListOID")
        if valuelist and not valuelist.strip():
            errors.append(f"{oid} has blank ValueListOID")

    # ---- CodeLists: OID -> explicit enumerations or external dictionaries
    codelists = {}
    for el in root.iter():
        if ln(el.tag) != "CodeList":
            continue
        oid = el.get("OID")
        if not oid:
            errors.append("CodeList without OID")
            continue
        if oid in codelists:
            errors.append(f"Duplicate CodeList OID {oid}")
            continue
        vals = []
        external = None
        for ch in el.iter():
            if ln(ch.tag) in ("CodeListItem", "EnumeratedItem"):
                cv = ch.get("CodedValue")
                if cv is not None:
                    vals.append(cv)
            elif ln(ch.tag) == "ExternalCodeList":
                external = {
                    "dictionary": ch.get("Dictionary") or ch.get("Name"),
                    "version": ch.get("Version"),
                    "href": ref_attr(ch, "href"),
                }
        codelists[oid] = {
            "values": vals,
            "external": external is not None,
            "dictionary": None if external is None else external.get("dictionary"),
            "version": None if external is None else external.get("version"),
            "href": None if external is None else external.get("href"),
        }

    for oid, item in items.items():
        cl = item.get("codelist")
        if cl and cl not in codelists:
            errors.append(f"{oid} references missing CodeList {cl}")

    # ---- WhereClauseDefs: OID -> condition list
    where_clauses = {}
    for el in root.iter():
        if ln(el.tag) != "WhereClauseDef":
            continue
        oid = el.get("OID")
        if not oid:
            errors.append("WhereClauseDef without OID")
            continue
        if oid in where_clauses:
            errors.append(f"Duplicate WhereClauseDef OID {oid}")
            continue
        conditions = []
        for rc in el:
            if ln(rc.tag) != "RangeCheck":
                continue
            item_oid = ref_attr(rc, "ItemOID")
            values = [cv.text.strip() for cv in rc if ln(cv.tag) == "CheckValue" and cv.text]
            conditions.append({
                "item_oid": item_oid,
                "variable": items.get(item_oid, {}).get("name"),
                "comparator": rc.get("Comparator"),
                "values": values,
            })
            if item_oid not in items:
                errors.append(f"{oid} RangeCheck references missing ItemDef {item_oid}")
        where_clauses[oid] = conditions

    # ---- ValueListDefs: OID -> resolved conditional ItemRefs
    value_lists = {}
    for el in root.iter():
        if ln(el.tag) != "ValueListDef":
            continue
        oid = el.get("OID")
        if not oid:
            errors.append("ValueListDef without OID")
            continue
        if oid in value_lists:
            errors.append(f"Duplicate ValueListDef OID {oid}")
            continue
        vl_items = []
        for item_ref in el:
            if ln(item_ref.tag) != "ItemRef":
                continue
            item_oid = item_ref.get("ItemOID")
            item = items.get(item_oid)
            if item is None:
                errors.append(f"{oid} ItemRef references missing ItemDef {item_oid}")
                continue
            wc_oids = [
                ch.get("WhereClauseOID") for ch in item_ref
                if ln(ch.tag) == "WhereClauseRef" and ch.get("WhereClauseOID")
            ]
            for wc_oid in wc_oids:
                if wc_oid not in where_clauses:
                    errors.append(f"{oid} ItemRef {item_oid} references missing WhereClause {wc_oid}")
            vl_items.append({
                **item,
                "mandatory": (item_ref.get("Mandatory") == "Yes"),
                "method": item_ref.get("MethodOID"),
                "where_clause_oids": wc_oids,
                "where_clauses": [where_clauses[wc_oid] for wc_oid in wc_oids
                                  if wc_oid in where_clauses],
            })
        value_lists[oid] = {"items": vl_items}

    for oid, item in items.items():
        vl = item.get("valuelist")
        if vl and vl not in value_lists:
            errors.append(f"{oid} references missing ValueList {vl}")

    # ---- ItemGroupDefs: dataset name -> ordered resolved variables
    datasets = {}
    for el in root.iter():
        if ln(el.tag) != "ItemGroupDef":
            continue
        name = el.get("Name")
        if not name:
            errors.append("ItemGroupDef without Name")
            continue
        if name in datasets:
            errors.append(f"Duplicate ItemGroupDef Name {name}")
            continue
        structure = attr_local(el, "Structure", "")
        vars_ = []
        for ch in el:
            if ln(ch.tag) != "ItemRef":
                continue
            item_oid = ch.get("ItemOID")
            d = items.get(item_oid)
            if not d:
                errors.append(f"{name} ItemRef references missing ItemDef {item_oid}")
                continue
            vars_.append({**d,
                          "mandatory": (ch.get("Mandatory") == "Yes"),
                          "order": int_attr(ch, "OrderNumber")})
        datasets[name] = {"structure": structure, "variables": vars_}

    if errors:
        raise ValueError("define.xml metadata parse failed:\n- " + "\n- ".join(errors))
    nv = sum(len(d["variables"]) for d in datasets.values())
    if not datasets or nv == 0:
        raise ValueError("define.xml metadata parse failed: no datasets/variables parsed")
    return {"datasets": datasets, "codelists": codelists, "value_lists": value_lists}


def main():
    meta = parse_define(DEFINE)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    nv = sum(len(d["variables"]) for d in meta["datasets"].values())
    print(f"[parse] {len(meta['datasets'])} datasets, {nv} variables, "
          f"{len(meta['codelists'])} codelists -> {OUT}")


if __name__ == "__main__":
    sys.exit(main())
