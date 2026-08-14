"""Independent controls for the governed, data-free TTE simulation core."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "platform" / "simulation_precision.py"
PROTOCOL_PATH = ROOT / "config" / "simulation_protocol.yaml"
SPEC = importlib.util.spec_from_file_location("tropic_simulation_precision", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
SIM = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SIM)


def governed_config() -> dict:
    return SIM.load_protocol(PROTOCOL_PATH)


def reduced_config(replicates: int = 120) -> dict:
    config = governed_config()
    config["acceptance_criteria"]["key_null_min_completed"] = replicates
    config["acceptance_criteria"]["alternative_min_completed"] = replicates
    config["acceptance_criteria"]["target_mcse_key_null"] = 0.2
    config["design"]["batch_size"] = 40
    config["representative_trial_selection"]["search_replicates"] = 120
    config["representative_trial_selection"]["batch_size"] = 40
    for scenario in config["scenarios"]:
        scenario["replicates"] = replicates
    return config


def write_protocol(path: Path, config: dict) -> Path:
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8", newline="\n")
    return path


def test_governed_protocol_schema_and_scope_without_full_simulation() -> None:
    config = governed_config()
    SIM.validate_protocol(config)

    scenarios = config["scenarios"]
    assert len(scenarios) == 10
    assert sum(item["replicates"] for item in scenarios) == 400_000
    assert len({item["id"] for item in scenarios}) == len(scenarios)
    assert len({item["seed"] for item in scenarios}) == len(scenarios)
    assert config["representative_trial_selection"]["selection_seed"] not in {
        item["seed"] for item in scenarios
    }
    nulls = [item for item in scenarios if item["class"].startswith("KEY_NULL")]
    alternatives = [item for item in scenarios if not item["class"].startswith("KEY_NULL")]
    assert {item["endpoint"] for item in nulls} == {"OS", "PFS"}
    assert all(item["replicates"] >= 100_000 for item in nulls)
    assert all(item["replicates"] >= 25_000 for item in alternatives)
    assert {item["family"] for item in scenarios} >= SIM.REQUIRED_FAMILIES

    boundary = config["protocol"]["qualification_boundary"]
    assert boundary["classification"] == "NON_MIDD_NON_CONFIRMATORY_DATA_FREE_METHODS_EVALUATION"
    assert boundary["authoritative_patient_data_used"] is False
    assert boundary["external_validation_completed"] is False
    assert "N=371" in config["design"]["allocation_basis"]
    assert config["design"]["allocation"] == {"control": 377, "experimental": 378}
    assert config["design"]["analysis_method"] == "ONE_SIDED_UNSTRATIFIED_LOGRANK"
    assert "stratification" in config["design"]["omitted_design_feature"].lower()
    assert config["change_control"] == {
        "full_run_started_after_freeze": True,
        "deviations": [],
    }

    estimand = config["estimand"]
    assert set(estimand["variables"]) == {"OS", "PFS"}
    assert estimand["intercurrent_events"]["permanent_treatment_discontinuation"]["strategy"] == "TREATMENT_POLICY"
    assert estimand["intercurrent_events"]["subsequent_anticancer_therapy"]["strategy"] == "TREATMENT_POLICY"
    assert "independent_withdrawal" in estimand["missing_data_and_censoring"]
    assert set(config["protocol_framework"]) == {"ADEMP", "OCTAVE"}


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda c: c["protocol"].__setitem__("status", "DRAFT"), "FROZEN_MAP"),
        (lambda c: c["protocol"]["qualification_boundary"].__setitem__(
            "authoritative_patient_data_used", True), "must be false"),
        (lambda c: c["design"].__setitem__("alpha_one_sided", 0.05), "0.025"),
        (lambda c: c["acceptance_criteria"].__setitem__(
            "alternative_precision_justification", None), "must be non-empty text"),
        (lambda c: c["scenarios"][1].__setitem__("seed", c["scenarios"][0]["seed"]),
         "seeds must be unique"),
        (lambda c: c["scenarios"][0]["treatment_hr_segments"][0].__setitem__(
            "hazard_ratio", 0.9), "null scenario treatment hazard ratios"),
        (lambda c: c["scenarios"][0]["withdrawal_rate_12m"].__setitem__(
            "control", 1.0), "must be < 1"),
        (lambda c: c["scenarios"][2].__setitem__("replicates", 10), "below required"),
        (lambda c: c["representative_trial_selection"].__setitem__(
            "scenario_seed_binding", 123), "must match the governed scenario seed"),
        (lambda c: c["estimand"]["intercurrent_events"][
            "permanent_treatment_discontinuation"].__setitem__("strategy", "WHILE_ON_TREATMENT"),
         "must be TREATMENT_POLICY"),
    ],
)
def test_malformed_protocol_fails_closed(mutation, message: str) -> None:
    config = governed_config()
    mutation(config)
    with pytest.raises(SIM.ProtocolError, match=message):
        SIM.validate_protocol(config)


def test_mcse_and_wilson_are_independently_recomputed() -> None:
    successes = 2_517
    trials = 100_000
    result = SIM.probability_summary(successes, trials)
    estimate = successes / trials
    expected_mcse = math.sqrt(estimate * (1.0 - estimate) / trials)
    z = 1.959963984540054
    denominator = 1.0 + z * z / trials
    center = (estimate + z * z / (2.0 * trials)) / denominator
    half_width = z * math.sqrt(
        estimate * (1.0 - estimate) / trials + z * z / (4.0 * trials * trials)
    ) / denominator

    assert result["numerator"] == successes
    assert result["denominator"] == trials
    assert result["estimate"] == pytest.approx(estimate, abs=0.0)
    assert result["mcse"] == pytest.approx(expected_mcse, rel=0.0, abs=1e-15)
    assert result["wilson_95"]["lower"] == pytest.approx(center - half_width, abs=1e-15)
    assert result["wilson_95"]["upper"] == pytest.approx(center + half_width, abs=1e-15)


def independent_logrank(times: np.ndarray, events: np.ndarray,
                        treatment: np.ndarray) -> float:
    order = np.argsort(times, kind="stable")
    times = times[order]
    events = events[order]
    treatment = treatment[order]
    observed_minus_expected = 0.0
    variance = 0.0
    for index in range(len(times)):
        if events[index] != 1:
            continue
        at_risk = treatment[index:]
        total = len(at_risk)
        experimental = int(at_risk.sum())
        observed_minus_expected += treatment[index] - experimental / total
        variance += experimental * (total - experimental) / (total * total)
    return observed_minus_expected / math.sqrt(variance)


def test_logrank_matches_independent_reference_and_direction() -> None:
    treatment = np.array([0, 0, 0, 0, 1, 1, 1, 1], dtype=int)
    events = np.array([1, 1, 0, 1, 1, 0, 1, 1], dtype=int)
    favorable_times = np.array([1.0, 2.0, 4.0, 5.0, 3.0, 6.0, 7.0, 8.0])
    z, estimable = SIM.logrank_batch(favorable_times[None, :], events[None, :], treatment)
    assert estimable.tolist() == [True]
    assert z[0] == pytest.approx(independent_logrank(favorable_times, events, treatment), abs=1e-14)
    assert z[0] < 0.0

    reversed_times = np.concatenate([favorable_times[4:], favorable_times[:4]])
    z_reversed, _ = SIM.logrank_batch(reversed_times[None, :], events[None, :], treatment)
    assert z_reversed[0] > 0.0


def test_reduced_null_behavior_contains_analytic_alpha() -> None:
    config = governed_config()
    scenario = copy.deepcopy(config["scenarios"][0])
    scenario["replicates"] = 4_000
    result = SIM.simulate_scenario(config, scenario)

    assert result["requested"] == result["completed"] + result["failed"]
    assert result["failed"] == 0
    assert result["rejection"]["estimate"] == pytest.approx(0.0245, abs=1e-15)
    interval = result["rejection"]["wilson_95"]
    assert interval["lower"] <= 0.025 <= interval["upper"]
    assert result["analytic_null_benchmark"]["acceptance_status"] == "PASS"


def test_large_755_subject_batch_has_finite_positive_logrank_variance() -> None:
    """Regression for NumPy 2.2/Python 3.14 temporary-reduction corruption."""
    config = governed_config()
    scenario = config["scenarios"][0]
    batch = SIM._generate_trial_batch(
        np.random.default_rng(scenario["seed"]),
        1_000,
        config,
        scenario,
    )
    assert batch["estimable"].shape == (1_000,)
    assert np.all(batch["estimable"])
    assert np.all(np.isfinite(batch["z_statistic"]))
    assert np.max(np.abs(batch["z_statistic"])) < 6.0


def test_accounted_analysis_failure_is_separate_from_execution_and_precision_cap() -> None:
    criteria = copy.deepcopy(governed_config()["acceptance_criteria"])
    criteria["key_null_min_completed"] = 999
    criteria["target_mcse_key_null"] = 0.1
    rejection = SIM.probability_summary(25, 999)
    statuses, _ = SIM.evaluate_scenario_statuses(
        requested=1_000,
        completed=999,
        failures={"zero_logrank_variance": 1},
        rejection=rejection,
        criteria=criteria,
        is_null=True,
    )
    assert statuses["execution"]["status"] == "PASS"
    assert statuses["precision"]["status"] == "PASS"

    over_cap, _ = SIM.evaluate_scenario_statuses(
        requested=1_000,
        completed=998,
        failures={"zero_logrank_variance": 2},
        rejection=SIM.probability_summary(25, 998),
        criteria=criteria,
        is_null=True,
    )
    assert over_cap["execution"]["status"] == "PASS"
    assert over_cap["precision"]["status"] == "FAIL"

    batch_failure, _ = SIM.evaluate_scenario_statuses(
        requested=1_000,
        completed=999,
        failures={"batch_exception:RuntimeError:synthetic": 1},
        rejection=rejection,
        criteria=criteria,
        is_null=True,
    )
    assert batch_failure["execution"]["status"] == "FAIL"


def test_reduced_fixture_is_deterministic_and_hash_bound(tmp_path: Path) -> None:
    config = reduced_config()
    protocol_path = write_protocol(tmp_path / "reduced_protocol.yaml", config)
    loaded = SIM.load_protocol(protocol_path)
    first = SIM.build_results(loaded, protocol_path)
    second = SIM.build_results(SIM.load_protocol(protocol_path), protocol_path)

    assert first == second
    assert first["scientific_output_sha256"] == second["scientific_output_sha256"]
    unhashed = copy.deepcopy(first)
    observed_hash = unhashed.pop("scientific_output_sha256")
    expected_hash = hashlib.sha256(
        json.dumps(unhashed, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()
    assert observed_hash == expected_hash
    assert first["protocol"]["protocol_sha256"] == hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    assert first["protocol"]["scenario_registry_sha256"] == SIM.sha256_value(loaded["scenarios"])
    assert {item["selection_role"] for item in first["representative_trials"]} == {
        "reject", "non_reject", "near_alpha_boundary"
    }
    assert all(item["scenario_id"] == loaded["representative_trial_selection"]["scenario_id"]
               for item in first["representative_trials"])
    assert all(item["scenario_seed"] == loaded["representative_trial_selection"]["scenario_seed_binding"]
               for item in first["representative_trials"])
    assert all(item["validation_status"] == "PASS"
               for item in first["validation"]["logrank_edge_fixtures"])
    for scenario in first["scenarios"]:
        assert scenario["requested"] == scenario["completed"] + scenario["failed"]
        assert scenario["events"]["control"]["mean_proportion"] + scenario["censoring"]["control"]["mean_proportion"] == pytest.approx(1.0)
        assert scenario["events"]["experimental"]["mean_proportion"] + scenario["censoring"]["experimental"]["mean_proportion"] == pytest.approx(1.0)


def test_in_memory_protocol_cannot_drift_from_hash_bound_file(tmp_path: Path) -> None:
    config = reduced_config()
    protocol_path = write_protocol(tmp_path / "reduced_protocol.yaml", config)
    config["design"]["batch_size"] += 1
    with pytest.raises(SIM.ProtocolError, match="differs from the hash-bound protocol file"):
        SIM.build_results(config, protocol_path)


def test_optional_report_is_machine_readable_only(tmp_path: Path) -> None:
    config = reduced_config(100)
    protocol_path = write_protocol(tmp_path / "reduced_protocol.yaml", config)
    result = SIM.build_results(SIM.load_protocol(protocol_path), protocol_path)
    paths = SIM.write_results(result, tmp_path / "outputs", tmp_path / "copy.json")
    assert paths["results"].name == "simulation_oc_status.json"
    assert json.loads(paths["report"].read_text(encoding="utf-8")) == result
    with pytest.raises(SIM.ProtocolError, match="machine-readable .json"):
        SIM.write_results(result, tmp_path / "outputs-2", tmp_path / "report.md")
