#!/usr/bin/env python3
"""
uplift_define_34.py — sync define_sdtm.xml to the SDTMIG 3.4 uplifted data.

Surgical, deterministic update of 07_define_xml/define_sdtm.xml:
  * Standards: SDTMIG 3.1.1 -> 3.4 ; CT 2024-03-29 -> 2026-03-27 (both refs +
    every def:StandardOID + the MetaDataVersion OID).
  * Touched domains (DM, AE, EX, DS, VS, SUPPDM) + new IG.TS, IG.TA: rebuild the
    ItemRef list to the *actual* uplifted column order/type/length/label (the
    define had drifted — IG.AE declared 41 vars for a 31-col dataset, IG.DM
    declared phantom ARM2/ARMA/ITT/PPROT/... absent from data). Existing
    CodeListRef/Origin metadata on surviving variables is preserved.
  * Untouched domains (CM, LB, LS, PN, SUPP*) keep their blocks (standard ref
    bumped only).
Column metadata is embedded (captured from the uplifted XPT) so the run is
deterministic and needs only lxml.
"""
import os
from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "define_sdtm.xml")
ODM = "http://www.cdisc.org/ns/odm/v1.3"; DEF = "http://www.cdisc.org/ns/def/v2.1"
XLINK = "http://www.w3.org/1999/xlink"; XML = "http://www.w3.org/XML/1998/namespace"
def o(t): return f"{{{ODM}}}{t}"
def d(t): return f"{{{DEF}}}{t}"

# (name, datatype, length) in submission order — captured from .core_run/sdtm34/*.xpt
COLS = {
 "DM": [("STUDYID","text",8),("DOMAIN","text",2),("USUBJID","text",20),("SUBJID","text",10),
        ("RFSTDTC","text",19),("RFENDTC","text",19),("AGE","integer",8),("AGEU","text",6),
        ("SEX","text",1),("RACE","text",40),("ARM","text",40),("ARMCD","text",20),
        ("ACTARM","text",40),("ACTARMCD","text",20)],
 "AE": [("STUDYID","text",8),("DOMAIN","text",2),("USUBJID","text",20),("AESEQ","integer",8),
        ("AESPID","text",10),("AEREFID","text",10),("AETERM","text",200),("AEDECOD","text",100),
        ("AEBODSYS","text",100),("AESOC","text",100),("AESER","text",1),("AESCONG","text",1),
        ("AESDISAB","text",1),("AESDTH","text",1),("AESHOSP","text",1),("AESLIFE","text",1),
        ("AESMIE","text",1),("AEACN","text",40),("AECONTRT","text",1),("AEREL","text",20),
        ("AEPATT","text",40),("AEOUT","text",40),("AETOXGR","text",2),("EPOCH","text",20),
        ("VISITNUM","integer",8),("VISIT","text",40)],
 "EX": [("STUDYID","text",8),("DOMAIN","text",2),("USUBJID","text",20),("EXSEQ","integer",8),
        ("EXTRT","text",40),("EXLOT","text",40),("EXDOSE","float",8),("EXDOSU","text",10),
        ("EXDOSFRM","text",20),("EXROUTE","text",20),("EPOCH","text",20),("VISITNUM","integer",8),
        ("VISIT","text",40),("EXSTDTC","text",19),("EXENDTC","text",19),("EXSTDY","integer",8),
        ("EXENDY","integer",8)],
 "DS": [("STUDYID","text",8),("DOMAIN","text",2),("USUBJID","text",20),("DSSEQ","integer",8),
        ("DSTERM","text",200),("DSDECOD","text",40),("DSCAT","text",40),("DSSCAT","text",40),
        ("EPOCH","text",20),("VISITNUM","integer",8),("VISIT","text",40)],
 "VS": [("STUDYID","text",8),("DOMAIN","text",2),("USUBJID","text",20),("VSSEQ","integer",8),
        ("VSTESTCD","text",8),("VSTEST","text",40),("VSORRES","text",20),("VSORRESU","text",20),
        ("VSSTRESC","text",20),("VSSTRESN","float",8),("VSSTRESU","text",20),("VSMETHOD","text",40),
        ("VSBLFL","text",1),("VSDRVFL","text",1),("EPOCH","text",20),("VISITNUM","integer",8),
        ("VISIT","text",40),("VSDTC","text",19),("VSDY","integer",8)],
 "SUPPDM": [("STUDYID","text",8),("RDOMAIN","text",2),("USUBJID","text",20),("IDVAR","text",8),
        ("IDVARVAL","text",8),("QNAM","text",8),("QLABEL","text",40),("QVAL","text",40),
        ("QORIG","text",40),("QEVAL","text",40)],
 "SUPPAE": [("STUDYID","text",8),("RDOMAIN","text",2),("USUBJID","text",20),("IDVAR","text",8),
        ("IDVARVAL","text",8),("QNAM","text",8),("QLABEL","text",40),("QVAL","text",40),
        ("QORIG","text",40),("QEVAL","text",40)],
 "SUPPDS": [("STUDYID","text",8),("RDOMAIN","text",2),("USUBJID","text",20),("IDVAR","text",8),
        ("IDVARVAL","text",8),("QNAM","text",8),("QLABEL","text",40),("QVAL","text",40),
        ("QORIG","text",40),("QEVAL","text",40)],
 "TS": [("STUDYID","text",8),("DOMAIN","text",2),("TSSEQ","integer",8),("TSPARMCD","text",8),
        ("TSPARM","text",40),("TSVAL","text",200)],
 "TA": [("STUDYID","text",8),("DOMAIN","text",2),("ARMCD","text",20),("ARM","text",40),
        ("TAETORD","integer",8),("ETCD","text",8),("ELEMENT","text",40),("TABRANCH","text",200),
        ("EPOCH","text",20)],
}
# Canonical, title-cased SDTM labels (<=40 chars for XPT v5)
LBL = {
 "STUDYID":"Study Identifier","DOMAIN":"Domain Abbreviation","USUBJID":"Unique Subject Identifier",
 "SUBJID":"Subject Identifier for the Study","RFSTDTC":"Subject Reference Start Date/Time",
 "RFENDTC":"Subject Reference End Date/Time","AGE":"Age","AGEU":"Age Units","SEX":"Sex","RACE":"Race",
 "ARM":"Description of Planned Arm","ARMCD":"Planned Arm Code","ACTARM":"Description of Actual Arm",
 "ACTARMCD":"Actual Arm Code","EPOCH":"Epoch","VISITNUM":"Visit Number","VISIT":"Visit Name",
 "AESEQ":"Sequence Number","AESPID":"Sponsor-Defined Identifier","AEREFID":"Reference ID",
 "AETERM":"Reported Term for the Adverse Event","AEDECOD":"Dictionary-Derived Term",
 "AEBODSYS":"Body System or Organ Class","AESOC":"Primary System Organ Class","AESER":"Serious Event",
 "AESCONG":"Congenital Anomaly or Birth Defect","AESDISAB":"Persist or Signif Disability/Incapacity",
 "AESDTH":"Results in Death","AESHOSP":"Requires or Prolongs Hospitalization",
 "AESLIFE":"Is Life Threatening","AESMIE":"Other Medically Important Serious Event",
 "AEACN":"Action Taken with Study Treatment","AECONTRT":"Concomitant or Additional Trtmnt Given",
 "AEREL":"Causality","AEPATT":"Pattern of Adverse Event","AEOUT":"Outcome of Adverse Event",
 "AETOXGR":"Standard Toxicity Grade","AESTWK":"Study Week of Start of Adverse Event",
 "AEENWK":"Study Week of End of Adverse Event","AESTWKF":"Imputation Level of AESTWK",
 "AEENWKF":"Imputation Level of AEENWK","EXSEQ":"Sequence Number","EXTRT":"Name of Actual Treatment",
 "EXLOT":"Lot Number","EXDOSE":"Dose per Administration","EXDOSU":"Dose Units","EXDOSFRM":"Dose Form",
 "EXROUTE":"Route of Administration","EXSTDTC":"Start Date/Time of Treatment",
 "EXENDTC":"End Date/Time of Treatment","EXSTDY":"Study Day of Start of Treatment",
 "EXENDY":"Study Day of End of Treatment","DSSEQ":"Sequence Number",
 "DSTERM":"Reported Term for the Disposition Event","DSDECOD":"Standardized Disposition Term",
 "DSCAT":"Category for Disposition Event","DSSCAT":"Subcategory for Disposition Event",
 "DSSTWK":"Study Week of Start of Disposition Event","DSSTWKF":"Imputation Level of DSSTWK",
 "VSSEQ":"Sequence Number","VSTESTCD":"Vital Signs Test Short Name","VSTEST":"Vital Signs Test Name",
 "VSORRES":"Result or Finding in Original Units","VSORRESU":"Original Units",
 "VSSTRESC":"Character Result/Finding in Std Format","VSSTRESN":"Numeric Finding in Standard Units",
 "VSSTRESU":"Standard Units","VSMETHOD":"Method of Test or Examination","VSBLFL":"Baseline Flag",
 "VSDRVFL":"Derived Flag","VSDTC":"Date/Time of Measurements","VSDY":"Study Day of Vital Signs",
 "RDOMAIN":"Related Domain Abbreviation","IDVAR":"Identifying Variable",
 "IDVARVAL":"Identifying Variable Value","QNAM":"Qualifier Variable Name","QLABEL":"Qualifier Variable Label",
 "QVAL":"Data Value","QORIG":"Origin","QEVAL":"Evaluator","TSSEQ":"Sequence Number",
 "TSPARMCD":"Trial Summary Parameter Short Name","TSPARM":"Trial Summary Parameter","TSVAL":"Parameter Value",
 "TAETORD":"Planned Order of Element within Arm","ETCD":"Element Code","ELEMENT":"Description of Element",
 "TABRANCH":"Branch",
}
ORIGIN = {"AGE":"Derived","ACTARM":"Assigned","ACTARMCD":"Assigned","AESOC":"Derived","EPOCH":"Derived",
          "EXENDY":"Derived"}
MANDATORY_YES = {"STUDYID","DOMAIN","USUBJID","RDOMAIN","QNAM","QVAL","TSSEQ","TSPARMCD","TSVAL",
                 "ARMCD","ARM","ETCD","ELEMENT","TAETORD"}
IG_META = {  # (Repeating, Structure, Class) for domains we (re)build
 "DM":("No","One record per subject","SPECIAL PURPOSE"),
 "AE":("Yes","One record per subject per adverse event","EVENTS"),
 "EX":("Yes","One record per subject per exposure record","INTERVENTIONS"),
 "DS":("Yes","One record per subject per disposition event","EVENTS"),
 "VS":("Yes","One record per subject per measurement per visit","FINDINGS"),
 "SUPPDM":("Yes","One record per subject per supplemental qualifier","RELATIONSHIP"),
 "SUPPAE":("Yes","One record per AE per supplemental qualifier","RELATIONSHIP"),
 "SUPPDS":("Yes","One record per disposition event per supplemental qualifier","RELATIONSHIP"),
 "TS":("Yes","One record per trial summary parameter","TRIAL DESIGN"),
 "TA":("Yes","One record per planned element per arm","TRIAL DESIGN"),
}

# Reorder touched-domain ItemRefs to CDISC SDTM library order (matches uplift_sdtm_34.R ORD;
# clears CORE-000852). Other domains keep their column order.
LIBORDER = {
 "DM": ["STUDYID","DOMAIN","USUBJID","SUBJID","RFSTDTC","RFENDTC","AGE","AGEU","SEX","RACE","ARMCD","ARM","ACTARMCD","ACTARM"],
 "AE": ["STUDYID","DOMAIN","USUBJID","AESEQ","AEREFID","AESPID","AETERM","AEDECOD","AEBODSYS","AESOC","AESER","AEACN","AEREL","AEPATT","AEOUT","AESCONG","AESDISAB","AESDTH","AESHOSP","AESLIFE","AESMIE","AECONTRT","AETOXGR","VISITNUM","VISIT","EPOCH"],
 "EX": ["STUDYID","DOMAIN","USUBJID","EXSEQ","EXTRT","EXDOSE","EXDOSU","EXDOSFRM","EXROUTE","EXLOT","VISITNUM","VISIT","EPOCH","EXSTDTC","EXENDTC","EXSTDY","EXENDY"],
 "DS": ["STUDYID","DOMAIN","USUBJID","DSSEQ","DSTERM","DSDECOD","DSCAT","DSSCAT","VISITNUM","VISIT","EPOCH"],
 "VS": ["STUDYID","DOMAIN","USUBJID","VSSEQ","VSTESTCD","VSTEST","VSORRES","VSORRESU","VSSTRESC","VSSTRESN","VSSTRESU","VSMETHOD","VSBLFL","VSDRVFL","VISITNUM","VISIT","EPOCH","VSDTC","VSDY"],
}
for ds, order in LIBORDER.items():
    by = {c[0]: c for c in COLS[ds]}
    COLS[ds] = [by[v] for v in order]

SDTMIG_OID="STD.SDTMIG.3.4"; CT_OID="STD.SDTMCT.2026-03-27"

parser = etree.XMLParser(remove_blank_text=True)
tree = etree.parse(SRC, parser); root = tree.getroot()
mdv = root.find(f".//{o('MetaDataVersion')}")

# 1. Standards
std_block = mdv.find(d("Standards"))
for s in list(std_block):
    if s.get("Type")=="IG":
        s.set("OID",SDTMIG_OID); s.set("Name","SDTMIG"); s.set("Version","3.4")
    elif s.get("Type")=="CT":
        s.set("OID",CT_OID); s.set("Version","2026-03-27")
mdv.set("OID", mdv.get("OID","").replace("SDTM.3.1.1","SDTM.3.4"))

# 2. every StandardOID ref -> 3.4
for el in mdv.iter():
    v = el.get(d("StandardOID"))
    if v == "STD.SDTMIG.3.1.1": el.set(d("StandardOID"), SDTMIG_OID)

def build_itemdef(ds, name, dtype, length, old_defs):
    oid = f"IT.{ds}.{name}"
    el = etree.Element(o("ItemDef"), OID=oid, Name=name, DataType=dtype, Length=str(length))
    desc = etree.SubElement(el, o("Description"))
    tt = etree.SubElement(desc, o("TranslatedText")); tt.set(f"{{{XML}}}lang","en")
    tt.text = LBL.get(name, name.title())
    # carry CodeListRef + Origin from prior same-OID def if present
    old = old_defs.get(oid)
    carried = False
    if old is not None:
        for ch in old:
            ln = etree.QName(ch).localname
            if ln in ("CodeListRef","Origin"):
                el.append(etree.fromstring(etree.tostring(ch))); carried = True
    if not carried and name in ORIGIN:
        etree.SubElement(el, d("Origin"), Type=ORIGIN[name])
    return el

# index existing ItemDefs
old_defs = {e.get("OID"): e for e in mdv.findall(o("ItemDef"))}

# 3. rebuild touched domains' ItemGroupDef ItemRefs + ItemDefs
igs = {ig.get("Name"): ig for ig in mdv.findall(o("ItemGroupDef"))}
for ds, cols in COLS.items():
    rep, struct, cls = IG_META[ds]
    ig = igs.get(ds)
    if ig is None:  # new domain (TS, TA)
        ig = etree.SubElement(mdv, o("ItemGroupDef"))
        ig.set("OID", f"IG.{ds}"); ig.set("Name", ds)
        ig.set("Repeating", rep); ig.set("IsReferenceData", "Yes" if ds in ("TS","TA") else "No")
        ig.set("Purpose","Tabulation"); ig.set(d("Structure"), struct)
        ig.set(d("ArchiveLocationID"), f"LF.{ds}"); ig.set(d("StandardOID"), SDTMIG_OID)
        desc = etree.SubElement(ig, o("Description"))
        tt = etree.SubElement(desc, o("TranslatedText")); tt.set(f"{{{XML}}}lang","en")
        tt.text = f"{ds} ({struct})"
    else:
        # drop existing ItemRef / Class / leaf; keep Description
        for ch in list(ig):
            if etree.QName(ch).localname in ("ItemRef","Class","leaf"):
                ig.remove(ch)
    # ItemRefs in data order
    for i,(name,dtype,length) in enumerate(cols, start=1):
        etree.SubElement(ig, o("ItemRef"), ItemOID=f"IT.{ds}.{name}",
                         Mandatory=("Yes" if name in MANDATORY_YES else "No"),
                         OrderNumber=str(i))
    etree.SubElement(ig, d("Class"), Name=cls)
    leaf = etree.SubElement(ig, d("leaf")); leaf.set("ID", f"LF.{ds}")
    leaf.set(f"{{{XLINK}}}href", f"{ds.lower()}.xpt")
    etree.SubElement(leaf, d("title")).text = f"{ds.lower()}.xpt"
    # rebuild this domain's ItemDefs: remove old IT.<DS>.*, insert fresh
    for e in mdv.findall(o("ItemDef")):
        if e.get("OID","").startswith(f"IT.{ds}."): mdv.remove(e)
    for (name,dtype,length) in cols:
        mdv.append(build_itemdef(ds, name, dtype, length, old_defs))

# 4. drop any ItemDef no longer referenced by any ItemRef (cleans phantoms)
referenced = {ir.get("ItemOID") for ir in mdv.findall(f"{o('ItemGroupDef')}/{o('ItemRef')}")}
for e in mdv.findall(o("ItemDef")):
    if e.get("OID") not in referenced:
        mdv.remove(e)

# 5. enforce Define-2.1 MetaDataVersion child order (ItemGroupDef before ItemDef, etc.)
ORDER = [d("Standards"), d("ValueListDef"), d("WhereClauseDef"), o("ItemGroupDef"),
         o("ItemDef"), o("CodeList"), o("MethodDef"), d("CommentDef"), d("leaf")]
rank = {t:i for i,t in enumerate(ORDER)}
kids = list(mdv)
kids.sort(key=lambda e: rank.get(e.tag, len(ORDER)))   # stable: preserves intra-type order
for e in kids: mdv.remove(e)
for e in kids: mdv.append(e)

tree.write(SRC, pretty_print=True, xml_declaration=True, encoding="UTF-8")
n_ig = len(mdv.findall(o("ItemGroupDef"))); n_it = len(mdv.findall(o("ItemDef")))
print(f"define_sdtm.xml -> SDTMIG 3.4 / CT 2026-03-27 ; {n_ig} ItemGroupDefs, {n_it} ItemDefs")
print("rebuilt:", ", ".join(COLS.keys()))
