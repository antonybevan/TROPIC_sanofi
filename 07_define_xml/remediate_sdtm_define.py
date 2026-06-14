import os
import sys
from lxml import etree

ODM_NS = "http://www.cdisc.org/ns/odm/v1.3"
DEF_NS = "http://www.cdisc.org/ns/def/v2.1"
XLINK_NS = "http://www.w3.org/1999/xlink"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
XML_NS = "http://www.w3.org/XML/1998/namespace"

NSMAP = {
    None: ODM_NS,
    'def': DEF_NS,
    'xlink': XLINK_NS,
    'xsi': XSI_NS
}

def o(tag): return f"{{{ODM_NS}}}{tag}"
def d(tag): return f"{{{DEF_NS}}}{tag}"

def map_attrs(attrib, tag_local):
    new_attrib = {}
    def_attrs = {
        "ItemGroupDef": {"Structure", "ArchiveLocationID", "IsNonStandard", "HasNoData", "CommentOID", "StandardOID"},
        "ItemDef": {"DisplayFormat", "CommentOID"},
        "CodeList": {"StandardOID", "IsNonStandard", "CommentOID"},
        "ItemRef": {"IsNonStandard", "HasNoData"},
        "CodeListItem": {"ExtendedValue"},
        "EnumeratedItem": {"ExtendedValue"},
    }.get(tag_local, set())
    
    for k, v in attrib.items():
        local_k = etree.QName(k).localname
        if local_k in def_attrs:
            new_attrib[d(local_k)] = v
        else:
            new_attrib[local_k] = v
    return new_attrib

def remediate(src_path, dest_path):
    # Parse source XML
    parser = etree.XMLParser(remove_blank_text=True)
    src_tree = etree.parse(src_path, parser)
    src_root = src_tree.getroot()
    
    # We want to construct the new <ODM> structure
    # Root ODM element
    odm_attrs = {
        "ODMVersion": "1.3.2",
        "FileType": "Snapshot",
        "FileOID": src_root.get("FileOID", "TROPIC_SDTM_Metadata_v2.1"),
        "CreationDateTime": "2026-06-12T21:49:25",
        "AsOfDateTime": src_root.get("AsOfDateTime", "2026-06-12T21:49:25"),
        "Originator": src_root.get("Originator", "Antony Bevan, Clinical Programming"),
        d("Context"): "Submission",
        f"{{{XSI_NS}}}schemaLocation": f"{ODM_NS} http://schema.cdisc.org/define/v2.1/define2-1-0.xsd"
    }
    
    new_root = etree.Element(o("ODM"), attrib=odm_attrs, nsmap=NSMAP)
    
    # Add Study and GlobalVariables wrappers
    study = etree.SubElement(new_root, o("Study"), attrib={"OID": "STDY.TROPIC"})
    gv = etree.SubElement(study, o("GlobalVariables"))
    etree.SubElement(gv, o("StudyName")).text = "TROPIC (EFC6193 / XRP6258)"
    etree.SubElement(gv, o("StudyDescription")).text = "Cabazitaxel vs Mitoxantrone in mCRPC progressing after docetaxel (NCT00417079)."
    etree.SubElement(gv, o("ProtocolName")).text = "EFC6193"
    
    # MetaDataVersion element
    src_mdv = src_root.find(".//MetaDataVersion")
    if src_mdv is None:
        src_mdv = src_root.find(f".//{{{DEF_NS}}}MetaDataVersion")
    if src_mdv is None:
        src_mdv = src_root.find(".//{*}MetaDataVersion")
        
    mdv_attrs = {
        "OID": src_mdv.get("OID", "MDV.TROPIC_NCT00417079.SDTM.3.1.1"),
        "Name": src_mdv.get("Name", "TROPIC Trial SDTM Metadata Specification"),
        "Description": src_mdv.get("Description", "Metadata specification for TROPIC Phase III re-analysis SDTM datasets"),
        d("DefineVersion"): "2.1.0"
    }
    
    new_mdv = etree.SubElement(study, o("MetaDataVersion"), attrib=mdv_attrs)
    
    # Add def:Standards block
    standards = etree.SubElement(new_mdv, d("Standards"))
    etree.SubElement(standards, d("Standard"), attrib={
        "OID": "STD.SDTMIG.3.1.1",
        "Name": "SDTMIG",
        "Type": "IG",
        "Version": "3.1.1",
        "Status": "Final"
    })
    etree.SubElement(standards, d("Standard"), attrib={
        "OID": "STD.SDTMCT.2024-03-29",
        "Name": "CDISC/NCI",
        "Type": "CT",
        "PublishingSet": "SDTM",
        "Version": "2024-03-29",
        "Status": "Final"
    })
    
    # Process child elements of MetaDataVersion
    for child in src_mdv:
        if not isinstance(child.tag, str):
            continue
        tag_local = etree.QName(child.tag).localname
        
        # 1. ItemGroupDef processing
        if tag_local == "ItemGroupDef":
            # Map standard attributes and exclude unwanted ones
            attrs = {k: v for k, v in child.attrib.items() if etree.QName(k).localname not in ("Label", "CDISCLibraryID", "CDISCLibraryVersion")}
            
            # Generate def:ArchiveLocationID
            ds_name = child.get("Name", "")
            leaf_id = f"LF.{ds_name}"
            attrs["ArchiveLocationID"] = leaf_id
            
            attrs = map_attrs(attrs, "ItemGroupDef")
            # Link to standard OID
            attrs[d("StandardOID")] = "STD.SDTMIG.3.1.1"
            
            new_ig = etree.SubElement(new_mdv, o("ItemGroupDef"), attrib=attrs)
            
            # Map description child
            desc = child.find(".//Description")
            if desc is None:
                desc = child.find(f".//{{{DEF_NS}}}Description")
            if desc is None:
                desc = child.find(".//{*}Description")
                
            if desc is not None:
                new_desc = etree.SubElement(new_ig, o("Description"))
                tt = etree.SubElement(new_desc, o("TranslatedText"), attrib={f"{{{XML_NS}}}lang": "en"})
                tt.text = desc.text.strip() if desc.text else ""
            
            # Map ItemRef elements (traverse direct children)
            for ir in child:
                if not isinstance(ir.tag, str):
                    continue
                ir_local = etree.QName(ir.tag).localname
                if ir_local == "ItemRef":
                    ir_attrs = {k: v for k, v in ir.attrib.items() if etree.QName(k).localname != "Order"}
                    if "Order" in ir.attrib:
                        ir_attrs["OrderNumber"] = ir.attrib["Order"]
                    ir_attrs = map_attrs(ir_attrs, "ItemRef")
                    etree.SubElement(new_ig, o("ItemRef"), attrib=ir_attrs)
            
            # Append def:leaf element as the last child of ItemGroupDef
            new_leaf = etree.SubElement(new_ig, d("leaf"), attrib={
                "ID": leaf_id,
                f"{{{XLINK_NS}}}href": f"{ds_name.lower()}.xpt"
            })
            etree.SubElement(new_leaf, d("title")).text = f"{ds_name.lower()}.xpt"
                
        # 2. ItemDef processing
        elif tag_local == "ItemDef":
            label_val = child.get("Label", "")
            attrs = {k: v for k, v in child.attrib.items() if etree.QName(k).localname != "Label"}
            attrs = map_attrs(attrs, "ItemDef")
            new_id = etree.SubElement(new_mdv, o("ItemDef"), attrib=attrs)
            
            # Add description containing Label value
            if label_val:
                new_desc = etree.SubElement(new_id, o("Description"))
                tt = etree.SubElement(new_desc, o("TranslatedText"), attrib={f"{{{XML_NS}}}lang": "en"})
                tt.text = label_val
                
            # Process Origin elements (traverse direct children)
            for origin in child:
                if not isinstance(origin.tag, str):
                    continue
                origin_local = etree.QName(origin.tag).localname
                if origin_local == "Origin":
                    etree.SubElement(new_id, d("Origin"), attrib=dict(origin.attrib))
                
        # 3. CodeList processing
        elif tag_local == "CodeList":
            attrs = dict(child.attrib)
            attrs = map_attrs(attrs, "CodeList")
            # Link standard codelists to CT
            if child.get("OID") in ("CL.NY", "CL.SEX"):
                attrs[d("StandardOID")] = "STD.SDTMCT.2024-03-29"
            new_cl = etree.SubElement(new_mdv, o("CodeList"), attrib=attrs)
            
            # Map CodeListItems (traverse direct children)
            for cli in child:
                if not isinstance(cli.tag, str):
                    continue
                cli_local = etree.QName(cli.tag).localname
                if cli_local == "CodeListItem":
                    cli_attrs = map_attrs(dict(cli.attrib), "CodeListItem")
                    new_cli = etree.SubElement(new_cl, o("CodeListItem"), attrib=cli_attrs)
                    
                    decode = cli.find(".//Decode")
                    if decode is None:
                        decode = cli.find(f".//{{{DEF_NS}}}Decode")
                    if decode is None:
                        decode = cli.find(".//{*}Decode")
                        
                    if decode is not None:
                        new_dec = etree.SubElement(new_cli, o("Decode"))
                        tt = decode.find(".//TranslatedText")
                        if tt is None:
                            tt = decode.find(f".//{{{DEF_NS}}}TranslatedText")
                        if tt is None:
                            tt = decode.find(".//{*}TranslatedText")
                            
                        if tt is not None:
                            etree.SubElement(new_dec, o("TranslatedText"), attrib=dict(tt.attrib)).text = tt.text
                        
    # Write to destination
    tree = etree.ElementTree(new_root)
    tree.write(dest_path, pretty_print=True, xml_declaration=True, encoding="UTF-8")

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "define_sdtm.xml")
    remediate(src, src)
    print("Successfully remediated define_sdtm.xml")
