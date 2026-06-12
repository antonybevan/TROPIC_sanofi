import os
from datetime import datetime

# Domain configurations and labels
domains_meta = {
    "DM": ("Demographics", "No", "Demographics", "One record per subject"),
    "AE": ("Adverse Events", "Yes", "Adverse Events", "One record per subject per adverse event"),
    "EX": ("Exposure", "Yes", "Exposure", "One record per subject per constant exposure cycle"),
    "CM": ("Concomitant Medications", "Yes", "Concomitant Medications", "One record per subject per medication"),
    "LB": ("Laboratory Test Results", "Yes", "Laboratory Test Results", "One record per subject per laboratory test per visit"),
    "DS": ("Disposition", "Yes", "Disposition", "One record per subject per disposition event"),
    "VS": ("Vital Signs", "Yes", "Vital Signs", "One record per subject per vital sign measurement per visit"),
    "LS": ("Lesion Assessment", "Yes", "Lesion Assessment", "One record per subject per lesion per assessment visit"),
    "PN": ("Pain Assessment", "Yes", "Pain Assessment", "One record per subject per pain assessment per visit"),
    
    # Supplementals
    "SUPPDM": ("Supplemental Demographics", "Yes", "Relationship", "One record per subject per supplemental qualifier"),
    "SUPPAE": ("Supplemental Adverse Events", "Yes", "Relationship", "One record per subject per adverse event per supplemental qualifier"),
    "SUPPEX": ("Supplemental Exposure", "Yes", "Relationship", "One record per subject per exposure cycle per supplemental qualifier"),
    "SUPPCM": ("Supplemental Concomitant Medications", "Yes", "Relationship", "One record per subject per medication per supplemental qualifier"),
    "SUPPLB": ("Supplemental Laboratory Test Results", "Yes", "Relationship", "One record per subject per laboratory test per supplemental qualifier"),
    "SUPPDS": ("Supplemental Disposition", "Yes", "Relationship", "One record per subject per disposition event per supplemental qualifier"),
    "SUPPLS": ("Supplemental Lesion Assessment", "Yes", "Relationship", "One record per subject per lesion per supplemental qualifier"),
}

# Variable configuration lists for each domain (derived from actual dataset checks)
domains_cols = {
    "DM": ["AGEGRP", "STUDYID", "DOMAIN", "USUBJID", "SUBJID", "RFSTDTC", "RFENDTC", "AGEU", "SEX", "RACE", "ARM", "ARMCD", "ARM2", "ARMA", "ARMCD2", "BSABL", "ITT", "PPROT", "SAFETY"],
    "AE": ["AESTWKF", "AEENWKF", "USUBJID", "STUDYID", "DOMAIN", "AESEQ", "AESPID", "AEREFID", "AETERM", "AEDECOD", "AEBODSYS", "AESER", "AEACN", "AECONTRT", "AEREL", "AEPATT", "AEOUT", "AESCONG", "AESDISAB", "AESDTH", "AESHOSP", "AESLIFE", "AESMIE", "AETOXGR", "VISITNUM", "VISIT", "AESTWK", "AEENWK", "SUBJID", "AECOLGR", "AECOLGRN", "AEDICTVS", "AEHLGT", "AEHLT", "AELLT", "AEOVISIT", "AETOXGRN", "AETRTEM", "AEREFER", "AEDTHDTC", "AESEQUCM"],
    "EX": ["STUDYID", "DOMAIN", "USUBJID", "EXSEQ", "EXTRT", "EXLOT", "EXDOSE", "EXDOSU", "EXDOSFRM", "EXROUTE", "VISITNUM", "VISIT", "EXSTDTC", "EXSTDY", "EXENDTC", "SUBJID", "EXPDOSE", "EXPDOSU", "EXCUMD", "EXCUMD2", "EXDOSE2", "EXPDOSE2", "EXTINT", "EXTRINT", "EXDSREA", "EXDELAY", "EXDSRCM", "ENDTCOL"],
    "CM": ["STUDYID", "DOMAIN", "USUBJID", "CMSEQ", "CMTRT", "CMDECOD", "CMCAT", "CMINDC", "CMDOSE", "CMDOSU", "CMDOSRGM", "VISITNUM", "VISIT", "CMSTDTC", "CMSTDY", "CMENDTC", "CMENDY", "SUBJID", "CMATCL1", "CMATCL2", "CMATCSEL", "CMONGB", "CMONGO", "CMLOC", "CMENDRCM", "CMRLTL", "CMRSON", "CMPRGDTC"],
    "LB": ["STUDYID", "DOMAIN", "USUBJID", "LBSEQ", "LBTESTCD", "LBTEST", "LBCAT", "LBSCAT", "LBORRES", "LBORRESU", "LBORNRLO", "LBORNRHI", "LBSTRESC", "LBSTRESN", "LBSTRESU", "LBSTNRLO", "LBSTNRHI", "LBNRIND", "LBSTAT", "LBTOX", "LBTOXGR", "LBBLFL", "VISITNUM", "VISIT", "LBDTC", "LBDY", "SUBJID", "LBOVISIT"],
    "DS": ["DSSTWKF", "USUBJID", "STUDYID", "DOMAIN", "DSSEQ", "DSTERM", "DSDECOD", "DSCAT", "DSSCAT", "EPOCH", "VISITNUM", "VISIT", "DSSTWK", "SUBJID", "DSPROG"],
    "VS": ["STUDYID", "DOMAIN", "USUBJID", "VSSEQ", "VSTESTCD", "VSTEST", "VSORRES", "VSORRESU", "VSSTRESC", "VSSTRESN", "VSSTRESU", "VSMETHOD", "VSBLFL", "VSDRVFL", "VISITNUM", "VISIT", "VSDTC", "VSDY", "SUBJID"],
    "LS": ["STUDYID", "DOMAIN", "USUBJID", "LSSEQ", "LSSPID", "LSTESTCD", "LSTEST", "LSCAT", "LSLOC", "LSORRES", "LSORRESU", "LSSTRESC", "LSSTRESN", "LSSTRESU", "LSMETHOD", "LSSTAT", "LSBLFL", "VISITNUM", "VISIT", "LSDTC", "SUBJID", "LSSLOC"],
    "PN": ["STUDYID", "DOMAIN", "USUBJID", "PNSEQ", "PNSPID", "PNTESTCD", "PNTEST", "PNCAT", "PNORRES", "PNORRESU", "PNSTRESC", "PNSTRESN", "PNSTRESU", "PNSTAT", "VISITNUM", "VISIT", "PNDTC", "SUBJID"]
}

supp_cols = ["STUDYID", "RDOMAIN", "USUBJID", "IDVAR", "IDVARVAL", "QNAM", "QLABEL", "QVAL", "QORIG", "QEVAL", "SUBJID"]
for s_dom in ["SUPPDM", "SUPPAE", "SUPPEX", "SUPPCM", "SUPPLB", "SUPPDS", "SUPPLS"]:
    domains_cols[s_dom] = supp_cols

# Common metadata mappings for variable attributes (Name -> (DataType, Length, Label, OriginType))
var_attr_defaults = {
    "STUDYID": ("text", "40", "Study Identifier", "Protocol"),
    "DOMAIN": ("text", "4", "Domain Abbreviation", "Assigned"),
    "USUBJID": ("text", "40", "Unique Subject Identifier", "Collected"),
    "SUBJID": ("text", "20", "Subject Identifier for the Study", "Collected"),
    "SITEID": ("text", "10", "Study Site Identifier", "Collected"),
    "SEX": ("text", "2", "Sex", "Collected"),
    "RACE": ("text", "40", "Race", "Collected"),
    "ETHNIC": ("text", "40", "Ethnicity", "Collected"),
    "AGE": ("integer", "8", "Age", "Collected"),
    "AGEU": ("text", "10", "Age Units", "Collected"),
    "ARMCD": ("text", "20", "Planned Arm Code", "Assigned"),
    "ARM": ("text", "40", "Description of Planned Arm", "Assigned"),
    "COUNTRY": ("text", "3", "Country", "Assigned"),
    "RFSTDTC": ("text", "20", "Subject Reference Start Date/Time", "Derived"),
    "RFENDTC": ("text", "20", "Subject Reference End Date/Time", "Derived"),
    "VISITNUM": ("float", "8", "Visit Number", "Protocol"),
    "VISIT": ("text", "40", "Visit Name", "Protocol"),
    "EPOCH": ("text", "20", "Epoch", "Derived"),
    
    # AE
    "AESEQ": ("integer", "8", "Adverse Event Sequence Number", "Assigned"),
    "AETERM": ("text", "200", "Reported Term for the Adverse Event", "Collected"),
    "AEDECOD": ("text", "100", "Dictionary-Derived Term", "Assigned"),
    "AEBODSYS": ("text", "100", "Body System or Organ Class", "Assigned"),
    "AESER": ("text", "2", "Serious Event", "Collected"),
    "AEACN": ("text", "100", "Action Taken with Study Treatment", "Collected"),
    "AEOUT": ("text", "100", "Outcome of Adverse Event", "Collected"),
    "AEREL": ("text", "40", "Causality", "Collected"),
    "AETOXGR": ("text", "10", "Toxicity Grade", "Collected"),
    
    # EX
    "EXSEQ": ("integer", "8", "Sequence Number", "Assigned"),
    "EXTRT": ("text", "40", "Name of Treatment", "Collected"),
    "EXDOSE": ("float", "8", "Dose", "Collected"),
    "EXDOSU": ("text", "20", "Dose Units", "Collected"),
    "EXDOSFRM": ("text", "40", "Dose Form", "Collected"),
    "EXROUTE": ("text", "40", "Route of Administration", "Collected"),
    "EXSTDTC": ("text", "20", "Start Date/Time of Treatment", "Collected"),
    "EXENDTC": ("text", "20", "End Date/Time of Treatment", "Collected"),
    
    # CM
    "CMSEQ": ("integer", "8", "Sequence Number", "Assigned"),
    "CMTRT": ("text", "100", "Reported Name of Drug, Med, or Therapy", "Collected"),
    "CMDECOD": ("text", "100", "Standardized Medication Name", "Assigned"),
    "CMCAT": ("text", "100", "Category for Medication", "Collected"),
    "CMINDC": ("text", "200", "Indication", "Collected"),
    "CMSTDTC": ("text", "20", "Start Date/Time of Medication", "Collected"),
    "CMENDTC": ("text", "20", "End Date/Time of Medication", "Collected"),
    
    # LB
    "LBSEQ": ("integer", "8", "Sequence Number", "Assigned"),
    "LBTESTCD": ("text", "20", "Lab Test Short Name", "Assigned"),
    "LBTEST": ("text", "100", "Lab Test Name", "Assigned"),
    "LBCAT": ("text", "100", "Category for Lab Test", "Collected"),
    "LBSCAT": ("text", "100", "Subcategory for Lab Test", "Collected"),
    "LBORRES": ("text", "40", "Result or Finding in Original Units", "Collected"),
    "LBORRESU": ("text", "20", "Original Units", "Collected"),
    "LBSTRESN": ("float", "8", "Numeric Result/Finding in Standard Units", "Derived"),
    "LBSTRESU": ("text", "20", "Standard Units", "Derived"),
    "LBDTC": ("text", "20", "Date/Time of Specimen Collection", "Collected"),
    "LBDY": ("integer", "8", "Analysis Day of Specimen Collection", "Derived"),
    
    # DS
    "DSSEQ": ("integer", "8", "Sequence Number", "Assigned"),
    "DSTERM": ("text", "200", "Reported Term for the Disposition Event", "Collected"),
    "DSDECOD": ("text", "100", "Standardized Disposition Term", "Assigned"),
    "DSCAT": ("text", "100", "Category for Disposition Event", "Collected"),
    "DSSCAT": ("text", "100", "Subcategory for Disposition Event", "Collected"),
    
    # VS
    "VSSEQ": ("integer", "8", "Sequence Number", "Assigned"),
    "VSTESTCD": ("text", "20", "Vital Signs Test Short Name", "Assigned"),
    "VSTEST": ("text", "100", "Vital Signs Test Name", "Assigned"),
    "VSORRES": ("text", "40", "Result or Finding in Original Units", "Collected"),
    "VSDTC": ("text", "20", "Date/Time of Specimen Collection", "Collected"),
    
    # LS
    "LSSEQ": ("integer", "8", "Sequence Number", "Assigned"),
    "LSTESTCD": ("text", "20", "Lesion Assessment Test Short Name", "Assigned"),
    "LSTEST": ("text", "100", "Lesion Assessment Test Name", "Assigned"),
    "LSCAT": ("text", "100", "Category for Lesion Assessment", "Collected"),
    "LSLOC": ("text", "100", "Location for Lesion Assessment", "Collected"),
    "LSORRES": ("text", "40", "Result or Finding in Original Units", "Collected"),
    
    # PN
    "PNSEQ": ("integer", "8", "Sequence Number", "Assigned"),
    "PNTESTCD": ("text", "20", "Pain Assessment Test Short Name", "Assigned"),
    "PNTEST": ("text", "100", "Pain Assessment Test Name", "Assigned"),
    "PNCAT": ("text", "100", "Category for Pain Assessment", "Collected"),
    "PNORRES": ("text", "40", "Result or Finding in Original Units", "Collected"),
    
    # Supplemental core
    "RDOMAIN": ("text", "4", "Related Domain", "Assigned"),
    "IDVAR": ("text", "8", "Identifying Variable", "Assigned"),
    "IDVARVAL": ("text", "40", "Identifying Variable Value", "Assigned"),
    "QNAM": ("text", "8", "Qualifier Variable Name", "Assigned"),
    "QLABEL": ("text", "40", "Qualifier Variable Label", "Assigned"),
    "QVAL": ("text", "200", "Qualifier Variable Value", "Assigned"),
    "QORIG": ("text", "10", "Origin", "Assigned"),
    "QEVAL": ("text", "40", "Evaluator", "Assigned"),
}

def get_var_attrs(domain, var_name):
    # Find matching attributes or return a generic default
    if var_name in var_attr_defaults:
        return var_attr_defaults[var_name]
    
    # Try generic suffixes
    if var_name.endswith("DTC"):
        return ("text", "20", f"Date/Time of {var_name[:-3]}", "Collected")
    if var_name.endswith("DY"):
        return ("integer", "8", f"Study Day of {var_name[:-2]}", "Derived")
    if var_name.endswith("SEQ"):
        return ("integer", "8", "Sequence Number", "Assigned")
    if var_name.endswith("FL"):
        return ("text", "1", "Flag", "Derived")
    
    # Generic default fallback
    return ("text", "100", f"{var_name} Variable for domain {domain}", "Collected")

def generate_define_xml(output_path):
    current_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("<?xml version='1.0' encoding='utf-8'?>\n")
        f.write('<?xml-stylesheet type="text/xsl" href="define2-1.xsl"?>\n')
        f.write('<Define xmlns="http://www.cdisc.org/ns/def/v2.1" '
                'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                'xsi:schemaLocation="http://www.cdisc.org/ns/def/v2.1 http://schema.cdisc.org/define/v2.1/define2-1-0.xsd" '
                'FileOID="TROPIC_SDTM_Metadata_v2.1" '
                f'AsOfDateTime="{current_ts}" '
                'DefineVersion="2.1.0" '
                'Originator="Principal Clinical Data Infrastructure Architect">\n\n')
        
        f.write('  <MetaDataVersion OID="MDV.TROPIC_NCT00417079.SDTM.3.1.1" '
                'Name="TROPIC Trial SDTM Metadata Specification" '
                'Description="Metadata specification for TROPIC Phase III re-analysis SDTM datasets" '
                'CDISCLibraryID="SDTMIG.3.1.1" CDISCLibraryVersion="3.1.1">\n\n')
        
        # 1. Author ItemGroupDefs
        for dom, meta in domains_meta.items():
            label, is_rep, role, structure = meta
            purpose = "Tabulation"
            f.write(f'    <ItemGroupDef OID="IG.{dom}" Name="{dom}" Repeating="{is_rep}" '
                    f'IsReferenceData="No" Purpose="{purpose}" Role="{role}" '
                    f'Structure="{structure}" Label="{label}">\n')
            f.write(f'      <Description>{label} domain for the TROPIC trial datasets.</Description>\n')
            
            # Loop through the variables and define ItemRefs
            cols = domains_cols[dom]
            for idx, col in enumerate(cols, 1):
                f.write(f'      <ItemRef ItemOID="IT.{dom}.{col}" Order="{idx}" Mandatory="{"Yes" if col in ["STUDYID", "DOMAIN", "USUBJID"] else "No"}" />\n')
            
            f.write('    </ItemGroupDef>\n\n')
        
        # 2. Author ItemDefs
        f.write('    <!-- ========================================================================= -->\n')
        f.write('    <!-- Item Definitions                                                          -->\n')
        f.write('    <!-- ========================================================================= -->\n\n')
        
        for dom, cols in domains_cols.items():
            for col in cols:
                datatype, length, label, origin = get_var_attrs(dom, col)
                f.write(f'    <ItemDef OID="IT.{dom}.{col}" Name="{col}" DataType="{datatype}" Length="{length}" Label="{label}">\n')
                f.write(f'      <Origin Type="{origin}" Source="Sponsor" />\n')
                f.write('    </ItemDef>\n')
            f.write('\n')
            
        f.write('  </MetaDataVersion>\n')
        f.write('</Define>\n')

def main():
    proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_path = os.path.join(proj_root, "07_define_xml", "define_sdtm.xml")
    
    print(f"Generating SDTM define.xml at: {out_path}")
    generate_define_xml(out_path)
    print("Generation complete!")

if __name__ == "__main__":
    main()
