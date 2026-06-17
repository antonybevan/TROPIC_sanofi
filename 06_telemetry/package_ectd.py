#!/usr/bin/env python3
"""
TROPIC eCTD Module 5 Packaging Orchestrator
Creates the canonical FDA m5 directory tree and packages datasets, programs,
metadata, reviewer guides, and clinical study reports (CSR) with output TFLs.
"""

import os
import sys
import shutil
import glob
import subprocess
import re
import argparse

# Resolve Rscript path
def resolve_rscript():
    rscript = shutil.which("Rscript")
    if rscript:
        return rscript
    # Environment override
    rscript = os.environ.get("TROPIC_RSCRIPT")
    if rscript:
        return rscript
    # Common locations
    if sys.platform == "win32":
        candidates = [
            os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "R"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\R"),
        ]
        for base in candidates:
            hits = glob.glob(os.path.join(base, "R-*", "bin", "Rscript.exe")) if base else []
            if hits:
                return sorted(hits)[-1]
    else:
        for path in ["/usr/local/bin/Rscript", "/opt/homebrew/bin/Rscript",
                     "/Library/Frameworks/R.framework/Resources/bin/Rscript"]:
            if os.path.exists(path):
                return path
    return "Rscript"

RSCRIPT_PATH = resolve_rscript()

def clean_text(text):
    """Replaces Unicode characters not supported by standard latin-1/Helvetica in FPDF."""
    text = text.replace('\u2013', '-')
    text = text.replace('\u2014', '--')
    text = text.replace('\u201c', '"')
    text = text.replace('\u201d', '"')
    text = text.replace('\u2018', "'")
    text = text.replace('\u2019', "'")
    text = text.replace('\u2022', '*')
    text = text.replace('\u2026', '...')
    text = text.replace('\u2020', '[dagger]')
    text = text.replace('\u2021', '[double-dagger]')
    text = text.replace('\xb7', '*')
    text = text.replace('\xe0', 'a')
    text = text.replace('\xe9', 'e')
    # Clean other non-latin-1 characters
    cleaned = []
    for char in text:
        try:
            char.encode('latin-1')
            cleaned.append(char)
        except UnicodeEncodeError:
            cleaned.append('?')
    return "".join(cleaned)

def md_to_pdf(md_path, pdf_path):
    """Converts a Markdown file to a styled PDF using fpdf2."""
    from fpdf import FPDF
    from fpdf.fonts import FontFace
    
    class PDF(FPDF):
        def header(self):
            self.set_font('helvetica', 'B', 8)
            self.cell(0, 10, 'TROPIC Clinical Analysis & FDA eCTD Module 5 Package', border=0, align='R')
            self.ln(10)
        def footer(self):
            self.set_y(-15)
            self.set_font('helvetica', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', border=0, align='C')

    print(f"Converting Markdown: {md_path} -> PDF: {pdf_path}")
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    in_table = False
    table_data = []
    bold_font = FontFace(emphasis="BOLD")
    
    for line in lines:
        line_str = line.strip()
        
        # Check if we are in a table
        if line_str.startswith('|'):
            is_sep = all(c in '|- :+*' for c in line_str) and len(line_str.replace('|', '').strip()) > 0
            if is_sep:
                continue
            cells = [clean_text(c.strip()) for c in line_str.split('|')[1:-1]]
            table_data.append(cells)
            in_table = True
            continue
        else:
            if in_table and table_data:
                # Render the parsed table
                pdf.ln(2)
                try:
                    with pdf.table(text_align="LEFT") as table:
                        for r_idx, row in enumerate(table_data):
                            row_cells = table.row()
                            for cell in row:
                                if r_idx == 0:
                                    row_cells.cell(cell, style=bold_font)
                                else:
                                    row_cells.cell(cell)
                except Exception as e:
                    print(f"Table render exception: {e}")
                    pdf.set_font("helvetica", "B", 9)
                    for r_idx, row in enumerate(table_data):
                        row_str = " | ".join(row)
                        pdf.multi_cell(0, 6, row_str)
                        pdf.set_font("helvetica", "", 9)
                    pdf.ln(2)
                table_data = []
                in_table = False
                pdf.ln(2)
            
        if not line_str:
            pdf.ln(3)
            continue
            
        # Handle markdown blocks and headers
        if line_str.startswith('>'):
            line_str = line_str.lstrip('>').strip()
            if line_str.startswith('[!'):
                continue
            pdf.set_font("helvetica", "I", size=9)
            pdf.multi_cell(0, 5, clean_text(line_str))
            pdf.set_font("helvetica", size=10)
            pdf.ln(2)
            continue
            
        if line_str.startswith('# '):
            pdf.ln(4)
            pdf.set_font("helvetica", "B", size=15)
            pdf.multi_cell(0, 8, clean_text(line_str[2:]))
            pdf.set_font("helvetica", size=10)
            pdf.ln(2)
        elif line_str.startswith('## '):
            pdf.ln(3)
            pdf.set_font("helvetica", "B", size=12)
            pdf.multi_cell(0, 7, clean_text(line_str[3:]))
            pdf.set_font("helvetica", size=10)
            pdf.ln(2)
        elif line_str.startswith('### '):
            pdf.ln(2)
            pdf.set_font("helvetica", "B", size=11)
            pdf.multi_cell(0, 6, clean_text(line_str[4:]))
            pdf.set_font("helvetica", size=10)
            pdf.ln(2)
        elif line_str.startswith('#### '):
            pdf.ln(2)
            pdf.set_font("helvetica", "B", size=10)
            pdf.multi_cell(0, 5, clean_text(line_str[5:]))
            pdf.set_font("helvetica", size=10)
            pdf.ln(1)
        elif line_str.startswith('---'):
            # Draw line
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.line(x, y + 2, x + 190, y + 2)
            pdf.ln(4)
        elif line_str.startswith('* ') or line_str.startswith('- '):
            pdf.multi_cell(0, 5, " * " + clean_text(line_str[2:]))
            pdf.ln(1)
        else:
            cleaned = clean_text(line_str)
            # Remove markdown links [label](url) -> label
            cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned)
            cleaned = cleaned.replace('**', '').replace('*', '').replace('`', '')
            pdf.multi_cell(0, 5, cleaned)
            pdf.ln(1.5)
            
    # Handle end of file table edge case
    if in_table and table_data:
        pdf.ln(2)
        try:
            with pdf.table(text_align="LEFT") as table:
                for r_idx, row in enumerate(table_data):
                    row_cells = table.row()
                    for cell in row:
                        if r_idx == 0:
                            row_cells.cell(cell, style=bold_font)
                        else:
                            row_cells.cell(cell)
        except Exception as e:
            pdf.set_font("helvetica", "B", 9)
            for r_idx, row in enumerate(table_data):
                row_str = " | ".join(row)
                pdf.multi_cell(0, 6, row_str)
                pdf.set_font("helvetica", "", 9)
            pdf.ln(2)
            
    pdf.output(pdf_path)

def generate_blank_crf(pdf_path):
    """Generates a placeholder case report form PDF."""
    from fpdf import FPDF
    print(f"Generating Blank CRF: {pdf_path}")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 20, "TROPIC Study - Blank Case Report Form (CRF)", align="C")
    pdf.ln(20)
    pdf.set_font("helvetica", "", 12)
    pdf.multi_cell(0, 10, "This is a placeholder for the blank Case Report Form (CRF) for Study EFC6193 / XRP6258.\n\nIn a standard regulatory submission, this PDF would contain the annotated Case Report Forms used during the clinical trial to collect patient-level data.", align="C")
    pdf.output(pdf_path)

def convert_sdtm_to_xpt(sdtm_src_dir, out_dir):
    """Convert the source SDTM SAS7BDAT files to SAS Transport (XPORT v5) via R/haven."""
    r_converter_script = "sdtm_to_xpt.R"
    r_converter_content = f"""
suppressMessages({{ library(haven) }})
files <- list.files("{sdtm_src_dir}", pattern = "\\\\.sas7bdat$", full.names = TRUE)
out_dir <- "{out_dir}"
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
for (f in files) {{
  dom <- tools::file_path_sans_ext(basename(f))
  out_path <- file.path(out_dir, paste0(dom, ".xpt"))
  df <- as.data.frame(read_sas(f))
  for (col in names(df)) {{
    if (inherits(df[[col]], "Date")) df[[col]] <- as.numeric(df[[col]]) + 3653
  }}
  write_xpt(df, out_path, version = 5, name = toupper(dom))
}}
cat("SDTM conversion completed successfully.\\n")
"""
    with open(r_converter_script, "w", encoding="utf-8") as rf:
        rf.write(r_converter_content)
    try:
        res = subprocess.run([RSCRIPT_PATH, r_converter_script], capture_output=True, text=True)
        if res.returncode != 0:
            print("Error: SDTM to XPT conversion via R failed.")
            print(res.stderr)
            sys.exit(1)
        print("Successfully converted all SDTM SAS7BDAT datasets to XPT.")
    finally:
        if os.path.exists(r_converter_script):
            os.remove(r_converter_script)


def write_dataset_placeholder(folder):
    """In data-free preview mode, drop a note where the patient-level *.xpt would sit."""
    os.makedirs(folder, exist_ok=True)
    note = (
        "DATASETS EXCLUDED FROM THIS DATA-FREE PREVIEW\n"
        "=============================================\n\n"
        "This eCTD Module 5 tree was assembled in PREVIEW (data-free) mode:\n"
        "    python3 06_telemetry/package_ectd.py --preview\n\n"
        "The SAS Transport (XPORT v5, *.xpt) datasets that belong in this folder are\n"
        "deliberately NOT included. They are de-identified, patient-level clinical-trial\n"
        "data obtained via Project Data Sphere under a Data Use Agreement that does not\n"
        "permit public redistribution; the project therefore never commits row-level data.\n"
        "The co-located define.xml fully describes the datasets that would be present here\n"
        "(structure, variables, controlled terminology, and derivations/origins).\n\n"
        "To materialise the datasets locally (with the licensed source data present):\n"
        "    python3 06_telemetry/package_ectd.py\n"
    )
    with open(os.path.join(folder, "README_datasets_excluded.txt"), "w", encoding="utf-8") as fh:
        fh.write(note)


def main(data_free=False):
    mode = "DATA-FREE PREVIEW" if data_free else "FULL"
    print(f"=== STARTING eCTD MODULE 5 PACKAGING ({mode}) ===")
    
    # 1. Define paths
    sdtm_src_dir = "01_raw_source/real_sdtm"
    adam_src_dir = "04_adam"
    define_src_dir = "07_define_xml"
    guides_src_dir = "08_reviewers_guides"
    csr_src_file = "ANALYSIS_REPORT.md"
    tfl_src_dir = "09_tfl/output"
    
    m5_root = "m5"
    m5_sdtm_dir = os.path.join(m5_root, "datasets/tropic/tabulations/sdtm")
    m5_sdtm_datasets_dir = os.path.join(m5_sdtm_dir, "datasets")
    
    m5_adam_dir = os.path.join(m5_root, "datasets/tropic/analysis/adam")
    m5_adam_datasets_dir = os.path.join(m5_adam_dir, "datasets")
    m5_adam_programs_dir = os.path.join(m5_adam_dir, "programs")
    
    m5_bimo_dir = os.path.join(m5_root, "datasets/tropic/bimo/datasets")
    m5_csr_dir = os.path.join(m5_root, "53-clin-stud-rep/535-rep-effic-safety-stud/mcrpc/5351-stud-rep-contr/tropic")
    
    # Check that required input files/directories exist. The data-free preview needs none
    # of the (uncommitted, licensed) source/derived data, so its required set is narrower.
    required_inputs = [
        define_src_dir, guides_src_dir, csr_src_file, tfl_src_dir,
        "02_production_sas", "03_validation_r", "09_tfl"
    ]
    if not data_free:
        required_inputs = [sdtm_src_dir, adam_src_dir] + required_inputs
    for inp in required_inputs:
        if not os.path.exists(inp):
            print(f"Error: Missing required input '{inp}'. Ensure pipeline has run successfully.")
            sys.exit(1)
            
    # 2. Re-create target folder structure
    if os.path.exists(m5_root):
        print(f"Cleaning existing {m5_root}/ folder...")
        shutil.rmtree(m5_root)
        
    os.makedirs(m5_sdtm_datasets_dir, exist_ok=True)
    os.makedirs(m5_adam_datasets_dir, exist_ok=True)
    os.makedirs(m5_adam_programs_dir, exist_ok=True)
    os.makedirs(m5_bimo_dir, exist_ok=True)
    os.makedirs(m5_csr_dir, exist_ok=True)
    
    print("Created target folder structure under m5/.")
    
    # 3. SDTM tabulation datasets (XPORT v5) — converted from source SAS7BDAT via R.
    if data_free:
        print("Preview mode: skipping SDTM dataset conversion (patient-level data excluded).")
        write_dataset_placeholder(m5_sdtm_datasets_dir)
    else:
        print("Converting SDTM datasets to Version 5 XPT format...")
        convert_sdtm_to_xpt(sdtm_src_dir, m5_sdtm_datasets_dir)
            
    # 4. Copy ADaM Datasets and strip '_prod' suffix (skipped in data-free preview)
    if data_free:
        print("Preview mode: skipping ADaM dataset copy (patient-level data excluded).")
        write_dataset_placeholder(m5_adam_datasets_dir)
    else:
        print("Copying ADaM datasets...")
        adam_prod_files = glob.glob(os.path.join(adam_src_dir, "*_prod.xpt"))
        if not adam_prod_files:
            print("Error: No ADaM '*_prod.xpt' datasets found in 04_adam/.")
            sys.exit(1)
        for f in adam_prod_files:
            base = os.path.basename(f)
            new_base = base.replace("_prod.xpt", ".xpt")
            dest = os.path.join(m5_adam_datasets_dir, new_base)
            shutil.copy(f, dest)
            print(f"  Copied and renamed: {base} -> {new_base}")

    # 4b. Copy BIMO Datasets + its data-definition guide (BDRG). clinsite is delivered
    # with its own documentation (it is NOT in the ADaM define.xml) per the BIMO TCG.
    print("Copying BIMO package...")
    bimo_prod_file = os.path.join(adam_src_dir, "clinsite_prod.xpt")
    if data_free:
        write_dataset_placeholder(m5_bimo_dir)
    elif os.path.exists(bimo_prod_file):
        shutil.copy(bimo_prod_file, os.path.join(m5_bimo_dir, "clinsite.xpt"))
        print("  Copied BIMO clinsite.xpt.")
    bdrg_file = "08_reviewers_guides/BDRG.md"
    if os.path.exists(bdrg_file):
        # Render to PDF for parity with the SDRG/ADRG reviewer guides (a submission
        # package ships rendered guides, not raw Markdown).
        md_to_pdf(bdrg_file, os.path.join(m5_bimo_dir, "bdrg.pdf"))
        print("  Generated BIMO data reviewer's guide (bdrg.pdf).")

    # 4c. Copy the authoritative ADaM specification (audit C-4 inversion): ADaM_spec.xlsx
    # is the upstream single source of truth (CDISC/Pinnacle-21 metacore format) that
    # GOVERNS define.xml -- not a rendering derived from it. Ship it alongside the
    # spec->define conformance report that proves define.xml matches the spec.
    print("Copying authoritative ADaM specification + conformance evidence...")
    spec_file = "00_specifications/ADaM_spec.xlsx"
    if os.path.exists(spec_file):
        shutil.copy(spec_file, os.path.join(m5_adam_dir, "ADaM_spec.xlsx"))
        print("  Copied ADaM_spec.xlsx (governing specification).")
    conf_file = "06_telemetry/conformance/spec_define_conformance.json"
    if os.path.exists(conf_file):
        shutil.copy(conf_file, os.path.join(m5_adam_dir, "spec_define_conformance.json"))
        print("  Copied spec->define conformance report.")
        
    # 5. Co-locate Define-XML metadata
    print("Copying Define-XML metadata...")
    # SDTM Define
    shutil.copy(os.path.join(define_src_dir, "define_sdtm.xml"), os.path.join(m5_sdtm_datasets_dir, "define.xml"))
    shutil.copy(os.path.join(define_src_dir, "define2-1.xsl"), os.path.join(m5_sdtm_datasets_dir, "define2-1.xsl"))
    print("  Copied SDTM define.xml and define2-1.xsl.")
    # ADaM Define
    shutil.copy(os.path.join(define_src_dir, "define.xml"), os.path.join(m5_adam_datasets_dir, "define.xml"))
    shutil.copy(os.path.join(define_src_dir, "define2-1.xsl"), os.path.join(m5_adam_datasets_dir, "define2-1.xsl"))
    print("  Copied ADaM define.xml and define2-1.xsl.")
    
    # 6. Generate PDFs for Reviewer's Guides and CSR
    print("Generating Reviewer's Guides and CSR PDFs...")
    # SDRG
    md_to_pdf(os.path.join(guides_src_dir, "SDRG.md"), os.path.join(m5_sdtm_dir, "sdrg.pdf"))
    # ADRG
    md_to_pdf(os.path.join(guides_src_dir, "ADRG.md"), os.path.join(m5_adam_dir, "adrg.pdf"))
    # CSR (both csr.pdf and tropic.pdf for maximal path safety)
    md_to_pdf(csr_src_file, os.path.join(m5_csr_dir, "csr.pdf"))
    shutil.copy(os.path.join(m5_csr_dir, "csr.pdf"), os.path.join(m5_csr_dir, "tropic.pdf"))
    print("  Successfully generated SDRG, ADRG, and CSR PDFs.")
    
    # 7. Generate Blank CRF placeholder
    generate_blank_crf(os.path.join(m5_sdtm_dir, "blankcrf.pdf"))
    
    # 8. Copy programs (SAS, R, TFL source codes)
    print("Copying analysis and validation programs to m5/datasets/tropic/analysis/adam/programs/...")
    # SAS programs
    sas_files = glob.glob(os.path.join("02_production_sas", "*.sas"))
    for f in sas_files:
        shutil.copy(f, m5_adam_programs_dir)
    # R programs
    r_files = glob.glob(os.path.join("03_validation_r", "*.R"))
    for f in r_files:
        shutil.copy(f, m5_adam_programs_dir)
    # TFL programs
    shutil.copy("09_tfl/tfl_generation.R", m5_adam_programs_dir)
    shutil.copy("09_tfl/tfl_stats.R", m5_adam_programs_dir)
    # spec -> define conformance program (ships with its spec_define_conformance.json report)
    extra_programs = ["07_define_xml/check_define_conformance.R"]
    n_extra = 0
    for f in extra_programs:
        if os.path.exists(f):
            shutil.copy(f, m5_adam_programs_dir)
            n_extra += 1
    print(f"  Successfully copied {len(sas_files)} SAS files, {len(r_files)} R files, "
          f"2 TFL R scripts, and {n_extra} conformance program(s).")
    
    # 9. Copy output TFLs into CSR Appendices
    print("Copying output TFLs (tables, listings, figures) to CSR appendices...")
    # Preserve subdirectories: figures, tables, listings
    for subdir in ["figures", "tables", "listings"]:
        src_path = os.path.join(tfl_src_dir, subdir)
        dest_path = os.path.join(m5_csr_dir, subdir)
        if os.path.exists(src_path):
            # Never ship VCS scaffolding (.gitkeep) or other hidden files in a submission.
            shutil.copytree(src_path, dest_path,
                            ignore=shutil.ignore_patterns(".gitkeep", ".*"))
            print(f"  Copied subdirectory {subdir} -> {dest_path}")
            
    print("\n=== eCTD MODULE 5 PACKAGING COMPLETED SUCCESSFULLY ===")
    if data_free:
        print("Canonical FDA layout built in 'm5/' (DATA-FREE PREVIEW — no patient-level *.xpt).")
    else:
        print("Canonical FDA layout built in 'm5/'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TROPIC eCTD Module 5 packaging orchestrator.")
    parser.add_argument(
        "--preview", "--data-free", dest="preview", action="store_true",
        help="Build a committable, data-free preview: the full eCTD tree with metadata, "
             "rendered reviewer guides/CSR, the ADaM spec, conformance reports and TFLs, but "
             "with placeholder notes where the patient-level *.xpt would sit (no source data "
             "or SAS engine required).")
    args = parser.parse_args()
    main(data_free=args.preview)
