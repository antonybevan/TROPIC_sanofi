#!/usr/bin/env python3
"""CT cross-validation: verify the ADaM spec Codelists against authoritative CDISC CT.

Prototype of CDISC-Library-backed cross-validation (see the standards-currency review). The
data-level CORE run checks the produced *datasets* against CT; nothing checks the hand-authored
`00_specifications/ADaM_spec.xlsx` 'Codelists' sheet -- the source of truth that drives
define.xml -- against the authoritative Controlled Terminology. This closes that gap.

Authoritative CT is sourced from the **CDISC Library API** when `CDISC_LIBRARY_API_KEY` is set
(live GET /mdr/ct/packages/{package}); otherwise it falls back to the CORE engine's pinned,
offline cache (`.core_run/engine/resources/cache/{package}-{version}.pkl`) -- the same package
the Library produced -- so the check is reproducible and runs without network/credentials.

Findings:
  - VIOLATION (fails the build): a codelist confidently linked to a NON-extensible CDISC
    codelist (by NCI C-code or exact name) carries a submission value that is not a valid CDISC
    term. This is a real spec-authoring / define.xml conformance error.
  - traceability-gap (warning): a spec codelist/term carries no NCI code, so there is no
    machine-checkable link to CDISC CT (here we infer the link by value-set).
  - sponsor-defined (info): the codelist does not correspond to any CDISC CT codelist (expected
    for study-specific lists such as treatment or PARAMCD).

Usage:
  python3 06_telemetry/ct_cross_validation.py [--version 2026-03-27]
                                              [--packages adamct,sdtmct]
"""
import argparse
import json
import os
import pickle
import sys
import urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SPEC = os.path.join(ROOT, "00_specifications", "ADaM_spec.xlsx")
CACHE = os.path.join(ROOT, ".core_run", "engine", "resources", "cache")
OUT = os.path.join(HERE, "conformance", "ct_cross_validation.json")
LIBRARY = "https://api.library.cdisc.org/mdr/ct/packages"

DEFAULT_VERSION = "2026-03-27"
DEFAULT_PACKAGES = ["sdtmct", "adamct"]


# --------------------------------------------------------------------------- CT source

def load_ct(packages, version):
    """Return (codelists, source). Live CDISC Library API if a key is present, else the
    pinned CORE offline cache. Both yield the same {conceptId,name,extensible,terms[]} shape."""
    api_key = os.environ.get("CDISC_LIBRARY_API_KEY")
    codelists = []
    if api_key:
        for pkg in packages:
            url = f"{LIBRARY}/{pkg}-{version}"
            req = urllib.request.Request(url, headers={"api-key": api_key,
                                                       "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                codelists += json.load(r).get("codelists", [])
        return codelists, f"cdisc_library_api ({LIBRARY})"
    for pkg in packages:
        path = os.path.join(CACHE, f"{pkg}-{version}.pkl")
        if not os.path.exists(path):
            sys.exit(f"No CDISC_LIBRARY_API_KEY and no offline cache at {path}. "
                     f"Set the key or run 06_telemetry/run_core_conformance.sh once to seed it.")
        with open(path, "rb") as f:
            codelists += pickle.load(f).get("codelists", [])
    return codelists, f"core_offline_cache ({os.path.relpath(CACHE, ROOT)})"


def index_ct(codelists):
    """Build lookup indices over the authoritative codelists."""
    by_ccode, by_name, value_sets = {}, {}, []
    for cl in codelists:
        values = {t["submissionValue"] for t in cl.get("terms", [])}
        rec = {"conceptId": cl.get("conceptId"), "name": cl.get("name"),
               "extensible": bool(cl.get("extensible")), "values": values,
               "decodes": {t["submissionValue"]: t.get("preferredTerm") for t in cl.get("terms", [])}}
        by_ccode[rec["conceptId"]] = rec
        by_name[_norm(rec["name"])] = rec
        value_sets.append(rec)
    return by_ccode, by_name, value_sets


def _norm(name):
    return (name or "").strip().lower().replace(" codelist", "").replace("codelist", "").strip()


def _is_numeric(v):
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


# --------------------------------------------------------------------------- spec source

def load_spec_codelists(path):
    import openpyxl
    ws = openpyxl.load_workbook(path, read_only=True)["Codelists"]
    rows = list(ws.iter_rows(values_only=True))
    hdr = {name: i for i, name in enumerate(rows[0])}
    col = lambda r, name: r[hdr[name]] if name in hdr and hdr[name] < len(r) else None
    out = {}
    for r in rows[1:]:
        cid = col(r, "ID")
        if cid is None:
            continue
        cl = out.setdefault(cid, {"id": cid, "name": col(r, "Name"),
                                  "nci_ccode": col(r, "NCI Codelist Code"), "terms": []})
        cl["terms"].append({"value": str(col(r, "Term")),
                            "nci_term": col(r, "NCI Term Code"),
                            "decode": col(r, "Decoded Value")})
    return out


# --------------------------------------------------------------------------- linking + validation

def link(spec_cl, by_ccode, by_name, value_sets):
    """Link a spec codelist to a CDISC codelist. Returns (ct_rec, method, confidence, candidates).
    A unique high-confidence link sets ct_rec; multiple value-set matches are returned as
    'ambiguous' candidates (the spec needs an NCI code to disambiguate); none is sponsor-defined."""
    if spec_cl["nci_ccode"] and spec_cl["nci_ccode"] in by_ccode:
        return by_ccode[spec_cl["nci_ccode"]], "nci_ccode", "high", []
    nm = _norm(spec_cl["name"])
    if nm and nm in by_name:
        return by_name[nm], "name", "high", []
    spec_vals = {t["value"] for t in spec_cl["terms"]}
    # Skip value-set inference for all-numeric lists: by ADaM convention these are sponsor
    # numeric codes (e.g. TRT01PN 1/2, CNSR 0/1), not CT submission values, and tiny numeric
    # sets spuriously match large numeric-result CT codelists.
    if len(spec_vals) >= 2 and not all(_is_numeric(v) for v in spec_vals):
        supersets = sorted((c for c in value_sets if spec_vals <= c["values"]),
                           key=lambda c: len(c["values"]))
        if len(supersets) == 1:
            return supersets[0], "value_set", "inferred", []
        if len(supersets) >= 2:
            return None, "value_set", "ambiguous", supersets[:5]
    return None, None, None, []


def validate(spec, by_ccode, by_name, value_sets):
    results, violations, traceability_gaps, sponsor, ambiguous = [], 0, 0, 0, 0
    for cl in spec.values():
        ct, method, confidence, candidates = link(cl, by_ccode, by_name, value_sets)
        rec = {"id": cl["id"], "name": cl["name"], "n_terms": len(cl["terms"])}
        if ct is None and confidence == "ambiguous":
            rec["classification"] = "ambiguous-cdisc"
            rec["candidates"] = [{"conceptId": c["conceptId"], "name": c["name"]} for c in candidates]
            rec["note"] = ("matches multiple CDISC codelists by value-set; add the NCI Codelist "
                           "Code to the spec to disambiguate and enable traceability")
            ambiguous += 1
            traceability_gaps += 1
            results.append(rec)
            continue
        if ct is None:
            rec["classification"] = "sponsor-defined"
            rec["note"] = "no corresponding CDISC CT codelist (study-specific; expected)"
            sponsor += 1
            results.append(rec)
            continue
        rec.update({"classification": "cdisc-linked", "linked_to": ct["conceptId"],
                    "linked_name": ct["name"], "link_method": method,
                    "link_confidence": confidence, "extensible": ct["extensible"]})
        bad = [t["value"] for t in cl["terms"] if t["value"] not in ct["values"]]
        decode_warn = [t["value"] for t in cl["terms"]
                       if t["value"] in ct["values"] and t["decode"]
                       and _norm(t["decode"]) != _norm(ct["decodes"].get(t["value"]))]
        if cl["nci_ccode"] is None:
            rec["traceability"] = f"spec carries no NCI Codelist Code; CDISC code is {ct['conceptId']}"
            traceability_gaps += 1
        if bad:
            if not ct["extensible"] and confidence == "high":
                rec["status"] = "VIOLATION"
                rec["invalid_terms"] = bad
                violations += 1
            else:
                rec["status"] = "review"
                rec["non_cdisc_terms"] = bad
                rec["note"] = ("extensible codelist (sponsor extension allowed)" if ct["extensible"]
                               else "inferred link; verify before treating as conformance error")
        else:
            rec["status"] = "conformant"
        if decode_warn:
            rec["decode_mismatches"] = decode_warn
        results.append(rec)
    summary = {"total": len(spec), "cdisc_linked": len(spec) - sponsor - ambiguous,
               "ambiguous_cdisc": ambiguous, "sponsor_defined": sponsor,
               "violations": violations, "traceability_gaps": traceability_gaps}
    return results, summary


# --------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="Cross-validate spec CT against CDISC CT.")
    ap.add_argument("--version", default=DEFAULT_VERSION)
    ap.add_argument("--packages", default=",".join(DEFAULT_PACKAGES))
    args = ap.parse_args()
    packages = [p.strip() for p in args.packages.split(",") if p.strip()]

    codelists, source = load_ct(packages, args.version)
    by_ccode, by_name, value_sets = index_ct(codelists)
    spec = load_spec_codelists(SPEC)
    results, summary = validate(spec, by_ccode, by_name, value_sets)

    report = {"generated": datetime.now().isoformat(), "ct_version": args.version,
              "ct_packages": packages, "ct_source": source, "summary": summary,
              "codelists": results}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"CT cross-validation -- spec vs CDISC CT {args.version} ({source})")
    for r in results:
        tag = {"conformant": "OK", "VIOLATION": "FAIL", "review": "REVIEW",
               "sponsor-defined": "sponsor", "ambiguous-cdisc": "ambig"}.get(
                   r.get("status", r["classification"]), "-")
        link = f" -> {r.get('linked_to','')} {r.get('linked_name','')} [{r.get('link_method','')}]" if r.get("linked_to") else ""
        print(f"  [{tag:>7}] {r['id']:<12} ({r['n_terms']} terms){link}")
        if r.get("invalid_terms"):  print(f"            invalid CDISC terms: {r['invalid_terms']}")
        if r.get("candidates"):     print(f"            candidates: " +
                                          ", ".join(f"{c['conceptId']} {c['name']}" for c in r["candidates"]))
        if r.get("traceability"):   print(f"            traceability: {r['traceability']}")
    s = summary
    print(f"\nsummary: {s['total']} codelists | {s['cdisc_linked']} CDISC-linked | "
          f"{s['ambiguous_cdisc']} ambiguous | {s['sponsor_defined']} sponsor-defined | "
          f"{s['traceability_gaps']} traceability gaps | {s['violations']} violations")
    print(f"report: {os.path.relpath(OUT, ROOT)}")
    sys.exit(1 if summary["violations"] else 0)


if __name__ == "__main__":
    main()
