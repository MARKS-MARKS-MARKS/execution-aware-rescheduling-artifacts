#!/usr/bin/env python3
"""Read-only aggregation used for the formal paper assets.

This is the portable artifact version of ``formal_paper_aggregation.py`` used
for the active-only formal Release results.  It reads only the published
run-level CSV and never invokes the optimization implementation.
"""
from __future__ import annotations

import csv
import math
import statistics
from pathlib import Path


METHOD_ORDER = ("greedy", "greedy_ls", "dynamic_ails", "global_replan")
METHOD_LABEL = {
    "greedy": "Greedy",
    "greedy_ls": "Greedy+LS",
    "dynamic_ails": "D-AILS",
    "global_replan": "Global Replan",
}
EVENT_ORDER = (
    "new_task_arrival",
    "service_location_invalidation",
    "robot_failure",
)
EVENT_LABEL = {
    "new_task_arrival": "Task arrival",
    "service_location_invalidation": "Location invalidation",
    "robot_failure": "Robot failure",
}
PRIMARY_MODE = "minimum_makespan"
DISRUPTION_MODE = "disruption_aware"
COMMON_KEY = ("instance", "scenario", "progress", "seed")
EXPECTED_COLUMNS = {
    "instance",
    "static_plan_identifier",
    "static_input_groups",
    "scenario",
    "progress",
    "algorithm",
    "objective_mode",
    "seed",
    "final_dynamic_makespan",
    "replanning_time_ms",
    "reassigned_tasks",
    "changed_candidates",
    "changed_edges",
    "status",
}
EXPECTED_ACTIVE_GROUPS = {
    "S-U": "20",
    "S-C": "20",
    "M-U": "50",
    "M-C": "50",
    "L-U": "100",
    "L-C": "100",
}


def number(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"non-finite formal metric: {value}")
    return parsed


def mean(rows: list[dict[str, str]], field: str) -> float:
    return statistics.fmean(number(row[field]) for row in rows)


def stdev(rows: list[dict[str, str]], field: str) -> float:
    values = [number(row[field]) for row in rows]
    return statistics.stdev(values) if len(values) > 1 else 0.0


def read_records(raw: Path) -> list[dict[str, str]]:
    with raw.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or ())
        missing = sorted(EXPECTED_COLUMNS - columns)
        if missing:
            raise ValueError(f"formal CSV is missing required columns: {missing}")
        records = list(reader)
    if len(records) != 297:
        raise ValueError(f"expected 297 formal release rows, found {len(records)}")
    validate_active_only(records)
    return records


def validate_active_only(records: list[dict[str, str]]) -> None:
    for row in records:
        instance = Path(row["instance"]).stem
        if instance not in EXPECTED_ACTIVE_GROUPS:
            raise ValueError(f"unexpected formal instance: {row['instance']}")
        if ":active-only-v1:" not in row["static_plan_identifier"]:
            raise ValueError(
                "formal CSV does not exclusively use active-only static plans"
            )
        if row["static_input_groups"] != EXPECTED_ACTIVE_GROUPS[instance]:
            raise ValueError(
                f"static input for {instance} contains "
                f"{row['static_input_groups']} groups; expected "
                f"{EXPECTED_ACTIVE_GROUPS[instance]}"
            )


def key(row: dict[str, str]) -> tuple[str, ...]:
    return tuple(row[column] for column in COMMON_KEY)


def common_feasible_primary(
    records: list[dict[str, str]],
) -> dict[str, list[dict[str, str]]]:
    primary = [row for row in records if row["objective_mode"] == PRIMARY_MODE]
    successful_keys = [
        {
            key(row)
            for row in primary
            if row["algorithm"] == method and row["status"] == "SUCCESS"
        }
        for method in METHOD_ORDER
    ]
    common = set.intersection(*successful_keys)
    groups = {
        method: [
            row
            for row in primary
            if row["algorithm"] == method and key(row) in common
        ]
        for method in METHOD_ORDER
    }
    if not common or any(
        len(groups[method]) != len(common) for method in METHOD_ORDER
    ):
        raise ValueError(
            "formal common-feasible primary-objective sets are empty or unequal"
        )
    return groups


def method_summary(
    records: list[dict[str, str]],
) -> list[dict[str, float | str]]:
    groups = common_feasible_primary(records)
    primary = [row for row in records if row["objective_mode"] == PRIMARY_MODE]
    result: list[dict[str, float | str]] = []
    for method in METHOD_ORDER:
        group = groups[method]
        method_rows = [row for row in primary if row["algorithm"] == method]
        result.append(
            {
                "method": method,
                "label": METHOD_LABEL[method],
                "common_cases": float(len(group)),
                "feasible_rate": 100.0
                * sum(row["status"] == "SUCCESS" for row in method_rows)
                / len(method_rows),
                "cost": mean(group, "final_dynamic_makespan"),
                "cost_std": stdev(group, "final_dynamic_makespan"),
                "time_ms": mean(group, "replanning_time_ms"),
                "time_ms_std": stdev(group, "replanning_time_ms"),
                "reassigned": mean(group, "reassigned_tasks"),
                "changed_locations": mean(group, "changed_candidates"),
                "changed_edges": mean(group, "changed_edges"),
            }
        )
    return result


def event_recovery(
    records: list[dict[str, str]],
) -> list[dict[str, float | str]]:
    result: list[dict[str, float | str]] = []
    for event in EVENT_ORDER:
        rows = [row for row in records if row["scenario"] == event]
        successful = sum(row["status"] == "SUCCESS" for row in rows)
        result.append(
            {
                "event": event,
                "label": EVENT_LABEL[event],
                "successful": float(successful),
                "total": float(len(rows)),
                "rate": 100.0 * successful / len(rows),
            }
        )
    return result


def event_case_summary(
    records: list[dict[str, str]],
) -> list[dict[str, float | str]]:
    """Return the case-level and run-level values used in paper Table II."""
    primary = [row for row in records if row["objective_mode"] == PRIMARY_MODE]
    result: list[dict[str, float | str]] = []
    run_rows = {str(row["event"]): row for row in event_recovery(records)}
    for event in EVENT_ORDER:
        event_rows = [row for row in primary if row["scenario"] == event]
        cases: dict[tuple[str, ...], list[dict[str, str]]] = {}
        for row in event_rows:
            cases.setdefault(key(row), []).append(row)
        if len(cases) != 24:
            raise ValueError(f"expected 24 primary cases for {event}")
        if any(
            sorted(row["algorithm"] for row in rows) != sorted(METHOD_ORDER)
            for rows in cases.values()
        ):
            raise ValueError(f"incomplete method set in {event} scenario cases")
        feasible = sum(
            all(row["status"] == "SUCCESS" for row in rows)
            for rows in cases.values()
        )
        run = run_rows[event]
        result.append(
            {
                "event": event,
                "label": EVENT_LABEL[event],
                "feasible_cases": float(feasible),
                "total_cases": float(len(cases)),
                "successful_runs": float(run["successful"]),
                "total_runs": float(run["total"]),
            }
        )
    return result


def progress_summary(
    records: list[dict[str, str]],
) -> list[dict[str, float | str]]:
    result: list[dict[str, float | str]] = []
    for progress in (0.25, 0.50, 0.75):
        for method in METHOD_ORDER:
            rows = [
                row
                for row in records
                if Path(row["instance"]).stem == "M-C"
                and row["objective_mode"] == PRIMARY_MODE
                and row["algorithm"] == method
                and row["status"] == "SUCCESS"
                and math.isclose(number(row["progress"]), progress, abs_tol=1e-9)
            ]
            if len(rows) != 9:
                raise ValueError(
                    f"expected 9 M-C rows for {method} at progress {progress}"
                )
            result.append(
                {
                    "progress": progress,
                    "method": method,
                    "label": METHOD_LABEL[method],
                    "time_ms": mean(rows, "replanning_time_ms"),
                }
            )
    if len(result) != 12:
        raise ValueError(
            "formal route-local progress summary does not contain 12 points"
        )
    return result


def objective_tradeoff(
    records: list[dict[str, str]],
) -> list[dict[str, float | str]]:
    result: list[dict[str, float | str]] = []
    for mode, label in (
        (PRIMARY_MODE, "Primary objective"),
        (DISRUPTION_MODE, "Disruption-aware"),
    ):
        rows = [
            row
            for row in records
            if Path(row["instance"]).stem == "M-C"
            and row["algorithm"] == "dynamic_ails"
            and row["objective_mode"] == mode
            and row["status"] == "SUCCESS"
            and math.isclose(number(row["progress"]), 0.50, abs_tol=1e-9)
        ]
        if len(rows) != 9:
            raise ValueError(
                f"expected 9 M-C objective-comparison rows for {mode}"
            )
        result.append(
            {
                "mode": mode,
                "label": label,
                "cost": mean(rows, "final_dynamic_makespan"),
                "time_ms": mean(rows, "replanning_time_ms"),
                "reassigned": mean(rows, "reassigned_tasks"),
                "changed_locations": mean(rows, "changed_candidates"),
                "changed_edges": mean(rows, "changed_edges"),
            }
        )
    return result


def scaling_summary(
    records: list[dict[str, str]],
) -> list[dict[str, float | str]]:
    result: list[dict[str, float | str]] = []
    for scale in ("S", "M", "L"):
        for method in METHOD_ORDER:
            rows = [
                row
                for row in records
                if Path(row["instance"]).stem.startswith(scale + "-")
                and row["objective_mode"] == PRIMARY_MODE
                and row["algorithm"] == method
                and row["status"] == "SUCCESS"
                and math.isclose(number(row["progress"]), 0.50, abs_tol=1e-9)
            ]
            if not rows:
                raise ValueError(f"no successful scale rows for {scale}/{method}")
            result.append(
                {
                    "scale": scale,
                    "method": method,
                    "label": METHOD_LABEL[method],
                    "successful": float(len(rows)),
                    "time_ms": mean(rows, "replanning_time_ms"),
                    "cost": mean(rows, "final_dynamic_makespan"),
                }
            )
    return result


def paper_metrics(records: list[dict[str, str]]) -> dict[str, object]:
    """Reproduce the published ``formal_release_paper_metrics.json`` digest."""
    methods = method_summary(records)
    tradeoff_rows = objective_tradeoff(records)
    tradeoff = {
        str(row["mode"]): {
            "runs": 9,
            "makespan": float(row["cost"]),
            "time_ms": float(row["time_ms"]),
            "reassigned": float(row["reassigned"]),
            "locations": float(row["changed_locations"]),
            "edges": float(row["changed_edges"]),
        }
        for row in tradeoff_rows
    }
    primary, disruption = tradeoff[PRIMARY_MODE], tradeoff[DISRUPTION_MODE]
    progress = progress_summary(records)
    scaling = scaling_summary(records)
    method_map = {
        str(row["method"]): {
            "runs": int(float(row["common_cases"])),
            "feasible_rate": float(row["feasible_rate"]),
            "makespan": float(row["cost"]),
            "time_ms": float(row["time_ms"]),
            "reassigned": float(row["reassigned"]),
            "locations": float(row["changed_locations"]),
            "edges": float(row["changed_edges"]),
        }
        for row in methods
    }
    common_cases = int(float(methods[0]["common_cases"]))
    return {
        "release_rows": len(records),
        "common_feasible_primary_cases": common_cases,
        "events": {
            str(row["event"]): {
                "runs": int(float(row["total"])),
                "success": int(float(row["successful"])),
                "rate_percent": float(row["rate"]),
            }
            for row in event_recovery(records)
        },
        "structural_failures": sum(
            row["status"] == "FAILED" for row in records
        ),
        "methods_common_feasible_primary": method_map,
        "dails_vs_greedy_aggregate_mean_reduction_percent": 100.0
        * (
            method_map["greedy"]["makespan"]
            - method_map["dynamic_ails"]["makespan"]
        )
        / method_map["greedy"]["makespan"],
        "objective_tradeoff_m_c_p50": tradeoff,
        "tradeoff_percent": {
            "edges_reduction": 100.0
            * (primary["edges"] - disruption["edges"])
            / primary["edges"],
            "reassignment_reduction": 100.0
            * (primary["reassigned"] - disruption["reassigned"])
            / primary["reassigned"],
            "makespan_increase": 100.0
            * (disruption["makespan"] - primary["makespan"])
            / primary["makespan"],
        },
        "progress_sensitivity_m_c": progress,
        "scaling_p50": scaling,
    }
