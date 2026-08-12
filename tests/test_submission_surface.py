from __future__ import annotations

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
