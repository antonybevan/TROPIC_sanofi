#!/usr/bin/env python3
"""Build the explicit orphan, dangling-reference, and dead-code register.

The register is derived from the current eCTD index, manifest, catalog, and
filesystem. Historical cleanup actions belong in dated audit reports; they must
not remain labelled as current orphans after resolution.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SEQ = ROOT / "08_submission_package/ectd/0000"
OUT = ROOT / "06_qc_evidence/audit/orphans_dangling_deadcode.csv"
FIELDS = ("type", "path_or_reference", "evidence", "status", "remediation")


def _add(rows, kind, path, evidence, status, remediation):
    rows.append(
        {
            "type": kind,
            "path_or_reference": path,
            "evidence": evidence,
            "status": status,
            "remediation": remediation,
        }
    )


def _yaml_list_block(text: str, key: str) -> str:
    """Return one top-level YAML list block without adding a PyYAML dependency."""
    match = re.search(rf"(?ms)^{re.escape(key)}:\s*\n(.*?)(?=^\S|\Z)", text)
    return match.group(1) if match else ""


def _yaml_list_ids(text: str, key: str) -> list[str]:
    return re.findall(r"(?m)^\s+-\s+id:\s*([^\s#]+)", _yaml_list_block(text, key))


def _orchestration_row(rows, manifest_text, *, kind, path, label, status, remediation):
    if path in manifest_text:
        _add(
            rows,
            kind,
            path,
            f"Invoked by config/study_manifest.yaml ({label})",
            status,
            remediation,
        )
    else:
        _add(
            rows,
            f"UNORCHESTRATED {kind}",
            path,
            f"Absent from config/study_manifest.yaml ({label})",
            "CONFIRMED",
            "Restore the required manifest stage or formally remove and disposition the capability.",
        )


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    index_text = (SEQ / "index.xml").read_text(encoding="utf-8")
    hrefs = {
        match.replace("\\", "/")
        for match in re.findall(r'xlink:href="([^"]+)"', index_text)
    }
    unindexed = []
    for path in sorted((SEQ / "m5").rglob("*.xpt")):
        relative = path.relative_to(SEQ).as_posix()
        if relative not in hrefs:
            unindexed.append(path)
            _add(
                rows,
                "ORPHAN/UNINDEXED PAYLOAD",
                path.relative_to(ROOT).as_posix(),
                "Not present as an xlink:href in 08_submission_package/ectd/0000/index.xml",
                "CONFIRMED",
                "Delete the stale payload and rebuild one atomic full or preview sequence.",
            )
    if not unindexed:
        _add(
            rows,
            "CONTROL RESULT",
            "08_submission_package/ectd/0000/m5/**/*.xpt",
            "Every materialized Module 5 XPT is referenced by index.xml",
            "NO_UNINDEXED_PAYLOADS",
            "No action; retain index/payload parity validation in the release DAG.",
        )

    discontinuation = ROOT / "05_outputs/tfl/output/listings/L-01-1_Discontinuations.txt"
    if discontinuation.exists():
        text = discontinuation.read_text(encoding="utf-8", errors="replace")
        if "L_discon.sas" in text and not (
            ROOT / "04_analysis_datasets/programs/sas/L_discon.sas"
        ).exists():
            _add(
                rows,
                "DANGLING REFERENCE",
                "L_discon.sas",
                "L-01-1_Discontinuations.txt cites the missing producer L_discon.sas",
                "CONFIRMED",
                "Remove the placeholder or generate it from an approved, validated program.",
            )
    else:
        _add(
            rows,
            "CONTROL RESULT",
            "05_outputs/tfl/output/listings/L-01-1_Discontinuations.txt",
            "The prohibited false listing is absent; no listing is in controlled scope",
            "NO_FALSE_LISTING",
            "No action; future listings require an approved shell, source lineage, and QC.",
        )

    manifest_text = (ROOT / "config/study_manifest.yaml").read_text(encoding="utf-8")
    orchestrated = (
        ("ORCHESTRATED GENERATOR", "platform/gen_adam_labels.R", "ADaM Spec Label/Order Artifacts", "RESOLVED_IN_DAG", "Keep the label/order artifacts gated before SAS/R derivations."),
        ("ORCHESTRATED SOURCE WORKFLOW", "01_source_data/reconstruct_cbzp_arm.R", "Synthetic Comparator Reconstruction", "RESOLVED_IN_DAG", "Keep the synthetic-comparator disclosure and deterministic bridge controls."),
        ("ORCHESTRATED SOURCE WORKFLOW", "01_source_data/guyot_validation_report.R", "Guyot Reconstruction Validation", "RESOLVED_IN_DAG", "Keep the reconstruction validation ahead of SAS production."),
        ("ORCHESTRATED SOURCE WORKFLOW", "01_source_data/export_cbzp_xpt.R", "Synthetic Comparator XPT Export", "RESOLVED_IN_DAG", "Keep the deterministic XPT export ahead of SAS production."),
        ("ORCHESTRATED QC", "01_source_data/check_cbzp_bridge.R", "Synthetic Comparator Bridge Parity", "RESOLVED_IN_DAG", "Keep exact RDS/XPT bridge parity before TFL compilation."),
        ("ORCHESTRATED QC", "04_analysis_datasets/programs/r/admiral_adsl.R", "Admiral ADSL Re-derivation", "RESOLVED_IN_DAG", "Keep the risk-based third-engine ADSL track."),
        ("ORCHESTRATED QC", "04_analysis_datasets/programs/r/admiral_adtte.R", "Admiral ADTTE Re-derivation (OS/PFS)", "RESOLVED_IN_DAG", "Keep the risk-based third-engine ADTTE track."),
        ("ORCHESTRATED QC", "06_qc_evidence/reconciliation/admiral_reconcile.R", "Admiral Core Reconciliation", "RESOLVED_IN_DAG", "Keep the gated third-engine reconciliation."),
        ("ORCHESTRATED QC", "06_qc_evidence/reconciliation/figure_data_reconcile.R", "Figure-Data Reconciliation (SAS vs R)", "RESOLVED_IN_DAG", "Keep the figure-driving-data reconciliation in the release DAG."),
        ("ORCHESTRATED ADDITIVE OUTPUT", "platform/export_datasetjson.py", "Dataset-JSON Export (v1.1)", "CLASSIFIED_ADDITIVE", "Retain as an exploratory exchange layer; it is not an eCTD primary payload."),
        ("ORCHESTRATED ADDITIVE OUTPUT", "platform/build_ars.py", "Analysis Results Standard (ARS v1.0)", "CLASSIFIED_ADDITIVE", "Retain as a scoped ARS pilot; it is not an eCTD primary payload."),
        ("ORCHESTRATED ADDITIVE OUTPUT", "platform/build_usdm.py", "USDM Study Definition (v3.0)", "CLASSIFIED_ADDITIVE", "Retain as an exploratory study-definition layer; it is not an eCTD payload."),
    )
    for kind, path, label, status, remediation in orchestrated:
        _orchestration_row(
            rows,
            manifest_text,
            kind=kind,
            path=path,
            label=label,
            status=status,
            remediation=remediation,
        )

    reconstruction = (ROOT / "01_source_data/reconstruct_cbzp_arm.R").read_text(encoding="utf-8")
    helper = "01_source_data/reconstruct_cbzp_guyot.R"
    if helper in reconstruction:
        _add(
            rows,
            "ORCHESTRATED HELPER",
            helper,
            "Sourced by the manifest-orchestrated reconstruct_cbzp_arm.R workflow",
            "RESOLVED_IN_DAG",
            "No action; keep helper provenance bound through the source-tree seal.",
        )
    else:
        _add(
            rows,
            "UNREFERENCED SOURCE HELPER",
            helper,
            "Not sourced by reconstruct_cbzp_arm.R and not present in the manifest",
            "CONFIRMED",
            "Restore its call path or remove it after confirming it has no supported use.",
        )

    metadata_control = (ROOT / "platform/build_metadata_control_report.py").read_text(
        encoding="utf-8"
    )
    for helper, purpose in (
        (
            "06_qc_evidence/audit/build_variable_traceability.py",
            "ADaM variable traceability",
        ),
        (
            "06_qc_evidence/audit/build_metadata_drift.py",
            "metadata/data drift",
        ),
    ):
        if helper in metadata_control and "platform/build_metadata_control_report.py" in manifest_text:
            _add(
                rows,
                "ORCHESTRATED HELPER",
                helper,
                f"Called by the manifest-orchestrated Metadata Control Evidence Refresh ({purpose})",
                "RESOLVED_IN_DAG",
                "Keep prerequisite regeneration and fail-closed nonempty/schema checks together.",
            )
        else:
            _add(
                rows,
                "UNORCHESTRATED CONTROL INPUT BUILDER",
                helper,
                f"No complete call path from the metadata-control manifest stage ({purpose})",
                "CONFIRMED",
                "Restore current-run orchestration or remove dependent current-state claims.",
            )

    _add(
        rows,
        "MANUAL DIAGNOSTIC",
        "platform/_oda_render_tfl.py",
        "The release DAG renders SAS companions; this helper is diagnostic only",
        "CLASSIFIED_OUT_OF_DAG",
        "Keep outside release evidence; document and use only for bounded diagnostics.",
    )
    _add(
        rows,
        "MANUAL AUDIT UTILITY",
        "06_qc_evidence/audit/build_inventory.py",
        "Local audit inventory; credential bytes are excluded and outputs are mode 0600",
        "CLASSIFIED_OUT_OF_DAG",
        "Run only for a deliberate local repository audit; do not treat its ignored CSVs as release evidence.",
    )
    _add(
        rows,
        "GOVERNANCE REGISTER BUILDER",
        "06_qc_evidence/audit/build_orphan_register.py",
        "Regenerates this controlled classification from current manifest/catalog/filesystem state",
        "CLASSIFIED_OUT_OF_DAG",
        "Run during repository-hygiene review and gate the checked-in register with data-free tests.",
    )

    ndjson_files = sorted((ROOT / "04_analysis_datasets/datasetjson").rglob("*.ndjson"))
    if ndjson_files:
        _add(
            rows,
            "OUT-OF-BAND OUTPUT",
            "04_analysis_datasets/datasetjson/**/*.ndjson",
            f"Found {len(ndjson_files)} NDJSON file(s), while the release DAG invokes JSON mode",
            "CONFIRMED",
            "Remove stale NDJSON files or approve and orchestrate the streaming variant.",
        )
    else:
        _add(
            rows,
            "OPTIONAL OUTPUT PATTERN",
            "04_analysis_datasets/datasetjson/**/*.ndjson",
            "No NDJSON files are present; --ndjson remains an explicitly optional export mode",
            "NO_STALE_OUTPUT",
            "No action; do not retain optional NDJSON output as release evidence unless scoped.",
        )

    catalog_text = (ROOT / "config/tfl_output_catalog.yaml").read_text(encoding="utf-8")
    deferred = _yaml_list_ids(catalog_text, "deferred_not_in_scope")
    controlled_block = _yaml_list_block(catalog_text, "controlled_in_scope")
    approved_extensions = len(re.findall(r"(?m)^\s+disposition:\s*approved_extension\s*$", controlled_block))
    _add(
        rows,
        "CONTROLLED SCOPE DEFERMENT",
        f"config/tfl_output_catalog.yaml deferred_not_in_scope ({len(deferred)} IDs)",
        "SAP v4 full-catalog IDs not delivered in the controlled demonstration scope",
        "DISPOSITIONED_IN_CONTROLLED_CATALOG",
        "Implement only under approved shells and QC, or retain the explicit deferments.",
    )
    _add(
        rows,
        "CONTROLLED SCOPE EXTENSION",
        f"config/tfl_output_catalog.yaml controlled_in_scope ({approved_extensions} approved extensions)",
        "Produced IDs outside the historical SAP ID list carry explicit SAP-section bases",
        "DISPOSITIONED_IN_CONTROLLED_CATALOG",
        "Keep each extension basis current and prohibit unlisted outputs.",
    )
    return rows


def main() -> int:
    rows = build_rows()
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    confirmed = sum(row["status"] == "CONFIRMED" for row in rows)
    print(f"Wrote {len(rows)} register entries ({confirmed} confirmed cleanup findings)")
    return 1 if confirmed else 0


if __name__ == "__main__":
    raise SystemExit(main())
