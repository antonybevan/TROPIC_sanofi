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
import re
import argparse
from datetime import datetime, timezone

# Fixed PDF creation/mod date so the rendered reviewer guides and CSR are byte-reproducible.
# The tracked data-free m5 preview must only change when content changes, not on every rebuild.
_PDF_DATE = datetime(2026, 6, 17, tzinfo=timezone.utc)

def clean_text(text, counter=None):
    """Replaces Unicode characters not supported by standard latin-1/Helvetica in FPDF.

    `counter`, if given a single-element list, has [0] incremented once per character silently
    substituted with '?' -- a rendered reviewer's guide/CSR is meant to accurately represent its
    markdown source, so a caller can report how many characters were altered instead of that
    substitution being completely invisible."""
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
            if counter is not None:
                counter[0] += 1
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
    pdf.creation_date = _PDF_DATE
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    in_table = False
    table_data = []
    bold_font = FontFace(emphasis="BOLD")
    replaced = [0]  # count of non-latin-1 chars silently '?'-substituted by clean_text below
    
    for line in lines:
        line_str = line.strip()
        
        # Check if we are in a table
        if line_str.startswith('|'):
            is_sep = all(c in '|- :+*' for c in line_str) and len(line_str.replace('|', '').strip()) > 0
            if is_sep:
                continue
            cells = [clean_text(c.strip(), replaced) for c in line_str.split('|')[1:-1]]
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
            # GFM alert marker (> [!WARNING]/[!NOTE]/etc). Every real source in this repo puts
            # the marker on its own line with the body on the NEXT '>' line, so stripping just
            # the marker leaves nothing here and the `continue` below is a no-op change from
            # before -- but if a marker and body ever DO share one line, the body text now
            # survives and renders instead of being silently discarded along with the marker.
            admonition = re.match(r'^\[!\w+\]\s*(.*)$', line_str)
            if admonition:
                line_str = admonition.group(1)
                if not line_str:
                    continue
            pdf.set_font("helvetica", "I", size=9)
            pdf.multi_cell(0, 5, clean_text(line_str, replaced))
            pdf.set_font("helvetica", size=10)
            pdf.ln(2)
            continue

        if line_str.startswith('# '):
            pdf.ln(4)
            pdf.set_font("helvetica", "B", size=15)
            pdf.multi_cell(0, 8, clean_text(line_str[2:], replaced))
            pdf.set_font("helvetica", size=10)
            pdf.ln(2)
        elif line_str.startswith('## '):
            pdf.ln(3)
            pdf.set_font("helvetica", "B", size=12)
            pdf.multi_cell(0, 7, clean_text(line_str[3:], replaced))
            pdf.set_font("helvetica", size=10)
            pdf.ln(2)
        elif line_str.startswith('### '):
            pdf.ln(2)
            pdf.set_font("helvetica", "B", size=11)
            pdf.multi_cell(0, 6, clean_text(line_str[4:], replaced))
            pdf.set_font("helvetica", size=10)
            pdf.ln(2)
        elif line_str.startswith('#### '):
            pdf.ln(2)
            pdf.set_font("helvetica", "B", size=10)
            pdf.multi_cell(0, 5, clean_text(line_str[5:], replaced))
            pdf.set_font("helvetica", size=10)
            pdf.ln(1)
        elif line_str.startswith('---'):
            # Draw line
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.line(x, y + 2, x + 190, y + 2)
            pdf.ln(4)
        elif line_str.startswith('* ') or line_str.startswith('- '):
            pdf.multi_cell(0, 5, " * " + clean_text(line_str[2:], replaced))
            pdf.ln(1)
        else:
            cleaned = clean_text(line_str, replaced)
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

    if replaced[0]:
        print(f"  {replaced[0]} character(s) replaced with '?' (non-latin-1) in {md_path}")
    pdf.output(pdf_path)

def copy_source_crf(pdf_path):
    """Copy the available source CRF; never generate a fabricated CRF placeholder."""
    src = "01_raw_source/Sanofi CRF Tropic.pdf"
    if not os.path.exists(src):
        sys.exit(
            "Missing source CRF: 01_raw_source/Sanofi CRF Tropic.pdf. "
            "The package refuses to create a placeholder CRF."
        )
    shutil.copy2(src, pdf_path)
    print(
        "Copied source CRF to blankcrf.pdf. "
        "Release note: this is not an annotated CRF unless annotation evidence is supplied."
    )

def copy_uplifted_sdtm34_xpts(sdtm34_dir, out_dir):
    """Copy the SDTMIG 3.4 XPT layer that matches define_sdtm.xml."""
    xpts = sorted(glob.glob(os.path.join(sdtm34_dir, "*.xpt")))
    if not xpts:
        sys.exit(
            "Missing uplifted SDTMIG 3.4 XPT layer at .core_run/sdtm34/*.xpt. "
            "Run: Rscript 06_telemetry/uplift_sdtm_34.R before building a full package. "
            "Raw SDTMIG 3.1.1 conversion is not allowed when define_sdtm.xml declares SDTMIG 3.4."
        )
    os.makedirs(out_dir, exist_ok=True)
    for f in xpts:
        shutil.copy2(f, os.path.join(out_dir, os.path.basename(f)))
    print(f"Copied {len(xpts)} uplifted SDTMIG 3.4 XPT datasets from {sdtm34_dir}.")


def _require_exists(path, what):
    """Fail with a clear, actionable message -- matching copy_source_crf/copy_uplifted_sdtm34_xpts's
    existing style -- instead of a raw FileNotFoundError traceback when a file this packaging
    step depends on (but doesn't itself copy/render) is missing. Used ahead of a bare shutil.copy
    or md_to_pdf call for a file that's required, not merely optional-if-present."""
    if not os.path.exists(path):
        sys.exit(f"Missing required file for eCTD packaging: {path} ({what}). "
                  "Ensure the pipeline has run successfully before packaging.")


def copy_if_present(src, action, label):
    """Run `action()` (a copy/render) if `src` exists; otherwise print an explicit
    '[WARNING] ... omitted' line, so a maintainer sees a missing optional full-mode artifact in
    the console log instead of needing to diff directory listings against expectations. These
    are optional-if-present artifacts (BDRG render, ADaM spec, spec->define conformance report)
    -- not hard requirements like the ADaM/BIMO datasets, so a missing one warns, not fails."""
    if os.path.exists(src):
        action()
        return True
    print(f"  [WARNING] {label} not found at '{src}' — omitted from the package.")
    return False


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
    sdtm34_xpt_dir = ".core_run/sdtm34"
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
    
    # 3. SDTM tabulation datasets (XPORT v5). The full package must use the
    # SDTMIG 3.4 uplifted layer that matches define_sdtm.xml. Raw source SDTMIG
    # 3.1.1 conversion is retained as a utility function, but is not an allowed
    # packaging fallback because it creates metadata/data drift.
    if data_free:
        print("Preview mode: skipping SDTM dataset conversion (patient-level data excluded).")
        write_dataset_placeholder(m5_sdtm_datasets_dir)
    else:
        print("Copying uplifted SDTMIG 3.4 datasets to Version 5 XPT package folder...")
        copy_uplifted_sdtm34_xpts(sdtm34_xpt_dir, m5_sdtm_datasets_dir)
            
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
    else:
        # clinsite is a required BIMO deliverable (per the BIMO TCG comment above), not an
        # optional one -- mirrors the ADaM '*_prod.xpt' guard three lines above this block,
        # which correctly hard-fails on the exact same shape of missing input.
        print("Error: Missing BIMO 'clinsite_prod.xpt' in 04_adam/. Ensure pipeline has run "
              "successfully.")
        sys.exit(1)
    bdrg_file = "08_reviewers_guides/BDRG.md"
    # Rendered to PDF for parity with the SDRG/ADRG reviewer guides (a submission package
    # ships rendered guides, not raw Markdown).
    if copy_if_present(bdrg_file,
                        lambda: md_to_pdf(bdrg_file, os.path.join(m5_bimo_dir, "bdrg.pdf")),
                        "BDRG (08_reviewers_guides/BDRG.md)"):
        print("  Generated BIMO data reviewer's guide (bdrg.pdf).")

    # 4c. Copy the authoritative ADaM specification (audit C-4 inversion): ADaM_spec.xlsx
    # is the upstream metadata control source (CDISC/Pinnacle-21 metacore format) that
    # governs define.xml -- not a rendering derived from it. Ship it alongside the
    # spec->define conformance report that proves define.xml matches the spec.
    print("Copying authoritative ADaM specification + conformance evidence...")
    spec_file = "00_specifications/ADaM_spec.xlsx"
    if copy_if_present(spec_file,
                        lambda: shutil.copy(spec_file, os.path.join(m5_adam_dir, "ADaM_spec.xlsx")),
                        "ADaM specification (00_specifications/ADaM_spec.xlsx)"):
        print("  Copied ADaM_spec.xlsx (governing specification).")
    conf_file = "06_telemetry/conformance/spec_define_conformance.json"
    if copy_if_present(
            conf_file,
            lambda: shutil.copy(conf_file, os.path.join(m5_adam_dir, "spec_define_conformance.json")),
            "spec->define conformance report (06_telemetry/conformance/spec_define_conformance.json)"):
        print("  Copied spec->define conformance report.")
        
    # 5. Co-locate Define-XML metadata
    print("Copying Define-XML metadata...")
    # SDTM Define
    _require_exists(os.path.join(define_src_dir, "define_sdtm.xml"), "SDTM Define-XML")
    shutil.copy(os.path.join(define_src_dir, "define_sdtm.xml"), os.path.join(m5_sdtm_datasets_dir, "define.xml"))
    _require_exists(os.path.join(define_src_dir, "define2-1.xsl"), "Define-XML stylesheet")
    shutil.copy(os.path.join(define_src_dir, "define2-1.xsl"), os.path.join(m5_sdtm_datasets_dir, "define2-1.xsl"))
    print("  Copied SDTM define.xml and define2-1.xsl.")
    # ADaM Define
    _require_exists(os.path.join(define_src_dir, "define.xml"), "ADaM Define-XML")
    shutil.copy(os.path.join(define_src_dir, "define.xml"), os.path.join(m5_adam_datasets_dir, "define.xml"))
    _require_exists(os.path.join(define_src_dir, "define2-1.xsl"), "Define-XML stylesheet")
    shutil.copy(os.path.join(define_src_dir, "define2-1.xsl"), os.path.join(m5_adam_datasets_dir, "define2-1.xsl"))
    print("  Copied ADaM define.xml and define2-1.xsl.")

    # 6. Generate PDFs for Reviewer's Guides and CSR
    print("Generating Reviewer's Guides and CSR PDFs...")
    # SDRG
    _require_exists(os.path.join(guides_src_dir, "SDRG.md"), "SDRG (Study Data Reviewer's Guide)")
    md_to_pdf(os.path.join(guides_src_dir, "SDRG.md"), os.path.join(m5_sdtm_dir, "sdrg.pdf"))
    # ADRG
    _require_exists(os.path.join(guides_src_dir, "ADRG.md"), "ADRG (Analysis Data Reviewer's Guide)")
    md_to_pdf(os.path.join(guides_src_dir, "ADRG.md"), os.path.join(m5_adam_dir, "adrg.pdf"))
    # CSR
    _require_exists(csr_src_file, "Clinical Study Report source")
    md_to_pdf(csr_src_file, os.path.join(m5_csr_dir, "csr.pdf"))
    print("  Successfully generated SDRG, ADRG, and CSR PDFs.")
    
    # 7. Copy the available source CRF. Do not fabricate a placeholder CRF.
    copy_source_crf(os.path.join(m5_sdtm_dir, "blankcrf.pdf"))
    
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
