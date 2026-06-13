"""
add_arm_metadata.py — add Analysis Results Metadata (ARM v1.0) to define.xml for the two
headline efficacy analyses (OS, PFS), referencing the real stratified Cox / log-rank derivation.

Adds the arm: namespace to the ODM root and an <arm:AnalysisResultDisplays> block inside
MetaDataVersion. Every reference (ParameterOID, ItemGroupOID, def:WhereClauseRef, AnalysisVariable)
points at an existing object, so validate_define.py referential integrity stays green.

Run:  python3 07_define_xml/add_arm_metadata.py   (idempotent: re-adding is a no-op)
"""
import os
from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "define.xml")
ODM = "http://www.cdisc.org/ns/odm/v1.3"
DEF = "http://www.cdisc.org/ns/def/v2.1"
ARM = "http://www.cdisc.org/ns/arm/v1.0"
XML = "http://www.w3.org/XML/1998/namespace"


def q(ns, ln): return etree.QName(ns, ln)


def _desc(parent, text):
    de = etree.SubElement(parent, q(ODM, "Description"))
    tt = etree.SubElement(de, q(ODM, "TranslatedText")); tt.set(q(XML, "lang"), "en")
    tt.text = text
    return de


def _analysis_result(parent, oid, wc_oid, title, code):
    ar = etree.SubElement(parent, q(ARM, "AnalysisResult"))
    ar.set("OID", oid)
    ar.set("ParameterOID", "IT.ADTTE.PARAMCD")
    ar.set("AnalysisReason", "PRE-SPECIFIED IN SAP")
    ar.set("AnalysisPurpose", "PRIMARY OUTCOME MEASURE" if "OS" in oid else "SECONDARY OUTCOME MEASURE")
    _desc(ar, title)
    ads = etree.SubElement(ar, q(ARM, "AnalysisDatasets"))
    ad = etree.SubElement(ads, q(ARM, "AnalysisDataset")); ad.set("ItemGroupOID", "IG.ADTTE")
    etree.SubElement(ad, q(DEF, "WhereClauseRef")).set("WhereClauseOID", wc_oid)
    for v in ("IT.ADTTE.AVAL", "IT.ADTTE.CNSR", "IT.ADTTE.TRT01P"):
        etree.SubElement(ad, q(ARM, "AnalysisVariable")).set("ItemOID", v)
    apc = etree.SubElement(ar, q(ARM, "AnalysisProgrammingCode"))
    apc.set("Context", "R 4.6.0 (survival::coxph / survdiff)")
    etree.SubElement(apc, q(ARM, "Code")).text = code


def main():
    tree = etree.parse(SRC)
    root = tree.getroot()
    if ARM in (root.nsmap or {}).values():
        print("  ARM already present — no-op."); return

    # Rebuild root to add the arm: prefix to the namespace map (lxml nsmap is immutable).
    nsmap = dict(root.nsmap); nsmap["arm"] = ARM
    new = etree.Element(root.tag, nsmap=nsmap)
    for k, v in root.attrib.items():
        new.set(k, v)
    for child in list(root):
        new.append(child)

    mdv = new.find(f"{{{ODM}}}MetaDataVersion")
    ard = etree.SubElement(mdv, q(ARM, "AnalysisResultDisplays"))
    rd = etree.SubElement(ard, q(ARM, "ResultDisplay")); rd.set("OID", "RD.EFFICACY.SURVIVAL")
    rd.set("Name", "Primary & Secondary Survival Analyses")
    _desc(rd, "Stratified Cox proportional-hazards and log-rank analyses of OS and PFS "
              "(CbzP vs MP), stratified by ECOGBL and MEASDISF, per SAP v3.0 §5.1.")
    _analysis_result(
        rd, "AR.OS.COX", "WC.ADTTE.PARAMCD.EQ.OS",
        "Overall Survival — stratified Cox HR and stratified log-rank p-value, CbzP vs MP.",
        "coxph(Surv(AVAL, 1 - CNSR) ~ TRT01P + strata(ECOGBL, MEASDISF), data = adtte[PARAMCD=='OS'])")
    _analysis_result(
        rd, "AR.PFS.COX", "WC.ADTTE.PARAMCD.EQ.PFS",
        "Progression-Free Survival — stratified Cox HR and stratified log-rank p-value, CbzP vs MP.",
        "coxph(Surv(AVAL, 1 - CNSR) ~ TRT01P + strata(ECOGBL, MEASDISF), data = adtte[PARAMCD=='PFS'])")

    out = etree.tostring(new, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    out = out.replace(b"?>\n", b'?>\n<?xml-stylesheet type="text/xsl" href="define2-1.xsl"?>\n', 1)
    with open(SRC, "wb") as f:
        f.write(out)
    print("  added ARM: 1 ResultDisplay, 2 AnalysisResults (OS, PFS).")


if __name__ == "__main__":
    main()
