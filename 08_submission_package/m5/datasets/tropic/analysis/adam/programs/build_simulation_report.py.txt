#!/usr/bin/env python3
"""Build deterministic reviewer-facing simulation plan and result reports.

The governed protocol YAML and authoritative scientific JSON are the only data
inputs.  Result values are never copied into this program or transcribed into a
separate template.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

try:
    import yaml
except ImportError:  # pragma: no cover - exercised through the explicit error path
    yaml = None


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / "config/simulation_protocol.yaml"
DEFAULT_RESULTS = (
    ROOT / "platform/simulation_operating_characteristics/simulation_oc_status.json"
)
DEFAULT_PLAN = ROOT / "07_reviewer_explanation/simulation_model_analysis_plan.md"
DEFAULT_REPORT = ROOT / "07_reviewer_explanation/simulation_report.md"
NOT_REPORTED = "Not reported"
NOT_APPLICABLE = "Not applicable"
RELEASE_IDENTITY = (
    "**Current sealed controlled release:** `v0.3.0-clinical-simulation` · "
    "[`docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md`]"
    "(../docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md)"
)
REFERENCE_LINES = (
    "- [TROPIC simulation-precision research basis](../docs/SIMULATION_PRECISION_RESEARCH.md)",
    "- [ICH M15: General Principles for Model-Informed Drug Development](https://database.ich.org/sites/default/files/ICH_M15_Step4_Final_Guideline_2026_0129.pdf)",
    "- [ICH E9(R1): Estimands and Sensitivity Analysis](https://database.ich.org/sites/default/files/E9-R1_Step4_Guideline_2019_1203.pdf)",
    "- [FDA: Adaptive Designs for Clinical Trials of Drugs and Biologics](https://www.fda.gov/media/78495/download)",
    "- [FDA: Complex Innovative Trial Design Meeting Program](https://www.fda.gov/drugs/development-resources/complex-innovative-trial-design-meeting-program)",
    "- [ADEMP framework](https://doi.org/10.1002/sim.8086)",
    "- [OCTAVE framework](https://doi.org/10.1002/sim.70449)",
)


def _load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to build the simulation reports")
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} did not parse to a YAML mapping")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} did not parse to a JSON object")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pick(mapping: Mapping[str, Any] | None, *keys: str, default: Any = None) -> Any:
    if not isinstance(mapping, Mapping):
        return default
    for key in keys:
        if key in mapping:
            return mapping[key]
    return default


def _md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def _display(value: Any, *, missing: str = NOT_REPORTED) -> str:
    """Return a compact, unambiguous Markdown table value."""
    if value is None or value == "":
        return missing
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        if not math.isfinite(value):
            return NOT_APPLICABLE
        return f"{value:.6g}"
    if isinstance(value, Mapping):
        if not value:
            return missing
        return "; ".join(
            f"{str(key).replace('_', ' ')}: {_display(item)}"
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        if not value:
            return missing
        return "; ".join(_display(item) for item in value)
    return str(value)


def _deviations(change_control: Any) -> Any:
    if not isinstance(change_control, Mapping):
        return NOT_REPORTED
    deviations = _pick(change_control, "deviations")
    return "None" if deviations == [] else deviations


def _pct(value: Any) -> str:
    if value is None:
        return NOT_REPORTED
    try:
        number = float(value)
    except (TypeError, ValueError):
        return _display(value)
    if not math.isfinite(number):
        return NOT_APPLICABLE
    return f"{100 * number:.3f}%"


def _table(headers: Iterable[str], rows: Iterable[Iterable[Any]]) -> str:
    header_list = list(headers)
    lines = [
        "| " + " | ".join(_md_escape(item) for item in header_list) + " |",
        "| " + " | ".join("---" for _ in header_list) + " |",
    ]
    for row in rows:
        cells = [_display(item) for item in row]
        if len(cells) != len(header_list):
            raise RuntimeError("Markdown table row does not match its header width")
        lines.append("| " + " | ".join(_md_escape(item) for item in cells) + " |")
    return "\n".join(lines)


def _bullets(items: Any, *, fallback: str = NOT_REPORTED) -> list[str]:
    if isinstance(items, Mapping):
        values = [f"**{str(key).replace('_', ' ').title()}:** {_display(value)}" for key, value in items.items()]
    elif isinstance(items, list):
        values = [_display(item) for item in items]
    elif items not in (None, ""):
        values = [_display(items)]
    else:
        values = [fallback]
    return [f"- {value}" for value in values]


def _status_value(statuses: Mapping[str, Any], name: str) -> Any:
    value = _pick(statuses, name, f"{name}_status")
    if isinstance(value, Mapping):
        return _pick(value, "status", "value", default=value)
    return value


def _status_reason(statuses: Mapping[str, Any], name: str) -> Any:
    value = _pick(statuses, name, f"{name}_status")
    return _pick(value, "reason") if isinstance(value, Mapping) else NOT_REPORTED


def _scenario_id(item: Mapping[str, Any]) -> str:
    return str(_pick(item, "scenario_id", "id", "name", default=NOT_REPORTED))


def _scenario_registry(protocol: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = _pick(protocol, "scenarios", "scenario_registry", default=[])
    if isinstance(raw, Mapping):
        return [dict(value, scenario_id=key) if isinstance(value, Mapping) else {"scenario_id": key, "description": value} for key, value in raw.items()]
    if isinstance(raw, list):
        return [dict(value) for value in raw if isinstance(value, Mapping)]
    return []


def _result_scenarios(results: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = _pick(results, "scenarios", default=[])
    if not isinstance(raw, list):
        raise RuntimeError("authoritative results `scenarios` must be a list")
    scenarios = [dict(item) for item in raw if isinstance(item, Mapping)]
    if len(scenarios) != len(raw):
        raise RuntimeError("every authoritative result scenario must be an object")
    return scenarios


def _scenario_design(item: Mapping[str, Any]) -> str:
    fields = []
    for key in (
        "treatment_hr_segments",
        "withdrawal_rate_12m",
        "discontinuation_rate_12m",
        "post_discontinuation_hazard_ratio",
    ):
        if key in item:
            fields.append(f"{key.replace('_', ' ')}={_display(item[key])}")
    assumptions = _pick(item, "assumptions", "parameters")
    if assumptions is not None:
        fields.append(_display(assumptions))
    return "; ".join(fields) if fields else NOT_REPORTED


def _assessment_rows(assessment: Mapping[str, Any]) -> list[list[Any]]:
    preferred = (
        ("Question of interest", ("question_of_interest", "question")),
        ("Context of use", ("context_of_use",)),
        ("Model influence", ("model_influence",)),
        ("Consequence of a wrong decision", ("consequence_of_wrong_decision", "wrong_decision_consequence")),
        ("Model risk", ("model_risk", "risk")),
        ("Model impact", ("model_impact", "impact")),
    )
    return [[label, _pick(assessment, *keys)] for label, keys in preferred]


def _estimand_rows(estimand: Mapping[str, Any]) -> list[list[Any]]:
    preferred = (
        ("Population", ("population",)),
        ("Treatment conditions", ("treatment_conditions", "treatments")),
        ("Variables / endpoints", ("variables", "variable", "endpoint")),
        ("Population-level summary", ("population_summary", "summary_measure", "summary")),
    )
    return [[label, _pick(estimand, *keys)] for label, keys in preferred]


def _ice_rows(estimand: Mapping[str, Any]) -> list[list[Any]]:
    raw = _pick(estimand, "intercurrent_events", "ices", default=[])
    rows: list[list[Any]] = []
    if isinstance(raw, Mapping):
        raw = [dict(value, event=key) if isinstance(value, Mapping) else {"event": key, "strategy": value} for key, value in raw.items()]
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, Mapping):
                rows.append([
                    _pick(item, "event", "name", "intercurrent_event"),
                    _pick(
                        item,
                        "strategy",
                        "handling_strategy",
                        default={
                            key.replace("strategy_", ""): value
                            for key, value in item.items()
                            if key.startswith("strategy_")
                        },
                    ),
                    _pick(item, "handling", "implementation", "data_handling", "rationale"),
                ])
    return rows or [[NOT_REPORTED, NOT_REPORTED, NOT_REPORTED]]


def _missingness_rows(estimand: Mapping[str, Any]) -> list[list[Any]]:
    raw = _pick(estimand, "missing_data_and_censoring", default={})
    rows: list[list[Any]] = []
    if isinstance(raw, Mapping):
        for name, item in raw.items():
            if isinstance(item, Mapping):
                rows.append([
                    name.replace("_", " ").title(),
                    _pick(item, "classification", default="Censoring"),
                    _pick(item, "handling"),
                ])
            else:
                rows.append([name.replace("_", " ").title(), "Censoring", item])
    return rows or [[NOT_REPORTED, NOT_REPORTED, NOT_REPORTED]]


def _criteria_rows(criteria: Mapping[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for name, value in criteria.items():
        if isinstance(value, Mapping):
            criterion = _pick(value, "criterion", "threshold", "rule", default=value)
            scope = _pick(value, "scope", "applies_to", default="All applicable scenarios")
        else:
            criterion = value if value is not None else "Not applicable — no exception specified"
            scope = "All applicable scenarios"
        rows.append([name.replace("_", " ").title(), criterion, scope])
    return rows or [[NOT_REPORTED, NOT_REPORTED, NOT_REPORTED]]


def _software_rows(identity: Any) -> list[list[Any]]:
    if not isinstance(identity, Mapping):
        return [[NOT_REPORTED, NOT_REPORTED]]
    python = _pick(identity, "python", default={})
    return [
        ["Python", _pick(python, "version")],
        ["NumPy", _pick(identity, "numpy_version")],
        ["PyYAML", _pick(identity, "pyyaml_version")],
        ["Floating-point dtype", _pick(identity, "floating_point_dtype")],
        ["Random-number generator", _pick(identity, "random_number_generator")],
        ["Dependency lock", _pick(identity, "dependency_lock")],
    ]


def _wilson_interval(numerator: int, denominator: int) -> tuple[float, float]:
    if denominator <= 0:
        raise RuntimeError("Wilson interval requires a positive denominator")
    z = 1.959963984540054
    estimate = numerator / denominator
    denominator_term = 1.0 + z * z / denominator
    center = (estimate + z * z / (2.0 * denominator)) / denominator_term
    half_width = (
        z
        * math.sqrt(
            estimate * (1.0 - estimate) / denominator
            + z * z / (4.0 * denominator * denominator)
        )
        / denominator_term
    )
    return center - half_width, center + half_width


def _representative_rows(items: Any) -> list[list[Any]]:
    if not isinstance(items, list) or not items:
        return [[NOT_REPORTED] * 9]
    rows = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        events = _pick(item, "events", default={})
        censors = _pick(item, "censors", default={})
        distance = _pick(item, "absolute_distance_from_alpha")
        selection_evidence = (
            f"absolute distance from alpha={_display(distance)}"
            if distance is not None
            else "First eligible trial in governed search order"
        )
        rows.append([
            _pick(item, "selection_role"),
            _pick(item, "scenario_id"),
            _pick(item, "search_index"),
            f"scenario={_pick(item, 'scenario_seed')}; selection={_pick(item, 'selection_seed')}",
            f"control={_pick(events, 'control')}; experimental={_pick(events, 'experimental')}",
            f"control={_pick(censors, 'control')}; experimental={_pick(censors, 'experimental')}",
            _pick(item, "z_statistic"),
            _pick(item, "one_sided_p_value"),
            f"{_pick(item, 'decision')} — {selection_evidence}",
        ])
    return rows or [[NOT_REPORTED] * 9]


def _fixture_rows(items: Any) -> list[list[Any]]:
    if not isinstance(items, list) or not items:
        return [[NOT_REPORTED] * 11]
    rows = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        estimable = _pick(item, "analysis_status") == "COMPLETED"
        rows.append([
            _pick(item, "id"),
            _pick(item, "role"),
            _pick(item, "seed"),
            _pick(item, "analysis_status"),
            _pick(item, "failure_reason", default=NOT_APPLICABLE) or NOT_APPLICABLE,
            _pick(item, "z_statistic", default="Not applicable — non-estimable") if estimable else "Not applicable — non-estimable",
            _pick(item, "one_sided_p_value", default="Not applicable — non-estimable") if estimable else "Not applicable — non-estimable",
            _pick(item, "reject", default="Not applicable — non-estimable") if estimable else "Not applicable — non-estimable",
            _pick(item, "events"),
            _pick(item, "expected"),
            _pick(item, "validation_status"),
        ])
    return rows or [[NOT_REPORTED] * 11]


def validate_inputs(protocol: Mapping[str, Any], results: Mapping[str, Any], protocol_path: Path) -> None:
    protocol_scenarios = _scenario_registry(protocol)
    protocol_ids = [_scenario_id(item) for item in protocol_scenarios]
    result_scenarios = _result_scenarios(results)
    result_ids = [_scenario_id(item) for item in result_scenarios]
    if not protocol_ids:
        raise RuntimeError("governed protocol contains no scenarios")
    if len(protocol_ids) != len(set(protocol_ids)):
        raise RuntimeError("governed protocol scenario identifiers are not unique")
    if len(result_ids) != len(set(result_ids)):
        raise RuntimeError("authoritative result scenario identifiers are not unique")
    if set(protocol_ids) != set(result_ids):
        missing = sorted(set(protocol_ids) - set(result_ids))
        extra = sorted(set(result_ids) - set(protocol_ids))
        raise RuntimeError(f"protocol/result scenario mismatch; missing={missing}, extra={extra}")

    result_protocol = _pick(results, "protocol", default={})
    expected_protocol_hash = _pick(result_protocol, "protocol_sha256")
    actual_protocol_hash = _sha256(protocol_path)
    if expected_protocol_hash and expected_protocol_hash != actual_protocol_hash:
        raise RuntimeError("authoritative results do not match the governed protocol SHA-256")

    protocol_by_id = {_scenario_id(item): item for item in protocol_scenarios}
    for item in result_scenarios:
        scenario_id = _scenario_id(item)
        planned = protocol_by_id[scenario_id]
        requested = _pick(item, "requested", "requested_replicates")
        completed = _pick(item, "completed", "completed_replicates")
        failed = _pick(item, "failed", "failed_replicates")
        if not all(isinstance(value, int) and not isinstance(value, bool) for value in (requested, completed, failed)):
            raise RuntimeError(f"{scenario_id}: requested/completed/failed must be integers")
        if requested != completed + failed:
            raise RuntimeError(f"{scenario_id}: requested != completed + failed")
        if requested != _pick(planned, "replicates"):
            raise RuntimeError(f"{scenario_id}: requested replicates do not match the protocol")
        if _pick(item, "seed") != _pick(planned, "seed"):
            raise RuntimeError(f"{scenario_id}: seed does not match the protocol")

        rejection = _pick(item, "rejection", "operating_characteristic", default={})
        if not isinstance(rejection, Mapping):
            raise RuntimeError(f"{scenario_id}: rejection result must be an object")
        numerator = _pick(rejection, "numerator")
        denominator = _pick(rejection, "denominator")
        if numerator is not None or denominator is not None:
            if denominator != completed:
                raise RuntimeError(f"{scenario_id}: rejection denominator must equal completed replicates")
            if not isinstance(numerator, int) or numerator < 0 or numerator > denominator:
                raise RuntimeError(f"{scenario_id}: invalid rejection numerator")
            estimate = _pick(rejection, "estimate")
            mcse = _pick(rejection, "mcse")
            wilson = _pick(rejection, "wilson_95", "wilson_95_interval")
            expected_estimate = numerator / denominator
            expected_mcse = math.sqrt(expected_estimate * (1.0 - expected_estimate) / denominator)
            expected_wilson = _wilson_interval(numerator, denominator)
            if not isinstance(estimate, (int, float)) or not math.isclose(
                estimate, expected_estimate, rel_tol=0.0, abs_tol=5e-12
            ):
                raise RuntimeError(f"{scenario_id}: rejection estimate does not equal numerator / denominator")
            if not isinstance(mcse, (int, float)) or not math.isclose(
                mcse, expected_mcse, rel_tol=0.0, abs_tol=5e-12
            ):
                raise RuntimeError(f"{scenario_id}: MCSE does not match the binomial formula")
            if not isinstance(wilson, Mapping) or any(
                not isinstance(actual, (int, float))
                or not math.isclose(actual, expected, rel_tol=0.0, abs_tol=5e-12)
                for actual, expected in zip(
                    (_pick(wilson, "lower"), _pick(wilson, "upper")), expected_wilson
                )
            ):
                raise RuntimeError(f"{scenario_id}: Wilson 95% interval does not recompute")


def build_analysis_plan(
    protocol: Mapping[str, Any],
    results: Mapping[str, Any],
    protocol_sha256: str,
    results_sha256: str,
) -> str:
    protocol_info = _pick(protocol, "protocol", "document", default={})
    assessment = dict(_pick(protocol, "m15_assessment", "assessment", default={}))
    assessment["question_of_interest"] = _pick(
        protocol_info, "question_of_interest", default=_pick(assessment, "question_of_interest")
    )
    assessment["context_of_use"] = _pick(
        protocol_info, "context_of_use", default=_pick(assessment, "context_of_use")
    )
    assessment["model_influence"] = _pick(
        _pick(protocol_info, "qualification_boundary", default={}),
        "model_influence",
        default=_pick(assessment, "model_influence"),
    )
    estimand = _pick(protocol, "estimand", default={})
    framework = _pick(protocol, "protocol_framework", default={})
    ademp = _pick(framework, "ADEMP", default={})
    octave = _pick(framework, "OCTAVE", default={})
    design = _pick(protocol, "design", default={})
    criteria = _pick(protocol, "acceptance_criteria", default={})
    change_control = _pick(protocol, "change_control", default={})
    scenarios = _scenario_registry(protocol)
    result_by_id = {_scenario_id(item): item for item in _result_scenarios(results)}
    result_protocol = _pick(results, "protocol", default={})
    qualification = _pick(
        protocol_info,
        "qualification_boundary",
        default=_pick(results, "qualification_boundary"),
    )

    scenario_rows = []
    for scenario in scenarios:
        scenario_id = _scenario_id(scenario)
        result = result_by_id[scenario_id]
        scenario_rows.append([
            scenario_id,
            _pick(scenario, "class", "type", "scenario_type", "classification"),
            _pick(scenario, "endpoint"),
            _pick(scenario, "assumption_basis", "rationale"),
            _scenario_design(scenario),
            _pick(scenario, "replicates", "requested", default=_pick(result, "requested", "requested_replicates")),
            _pick(scenario, "seed", default=_pick(result, "seed")),
        ])

    lines = [
        "# TROPIC Simulation Model Analysis Plan",
        "",
        RELEASE_IDENTITY,
        "",
        "> **Informative annex boundary.** This plan is a data-free simulation-science "
        "methods evaluation layered on the historical sealed clinical-simulation release. "
        "It is not MIDD evidence, a filing artifact, confirmatory efficacy evidence, sponsor "
        "approval, or evidence of regulator acceptance.",
        "",
        "## Document Control",
        "",
        _table(
            ["Item", "Governed value"],
            [
                ["Protocol identifier", _pick(protocol_info, "id", "protocol_id", default=_pick(protocol, "protocol_id"))],
                ["Protocol version", _pick(protocol_info, "version", default=_pick(protocol, "version"))],
                ["Protocol status", _pick(protocol_info, "status", default=_pick(protocol, "status"))],
                ["Protocol frozen on", _pick(protocol_info, "frozen_on")],
                ["Full run started after freeze", _pick(change_control, "full_run_started_after_freeze")],
                ["Prospectively recorded deviations", _deviations(change_control)],
                ["Governed protocol SHA-256", protocol_sha256],
                ["Authoritative result SHA-256", results_sha256],
                ["Scientific output SHA-256", _pick(results, "scientific_output_sha256")],
            ],
        ),
        "",
        "The result hash above was added by this post-run report build for traceability only. "
        "It is not presented as a prospective MAP element; design assumptions, methods, "
        "criteria, scenario identities, and seeds are governed by the frozen protocol.",
        "",
        "## ICH M15 Context and Model Risk",
        "",
        _table(["Assessment element", "Prespecified statement"], _assessment_rows(assessment)),
        "",
        "### Context and Risk Interpretation",
        "",
        *_bullets(_pick(assessment, "model_risk_rationale", "risk_rationale", "interpretation")),
        *_bullets(_pick(assessment, "residual_uncertainty")),
        "",
        "## ICH E9(R1) Estimand",
        "",
        _table(["Attribute", "Prespecified definition"], _estimand_rows(estimand)),
        "",
        "### Intercurrent Events",
        "",
        _table(["Intercurrent event", "Strategy", "Simulation / analysis handling"], _ice_rows(estimand)),
        "",
        "### Missing Data and Censoring",
        "",
        _table(["Mechanism", "Classification", "Handling"], _missingness_rows(estimand)),
        "",
        "Missing observations and administrative censoring are handled according to the "
        "governed methods; they are not silently relabelled as intercurrent events.",
        "",
        "## ADEMP and OCTAVE Framework",
        "",
        "### Objectives and Aims",
        "",
        *_bullets([_pick(protocol_info, "objective"), _pick(ademp, "aims"), _pick(octave, "objectives")]),
        "",
        "### Characteristics and Data-Generating Mechanisms",
        "",
        *_bullets([_pick(ademp, "data_generating_mechanism"), _pick(octave, "characteristics")]),
        "",
        "### Trial Design and Analysis Methods",
        "",
        _table(
            ["Design element", "Governed value"],
            [[key.replace("_", " ").title(), value] for key, value in design.items()],
        ),
        "",
        *_bullets([_pick(octave, "trial_design"), _pick(ademp, "methods"), _pick(octave, "analyses")]),
        "",
        "### Valuation Metrics and Evidence",
        "",
        *_bullets(_pick(ademp, "performance_measures")),
        *_bullets([_pick(octave, "valuation_metrics"), _pick(octave, "evidence")]),
        "",
        "### Parameter Provenance",
        "",
        _table(
            ["Provenance class", "Governed assumptions"],
            [
                [key.replace("_", " ").title(), value]
                for key, value in _pick(protocol, "parameter_provenance", default={}).items()
            ],
        ),
        "",
        "## Scenario Registry",
        "",
        _table(
            ["Scenario", "Class", "Endpoint", "Assumption basis", "Varying factors", "Replicates", "Seed"],
            scenario_rows,
        ),
        "",
        "Scenario identifiers, requested replication counts, and seeds are exact governed "
        "values. Null, alternative, non-proportional-effect, and operational-stress roles "
        "must remain explicit; scenarios are not pooled into an undocumented average.",
        "",
        "## Monte Carlo and Operating-Characteristic Methods",
        "",
        *_bullets(
            [
                f"One-sided alpha: {_display(_pick(design, 'alpha_one_sided'))}",
                f"Batch size: {_display(_pick(design, 'batch_size'))}",
                _pick(ademp, "methods"),
                _pick(ademp, "performance_measures"),
            ]
        ),
        "",
        "For every binomial operating characteristic, the report presents the exact "
        "numerator and denominator, estimate, Monte Carlo standard error, and Wilson 95% "
        "interval supplied by the authoritative scientific JSON.",
        "",
        "## Prespecified Acceptance Criteria",
        "",
        _table(["Control", "Criterion", "Scope"], _criteria_rows(criteria)),
        "",
        "Execution, Monte Carlo precision, design operating characteristics, and evidence "
        "qualification are assessed separately. A successfully executed, precisely estimated "
        "unacceptable design remains a design failure or review finding.",
        "",
        "## Representative Simulated Trial Path Selection",
        "",
        _table(
            ["Selection element", "Governed value"],
            [
                [key.replace("_", " ").title(), value]
                for key, value in _pick(
                    protocol, "representative_trial_selection", default={}
                ).items()
            ],
        ),
        "",
        "Actual aggregate simulated trial paths are selected deterministically from the "
        "governed scenario using a separate selection seed and frozen search rules. They "
        "supplement aggregate operating characteristics and do not replace them.",
        "",
        "## Deterministic Edge-Case Verification Fixtures",
        "",
        "Artificial separated-time and zero-event cases are retained only as software "
        "verification fixtures for log-rank direction, decisions, and non-estimable handling.",
        "",
        *_bullets(_pick(assessment, "validation_plan")),
        "",
        "## Reproducibility, Verification, and Change Control",
        "",
        "### Observed Execution Environment",
        "",
        _table(["Component", "Recorded identity"], _software_rows(_pick(results, "software_identity"))),
        "",
        "The environment above is a post-run traceability record, not a prospective design "
        "element. The dependency lock, float64 arithmetic, and PCG64 generator are part of "
        "the reproducibility contract.",
        "",
        "### Artifact Bindings",
        "",
        _table(
            ["Artifact", "Identity"],
            [
                ["Governed protocol", f"config/simulation_protocol.yaml — SHA-256 `{protocol_sha256}`"],
                ["Authoritative scientific results", f"platform/simulation_operating_characteristics/simulation_oc_status.json — SHA-256 `{results_sha256}`"],
                ["Scenario registry", _pick(result_protocol, "scenario_registry_sha256")],
                ["Simulation code", _pick(result_protocol, "code_sha256")],
                ["Scientific output", _pick(results, "scientific_output_sha256")],
            ],
        ),
        "",
        "Reproduce with `python3 platform/simulation_precision.py`, then run "
        "`python3 platform/build_simulation_report.py`. Identical governed inputs and seeds "
        "must reproduce identical scientific JSON and reports.",
        "",
        "## Qualification and Claim Boundary",
        "",
        *_bullets(qualification),
        "",
        "Reconstructed or synthetic CbzP data remain illustrative. This plan does not establish "
        "a clinically justified minimum effect, validate virtual patients against source IPD, "
        "support a clinical or filing decision, or convert TROPIC into a regulatory submission.",
        "",
        "## References and Governing Basis",
        "",
        *REFERENCE_LINES,
        "",
    ]
    return "\n".join(lines)


def build_report(
    protocol: Mapping[str, Any],
    results: Mapping[str, Any],
    protocol_sha256: str,
    results_sha256: str,
) -> str:
    protocol_info = _pick(protocol, "protocol", default={})
    assessment = dict(_pick(protocol, "m15_assessment", "assessment", default={}))
    assessment["question_of_interest"] = _pick(
        protocol_info, "question_of_interest", default=_pick(assessment, "question_of_interest")
    )
    assessment["context_of_use"] = _pick(
        protocol_info, "context_of_use", default=_pick(assessment, "context_of_use")
    )
    assessment["model_influence"] = _pick(
        _pick(protocol_info, "qualification_boundary", default={}),
        "model_influence",
        default=_pick(assessment, "model_influence"),
    )
    estimand = _pick(protocol, "estimand", default={})
    criteria = _pick(protocol, "acceptance_criteria", default={})
    framework = _pick(protocol, "protocol_framework", default={})
    ademp = _pick(framework, "ADEMP", default={})
    octave = _pick(framework, "OCTAVE", default={})
    statuses = _pick(results, "statuses", default={})
    result_protocol = _pick(results, "protocol", default={})
    scenarios = _result_scenarios(results)

    accounting_rows = []
    execution_status_rows = []
    oc_rows = []
    decision_rows = []
    seed_rows = []
    total_requested = total_completed = total_failed = 0
    for item in scenarios:
        scenario_id = _scenario_id(item)
        requested = _pick(item, "requested", "requested_replicates")
        completed = _pick(item, "completed", "completed_replicates")
        failed = _pick(item, "failed", "failed_replicates")
        total_requested += requested
        total_completed += completed
        total_failed += failed
        failures = _pick(item, "failures", "failure_reasons")
        if not failures and failed == 0:
            failures = NOT_APPLICABLE
        scenario_statuses = _pick(item, "statuses", default={})
        accounting_rows.append([
            scenario_id,
            requested,
            completed,
            failed,
            _pct(failed / requested if requested else None),
            failures,
        ])
        execution_status_rows.append([
            scenario_id,
            _status_value(scenario_statuses, "execution"),
            _pick(_pick(scenario_statuses, "execution", default={}), "reason"),
        ])
        rejection = _pick(item, "rejection", "operating_characteristic", default={})
        wilson = _pick(rejection, "wilson_95", "wilson_95_interval", default=[])
        if not isinstance(wilson, Mapping):
            wilson_display = NOT_REPORTED
        else:
            wilson_display = f"{_pct(_pick(wilson, 'lower'))} to {_pct(_pick(wilson, 'upper'))}"
        oc_rows.append([
            scenario_id,
            _pick(item, "class", "type", "scenario_type", "classification"),
            f"{_pick(rejection, 'numerator')} / {_pick(rejection, 'denominator')}",
            _pct(_pick(rejection, "estimate")),
            _display(_pick(rejection, "mcse")),
            wilson_display,
        ])
        decision_rows.append([
            scenario_id,
            _status_value(scenario_statuses, "precision"),
            _pick(_pick(scenario_statuses, "precision", default={}), "reason"),
            _status_value(scenario_statuses, "design_operating_characteristic"),
            _pick(_pick(scenario_statuses, "design_operating_characteristic", default={}), "reason"),
        ])
        seed_rows.append([
            scenario_id,
            _pick(item, "seed"),
            _pick(item, "scenario_sha256"),
        ])

    if total_requested != total_completed + total_failed:
        raise RuntimeError("aggregate requested replicates do not reconcile")

    status_rows = [
        ["Execution", _status_value(statuses, "execution"), _status_reason(statuses, "execution"), "Did requested replicates complete with failures explicitly accounted for?"],
        ["Monte Carlo precision", _status_value(statuses, "monte_carlo_precision"), _status_reason(statuses, "monte_carlo_precision"), "Were prespecified replication, failure-rate, and uncertainty criteria met?"],
        ["Design operating characteristics", _status_value(statuses, "design_operating_characteristics"), _status_reason(statuses, "design_operating_characteristics"), "Did the design meet the scenario-specific scientific acceptance criteria?"],
        ["Evidence qualification", _status_value(statuses, "evidence_qualification"), _status_reason(statuses, "evidence_qualification"), "What decisions may these results support?"],
    ]

    scenario_context_rows = []
    protocol_by_id = {_scenario_id(item): item for item in _scenario_registry(protocol)}
    for item in scenarios:
        scenario_id = _scenario_id(item)
        planned = protocol_by_id.get(scenario_id, {})
        scenario_context_rows.append([
            scenario_id,
            _pick(item, "endpoint", default=_pick(planned, "endpoint")),
            _pick(item, "class", "type", "scenario_type", "classification", default=_pick(planned, "class", "type", "scenario_type", "classification")),
            _pick(item, "assumption_basis", default=_pick(planned, "assumption_basis", "rationale")),
            _scenario_design(planned),
        ])

    validation = _pick(results, "validation", default={})
    if isinstance(validation, Mapping):
        validation_rows = [
            [key.replace("_", " ").title(), value]
            for key, value in validation.items()
            if key != "logrank_edge_fixtures"
        ]
    else:
        validation_rows = [["Validation", validation]]

    lines = [
        "# TROPIC Simulation Model Analysis Report",
        "",
        RELEASE_IDENTITY,
        "",
        "> **Informative annex boundary.** These deterministic simulation results are a "
        "data-free methods evaluation layered on the historical sealed clinical-simulation "
        "release. They are not MIDD evidence, a filing artifact, confirmatory efficacy "
        "evidence, sponsor approval, or evidence of regulator acceptance.",
        "",
        "## Reviewer Status Snapshot",
        "",
        _table(["Assessment", "Status", "Authoritative rationale", "Meaning"], status_rows),
        "",
        "There is deliberately no single overall PASS. Execution and precision statuses "
        "describe the reliability of the computation; the design status describes the "
        "operating characteristics. Precision does not rescue an unacceptable design result.",
        "",
        "## Question, Context, and Model Risk",
        "",
        _table(["ICH M15 element", "Assessed value"], _assessment_rows(assessment)),
        "",
        "## Estimand and Intercurrent Events",
        "",
        _table(["ICH E9(R1) attribute", "Implemented definition"], _estimand_rows(estimand)),
        "",
        "### Intercurrent-Event Handling",
        "",
        _table(["Intercurrent event", "Strategy", "Simulation / analysis handling"], _ice_rows(estimand)),
        "",
        "### Missing Data and Censoring",
        "",
        _table(["Mechanism", "Classification", "Handling"], _missingness_rows(estimand)),
        "",
        "## Implemented ADEMP and OCTAVE Methods",
        "",
        _table(
            ["Framework element", "Implemented method"],
            [
                ["ADEMP aims", _pick(ademp, "aims")],
                ["ADEMP data-generating mechanism", _pick(ademp, "data_generating_mechanism")],
                ["ADEMP methods", _pick(ademp, "methods")],
                ["ADEMP performance measures", _pick(ademp, "performance_measures")],
                ["OCTAVE characteristics", _pick(octave, "characteristics")],
                ["OCTAVE trial design", _pick(octave, "trial_design")],
                ["OCTAVE analyses", _pick(octave, "analyses")],
                ["OCTAVE valuation metrics", _pick(octave, "valuation_metrics")],
                ["OCTAVE evidence", _pick(octave, "evidence")],
            ],
        ),
        "",
        "## Scenario Coverage",
        "",
        _table(["Scenario", "Endpoint", "Class", "Assumption basis", "Varying factors"], scenario_context_rows),
        "",
        "The scenario registry is reported without pooling so reviewers can distinguish null, "
        "alternative, non-proportional-effect, and operational-stress behavior.",
        "",
        "## Exact Execution and Failure Accounting",
        "",
        _table(
            ["Scenario", "Requested", "Completed", "Failed", "Failure rate", "Failure detail"],
            accounting_rows,
        ),
        "",
        _table(
            ["Aggregate requested", "Aggregate completed", "Aggregate failed", "Reconciliation"],
            [[total_requested, total_completed, total_failed, "PASS" if total_requested == total_completed + total_failed else "FAIL"]],
        ),
        "",
        "### Execution Status Rationale",
        "",
        _table(["Scenario", "Execution status", "Execution rationale"], execution_status_rows),
        "",
        "Every failed replicate remains in the denominator accounting above; failures are not "
        "silently deleted from the evidence surface.",
        "",
        "## Operating Characteristics and Monte Carlo Precision",
        "",
        _table(
            ["Scenario", "Class", "Rejections / analyzed", "Estimate", "MCSE", "Wilson 95% interval"],
            oc_rows,
        ),
        "",
        "### Precision and Design Decisions",
        "",
        _table(
            ["Scenario", "Precision status", "Precision rationale", "Design status", "Design rationale"],
            decision_rows,
        ),
        "",
        "Probability estimates, numerators, denominators, Monte Carlo standard errors, and "
        "Wilson intervals above are rendered directly from the authoritative scientific JSON. "
        "No result number is manually transcribed into this report.",
        "",
        "## Prespecified Criteria and Interpretation",
        "",
        _table(["Control", "Criterion", "Scope"], _criteria_rows(criteria)),
        "",
        "Design conclusions are scenario-specific. Null scenarios assess error control; "
        "alternatives and stress cases characterize behavior under their stated assumptions. "
        "Published effects, reconstructed comparators, or calibration values are not promoted "
        "to clinically justified target effects or minimum clinically important differences.",
        "",
        "## Representative Simulated Trial Paths",
        "",
        _table(
            ["Role", "Scenario", "Search index", "Seed binding", "Events", "Censors", "Z statistic", "One-sided p-value", "Decision and selection evidence"],
            _representative_rows(_pick(results, "representative_trials")),
        ),
        "",
        "These are actual aggregate paths selected from the governed OS null scenario using "
        "the frozen scenario binding, independent selection seed, and deterministic search "
        "rules. They are simulated trials, not original TROPIC participants, and they do not "
        "substitute for aggregate operating-characteristic estimates.",
        "",
        "## Deterministic Edge-Case Verification Fixtures",
        "",
        _table(
            ["Fixture", "Role", "Seed", "Analysis status", "Failure reason", "Z statistic", "One-sided p-value", "Reject", "Events", "Expected", "Validation status"],
            _fixture_rows(
                _pick(_pick(results, "validation", default={}), "logrank_edge_fixtures")
            ),
        ),
        "",
        "These deliberately artificial separated-time and zero-event fixtures verify sign, "
        "decision, and non-estimable boundary handling. They are software-validation cases, "
        "not representative simulated trial paths and not scientific operating-characteristic "
        "results.",
        "",
        "## Change Control and Deviations",
        "",
        _table(
            ["Item", "Final result"],
            [[
                "Deviations from the frozen MAP",
                _deviations(_pick(results, "change_control", default={})),
            ]],
        ),
        "",
        "## Verification and Validation Evidence",
        "",
        _table(["Check", "Evidence / result"], validation_rows),
        "",
        "## Seeds, Hashes, and Reproduction",
        "",
        "### Observed Execution Environment",
        "",
        _table(["Component", "Recorded identity"], _software_rows(_pick(results, "software_identity"))),
        "",
        "### Scenario Seed Ledger",
        "",
        _table(["Scenario", "Seed", "Scenario SHA-256"], seed_rows),
        "",
        "### Artifact Bindings",
        "",
        _table(
            ["Artifact", "SHA-256"],
            [
                ["Governed protocol", protocol_sha256],
                ["Authoritative result file", results_sha256],
                ["Protocol recorded by result", _pick(result_protocol, "protocol_sha256")],
                ["Scenario registry", _pick(result_protocol, "scenario_registry_sha256")],
                ["Simulation code", _pick(result_protocol, "code_sha256")],
                ["Scientific output", _pick(results, "scientific_output_sha256")],
            ],
        ),
        "",
        "Reproduce the scientific JSON with `python3 platform/simulation_precision.py`; "
        "rebuild both reviewer documents with `python3 platform/build_simulation_report.py`. "
        "Identical governed inputs and seeds must reproduce byte-identical scientific content "
        "and reviewer reports.",
        "",
        "## Limitations and Qualification Boundary",
        "",
        *_bullets(
            _pick(
                results,
                "qualification_boundary",
                default=_pick(protocol_info, "qualification_boundary"),
            )
        ),
        "",
        "This evidence surface does not establish authoritative CbzP subject-level data, a "
        "clinically justified minimum effect, external model validation, independent "
        "organizational review, sponsor approval, or regulator alignment. It must not be used "
        "for clinical, labeling, filing, or patient-level decisions.",
        "",
        "## References and Governing Basis",
        "",
        *REFERENCE_LINES,
        "",
    ]
    return "\n".join(lines)


def write_reports(
    protocol_path: Path,
    results_path: Path,
    plan_path: Path,
    report_path: Path,
) -> tuple[str, str]:
    protocol = _load_yaml(protocol_path)
    results = _load_json(results_path)
    validate_inputs(protocol, results, protocol_path)
    protocol_hash = _sha256(protocol_path)
    results_hash = _sha256(results_path)
    plan = build_analysis_plan(protocol, results, protocol_hash, results_hash)
    report = build_report(protocol, results, protocol_hash, results_hash)
    for path, content in ((plan_path, plan), (report_path, report)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return plan, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build deterministic simulation reviewer reports")
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--plan-output", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    write_reports(
        args.protocol.resolve(),
        args.results.resolve(),
        args.plan_output.resolve(),
        args.report_output.resolve(),
    )
    print(f"Wrote {os.path.relpath(args.plan_output.resolve(), ROOT)}")
    print(f"Wrote {os.path.relpath(args.report_output.resolve(), ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
