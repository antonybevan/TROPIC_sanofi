import importlib.util
import json
import re
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "platform/build_simulation_report.py"
PROTOCOL_PATH = ROOT / "config/simulation_protocol.yaml"
RESULTS_PATH = ROOT / "platform/simulation_operating_characteristics/simulation_oc_status.json"
PLAN_PATH = ROOT / "07_reviewer_explanation/simulation_model_analysis_plan.md"
REPORT_PATH = ROOT / "07_reviewer_explanation/simulation_report.md"

SPEC = importlib.util.spec_from_file_location("build_simulation_report", MODULE_PATH)
REPORTER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(REPORTER)


def _load_inputs():
    protocol = yaml.safe_load(PROTOCOL_PATH.read_text(encoding="utf-8"))
    results = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    return protocol, results


def _headings(text):
    return [
        (len(match.group(1)), match.group(2))
        for match in re.finditer(r"^(#{1,6})\s+(.+?)\s*$", text, flags=re.MULTILINE)
    ]


def _table_after(text, heading):
    section = text.split(heading, 1)[1]
    lines = section.splitlines()
    start = next(index for index, line in enumerate(lines) if line.startswith("| "))
    table = []
    for line in lines[start:]:
        if not line.startswith("| "):
            break
        table.append([cell.strip() for cell in line.strip("|").split("|")])
    return table


def test_checked_in_reports_are_exact_deterministic_builds():
    protocol, results = _load_inputs()
    protocol_hash = REPORTER._sha256(PROTOCOL_PATH)
    results_hash = REPORTER._sha256(RESULTS_PATH)

    expected_plan = REPORTER.build_analysis_plan(protocol, results, protocol_hash, results_hash)
    expected_report = REPORTER.build_report(protocol, results, protocol_hash, results_hash)

    assert PLAN_PATH.read_text(encoding="utf-8") == expected_plan
    assert REPORT_PATH.read_text(encoding="utf-8") == expected_report


@pytest.mark.parametrize("path", [PLAN_PATH, REPORT_PATH])
def test_accessible_heading_hierarchy_and_release_identity(path):
    text = path.read_text(encoding="utf-8")
    headings = _headings(text)

    assert sum(level == 1 for level, _ in headings) == 1
    assert headings[0][0] == 1
    assert all(current <= previous + 1 for (previous, _), (current, _) in zip(headings, headings[1:]))
    identity_lines = [
        line for line in text.splitlines()
        if line.startswith("**Current sealed controlled release:**")
    ]
    assert len(identity_lines) == 1
    assert "v0.3.0-clinical-simulation" in identity_lines[0]
    assert "docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md" in identity_lines[0]


@pytest.mark.parametrize("path", [PLAN_PATH, REPORT_PATH])
def test_markdown_tables_have_no_ambiguous_blank_cells(path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or re.fullmatch(r"\|(?:\s*:?-+:?\s*\|)+", line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        assert all(cells), f"ambiguous blank table cell in: {line}"


def test_scenario_coverage_and_result_parity():
    protocol, results = _load_inputs()
    protocol_ids = {REPORTER._scenario_id(item) for item in REPORTER._scenario_registry(protocol)}
    result_scenarios = REPORTER._result_scenarios(results)
    result_ids = {REPORTER._scenario_id(item) for item in result_scenarios}
    plan = PLAN_PATH.read_text(encoding="utf-8")
    report = REPORT_PATH.read_text(encoding="utf-8")

    assert protocol_ids == result_ids
    for scenario_id in protocol_ids:
        assert scenario_id in plan
        assert scenario_id in report

    accounting = _table_after(report, "## Exact Execution and Failure Accounting")
    accounting_by_id = {row[0]: row for row in accounting[2:]}
    execution_status = _table_after(report, "### Execution Status Rationale")
    execution_status_by_id = {row[0]: row for row in execution_status[2:]}
    operating = _table_after(report, "## Operating Characteristics and Monte Carlo Precision")
    operating_by_id = {row[0]: row for row in operating[2:]}
    decisions = _table_after(report, "### Precision and Design Decisions")
    decisions_by_id = {row[0]: row for row in decisions[2:]}

    for item in result_scenarios:
        scenario_id = REPORTER._scenario_id(item)
        requested = REPORTER._pick(item, "requested", "requested_replicates")
        completed = REPORTER._pick(item, "completed", "completed_replicates")
        failed = REPORTER._pick(item, "failed", "failed_replicates")
        assert accounting_by_id[scenario_id][1:4] == [str(requested), str(completed), str(failed)]
        assert execution_status_by_id[scenario_id][1] == REPORTER._display(
            item["statuses"]["execution"]["status"]
        )
        assert execution_status_by_id[scenario_id][2] == REPORTER._display(
            item["statuses"]["execution"]["reason"]
        )

        rejection = REPORTER._pick(item, "rejection", "operating_characteristic")
        row = operating_by_id[scenario_id]
        assert row[2] == f"{rejection['numerator']} / {rejection['denominator']}"
        assert row[3] == REPORTER._pct(rejection["estimate"])
        assert row[4] == REPORTER._display(rejection["mcse"])
        assert row[5] == (
            f"{REPORTER._pct(rejection['wilson_95']['lower'])} to "
            f"{REPORTER._pct(rejection['wilson_95']['upper'])}"
        )
        decision = decisions_by_id[scenario_id]
        assert decision[1] == REPORTER._display(item["statuses"]["precision"]["status"])
        assert decision[2] == REPORTER._display(item["statuses"]["precision"]["reason"])
        assert decision[3] == REPORTER._display(
            item["statuses"]["design_operating_characteristic"]["status"]
        )
        assert decision[4] == REPORTER._display(
            item["statuses"]["design_operating_characteristic"]["reason"]
        )


def test_representative_paths_and_edge_fixtures_are_distinct_and_exact():
    _, results = _load_inputs()
    report = REPORT_PATH.read_text(encoding="utf-8")
    representative = _table_after(report, "## Representative Simulated Trial Paths")
    representative_by_role = {row[0]: row for row in representative[2:]}

    assert "## Deterministic Edge-Case Verification Fixtures" in report
    for item in results["representative_trials"]:
        row = representative_by_role[item["selection_role"]]
        assert row[1] == item["scenario_id"]
        assert row[2] == str(item["search_index"])
        assert row[3] == (
            f"scenario={item['scenario_seed']}; selection={item['selection_seed']}"
        )
        assert row[4] == (
            f"control={item['events']['control']}; "
            f"experimental={item['events']['experimental']}"
        )
        assert row[5] == (
            f"control={item['censors']['control']}; "
            f"experimental={item['censors']['experimental']}"
        )
        assert row[6] == REPORTER._display(item["z_statistic"])
        assert row[7] == REPORTER._display(item["one_sided_p_value"])
        assert row[8].startswith(item["decision"] + " — ")

    fixtures = _table_after(report, "## Deterministic Edge-Case Verification Fixtures")
    fixture_ids = {row[0] for row in fixtures[2:]}
    expected_fixture_ids = {
        item["id"] for item in results["validation"]["logrank_edge_fixtures"]
    }
    assert fixture_ids == expected_fixture_ids
    fixture_by_id = {row[0]: row for row in fixtures[2:]}
    for item in results["validation"]["logrank_edge_fixtures"]:
        if item["analysis_status"] != "COMPLETED":
            assert fixture_by_id[item["id"]][5:8] == [
                "Not applicable — non-estimable",
                "Not applicable — non-estimable",
                "Not applicable — non-estimable",
            ]


def test_change_control_and_governing_references_are_explicit():
    protocol, results = _load_inputs()
    plan = PLAN_PATH.read_text(encoding="utf-8")
    report = REPORT_PATH.read_text(encoding="utf-8")

    assert REPORTER._display(REPORTER._deviations(protocol["change_control"])) in plan
    assert REPORTER._display(REPORTER._deviations(results["change_control"])) in report
    for text in (plan, report):
        assert "## References and Governing Basis" in text
        assert "../docs/SIMULATION_PRECISION_RESEARCH.md" in text
        assert "ICH M15" in text
        assert "ICH E9(R1)" in text
        assert "ADEMP" in text
        assert "OCTAVE" in text


def test_recorded_software_identity_is_reviewer_visible():
    _, results = _load_inputs()
    identity = results["software_identity"]
    python_version = identity["python"]["version"]
    for path in (PLAN_PATH, REPORT_PATH):
        text = path.read_text(encoding="utf-8")
        assert "## Seeds, Hashes, and Reproduction" in text or "## Reproducibility, Verification, and Change Control" in text
        assert "### Observed Execution Environment" in text
        assert python_version in text
        assert identity["numpy_version"] in text
        assert identity["pyyaml_version"] in text
        assert identity["floating_point_dtype"] in text
        assert identity["random_number_generator"] in text
        assert identity["dependency_lock"] in text


def test_repeatable_writes(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_plan, first_report = REPORTER.write_reports(
        PROTOCOL_PATH, RESULTS_PATH, first / "plan.md", first / "report.md"
    )
    second_plan, second_report = REPORTER.write_reports(
        PROTOCOL_PATH, RESULTS_PATH, second / "plan.md", second / "report.md"
    )

    assert (first_plan, first_report) == (second_plan, second_report)
    assert (first / "plan.md").read_bytes() == (second / "plan.md").read_bytes()
    assert (first / "report.md").read_bytes() == (second / "report.md").read_bytes()


def test_fail_closed_on_scenario_or_replicate_mismatch(tmp_path):
    protocol, results = _load_inputs()
    bad_results = json.loads(json.dumps(results))
    bad_results["scenarios"][0]["failed"] += 1

    with pytest.raises(RuntimeError, match=r"requested != completed \+ failed"):
        REPORTER.validate_inputs(protocol, bad_results, PROTOCOL_PATH)

    bad_results = json.loads(json.dumps(results))
    bad_results["scenarios"][0]["scenario_id"] = "UNPLANNED-SCENARIO"
    with pytest.raises(RuntimeError, match="protocol/result scenario mismatch"):
        REPORTER.validate_inputs(protocol, bad_results, PROTOCOL_PATH)
