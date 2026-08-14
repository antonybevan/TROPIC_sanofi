#!/usr/bin/env python3
"""Governed, data-free Monte Carlo evaluation of a fixed two-arm TTE design.

This module deliberately has a narrow qualification boundary.  It evaluates a
simplified design under assumptions frozen in ``config/simulation_protocol.yaml``;
it is not a clinical-trial reconstruction, MIDD analysis, or confirmatory result.

Only NumPy and PyYAML from the repository's pinned Python environment are used.
Scientific outputs contain no timestamps or runtimes so identical protocol, code,
and seed inputs produce byte-identical JSON and CSV artifacts.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / "config" / "simulation_protocol.yaml"
DEFAULT_OUT_DIR = ROOT / "platform" / "simulation_operating_characteristics"
RESULT_NAME = "simulation_oc_status.json"
CSV_NAME = "scenario_results.csv"
TRIALS_NAME = "representative_trials.json"
NORMAL_975 = 1.959963984540054
NORMAL_CDF_025 = -1.959963984540054
ALLOWED_ENDPOINTS = {"OS", "PFS"}
ALLOWED_CLASSES = {
    "KEY_NULL",
    "KEY_NULL_OPERATIONAL_STRESS",
    "ALTERNATIVE",
    "ALTERNATIVE_STRESS",
}
REQUIRED_FAMILIES = {
    "NULL_REFERENCE",
    "NULL_HIGH_DROPOUT",
    "PUBLISHED_EFFECT",
    "MEDIAN_CALIBRATED",
    "DELAYED_NON_PH",
    "WANING_DISCONTINUATION",
}


class ProtocolError(ValueError):
    """Raised when a simulation control is missing, malformed, or contradictory."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProtocolError(message)


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), f"{path} must be a mapping")
    return value


def _list(value: Any, path: str) -> list[Any]:
    _require(isinstance(value, list), f"{path} must be a list")
    return value


def _text(value: Any, path: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{path} must be non-empty text")
    return value.strip()


def _number(value: Any, path: str, *, minimum: float | None = None,
            maximum: float | None = None) -> float:
    _require(isinstance(value, (int, float)) and not isinstance(value, bool),
             f"{path} must be numeric")
    result = float(value)
    _require(math.isfinite(result), f"{path} must be finite")
    if minimum is not None:
        _require(result >= minimum, f"{path} must be >= {minimum}")
    if maximum is not None:
        _require(result <= maximum, f"{path} must be <= {maximum}")
    return result


def _integer(value: Any, path: str, *, minimum: int = 0) -> int:
    _require(isinstance(value, int) and not isinstance(value, bool), f"{path} must be an integer")
    _require(value >= minimum, f"{path} must be >= {minimum}")
    return value


def _require_keys(mapping: Mapping[str, Any], keys: Sequence[str], path: str) -> None:
    missing = [key for key in keys if key not in mapping]
    _require(not missing, f"{path} missing required field(s): {', '.join(missing)}")


def canonical_json(value: Any) -> str:
    """Return the canonical representation used for every governed SHA-256."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def software_identity() -> dict[str, Any]:
    return {
        "python": {
            "major": sys.version_info.major,
            "minor": sys.version_info.minor,
            "patch": sys.version_info.micro,
            "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        },
        "numpy_version": np.__version__,
        "pyyaml_version": yaml.__version__,
        "floating_point_dtype": "float64",
        "random_number_generator": "numpy.random.PCG64",
        "dependency_lock": "requirements-ci.lock",
    }


def load_protocol(path: str | Path = DEFAULT_PROTOCOL) -> dict[str, Any]:
    protocol_path = Path(path)
    try:
        loaded = yaml.safe_load(protocol_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ProtocolError(f"cannot read protocol {protocol_path}: {exc}") from exc
    _require(isinstance(loaded, dict), "protocol root must be a mapping")
    return loaded


def validate_protocol(config: Mapping[str, Any]) -> None:
    """Fail closed on the complete governed configuration before any simulation."""
    root = _mapping(config, "protocol root")
    _require_keys(
        root,
        ["schema_version", "change_control", "protocol", "m15_assessment", "estimand",
         "protocol_framework", "design", "acceptance_criteria",
         "representative_trial_selection", "scenarios"],
        "protocol root",
    )
    _require(root["schema_version"] == "1.0.0", "schema_version must equal 1.0.0")

    change_control = _mapping(root["change_control"], "change_control")
    _require_keys(change_control, ["full_run_started_after_freeze", "deviations"], "change_control")
    _require(change_control["full_run_started_after_freeze"] is True,
             "change_control.full_run_started_after_freeze must be true")
    deviations = _list(change_control["deviations"], "change_control.deviations")
    for index, deviation in enumerate(deviations):
        item = _mapping(deviation, f"change_control.deviations[{index}]")
        _require_keys(item, ["id", "description", "impact", "approved_by"],
                      f"change_control.deviations[{index}]")

    protocol = _mapping(root["protocol"], "protocol")
    _require_keys(
        protocol,
        ["id", "version", "status", "question_of_interest", "objective",
         "context_of_use", "decision_use", "prohibited_uses", "qualification_boundary"],
        "protocol",
    )
    for key in ("id", "version", "question_of_interest", "objective", "context_of_use", "decision_use"):
        _text(protocol[key], f"protocol.{key}")
    _require(protocol["status"] == "FROZEN_MAP", "protocol.status must equal FROZEN_MAP")
    prohibited = _list(protocol["prohibited_uses"], "protocol.prohibited_uses")
    _require(len(prohibited) >= 3, "protocol.prohibited_uses must contain at least three controls")
    for index, item in enumerate(prohibited):
        _text(item, f"protocol.prohibited_uses[{index}]")
    prohibited_joined = " ".join(prohibited).upper()
    _require("MIDD" in prohibited_joined and "CONFIRMATORY" in prohibited_joined,
             "protocol.prohibited_uses must state hard MIDD and confirmatory boundaries")

    boundary = _mapping(protocol["qualification_boundary"], "protocol.qualification_boundary")
    _require_keys(boundary, ["classification", "model_influence", "evidence_status",
                             "authoritative_patient_data_used", "external_validation_completed"],
                  "protocol.qualification_boundary")
    _require(boundary["classification"] == "NON_MIDD_NON_CONFIRMATORY_DATA_FREE_METHODS_EVALUATION",
             "qualification boundary classification is not the governed non-MIDD/non-confirmatory value")
    _require(boundary["model_influence"] == "LOW", "model influence must remain LOW")
    _require(boundary["evidence_status"] == "INFORMATIONAL_ONLY",
             "evidence status must remain INFORMATIONAL_ONLY")
    _require(boundary["authoritative_patient_data_used"] is False,
             "authoritative_patient_data_used must be false")
    _require(boundary["external_validation_completed"] is False,
             "external_validation_completed must be false")

    m15 = _mapping(root["m15_assessment"], "m15_assessment")
    m15_keys = ["question_of_interest", "context_of_use", "model_influence",
                "consequence_of_wrong_decision", "model_risk", "model_risk_rationale",
                "model_impact", "verification_plan", "validation_plan", "applicability",
                "residual_uncertainty"]
    _require_keys(m15, m15_keys, "m15_assessment")
    for key in ("question_of_interest", "context_of_use", "model_influence",
                "consequence_of_wrong_decision", "model_risk", "model_risk_rationale",
                "model_impact", "applicability"):
        _text(m15[key], f"m15_assessment.{key}")
    for key in ("verification_plan", "validation_plan", "residual_uncertainty"):
        values = _list(m15[key], f"m15_assessment.{key}")
        _require(values, f"m15_assessment.{key} must not be empty")

    estimand = _mapping(root["estimand"], "estimand")
    _require_keys(
        estimand,
        ["id", "framework", "population", "treatment_conditions", "variables",
         "population_summary", "intercurrent_events", "missing_data_and_censoring",
         "estimator", "sensitivity_scope"],
        "estimand",
    )
    for key in ("id", "framework", "population", "population_summary", "estimator", "sensitivity_scope"):
        _text(estimand[key], f"estimand.{key}")
    treatments = _mapping(estimand["treatment_conditions"], "estimand.treatment_conditions")
    _require_keys(treatments, ["control", "experimental"], "estimand.treatment_conditions")
    variables = _mapping(estimand["variables"], "estimand.variables")
    _require(set(variables) == ALLOWED_ENDPOINTS, "estimand.variables must define exactly OS and PFS")
    ice = _mapping(estimand["intercurrent_events"], "estimand.intercurrent_events")
    _require_keys(ice, ["permanent_treatment_discontinuation", "subsequent_anticancer_therapy", "death"],
                  "estimand.intercurrent_events")
    _require(_mapping(ice["permanent_treatment_discontinuation"],
                     "estimand.intercurrent_events.permanent_treatment_discontinuation").get("strategy")
             == "TREATMENT_POLICY",
             "permanent discontinuation strategy must be TREATMENT_POLICY")
    _require(_mapping(ice["subsequent_anticancer_therapy"],
                     "estimand.intercurrent_events.subsequent_anticancer_therapy").get("strategy")
             == "TREATMENT_POLICY", "subsequent therapy strategy must be TREATMENT_POLICY")
    missing = _mapping(estimand["missing_data_and_censoring"], "estimand.missing_data_and_censoring")
    _require_keys(missing, ["independent_withdrawal", "administrative_censoring"],
                  "estimand.missing_data_and_censoring")

    framework = _mapping(root["protocol_framework"], "protocol_framework")
    _require_keys(framework, ["ADEMP", "OCTAVE"], "protocol_framework")
    _require_keys(_mapping(framework["ADEMP"], "protocol_framework.ADEMP"),
                  ["aims", "data_generating_mechanism", "estimands", "methods", "performance_measures"],
                  "protocol_framework.ADEMP")
    _require_keys(_mapping(framework["OCTAVE"], "protocol_framework.OCTAVE"),
                  ["objectives", "characteristics", "trial_design", "analyses", "valuation_metrics", "evidence"],
                  "protocol_framework.OCTAVE")

    design = _mapping(root["design"], "design")
    _require_keys(design, ["allocation_basis", "allocation", "alpha_one_sided", "enrollment_months",
                           "analysis_month", "batch_size", "analysis_method",
                           "omitted_design_feature", "endpoint_control_medians_months"], "design")
    _text(design["allocation_basis"], "design.allocation_basis")
    _require("N=371" in design["allocation_basis"],
             "design.allocation_basis must distinguish the available real MP N=371")
    _require(design["analysis_method"] == "ONE_SIDED_UNSTRATIFIED_LOGRANK",
             "design.analysis_method must equal ONE_SIDED_UNSTRATIFIED_LOGRANK")
    _require("stratification" in _text(design["omitted_design_feature"],
                                       "design.omitted_design_feature").lower(),
             "design.omitted_design_feature must disclose omitted original stratification")
    allocation = _mapping(design["allocation"], "design.allocation")
    _require_keys(allocation, ["control", "experimental"], "design.allocation")
    _integer(allocation["control"], "design.allocation.control", minimum=2)
    _integer(allocation["experimental"], "design.allocation.experimental", minimum=2)
    alpha = _number(design["alpha_one_sided"], "design.alpha_one_sided", minimum=1e-9, maximum=0.5)
    _require(abs(alpha - 0.025) < 1e-15, "design.alpha_one_sided must equal governed value 0.025")
    enrollment = _number(design["enrollment_months"], "design.enrollment_months", minimum=0.0)
    analysis = _number(design["analysis_month"], "design.analysis_month", minimum=1e-9)
    _require(enrollment < analysis, "design.enrollment_months must be less than design.analysis_month")
    _integer(design["batch_size"], "design.batch_size", minimum=1)
    medians = _mapping(design["endpoint_control_medians_months"],
                       "design.endpoint_control_medians_months")
    _require(set(medians) == ALLOWED_ENDPOINTS,
             "design.endpoint_control_medians_months must define exactly OS and PFS")
    for endpoint in sorted(ALLOWED_ENDPOINTS):
        _number(medians[endpoint], f"design.endpoint_control_medians_months.{endpoint}", minimum=1e-9)

    criteria = _mapping(root["acceptance_criteria"], "acceptance_criteria")
    _require_keys(
        criteria,
        ["key_null_min_completed", "alternative_min_completed",
         "alternative_precision_justification", "target_mcse_key_null", "max_failure_rate",
         "analytic_null_probability", "analytic_null_abs_tolerance_floor",
         "analytic_null_mcse_multiplier", "wilson_confidence_level", "null_acceptance"],
        "acceptance_criteria",
    )
    null_min = _integer(criteria["key_null_min_completed"],
                        "acceptance_criteria.key_null_min_completed", minimum=1)
    alternative_min = _integer(criteria["alternative_min_completed"],
                               "acceptance_criteria.alternative_min_completed", minimum=1)
    alternative_justification = _text(
        criteria["alternative_precision_justification"],
        "acceptance_criteria.alternative_precision_justification",
    )
    _require("0.003163" in alternative_justification and "descriptive" in alternative_justification.lower(),
             "alternative precision justification must state the worst-case MCSE and descriptive boundary")
    _number(criteria["target_mcse_key_null"], "acceptance_criteria.target_mcse_key_null",
            minimum=1e-12, maximum=0.5)
    _number(criteria["max_failure_rate"], "acceptance_criteria.max_failure_rate", minimum=0.0, maximum=1.0)
    expected_alpha = _number(criteria["analytic_null_probability"],
                             "acceptance_criteria.analytic_null_probability", minimum=0.0, maximum=1.0)
    _require(abs(expected_alpha - alpha) < 1e-15,
             "analytic_null_probability must equal design.alpha_one_sided")
    _number(criteria["analytic_null_abs_tolerance_floor"],
            "acceptance_criteria.analytic_null_abs_tolerance_floor", minimum=0.0, maximum=1.0)
    _number(criteria["analytic_null_mcse_multiplier"],
            "acceptance_criteria.analytic_null_mcse_multiplier", minimum=0.0)
    confidence = _number(criteria["wilson_confidence_level"],
                         "acceptance_criteria.wilson_confidence_level", minimum=0.5, maximum=0.999999)
    _require(abs(confidence - 0.95) < 1e-15, "only the governed 95% Wilson interval is supported")
    _text(criteria["null_acceptance"], "acceptance_criteria.null_acceptance")

    scenarios = _list(root["scenarios"], "scenarios")
    _require(scenarios, "scenarios must not be empty")
    ids: list[str] = []
    seeds: list[int] = []
    families: set[str] = set()
    null_endpoints: set[str] = set()
    for index, item in enumerate(scenarios):
        path = f"scenarios[{index}]"
        scenario = _mapping(item, path)
        _require_keys(
            scenario,
            ["id", "endpoint", "class", "family", "rationale", "assumption_basis",
             "seed", "replicates", "treatment_hr_segments", "withdrawal_rate_12m",
             "discontinuation_rate_12m", "post_discontinuation_hazard_ratio"],
            path,
        )
        scenario_id = _text(scenario["id"], f"{path}.id")
        _require(scenario_id.replace("_", "").isalnum() and scenario_id == scenario_id.upper(),
                 f"{path}.id must be an uppercase alphanumeric/underscore identifier")
        ids.append(scenario_id)
        endpoint = scenario["endpoint"]
        _require(endpoint in ALLOWED_ENDPOINTS, f"{path}.endpoint must be OS or PFS")
        scenario_class = scenario["class"]
        _require(scenario_class in ALLOWED_CLASSES, f"{path}.class is unsupported")
        family = _text(scenario["family"], f"{path}.family")
        families.add(family)
        _text(scenario["rationale"], f"{path}.rationale")
        _text(scenario["assumption_basis"], f"{path}.assumption_basis")
        seed = _integer(scenario["seed"], f"{path}.seed", minimum=1)
        seeds.append(seed)
        replicates = _integer(scenario["replicates"], f"{path}.replicates", minimum=1)
        is_null = scenario_class.startswith("KEY_NULL")
        minimum_replicates = null_min if is_null else alternative_min
        if replicates < minimum_replicates:
            raise ProtocolError(
                f"{path}.replicates={replicates} is below required {minimum_replicates}; "
                "the governed justification supports 25,000 alternatives and does not authorize a reduction"
            )
        if is_null:
            null_endpoints.add(str(endpoint))
        segments = _list(scenario["treatment_hr_segments"], f"{path}.treatment_hr_segments")
        _require(segments, f"{path}.treatment_hr_segments must not be empty")
        starts: list[float] = []
        hrs: list[float] = []
        for segment_index, raw_segment in enumerate(segments):
            segment_path = f"{path}.treatment_hr_segments[{segment_index}]"
            segment = _mapping(raw_segment, segment_path)
            _require_keys(segment, ["start_month", "hazard_ratio"], segment_path)
            starts.append(_number(segment["start_month"], f"{segment_path}.start_month", minimum=0.0))
            hrs.append(_number(segment["hazard_ratio"], f"{segment_path}.hazard_ratio",
                               minimum=1e-9, maximum=10.0))
        _require(starts[0] == 0.0, f"{path} first hazard segment must start at month 0")
        _require(all(right > left for left, right in zip(starts, starts[1:])),
                 f"{path} hazard-segment starts must be strictly increasing")
        _require(all(start < analysis for start in starts[1:]),
                 f"{path} hazard-segment starts must precede the analysis month")
        withdrawal = _mapping(scenario["withdrawal_rate_12m"], f"{path}.withdrawal_rate_12m")
        _require_keys(withdrawal, ["control", "experimental"], f"{path}.withdrawal_rate_12m")
        for arm in ("control", "experimental"):
            rate = _number(withdrawal[arm], f"{path}.withdrawal_rate_12m.{arm}", minimum=0.0)
            _require(rate < 1.0, f"{path}.withdrawal_rate_12m.{arm} must be < 1")
        discontinuation = _number(scenario["discontinuation_rate_12m"],
                                  f"{path}.discontinuation_rate_12m", minimum=0.0)
        _require(discontinuation < 1.0, f"{path}.discontinuation_rate_12m must be < 1")
        post_hr = _number(scenario["post_discontinuation_hazard_ratio"],
                          f"{path}.post_discontinuation_hazard_ratio", minimum=1e-9, maximum=10.0)
        if is_null:
            _require(all(abs(hr - 1.0) < 1e-15 for hr in hrs),
                     f"{path} null scenario treatment hazard ratios must all equal 1")
            _require(discontinuation == 0.0 and abs(post_hr - 1.0) < 1e-15,
                     f"{path} null scenario cannot encode a discontinuation effect")
    _require(len(ids) == len(set(ids)), "scenario ids must be unique")
    _require(len(seeds) == len(set(seeds)), "scenario seeds must be unique and independent")
    _require(null_endpoints == ALLOWED_ENDPOINTS, "key-null scenarios must cover both OS and PFS")
    missing_families = sorted(REQUIRED_FAMILIES - families)
    _require(not missing_families,
             f"scenario grid missing required family/families: {', '.join(missing_families)}")

    selection = _mapping(root["representative_trial_selection"], "representative_trial_selection")
    _require_keys(selection, ["scenario_id", "scenario_seed_binding", "selection_seed",
                              "search_replicates", "batch_size", "roles"],
                  "representative_trial_selection")
    selection_scenario_id = _text(selection["scenario_id"],
                                  "representative_trial_selection.scenario_id")
    _require(selection_scenario_id in ids,
             "representative_trial_selection.scenario_id must identify a governed scenario")
    selected_scenario = scenarios[ids.index(selection_scenario_id)]
    bound_seed = _integer(selection["scenario_seed_binding"],
                          "representative_trial_selection.scenario_seed_binding", minimum=1)
    _require(bound_seed == selected_scenario["seed"],
             "representative_trial_selection.scenario_seed_binding must match the governed scenario seed")
    selection_seed = _integer(selection["selection_seed"],
                              "representative_trial_selection.selection_seed", minimum=1)
    _require(selection_seed not in seeds,
             "representative trial selection seed must be independent of every scenario seed")
    search_replicates = _integer(selection["search_replicates"],
                                 "representative_trial_selection.search_replicates", minimum=100)
    selection_batch = _integer(selection["batch_size"],
                               "representative_trial_selection.batch_size", minimum=1)
    _require(selection_batch <= search_replicates,
             "representative_trial_selection.batch_size cannot exceed search_replicates")
    roles = _mapping(selection["roles"], "representative_trial_selection.roles")
    _require(set(roles) == {"reject", "non_reject", "near_alpha_boundary"},
             "representative_trial_selection.roles must define reject, non_reject, and near_alpha_boundary")
    for role, item in roles.items():
        role_config = _mapping(item, f"representative_trial_selection.roles.{role}")
        _require_keys(role_config, ["eligibility", "selection_rule"],
                      f"representative_trial_selection.roles.{role}")
        _text(role_config["eligibility"], f"representative_trial_selection.roles.{role}.eligibility")
        _text(role_config["selection_rule"], f"representative_trial_selection.roles.{role}.selection_rule")


def wilson_interval(successes: int, trials: int, confidence_level: float = 0.95) -> tuple[float, float]:
    """Two-sided Wilson score interval for a binomial probability."""
    _require(isinstance(successes, int) and isinstance(trials, int),
             "Wilson successes and trials must be integers")
    _require(trials > 0 and 0 <= successes <= trials,
             "Wilson inputs must satisfy 0 <= successes <= trials and trials > 0")
    _require(abs(confidence_level - 0.95) < 1e-15,
             "only the governed 95% Wilson interval is supported")
    p = successes / trials
    z = NORMAL_975
    denominator = 1.0 + z * z / trials
    center = (p + z * z / (2.0 * trials)) / denominator
    half_width = z * math.sqrt(p * (1.0 - p) / trials + z * z / (4.0 * trials * trials)) / denominator
    return max(0.0, center - half_width), min(1.0, center + half_width)


def probability_summary(successes: int, trials: int, confidence_level: float = 0.95) -> dict[str, Any]:
    estimate = successes / trials
    lower, upper = wilson_interval(successes, trials, confidence_level)
    return {
        "numerator": successes,
        "denominator": trials,
        "estimate": estimate,
        "mcse": math.sqrt(estimate * (1.0 - estimate) / trials),
        "wilson_95": {
            "lower": lower,
            "upper": upper,
            "confidence_level": confidence_level,
        },
    }


def _normal_cdf(value: float) -> float:
    return 0.5 * math.erfc(-value / math.sqrt(2.0))


def logrank_batch(times: np.ndarray, events: np.ndarray, treatment: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Vectorized no-tie log-rank Z statistics and estimability flags.

    Simulated times are continuous, so event ties occur with probability zero.  The
    function rejects malformed arrays and uses the experimental-minus-expected sign;
    beneficial experimental survival therefore yields a negative statistic.
    """
    times = np.asarray(times, dtype=float)
    events = np.asarray(events)
    treatment = np.asarray(treatment)
    _require(times.ndim == 2, "logrank times must be a two-dimensional trial-by-subject array")
    _require(events.shape == times.shape, "logrank events shape must match times")
    _require(treatment.ndim == 1 and treatment.shape[0] == times.shape[1],
             "logrank treatment must be a subject vector matching times columns")
    _require(np.all(np.isfinite(times)) and np.all(times >= 0.0),
             "logrank times must be finite and non-negative")
    _require(np.all(np.isin(events, [0, 1])), "logrank events must contain only 0/1")
    _require(np.all(np.isin(treatment, [0, 1])) and len(np.unique(treatment)) == 2,
             "logrank treatment must contain both 0 and 1")

    order = np.argsort(times, axis=1, kind="stable")
    sorted_events = np.take_along_axis(events.astype(float), order, axis=1)
    arm_matrix = np.broadcast_to(treatment, times.shape)
    sorted_arm = np.take_along_axis(arm_matrix, order, axis=1).astype(float)
    arm_at_risk = np.cumsum(sorted_arm[:, ::-1], axis=1)[:, ::-1]
    total_at_risk = np.arange(times.shape[1], 0, -1, dtype=float)[None, :]
    # Materialize the reduction inputs explicitly.  This avoids an incorrect
    # temporary-expression reduction observed with NumPy 2.2.x on Python 3.14
    # for larger batches, while producing the same float64 calculation on the
    # governed Python 3.10+ stack.
    expected_fraction = np.empty_like(arm_at_risk)
    np.divide(arm_at_risk, total_at_risk, out=expected_fraction)
    score_contributions = np.empty_like(sorted_events)
    np.subtract(sorted_arm, expected_fraction, out=score_contributions)
    np.multiply(sorted_events, score_contributions, out=score_contributions)
    observed_minus_expected = np.sum(score_contributions, axis=1, dtype=np.float64)
    variance_terms = np.empty_like(arm_at_risk)
    np.subtract(total_at_risk, arm_at_risk, out=variance_terms)
    np.multiply(arm_at_risk, variance_terms, out=variance_terms)
    np.divide(variance_terms, total_at_risk * total_at_risk, out=variance_terms)
    variance_contributions = np.empty_like(sorted_events)
    np.multiply(sorted_events, variance_terms, out=variance_contributions)
    variance = np.sum(variance_contributions, axis=1, dtype=np.float64)
    estimable = np.isfinite(variance) & (variance > 0.0)
    statistic = np.full(times.shape[0], np.nan, dtype=float)
    statistic[estimable] = observed_minus_expected[estimable] / np.sqrt(variance[estimable])
    return statistic, estimable


def summarize_trial(times: Sequence[float], events: Sequence[int], treatment: Sequence[int],
                    alpha: float = 0.025) -> dict[str, Any]:
    time_array = np.asarray(times, dtype=float)[None, :]
    event_array = np.asarray(events, dtype=int)[None, :]
    treatment_array = np.asarray(treatment, dtype=int)
    statistic, estimable = logrank_batch(time_array, event_array, treatment_array)
    if not bool(estimable[0]):
        return {
            "analysis_status": "FAILED",
            "failure_reason": "zero_logrank_variance",
            "z_statistic": None,
            "one_sided_p_value": None,
            "reject": None,
            "events": int(event_array.sum()),
        }
    z_statistic = float(statistic[0])
    p_value = _normal_cdf(z_statistic)
    return {
        "analysis_status": "COMPLETED",
        "failure_reason": None,
        "z_statistic": z_statistic,
        "one_sided_p_value": p_value,
        "reject": bool(p_value < alpha),
        "events": int(event_array.sum()),
    }


def logrank_edge_fixtures(alpha: float = 0.025) -> list[dict[str, Any]]:
    n = 24
    control = np.arange(1.0, n + 1.0)
    experimental = np.arange(n + 1.0, 2.0 * n + 1.0)
    treatment = np.array([0] * n + [1] * n, dtype=int)
    specifications = [
        ("POSITIVE_FAVORABLE", "positive", 2026081491,
         np.concatenate([control, experimental]), np.ones(2 * n, dtype=int)),
        ("NEGATIVE_UNFAVORABLE", "negative", 2026081492,
         np.concatenate([experimental, control]), np.ones(2 * n, dtype=int)),
        ("BOUNDARY_NO_EVENTS", "boundary_non_estimable", 2026081493,
         np.arange(1.0, 2.0 * n + 1.0), np.zeros(2 * n, dtype=int)),
    ]
    summaries: list[dict[str, Any]] = []
    for trial_id, role, seed, times, events in specifications:
        # The fixed seed controls row ordering and is retained in evidence even though
        # log-rank results are invariant to this permutation.
        order = np.random.default_rng(seed).permutation(2 * n)
        summary = summarize_trial(times[order], events[order], treatment[order], alpha)
        summaries.append({"id": trial_id, "role": role, "seed": seed, **summary})
    positive, negative, boundary = summaries
    records = [
        {**positive, "expected": "COMPLETED_REJECT"},
        {**negative, "expected": "COMPLETED_DO_NOT_REJECT"},
        {**boundary, "expected": "FAILED_ZERO_VARIANCE"},
    ]
    records[0]["validation_status"] = (
        "PASS" if records[0]["analysis_status"] == "COMPLETED" and records[0]["reject"] is True
        and records[0]["z_statistic"] < 0 else "FAIL"
    )
    records[1]["validation_status"] = (
        "PASS" if records[1]["analysis_status"] == "COMPLETED" and records[1]["reject"] is False
        and records[1]["z_statistic"] > 0 else "FAIL"
    )
    records[2]["validation_status"] = (
        "PASS" if records[2]["analysis_status"] == "FAILED"
        and records[2]["failure_reason"] == "zero_logrank_variance" else "FAIL"
    )
    return records


def _annual_probability_to_monthly_hazard(probability: float) -> float:
    if probability == 0.0:
        return 0.0
    return -math.log1p(-probability) / 12.0


def _piecewise_cumulative_hazard(time: np.ndarray, starts: np.ndarray, hrs: np.ndarray,
                                 baseline_hazard: float) -> np.ndarray:
    result = np.zeros_like(time, dtype=float)
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else np.inf
        duration = np.maximum(np.minimum(time, end) - start, 0.0)
        result += baseline_hazard * hrs[index] * duration
    return result


def _inverse_piecewise_hazard(target: np.ndarray, starts: np.ndarray, hrs: np.ndarray,
                              baseline_hazard: float) -> np.ndarray:
    result = np.empty_like(target, dtype=float)
    unresolved = np.ones(target.shape, dtype=bool)
    consumed = 0.0
    for index, start in enumerate(starts):
        rate = baseline_hazard * hrs[index]
        if index + 1 == len(starts):
            result[unresolved] = start + (target[unresolved] - consumed) / rate
            unresolved[:] = False
            break
        end = starts[index + 1]
        capacity = rate * (end - start)
        within = unresolved & (target <= consumed + capacity)
        result[within] = start + (target[within] - consumed) / rate
        unresolved &= ~within
        consumed += capacity
    return result


def _event_time_experimental(rng: np.random.Generator, shape: tuple[int, int],
                             baseline_hazard: float, scenario: Mapping[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    segments = scenario["treatment_hr_segments"]
    starts = np.asarray([segment["start_month"] for segment in segments], dtype=float)
    hrs = np.asarray([segment["hazard_ratio"] for segment in segments], dtype=float)
    target = rng.exponential(scale=1.0, size=shape)
    discontinuation_hazard = _annual_probability_to_monthly_hazard(
        float(scenario["discontinuation_rate_12m"])
    )
    if discontinuation_hazard == 0.0:
        discontinuation = np.full(shape, np.inf, dtype=float)
        return _inverse_piecewise_hazard(target, starts, hrs, baseline_hazard), discontinuation

    discontinuation = rng.exponential(scale=1.0 / discontinuation_hazard, size=shape)
    hazard_at_discontinuation = _piecewise_cumulative_hazard(
        discontinuation, starts, hrs, baseline_hazard
    )
    before = target <= hazard_at_discontinuation
    event_time = np.empty(shape, dtype=float)
    if np.any(before):
        event_time[before] = _inverse_piecewise_hazard(
            target[before], starts, hrs, baseline_hazard
        )
    post_rate = baseline_hazard * float(scenario["post_discontinuation_hazard_ratio"])
    event_time[~before] = (
        discontinuation[~before]
        + (target[~before] - hazard_at_discontinuation[~before]) / post_rate
    )
    return event_time, discontinuation


def _withdrawal_time(rng: np.random.Generator, shape: tuple[int, int], probability: float) -> np.ndarray:
    hazard = _annual_probability_to_monthly_hazard(probability)
    if hazard == 0.0:
        return np.full(shape, np.inf, dtype=float)
    return rng.exponential(scale=1.0 / hazard, size=shape)


def _status(value: str, reason: str) -> dict[str, str]:
    return {"status": value, "reason": reason}


def evaluate_scenario_statuses(
    *,
    requested: int,
    completed: int,
    failures: Mapping[str, int],
    rejection: Mapping[str, Any] | None,
    criteria: Mapping[str, Any],
    is_null: bool,
) -> tuple[dict[str, dict[str, str]], dict[str, Any] | None]:
    """Separate run execution/accounting from precision and design acceptance."""
    failed = sum(int(value) for value in failures.values())
    accounted = requested == completed + failed
    batch_failures = sum(
        int(value) for key, value in failures.items() if str(key).startswith("batch_exception:")
    )
    execution_pass = accounted and batch_failures == 0
    execution = _status(
        "PASS" if execution_pass else "FAIL",
        (
            f"Run executed and all replicates are accounted: requested={requested}, "
            f"completed={completed}, failed={failed}."
        ) if execution_pass else (
            f"Execution/accounting failed: requested={requested}, completed={completed}, "
            f"failed={failed}, batch_exception_failures={batch_failures}."
        ),
    )

    failure_rate = failed / requested if requested else math.inf
    minimum = (int(criteria["key_null_min_completed"]) if is_null
               else int(criteria["alternative_min_completed"]))
    target_mcse = float(criteria["target_mcse_key_null"]) if is_null else None
    precision_pass = (
        execution_pass
        and rejection is not None
        and completed >= minimum
        and failure_rate <= float(criteria["max_failure_rate"])
        and (target_mcse is None or float(rejection["mcse"]) <= target_mcse)
    )
    precision_reason = (
        f"Completed {completed} >= {minimum}; failure rate {failure_rate:.6g} <= "
        f"{float(criteria['max_failure_rate']):.6g}"
        + (f"; MCSE {float(rejection['mcse']):.6g} <= {target_mcse:.6g}."
           if target_mcse is not None and rejection is not None else ".")
    ) if precision_pass else (
        f"Required completed={minimum}, max failure rate={float(criteria['max_failure_rate']):.6g}"
        + (f", max MCSE={target_mcse:.6g}" if target_mcse is not None else "")
        + f"; observed completed={completed}, failure rate={failure_rate:.6g}"
        + (f", MCSE={float(rejection['mcse']):.6g}." if rejection is not None
           else ", no estimable result.")
    )
    precision = _status("PASS" if precision_pass else "FAIL", precision_reason)

    if is_null and rejection is not None:
        expected = float(criteria["analytic_null_probability"])
        absolute_deviation = abs(float(rejection["estimate"]) - expected)
        tolerance = max(
            float(criteria["analytic_null_abs_tolerance_floor"]),
            float(criteria["analytic_null_mcse_multiplier"]) * float(rejection["mcse"]),
        )
        interval = rejection["wilson_95"]
        interval_contains = float(interval["lower"]) <= expected <= float(interval["upper"])
        design_pass = interval_contains and absolute_deviation <= tolerance
        design = _status(
            "PASS" if design_pass else "FAIL",
            f"Wilson contains alpha={interval_contains}; absolute deviation "
            f"{absolute_deviation:.6g} <= tolerance {tolerance:.6g} is "
            f"{absolute_deviation <= tolerance}.",
        )
        analytic_null = {
            "expected_probability": expected,
            "absolute_deviation": absolute_deviation,
            "acceptance_tolerance": tolerance,
            "wilson_contains_expected": interval_contains,
            "acceptance_status": design["status"],
        }
    else:
        design = _status(
            "NOT_PREDEFINED",
            "No minimum power criterion was prespecified; estimate is descriptive.",
        )
        analytic_null = None
    return {
        "execution": execution,
        "precision": precision,
        "design_operating_characteristic": design,
    }, analytic_null


def _generate_trial_batch(rng: np.random.Generator, current: int,
                          config: Mapping[str, Any], scenario: Mapping[str, Any]) -> dict[str, np.ndarray]:
    """Generate one vectorized batch and retain only arrays needed for analysis/evidence."""
    design = config["design"]
    n_control = int(design["allocation"]["control"])
    n_experimental = int(design["allocation"]["experimental"])
    baseline_hazard = math.log(2.0) / float(
        design["endpoint_control_medians_months"][scenario["endpoint"]]
    )
    treatment = np.array([0] * n_control + [1] * n_experimental, dtype=int)
    enroll_control = rng.uniform(0.0, float(design["enrollment_months"]),
                                 size=(current, n_control))
    enroll_experimental = rng.uniform(0.0, float(design["enrollment_months"]),
                                      size=(current, n_experimental))
    event_control = rng.exponential(scale=1.0 / baseline_hazard, size=(current, n_control))
    event_experimental, discontinuation = _event_time_experimental(
        rng, (current, n_experimental), baseline_hazard, scenario
    )
    withdrawal_control = _withdrawal_time(
        rng, (current, n_control), float(scenario["withdrawal_rate_12m"]["control"])
    )
    withdrawal_experimental = _withdrawal_time(
        rng, (current, n_experimental), float(scenario["withdrawal_rate_12m"]["experimental"])
    )
    admin_control = float(design["analysis_month"]) - enroll_control
    admin_experimental = float(design["analysis_month"]) - enroll_experimental
    censor_control = np.minimum(withdrawal_control, admin_control)
    censor_experimental = np.minimum(withdrawal_experimental, admin_experimental)
    observed_control = np.minimum(event_control, censor_control)
    observed_experimental = np.minimum(event_experimental, censor_experimental)
    status_control = event_control <= censor_control
    status_experimental = event_experimental <= censor_experimental
    observed = np.concatenate([observed_control, observed_experimental], axis=1)
    status = np.concatenate([status_control, status_experimental], axis=1).astype(np.int8)
    z_statistic, estimable = logrank_batch(observed, status, treatment)
    return {
        "z_statistic": z_statistic,
        "estimable": estimable,
        "status_control": status_control,
        "status_experimental": status_experimental,
        "event_experimental": event_experimental,
        "discontinuation": discontinuation,
    }


def select_representative_trials(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Select aggregate scenario-derived trials using the frozen seed/search rule."""
    selection = config["representative_trial_selection"]
    scenario = next(item for item in config["scenarios"] if item["id"] == selection["scenario_id"])
    _require(int(selection["scenario_seed_binding"]) == int(scenario["seed"]),
             "representative trial scenario seed binding drifted")
    rng = np.random.default_rng(int(selection["selection_seed"]))
    alpha = float(config["design"]["alpha_one_sided"])
    search_replicates = int(selection["search_replicates"])
    batch_size = int(selection["batch_size"])
    n_control = int(config["design"]["allocation"]["control"])
    n_experimental = int(config["design"]["allocation"]["experimental"])
    selected: dict[str, dict[str, Any]] = {}
    nearest_distance = math.inf

    for offset in range(0, search_replicates, batch_size):
        current = min(batch_size, search_replicates - offset)
        batch = _generate_trial_batch(rng, current, config, scenario)
        for local_index in range(current):
            if not bool(batch["estimable"][local_index]):
                continue
            search_index = offset + local_index + 1
            z_statistic = float(batch["z_statistic"][local_index])
            p_value = _normal_cdf(z_statistic)
            control_events = int(batch["status_control"][local_index].sum())
            experimental_events = int(batch["status_experimental"][local_index].sum())
            record = {
                "scenario_id": scenario["id"],
                "scenario_seed": int(scenario["seed"]),
                "selection_seed": int(selection["selection_seed"]),
                "search_index": search_index,
                "endpoint": scenario["endpoint"],
                "events": {"control": control_events, "experimental": experimental_events},
                "censors": {
                    "control": n_control - control_events,
                    "experimental": n_experimental - experimental_events,
                },
                "z_statistic": z_statistic,
                "one_sided_p_value": p_value,
                "alpha_one_sided": alpha,
                "decision": "REJECT" if p_value < alpha else "DO_NOT_REJECT",
            }
            if "reject" not in selected and p_value < alpha:
                selected["reject"] = {"selection_role": "reject", **record}
            if "non_reject" not in selected and p_value >= 0.5:
                selected["non_reject"] = {"selection_role": "non_reject", **record}
            distance = abs(p_value - alpha)
            if distance < nearest_distance:
                nearest_distance = distance
                selected["near_alpha_boundary"] = {
                    "selection_role": "near_alpha_boundary",
                    "absolute_distance_from_alpha": distance,
                    **record,
                }
    missing = [role for role in ("reject", "non_reject", "near_alpha_boundary") if role not in selected]
    _require(not missing,
             "representative trial search did not find governed role(s): " + ", ".join(missing))
    return [selected[role] for role in ("reject", "non_reject", "near_alpha_boundary")]


def simulate_scenario(config: Mapping[str, Any], scenario: Mapping[str, Any]) -> dict[str, Any]:
    design = config["design"]
    criteria = config["acceptance_criteria"]
    n_control = int(design["allocation"]["control"])
    n_experimental = int(design["allocation"]["experimental"])
    requested = int(scenario["replicates"])
    batch_size = int(design["batch_size"])
    rng = np.random.default_rng(int(scenario["seed"]))
    alpha = float(design["alpha_one_sided"])
    critical_z = NORMAL_CDF_025  # valid because governed alpha is exactly 0.025

    completed = 0
    failed = 0
    rejected = 0
    failure_reasons: dict[str, int] = {}
    event_sums = {"control": 0, "experimental": 0}
    censor_sums = {"control": 0, "experimental": 0}
    discontinuation_sum = 0

    for offset in range(0, requested, batch_size):
        current = min(batch_size, requested - offset)
        try:
            batch = _generate_trial_batch(rng, current, config, scenario)
            z_statistic = batch["z_statistic"]
            estimable = batch["estimable"]
            status_control = batch["status_control"]
            status_experimental = batch["status_experimental"]
            event_experimental = batch["event_experimental"]
            discontinuation = batch["discontinuation"]
        except Exception as exc:  # batch failures are retained, categorized, and block execution
            failed += current
            reason = f"batch_exception:{type(exc).__name__}:{str(exc)}"
            failure_reasons[reason] = failure_reasons.get(reason, 0) + current
            continue

        invalid_count = int((~estimable).sum())
        if invalid_count:
            failed += invalid_count
            failure_reasons["zero_logrank_variance"] = (
                failure_reasons.get("zero_logrank_variance", 0) + invalid_count
            )
        valid = estimable
        valid_count = int(valid.sum())
        completed += valid_count
        if valid_count:
            rejected += int(np.count_nonzero(z_statistic[valid] < critical_z))
            control_events = status_control[valid].sum(axis=1)
            experimental_events = status_experimental[valid].sum(axis=1)
            event_sums["control"] += int(control_events.sum())
            event_sums["experimental"] += int(experimental_events.sum())
            censor_sums["control"] += int(valid_count * n_control - control_events.sum())
            censor_sums["experimental"] += int(valid_count * n_experimental - experimental_events.sum())
            discontinuation_sum += int(
                np.count_nonzero(discontinuation[valid] < event_experimental[valid])
            )

    _require(requested == completed + failed,
             f"internal accounting failure for {scenario['id']}: requested != completed + failed")
    rejection = probability_summary(rejected, completed, float(criteria["wilson_confidence_level"])) if completed else None
    failure_rate = failed / requested
    is_null = str(scenario["class"]).startswith("KEY_NULL")
    status_map, analytic_null = evaluate_scenario_statuses(
        requested=requested,
        completed=completed,
        failures=failure_reasons,
        rejection=rejection,
        criteria=criteria,
        is_null=is_null,
    )

    def arm_summary(sum_value: int, subjects: int) -> dict[str, Any]:
        denominator = completed * subjects
        return {
            "total": sum_value,
            "denominator": denominator,
            "mean_count_per_trial": (sum_value / completed if completed else None),
            "mean_proportion": (sum_value / denominator if denominator else None),
        }

    result: dict[str, Any] = {
        "id": scenario["id"],
        "endpoint": scenario["endpoint"],
        "class": scenario["class"],
        "family": scenario["family"],
        "rationale": scenario["rationale"],
        "assumption_basis": scenario["assumption_basis"],
        "seed": int(scenario["seed"]),
        "requested": requested,
        "completed": completed,
        "failed": failed,
        "failure_rate": failure_rate,
        "failures": dict(sorted(failure_reasons.items())),
        "rejection": rejection,
        "events": {
            "control": arm_summary(event_sums["control"], n_control),
            "experimental": arm_summary(event_sums["experimental"], n_experimental),
        },
        "censoring": {
            "control": arm_summary(censor_sums["control"], n_control),
            "experimental": arm_summary(censor_sums["experimental"], n_experimental),
        },
        "experimental_discontinuations_before_event": {
            "total": discontinuation_sum,
            "denominator": completed * n_experimental,
            "mean_proportion": (
                discontinuation_sum / (completed * n_experimental) if completed else None
            ),
        },
        "analytic_null_benchmark": analytic_null,
        "statuses": status_map,
        "scenario_sha256": sha256_value(scenario),
    }
    return result


def build_results(config: Mapping[str, Any], protocol_path: str | Path = DEFAULT_PROTOCOL) -> dict[str, Any]:
    validate_protocol(config)
    path = Path(protocol_path)
    if path.exists():
        on_disk = load_protocol(path)
        _require(canonical_json(on_disk) == canonical_json(config),
                 "in-memory protocol differs from the hash-bound protocol file")
    scenario_results = [simulate_scenario(config, scenario) for scenario in config["scenarios"]]
    trials = select_representative_trials(config)
    edge_fixtures = logrank_edge_fixtures(float(config["design"]["alpha_one_sided"]))
    null_results = [result for result in scenario_results
                    if str(result["class"]).startswith("KEY_NULL")]
    analytic_pass = bool(null_results) and all(
        result["statuses"]["design_operating_characteristic"]["status"] == "PASS"
        for result in null_results
    )
    edge_fixtures_pass = all(trial["validation_status"] == "PASS" for trial in edge_fixtures)
    representative_roles_pass = (
        [trial["selection_role"] for trial in trials]
        == ["reject", "non_reject", "near_alpha_boundary"]
        and trials[0]["decision"] == "REJECT"
        and trials[1]["decision"] == "DO_NOT_REJECT"
    )
    execution_pass = all(result["statuses"]["execution"]["status"] == "PASS"
                         for result in scenario_results)
    precision_pass = all(result["statuses"]["precision"]["status"] == "PASS"
                         for result in scenario_results)
    design_pass = analytic_pass and edge_fixtures_pass and representative_roles_pass
    try:
        protocol_display_path = str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        protocol_display_path = path.name
    protocol_hash = sha256_file(path) if path.exists() else sha256_value(config)
    result: dict[str, Any] = {
        "schema_version": "1.0.0",
        "change_control": config["change_control"],
        "protocol": {
            "id": config["protocol"]["id"],
            "version": config["protocol"]["version"],
            "status": config["protocol"]["status"],
            "path": protocol_display_path,
            "protocol_sha256": protocol_hash,
            "scenario_registry_sha256": sha256_value(config["scenarios"]),
            "code_sha256": sha256_file(Path(__file__)),
        },
        "qualification_boundary": config["protocol"]["qualification_boundary"],
        "m15_assessment": config["m15_assessment"],
        "estimand": config["estimand"],
        "protocol_framework": config["protocol_framework"],
        "design": config["design"],
        "acceptance_criteria": config["acceptance_criteria"],
        "representative_trial_selection": config["representative_trial_selection"],
        "software_identity": software_identity(),
        "methods": {
            "data_level": "INDIVIDUAL_SIMULATED_SUBJECT",
            "event_model": "PIECEWISE_EXPONENTIAL",
            "random_number_generator": "numpy.random.Generator(PCG64)",
            "analysis_method": "ONE_SIDED_UNSTRATIFIED_LOGRANK",
            "benefit_direction": "NEGATIVE_Z",
            "continuous_time_ties": "PROBABILITY_ZERO",
            "limitation": config["design"]["omitted_design_feature"],
        },
        "scenarios": scenario_results,
        "representative_trials": trials,
        "validation": {
            "analytic_null_benchmark": {
                "status": "PASS" if analytic_pass else "FAIL",
                "rule": config["acceptance_criteria"]["null_acceptance"],
                "scenario_ids": [result["id"] for result in null_results],
            },
            "representative_trial_selection": {
                "status": "PASS" if representative_roles_pass else "FAIL",
                "roles_found": [trial["selection_role"] for trial in trials],
                "note": "Scenario-derived aggregate trial examples; no subject rows are retained.",
            },
            "logrank_edge_fixtures": edge_fixtures,
            "logrank_edge_fixture_status": {
                "status": "PASS" if edge_fixtures_pass else "FAIL",
                "note": "Artificial positive, negative, and non-estimable fixtures; not simulated trial paths.",
            },
            "accounting_identity": {
                "status": "PASS" if all(
                    result["requested"] == result["completed"] + result["failed"]
                    for result in scenario_results
                ) else "FAIL",
                "rule": "requested = completed + failed for every scenario",
            },
        },
        "statuses": {
            "execution": _status("PASS" if execution_pass else "FAIL",
                                 "Every run executed and requested/completed/failed accounting is complete."
                                 if execution_pass else "At least one scenario has an execution or accounting failure."),
            "monte_carlo_precision": _status(
                "PASS" if precision_pass else "FAIL",
                "Every scenario met its prespecified replication, failure-rate, and MCSE controls."
                if precision_pass else "At least one scenario missed a precision control.",
            ),
            "design_operating_characteristics": _status(
                "PASS" if design_pass else "FAIL",
                "Analytic null, scenario-derived trial selection, and log-rank edge checks passed."
                if design_pass else "At least one analytic-null, trial-selection, or log-rank edge check failed.",
            ),
            "evidence_qualification": _status(
                "NOT_QUALIFIED",
                "Informational, data-free, non-MIDD, non-confirmatory methods evaluation only.",
            ),
        },
    }
    result["scientific_output_sha256"] = sha256_value(result)
    return result


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                    encoding="utf-8", newline="\n")


def write_results(result: Mapping[str, Any], out_dir: str | Path,
                  report: str | Path | None = None) -> dict[str, Path]:
    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    result_path = directory / RESULT_NAME
    csv_path = directory / CSV_NAME
    trials_path = directory / TRIALS_NAME
    _write_json(result_path, result)
    _write_json(trials_path, result["representative_trials"])

    columns = [
        "id", "endpoint", "class", "family", "assumption_basis", "seed",
        "requested", "completed", "failed", "failure_rate", "rejections",
        "estimate", "mcse", "wilson_95_lower", "wilson_95_upper",
        "control_event_proportion", "experimental_event_proportion",
        "control_censor_proportion", "experimental_censor_proportion",
        "execution_status", "precision_status", "design_status", "scenario_sha256",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for scenario in result["scenarios"]:
            rejection = scenario["rejection"] or {}
            wilson = rejection.get("wilson_95", {})
            writer.writerow({
                "id": scenario["id"],
                "endpoint": scenario["endpoint"],
                "class": scenario["class"],
                "family": scenario["family"],
                "assumption_basis": scenario["assumption_basis"],
                "seed": scenario["seed"],
                "requested": scenario["requested"],
                "completed": scenario["completed"],
                "failed": scenario["failed"],
                "failure_rate": scenario["failure_rate"],
                "rejections": rejection.get("numerator"),
                "estimate": rejection.get("estimate"),
                "mcse": rejection.get("mcse"),
                "wilson_95_lower": wilson.get("lower"),
                "wilson_95_upper": wilson.get("upper"),
                "control_event_proportion": scenario["events"]["control"]["mean_proportion"],
                "experimental_event_proportion": scenario["events"]["experimental"]["mean_proportion"],
                "control_censor_proportion": scenario["censoring"]["control"]["mean_proportion"],
                "experimental_censor_proportion": scenario["censoring"]["experimental"]["mean_proportion"],
                "execution_status": scenario["statuses"]["execution"]["status"],
                "precision_status": scenario["statuses"]["precision"]["status"],
                "design_status": scenario["statuses"]["design_operating_characteristic"]["status"],
                "scenario_sha256": scenario["scenario_sha256"],
            })

    paths = {"results": result_path, "csv": csv_path, "representative_trials": trials_path}
    if report is not None:
        report_path = Path(report)
        _require(report_path.suffix.lower() == ".json",
                 "--report accepts only a machine-readable .json path; reviewer Markdown is generated separately")
        _write_json(report_path, result)
        paths["report"] = report_path
    return paths


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL,
                        help="governed YAML protocol (default: config/simulation_protocol.yaml)")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR,
                        help="directory for authoritative JSON/CSV outputs")
    parser.add_argument("--report", type=Path, default=None,
                        help="optional additional machine-readable .json copy; never generates reviewer Markdown")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        config = load_protocol(args.protocol)
        validate_protocol(config)
        result = build_results(config, args.protocol)
        paths = write_results(result, args.out_dir, args.report)
    except (ProtocolError, OSError) as exc:
        print(f"SIMULATION_PROTOCOL_ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Protocol SHA-256: {result['protocol']['protocol_sha256']}")
    print(f"Scenario registry SHA-256: {result['protocol']['scenario_registry_sha256']}")
    print(f"Scientific output SHA-256: {result['scientific_output_sha256']}")
    for label, path in paths.items():
        print(f"Wrote {label}: {path}")
    for name, status in result["statuses"].items():
        print(f"{name}: {status['status']} - {status['reason']}")
    return 0 if all(
        result["statuses"][name]["status"] == "PASS"
        for name in ("execution", "monte_carlo_precision", "design_operating_characteristics")
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
