#!/usr/bin/env python3
"""
build_usdm.py - generate a CDISC/TransCelerate USDM (Digital Data Flow) machine-readable
study definition for TROPIC.

WHY
---
The package has a protocol PDF, SAP, and study_config.yaml, but no machine-readable
study definition. USDM (the front end of CDISC 360i / DDF) is the emerging standard for
exactly that. This adds a USDM Wrapper JSON additively (new file; pipeline untouched).

HOW / VALIDATION
----------------
Built directly against the official `usdm_model` Pydantic classes (`pip install usdm`).
Construction *is* validation: every entity is instantiated through the model, so a file
that writes successfully is structurally USDM-conformant (required slots, instanceType
literals, reference types). Facts sourced from study_config.yaml + the public TROPIC
protocol (NCT00417079 / EFC6193 / XRP6258).

OUTPUT:  13_usdm/tropic_usdm.json
USAGE:   python3 06_telemetry/build_usdm.py
"""
from __future__ import annotations

import importlib
import inspect
import json
import os
import pkgutil
import uuid

import usdm_model

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "13_usdm", "tropic_usdm.json")
CT_SYS = "http://www.cdisc.org/ns/ct"
CT_VER = "2024-03-29"

# name -> class across all usdm_model submodules
C = {}
for _m in pkgutil.iter_modules(usdm_model.__path__):
    try:
        _mod = importlib.import_module(f"usdm_model.{_m.name}")
        for _n, _o in inspect.getmembers(_mod, inspect.isclass):
            if _o.__module__.startswith("usdm_model"):
                C[_n] = _o
    except Exception:
        pass

_ids = {}


def nid(prefix):
    # USDM id fields are typed as UUIDs in usdm_model; references use the object's .id
    return str(uuid.uuid4())


def make(cls_name, **kw):
    cls = C[cls_name]
    kw.setdefault("instanceType", cls_name)
    if "id" not in kw and "id" in cls.model_fields:
        kw["id"] = nid(cls_name)
    return cls(**kw)


def code(code_val, decode):
    return make("Code", code=code_val, codeSystem=CT_SYS, codeSystemVersion=CT_VER,
                decode=decode)


def build_wrapper():
    # organizations
    sponsor = make("Organization", name="Sanofi-Aventis", type=code("C70793", "Clinical Study Sponsor"),
                   identifierScheme="DUNS", identifier="000000000")
    registry = make("Organization", name="ClinicalTrials.gov",
                    type=code("C93453", "Study Registry"),
                    identifierScheme="USGOV", identifier="CT.gov")

    identifiers = [
        make("StudyIdentifier", text="NCT00417079", scopeId=registry.id),
        make("StudyIdentifier", text="EFC6193", scopeId=sponsor.id),
        make("StudyIdentifier", text="XRP6258", scopeId=sponsor.id),
    ]
    titles = [
        make("StudyTitle",
             text=("A randomized, open-label, multicenter study of cabazitaxel plus "
                   "prednisone versus mitoxantrone plus prednisone in metastatic "
                   "castration-resistant prostate cancer previously treated with a "
                   "docetaxel-containing regimen"),
             type=code("C207615", "Official Study Title")),
        make("StudyTitle", text="TROPIC", type=code("C207646", "Study Acronym")),
    ]

    # interventions
    interventions = [
        make("StudyIntervention", name="Cabazitaxel + Prednisone",
             description="Cabazitaxel 25 mg/m2 IV q3w + prednisone 10 mg PO daily",
             role=code("C41161", "Experimental Intervention"),
             type=code("C1909", "Pharmacologic Substance")),
        make("StudyIntervention", name="Mitoxantrone + Prednisone",
             description="Mitoxantrone 12 mg/m2 IV q3w + prednisone 10 mg PO daily",
             role=code("C41162", "Active Comparator"),
             type=code("C1909", "Pharmacologic Substance")),
    ]

    # arms
    arms = [
        make("StudyArm", name="Cabazitaxel + Prednisone",
             type=code("C174266", "Experimental Arm"),
             dataOriginDescription="Subject data collected during the trial",
             dataOriginType=code("C188866", "Subject Data Origin")),
        make("StudyArm", name="Mitoxantrone + Prednisone",
             type=code("C174267", "Active Comparator Arm"),
             dataOriginDescription="Subject data collected during the trial",
             dataOriginType=code("C188866", "Subject Data Origin")),
    ]
    # epochs + elements + cells
    epoch_defs = [("Screening", "C48262"), ("Treatment", "C101526"), ("Follow-up", "C99158")]
    epochs, elements, cells = [], [], []
    for enm, ecode in epoch_defs:
        ep = make("StudyEpoch", name=enm, type=code(ecode, enm))
        el = make("StudyElement", name=f"{enm} element")
        epochs.append(ep)
        elements.append(el)
        for arm in arms:
            cells.append(make("StudyCell", armId=arm.id, epochId=ep.id,
                              elementIds=[el.id]))

    # objectives + endpoints
    def obj(text, level_decode, ep_text, ep_purpose):
        ep = make("Endpoint", name=ep_text, text=ep_text,
                  purpose=ep_purpose,
                  level=code("C94496", level_decode))
        return make("Objective", name=text, text=text,
                    level=code("C94496", level_decode), endpoints=[ep])

    objectives = [
        obj("Compare overall survival between treatment arms", "Primary Objective",
            "Overall survival (OS)", "Primary Endpoint"),
        obj("Compare progression-free survival", "Secondary Objective",
            "Progression-free survival (PFS)", "Secondary Endpoint"),
        obj("Compare confirmed PSA response", "Secondary Objective",
            "PSA response (>=50% confirmed decline)", "Secondary Endpoint"),
        obj("Compare tumor response and time to tumor progression", "Secondary Objective",
            "Tumor response / time to tumor progression", "Secondary Endpoint"),
        obj("Characterize safety and tolerability", "Secondary Objective",
            "Adverse events, CTCAE grade", "Secondary Endpoint"),
    ]

    population = make("StudyDesignPopulation",
                      name="Metastatic castration-resistant prostate cancer, post-docetaxel",
                      includesHealthySubjects=False,
                      plannedSex=[code("C20197", "Male")])

    design = make("InterventionalStudyDesign", name="TROPIC interventional design",
                  rationale="Two-arm randomized comparison of cabazitaxel vs mitoxantrone.",
                  arms=arms, studyCells=cells, epochs=epochs, elements=elements,
                  population=population, objectives=objectives,
                  studyInterventionIds=[i.id for i in interventions],
                  studyPhase=make("AliasCode",
                                  standardCode=code("C15602", "Phase III Trial")),
                  model=code("C82639", "Parallel Study"),
                  subTypes=[], intentTypes=[code("C49656", "Treatment Study")])

    sv = make("StudyVersion", versionIdentifier="1.0", rationale="Initial reconstruction.",
              studyIdentifiers=identifiers, titles=titles,
              organizations=[sponsor, registry], studyInterventions=interventions,
              studyDesigns=[design],
              businessTherapeuticAreas=[code("C2991", "Oncology")])

    study = make("Study", name="TROPIC", label="TROPIC",
                 description="Cabazitaxel vs mitoxantrone in mCRPC (NCT00417079).",
                 versions=[sv])

    Wrapper = C["Wrapper"]
    return Wrapper(study=study, usdmVersion="3.0.0",
                   systemName="TROPIC build_usdm.py", systemVersion="1.0.0")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wrapper = build_wrapper()  # constructs => validates against usdm_model
    js = wrapper.model_dump_json(indent=2, exclude_none=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(js)

    d = json.loads(js)
    # self-check: every object has instanceType + unique id
    ids, types, missing = [], set(), 0
    def walk(o):
        nonlocal missing
        if isinstance(o, dict):
            if "instanceType" in o:
                types.add(o["instanceType"])
                if "id" in o:
                    ids.append(o["id"])
                else:
                    missing += 1
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(d)
    sv = d["study"]["versions"][0]
    des = sv["studyDesigns"][0]
    print("USDM Wrapper written:", os.path.relpath(OUT, ROOT))
    print(f"  usdmVersion {d['usdmVersion']} | study '{d['study']['name']}'")
    print(f"  identifiers: {[i['text'] for i in sv['studyIdentifiers']]}")
    print(f"  arms: {len(des['arms'])} | epochs: {len(des['epochs'])} | "
          f"studyCells: {len(des['studyCells'])} | objectives: {len(des['objectives'])} | "
          f"interventions: {len(sv['studyInterventions'])}")
    print(f"  entities: {len(ids)} | unique ids: {len(set(ids))==len(ids)} | "
          f"distinct instanceTypes: {len(types)} | objects missing id: {missing}")
    print("  validation: PASS (constructed through usdm_model Pydantic classes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
