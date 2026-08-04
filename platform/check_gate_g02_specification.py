#!/usr/bin/env python3
"""G02 Analysis Specification Lock — executable gate.

Ensures SAP authority, study_config, controlled TFL catalog, population/endpoint
control, and CTQ register exist and are coherent for Path A.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from define_arm_contract import evaluate as evaluate_define_arm

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "06_qc_evidence/gates/g02_specification_status.json"

REQUIRED_FILES = [
    "docs/PRODUCT_CLAIM.md",
    "02_specifications/sap/TROPIC_SAP_v4.0_industry_grade.docx",
    "config/study_config.yaml",
    "config/study_manifest.yaml",
    "config/tfl_output_catalog.yaml",
    "config/ctq_traceability.yaml",
    "docs/workstreams/WS2_POPULATION_ENDPOINT_CONTROL.md",
    "03_metadata/adam/ADaM_spec.xlsx",
    "03_metadata/define/define.xml",
]

CONFIG_KEYS = [
    "STUDYID",
    "STUDY_CUTOFF_DT",
    "PSA_RESP_THRESHOLD",
    "EPISODE_GAP_DAYS",
]


def main() -> int:
    checks = []
    problems = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            problems.append(f"{name}: {detail}" if detail else name)

    for rel in REQUIRED_FILES:
        p = ROOT / rel
        add(f"exists:{rel}", p.is_file(), "missing" if not p.is_file() else "present")

    if yaml is None:
        add("pyyaml", False, "PyYAML required")
    else:
        cfg_path = ROOT / "config/study_config.yaml"
        if cfg_path.is_file():
            cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            for key in CONFIG_KEYS:
                add(f"config.{key}", key in cfg and cfg[key] not in (None, ""), str(cfg.get(key, "missing")))

        cat_path = ROOT / "config/tfl_output_catalog.yaml"
        if cat_path.is_file():
            cat = yaml.safe_load(cat_path.read_text(encoding="utf-8")) or {}
            in_scope = cat.get("controlled_in_scope") or []
            deferred = cat.get("deferred_not_in_scope") or []
            add("catalog.in_scope_nonempty", len(in_scope) >= 1, f"n={len(in_scope)}")
            add("catalog.deferred_documented", len(deferred) >= 1, f"n={len(deferred)}")
            # Path A honesty: deferred SAP IDs must exist (not silent full catalog claim)
            add(
                "catalog.not_pretending_full_sap_only",
                len(in_scope) < 50 or len(deferred) > 0,
                f"in_scope={len(in_scope)} deferred={len(deferred)}",
            )

        man_path = ROOT / "config/study_manifest.yaml"
        if man_path.is_file():
            man = yaml.safe_load(man_path.read_text(encoding="utf-8")) or {}
            study = man.get("study") or {}
            add("manifest.study_id", bool(study.get("id")), str(study.get("id")))
            add("manifest.datasets", bool(man.get("datasets")), f"n={len(man.get('datasets') or [])}")

    pop = ROOT / "docs/workstreams/WS2_POPULATION_ENDPOINT_CONTROL.md"
    if pop.is_file():
        text = pop.read_text(encoding="utf-8")
        for token in ("ITTFL", "SAFFL", "tfl_output_catalog", "OS", "PFS"):
            add(f"population_doc.{token}", token in text, "missing token" if token not in text else "ok")

        # Semantic controls added after the structural G02 lock.  These are
        # deliberately data-free: the live XPT denominator checks belong in
        # the Section 2 audit, while this gate prevents a stale control table
        # from silently reintroducing the known endpoint/denominator drift.
        lower = text.lower()
        add(
            "population_doc.T-11-6_TTUMOR",
            "time to tumor progression" in lower and "t-11-6" in lower,
            "T-11-6 must be the TTUMOR mapping",
        )
        add(
            "population_doc.T-11-7_TTPSA",
            "time to psa progression" in lower and "t-11-7" in lower,
            "T-11-7 must be the TTPSA mapping",
        )
        add(
            "population_doc.F-011_closure",
            "f-011 resolved" in lower and "145/361" in lower and "61/329" in lower,
            "PSA eligibility closure and current arm counts must be present",
        )
        add(
            "population_doc.T-11-8_mapping_restored",
            "t-11-8" in lower
            and "ttpain" in lower
            and ("mapping restored" in lower or "mapping resolved" in lower),
            "the adopted SAP T-11-8 TTPAIN mapping and its restoration must be explicit",
        )
        endpoint_doc_checks = {
            "T-11-3_PSA_response": ("t-11-3" in lower and "psa response" in lower),
            "T-11-4_objective_response": (
                "t-11-4" in lower and "objective response" in lower
            ),
            "T-11-5_pain_response": ("t-11-5" in lower and "pain response" in lower),
            "T-11-6_TTUMOR": (
                "t-11-6" in lower and "time to tumor progression" in lower
            ),
            "T-11-7_TTPSA": (
                "t-11-7" in lower and "time to psa progression" in lower
            ),
            "T-11-8_TTPAIN": (
                "t-11-8" in lower and "time to pain progression" in lower
            ),
        }
        for check_name, ok in endpoint_doc_checks.items():
            add(
                f"population_doc.{check_name}",
                ok,
                "SAP-native T-11 endpoint mapping is missing or stale",
            )

    cat_path = ROOT / "config/tfl_output_catalog.yaml"
    if yaml is not None and cat_path.is_file():
        cat = yaml.safe_load(cat_path.read_text(encoding="utf-8")) or {}
        in_scope = {
            str(row.get("id")): str(row.get("title", "")).lower()
            for row in (cat.get("controlled_in_scope") or [])
            if row.get("id")
        }
        full = {
            str(row.get("id")): str(row.get("title", "")).lower()
            for row in ((cat.get("sap_full_catalog") or {}).get("tables") or [])
            if row.get("id")
        }
        add(
            "catalog.T-11-6_semantics",
            "tumor" in in_scope.get("T-11-6", "") and "tumor" in full.get("T-11-6", ""),
            "T-11-6 must be tumor progression in both release and SAP catalogs",
        )
        add(
            "catalog.T-11-7_semantics",
            "psa" in in_scope.get("T-11-7", "") and "psa" in full.get("T-11-7", ""),
            "T-11-7 must be PSA progression in both release and SAP catalogs",
        )
        catalog_semantics = {
            "T-11-3": "psa",
            "T-11-4": "objective response",
            "T-11-5": "pain response",
            "T-11-8": "pain progression",
        }
        for output_id, token in catalog_semantics.items():
            add(
                f"catalog.{output_id}_semantics",
                token in in_scope.get(output_id, "") and token in full.get(output_id, ""),
                f"{output_id} must be '{token}' in both release and SAP catalogs",
            )

    define_path = ROOT / "03_metadata/define/define.xml"
    if define_path.is_file():
        try:
            for check in evaluate_define_arm(define_path):
                add(
                    str(check["name"]),
                    bool(check["ok"]),
                    str(check["detail"]),
                )
        except Exception as exc:
            add("define.parse", False, str(exc))

    status = "PASS" if not problems else "FAIL"
    payload = {
        "gate": "G02",
        "name": "analysis_specification_lock",
        "status": status,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checks": checks,
        "problems": problems,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"G02 Analysis Specification Lock: {status}")
    for p in problems:
        print(f"  - {p}")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
