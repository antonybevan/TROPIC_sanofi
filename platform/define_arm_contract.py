#!/usr/bin/env python3
"""Validate Path A endpoint semantics and evidence boundaries in ADaM ARM."""

from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


NS = {
    "odm": "http://www.cdisc.org/ns/odm/v1.3",
    "def": "http://www.cdisc.org/ns/def/v2.1",
    "arm": "http://www.cdisc.org/ns/arm/v1.0",
}


def _translated(node: ET.Element | None) -> str:
    if node is None:
        return ""
    text = node.find("./odm:Description/odm:TranslatedText", NS)
    return "".join(text.itertext()).strip() if text is not None else ""


def evaluate(path: Path) -> list[dict[str, object]]:
    """Return named pass/fail checks for the governed Path A ARM contract."""
    root = ET.parse(path).getroot()
    checks: list[dict[str, object]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    ttpain_where = root.find(
        ".//def:WhereClauseDef[@OID='WC.ADTTE.PARAMCD.EQ.TTPAIN']",
        NS,
    )
    add(
        "define.where.TTPAIN",
        ttpain_where is not None,
        "Define-XML must carry the TTPAIN ARM where-clause",
    )
    supporting_where_oids = (
        "WC.ADRS.PARAMCD.EQ.PSARESP",
        "WC.ADRS.PARAMCD.EQ.OBJRESP",
        "WC.ADEX.PARAMCD.EQ.RDIDL",
    )
    missing_where = [
        oid
        for oid in supporting_where_oids
        if root.find(f".//def:WhereClauseDef[@OID='{oid}']", NS) is None
    ]
    add(
        "define.where.controlled_tables",
        not missing_where,
        "missing where-clauses: " + ", ".join(missing_where)
        if missing_where
        else "response and Optimus clauses present",
    )

    adtte_description = _translated(
        root.find(".//odm:ItemGroupDef[@OID='IG.ADTTE']", NS)
    )
    add(
        "define.ADTTE_description",
        all(
            token in adtte_description
            for token in ("OS", "PFS", "TTPSA", "TTUMOR", "TTPAIN", "TTSAE")
        ),
        "ADTTE description must enumerate the current controlled endpoint set",
    )

    survival_description = _translated(
        root.find(".//arm:ResultDisplay[@OID='RD.EFFICACY.SURVIVAL']", NS)
    )
    add(
        "define.arm_survival_truth",
        all(
            token in survival_description
            for token in ("SAP v4.0", "TFL-only", "non-confirmatory")
        ),
        "survival ARM must disclose current SAP authority and CbzP evidence boundary",
    )

    secondary_description = _translated(
        root.find(".//arm:ResultDisplay[@OID='RD.EFFICACY.SECONDARY']", NS)
    )
    add(
        "define.arm_secondary_truth",
        all(
            token in secondary_description
            for token in ("SAP v4.0", "TTPSA", "TTUMOR", "TTPAIN", "ITT", "circular")
        ),
        "secondary ARM must match SAP v4.0, ITT populations, and synthetic limitations",
    )

    ttumor_description = _translated(
        root.find(".//arm:AnalysisResult[@OID='AR.TTUMOR.COX']", NS)
    )
    add(
        "define.arm_TTUMOR_ITT",
        "ITT" in ttumor_description
        and "measurable-disease subpopulation" not in ttumor_description.lower(),
        "TTUMOR ARM must be ITT-primary and must not retain the superseded subset claim",
    )

    ttpain_result = root.find(
        ".//arm:AnalysisResult[@OID='AR.TTPAIN.COX']",
        NS,
    )
    ttpain_ref = (
        ttpain_result.find(
            "./arm:AnalysisDatasets/arm:AnalysisDataset/def:WhereClauseRef",
            NS,
        )
        if ttpain_result is not None
        else None
    )
    add(
        "define.arm_TTPAIN_result",
        ttpain_ref is not None
        and ttpain_ref.get("WhereClauseOID") == "WC.ADTTE.PARAMCD.EQ.TTPAIN",
        "TTPAIN requires a dedicated ARM result bound to the TTPAIN where-clause",
    )

    missing_survival_covariates: list[str] = []
    for result_oid in ("AR.OS.COX", "AR.PFS.COX"):
        result = root.find(f".//arm:AnalysisResult[@OID='{result_oid}']", NS)
        declared = {
            variable.get("ItemOID", "")
            for variable in (
                result.findall(
                    "./arm:AnalysisDatasets/arm:AnalysisDataset"
                    "[@ItemGroupOID='IG.ADSL']/arm:AnalysisVariable",
                    NS,
                )
                if result is not None
                else []
            )
        }
        required = {"IT.ADSL.ECOGBL", "IT.ADSL.MEASDISF", "IT.ADSL.TRT01P"}
        if not required.issubset(declared):
            missing_survival_covariates.append(result_oid)
    add(
        "define.arm_survival_covariates",
        not missing_survival_covariates,
        "missing ADSL covariates: " + ", ".join(missing_survival_covariates)
        if missing_survival_covariates
        else "OS/PFS ADSL stratification variables declared",
    )

    displays = root.findall(".//arm:ResultDisplay", NS)
    results = root.findall(".//arm:AnalysisResult", NS)
    controlled_result_oids = (
        "AR.PSA.RESPONSE",
        "AR.OBJECTIVE.RESPONSE",
        "AR.PAIN.RESPONSE",
        "AR.OBJECTIVE.RESPONSE.EVALUABLE",
        "AR.RDI.DISTRIBUTION",
        "AR.ANC.GCSF",
        "AR.BENEFIT.RISK.RDI",
    )
    missing_results = [
        oid
        for oid in controlled_result_oids
        if root.find(f".//arm:AnalysisResult[@OID='{oid}']", NS) is None
    ]
    add(
        "define.arm_controlled_table_results",
        not missing_results,
        "missing analysis results: " + ", ".join(missing_results)
        if missing_results
        else "controlled response and Optimus table results present",
    )
    expected_name_tokens = {
        "RD.EFFICACY.SURVIVAL": ("F-11-1", "F-11-2"),
        "RD.EFFICACY.SECONDARY": ("T-11-6", "T-11-7", "T-11-8"),
        "RD.EFFICACY.RESPONSE": ("T-11-3", "T-11-4", "T-11-5", "T-11-8b"),
        "RD.OPTIMUS.TABLES": ("T-17-1", "T-17-2", "T-17-4"),
        "RD.SAFETY.TEAE": ("T-20-1", "T-20-2"),
        "RD.SAFETY.LABSHIFT": ("T-21-1", "T-21-2"),
    }
    stale_names = []
    for oid, tokens in expected_name_tokens.items():
        display = root.find(f".//arm:ResultDisplay[@OID='{oid}']", NS)
        name = display.get("Name", "") if display is not None else ""
        if not all(token in name for token in tokens):
            stale_names.append(oid)
    add(
        "define.arm_TFL_name_binding",
        not stale_names,
        "display names missing TFL IDs: " + ", ".join(stale_names)
        if stale_names
        else "controlled display names bind physical TFL IDs",
    )
    add(
        "define.arm_coverage",
        len(displays) >= 10 and len(results) >= 18,
        f"result_displays={len(displays)} analysis_results={len(results)}",
    )

    undisclosed = [
        display.get("OID", "")
        for display in displays
        if "Path A limitation:" not in _translated(display)
    ]
    add(
        "define.arm_CbzP_disclosure",
        not undisclosed,
        "missing disclosure: " + ", ".join(undisclosed) if undisclosed else "all displays",
    )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "define_xml",
        nargs="?",
        type=Path,
        default=Path("03_metadata/define/define.xml"),
    )
    args = parser.parse_args()
    try:
        checks = evaluate(args.define_xml)
    except (ET.ParseError, OSError) as exc:
        print(f"Define ARM contract: FAIL - {exc}")
        return 1

    failures = [check for check in checks if not check["ok"]]
    print(f"Define ARM contract: {'PASS' if not failures else 'FAIL'}")
    for check in checks:
        print(
            f"  {'OK' if check['ok'] else 'FAIL'}: "
            f"{check['name']} - {check['detail']}"
        )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
