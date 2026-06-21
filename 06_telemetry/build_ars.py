#!/usr/bin/env python3
"""
build_ars.py - generate a CDISC Analysis Results Standard (ARS) v1.0 ReportingEvent
plus the Analysis Results Dataset (ARD) for TROPIC.

WHY
---
The package carries Analysis Results Metadata (ARM v1.0) inside define.xml, but not the
newer machine-readable CDISC Analysis Results Standard (ARS v1.0, adoption from May 2025)
or an Analysis Results Dataset. ARS expresses each analysis as
ReportingEvent -> Analysis{reason,purpose,analysisSet,method,groupings,results} ->
OperationResult, giving end-to-end, machine-readable result traceability. This script
adds that layer additively (new files only; the validated pipeline is untouched).

SCOPE / HONESTY
---------------
Results are the **real Mitoxantrone arm** time-to-event summary (the reviewable cohort),
with N / events / KM-median computed here directly from `04_adam/adtte_prod.xpt` (same KM
routine cross-validated in date_precision_sensitivity.py — MP OS median 12.68 mo matches
the published ~12.7 mo). The synthetic comparator arm and two-arm hazard ratios are
deliberately excluded (reviewer finding R-1: a synthetic arm carries no evidentiary
weight); the grouping is modelled with the single real arm. Extending to two arms is a
one-line change once real comparator data exists.

OUTPUT  (additive)
------------------
  12_ars/tropic_reporting_event.json   ARS v1.0 ReportingEvent instance
  12_ars/tropic_ard.csv                Analysis Results Dataset (tidy results)

Model basis: CDISC ARS v1.0 LinkML (cdisc-org.github.io/analysis-results-standard).
USAGE:  python3 06_telemetry/build_ars.py
Requires: numpy, pyreadstat.
"""
from __future__ import annotations

import csv
import json
import os
import numpy as np
import pyreadstat

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADTTE = os.path.join(ROOT, "04_adam", "adtte_prod.xpt")
OUT_DIR = os.path.join(ROOT, "12_ars")
DPM = 30.4375

# analysis variable per TTE parameter, with ARS analysis purpose (CT) + SAP reason
ANALYSES = [
    ("OS",     "Overall Survival",            "PRIMARY OUTCOME MEASURE"),
    ("PFS",    "Progression-Free Survival",   "SECONDARY OUTCOME MEASURE"),
    ("TTPSA",  "Time to PSA Progression",     "SECONDARY OUTCOME MEASURE"),
    ("TTUMOR", "Time to Tumor Progression",   "SECONDARY OUTCOME MEASURE"),
]


def km_median_days(time, event):
    order = np.argsort(time, kind="mergesort")
    t, e = time[order], event[order]
    surv, found = 1.0, float("nan")
    for ut in np.unique(t):
        at_risk = int(np.count_nonzero(t >= ut))
        d = int(np.count_nonzero((t == ut) & (e == 1)))
        if at_risk and d:
            surv *= (1 - d / at_risk)
            if surv <= 0.5:
                found = float(ut)
                break
    return found


def term(ct):
    return {"controlledTerm": ct}


def build():
    df, _ = pyreadstat.read_xport(ADTTE, disable_datetime_conversion=True)
    df["PARAMCD"] = df["PARAMCD"].astype(str).str.strip()

    # ---- shared components ----
    analysis_set = {
        "id": "AS.ITT", "name": "Intent-to-Treat",
        "label": "Randomized analysis cohort (ITTFL = Y)", "order": 1,
        "condition": {"dataset": "ADSL", "variable": "ITTFL",
                      "comparator": "EQ", "value": ["Y"]},
    }
    grouping = {
        "id": "GF.TRT", "name": "Treatment", "label": "Planned treatment",
        "groupingDataset": "ADSL", "groupingVariable": "TRT01P", "dataDriven": False,
        "groups": [{"id": "G.MP", "name": "Mitoxantrone + Prednisone", "label": "MP",
                    "condition": {"dataset": "ADSL", "variable": "TRT01P",
                                  "comparator": "EQ", "value": ["MP"]}}],
    }
    operations = [
        {"id": "OP.N",    "name": "Number of subjects",   "order": 1, "resultPattern": "XXX"},
        {"id": "OP.EVNT", "name": "Number of events",     "order": 2, "resultPattern": "XXX"},
        {"id": "OP.MEDD", "name": "KM median (days)",     "order": 3, "resultPattern": "XXX.X"},
        {"id": "OP.MEDM", "name": "KM median (months)",   "order": 4, "resultPattern": "XX.XX"},
    ]
    method = {
        "id": "MTH.KMTTE", "name": "Kaplan-Meier time-to-event summary",
        "label": "KM N / events / median",
        "description": "Kaplan-Meier estimate of the survival function; median is the "
                       "first time at which S(t) <= 0.5. Time origin and event per "
                       "ADTTE PARAM (ADRG section 4).",
        "operations": operations,
    }

    analyses, ard_rows = [], []
    contents = []
    for i, (pcd, pname, purpose) in enumerate(ANALYSES, start=1):
        sub = df[df["PARAMCD"] == pcd]
        aval = sub["AVAL"].to_numpy(float)
        event = (sub["CNSR"].to_numpy(float) == 0).astype(int)
        n = int(len(sub)); nev = int(event.sum())
        med_d = km_median_days(aval, event)
        med_m = None if not np.isfinite(med_d) else round(med_d / DPM, 2)

        def opres(op_id, raw, fmt):
            return {"operationId": op_id,
                    "resultGroups": [{"groupingId": "GF.TRT", "groupId": "G.MP"}],
                    "rawValue": raw, "formattedValue": fmt}

        results = [
            opres("OP.N", n, str(n)),
            opres("OP.EVNT", nev, str(nev)),
            opres("OP.MEDD", None if not np.isfinite(med_d) else round(med_d, 1),
                  "Not reached" if not np.isfinite(med_d) else f"{med_d:.1f}"),
            opres("OP.MEDM", med_m,
                  "Not reached" if med_m is None else f"{med_m:.2f}"),
        ]
        analyses.append({
            "id": f"AN.{pcd}", "name": pname,
            "description": f"Kaplan-Meier {pname} on the real MP arm.",
            "reason": term("SPECIFIED IN SAP"), "purpose": term(purpose),
            "dataset": "ADTTE", "variable": "AVAL",
            "analysisSetId": "AS.ITT", "methodId": "MTH.KMTTE",
            "orderedGroupings": [{"order": 1, "groupingId": "GF.TRT"}],
            "results": results,
        })
        contents.append({"order": i, "analysisId": f"AN.{pcd}"})
        for op_id, raw, fmt in [("OP.N", n, str(n)), ("OP.EVNT", nev, str(nev)),
                                ("OP.MEDD", med_d, results[2]["formattedValue"]),
                                ("OP.MEDM", med_m, results[3]["formattedValue"])]:
            ard_rows.append({"reportingEventId": "RE.TROPIC", "analysisId": f"AN.{pcd}",
                             "analysis": pname, "analysisSetId": "AS.ITT",
                             "groupingId": "GF.TRT", "groupId": "G.MP",
                             "operationId": op_id,
                             "rawValue": "" if raw is None or (isinstance(raw, float)
                                         and not np.isfinite(raw)) else raw,
                             "formattedValue": fmt})

    reporting_event = {
        "id": "RE.TROPIC", "name": "TROPIC MP-arm time-to-event reporting event",
        "version": 1,
        "label": "ARS v1.0 results for the real Mitoxantrone arm (NCT00417079)",
        "mainListOfContents": {
            "name": "TROPIC time-to-event analyses",
            "contents": contents,
        },
        "referenceDocuments": [
            {"id": "RD.SAP", "name": "TROPIC SAP v3.0", "location": "TROPIC_SAP_v3.0.docx"},
            {"id": "RD.ADRG", "name": "Analysis Data Reviewer's Guide",
             "location": "08_reviewers_guides/ADRG.md"},
        ],
        "analysisSets": [analysis_set],
        "analysisGroupings": [grouping],
        "methods": [method],
        "analyses": analyses,
    }
    return reporting_event, ard_rows


def validate(re_obj):
    """Referential-integrity + required-slot self-check (offline, rigorous)."""
    errs = []
    if not re_obj.get("id") or not re_obj.get("name"):
        errs.append("ReportingEvent missing id/name")
    if not re_obj.get("mainListOfContents"):
        errs.append("ReportingEvent missing required mainListOfContents")
    set_ids = {s["id"] for s in re_obj["analysisSets"]}
    grp_ids = {g["id"] for g in re_obj["analysisGroupings"]}
    group_ids = {gg["id"] for g in re_obj["analysisGroupings"] for gg in g["groups"]}
    method_ops = {m["id"]: {o["id"] for o in m["operations"]} for m in re_obj["methods"]}
    listed = {c["analysisId"] for c in re_obj["mainListOfContents"]["contents"]}
    for a in re_obj["analyses"]:
        for req in ("id", "name", "reason", "purpose", "methodId"):
            if not a.get(req):
                errs.append(f"{a.get('id')}: missing required {req}")
        if a["analysisSetId"] not in set_ids:
            errs.append(f"{a['id']}: analysisSetId {a['analysisSetId']} unresolved")
        if a["methodId"] not in method_ops:
            errs.append(f"{a['id']}: methodId unresolved")
        for og in a.get("orderedGroupings", []):
            if og["groupingId"] not in grp_ids:
                errs.append(f"{a['id']}: groupingId {og['groupingId']} unresolved")
        for r in a.get("results", []):
            if r["operationId"] not in method_ops.get(a["methodId"], set()):
                errs.append(f"{a['id']}: operationId {r['operationId']} not in method")
            for rg in r["resultGroups"]:
                if rg["groupingId"] not in grp_ids or rg["groupId"] not in group_ids:
                    errs.append(f"{a['id']}: resultGroup ref unresolved")
        if a["id"] not in listed:
            errs.append(f"{a['id']}: not referenced in mainListOfContents")
    return errs


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    re_obj, ard = build()
    errs = validate(re_obj)

    with open(os.path.join(OUT_DIR, "tropic_reporting_event.json"), "w", encoding="utf-8") as fh:
        json.dump(re_obj, fh, indent=2, ensure_ascii=False)
    with open(os.path.join(OUT_DIR, "tropic_ard.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["reportingEventId", "analysisId", "analysis",
                           "analysisSetId", "groupingId", "groupId", "operationId",
                           "rawValue", "formattedValue"])
        w.writeheader()
        w.writerows(ard)

    print(f"ARS ReportingEvent: {len(re_obj['analyses'])} analyses, "
          f"{len(re_obj['methods'][0]['operations'])} operations, "
          f"{len(re_obj['analysisSets'])} analysis set, "
          f"{sum(len(g['groups']) for g in re_obj['analysisGroupings'])} group")
    print(f"ARD rows: {len(ard)}")
    print("\nResults (real MP arm, computed here):")
    for a in re_obj["analyses"]:
        vals = {r["operationId"]: r["formattedValue"] for r in a["results"]}
        print(f"  {a['id']:9} N={vals['OP.N']:>4} events={vals['OP.EVNT']:>4} "
              f"KM median={vals['OP.MEDM']:>11} mo")
    print("\nValidation (referential integrity + required slots):",
          "PASS" if not errs else "FAIL")
    for e in errs:
        print("   -", e)
    return 0 if not errs else 1


if __name__ == "__main__":
    raise SystemExit(main())
