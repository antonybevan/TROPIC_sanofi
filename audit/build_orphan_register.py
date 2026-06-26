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

manual = [
    ("DANGLING REFERENCE", "L_discon.sas", "09_tfl/output/listings/L-01-1_Discontinuations.txt:19; file absent", "CONFIRMED", "Remove placeholder listing and generate it from an existing, validated program."),
    ("DEAD/UNREFERENCED CODE", "02_production_sas/utilities/GIT_RESCUE.sas", "06_telemetry/REPO_AUDIT_2026-06-21.md:154-158", "CONFIRMED MANUAL DEV SNIPPET", "Move to a documented developer-tools area or remove."),
    ("DEAD/UNREFERENCED CODE", "06_telemetry/remediate_sdtm_define.py", "06_telemetry/REPO_AUDIT_2026-06-21.md:154-158", "CONFIRMED HISTORICAL/MANUAL", "Archive outside the validated pipeline or document and test its intended use."),
    ("UNORCHESTRATED REQUIRED GENERATOR", "06_telemetry/gen_adam_labels.R", "No invocation in study_manifest.yaml/.github; labels are stale", "CONFIRMED", "Run it before SAS/R derivations and gate clean-tree/hash parity of generated labels."),
    ("UNORCHESTRATED QC", "03_validation_r/admiral_adsl.R", "Standalone only; absent from 22-stage DAG", "CONFIRMED", "Add the third-track run and its reconciliation gate to the release DAG or remove readiness claims."),
    ("UNORCHESTRATED QC", "03_validation_r/admiral_adtte.R", "Standalone only; absent from 22-stage DAG", "CONFIRMED", "Add the third-track run and its reconciliation gate to the release DAG or remove readiness claims."),
    ("UNORCHESTRATED QC", "05_reconciliation/admiral_reconcile.R", "Standalone only; absent from 22-stage DAG", "CONFIRMED", "Add to the release DAG and fail on divergence."),
    ("UNORCHESTRATED QC", "05_reconciliation/figure_data_reconcile.R", "README claim but no manifest/CI invocation", "CONFIRMED", "Invoke for every release or withdraw the QC claim."),
    ("MANUAL PREREQUISITE", "01_raw_source/reconstruct_cbzp_arm.R", "REPRODUCIBILITY.md:75; not in release DAG", "DOCUMENTED BUT UNORCHESTRATED", "Pin/run before release and bind output hashes to the release record."),
    ("MANUAL PREREQUISITE", "01_raw_source/reconstruct_cbzp_guyot.R", "Sourced by reconstruct_cbzp_arm.R only", "DOCUMENTED BUT UNORCHESTRATED", "Pin digitization inputs and bind reconstructed output hashes."),
    ("MANUAL PREREQUISITE", "01_raw_source/export_cbzp_xpt.R", "Invoked by _oda_render_tfl.py, not main DAG", "DOCUMENTED BUT OUT-OF-DAG", "Integrate the bridge into the validated release DAG."),
    ("ONE-TIME/HISTORICAL", "00_specifications/build_spec_seed.R", "Header identifies one-time migration", "DOCUMENTED", "Archive as migration evidence; do not treat as an active generator."),
    ("DELIVERY ORPHAN", "10_datasetjson/", "No package_ectd.py consumer", "CONFIRMED", "Classify as exploratory/pilot output or add a regulator-approved delivery route."),
    ("DELIVERY ORPHAN", "12_ars/", "No package_ectd.py consumer", "CONFIRMED", "Add a defined delivery location and complete ARS coverage/schema validation."),
    ("DELIVERY ORPHAN", "13_usdm/", "No package_ectd.py consumer", "CONFIRMED", "Classify as exploratory or add a defined delivery route and official schema validation."),
    ("OUT-OF-BAND OUTPUT", "10_datasetjson/**/*.ndjson", "Requires --ndjson; pipeline invokes JSON path only", "CONFIRMED", "Orchestrate and validate NDJSON or remove stale files."),
    ("SPECIFIED-BUT-NOT-PRODUCED", "TFL catalog (21 IDs)", "TROPIC_SAP_v3.0.docx Table 21 vs 09_tfl/output", "CONFIRMED", "Implement or formally amend/approve the SAP output catalog."),
    ("PRODUCED-BUT-NOT-SPECIFIED", "TFL catalog (9 IDs)", "09_tfl/output vs TROPIC_SAP_v3.0.docx Table 21", "CONFIRMED", "Add approved SAP basis or remove outputs from submission."),
    ("PRODUCED-BUT-NOT-SPECIFIED", "17 SDTM datasets", "metadata_data_drift.csv", "CONFIRMED", "Add complete Define-XML metadata or stop packaging the datasets."),
]
for item in manual:
    add(*item)

out = ROOT / "audit/orphans_dangling_deadcode.csv"
with out.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print(f"Wrote {len(rows)} register entries ({sum(r['type'].startswith('ORPHAN') for r in rows)} unindexed XPT payloads)")
