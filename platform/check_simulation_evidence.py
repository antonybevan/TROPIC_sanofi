#!/usr/bin/env python3
"""Independently verify the governed simulation evidence bundle.

This program is deliberately a consumer of the scientific artifacts.  It does
not import the simulation engine and it never writes or repairs evidence.  A
single failed invariant makes the command fail closed with actionable errors.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Mapping, Sequence

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / "config/simulation_protocol.yaml"
DEFAULT_RESULTS = (
    ROOT / "platform/simulation_operating_characteristics/simulation_oc_status.json"
)
DEFAULT_CODE = ROOT / "platform/simulation_precision.py"
DEFAULT_CSV = ROOT / "platform/simulation_operating_characteristics/scenario_results.csv"
DEFAULT_TRIALS = (
    ROOT / "platform/simulation_operating_characteristics/representative_trials.json"
)
DEFAULT_REPORT = ROOT / "07_reviewer_explanation/simulation_report.md"

NORMAL_975 = 1.959963984540054
FLOAT_TOLERANCE = 5e-12
KEY_NULL_MINIMUM = 100_000
OTHER_SCENARIO_MINIMUM = 25_000
MAX_FAILURE_RATE = 0.001
NULL_ALPHA = 0.025
NULL_ABSOLUTE_FLOOR = 0.001
NULL_MCSE_MULTIPLIER = 3.0
KEY_NULL_MAX_MCSE = 0.0005
GOVERNED_SCENARIO_IDS = (
    "OS_NULL_REFERENCE",
    "PFS_NULL_HIGH_DROPOUT",
    "OS_PUBLISHED_EFFECT",
    "PFS_PUBLISHED_EFFECT",
    "OS_MEDIAN_CALIBRATED",
    "PFS_MEDIAN_CALIBRATED",
    "OS_DELAYED_NON_PH",
    "PFS_DELAYED_NON_PH",
    "OS_WANING_AFTER_DISCONTINUATION",
    "PFS_WANING_AFTER_DISCONTINUATION",
)


class EvidenceVerificationError(ValueError):
    """Raised when one or more governed evidence invariants fail."""

    def __init__(self, errors: Sequence[str]):
        self.errors = list(errors)
        super().__init__("\n".join(self.errors))


class _Audit:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def error(self, path: str, message: str) -> None:
        self.errors.append(f"{path}: {message}")

    def check(self, condition: bool, path: str, message: str) -> bool:
        if not condition:
            self.error(path, message)
            return False
        return True

    def finish(self) -> None:
        if self.errors:
            raise EvidenceVerificationError(self.errors)


def _reject_nonfinite_json(token: str) -> None:
    raise ValueError(f"non-finite JSON number {token!r} is prohibited")


def _load_json(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"), parse_constant=_reject_nonfinite_json
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise EvidenceVerificationError([f"{path}: cannot read strict JSON: {exc}"]) from exc


def _load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise EvidenceVerificationError([f"{path}: cannot read YAML: {exc}"]) from exc


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _sha256_value(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _close(actual: Any, expected: float) -> bool:
    return (
        _is_number(actual)
        and math.isfinite(float(actual))
        and math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=FLOAT_TOLERANCE)
    )


def _walk_finite(value: Any, path: str, audit: _Audit) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        audit.error(path, "NaN and infinity are prohibited")
    elif isinstance(value, Mapping):
        for key, item in value.items():
            _walk_finite(item, f"{path}.{key}", audit)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk_finite(item, f"{path}[{index}]", audit)


def _mapping(value: Any, path: str, audit: _Audit) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        audit.error(path, "must be an object")
        return None
    return value


def _list(value: Any, path: str, audit: _Audit) -> list[Any] | None:
    if not isinstance(value, list):
        audit.error(path, "must be an array")
        return None
    return value


def _require_keys(
    value: Mapping[str, Any], keys: Iterable[str], path: str, audit: _Audit
) -> bool:
    missing = [key for key in keys if key not in value]
    if missing:
        audit.error(path, f"missing required field(s): {', '.join(missing)}")
        return False
    return True


def _status(
    statuses: Mapping[str, Any] | None, name: str, path: str, audit: _Audit
) -> str | None:
    if statuses is None:
        return None
    record = _mapping(statuses.get(name), f"{path}.{name}", audit)
    if record is None:
        return None
    value = record.get("status")
    if not isinstance(value, str) or not value:
        audit.error(f"{path}.{name}.status", "must be non-empty text")
        value = None
    reason = record.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        audit.error(f"{path}.{name}.reason", "must be non-empty text")
    return value


def _wilson(successes: int, trials: int) -> tuple[float, float]:
    estimate = successes / trials
    z2 = NORMAL_975 * NORMAL_975
    denominator = 1.0 + z2 / trials
    center = (estimate + z2 / (2.0 * trials)) / denominator
    half_width = (
        NORMAL_975
        * math.sqrt(
            estimate * (1.0 - estimate) / trials + z2 / (4.0 * trials * trials)
        )
        / denominator
    )
    return max(0.0, center - half_width), min(1.0, center + half_width)


def _check_exact_number(
    value: Any, expected: float, path: str, audit: _Audit, description: str
) -> None:
    audit.check(_close(value, expected), path, f"must equal {description} ({expected!r})")


def _check_protocol_controls(protocol: Mapping[str, Any], audit: _Audit) -> None:
    audit.check(protocol.get("schema_version") == "1.0.0", "protocol.schema_version", "must equal 1.0.0")
    change_control = _mapping(protocol.get("change_control"), "protocol.change_control", audit)
    if change_control is not None:
        audit.check(
            change_control.get("full_run_started_after_freeze") is True,
            "protocol.change_control.full_run_started_after_freeze",
            "must be true",
        )
        audit.check(
            isinstance(change_control.get("deviations"), list),
            "protocol.change_control.deviations",
            "must be an array",
        )
    info = _mapping(protocol.get("protocol"), "protocol.protocol", audit)
    criteria = _mapping(protocol.get("acceptance_criteria"), "protocol.acceptance_criteria", audit)
    if info is not None:
        audit.check(info.get("status") == "FROZEN_MAP", "protocol.protocol.status", "must equal FROZEN_MAP")
        boundary = _mapping(
            info.get("qualification_boundary"),
            "protocol.protocol.qualification_boundary",
            audit,
        )
        if boundary is not None:
            expected = {
                "classification": "NON_MIDD_NON_CONFIRMATORY_DATA_FREE_METHODS_EVALUATION",
                "model_influence": "LOW",
                "evidence_status": "INFORMATIONAL_ONLY",
                "authoritative_patient_data_used": False,
                "external_validation_completed": False,
            }
            for key, value in expected.items():
                audit.check(
                    boundary.get(key) == value,
                    f"protocol.protocol.qualification_boundary.{key}",
                    f"must equal {value!r}",
                )
        prohibited = info.get("prohibited_uses")
        if isinstance(prohibited, list) and all(isinstance(item, str) for item in prohibited):
            joined = " ".join(prohibited).lower()
            audit.check("midd" in joined, "protocol.protocol.prohibited_uses", "must prohibit MIDD use")
            audit.check(
                "confirmatory" in joined and "filing" in joined,
                "protocol.protocol.prohibited_uses",
                "must prohibit confirmatory and filing use",
            )
        else:
            audit.error("protocol.protocol.prohibited_uses", "must be an array of text")
    if criteria is not None:
        required = (
            "key_null_min_completed",
            "alternative_min_completed",
            "target_mcse_key_null",
            "max_failure_rate",
            "analytic_null_probability",
            "analytic_null_abs_tolerance_floor",
            "analytic_null_mcse_multiplier",
            "wilson_confidence_level",
        )
        _require_keys(criteria, required, "protocol.acceptance_criteria", audit)
        audit.check(
            _is_int(criteria.get("key_null_min_completed"))
            and criteria["key_null_min_completed"] >= KEY_NULL_MINIMUM,
            "protocol.acceptance_criteria.key_null_min_completed",
            f"must be an integer >= {KEY_NULL_MINIMUM}",
        )
        audit.check(
            _is_int(criteria.get("alternative_min_completed"))
            and criteria["alternative_min_completed"] >= OTHER_SCENARIO_MINIMUM,
            "protocol.acceptance_criteria.alternative_min_completed",
            f"must be an integer >= {OTHER_SCENARIO_MINIMUM}",
        )
        _check_exact_number(
            criteria.get("target_mcse_key_null"),
            KEY_NULL_MAX_MCSE,
            "protocol.acceptance_criteria.target_mcse_key_null",
            audit,
            "the governed key-null MCSE ceiling",
        )
        _check_exact_number(
            criteria.get("max_failure_rate"),
            MAX_FAILURE_RATE,
            "protocol.acceptance_criteria.max_failure_rate",
            audit,
            "the governed failure cap",
        )
        _check_exact_number(
            criteria.get("analytic_null_probability"),
            NULL_ALPHA,
            "protocol.acceptance_criteria.analytic_null_probability",
            audit,
            "the governed one-sided alpha",
        )
        _check_exact_number(
            criteria.get("analytic_null_abs_tolerance_floor"),
            NULL_ABSOLUTE_FLOOR,
            "protocol.acceptance_criteria.analytic_null_abs_tolerance_floor",
            audit,
            "the governed absolute-deviation floor",
        )
        _check_exact_number(
            criteria.get("analytic_null_mcse_multiplier"),
            NULL_MCSE_MULTIPLIER,
            "protocol.acceptance_criteria.analytic_null_mcse_multiplier",
            audit,
            "the governed MCSE multiplier",
        )
        _check_exact_number(
            criteria.get("wilson_confidence_level"),
            0.95,
            "protocol.acceptance_criteria.wilson_confidence_level",
            audit,
            "the governed confidence level",
        )


def _check_hashes(
    protocol: Mapping[str, Any],
    results: Mapping[str, Any],
    protocol_path: Path,
    code_path: Path,
    audit: _Audit,
) -> None:
    recorded = _mapping(results.get("protocol"), "results.protocol", audit)
    if recorded is not None:
        try:
            expected_protocol_hash = _sha256_file(protocol_path)
        except OSError as exc:
            audit.error(str(protocol_path), f"cannot hash governed protocol: {exc}")
        else:
            audit.check(
                recorded.get("protocol_sha256") == expected_protocol_hash,
                "results.protocol.protocol_sha256",
                f"does not match {protocol_path} ({expected_protocol_hash})",
            )
        try:
            expected_code_hash = _sha256_file(code_path)
        except OSError as exc:
            audit.error(str(code_path), f"cannot hash simulation code: {exc}")
        else:
            audit.check(
                recorded.get("code_sha256") == expected_code_hash,
                "results.protocol.code_sha256",
                f"does not match {code_path} ({expected_code_hash})",
            )
        scenarios = protocol.get("scenarios")
        if isinstance(scenarios, list):
            expected_registry_hash = _sha256_value(scenarios)
            audit.check(
                recorded.get("scenario_registry_sha256") == expected_registry_hash,
                "results.protocol.scenario_registry_sha256",
                f"does not match canonical governed scenario registry ({expected_registry_hash})",
            )
    recorded_output_hash = results.get("scientific_output_sha256")
    if not isinstance(recorded_output_hash, str):
        audit.error("results.scientific_output_sha256", "must be a SHA-256 string")
    else:
        unhashed = dict(results)
        unhashed.pop("scientific_output_sha256", None)
        try:
            expected_output_hash = _sha256_value(unhashed)
        except (TypeError, ValueError) as exc:
            audit.error("results", f"cannot canonicalize scientific output: {exc}")
        else:
            audit.check(
                recorded_output_hash == expected_output_hash,
                "results.scientific_output_sha256",
                f"does not match canonical scientific content ({expected_output_hash})",
            )


def _check_arm_summary(
    summary: Any,
    path: str,
    completed: int,
    subjects: int,
    audit: _Audit,
) -> int | None:
    record = _mapping(summary, path, audit)
    if record is None:
        return None
    total = record.get("total")
    denominator = record.get("denominator")
    expected_denominator = completed * subjects
    if not _is_int(total) or total < 0:
        audit.error(f"{path}.total", "must be a non-negative integer")
        total_value = None
    else:
        total_value = total
        audit.check(total <= expected_denominator, f"{path}.total", "must not exceed its denominator")
    audit.check(
        _is_int(denominator) and denominator == expected_denominator,
        f"{path}.denominator",
        f"must equal completed * arm size ({expected_denominator})",
    )
    expected_count = total_value / completed if completed and total_value is not None else None
    expected_proportion = (
        total_value / expected_denominator
        if expected_denominator and total_value is not None
        else None
    )
    if expected_count is None:
        audit.check(record.get("mean_count_per_trial") is None, f"{path}.mean_count_per_trial", "must be null when no replicate completed")
    else:
        _check_exact_number(record.get("mean_count_per_trial"), expected_count, f"{path}.mean_count_per_trial", audit, "total / completed")
    if expected_proportion is None:
        audit.check(record.get("mean_proportion") is None, f"{path}.mean_proportion", "must be null when its denominator is zero")
    else:
        _check_exact_number(record.get("mean_proportion"), expected_proportion, f"{path}.mean_proportion", audit, "total / denominator")
    return total_value


def _check_scenario(
    planned: Mapping[str, Any],
    observed: Mapping[str, Any],
    index: int,
    design: Mapping[str, Any],
    audit: _Audit,
) -> dict[str, bool]:
    scenario_id = planned.get("id")
    path = f"results.scenarios[{index}]({scenario_id})"
    for key in ("id", "endpoint", "class", "family", "rationale", "assumption_basis", "seed"):
        audit.check(observed.get(key) == planned.get(key), f"{path}.{key}", "must exactly match the governed scenario")
    audit.check(
        observed.get("scenario_sha256") == _sha256_value(planned),
        f"{path}.scenario_sha256",
        "does not match the canonical governed scenario",
    )

    requested = observed.get("requested")
    completed = observed.get("completed")
    failed = observed.get("failed")
    counts_valid = all(_is_int(value) and value >= 0 for value in (requested, completed, failed))
    if not counts_valid:
        audit.error(f"{path}.requested/completed/failed", "must be non-negative integers")
        return {"execution": False, "precision": False, "design": False, "null": False}
    audit.check(requested == planned.get("replicates"), f"{path}.requested", "must equal governed replicates")
    audit.check(requested == completed + failed, path, "requested must equal completed + failed")
    if "analyzed" in observed:
        audit.check(observed["analyzed"] == completed, f"{path}.analyzed", "must equal completed")
    minimum = KEY_NULL_MINIMUM if str(planned.get("class", "")).startswith("KEY_NULL") else OTHER_SCENARIO_MINIMUM
    audit.check(
        _is_int(planned.get("replicates")) and planned["replicates"] >= minimum,
        f"protocol.scenarios[{index}].replicates",
        f"must be an integer >= {minimum}",
    )
    audit.check(completed >= minimum, f"{path}.completed", f"must be >= {minimum}")
    expected_failure_rate = failed / requested if requested else math.inf
    _check_exact_number(observed.get("failure_rate"), expected_failure_rate, f"{path}.failure_rate", audit, "failed / requested")
    failure_rate_ok = math.isfinite(expected_failure_rate) and expected_failure_rate <= MAX_FAILURE_RATE
    audit.check(failure_rate_ok, f"{path}.failure_rate", f"must be <= {MAX_FAILURE_RATE}")
    failures = _mapping(observed.get("failures"), f"{path}.failures", audit)
    if failures is not None:
        values_valid = all(_is_int(value) and value > 0 for value in failures.values())
        audit.check(values_valid, f"{path}.failures", "counts must be positive integers")
        if values_valid:
            audit.check(sum(failures.values()) == failed, f"{path}.failures", "counts must sum to failed")

    rejection = _mapping(observed.get("rejection"), f"{path}.rejection", audit)
    statistics_valid = False
    estimate = mcse = lower = upper = None
    if rejection is not None:
        numerator = rejection.get("numerator")
        denominator = rejection.get("denominator")
        audit.check(_is_int(denominator) and denominator == completed, f"{path}.rejection.denominator", "must equal completed")
        numerator_valid = _is_int(numerator) and 0 <= numerator <= completed
        audit.check(numerator_valid, f"{path}.rejection.numerator", "must be an integer from 0 through completed")
        if denominator == completed and completed > 0 and numerator_valid:
            estimate = numerator / completed
            mcse = math.sqrt(estimate * (1.0 - estimate) / completed)
            lower, upper = _wilson(numerator, completed)
            _check_exact_number(rejection.get("estimate"), estimate, f"{path}.rejection.estimate", audit, "numerator / denominator")
            _check_exact_number(rejection.get("mcse"), mcse, f"{path}.rejection.mcse", audit, "binomial MCSE")
            interval = _mapping(rejection.get("wilson_95"), f"{path}.rejection.wilson_95", audit)
            if interval is not None:
                _check_exact_number(interval.get("lower"), lower, f"{path}.rejection.wilson_95.lower", audit, "the independently recomputed Wilson lower bound")
                _check_exact_number(interval.get("upper"), upper, f"{path}.rejection.wilson_95.upper", audit, "the independently recomputed Wilson upper bound")
                _check_exact_number(interval.get("confidence_level"), 0.95, f"{path}.rejection.wilson_95.confidence_level", audit, "0.95")
            statistics_valid = (
                _close(rejection.get("estimate"), estimate)
                and _close(rejection.get("mcse"), mcse)
                and interval is not None
                and _close(interval.get("lower"), lower)
                and _close(interval.get("upper"), upper)
                and _close(interval.get("confidence_level"), 0.95)
            )

    allocation = design.get("allocation") if isinstance(design.get("allocation"), Mapping) else {}
    n_control = allocation.get("control")
    n_experimental = allocation.get("experimental")
    if _is_int(n_control) and _is_int(n_experimental) and n_control > 0 and n_experimental > 0:
        event_record = _mapping(observed.get("events"), f"{path}.events", audit)
        censor_record = _mapping(observed.get("censoring"), f"{path}.censoring", audit)
        if event_record is not None and censor_record is not None:
            for arm, subjects in (("control", n_control), ("experimental", n_experimental)):
                event_total = _check_arm_summary(event_record.get(arm), f"{path}.events.{arm}", completed, subjects, audit)
                censor_total = _check_arm_summary(censor_record.get(arm), f"{path}.censoring.{arm}", completed, subjects, audit)
                if event_total is not None and censor_total is not None:
                    audit.check(event_total + censor_total == completed * subjects, f"{path}.{arm}", "event and censor totals must partition all completed arm observations")
        discontinuations = _mapping(
            observed.get("experimental_discontinuations_before_event"),
            f"{path}.experimental_discontinuations_before_event",
            audit,
        )
        if discontinuations is not None:
            total = discontinuations.get("total")
            expected_denominator = completed * n_experimental
            audit.check(_is_int(total) and 0 <= total <= expected_denominator, f"{path}.experimental_discontinuations_before_event.total", "must be a non-negative integer no larger than its denominator")
            audit.check(discontinuations.get("denominator") == expected_denominator, f"{path}.experimental_discontinuations_before_event.denominator", f"must equal {expected_denominator}")
            if _is_int(total) and expected_denominator:
                _check_exact_number(discontinuations.get("mean_proportion"), total / expected_denominator, f"{path}.experimental_discontinuations_before_event.mean_proportion", audit, "total / denominator")
            elif not expected_denominator:
                audit.check(discontinuations.get("mean_proportion") is None, f"{path}.experimental_discontinuations_before_event.mean_proportion", "must be null when denominator is zero")
    else:
        audit.error("protocol.design.allocation", "control and experimental arm sizes must be positive integers")

    is_null = str(planned.get("class", "")).startswith("KEY_NULL")
    null_pass = False
    analytic = observed.get("analytic_null_benchmark")
    if is_null and statistics_valid and estimate is not None and mcse is not None and lower is not None and upper is not None:
        analytic_record = _mapping(analytic, f"{path}.analytic_null_benchmark", audit)
        deviation = abs(estimate - NULL_ALPHA)
        tolerance = max(NULL_ABSOLUTE_FLOOR, NULL_MCSE_MULTIPLIER * mcse)
        contains = lower <= NULL_ALPHA <= upper
        null_pass = contains and deviation <= tolerance
        if analytic_record is not None:
            _check_exact_number(analytic_record.get("expected_probability"), NULL_ALPHA, f"{path}.analytic_null_benchmark.expected_probability", audit, "alpha")
            _check_exact_number(analytic_record.get("absolute_deviation"), deviation, f"{path}.analytic_null_benchmark.absolute_deviation", audit, "absolute estimate-alpha deviation")
            _check_exact_number(analytic_record.get("acceptance_tolerance"), tolerance, f"{path}.analytic_null_benchmark.acceptance_tolerance", audit, "max(0.001, 3*MCSE)")
            audit.check(analytic_record.get("wilson_contains_expected") is contains, f"{path}.analytic_null_benchmark.wilson_contains_expected", f"must equal {contains}")
            audit.check(analytic_record.get("acceptance_status") == ("PASS" if null_pass else "FAIL"), f"{path}.analytic_null_benchmark.acceptance_status", "must match the independent null acceptance decision")
    elif not is_null:
        audit.check(analytic is None, f"{path}.analytic_null_benchmark", "must be null for non-null scenarios")

    statuses = _mapping(observed.get("statuses"), f"{path}.statuses", audit)
    actual_execution = _status(statuses, "execution", f"{path}.statuses", audit)
    actual_precision = _status(statuses, "precision", f"{path}.statuses", audit)
    actual_design = _status(statuses, "design_operating_characteristic", f"{path}.statuses", audit)
    batch_failures = sum(
        value
        for key, value in (failures or {}).items()
        if isinstance(key, str)
        and key.startswith("batch_exception:")
        and _is_int(value)
    )
    execution_pass = requested == completed + failed and batch_failures == 0
    precision_pass = (
        execution_pass
        and statistics_valid
        and completed >= minimum
        and failure_rate_ok
        and (not is_null or (mcse is not None and mcse <= KEY_NULL_MAX_MCSE))
    )
    expected_design_status = "PASS" if is_null and null_pass else ("FAIL" if is_null else "NOT_PREDEFINED")
    audit.check(actual_execution == ("PASS" if execution_pass else "FAIL"), f"{path}.statuses.execution.status", "does not match failed-replicate accounting")
    audit.check(actual_precision == ("PASS" if precision_pass else "FAIL"), f"{path}.statuses.precision.status", "does not match replication, failure-rate, and MCSE thresholds")
    audit.check(actual_design == expected_design_status, f"{path}.statuses.design_operating_characteristic.status", "does not match the independent design acceptance decision")
    return {
        "execution": execution_pass,
        "precision": precision_pass,
        "design": (null_pass if is_null else True),
        "null": is_null,
    }


def _check_representative_trials(
    trials: Any,
    planned_by_id: Mapping[str, Mapping[str, Any]],
    selection: Any,
    design: Mapping[str, Any],
    audit: _Audit,
) -> bool:
    values = _list(trials, "results.representative_trials", audit)
    selection_record = _mapping(selection, "protocol.representative_trial_selection", audit)
    if values is None or selection_record is None:
        return False
    required_roles = ["reject", "non_reject", "near_alpha_boundary"]
    roles_seen: list[str] = []
    all_pass = True
    selected_id = selection_record.get("scenario_id")
    selected_scenario = planned_by_id.get(selected_id) if isinstance(selected_id, str) else None
    audit.check(selected_scenario is not None, "protocol.representative_trial_selection.scenario_id", "must identify a governed scenario")
    selected_seed = selection_record.get("scenario_seed_binding")
    selection_seed = selection_record.get("selection_seed")
    search_replicates = selection_record.get("search_replicates")
    audit.check(
        selected_scenario is not None
        and _is_int(selected_seed)
        and selected_seed == selected_scenario.get("seed"),
        "protocol.representative_trial_selection.scenario_seed_binding",
        "must match the bound governed scenario seed",
    )
    audit.check(_is_int(selection_seed), "protocol.representative_trial_selection.selection_seed", "must be an integer")
    audit.check(_is_int(search_replicates) and search_replicates >= 1, "protocol.representative_trial_selection.search_replicates", "must be a positive integer")
    allocation = design.get("allocation") if isinstance(design.get("allocation"), Mapping) else {}
    for index, item in enumerate(values):
        path = f"results.representative_trials[{index}]"
        trial = _mapping(item, path, audit)
        if trial is None:
            all_pass = False
            continue
        role = trial.get("selection_role")
        roles_seen.append(role if isinstance(role, str) else "")
        audit.check(role in required_roles, f"{path}.selection_role", "must be reject, non_reject, or near_alpha_boundary")
        scenario_id = trial.get("scenario_id")
        scenario_seed = trial.get("scenario_seed")
        governed = planned_by_id.get(scenario_id) if isinstance(scenario_id, str) else None
        audit.check(governed is not None, f"{path}.scenario_id", "must identify a governed scenario")
        if governed is not None:
            audit.check(_is_int(scenario_seed) and scenario_seed == governed.get("seed"), f"{path}.scenario_seed", "must equal the bound governed scenario seed")
        audit.check(scenario_id == selected_id, f"{path}.scenario_id", "must match the frozen representative-trial selection scenario")
        audit.check(trial.get("selection_seed") == selection_seed, f"{path}.selection_seed", "must match the frozen independent selection seed")
        search_index = trial.get("search_index")
        audit.check(
            _is_int(search_index)
            and search_index >= 1
            and _is_int(search_replicates)
            and search_index <= search_replicates,
            f"{path}.search_index",
            "must be within the frozen representative-trial search",
        )
        if governed is not None:
            audit.check(trial.get("endpoint") == governed.get("endpoint"), f"{path}.endpoint", "must match the bound scenario")
        z_statistic = trial.get("z_statistic")
        p_value = trial.get("one_sided_p_value")
        valid = (
            _is_number(z_statistic)
            and math.isfinite(float(z_statistic))
            and _is_number(p_value)
            and 0.0 <= float(p_value) <= 1.0
        )
        if valid:
            recomputed_p = 0.5 * (1.0 + math.erf(float(z_statistic) / math.sqrt(2.0)))
            audit.check(_close(p_value, recomputed_p), f"{path}.one_sided_p_value", "must match the normal CDF of z_statistic")
            valid = valid and _close(p_value, recomputed_p)
        _check_exact_number(trial.get("alpha_one_sided"), NULL_ALPHA, f"{path}.alpha_one_sided", audit, "the governed alpha")
        if valid:
            expected_decision = "REJECT" if float(p_value) < NULL_ALPHA else "DO_NOT_REJECT"
            audit.check(trial.get("decision") == expected_decision, f"{path}.decision", "must agree with p-value < alpha")
            valid = valid and trial.get("decision") == expected_decision
            if role == "reject":
                audit.check(float(p_value) < NULL_ALPHA, path, "reject representative must have p < alpha")
                valid = valid and float(p_value) < NULL_ALPHA
            elif role == "non_reject":
                audit.check(float(p_value) >= 0.5, path, "non-reject representative must have p >= 0.5")
                valid = valid and float(p_value) >= 0.5
            elif role == "near_alpha_boundary":
                distance = abs(float(p_value) - NULL_ALPHA)
                _check_exact_number(trial.get("absolute_distance_from_alpha"), distance, f"{path}.absolute_distance_from_alpha", audit, "abs(p-alpha)")
                valid = valid and _close(trial.get("absolute_distance_from_alpha"), distance)
        events = _mapping(trial.get("events"), f"{path}.events", audit)
        censors = _mapping(trial.get("censors"), f"{path}.censors", audit)
        if events is not None and censors is not None:
            for arm in ("control", "experimental"):
                event_count = events.get(arm)
                censor_count = censors.get(arm)
                arm_size = allocation.get(arm)
                audit.check(_is_int(event_count) and event_count >= 0, f"{path}.events.{arm}", "must be a non-negative integer")
                audit.check(_is_int(censor_count) and censor_count >= 0, f"{path}.censors.{arm}", "must be a non-negative integer")
                audit.check(
                    _is_int(event_count)
                    and _is_int(censor_count)
                    and _is_int(arm_size)
                    and event_count + censor_count == arm_size,
                    f"{path}.{arm}",
                    "event and censor counts must partition the governed arm size",
                )
        audit.check(valid, path, f"does not satisfy the independent {role!r} representative-trial checks")
        all_pass = all_pass and valid
    audit.check(roles_seen == required_roles, "results.representative_trials", f"selection roles/order must equal {required_roles!r}")
    return all_pass and roles_seen == required_roles


def _check_edge_fixtures(value: Any, audit: _Audit) -> bool:
    fixtures = _list(value, "results.validation.logrank_edge_fixtures", audit)
    if fixtures is None:
        return False
    expected_roles = ["positive", "negative", "boundary_non_estimable"]
    observed_roles: list[Any] = []
    seeds: set[int] = set()
    all_pass = True
    for index, item in enumerate(fixtures):
        path = f"results.validation.logrank_edge_fixtures[{index}]"
        fixture = _mapping(item, path, audit)
        if fixture is None:
            all_pass = False
            continue
        role = fixture.get("role")
        observed_roles.append(role)
        seed = fixture.get("seed")
        audit.check(_is_int(seed) and seed not in seeds, f"{path}.seed", "must be a unique integer")
        if _is_int(seed):
            seeds.add(seed)
        status = fixture.get("analysis_status")
        reject = fixture.get("reject")
        z_statistic = fixture.get("z_statistic")
        p_value = fixture.get("one_sided_p_value")
        reason = fixture.get("failure_reason")
        if role == "positive":
            valid = status == "COMPLETED" and reject is True and _is_number(z_statistic) and float(z_statistic) < 0 and _is_number(p_value) and float(p_value) < NULL_ALPHA and reason is None
        elif role == "negative":
            valid = status == "COMPLETED" and reject is False and _is_number(z_statistic) and float(z_statistic) > 0 and _is_number(p_value) and float(p_value) >= NULL_ALPHA and reason is None
        elif role == "boundary_non_estimable":
            valid = status == "FAILED" and reject is None and z_statistic is None and p_value is None and reason == "zero_logrank_variance"
        else:
            valid = False
        if status == "COMPLETED" and _is_number(z_statistic) and _is_number(p_value):
            recomputed = 0.5 * (1.0 + math.erf(float(z_statistic) / math.sqrt(2.0)))
            audit.check(_close(p_value, recomputed), f"{path}.one_sided_p_value", "must match the normal CDF of z_statistic")
            valid = valid and _close(p_value, recomputed)
        audit.check(valid, path, f"does not satisfy independent {role!r} edge-fixture checks")
        audit.check(fixture.get("validation_status") == ("PASS" if valid else "FAIL"), f"{path}.validation_status", "must match the independent edge-fixture decision")
        all_pass = all_pass and valid
    audit.check(observed_roles == expected_roles, "results.validation.logrank_edge_fixtures", f"roles/order must equal {expected_roles!r}")
    return all_pass and observed_roles == expected_roles


def _display(value: Any) -> str:
    if value is None or value == "":
        return "Not reported"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        return "Not applicable" if not math.isfinite(value) else f"{value:.6g}"
    if isinstance(value, Mapping):
        if not value:
            return "Not reported"
        return "; ".join(f"{str(key).replace('_', ' ')}: {_display(item)}" for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return "; ".join(_display(item) for item in value) if value else "Not reported"
    return str(value)


def _pct(value: float | None) -> str:
    return "Not reported" if value is None else f"{100.0 * value:.3f}%"


def _split_markdown_row(line: str) -> list[str]:
    body = line.strip()[1:-1]
    cells = re.split(r"(?<!\\)\|", body)
    return [cell.strip().replace("\\|", "|").replace("<br>", "\n") for cell in cells]


def _table_after_heading(
    text: str, heading: str, audit: _Audit, *, level: int = 2
) -> list[list[str]] | None:
    marker = f"{'#' * level} {heading}"
    if marker not in text:
        audit.error("reviewer report", f"missing section {marker!r}")
        return None
    section = text.split(marker, 1)[1]
    lines = section.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line.startswith("| "))
    except StopIteration:
        audit.error("reviewer report", f"section {marker!r} has no Markdown table")
        return None
    table: list[list[str]] = []
    for line in lines[start:]:
        if not line.startswith("| "):
            break
        table.append(_split_markdown_row(line))
    return table


def _check_report(
    report_path: Path,
    results_path: Path,
    results: Mapping[str, Any],
    audit: _Audit,
) -> None:
    if not report_path.exists():
        audit.error(str(report_path), "required reviewer report is missing")
        return
    try:
        text = report_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        audit.error(str(report_path), f"cannot read reviewer report: {exc}")
        return
    lowered = text.lower()
    audit.check("not midd" in lowered, "reviewer report", "must retain the non-MIDD boundary")
    audit.check(
        re.search(r"not.{0,100}filing", lowered, flags=re.DOTALL) is not None,
        "reviewer report",
        "must retain the non-filing boundary",
    )
    try:
        result_file_hash = _sha256_file(results_path)
    except OSError as exc:
        audit.error(str(results_path), f"cannot hash authoritative result for report parity: {exc}")
    else:
        audit.check(result_file_hash in text, "reviewer report", "must report the authoritative result-file SHA-256")
    for path, value in (
        ("results.protocol.protocol_sha256", results.get("protocol", {}).get("protocol_sha256") if isinstance(results.get("protocol"), Mapping) else None),
        ("results.protocol.scenario_registry_sha256", results.get("protocol", {}).get("scenario_registry_sha256") if isinstance(results.get("protocol"), Mapping) else None),
        ("results.protocol.code_sha256", results.get("protocol", {}).get("code_sha256") if isinstance(results.get("protocol"), Mapping) else None),
        ("results.scientific_output_sha256", results.get("scientific_output_sha256")),
    ):
        audit.check(isinstance(value, str) and value in text, "reviewer report", f"must contain {path}")
    scenarios = results.get("scenarios")
    if not isinstance(scenarios, list):
        return
    accounting = _table_after_heading(text, "Exact Execution and Failure Accounting", audit)
    execution_status = _table_after_heading(text, "Execution Status Rationale", audit, level=3)
    operating = _table_after_heading(text, "Operating Characteristics and Monte Carlo Precision", audit)
    decisions = _table_after_heading(text, "Precision and Design Decisions", audit, level=3)
    software = _table_after_heading(text, "Observed Execution Environment", audit, level=3)
    seeds = _table_after_heading(text, "Scenario Seed Ledger", audit, level=3)
    if software is not None and len(software) >= 2:
        identity = results.get("software_identity")
        if not isinstance(identity, Mapping):
            audit.error("results.software_identity", "must be an object for reviewer-report parity")
        else:
            python = identity.get("python") if isinstance(identity.get("python"), Mapping) else {}
            expected_software = [
                ["Python", _display(python.get("version"))],
                ["NumPy", _display(identity.get("numpy_version"))],
                ["PyYAML", _display(identity.get("pyyaml_version"))],
                ["Floating-point dtype", _display(identity.get("floating_point_dtype"))],
                ["Random-number generator", _display(identity.get("random_number_generator"))],
                ["Dependency lock", _display(identity.get("dependency_lock"))],
            ]
            audit.check(
                software[2:] == expected_software,
                "reviewer report software table",
                "does not exactly match authoritative JSON",
            )
    if accounting is not None and len(accounting) >= 2:
        rows = accounting[2:]
        audit.check(len(rows) == len(scenarios), "reviewer report execution table", "must contain exactly one row per governed scenario")
        for index, (item, row) in enumerate(zip(scenarios, rows)):
            failures = item.get("failures")
            if not failures and item.get("failed") == 0:
                failures = "Not applicable"
            expected = [
                str(item.get("id")),
                str(item.get("requested")),
                str(item.get("completed")),
                str(item.get("failed")),
                _pct(item.get("failed") / item.get("requested") if item.get("requested") else None),
                _display(failures),
            ]
            audit.check(row == expected, f"reviewer report execution row {index + 1}", "does not match authoritative JSON")
    if execution_status is not None and len(execution_status) >= 2:
        rows = execution_status[2:]
        audit.check(len(rows) == len(scenarios), "reviewer report execution-status table", "must contain exactly one row per governed scenario")
        for index, (item, row) in enumerate(zip(scenarios, rows)):
            execution = item.get("statuses", {}).get("execution", {})
            expected = [
                str(item.get("id")),
                _display(execution.get("status")),
                _display(execution.get("reason")),
            ]
            audit.check(row == expected, f"reviewer report execution-status row {index + 1}", "does not match authoritative JSON")
    if operating is not None and len(operating) >= 2:
        rows = operating[2:]
        audit.check(len(rows) == len(scenarios), "reviewer report operating-characteristics table", "must contain exactly one row per governed scenario")
        for index, (item, row) in enumerate(zip(scenarios, rows)):
            rejection = item.get("rejection", {})
            interval = rejection.get("wilson_95", {})
            statuses = item.get("statuses", {})
            expected = [
                str(item.get("id")),
                str(item.get("class")),
                f"{rejection.get('numerator')} / {rejection.get('denominator')}",
                _pct(rejection.get("estimate")),
                _display(rejection.get("mcse")),
                f"{_pct(interval.get('lower'))} to {_pct(interval.get('upper'))}",
            ]
            audit.check(row == expected, f"reviewer report operating-characteristics row {index + 1}", "does not match authoritative JSON")
    if decisions is not None and len(decisions) >= 2:
        rows = decisions[2:]
        audit.check(len(rows) == len(scenarios), "reviewer report decision table", "must contain exactly one row per governed scenario")
        for index, (item, row) in enumerate(zip(scenarios, rows)):
            statuses = item.get("statuses", {})
            expected = [
                str(item.get("id")),
                _display(statuses.get("precision", {}).get("status")),
                _display(statuses.get("precision", {}).get("reason")),
                _display(statuses.get("design_operating_characteristic", {}).get("status")),
                _display(statuses.get("design_operating_characteristic", {}).get("reason")),
            ]
            audit.check(row == expected, f"reviewer report decision row {index + 1}", "does not match authoritative JSON")
    if seeds is not None and len(seeds) >= 2:
        rows = seeds[2:]
        audit.check(len(rows) == len(scenarios), "reviewer report seed table", "must contain exactly one row per governed scenario")
        for index, (item, row) in enumerate(zip(scenarios, rows)):
            expected = [str(item.get("id")), str(item.get("seed")), str(item.get("scenario_sha256"))]
            audit.check(row == expected, f"reviewer report seed row {index + 1}", "does not match authoritative JSON")


def _check_csv(csv_path: Path, results: Mapping[str, Any], audit: _Audit) -> None:
    if not csv_path.exists():
        audit.error(str(csv_path), "required flat scenario sidecar is missing")
        return
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            fields = reader.fieldnames
    except (OSError, UnicodeError, csv.Error) as exc:
        audit.error(str(csv_path), f"cannot read CSV sidecar: {exc}")
        return
    columns = [
        "id", "endpoint", "class", "family", "assumption_basis", "seed",
        "requested", "completed", "failed", "failure_rate", "rejections",
        "estimate", "mcse", "wilson_95_lower", "wilson_95_upper",
        "control_event_proportion", "experimental_event_proportion",
        "control_censor_proportion", "experimental_censor_proportion",
        "execution_status", "precision_status", "design_status", "scenario_sha256",
    ]
    audit.check(fields == columns, str(csv_path), "header does not match the governed flat schema")
    scenarios = results.get("scenarios")
    if not isinstance(scenarios, list):
        return
    audit.check(len(rows) == len(scenarios), str(csv_path), "must contain exactly one row per JSON scenario")

    def cell(value: Any) -> str:
        return "" if value is None else str(value)

    for index, (item, row) in enumerate(zip(scenarios, rows)):
        rejection = item.get("rejection") or {}
        interval = rejection.get("wilson_95") or {}
        expected = {
            "id": item.get("id"),
            "endpoint": item.get("endpoint"),
            "class": item.get("class"),
            "family": item.get("family"),
            "assumption_basis": item.get("assumption_basis"),
            "seed": item.get("seed"),
            "requested": item.get("requested"),
            "completed": item.get("completed"),
            "failed": item.get("failed"),
            "failure_rate": item.get("failure_rate"),
            "rejections": rejection.get("numerator"),
            "estimate": rejection.get("estimate"),
            "mcse": rejection.get("mcse"),
            "wilson_95_lower": interval.get("lower"),
            "wilson_95_upper": interval.get("upper"),
            "control_event_proportion": item.get("events", {}).get("control", {}).get("mean_proportion"),
            "experimental_event_proportion": item.get("events", {}).get("experimental", {}).get("mean_proportion"),
            "control_censor_proportion": item.get("censoring", {}).get("control", {}).get("mean_proportion"),
            "experimental_censor_proportion": item.get("censoring", {}).get("experimental", {}).get("mean_proportion"),
            "execution_status": item.get("statuses", {}).get("execution", {}).get("status"),
            "precision_status": item.get("statuses", {}).get("precision", {}).get("status"),
            "design_status": item.get("statuses", {}).get("design_operating_characteristic", {}).get("status"),
            "scenario_sha256": item.get("scenario_sha256"),
        }
        mismatches = [key for key in columns if row.get(key) != cell(expected[key])]
        audit.check(not mismatches, f"{csv_path} row {index + 2}", f"differs from JSON in column(s): {', '.join(mismatches)}")


def _check_trial_sidecar(
    path: Path, results: Mapping[str, Any], audit: _Audit
) -> None:
    if not path.exists():
        audit.error(str(path), "required representative-trial sidecar is missing")
        return
    try:
        sidecar = _load_json(path)
    except EvidenceVerificationError as exc:
        audit.errors.extend(exc.errors)
        return
    audit.check(sidecar == results.get("representative_trials"), str(path), "does not exactly match results.representative_trials")


def verify_evidence(
    protocol_path: str | Path = DEFAULT_PROTOCOL,
    results_path: str | Path = DEFAULT_RESULTS,
    code_path: str | Path = DEFAULT_CODE,
    csv_path: str | Path | None = DEFAULT_CSV,
    trials_path: str | Path | None = DEFAULT_TRIALS,
    report_path: str | Path | None = DEFAULT_REPORT,
) -> None:
    """Verify the full bundle or raise :class:`EvidenceVerificationError`."""
    protocol_file = Path(protocol_path)
    results_file = Path(results_path)
    code_file = Path(code_path)
    protocol = _load_yaml(protocol_file)
    results = _load_json(results_file)
    audit = _Audit()
    protocol_map = _mapping(protocol, "protocol", audit)
    results_map = _mapping(results, "results", audit)
    if protocol_map is None or results_map is None:
        audit.finish()
        return
    _walk_finite(protocol_map, "protocol", audit)
    _walk_finite(results_map, "results", audit)
    _check_protocol_controls(protocol_map, audit)
    audit.check(results_map.get("schema_version") == "1.0.0", "results.schema_version", "must equal 1.0.0")
    _check_hashes(protocol_map, results_map, protocol_file, code_file, audit)

    result_protocol = _mapping(results_map.get("protocol"), "results.protocol", audit)
    protocol_info = _mapping(protocol_map.get("protocol"), "protocol.protocol", audit)
    if result_protocol is not None and protocol_info is not None:
        for key in ("id", "version", "status"):
            audit.check(result_protocol.get(key) == protocol_info.get(key), f"results.protocol.{key}", "must match governed protocol")
    duplicated = {
        "change_control": protocol_map.get("change_control"),
        "qualification_boundary": protocol_info.get("qualification_boundary") if protocol_info is not None else None,
        "m15_assessment": protocol_map.get("m15_assessment"),
        "estimand": protocol_map.get("estimand"),
        "protocol_framework": protocol_map.get("protocol_framework"),
        "design": protocol_map.get("design"),
        "acceptance_criteria": protocol_map.get("acceptance_criteria"),
        "representative_trial_selection": protocol_map.get("representative_trial_selection"),
    }
    for key, expected in duplicated.items():
        audit.check(results_map.get(key) == expected, f"results.{key}", "must exactly match the governed protocol")

    planned_values = _list(protocol_map.get("scenarios"), "protocol.scenarios", audit)
    result_values = _list(results_map.get("scenarios"), "results.scenarios", audit)
    planned: list[Mapping[str, Any]] = []
    observed: list[Mapping[str, Any]] = []
    if planned_values is not None:
        for index, item in enumerate(planned_values):
            value = _mapping(item, f"protocol.scenarios[{index}]", audit)
            if value is not None:
                planned.append(value)
    if result_values is not None:
        for index, item in enumerate(result_values):
            value = _mapping(item, f"results.scenarios[{index}]", audit)
            if value is not None:
                observed.append(value)
    planned_ids = [item.get("id") for item in planned]
    observed_ids = [item.get("id") for item in observed]
    audit.check(all(isinstance(item, str) and item for item in planned_ids), "protocol.scenarios", "every scenario id must be non-empty text")
    audit.check(len(planned_ids) == len(set(planned_ids)), "protocol.scenarios", "scenario ids must be unique")
    audit.check(
        planned_ids == list(GOVERNED_SCENARIO_IDS),
        "protocol.scenarios",
        f"ids/order must equal the frozen governed registry {list(GOVERNED_SCENARIO_IDS)!r}",
    )
    audit.check(observed_ids == planned_ids, "results.scenarios", f"scenario ids/order must exactly equal governed order {planned_ids!r}")
    planned_seeds = [item.get("seed") for item in planned]
    audit.check(all(_is_int(seed) for seed in planned_seeds), "protocol.scenarios", "every seed must be an integer (booleans prohibited)")
    audit.check(len(planned_seeds) == len(set(planned_seeds)), "protocol.scenarios", "scenario seeds must be unique")
    observed_seeds = [item.get("seed") for item in observed]
    audit.check(all(_is_int(seed) for seed in observed_seeds), "results.scenarios", "every seed must be an integer (booleans prohibited)")
    audit.check(len(observed_seeds) == len(set(observed_seeds)), "results.scenarios", "scenario seeds must be unique")

    scenario_checks: list[dict[str, bool]] = []
    design = protocol_map.get("design") if isinstance(protocol_map.get("design"), Mapping) else {}
    if len(planned) == len(observed) and observed_ids == planned_ids:
        for index, (planned_item, observed_item) in enumerate(zip(planned, observed)):
            scenario_checks.append(_check_scenario(planned_item, observed_item, index, design, audit))

    planned_by_id = {
        str(item.get("id")): item for item in planned if isinstance(item.get("id"), str)
    }
    trials_pass = _check_representative_trials(
        results_map.get("representative_trials"),
        planned_by_id,
        protocol_map.get("representative_trial_selection"),
        design,
        audit,
    )
    validation = _mapping(results_map.get("validation"), "results.validation", audit)
    edge_fixtures_pass = False
    if validation is not None:
        null_ids = [str(item.get("id")) for item in planned if str(item.get("class", "")).startswith("KEY_NULL")]
        analytic = _mapping(validation.get("analytic_null_benchmark"), "results.validation.analytic_null_benchmark", audit)
        if analytic is not None:
            null_pass = bool(scenario_checks) and all(item["design"] for item in scenario_checks if item["null"])
            audit.check(analytic.get("status") == ("PASS" if null_pass else "FAIL"), "results.validation.analytic_null_benchmark.status", "must match independent null checks")
            audit.check(analytic.get("scenario_ids") == null_ids, "results.validation.analytic_null_benchmark.scenario_ids", "must list governed null scenarios in order")
        representative = _mapping(validation.get("representative_trial_selection"), "results.validation.representative_trial_selection", audit)
        if representative is not None:
            audit.check(representative.get("status") == ("PASS" if trials_pass else "FAIL"), "results.validation.representative_trial_selection.status", "must match independent representative checks")
            expected_roles = ["reject", "non_reject", "near_alpha_boundary"]
            audit.check(representative.get("roles_found") == expected_roles, "results.validation.representative_trial_selection.roles_found", "must list the governed roles in order")
        edge_fixtures_pass = _check_edge_fixtures(validation.get("logrank_edge_fixtures"), audit)
        edge_status = _mapping(validation.get("logrank_edge_fixture_status"), "results.validation.logrank_edge_fixture_status", audit)
        if edge_status is not None:
            audit.check(edge_status.get("status") == ("PASS" if edge_fixtures_pass else "FAIL"), "results.validation.logrank_edge_fixture_status.status", "must match independent edge-fixture checks")
        accounting = _mapping(validation.get("accounting_identity"), "results.validation.accounting_identity", audit)
        if accounting is not None:
            accounting_pass = bool(scenario_checks) and all(
                item.get("requested") == item.get("completed") + item.get("failed")
                for item in observed
                if _is_int(item.get("requested")) and _is_int(item.get("completed")) and _is_int(item.get("failed"))
            )
            audit.check(accounting.get("status") == ("PASS" if accounting_pass else "FAIL"), "results.validation.accounting_identity.status", "must match independent accounting checks")

    top_statuses = _mapping(results_map.get("statuses"), "results.statuses", audit)
    if top_statuses is not None:
        execution = _status(top_statuses, "execution", "results.statuses", audit)
        precision = _status(top_statuses, "monte_carlo_precision", "results.statuses", audit)
        design_status = _status(top_statuses, "design_operating_characteristics", "results.statuses", audit)
        qualification = _status(top_statuses, "evidence_qualification", "results.statuses", audit)
        execution_pass = bool(scenario_checks) and all(item["execution"] for item in scenario_checks)
        precision_pass = bool(scenario_checks) and all(item["precision"] for item in scenario_checks)
        design_pass = (
            bool(scenario_checks)
            and all(item["design"] for item in scenario_checks)
            and trials_pass
            and edge_fixtures_pass
        )
        audit.check(execution == ("PASS" if execution_pass else "FAIL"), "results.statuses.execution.status", "must aggregate scenario execution decisions")
        audit.check(precision == ("PASS" if precision_pass else "FAIL"), "results.statuses.monte_carlo_precision.status", "must aggregate scenario precision decisions")
        audit.check(design_status == ("PASS" if design_pass else "FAIL"), "results.statuses.design_operating_characteristics.status", "must aggregate null and representative-trial decisions")
        audit.check(qualification == "NOT_QUALIFIED", "results.statuses.evidence_qualification.status", "must remain NOT_QUALIFIED")
        evidence_reason = top_statuses.get("evidence_qualification", {}).get("reason") if isinstance(top_statuses.get("evidence_qualification"), Mapping) else ""
        lowered = evidence_reason.lower() if isinstance(evidence_reason, str) else ""
        audit.check("non-midd" in lowered and "non-confirmatory" in lowered and "informational" in lowered, "results.statuses.evidence_qualification.reason", "must retain informational, non-MIDD, non-confirmatory limits")

    if csv_path is not None:
        _check_csv(Path(csv_path), results_map, audit)
    if trials_path is not None:
        _check_trial_sidecar(Path(trials_path), results_map, audit)
    if report_path is not None:
        _check_report(Path(report_path), results_file, results_map, audit)
    audit.finish()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--code", type=Path, default=DEFAULT_CODE)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--trials", type=Path, default=DEFAULT_TRIALS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--skip-sidecars", action="store_true", help="validate the primary JSON only")
    parser.add_argument("--skip-report", action="store_true", help="do not validate reviewer-report parity")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        verify_evidence(
            protocol_path=args.protocol,
            results_path=args.results,
            code_path=args.code,
            csv_path=None if args.skip_sidecars else args.csv,
            trials_path=None if args.skip_sidecars else args.trials,
            report_path=None if args.skip_report else args.report,
        )
    except EvidenceVerificationError as exc:
        for error in exc.errors:
            print(f"SIMULATION_EVIDENCE_ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
