from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform"))

from check_gate_g07_reviewer_package import (  # noqa: E402
    CURRENT_RELEASE,
    CURRENT_RELEASE_NOTE,
    RELEASE_ID_SOURCES,
    SECONDARY_TTE_ROWS,
    _report_secondary_metrics,
    _tfl_secondary_metrics,
)
from package_ectd import split_markdown_table_row  # noqa: E402
from build_ectd_backbone import classify  # noqa: E402
from validate_ectd_sequence import validate_sequence  # noqa: E402


def test_escaped_markdown_pipes_stay_inside_one_cell():
    row = r'| `INVNAM` | Principal Investigator | `"PI_" \|\| SITEID` — see Section 2 |'
    cells = split_markdown_table_row(row)
    assert len(cells) == 3
    assert cells[2].startswith('`"PI_" || SITEID`')


def test_current_release_identity_is_bound_across_reviewer_sources():
    for rel in RELEASE_ID_SOURCES:
        lines = [
            line
            for line in (ROOT / rel).read_text(encoding="utf-8").splitlines()
            if "Current controlled release" in line or "Current sealed controlled release" in line
        ]
        assert len(lines) == 1, (rel, lines)
        assert CURRENT_RELEASE in lines[0]
        assert CURRENT_RELEASE_NOTE in lines[0]


def test_committed_ectd_surface_has_no_extras_or_broken_support_references():
    # Patient-level/materialized payloads are deliberately absent in a clean CI
    # checkout. Every present leaf and the complete control/UTIL surface still
    # must validate, and an ignored desktop file must never be tolerated.
    result = validate_sequence(require_all_leaves=False)
    assert result["status"] == "PASS", result["problems"]
    assert result["unexpected_files"] == []


def test_packaged_tfl_driver_includes_its_runtime_helper():
    source_dir = ROOT / "05_outputs/tfl"
    package_dir = (
        ROOT
        / "08_submission_package/m5/datasets/tropic/analysis/adam/programs"
    )
    for name in ("tfl_generation.R", "tfl_stats.R", "lab_shift_table.R"):
        assert (package_dir / name).read_bytes() == (source_dir / name).read_bytes()


def test_packaged_simulation_sources_are_exact_plain_text_analysis_programs():
    package_dir = ROOT / "08_submission_package/m5/datasets/tropic/analysis/adam/programs"
    sources = {
        "simulation_precision.py.txt": ROOT / "platform/simulation_precision.py",
        "check_simulation_evidence.py.txt": ROOT / "platform/check_simulation_evidence.py",
        "build_simulation_report.py.txt": ROOT / "platform/build_simulation_report.py",
        "simulation_protocol.yaml.txt": ROOT / "config/simulation_protocol.yaml",
    }
    for packaged_name, source in sources.items():
        packaged = package_dir / packaged_name
        assert packaged.read_bytes() == source.read_bytes()
        tag, info = classify(
            f"m5/datasets/tropic/analysis/adam/programs/{packaged_name}"
        )
        assert (tag, info) == ("analysis-program", "us")


def test_simulation_report_keeps_table_heading_with_first_table_row():
    """A reviewer heading must not be orphaned above the page footer."""
    from pypdf import PdfReader

    report = (
        ROOT
        / "08_submission_package/m5/53-clin-stud-rep/535-rep-effic-safety-stud/"
        "mcrpc/5351-stud-rep-contr/tropic/simulation-report.pdf"
    )
    pages = [page.extract_text() or "" for page in PdfReader(report).pages]
    heading = "Representative Simulated Trial Paths"
    # Page 1 is the generated table of contents and legitimately repeats the
    # heading text; inspect the section occurrence in the document body.
    heading_pages = [index for index, text in enumerate(pages[1:], 1) if heading in text]
    assert len(heading_pages) == 1
    heading_page = " ".join(pages[heading_pages[0]].split())
    assert "Search index" in heading_page
    assert "reject" in heading_page


def test_analysis_report_secondary_tte_rows_match_generated_table():
    report = (ROOT / "07_reviewer_explanation/analysis_report.md").read_text(
        encoding="utf-8"
    )
    table = (
        ROOT / "05_outputs/tfl/output/tables/T-11-Efficacy_Tables.txt"
    ).read_text(encoding="utf-8")
    for table_id, label in SECONDARY_TTE_ROWS.items():
        assert _report_secondary_metrics(report, label) == _tfl_secondary_metrics(
            table, table_id
        )


def test_tfl_gallery_matches_controlled_tables_and_is_keyboard_accessible():
    """Keep the reviewer-facing static gallery tied to the controlled TFL text."""
    gallery_path = ROOT / "05_outputs/tfl/TFL_Gallery.html"
    gallery = gallery_path.read_text(encoding="utf-8")
    t11 = (ROOT / "05_outputs/tfl/output/tables/T-11-Efficacy_Tables.txt").read_text(
        encoding="utf-8"
    )
    t21 = (ROOT / "05_outputs/tfl/output/tables/T-21-Lab_Shift_Tables.txt").read_text(
        encoding="utf-8"
    )

    # The gallery is a committed reviewer surface, so its endpoint and shift cells
    # must remain synchronized with the generated, controlled text outputs.
    assert "Median Survival Time (Months)             4.9" in t11
    assert "0.89 (95% CI: 0.66-1.22)" in t11
    assert "Median Survival Time (Months)             8.1" in t11
    assert "2.85 (95% CI: 1.98-4.12)" in t11
    assert "Time to Tumour Progression</td><td class=\"val-info\">4.9 mo" in gallery
    assert "0.89 (0.66–1.22)</td><td>0.4406" in gallery
    assert "Time to Pain Progression</td><td class=\"val-info\">8.1 mo" in gallery
    assert "2.85 (1.98–4.12)</td><td>&lt;0.0001" in gallery
    assert "9.1 mo" not in gallery
    assert "7.9 mo" not in gallery

    for value in ("115", "45", "85", "100", "22", "110", "63", "53", "275", "69"):
        assert value in t21
    for stale in ("143", "59", "126", "341", "133", "67"):
        assert f">{stale}</td>" not in gallery
    assert gallery.count("shift n=370; safety N=371") == 3

    figure_sources = re.findall(r'<img class="fig-thumb" src="([^"]+)"', gallery)
    assert len(figure_sources) == 7
    for source in figure_sources:
        assert (gallery_path.parent / source).is_file(), source
    assert gallery.count('role="button"') == 7
    assert gallery.count('tabindex="0"') == 7
    assert 'aria-modal="true"' in gallery
    assert 'aria-label="Close figure preview"' in gallery
