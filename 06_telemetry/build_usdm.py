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
Construction provides structural validation only: every entity is instantiated through
the model, so required slots and `instanceType` literals are checked. This script adds
local checks for unique ids, internal `*Id`/`*Ids` reference resolution, and accidental
controlled-terminology code reuse with conflicting decode text. It does not replace a
full USDM/DDF semantic validator or live NCI EVS terminology lookup. Facts sourced from
study_config.yaml + the public TROPIC protocol (NCT00417079 / EFC6193 / XRP6258).

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
_IMPORT_ERRORS = []
for _m in sorted(pkgutil.iter_modules(usdm_model.__path__), key=lambda m: m.name):
    try:
        _mod = importlib.import_module(f"usdm_model.{_m.name}")
        for _n, _o in inspect.getmembers(_mod, inspect.isclass):
            if _o.__module__.startswith("usdm_model"):
                C[_n] = _o
    except Exception as e:
        _IMPORT_ERRORS.append(f"{_m.name}: {type(e).__name__}: {e}")


def nid():
    # USDM id fields are typed as UUIDs in usdm_model; references use the object's .id
    return str(uuid.uuid4())


def make(cls_name, **kw):
    if cls_name not in C:
        detail = "; ".join(_IMPORT_ERRORS) if _IMPORT_ERRORS else "no import errors recorded"
        raise KeyError(f"USDM class {cls_name!r} not discovered ({detail})")
    cls = C[cls_name]
    kw.setdefault("instanceType", cls_name)
    if "id" not in kw and "id" in cls.model_fields:
        kw["id"] = nid()
    return cls(**kw)


def code(code_val, decode):
    return make("Code", code=code_val, codeSystem=CT_SYS, codeSystemVersion=CT_VER,
                decode=decode)


OBJECTIVE_LEVEL = {
    "Primary Objective": ("C85826", "Trial Primary Objective"),
    "Secondary Objective": ("C85827", "Trial Secondary Objective"),
}

ENDPOINT_LEVEL = {
    "Primary Endpoint": ("C94496", "Primary Endpoint"),
    "Secondary Endpoint": ("C139173", "Secondary Endpoint"),
}


def build_wrapper():
    # organizations
    sponsor = make("Organization", name="Sanofi-Aventis", type=code("C70793", "Clinical Study Sponsor"),
                   identifierScheme="UNVERIFIED", identifier="SANOFI-DUNS-NOT-PROVIDED")
    registry = make("Organization", name="ClinicalTrials.gov",
                    type=code("C93453", "Study Registry"),
                    identifierScheme="URL", identifier="https://clinicaltrials.gov")

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
        obj_code, obj_decode = OBJECTIVE_LEVEL[level_decode]
        ep_code, ep_decode = ENDPOINT_LEVEL[ep_purpose]
        ep = make("Endpoint", name=ep_text, text=ep_text,
                  purpose=ep_purpose,
                  level=code(ep_code, ep_decode))
        return make("Objective", name=text, text=text,
                    level=code(obj_code, obj_decode), endpoints=[ep])

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


def _walk(o, path="$"):
    yield path, o
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _walk(v, f"{path}[{i}]")


def validate_usdm_dict(d):
    """Local structural checks beyond Pydantic construction."""
    errors = []
    ids = []
    instance_types = set()
    missing_id = 0
    refs = []
    code_decodes = {}

    for path, o in _walk(d):
        if not isinstance(o, dict):
            continue
        if "instanceType" in o:
            instance_types.add(o["instanceType"])
            if "id" in o:
                ids.append(o["id"])
            else:
                missing_id += 1
        if "code" in o and "decode" in o:
            code_decodes.setdefault((o.get("codeSystem"), o["code"]), set()).add(o["decode"])
        for k, v in o.items():
            if k.endswith("Id") and isinstance(v, str) and v:
                refs.append((path, k, v))
            elif k.endswith("Ids") and isinstance(v, list):
                refs.extend((path, k, item) for item in v if isinstance(item, str) and item)

    id_set = set(ids)
    if len(id_set) != len(ids):
        errors.append("duplicate ids detected")
    if missing_id:
        errors.append(f"{missing_id} typed object(s) missing id")
    for path, key, ref in refs:
        if ref not in id_set:
            errors.append(f"unresolved reference {path}.{key} -> {ref}")
    for (system, code_val), decodes in sorted(code_decodes.items()):
        if len(decodes) > 1:
            errors.append(
                f"CT code {code_val} ({system}) reused with multiple decodes: "
                + ", ".join(sorted(decodes))
            )
    if _IMPORT_ERRORS:
        errors.extend(f"usdm_model import warning: {e}" for e in _IMPORT_ERRORS)
    stats = {
        "ids": len(ids),
        "unique_ids": len(id_set) == len(ids),
        "instance_types": len(instance_types),
        "missing_id": missing_id,
        "references": len(refs),
    }
    return errors, stats


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wrapper = build_wrapper()  # Pydantic structural construction
    js = wrapper.model_dump_json(indent=2, exclude_none=True)
    d = json.loads(js)
    errors, stats = validate_usdm_dict(d)
    if errors:
        print("USDM local validation: FAIL")
        for e in errors:
            print("  -", e)
        return 1

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(js)

    sv = d["study"]["versions"][0]
    des = sv["studyDesigns"][0]
    print("USDM Wrapper written:", os.path.relpath(OUT, ROOT))
    print(f"  usdmVersion {d['usdmVersion']} | study '{d['study']['name']}'")
    print(f"  identifiers: {[i['text'] for i in sv['studyIdentifiers']]}")
    print(f"  arms: {len(des['arms'])} | epochs: {len(des['epochs'])} | "
          f"studyCells: {len(des['studyCells'])} | objectives: {len(des['objectives'])} | "
          f"interventions: {len(sv['studyInterventions'])}")
    print(f"  entities: {stats['ids']} | unique ids: {stats['unique_ids']} | "
          f"distinct instanceTypes: {stats['instance_types']} | "
          f"objects missing id: {stats['missing_id']} | references checked: {stats['references']}")
    print("  validation: PASS (Pydantic structure + local refs/CT-reuse checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
