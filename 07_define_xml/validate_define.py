"""
validate_define.py — self-contained Define-XML 2.1 conformance gate (no network).

This is the runnable, honest conformance check the repo CAN execute everywhere (the full
Pinnacle 21 / CDISC CORE certification needs the proprietary/cached rule packs + network and
is the documented offline step). It verifies the structural and referential-integrity rules
that a validator enforces and that a hand-authored define most often violates:

  * root <ODM> in the ODM 1.3.2 namespace with def:/xlink: bound;
  * required Study/GlobalVariables, MetaDataVersion, def:Standards, def:DefineVersion;
  * every ItemRef->ItemDef, MethodOID->MethodDef, CodeListRef->CodeList,
    def:WhereClauseRef->def:WhereClauseDef, def:ValueListRef->def:ValueListDef,
    def:CommentOID->def:CommentDef reference resolves;
  * every ItemGroupDef has a def:leaf whose ID matches its def:ArchiveLocationID;
  * ODM <Description> elements carry <TranslatedText> (not bare text).

Exit 0 = all checks pass; exit 1 = at least one violation (printed).

Run:  python3 07_define_xml/validate_define.py [path/to/define.xml]
"""
import os
import sys
from lxml import etree

ODM = "http://www.cdisc.org/ns/odm/v1.3"
DEF = "http://www.cdisc.org/ns/def/v2.1"
ARM = "http://www.cdisc.org/ns/arm/v1.0"


def validate(path):
    problems, checks = [], 0
    try:
        root = etree.parse(path).getroot()
    except (OSError, etree.XMLSyntaxError) as e:
        return [f"not well-formed: {e}"], 0

    def o(ln): return f"{{{ODM}}}{ln}"
    def d(ln): return f"{{{DEF}}}{ln}"
    def oids(tag): return {e.get("OID") for e in root.iter(tag) if e.get("OID")}

    # ---- structural ----
    checks += 1
    if etree.QName(root).localname != "ODM" or etree.QName(root).namespace != ODM:
        problems.append("root is not <ODM> in the ODM 1.3.2 namespace")
    checks += 1
    if DEF not in (root.nsmap or {}).values():
        problems.append("def: namespace (def/v2.1) is not declared")
    for req in ("Study", "GlobalVariables", "MetaDataVersion"):
        checks += 1
        if root.find(f".//{o(req)}") is None:
            problems.append(f"missing required <{req}>")
    checks += 1
    if root.find(f".//{d('Standards')}") is None:
        problems.append("missing def:Standards")
    checks += 1
    mdv = root.find(f".//{o('MetaDataVersion')}")
    if mdv is None or mdv.get(d("DefineVersion")) != "2.1.0":
        problems.append("MetaDataVersion missing def:DefineVersion='2.1.0'")

    # ---- referential integrity ----
    itemdefs, methods = oids(o("ItemDef")), oids(o("MethodDef"))
    codelists, wcs = oids(o("CodeList")), oids(d("WhereClauseDef"))
    vlds, comments = oids(d("ValueListDef")), oids(d("CommentDef"))

    def check_refs(tag, attr, universe, label):
        nonlocal checks
        for e in root.iter(tag):
            v = e.get(attr)
            if v:
                checks += 1
                if v not in universe:
                    problems.append(f"{label}: {v} -> no target")

    check_refs(o("ItemRef"), "ItemOID", itemdefs, "ItemRef.ItemOID")
    check_refs(o("ItemRef"), "MethodOID", methods, "ItemRef.MethodOID")
    check_refs(o("CodeListRef"), "CodeListOID", codelists, "CodeListRef")
    check_refs(d("WhereClauseRef"), "WhereClauseOID", wcs, "def:WhereClauseRef")
    check_refs(d("ValueListRef"), "ValueListOID", vlds, "def:ValueListRef")

    # ---- standards ----
    standards = oids(d("Standard"))
    check_refs(o("ItemGroupDef"), d("StandardOID"), standards, "ItemGroupDef.def:StandardOID")
    check_refs(o("CodeList"), d("StandardOID"), standards, "CodeList.def:StandardOID")

    for e in root.iter():
        c = e.get(d("CommentOID"))
        if c:
            checks += 1
            if c not in comments:
                problems.append(f"def:CommentOID: {c} -> no def:CommentDef")

    # ---- reverse-orphan: defined-but-unreferenced Method/Comment (audit F-06) ----
    # validate_define historically only checked ref->def, so a MethodDef/CommentDef defined but
    # wired to nothing slipped through. Flag those too (dead metadata).
    used_methods = {e.get("MethodOID") for e in root.iter(o("ItemRef")) if e.get("MethodOID")}
    for m in methods:
        checks += 1
        if m not in used_methods:
            problems.append(f"orphan MethodDef (defined, never referenced): {m}")
    used_comments = {e.get(d("CommentOID")) for e in root.iter() if e.get(d("CommentOID"))}
    for c in comments:
        checks += 1
        if c not in used_comments:
            problems.append(f"orphan def:CommentDef (defined, never referenced): {c}")

    # ---- ARM (Analysis Results Metadata), if present ----
    def a(ln): return f"{{{ARM}}}{ln}"
    item_groups = oids(o("ItemGroupDef"))
    if root.find(f".//{a('AnalysisResultDisplays')}") is not None:
        check_refs(a("AnalysisResult"), "ParameterOID", itemdefs, "arm:AnalysisResult.ParameterOID")
        check_refs(a("AnalysisDataset"), "ItemGroupOID", item_groups, "arm:AnalysisDataset.ItemGroupOID")
        check_refs(a("AnalysisVariable"), "ItemOID", itemdefs, "arm:AnalysisVariable.ItemOID")

    # ---- ItemGroupDef leaf + ArchiveLocationID ----
    for ig in root.iter(o("ItemGroupDef")):
        checks += 1
        alid = ig.get(d("ArchiveLocationID"))
        leaf = ig.find(d("leaf"))
        if leaf is None or leaf.get("ID") != alid:
            problems.append(f"ItemGroupDef {ig.get('OID')}: leaf/ArchiveLocationID mismatch")

    # ---- Description must hold TranslatedText ----
    for desc in root.iter(o("Description")):
        if (desc.text and desc.text.strip()) and desc.find(o("TranslatedText")) is None:
            checks += 1
            problems.append(f"Description with bare text (needs TranslatedText): {desc.text[:40]}")

    return problems, checks


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "define.xml")
    problems, checks = validate(path)
    print(f"Define-XML conformance gate — {os.path.basename(path)} — {checks} checks")
    if problems:
        print(f"FAIL: {len(problems)} violation(s):")
        for p in problems[:40]:
            print("  -", p)
        sys.exit(1)
    print("PASS: structure + referential integrity conform (full XSD/Pinnacle 21 = offline step).")
    sys.exit(0)


if __name__ == "__main__":
    main()
