#!/usr/bin/env python3
"""Build the explicit orphan, dangling-reference, and dead-code register."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEQ = ROOT / "11_ectd/0000"
index_text = (SEQ / "index.xml").read_text(encoding="utf-8")
hrefs = {m.replace("\\", "/") for m in re.findall(r'xlink:href="([^"]+)"', index_text)}
rows = []


def add(kind, path, evidence, status, remediation):
    rows.append({"type": kind, "path_or_reference": path, "evidence": evidence,
                 "status": status, "remediation": remediation})


for path in sorted((SEQ / "m5").rglob("*.xpt")):
    rel = path.relative_to(SEQ).as_posix()
    if rel not in hrefs:
        add("ORPHAN/UNINDEXED PAYLOAD", path.relative_to(ROOT).as_posix(),
            "Not present as an xlink:href in 11_ectd/0000/index.xml",
            "CONFIRMED", "Delete stale payload and rebuild a single atomic full or preview sequence.")

discon_listing = ROOT / "09_tfl/output/listings/L-01-1_Discontinuations.txt"
if discon_listing.exists():
    discon_text = discon_listing.read_text(encoding="utf-8", errors="replace")
    if "L_discon.sas" in discon_text and not (ROOT / "02_production_sas/L_discon.sas").exists():
        add("DANGLING REFERENCE", "L_discon.sas",
            "09_tfl/output/listings/L-01-1_Discontinuations.txt cites missing producer L_discon.sas",
            "CONFIRMED", "Remove placeholder listing or generate it from an existing, validated program.")

manual = [
    ("DEAD/UNREFERENCED CODE", "02_production_sas/utilities/GIT_RESCUE.sas", "06_telemetry/REPO_AUDIT_2026-06-21.md:154-158", "CONFIRMED MANUAL DEV SNIPPET", "Move to a documented developer-tools area or remove."),
    ("DEAD/UNREFERENCED CODE", "06_telemetry/remediate_sdtm_define.py", "06_telemetry/REPO_AUDIT_2026-06-21.md:154-158", "CONFIRMED HISTORICAL/MANUAL", "Archive outside the validated pipeline or document and test its intended use."),

    ("UNORCHESTRATED QC", "05_reconciliation/figure_data_reconcile.R", "README claim but no manifest/CI invocation", "CONFIRMED", "Invoke for every release or withdraw the QC claim."),
    ("MANUAL PREREQUISITE", "01_raw_source/reconstruct_cbzp_arm.R", "REPRODUCIBILITY.md:75; not in release DAG", "DOCUMENTED BUT UNORCHESTRATED", "Pin/run before release and bind output hashes to the release record."),
    ("MANUAL PREREQUISITE", "01_raw_source/reconstruct_cbzp_guyot.R", "Sourced by reconstruct_cbzp_arm.R only", "DOCUMENTED BUT UNORCHESTRATED", "Pin digitization inputs and bind reconstructed output hashes."),
    ("MANUAL PREREQUISITE", "01_raw_source/export_cbzp_xpt.R", "Invoked by _oda_render_tfl.py, not main DAG", "DOCUMENTED BUT OUT-OF-DAG", "Integrate the bridge into the validated release DAG."),
    ("OUT-OF-DAG CAPABILITY DEMO", "06_telemetry/_oda_render_tfl.py", "Renders 09_tfl/output/figures/sas/* outside study_manifest; package_ectd copies companions", "CONFIRMED", "Integrate into DAG or keep classified as historical capability demo (not current-run release evidence)."),
    ("ONE-TIME/HISTORICAL", "00_specifications/build_spec_seed.R", "Header identifies one-time migration", "DOCUMENTED", "Archive as migration evidence; do not treat as an active generator."),
    ("DELIVERY ORPHAN", "10_datasetjson/", "No package_ectd.py consumer", "CONFIRMED", "Classify as exploratory/pilot output or add a regulator-approved delivery route."),
    ("DELIVERY ORPHAN", "12_ars/", "No package_ectd.py consumer", "CONFIRMED", "Add a defined delivery location and complete ARS coverage/schema validation."),
    ("DELIVERY ORPHAN", "13_usdm/", "No package_ectd.py consumer", "CONFIRMED", "Classify as exploratory or add a defined delivery route and official schema validation."),
    ("OUT-OF-BAND OUTPUT", "10_datasetjson/**/*.ndjson", "Requires --ndjson; pipeline invokes JSON path only", "CONFIRMED", "Orchestrate and validate NDJSON or remove stale files."),
    ("DEFERRED SAP FULL-CATALOG TFLS", "tfl_output_catalog.yaml deferred_not_in_scope (21 IDs)", "SAP v4 full catalog vs controlled release scope", "DISPOSITIONED_IN_CONTROLLED_CATALOG", "Implement under approved shells+QC or keep deferred; gate is bijective controlled scope, not silent absence."),
    ("APPROVED TFL EXTENSIONS", "tfl_output_catalog.yaml controlled_in_scope disposition=approved_extension", "Safety/disposition/PSA displays with SAP v4 section basis", "DISPOSITIONED_IN_CONTROLLED_CATALOG", "Keep extension basis current; do not add unlisted outputs."),
]

# Dynamic: orchestrated generators / third-engine QC from study_manifest.yaml.
manifest_text = (ROOT / "study_manifest.yaml").read_text(encoding="utf-8")
if "gen_adam_labels.R" in manifest_text:
    add(
        "ORCHESTRATED GENERATOR",
        "06_telemetry/gen_adam_labels.R",
        "Invoked by study_manifest.yaml infrastructure_stages.pre (ADaM Spec Label/Order Artifacts)",
        "RESOLVED_IN_DAG",
        "No action; keep label/order artifacts gated before SAS/R derivation stages.",
    )
else:
    add(
        "UNORCHESTRATED REQUIRED GENERATOR",
        "06_telemetry/gen_adam_labels.R",
        "No invocation in study_manifest.yaml; labels may drift from ADaM_spec.xlsx",
        "CONFIRMED",
        "Run it before SAS/R derivations and gate clean-tree/hash parity of generated labels.",
    )

for path, label in [
    ("03_validation_r/admiral_adsl.R", "Admiral ADSL Re-derivation"),
    ("03_validation_r/admiral_adtte.R", "Admiral ADTTE Re-derivation (OS/PFS)"),
    ("05_reconciliation/admiral_reconcile.R", "Admiral Core Reconciliation"),
]:
    if path.split("/")[-1] in manifest_text or path in manifest_text:
        add(
            "ORCHESTRATED QC",
            path,
            f"Invoked by study_manifest.yaml post-stage ({label}); gated third-engine T1 track",
            "RESOLVED_IN_DAG",
            "Keep orchestrated; fail release on admiral recon non-PASS / stale evidence.",
        )
    else:
        add(
            "UNORCHESTRATED QC",
            path,
            "Standalone only; absent from study_manifest DAG",
            "CONFIRMED",
            "Add the third-track run and its reconciliation gate to the release DAG or remove readiness claims.",
        )

for item in manual:
    add(*item)

out = ROOT / "audit/orphans_dangling_deadcode.csv"
with out.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print(f"Wrote {len(rows)} register entries ({sum(r['type'].startswith('ORPHAN') for r in rows)} unindexed XPT payloads)")
