#!/usr/bin/env python3
"""Build a structured TFL output index with traceability and file hashes.

Controlled scope authority is config/tfl_output_catalog.yaml (SAP full catalog vs
release-in-scope dispositions). Physical CATALOG below must match controlled_in_scope.
"""

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


CONTROLLED_CATALOG_PATH = "config/tfl_output_catalog.yaml"

# Endpoint semantics are part of traceability, not just presentation.  The
# bijection gate catches missing IDs but would not catch a stable T-11-6/T-11-7
# title swap, so keep the SAP endpoint tokens executable here.
SEMANTIC_ENDPOINT_TOKENS = {
    "T-11-3": "psa",
    "T-11-4": "objective response",
    "T-11-5": "pain response",
    "T-11-6": "tumor",
    "T-11-7": "psa",
    "T-11-8": "pain progression",
}


CATALOG = {
    "F-01-1": {
        "title": "Analysis Population and Mortality Overview",
        "class": "figure",
        "file": "05_outputs/tfl/output/figures/F-01-1_CONSORT_Disposition.png",
        "sas_companion": None,
        "sap_ref": "SAP v4.0 section 3",
        "adam_inputs": "ADSL",
        "generator": "05_outputs/tfl/tfl_generation.R population-flow builder",
        "arm": "out of ARM scope (flow diagram)",
        "qc": "ADSL reconciliation; TFL generation gate; output hash",
    },
    "F-11-1": {
        "title": "Kaplan-Meier Overall Survival",
        "class": "figure",
        "file": "05_outputs/tfl/output/figures/F-11-1_KM_OS.png",
        "sas_companion": "05_outputs/tfl/output/figures/sas/F-11-1_KM_OS_SAS.png",
        "sap_ref": "SAP v4.0 section 9",
        "adam_inputs": "ADTTE (OS), ADSL",
        "generator": "05_outputs/tfl/tfl_generation.R compute_tte_stats() / KM plot",
        "arm": "RD.EFFICACY.SURVIVAL",
        "qc": "ADTTE reconciliation; numerical results reconciliation; R primary output hash; SAS companion rendered in real-SAS Stage 14",
    },
    "F-11-2": {
        "title": "Kaplan-Meier Progression-Free Survival",
        "class": "figure",
        "file": "05_outputs/tfl/output/figures/F-11-2_KM_PFS.png",
        "sas_companion": "05_outputs/tfl/output/figures/sas/F-11-2_KM_PFS_SAS.png",
        "sap_ref": "SAP v4.0 section 10.1",
        "adam_inputs": "ADTTE (PFS), ADSL",
        "generator": "05_outputs/tfl/tfl_generation.R compute_tte_stats() / KM plot",
        "arm": "RD.EFFICACY.SURVIVAL",
        "qc": "ADTTE reconciliation; numerical results reconciliation; R primary output hash; SAS companion rendered in real-SAS Stage 14",
    },
    "F-12-1": {
        "title": "Overall Survival Subgroup Forest Plot",
        "class": "figure",
        "file": "05_outputs/tfl/output/figures/F-12-1_Subgroup_Forest.png",
        "sas_companion": "05_outputs/tfl/output/figures/sas/F-12-1_Subgroup_Forest_SAS.png",
        "sap_ref": "SAP v4.0 section 8.2",
        "adam_inputs": "ADTTE (OS), ADSL covariates",
        "generator": "05_outputs/tfl/tfl_generation.R subgroup Cox model",
        "arm": "RD.EFFICACY.SUBGROUP",
        "qc": "ADTTE/ADSL reconciliation; forest HR reconciliation; R primary output hash; SAS companion rendered in real-SAS Stage 14",
    },
    "F-13-1": {
        "title": "PSA Best Percentage Change from Baseline Waterfall",
        "class": "figure",
        "file": "05_outputs/tfl/output/figures/F-13-1_PSA_Waterfall.png",
        "sas_companion": "05_outputs/tfl/output/figures/sas/F-13-1_PSA_Waterfall_SAS.png",
        "sap_ref": "SAP v4.0 section 5.2",
        "adam_inputs": "ADLB (PSA), ADSL",
        "generator": "05_outputs/tfl/tfl_generation.R PSA best-change waterfall",
        "arm": "RD.EFFICACY.PSA.RESPONSE",
        "qc": "ADLB/ADSL reconciliation; R primary output hash; SAS companion rendered in real-SAS Stage 14",
    },
    "F-14-1": {
        "title": "Treatment Exposure Duration Swimmer Plot",
        "class": "figure",
        "file": "05_outputs/tfl/output/figures/F-14-1_Swimmer_Plot.png",
        "sas_companion": "05_outputs/tfl/output/figures/sas/F-14-1_Swimmer_Plot_SAS.png",
        "sap_ref": "SAP v4.0 section 7.8",
        "adam_inputs": "ADEX, ADSL",
        "generator": "05_outputs/tfl/tfl_generation.R exposure swimmer plot",
        "arm": "RD.SAFETY.EXPOSURE",
        "qc": "ADEX/ADSL reconciliation; R primary output hash; SAS companion rendered in real-SAS Stage 14",
    },
    "F-17-1": {
        "title": "Project Optimus Exposure-Response Scatter",
        "class": "figure",
        "file": "05_outputs/tfl/output/figures/F-17-1_Optimus_Scatter.png",
        "sas_companion": "05_outputs/tfl/output/figures/sas/F-17-1_Optimus_Scatter_SAS.png",
        "sap_ref": "SAP v4.0 section 10",
        "adam_inputs": "ADEX (RDI), ADLB (ANC nadir)",
        "generator": "05_outputs/tfl/tfl_generation.R LOESS exposure-response scatter",
        "arm": "RD.OPTIMUS.ER",
        "qc": "ADEX/ADLB reconciliation; R primary output hash; SAS companion rendered in real-SAS Stage 14",
    },
    "T-11-3": {
        "title": "PSA Response Rate",
        "class": "table",
        "file": "05_outputs/tfl/output/tables/T-11-Efficacy_Tables.txt",
        "sap_ref": "SAP v4.0 sections 5.2, 10.2 / Appendix D Table 22",
        "adam_inputs": "ADRS, ADLB, ADSL",
        "generator": "05_outputs/tfl/tfl_generation.R SAP-native response block",
        "arm": "RD.EFFICACY.SECONDARY",
        "qc": "ADRS/ADLB/ADSL reconciliation; TFL generation gate; output hash",
    },
    "T-11-4": {
        "title": "Objective Response Rate per RECIST v1.0",
        "class": "table",
        "file": "05_outputs/tfl/output/tables/T-11-Efficacy_Tables.txt",
        "sap_ref": "SAP v4.0 sections 5.3, 10.3 / Appendix D Table 22",
        "adam_inputs": "ADRS, ADSL",
        "generator": "05_outputs/tfl/tfl_generation.R SAP-native response block",
        "arm": "RD.EFFICACY.SECONDARY",
        "qc": "ADRS/ADSL reconciliation; TFL generation gate; output hash",
    },
    "T-11-5": {
        "title": "Pain Response Rate",
        "class": "table",
        "file": "05_outputs/tfl/output/tables/T-11-Efficacy_Tables.txt",
        "sap_ref": "SAP v4.0 sections 6.4, 10.4 / Appendix D Table 22",
        "adam_inputs": "PN, SV, ADSL",
        "generator": "05_outputs/tfl/tfl_generation.R F-042 pain-response block",
        "arm": "RD.EFFICACY.SECONDARY",
        "qc": "F-042 regression fixtures; aggregate event-source evidence; TFL generation gate",
    },
    "T-11-6": {
        "title": "KM Analysis of Time to Tumor Progression",
        "class": "table",
        "file": "05_outputs/tfl/output/tables/T-11-Efficacy_Tables.txt",
        "sap_ref": "SAP v4.0 sections 4.3-5.3",
        "adam_inputs": "ADTTE",
        "generator": "05_outputs/tfl/tfl_generation.R secondary efficacy table block",
        "arm": "RD.EFFICACY.SECONDARY",
        "qc": "ADTTE reconciliation; TFL generation gate; output hash",
    },
    "T-11-7": {
        "title": "KM Analysis of Time to PSA Progression",
        "class": "table",
        "file": "05_outputs/tfl/output/tables/T-11-Efficacy_Tables.txt",
        "sap_ref": "SAP v4.0 sections 4.3-5.3",
        "adam_inputs": "ADTTE, ADSL",
        "generator": "05_outputs/tfl/tfl_generation.R secondary efficacy table block",
        "arm": "RD.EFFICACY.SECONDARY",
        "qc": "ADTTE/ADSL reconciliation; TFL generation gate; output hash",
    },
    "T-11-8": {
        "title": "Time to Pain Progression",
        "class": "table",
        "file": "05_outputs/tfl/output/tables/T-11-Efficacy_Tables.txt",
        "sap_ref": "SAP v4.0 sections 6.5, 10.4 / Appendix D Table 22",
        "adam_inputs": "ADTTE, ADSL",
        "generator": "05_outputs/tfl/tfl_generation.R TTPAIN KM/Cox block",
        "arm": "RD.EFFICACY.SECONDARY",
        "qc": "ADTTE reconciliation; numerical results reconciliation; TFL generation gate; output hash",
    },
    "T-11-8b": {
        "title": "Objective Response Rate - Response-Evaluable Denominator",
        "class": "table",
        "file": "05_outputs/tfl/output/tables/T-11-Efficacy_Tables.txt",
        "sap_ref": "review-board SR-1 sensitivity trace",
        "adam_inputs": "ADRS, ADSL",
        "generator": "05_outputs/tfl/tfl_generation.R response-evaluable sensitivity block",
        "arm": "not currently mapped in ARM",
        "qc": "ADRS/ADSL reconciliation; TFL generation gate; output hash",
    },
    "T-17-1": {
        "title": "Relative Dose Intensity Category Distribution",
        "class": "table",
        "file": "05_outputs/tfl/output/tables/T-17-Optimus_Tables.txt",
        "sap_ref": "Project Optimus demonstration (program comments); not in current traceability table",
        "adam_inputs": "ADEX, ADSL",
        "generator": "05_outputs/tfl/tfl_generation.R Project Optimus text table block",
        "arm": "not currently mapped in ARM",
        "qc": "ADEX/ADSL reconciliation; TFL generation gate; output hash",
    },
    "T-17-2": {
        "title": "Worst Cycle ANC Nadir Grade by G-CSF Usage",
        "class": "table",
        "file": "05_outputs/tfl/output/tables/T-17-Optimus_Tables.txt",
        "sap_ref": "Project Optimus demonstration (program comments); not in current traceability table",
        "adam_inputs": "ADLB, ADSL",
        "generator": "05_outputs/tfl/tfl_generation.R Project Optimus text table block",
        "arm": "not currently mapped in ARM",
        "qc": "ADLB/ADSL reconciliation; TFL generation gate; output hash",
    },
    "T-17-4": {
        "title": "Benefit-Risk Summary by RDI Tertile",
        "class": "table",
        "file": "05_outputs/tfl/output/tables/T-17-Optimus_Tables.txt",
        "sap_ref": "Project Optimus demonstration (program comments); not in current traceability table",
        "adam_inputs": "ADEX, ADLB, ADTTE",
        "generator": "05_outputs/tfl/tfl_generation.R Project Optimus text table block",
        "arm": "not currently mapped in ARM",
        "qc": "ADEX/ADLB/ADTTE reconciliation; TFL generation gate; output hash",
    },
    "T-20-1": {
        "title": "Treatment-Emergent Adverse Events Summary",
        "class": "table",
        "file": "05_outputs/tfl/output/tables/T-20-AE_Summary_Tables.txt",
        "sap_ref": "SAP v4.0 section 7",
        "adam_inputs": "ADAE, ADSL",
        "generator": "05_outputs/tfl/tfl_generation.R AE summary block",
        "arm": "RD.SAFETY.TEAE",
        "qc": "ADAE/ADSL reconciliation; TFL generation gate; output hash",
    },
    "T-20-2": {
        "title": "Grade >=3 TEAEs by System Organ Class",
        "class": "table",
        "file": "05_outputs/tfl/output/tables/T-20-AE_Summary_Tables.txt",
        "sap_ref": "SAP v4.0 section 7",
        "adam_inputs": "ADAE, ADSL",
        "generator": "05_outputs/tfl/tfl_generation.R AE SOC table block",
        "arm": "RD.SAFETY.TEAE",
        "qc": "ADAE/ADSL reconciliation; TFL generation gate; output hash",
    },
    "T-21-1": {
        "title": "Baseline to Worst CTCAE Grade Shift - MP Arm",
        "class": "table",
        "file": "05_outputs/tfl/output/tables/T-21-Lab_Shift_Tables.txt",
        "sap_ref": "SAP v4.0 section 7.5",
        "adam_inputs": "ADLB, ADSL",
        "generator": "05_outputs/tfl/tfl_generation.R lab shift block",
        "arm": "RD.SAFETY.LABSHIFT",
        "qc": "ADLB/ADSL reconciliation; TFL generation gate; output hash",
    },
    "T-21-2": {
        "title": "Baseline to Worst CTCAE Grade Shift - CbzP Arm",
        "class": "table",
        "file": "05_outputs/tfl/output/tables/T-21-Lab_Shift_Tables.txt",
        "sap_ref": "SAP v4.0 section 7.5; synthetic comparator demonstration",
        "adam_inputs": "ADLB, ADSL",
        "generator": "05_outputs/tfl/tfl_generation.R lab shift block",
        "arm": "not currently mapped in ARM",
        "qc": "TFL generation gate; output hash; comparator is synthetic",
    },
}


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _file_meta(path):
    if not path or not os.path.exists(path):
        return {"present": False, "size_bytes": None, "sha256": "", "mtime_utc": None, "mtime": None}
    mtime = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc)
    return {
        "present": True,
        "size_bytes": os.path.getsize(path),
        "sha256": _sha256(path),
        "mtime_utc": mtime.isoformat(),
        "mtime": mtime,
    }


def _pipeline_health_ts():
    path = "platform/pipeline_health.json"
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw = data.get("timestamp")
        if not raw:
            return None
        ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def _load_controlled_catalog(path=CONTROLLED_CATALOG_PATH):
    if yaml is None:
        raise RuntimeError("PyYAML is required to load config/tfl_output_catalog.yaml")
    if not os.path.exists(path):
        raise RuntimeError(f"Controlled TFL catalog missing: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} did not parse to a YAML mapping")
    return data


def _sap_full_ids(controlled):
    ids = set()
    sap = controlled.get("sap_full_catalog") or {}
    for group in ("figures", "tables", "listings"):
        for row in sap.get(group) or []:
            if row.get("id"):
                ids.add(str(row["id"]))
    return ids


def _evaluate_controlled_catalog(controlled, catalog_ids):
    """Bijective control: index CATALOG ↔ controlled_in_scope; SAP full IDs dispositioned."""
    in_scope = controlled.get("controlled_in_scope") or []
    deferred = controlled.get("deferred_not_in_scope") or []
    in_scope_ids = {str(r["id"]) for r in in_scope if r.get("id")}
    deferred_ids = {str(r["id"]) for r in deferred if r.get("id")}
    sap_ids = _sap_full_ids(controlled)

    index_not_in_scope = sorted(catalog_ids - in_scope_ids)
    scope_not_in_index = sorted(in_scope_ids - catalog_ids)
    sap_undispositioned = sorted(sap_ids - in_scope_ids - deferred_ids)
    deferred_also_in_scope = sorted(deferred_ids & in_scope_ids)
    deferred_not_in_sap = sorted(deferred_ids - sap_ids)

    problems = []
    if index_not_in_scope:
        problems.append(
            "index CATALOG IDs not listed in controlled_in_scope: "
            + ", ".join(index_not_in_scope)
        )
    if scope_not_in_index:
        problems.append(
            "controlled_in_scope IDs missing from index CATALOG: "
            + ", ".join(scope_not_in_index)
        )
    if sap_undispositioned:
        problems.append(
            "SAP full-catalog IDs neither in-scope nor deferred: "
            + ", ".join(sap_undispositioned)
        )
    if deferred_also_in_scope:
        problems.append(
            "IDs listed as both in-scope and deferred: "
            + ", ".join(deferred_also_in_scope)
        )

    return {
        "catalog_file": CONTROLLED_CATALOG_PATH,
        "sap_authority": controlled.get("sap_authority", ""),
        "controlled_in_scope_count": len(in_scope_ids),
        "sap_full_catalog_count": len(sap_ids),
        "deferred_count": len(deferred_ids),
        "approved_extension_count": sum(
            1 for r in in_scope if r.get("disposition") == "approved_extension"
        ),
        "index_not_in_scope": index_not_in_scope,
        "scope_not_in_index": scope_not_in_index,
        "sap_undispositioned": sap_undispositioned,
        "deferred_also_in_scope": deferred_also_in_scope,
        "deferred_not_in_sap": deferred_not_in_sap,
        "problems": problems,
        "status": "pass" if not problems else "fail",
    }


def _semantic_catalog_problems(controlled, rows, output_root):
    """Validate endpoint meaning across static catalogs and the physical text output."""
    problems = []
    in_scope = {
        str(row.get("id")): str(row.get("title", "")).lower()
        for row in (controlled.get("controlled_in_scope") or [])
        if row.get("id")
    }
    sap = controlled.get("sap_full_catalog") or {}
    full = {
        str(row.get("id")): str(row.get("title", "")).lower()
        for row in (sap.get("tables") or [])
        if row.get("id")
    }
    row_by_id = {row["output_id"]: row for row in rows}
    for output_id, token in SEMANTIC_ENDPOINT_TOKENS.items():
        expected = token.lower()
        for source, title in (
            ("CATALOG", str(CATALOG.get(output_id, {}).get("title", "")).lower()),
            ("controlled_in_scope", in_scope.get(output_id, "")),
            ("sap_full_catalog", full.get(output_id, "")),
        ):
            if expected not in title:
                problems.append(f"{source} {output_id} title lacks endpoint token '{token}'")

        row = row_by_id.get(output_id)
        if row and row.get("primary_present"):
            path = row["primary_file"]
            try:
                text = open(path, "r", encoding="utf-8", errors="replace").read().lower()
            except OSError:
                text = ""
            start = text.find(output_id.lower())
            block = text[start:start + 500] if start >= 0 else ""
            if expected not in block:
                problems.append(f"physical output {output_id} block lacks endpoint token '{token}'")
    return problems


def _companion_freshness(primary_meta, companion_meta, health_ts):
    """SAS companions are rendered in the real-SAS stage and must be current."""
    if not companion_meta.get("present"):
        return {
            "generation_scope": "in_dag_real_sas_companion",
            "current_with_primary": False,
            "current_with_pipeline_health": False,
            "freshness": "missing",
        }
    companion_mtime = companion_meta.get("mtime")
    primary_mtime = primary_meta.get("mtime")
    # The SAS companion is rendered before the R primary in the DAG, so the
    # companion is normally a few minutes older than the primary. Treat the
    # pair as same-run when their mtimes are within a bounded window in either
    # order; the independent pipeline-health timestamp below is the historical
    # file guard.
    current_primary = bool(
        companion_mtime and primary_mtime
        and abs(companion_mtime - primary_mtime) <= timedelta(hours=1)
    )
    # The health JSON is written after the companion download. Allow a bounded
    # clock/order skew while still rejecting historical files.
    current_health = bool(
        health_ts and companion_mtime and companion_mtime >= health_ts - timedelta(hours=1)
    )
    if current_primary and current_health:
        freshness = "current"
    else:
        freshness = "stale_or_historical"
    return {
        "generation_scope": "in_dag_real_sas_companion",
        "current_with_primary": current_primary,
        "current_with_pipeline_health": current_health,
        "freshness": freshness,
    }


def _extract_table_ids(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    return sorted(set(re.findall(r"\b[FTL]-\d{2}-\d+[a-z]?\b", text)))


def _physical_outputs(output_root):
    paths = []
    for root, _, files in os.walk(output_root):
        for name in files:
            if name == ".gitkeep":
                continue
            paths.append(os.path.join(root, name))
    return sorted(paths)


def _build_rows(output_root):
    rows = []
    health_ts = _pipeline_health_ts()
    for output_id, item in sorted(CATALOG.items()):
        meta = _file_meta(item["file"])
        companion = item.get("sas_companion") or ""
        companion_meta = _file_meta(companion) if companion else {
            "present": None, "sha256": "", "mtime_utc": None, "mtime": None,
        }
        freshness = (
            _companion_freshness(meta, companion_meta, health_ts)
            if companion
            else {
                "generation_scope": "n/a",
                "current_with_primary": None,
                "current_with_pipeline_health": None,
                "freshness": "n/a",
            }
        )
        rows.append({
            "output_id": output_id,
            "title": item["title"],
            "class": item["class"],
            "primary_file": item["file"],
            "primary_present": meta["present"],
            "primary_size_bytes": meta["size_bytes"],
            "primary_sha256": meta["sha256"],
            "sas_companion_file": companion,
            "sas_companion_present": companion_meta["present"],
            "sas_companion_sha256": companion_meta["sha256"],
            "sas_companion_mtime_utc": companion_meta.get("mtime_utc") or "",
            "sas_companion_generation_scope": freshness["generation_scope"],
            "sas_companion_freshness": freshness["freshness"],
            "sas_companion_current_with_primary": freshness["current_with_primary"],
            "sas_companion_current_with_pipeline_health": freshness["current_with_pipeline_health"],
            "sap_ref": item["sap_ref"],
            "adam_inputs": item["adam_inputs"],
            "generator": item["generator"],
            "arm_result_display": item["arm"],
            "qc_evidence": item["qc"],
            "reviewer_note": "Comparative CbzP content is synthetic/reconstructed demonstration where applicable; see ADRG/README.",
        })

    expected_files = {item["file"] for item in CATALOG.values()}
    expected_files.update(item.get("sas_companion") for item in CATALOG.values() if item.get("sas_companion"))
    physical = set(_physical_outputs(output_root))
    unindexed = sorted(physical - expected_files)

    extracted_ids = {}
    for path in sorted({item["file"] for item in CATALOG.values() if item["class"] == "table"}):
        extracted_ids[path] = _extract_table_ids(path)

    catalog_ids = set(CATALOG)
    extracted_id_set = set()
    for ids in extracted_ids.values():
        extracted_id_set.update(ids)
    table_ids_missing_catalog = sorted(extracted_id_set - catalog_ids)
    catalog_table_ids_missing_text = sorted(
        output_id for output_id, item in CATALOG.items()
        if item["class"] == "table" and output_id not in extracted_id_set
    )
    return rows, unindexed, extracted_ids, table_ids_missing_catalog, catalog_table_ids_missing_text


def _write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = [
        "output_id", "title", "class", "primary_file", "primary_present",
        "primary_size_bytes", "primary_sha256", "sas_companion_file",
        "sas_companion_present", "sas_companion_sha256", "sas_companion_mtime_utc",
        "sas_companion_generation_scope", "sas_companion_freshness",
        "sas_companion_current_with_primary", "sas_companion_current_with_pipeline_health",
        "sap_ref", "adam_inputs", "generator", "arm_result_display", "qc_evidence",
        "reviewer_note",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        clean = [str(v).replace("|", "\\|").replace("\n", " ") for v in row]
        lines.append("| " + " | ".join(clean) + " |")
    return "\n".join(lines)


def _build_markdown(generated_at, rows, unindexed, extracted_ids, missing_catalog, missing_text,
                    controlled_eval, controlled):
    figures = [r for r in rows if r["class"] == "figure"]
    tables = [r for r in rows if r["class"] == "table"]
    missing_files = [r for r in rows if not r["primary_present"]]
    missing_companions = [
        r for r in rows
        if r["sas_companion_file"] and not r["sas_companion_present"]
    ]
    stale_companions = [
        r for r in rows
        if r["sas_companion_file"] and r.get("sas_companion_freshness") == "stale_or_historical"
    ]
    summary_rows = [
        ["Generated", generated_at],
        ["Overall status", "see Machine-Readable status JSON"],
        ["Controlled catalog", CONTROLLED_CATALOG_PATH],
        ["Controlled catalog status", controlled_eval.get("status", "")],
        ["Controlled in-scope IDs", controlled_eval.get("controlled_in_scope_count", "")],
        ["SAP full-catalog IDs", controlled_eval.get("sap_full_catalog_count", "")],
        ["Deferred (not in release scope)", controlled_eval.get("deferred_count", "")],
        ["Approved extensions", controlled_eval.get("approved_extension_count", "")],
        ["Indexed output IDs", len(rows)],
        ["Figure IDs", len(figures)],
        ["Table IDs", len(tables)],
        ["Missing primary files", len(missing_files)],
        ["Missing SAS companion figures", len(missing_companions)],
        ["Historical SAS companions", len(stale_companions)],
        ["Unindexed physical files", len(unindexed)],
        ["Table IDs in text but not catalog", len(missing_catalog)],
        ["Catalog table IDs not found in text", len(missing_text)],
    ]
    index_rows = [
        [
            r["output_id"], r["class"], r["title"], r["primary_file"],
            "present" if r["primary_present"] else "missing",
            r["sap_ref"], r["adam_inputs"], r["arm_result_display"], r["qc_evidence"],
        ]
        for r in rows
    ]
    hash_rows = [
        [r["output_id"], r["primary_file"], r["primary_sha256"]]
        for r in rows
        if r["primary_present"]
    ]
    companion_rows = [
        [
            r["output_id"], r["sas_companion_file"],
            "present" if r["sas_companion_present"] else "missing",
            r.get("sas_companion_generation_scope", ""),
            r.get("sas_companion_freshness", ""),
            r.get("sas_companion_mtime_utc", ""),
            r["sas_companion_sha256"],
        ]
        for r in rows
        if r["sas_companion_file"]
    ]
    extracted_rows = [[path, ", ".join(ids)] for path, ids in sorted(extracted_ids.items())]

    in_scope_rows = [
        [
            r.get("id", ""),
            r.get("class", ""),
            r.get("title", ""),
            r.get("disposition", ""),
            r.get("basis", ""),
        ]
        for r in (controlled.get("controlled_in_scope") or [])
    ]
    deferred_rows = [
        [r.get("id", ""), r.get("reason", "")]
        for r in (controlled.get("deferred_not_in_scope") or [])
    ]
    lines = [
        "# TROPIC TFL Output Index",
        "",
        f"Generated: {generated_at}",
        "",
        "> Structured index for rendered tables, figures, listings, and companion SAS figures. "
        "This is output-control evidence, not a claim that every output is submission-ready. "
        f"**Controlled scope authority:** `{CONTROLLED_CATALOG_PATH}` "
        f"(SAP authority: {controlled.get('sap_authority', 'SAP v4.0')}). "
        "SAS companion figures are rendered in the real-SAS Stage 14 session and "
        "their figure-driving datasets are reconciled before release sealing.",
        "",
        "## Summary",
        "",
        _md_table(["Item", "Value"], summary_rows),
        "",
        "## Controlled Scope (release-in-scope outputs)",
        "",
        _md_table(["ID", "Class", "Title", "Disposition", "Basis"], in_scope_rows),
        "",
        "## Deferred SAP Full-Catalog IDs (not in this release scope)",
        "",
        _md_table(["ID", "Disposition reason"], deferred_rows)
        if deferred_rows else "No deferred IDs.",
        "",
        "## Output Traceability Index",
        "",
        _md_table(
            ["ID", "Class", "Title", "Primary file", "Presence", "Spec/SAP ref", "ADaM inputs", "ARM/ARS link", "QC evidence"],
            index_rows,
        ),
        "",
        "## Table IDs Extracted From Bundled Text Outputs",
        "",
        _md_table(["File", "Detected IDs"], extracted_rows),
        "",
        "## SAS Companion Figures (real-SAS Stage 14)",
        "",
        _md_table(
            ["ID", "SAS companion file", "Presence", "Scope", "Freshness", "mtime UTC", "SHA-256"],
            companion_rows,
        ),
        "",
        "## Primary Output Hashes",
        "",
        _md_table(["ID", "File", "SHA-256"], hash_rows),
        "",
        "## Control Exceptions",
        "",
    ]
    if controlled_eval.get("problems"):
        lines.append("Controlled catalog problems:")
        lines.append("")
        for p in controlled_eval["problems"]:
            lines.append(f"- {p}")
        lines.append("")
    if unindexed:
        lines.append("Unindexed physical files:")
        lines.append("")
        lines.append(_md_table(["File"], [[p] for p in unindexed]))
    else:
        lines.append("No unindexed physical output files were detected.")

    lines.extend(["", ""])
    if missing_catalog:
        lines.append("Table IDs detected in text outputs but absent from catalog:")
        lines.append("")
        lines.append(_md_table(["ID"], [[i] for i in missing_catalog]))
    else:
        lines.append("No table IDs were detected in text outputs without catalog coverage.")

    lines.extend(["", ""])
    if missing_text:
        lines.append("Catalog table IDs not detected in their bundled text file:")
        lines.append("")
        lines.append(_md_table(["ID"], [[i] for i in missing_text]))
    else:
        lines.append("All catalog table IDs were detected in their bundled text files.")

    lines.extend([
        "",
        "## Disclosure",
        "",
        "Comparative CbzP output content is synthetic/reconstructed demonstration content where applicable. "
        "The index preserves that disclosure by linking output control to ADRG/README limitations rather than "
        "representing comparative outputs as independent clinical evidence. "
        "Deferred SAP full-catalog IDs are **not** silent gaps: they are explicit non-commitments in "
        f"`{CONTROLLED_CATALOG_PATH}` until implemented under approved shells and QC.",
        "",
        "## Machine-Readable Outputs",
        "",
        "- `config/tfl_output_catalog.yaml` (controlled scope authority)",
        "- `platform/tfl_output_index/tfl_output_index.csv`",
        "- `platform/tfl_output_index/tfl_output_index.json`",
        "- `platform/tfl_output_index_status.json`",
        "",
    ])
    return "\n".join(lines)


def build_tfl_output_index(output_root, out_dir, report_path):
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    controlled = _load_controlled_catalog()
    controlled_eval = _evaluate_controlled_catalog(controlled, set(CATALOG))
    rows, unindexed, extracted_ids, missing_catalog, missing_text = _build_rows(output_root)
    semantic_problems = _semantic_catalog_problems(controlled, rows, output_root)
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.dirname(report_path) or ".", exist_ok=True)

    csv_path = os.path.join(out_dir, "tfl_output_index.csv")
    json_path = os.path.join(out_dir, "tfl_output_index.json")
    _write_csv(csv_path, rows)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    stale_companions = [
        r["output_id"] for r in rows
        if r["sas_companion_file"] and r.get("sas_companion_freshness") == "stale_or_historical"
    ]
    missing_primary = [r["output_id"] for r in rows if not r["primary_present"]]
    # Gate on controlled-scope completeness + physical index integrity.
    # In-DAG SAS companions are a controlled completeness gate. Historical
    # files are retained in the index as a visible failure signal.
    hard_fail = bool(
        controlled_eval["status"] != "pass"
        or unindexed
        or missing_catalog
        or missing_text
        or missing_primary
        or stale_companions
        or semantic_problems
    )
    status = {
        "status": "fail" if hard_fail else "pass",
        "generated_at": generated_at,
        "controlled_catalog": controlled_eval,
        "indexed_output_ids": len(rows),
        "missing_primary_files": missing_primary,
        "missing_sas_companion_figures": [
            r["output_id"] for r in rows if r["sas_companion_file"] and not r["sas_companion_present"]
        ],
        "stale_sas_companion_figures": stale_companions,
        "sas_companion_generation_scope": "in_dag_real_sas_companion",
        "sas_companion_gates_completeness": True,
        "unindexed_physical_files": unindexed,
        "table_ids_detected_without_catalog": missing_catalog,
        "catalog_table_ids_not_detected_in_text": missing_text,
        "semantic_problems": semantic_problems,
    }
    status_path = os.path.join(os.path.dirname(out_dir), "tfl_output_index_status.json")
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(_build_markdown(
            generated_at, rows, unindexed, extracted_ids, missing_catalog, missing_text,
            controlled_eval, controlled,
        ))
    return status


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build structured TFL output index")
    parser.add_argument("--output-root", default="05_outputs/tfl/output")
    parser.add_argument("--out-dir", default="platform/tfl_output_index")
    parser.add_argument("--report", default="docs/TFL_OUTPUT_INDEX.md")
    args = parser.parse_args(argv)

    status = build_tfl_output_index(args.output_root, args.out_dir, args.report)
    print(f"TFL output index status: {status['status']}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
