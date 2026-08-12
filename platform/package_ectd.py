#!/usr/bin/env python3
"""
TROPIC eCTD Module 5 Packaging Orchestrator
Creates the canonical FDA Module 5 package tree and packages datasets, programs,
metadata, reviewer guides, and clinical study reports (CSR) with output TFLs.
"""

import os
import sys
import shutil
import glob
import hashlib
import re
import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Fixed submission-surface remediation date keeps the rendered reviewer guides
# and CSR byte-reproducible while accurately post-dating their 2026-08-05 content.
_PDF_DATE = datetime(2026, 8, 9, tzinfo=timezone.utc)

# Convert typographic symbols used by the reviewer Markdown to readable ASCII.
# The generated PDFs use an embedded TrueType font, but clinical thresholds and
# derivation operators should remain searchable/copyable without glyph ambiguity.
_ASCII_REPLACEMENTS = {
    "\u2013": "-", "\u2014": "--", "\u2011": "-", "\u2212": "-",
    "\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'",
    "\u2022": "*", "\u2026": "...", "\u00b7": "*",
    "\u2020": "(1) ", "\u2021": "(2) ",
    "\u00a7": "Section ", "\u2190": "<-", "\u2192": "->",
    "\u2194": "<->", "\u21d2": "=>", "\u2260": "!=",
    "\u2264": "<=", "\u2265": ">=", "\u2248": "~", "\u2208": "in",
    "\u2227": "and", "\u00b1": "+/-", "\u00d7": "x",
    "\u03bc": "u", "\u00b5": "u", "\u00b2": "2", "\u00b3": "3",
    "\u2033": '"',
}

def clean_text(text, counter=None):
    """Return submission-safe text and count unsupported glyph substitutions.

    `counter`, if given a single-element list, has [0] incremented once per character silently
    substituted with '?' -- a rendered reviewer's guide/CSR is meant to accurately represent its
    markdown source, so a caller can report how many characters were altered instead of that
    substitution being completely invisible."""
    for source, replacement in _ASCII_REPLACEMENTS.items():
        text = text.replace(source, replacement)
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


def clean_markdown(text, counter=None):
    """Return readable plain text for every Markdown block type."""
    cleaned = clean_text(text, counter)
    cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned)
    return cleaned.replace('**', '').replace('__', '').replace('*', '').replace('`', '')

def split_markdown_table_row(line):
    r"""Split a pipe table row while preserving escaped literal pipes.

    A plain ``str.split('|')`` corrupts expressions such as ``"PI_" \|\| SITEID``
    into extra PDF columns. This small state machine implements the relevant
    Markdown escape rule and is intentionally exported for regression tests.
    """
    cells, current = [], []
    escaped = False
    for char in line.strip():
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "|":
            cells.append("".join(current))
            current = []
        else:
            current.append(char)
    if escaped:
        current.append("\\")
    cells.append("".join(current))
    if line.strip().startswith("|"):
        cells = cells[1:]
    if line.strip().endswith("|"):
        cells = cells[:-1]
    return [cell.strip() for cell in cells]


def _submission_font_files():
    """Locate a complete sans-serif family suitable for embedded PDF output."""
    configured = os.environ.get("TROPIC_PDF_FONT_DIR")
    roots = [Path(configured)] if configured else []
    roots.extend([
        Path("/System/Library/Fonts/Supplemental"),
        Path("/usr/share/fonts/truetype/liberation2"),
        Path("/usr/share/fonts/truetype/liberation"),
        Path("C:/Windows/Fonts"),
    ])
    families = [
        ("Arial.ttf", "Arial Bold.ttf", "Arial Italic.ttf", "Arial Bold Italic.ttf"),
        ("LiberationSans-Regular.ttf", "LiberationSans-Bold.ttf",
         "LiberationSans-Italic.ttf", "LiberationSans-BoldItalic.ttf"),
        ("arial.ttf", "arialbd.ttf", "ariali.ttf", "arialbi.ttf"),
    ]
    for root in roots:
        for names in families:
            paths = tuple(root / name for name in names)
            if all(path.is_file() for path in paths):
                return paths
    raise SystemExit(
        "No embeddable Arial/Liberation Sans family found. Install fonts-liberation "
        "or point TROPIC_PDF_FONT_DIR at regular/bold/italic/bold-italic font files."
    )


def md_to_pdf(md_path, pdf_path):
    """Convert Markdown to a navigable, submission-oriented PDF using fpdf2."""
    from fpdf import FPDF
    from fpdf.enums import MethodReturnValue, XPos, YPos
    from fpdf.fonts import FontFace, TextStyle
    from fpdf.outline import TableOfContents

    font_family = "submission"

    class PDF(FPDF):
        def header(self):
            self.set_y(10)
            self.set_font(font_family, "B", 9)
            self.cell(
                0, 5, "TROPIC Clinical Analysis & FDA eCTD Module 5 Package",
                border=0, align="R",
            )
            # Automatic page breaks invoke header() before positioning the next
            # body fragment.  Restore the document top margin explicitly so a
            # continued paragraph or table cannot collide with the header.
            self.set_y(self.t_margin)

        def footer(self):
            self.set_y(-13)
            self.set_font(font_family, "I", 9)
            self.cell(0, 5, f"Page {self.page_no()}/{{nb}}", border=0, align="C")

    print(f"Converting Markdown: {md_path} -> PDF: {pdf_path}")
    pdf = PDF(format="Letter", unit="mm")
    regular, bold, italic, bold_italic = _submission_font_files()
    pdf.add_font(font_family, "", str(regular))
    pdf.add_font(font_family, "B", str(bold))
    pdf.add_font(font_family, "I", str(italic))
    pdf.add_font(font_family, "BI", str(bold_italic))
    pdf.set_margins(left=19.05, top=20, right=12.7)
    pdf.set_auto_page_break(auto=True, margin=17)
    pdf.creation_date = _PDF_DATE
    pdf.pdf_version = "1.7"
    pdf.alias_nb_pages()
    pdf.set_compression(True)
    pdf.set_subject("TROPIC controlled non-submission demonstration reviewer document")
    pdf.set_author("TROPIC clinical biometrics portfolio")
    pdf.set_creator("TROPIC platform/package_ectd.py")
    pdf.set_lang("en-US")
    pdf.page_mode = "USE_OUTLINES"
    pdf.set_display_mode("default", "single")
    pdf.add_page()
    pdf.set_font(font_family, size=10)

    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    document_title = next(
        (clean_markdown(line.strip()[2:]) for line in lines if line.strip().startswith("# ")),
        Path(md_path).stem,
    )
    pdf.set_title(document_title)

    in_table = False
    in_code = False
    table_data = []
    heading_style = FontFace(emphasis="BOLD", fill_color=(232, 237, 242))
    replaced = [0]
    toc_inserted = False
    toc = TableOfContents(
        text_style=TextStyle(font_family=font_family, font_size_pt=9),
        level_indent=5,
        line_spacing=1.25,
        ignore_pages_before_toc=True,
    )

    def render_text_block(text, line_height, **kwargs):
        """Keep ordinary Markdown blocks out of FPDF's unsafe split-cell path."""
        height = pdf.multi_cell(
            0,
            line_height,
            text,
            dry_run=True,
            output=MethodReturnValue.HEIGHT,
            **kwargs,
        )
        body_height = pdf.h - pdf.t_margin - pdf.b_margin
        if height <= body_height and pdf.will_page_break(height):
            pdf.add_page()
        pdf.multi_cell(0, line_height, text, **kwargs)

    def render_table():
        nonlocal table_data, in_table
        if not table_data:
            in_table = False
            return
        widths = {len(row) for row in table_data}
        if len(widths) != 1 or 0 in widths:
            raise ValueError(
                f"Malformed Markdown table in {md_path}: inconsistent column counts "
                f"{[len(row) for row in table_data]}"
            )
        pdf.ln(1.5)
        pdf.set_font(font_family, size=9)
        with pdf.table(
            width=pdf.epw,
            text_align="LEFT",
            line_height=5,
            padding=1.2,
            headings_style=heading_style,
        ) as table:
            for row in table_data:
                table.row(row)
        pdf.set_font(font_family, size=10)
        pdf.ln(2)
        table_data = []
        in_table = False

    for line in lines:
        raw_line = line.rstrip("\r\n")
        line_str = raw_line.strip()

        if line_str.startswith("```"):
            if in_table:
                render_table()
            in_code = not in_code
            if not in_code:
                pdf.ln(1)
            continue
        if in_code:
            pdf.set_font(font_family, size=9)
            pdf.set_fill_color(245, 247, 249)
            render_text_block(
                clean_text(raw_line, replaced) or " ", 4.8, fill=True,
                new_x=XPos.LMARGIN, new_y=YPos.NEXT,
            )
            pdf.set_font(font_family, size=10)
            continue

        if line_str.startswith("|"):
            is_sep = (
                all(c in "|- :+*" for c in line_str)
                and len(line_str.replace("|", "").strip()) > 0
            )
            if is_sep:
                continue
            cells = [
                clean_markdown(cell, replaced)
                for cell in split_markdown_table_row(line_str)
            ]
            table_data.append(cells)
            in_table = True
            continue
        if in_table:
            render_table()

        if not line_str:
            pdf.ln(2.5)
            continue

        if line_str.startswith(">"):
            line_str = line_str.lstrip(">").strip()
            admonition = re.match(r"^\[!\w+\]\s*(.*)$", line_str)
            if admonition:
                line_str = admonition.group(1)
                if not line_str:
                    continue
            pdf.set_font(font_family, "I", size=9.5)
            pdf.set_text_color(55, 65, 75)
            render_text_block(
                clean_markdown(line_str, replaced), 5,
                new_x=XPos.LMARGIN, new_y=YPos.NEXT,
            )
            pdf.set_text_color(0, 0, 0)
            pdf.set_font(font_family, size=10)
            pdf.ln(1.5)
            continue

        heading = re.match(r"^(#{1,4})\s+(.+)$", line_str)
        if heading:
            level = len(heading.group(1)) - 1
            title = clean_markdown(heading.group(2), replaced)
            pdf.start_section(title, level=level, strict=False)
            sizes = (15, 13, 11.5, 10.5)
            heights = (8, 7, 6, 5.5)
            pdf.ln(3 if level < 2 else 2)
            pdf.set_font(font_family, "B", size=sizes[level])
            render_text_block(
                title, heights[level],
                new_x=XPos.LMARGIN, new_y=YPos.NEXT,
            )
            pdf.set_font(font_family, size=10)
            pdf.ln(1.5)
            if level == 0 and not toc_inserted:
                pdf.set_font(font_family, "B", 12)
                pdf.cell(0, 8, "Table of Contents")
                pdf.ln(10)
                pdf.set_font(font_family, size=9)
                pdf.insert_toc_placeholder(toc.render_toc, pages=1)
                pdf.set_font(font_family, size=10)
                toc_inserted = True
            continue

        if line_str.startswith("---"):
            x, y = pdf.get_x(), pdf.get_y()
            pdf.set_draw_color(120, 130, 140)
            pdf.line(x, y + 1, x + pdf.epw, y + 1)
            pdf.ln(4)
        elif line_str.startswith("* ") or line_str.startswith("- "):
            render_text_block(
                " - " + clean_markdown(line_str[2:], replaced), 5,
                new_x=XPos.LMARGIN, new_y=YPos.NEXT,
            )
            pdf.ln(0.8)
        else:
            render_text_block(
                clean_markdown(line_str, replaced), 5.2,
                new_x=XPos.LMARGIN, new_y=YPos.NEXT,
            )
            pdf.ln(1.2)

    if in_table:
        render_table()
    if in_code:
        raise ValueError(f"Unclosed fenced code block in {md_path}")
    if replaced[0]:
        raise ValueError(
            f"Refusing PDF with {replaced[0]} unsupported character substitution(s): {md_path}"
        )
    pdf_target = Path(pdf_path).resolve()
    pdf_target.parent.mkdir(parents=True, exist_ok=True)
    ghostscript = shutil.which("gs")
    if not ghostscript:
        raise SystemExit(
            "Ghostscript is required to linearize reviewer PDFs for Fast Web View."
        )
    raw_path = f"{pdf_target}.raw.pdf"
    optimized_path = f"{pdf_target}.optimized.pdf"
    pdf.output(raw_path)
    raw_digest = hashlib.sha256(Path(raw_path).read_bytes()).hexdigest()
    document_uuid = (
        f"{raw_digest[:8]}-{raw_digest[8:12]}-{raw_digest[12:16]}-"
        f"{raw_digest[16:20]}-{raw_digest[20:32]}"
    )
    environment = os.environ.copy()
    environment["SOURCE_DATE_EPOCH"] = str(int(_PDF_DATE.timestamp()))
    command = [
        ghostscript,
        "-q",
        "-dBATCH",
        "-dNOPAUSE",
        "-dSAFER",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.7",
        "-dFastWebView=true",
        "-dOmitID=true",
        "-dEmbedAllFonts=true",
        "-dSubsetFonts=false",
        "-dPreserveAnnots=true",
        "-dAutoRotatePages=/None",
        f"-sDocumentUUID={document_uuid}",
        f"-sInstanceUUID={document_uuid}",
        f"-sOutputFile={optimized_path}",
        "-c",
        (
            "[ /CreationDate "
            f"({_PDF_DATE.astimezone(timezone.utc).strftime('D:%Y%m%d%H%M%SZ')}) "
            "/ModDate "
            f"({_PDF_DATE.astimezone(timezone.utc).strftime('D:%Y%m%d%H%M%SZ')}) "
            "/DOCINFO pdfmark"
        ),
        "-f",
        raw_path,
    ]
    try:
        subprocess.run(
            command,
            check=True,
            cwd=pdf_target.parent,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        os.replace(optimized_path, pdf_target)
    finally:
        if os.path.exists(raw_path):
            os.remove(raw_path)
        if os.path.exists(optimized_path):
            os.remove(optimized_path)

def copy_source_crf(pdf_path):
    """Copy the available source CRF; never generate a fabricated CRF placeholder."""
    src = "01_source_data/Sanofi CRF Tropic.pdf"
    if not os.path.exists(src):
        sys.exit(
            "Missing source CRF: 01_source_data/Sanofi CRF Tropic.pdf. "
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
            "Run: Rscript platform/uplift_sdtm_34.R before building a full package. "
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
    are optional-if-present artifacts (BDRG render, ADaM spec)
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
        "    python3 platform/package_ectd.py --preview\n\n"
        "The SAS Transport (XPORT v5, *.xpt) datasets that belong in this folder are\n"
        "deliberately NOT included. They are de-identified, patient-level clinical-trial\n"
        "data obtained via Project Data Sphere under a Data Use Agreement that does not\n"
        "permit public redistribution; the project therefore never commits row-level data.\n"
        "The co-located define.xml fully describes the datasets that would be present here\n"
        "(structure, variables, controlled terminology, and derivations/origins).\n\n"
        "To materialise the datasets locally (with the licensed source data present):\n"
        "    python3 platform/package_ectd.py\n"
    )
    with open(os.path.join(folder, "README_datasets_excluded.txt"), "w", encoding="utf-8") as fh:
        fh.write(note)


def main(data_free=False):
    mode = "DATA-FREE PREVIEW" if data_free else "FULL"
    print(f"=== STARTING eCTD MODULE 5 PACKAGING ({mode}) ===")
    
    # 1. Define paths
    sdtm_src_dir = "01_source_data/real_sdtm"
    sdtm34_xpt_dir = ".core_run/sdtm34"
    adam_src_dir = "04_analysis_datasets/adam"
    define_src_dir = "03_metadata/define"
    guides_src_dir = "07_reviewer_explanation/guides"
    csr_src_file = "07_reviewer_explanation/analysis_report.md"
    tfl_src_dir = "05_outputs/tfl/output"
    
    m5_root = os.path.join("08_submission_package", "m5")
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
        "04_analysis_datasets/programs/sas", "04_analysis_datasets/programs/r", "05_outputs/tfl"
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
    
    print(f"Created target folder structure under {m5_root}/.")
    
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
        adam_prod_files = [
            f for f in glob.glob(os.path.join(adam_src_dir, "*_prod.xpt"))
            if os.path.basename(f).lower() != "clinsite_prod.xpt"
        ]
        if not adam_prod_files:
            print("Error: No ADaM '*_prod.xpt' datasets found in 04_analysis_datasets/adam/.")
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
        print("Error: Missing BIMO 'clinsite_prod.xpt' in 04_analysis_datasets/adam/. Ensure pipeline has run "
              "successfully.")
        sys.exit(1)
    bdrg_file = "07_reviewer_explanation/guides/BDRG.md"
    # Rendered to PDF for parity with the SDRG/ADRG reviewer guides (a submission package
    # ships rendered guides, not raw Markdown).
    if copy_if_present(bdrg_file,
                        lambda: md_to_pdf(bdrg_file, os.path.join(m5_bimo_dir, "bdrg.pdf")),
                        "BDRG (07_reviewer_explanation/guides/BDRG.md)"):
        print("  Generated BIMO data reviewer's guide (bdrg.pdf).")

    # 4c. Copy the authoritative ADaM specification (audit C-4 inversion): ADaM_spec.xlsx
    # is the upstream metadata control source (CDISC/Pinnacle-21 metacore format) that
    # governs define.xml -- not a rendering derived from it.
    print("Copying authoritative ADaM specification...")
    spec_file = "03_metadata/adam/ADaM_spec.xlsx"
    if copy_if_present(spec_file,
                        lambda: shutil.copy(spec_file, os.path.join(m5_adam_dir, "ADaM_spec.xlsx")),
                        "ADaM specification (03_metadata/adam/ADaM_spec.xlsx)"):
        print("  Copied ADaM_spec.xlsx (governing specification).")
        
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
    print(f"Copying analysis and validation programs to {m5_adam_programs_dir}/...")
    # SAS programs
    sas_files = glob.glob(os.path.join("04_analysis_datasets/programs/sas", "*.sas"))
    for f in sas_files:
        shutil.copy(f, m5_adam_programs_dir)
    # R programs
    r_files = glob.glob(os.path.join("04_analysis_datasets/programs/r", "*.R"))
    for f in r_files:
        shutil.copy(f, m5_adam_programs_dir)
    # TFL programs
    shutil.copy("05_outputs/tfl/tfl_generation.R", m5_adam_programs_dir)
    shutil.copy("05_outputs/tfl/tfl_stats.R", m5_adam_programs_dir)
    # spec -> define conformance program. Its report is QC evidence under platform/conformance/,
    # not a Module 5 package leaf.
    extra_programs = ["03_metadata/define/check_define_conformance.R"]
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
        print(f"Canonical FDA layout built in '{m5_root}/' (DATA-FREE PREVIEW — no patient-level *.xpt).")
    else:
        print(f"Canonical FDA layout built in '{m5_root}/'.")

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
