import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "platform/check_simulation_evidence.py"
PROTOCOL_PATH = ROOT / "config/simulation_protocol.yaml"
RESULTS_PATH = ROOT / "platform/simulation_operating_characteristics/simulation_oc_status.json"
CSV_PATH = ROOT / "platform/simulation_operating_characteristics/scenario_results.csv"
TRIALS_PATH = ROOT / "platform/simulation_operating_characteristics/representative_trials.json"
REPORT_PATH = ROOT / "07_reviewer_explanation/simulation_report.md"
CODE_PATH = ROOT / "platform/simulation_precision.py"

SPEC = importlib.util.spec_from_file_location("check_simulation_evidence", MODULE_PATH)
CHECKER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(CHECKER)


def _results():
    return json.loads(RESULTS_PATH.read_text(encoding="utf-8"))


def _rehash(value):
    value.pop("scientific_output_sha256", None)
    value["scientific_output_sha256"] = hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _write_result(tmp_path, value, *, allow_nan=False):
    path = tmp_path / "simulation_oc_status.json"
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=allow_nan) + "\n",
        encoding="utf-8",
    )
    return path


def _verify_primary(path):
    CHECKER.verify_evidence(
        protocol_path=PROTOCOL_PATH,
        results_path=path,
        code_path=CODE_PATH,
        csv_path=None,
        trials_path=None,
        report_path=None,
    )


def _assert_rejected(tmp_path, mutator, message):
    value = copy.deepcopy(_results())
    mutator(value)
    _rehash(value)
    path = _write_result(tmp_path, value)
    with pytest.raises(CHECKER.EvidenceVerificationError, match=message):
        _verify_primary(path)


def test_real_checked_in_bundle_passes_independent_verification():
    CHECKER.verify_evidence(
        protocol_path=PROTOCOL_PATH,
        results_path=RESULTS_PATH,
        code_path=CODE_PATH,
        csv_path=CSV_PATH,
        trials_path=TRIALS_PATH,
        report_path=REPORT_PATH,
    )


def test_cli_is_silent_on_success_and_does_not_modify_evidence():
    paths = [PROTOCOL_PATH, RESULTS_PATH, CSV_PATH, TRIALS_PATH, REPORT_PATH]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    completed = subprocess.run(
        [sys.executable, str(MODULE_PATH)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == ""
    assert completed.stderr == ""
    assert after == before


def test_rejects_scenario_order_drift(tmp_path):
    def mutate(value):
        value["scenarios"][0], value["scenarios"][1] = (
            value["scenarios"][1],
            value["scenarios"][0],
        )

    _assert_rejected(tmp_path, mutate, "scenario ids/order must exactly equal governed order")


def test_rejects_coordinated_attempt_to_change_frozen_governed_registry(tmp_path):
    protocol = yaml.safe_load(PROTOCOL_PATH.read_text(encoding="utf-8"))
    protocol["scenarios"][0], protocol["scenarios"][1] = (
        protocol["scenarios"][1],
        protocol["scenarios"][0],
    )
    protocol_path = tmp_path / "simulation_protocol.yaml"
    protocol_path.write_text(yaml.safe_dump(protocol, sort_keys=False), encoding="utf-8")
    value = _results()
    value["scenarios"][0], value["scenarios"][1] = value["scenarios"][1], value["scenarios"][0]
    value["protocol"]["protocol_sha256"] = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    value["protocol"]["scenario_registry_sha256"] = hashlib.sha256(
        json.dumps(
            protocol["scenarios"],
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    _rehash(value)
    results_path = _write_result(tmp_path, value)
    with pytest.raises(
        CHECKER.EvidenceVerificationError, match="ids/order must equal the frozen governed registry"
    ):
        CHECKER.verify_evidence(
            protocol_path,
            results_path,
            CODE_PATH,
            None,
            None,
            None,
        )


def test_rejects_duplicate_or_noninteger_scenario_seeds(tmp_path):
    def duplicate(value):
        value["scenarios"][1]["seed"] = value["scenarios"][0]["seed"]

    _assert_rejected(tmp_path, duplicate, "scenario seeds must be unique")

    def boolean(value):
        value["scenarios"][0]["seed"] = True

    _assert_rejected(tmp_path, boolean, "every seed must be an integer")


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("protocol_sha256", "does not match .*simulation_protocol.yaml"),
        ("scenario_registry_sha256", "does not match canonical governed scenario registry"),
        ("code_sha256", "does not match .*simulation_precision.py"),
    ],
)
def test_rejects_input_hash_drift(tmp_path, field, message):
    def mutate(value):
        value["protocol"][field] = "0" * 64

    _assert_rejected(tmp_path, mutate, message)


def test_rejects_scenario_and_scientific_hash_drift(tmp_path):
    def scenario_hash(value):
        value["scenarios"][0]["scenario_sha256"] = "0" * 64

    _assert_rejected(tmp_path, scenario_hash, "scenario_sha256.*does not match")

    value = _results()
    value["scientific_output_sha256"] = "0" * 64
    path = _write_result(tmp_path, value)
    with pytest.raises(
        CHECKER.EvidenceVerificationError,
        match="scientific_output_sha256.*does not match canonical scientific content",
    ):
        _verify_primary(path)


def test_rejects_accounting_and_analyzed_denominator_drift(tmp_path):
    def accounting(value):
        value["scenarios"][0]["failed"] += 1

    _assert_rejected(tmp_path, accounting, r"requested must equal completed \+ failed")

    def analyzed(value):
        value["scenarios"][0]["analyzed"] = value["scenarios"][0]["completed"] - 1

    _assert_rejected(tmp_path, analyzed, "analyzed.*must equal completed")

    def denominator(value):
        value["scenarios"][0]["rejection"]["denominator"] -= 1

    _assert_rejected(tmp_path, denominator, "rejection.denominator.*must equal completed")


@pytest.mark.parametrize(
    ("field_path", "message"),
    [
        (("estimate",), "rejection.estimate.*numerator / denominator"),
        (("mcse",), "rejection.mcse.*binomial MCSE"),
        (("wilson_95", "lower"), "wilson_95.lower.*independently recomputed"),
        (("wilson_95", "upper"), "wilson_95.upper.*independently recomputed"),
    ],
)
def test_rejects_recomputed_statistic_drift(tmp_path, field_path, message):
    def mutate(value):
        target = value["scenarios"][0]["rejection"]
        for key in field_path[:-1]:
            target = target[key]
        target[field_path[-1]] += 0.01

    _assert_rejected(tmp_path, mutate, message)


def test_rejects_nan_even_when_nonstandard_json_parser_would_accept_it(tmp_path):
    value = _results()
    value["scenarios"][0]["rejection"]["estimate"] = float("nan")
    path = _write_result(tmp_path, value, allow_nan=True)
    with pytest.raises(
        CHECKER.EvidenceVerificationError, match="non-finite JSON number 'NaN' is prohibited"
    ):
        _verify_primary(path)


def test_rejects_hard_replication_floor_and_failure_cap(tmp_path):
    def low_null(value):
        scenario = value["scenarios"][0]
        scenario["completed"] = 99_999

    _assert_rejected(tmp_path, low_null, "completed.*must be >= 100000")

    def high_failure(value):
        scenario = value["scenarios"][0]
        scenario["completed"] = 99_899
        scenario["failed"] = 101
        scenario["failure_rate"] = 101 / 100_000
        scenario["failures"] = {"zero_logrank_variance": 101}

    _assert_rejected(tmp_path, high_failure, r"failure_rate.*must be <= 0\.001")


def test_rejects_null_acceptance_or_status_misstatement(tmp_path):
    def analytic(value):
        value["scenarios"][0]["analytic_null_benchmark"]["wilson_contains_expected"] = False

    _assert_rejected(tmp_path, analytic, "wilson_contains_expected.*must equal True")

    def status(value):
        value["scenarios"][0]["statuses"]["design_operating_characteristic"][
            "status"
        ] = "FAIL"

    _assert_rejected(tmp_path, status, "design_operating_characteristic.status.*independent design acceptance")


def test_rejects_unbound_representative_trial_and_bad_edge_fixture(tmp_path):
    def unbound(value):
        value["representative_trials"][0]["scenario_id"] = "UNPLANNED"

    _assert_rejected(tmp_path, unbound, "scenario_id.*must identify a governed scenario")

    def invalid_role(value):
        value["representative_trials"][0]["selection_role"] = "invented"

    _assert_rejected(tmp_path, invalid_role, "selection_role.*must be reject")

    def bad_boundary(value):
        value["validation"]["logrank_edge_fixtures"][2]["failure_reason"] = None

    _assert_rejected(tmp_path, bad_boundary, "boundary_non_estimable.*edge-fixture checks")


def test_rejects_qualification_boundary_expansion(tmp_path):
    def mutate(value):
        value["qualification_boundary"]["evidence_status"] = "FILING_READY"

    _assert_rejected(tmp_path, mutate, "qualification_boundary.*must exactly match")

    def top_status(value):
        value["statuses"]["evidence_qualification"]["status"] = "PASS"

    _assert_rejected(tmp_path, top_status, "evidence_qualification.status.*NOT_QUALIFIED")


def test_rejects_sidecar_mismatch(tmp_path):
    bad_csv = tmp_path / "scenario_results.csv"
    text = CSV_PATH.read_text(encoding="utf-8")
    bad_csv.write_text(text.replace("OS_NULL_REFERENCE", "OS_NULL_TAMPERED", 1), encoding="utf-8")
    with pytest.raises(CHECKER.EvidenceVerificationError, match="differs from JSON"):
        CHECKER.verify_evidence(
            PROTOCOL_PATH,
            RESULTS_PATH,
            CODE_PATH,
            bad_csv,
            TRIALS_PATH,
            None,
        )

    bad_trials = tmp_path / "representative_trials.json"
    trials = json.loads(TRIALS_PATH.read_text(encoding="utf-8"))
    trials[0]["search_index"] += 1
    bad_trials.write_text(json.dumps(trials), encoding="utf-8")
    with pytest.raises(CHECKER.EvidenceVerificationError, match="does not exactly match"):
        CHECKER.verify_evidence(
            PROTOCOL_PATH,
            RESULTS_PATH,
            CODE_PATH,
            CSV_PATH,
            bad_trials,
            None,
        )


def test_rejects_reviewer_report_result_parity_drift(tmp_path):
    text = REPORT_PATH.read_text(encoding="utf-8")
    scenario = _results()["scenarios"][0]
    original = f"| {scenario['id']} | {scenario['requested']} |"
    assert original in text
    bad_report = tmp_path / "simulation_report.md"
    bad_report.write_text(text.replace(original, f"| {scenario['id']} | 999 |", 1), encoding="utf-8")
    with pytest.raises(CHECKER.EvidenceVerificationError, match="reviewer report execution row 1"):
        CHECKER.verify_evidence(
            PROTOCOL_PATH,
            RESULTS_PATH,
            CODE_PATH,
            CSV_PATH,
            TRIALS_PATH,
            bad_report,
        )


def test_cli_exits_nonzero_with_actionable_diagnostic(tmp_path):
    value = _results()
    value["scenarios"][0]["rejection"]["estimate"] += 0.1
    _rehash(value)
    path = _write_result(tmp_path, value)
    completed = subprocess.run(
        [
            sys.executable,
            str(MODULE_PATH),
            "--results",
            str(path),
            "--skip-sidecars",
            "--skip-report",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode != 0
    assert completed.stdout == ""
    assert "SIMULATION_EVIDENCE_ERROR" in completed.stderr
    assert "rejection.estimate" in completed.stderr
