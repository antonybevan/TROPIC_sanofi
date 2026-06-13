"""
remediate_define_namespace.py — one-shot, auditable transform that re-architects
07_define_xml/define.xml from its non-conformant form (everything in the def/v2.1
DEFAULT namespace under a bogus <Define> root) to a conformant Define-XML 2.1 document:

  * root becomes <ODM> in the ODM 1.3.2 namespace, with def:/xlink:/xsi: prefixes bound;
  * the structural backbone (MetaDataVersion, ItemGroupDef, ItemDef, ItemRef, CodeList,
    CodeListItem, Decode, Description, TranslatedText, MethodDef, RangeCheck, CheckValue)
    stays in the ODM namespace (unprefixed);
  * define extensions take the def: prefix: def:Origin, def:ValueListDef, def:WhereClauseDef,
    def:WhereClauseRef, def:CommentDef, def:leaf, def:Standards/def:Standard, def:ValueListRef;
  * adds the required Study/GlobalVariables, def:Standards, def:DefineVersion;
  * fixes content defects surfaced by the move: wraps plain-text <Description> in
    <TranslatedText>, drops the non-standard Role attribute on ItemGroupDef, converts
    <CommentRef> child elements to def:CommentOID attributes, adds a def:leaf archive
    location per ItemGroupDef, and wires base AVAL ItemDefs to their def:ValueListRef.

Run:  python3 07_define_xml/remediate_define_namespace.py
Writes 07_define_xml/define.xml in place (after the caller has validated the output).
"""
import os
from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "define.xml")

ODM = "http://www.cdisc.org/ns/odm/v1.3"
DEF = "http://www.cdisc.org/ns/def/v2.1"
XLINK = "http://www.w3.org/1999/xlink"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
XML = "http://www.w3.org/XML/1998/namespace"
NSMAP = {None: ODM, "def": DEF, "xlink": XLINK, "xsi": XSI}

# Local element names that belong to the def: extension namespace.
DEF_ELEMS = {"Origin", "ValueListDef", "WhereClauseDef", "WhereClauseRef",
             "CommentDef", "leaf", "Standards", "Standard", "ValueListRef", "title"}


def lname(tag):
    return etree.QName(tag).localname


def qn(ns, local):
    return etree.QName(ns, local)


def convert(old):
    """Rebuild an element in its correct target namespace, recursively."""
    ln = lname(old.tag)
    if ln == "CommentRef":
        return None  # folded into parent as def:CommentOID
    ns = DEF if ln in DEF_ELEMS else ODM
    el = etree.Element(qn(ns, ln))

    # ---- attributes (preserve namespaced attrs like xml:lang; remap a couple) ----
    for an, av in old.attrib.items():
        q = etree.QName(an)
        if ln == "ItemGroupDef" and q.namespace is None and q.localname == "Structure":
            el.set(qn(DEF, "Structure"), av);  continue
        if ln == "ItemGroupDef" and q.namespace is None and q.localname == "Role":
            continue  # Role is not a valid ItemGroupDef attribute in ODM/Define-XML
        if ln == "MetaDataVersion" and q.localname in ("CDISCLibraryID", "CDISCLibraryVersion"):
            continue  # non-standard; the standard is declared via def:Standards
        if q.namespace:
            el.set(an, av)            # keep xml:lang, xsi:* etc.
        else:
            el.set(q.localname, av)

    # ---- ODM <Description> must contain <TranslatedText>, not bare text ----
    if ln == "Description":
        has_tt = any(lname(c.tag) == "TranslatedText" for c in old)
        if not has_tt and old.text and old.text.strip():
            tt = etree.SubElement(el, qn(ODM, "TranslatedText"))
            tt.set(qn(XML, "lang"), "en")
            tt.text = old.text.strip()
    elif old.text and old.text.strip():
        el.text = old.text

    # ---- children ----
    for ch in old:
        if lname(ch.tag) == "CommentRef":
            el.set(qn(DEF, "CommentOID"), ch.get("CommentOID"))
            continue
        cnew = convert(ch)
        if cnew is not None:
            el.append(cnew)

    # ---- ItemGroupDef: add required archive location (def:ArchiveLocationID + def:leaf) ----
    if ln == "ItemGroupDef":
        name = el.get("Name")
        leaf_id = f"LF.{name}"
        el.set(qn(DEF, "ArchiveLocationID"), leaf_id)
        leaf = etree.SubElement(el, qn(DEF, "leaf"))   # schema order: ...ItemRef*, def:leaf
        leaf.set("ID", leaf_id)
        leaf.set(qn(XLINK, "href"), f"{name.lower()}.xpt")
        title = etree.SubElement(leaf, qn(DEF, "title"))
        title.text = f"{name.lower()}.xpt"
    return el


def main():
    tree = etree.parse(SRC)
    old_root = tree.getroot()           # <Define>
    old_mdv = old_root.find("{*}MetaDataVersion")

    # ---- new ODM root ----
    odm = etree.Element(qn(ODM, "ODM"), nsmap=NSMAP)
    odm.set(qn(XSI, "schemaLocation"),
            "http://www.cdisc.org/ns/odm/v1.3 http://schema.cdisc.org/define/v2.1/define2-1-0.xsd")
    odm.set("ODMVersion", "1.3.2")
    odm.set("FileType", "Snapshot")
    odm.set("FileOID", old_root.get("FileOID", "TROPIC.Define.ADaM"))
    odm.set("CreationDateTime", old_root.get("AsOfDateTime", "2026-06-13T00:00:00"))
    if old_root.get("AsOfDateTime"):
        odm.set("AsOfDateTime", old_root.get("AsOfDateTime"))
    odm.set("Originator", old_root.get("Originator", "Sponsor"))

    # ---- Study / GlobalVariables (required by ODM) ----
    study = etree.SubElement(odm, qn(ODM, "Study"), OID="STDY.TROPIC")
    gv = etree.SubElement(study, qn(ODM, "GlobalVariables"))
    etree.SubElement(gv, qn(ODM, "StudyName")).text = "TROPIC (EFC6193 / XRP6258)"
    etree.SubElement(gv, qn(ODM, "StudyDescription")).text = (
        "Cabazitaxel vs Mitoxantrone in mCRPC progressing after docetaxel (NCT00417079).")
    etree.SubElement(gv, qn(ODM, "ProtocolName")).text = "EFC6193"

    # ---- MetaDataVersion (converted) + def:Standards + def:DefineVersion ----
    mdv = convert(old_mdv)
    mdv.set(qn(DEF, "DefineVersion"), "2.1.0")
    standards = etree.Element(qn(DEF, "Standards"))
    etree.SubElement(standards, qn(DEF, "Standard"), OID="STD.ADaMIG.1.3", Name="ADaMIG",
                     Type="IG", Version="1.3", Status="Final")
    mdv.insert(0, standards)          # def:Standards is the first MDV child

    # ---- wire base AVAL ItemDefs to their value lists (def:ValueListRef) ----
    wired = []
    vlds = {e.get("OID") for e in mdv.iter(qn(DEF, "ValueListDef"))}
    for itemdef in mdv.iter(qn(ODM, "ItemDef")):
        oid = itemdef.get("OID")
        vl = f"VL.{oid[3:]}" if oid and oid.startswith("IT.") else None
        if vl and vl in vlds:
            vlref = etree.Element(qn(DEF, "ValueListRef"), ValueListOID=vl)
            # insert after Description if present, else first
            desc = itemdef.find(qn(ODM, "Description"))
            itemdef.insert(list(itemdef).index(desc) + 1 if desc is not None else 0, vlref)
            wired.append((oid, vl))
    odm.append(mdv)

    out = etree.tostring(odm, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    # keep the stylesheet PI
    pi = b'<?xml-stylesheet type="text/xsl" href="define2-1.xsl"?>\n'
    out = out.replace(b"?>\n", b"?>\n" + pi, 1)
    with open(SRC, "wb") as f:
        f.write(out)
    print(f"  wired value-level ValueListRef: {wired}")
    print(f"  wrote {SRC}")


if __name__ == "__main__":
    main()
