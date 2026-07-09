#!/usr/bin/env python3
"""Build the explicit orphan, dangling-reference, and dead-code register."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SEQ = ROOT / "08_submission_package/ectd/0000"
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
            "Not present as an xlink:href in 08_submission_package/ectd/0000/index.xml",
            "CONFIRMED", "Delete stale payload and rebuild a single atomic full or preview sequence.")

discon_listing = ROOT / "05_outputs/tfl/output/listings/L-01-1_Discontinuations.txt"
if discon_listing.exists():
    discon_text = discon_listing.read_text(encoding="utf-8", errors="replace")
    if "L_discon.sas" in discon_text and not (ROOT / "04_analysis_datasets/programs/sas/L_discon.sas").exists():
        add("DANGLING REFERENCE", "L_discon.sas",
            "05_outputs/tfl/output/listings/L-01-1_Discontinuations.txt cites missing producer L_discon.sas",
            "CONFIRMED", "Remove placeholder listing or generate it from an existing, validated program.")

manual = [
    ("ARCHIVED DEAD CODE", "tools/archive/dev_snippets/GIT_RESCUE.sas", "Moved from programs/sas/utilities/ during factory cleanup 2026-07-09", "ARCHIVED", "Keep out of active program paths; see tools/archive/README.md."),
    ("ARCHIVED DEAD CODE", "tools/archive/dev_snippets/GIT_PUSH.sas", "Moved from programs/sas/utilities/ during factory cleanup 2026-07-09", "ARCHIVED", "Keep out of active program paths; see tools/archive/README.md."),
    ("ARCHIVED HISTORICAL", "tools/archive/define_oneoffs/remediate_sdtm_define.py", "Moved from 03_metadata/define/ during factory cleanup 2026-07-09", "ARCHIVED", "Not on DAG; restore only for deliberate one-off define work."),
    ("ARCHIVED MIGRATION", "tools/archive/migration/build_spec_seed.R", "Moved from 03_metadata/adam/; one-time ADaM_spec bootstrap", "ARCHIVED", "Do not re-run; would re-create define→spec circularity."),

    ("MANUAL PREREQUISITE", "01_source_data/reconstruct_cbzp_arm.R", "00_governance/REPRODUCIBILITY.md:75; not in release DAG", "DOCUMENTED BUT UNORCHESTRATED", "Pin/run before release and bind output hashes to the release record."),
    ("MANUAL PREREQUISITE", "01_source_data/reconstruct_cbzp_guyot.R", "Sourced by reconstruct_cbzp_arm.R only", "DOCUMENTED BUT UNORCHESTRATED", "Pin digitization inputs and bind reconstructed output hashes."),
    ("MANUAL PREREQUISITE", "01_source_data/export_cbzp_xpt.R", "Invoked by _oda_render_tfl.py, not main DAG", "DOCUMENTED BUT OUT-OF-DAG", "Integrate the bridge into the validated release DAG."),
    ("OUT-OF-DAG CAPABILITY DEMO", "platform/_oda_render_tfl.py", "Renders 05_outputs/tfl/output/figures/sas/* outside study_manifest; package_ectd copies companions", "CLASSIFIED_OUT_OF_DAG", "Keep as capability demo; not current-run release spine evidence. Documented in platform/README.md."),
    ("DELIVERY ORPHAN", "04_analysis_datasets/datasetjson/", "No package_ectd.py consumer; built on DAG as additive layer", "CLASSIFIED_ADDITIVE", "Exploratory/pilot transport; not Module 5 primary package path. See folder README."),
    ("DELIVERY ORPHAN", "05_outputs/ars/", "No package_ectd.py consumer; built on DAG as additive layer", "CLASSIFIED_ADDITIVE", "ARS pilot outputs; not eCTD primary path. See folder README."),
    ("DELIVERY ORPHAN", "03_metadata/usdm/", "No package_ectd.py consumer; built on DAG as additive layer", "CLASSIFIED_ADDITIVE", "USDM pilot; not eCTD primary path. See folder README."),
    ("OUT-OF-BAND OUTPUT", "04_analysis_datasets/datasetjson/**/*.ndjson", "Requires --ndjson; pipeline invokes JSON path only", "CONFIRMED", "Orchestrate and validate NDJSON or remove stale files."),
    ("DEFERRED SAP FULL-CATALOG TFLS", "config/tfl_output_catalog.yaml deferred_not_in_scope (21 IDs)", "SAP v4 full catalog vs controlled release scope", "DISPOSITIONED_IN_CONTROLLED_CATALOG", "Implement under approved shells+QC or keep deferred; gate is bijective controlled scope, not silent absence."),
    ("APPROVED TFL EXTENSIONS", "config/tfl_output_catalog.yaml controlled_in_scope disposition=approved_extension", "Safety/disposition/PSA displays with SAP v4 section basis", "DISPOSITIONED_IN_CONTROLLED_CATALOG", "Keep extension basis current; do not add unlisted outputs."),
]

# Dynamic: orchestrated generators / third-engine QC from config/study_manifest.yaml.
manifest_text = (ROOT / "config/study_manifest.yaml").read_text(encoding="utf-8")
if "gen_adam_labels.R" in manifest_text:
    add(
        "ORCHESTRATED GENERATOR",
        "platform/gen_adam_labels.R",
        "Invoked by config/study_manifest.yaml infrastructure_stages.pre (ADaM Spec Label/Order Artifacts)",
        "RESOLVED_IN_DAG",
        "No action; keep label/order artifacts gated before SAS/R derivation stages.",
    )
else:
    add(
        "UNORCHESTRATED REQUIRED GENERATOR",
        "platform/gen_adam_labels.R",
        "No invocation in config/study_manifest.yaml; labels may drift from ADaM_spec.xlsx",
        "CONFIRMED",
        "Run it before SAS/R derivations and gate clean-tree/hash parity of generated labels.",
    )

for path, label, note in [
    ("04_analysis_datasets/programs/r/admiral_adsl.R", "Admiral ADSL Re-derivation", "gated third-engine T1 track"),
    ("04_analysis_datasets/programs/r/admiral_adtte.R", "Admiral ADTTE Re-derivation (OS/PFS)", "gated third-engine T1 track"),
    ("06_qc_evidence/reconciliation/admiral_reconcile.R", "Admiral Core Reconciliation", "gated third-engine T1 track"),
    ("06_qc_evidence/reconciliation/figure_data_reconcile.R", "Figure-Data Reconciliation (SAS vs R)", "non-gated; not_available if SAS figure CSVs absent"),
]:
    if path.split("/")[-1] in manifest_text or path in manifest_text:
        add(
            "ORCHESTRATED QC",
            path,
            f"Invoked by config/study_manifest.yaml post-stage ({label}); {note}",
            "RESOLVED_IN_DAG",
            "Keep orchestrated; fail release on recon non-PASS; treat not_available as incomplete SAS figure evidence, not PASS.",
        )
    else:
        add(
            "UNORCHESTRATED QC",
            path,
            "Standalone only; absent from study_manifest DAG",
            "CONFIRMED",
            "Add the run and its reconciliation gate to the release DAG or remove readiness claims.",
        )

for item in manual:
    add(*item)

out = ROOT / "06_qc_evidence/audit/orphans_dangling_deadcode.csv"
with out.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print(f"Wrote {len(rows)} register entries ({sum(r['type'].startswith('ORPHAN') for r in rows)} unindexed XPT payloads)")
