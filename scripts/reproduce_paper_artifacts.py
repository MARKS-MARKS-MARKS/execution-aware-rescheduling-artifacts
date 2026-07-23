#!/usr/bin/env python3
"""Reproduce the paper's aggregate metrics, Tables II--III, and Figs. 3--4."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from paper_aggregation import (
    DISRUPTION_MODE,
    METHOD_ORDER,
    PRIMARY_MODE,
    event_case_summary,
    method_summary,
    paper_metrics,
    read_records,
)
from plot_paper_figures import generate_all


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "raw" / "formal_release_raw.csv"
DEFAULT_OUTPUT = ROOT / "generated"


def close(actual: float, expected: float, tolerance: float = 5e-4) -> None:
    if not math.isclose(actual, expected, abs_tol=tolerance):
        raise ValueError(f"expected {expected}, obtained {actual}")


def validate_expected_values(
    records: list[dict[str, str]], digest: dict[str, object]
) -> None:
    if digest["release_rows"] != 297:
        raise ValueError("release row count changed")
    if digest["common_feasible_primary_cases"] != 66:
        raise ValueError("common-feasible primary set changed")

    expected_events = {
        "new_task_arrival": (24, 24, 99, 99),
        "service_location_invalidation": (24, 24, 99, 99),
        "robot_failure": (18, 24, 75, 99),
    }
    for row in event_case_summary(records):
        actual = (
            int(float(row["feasible_cases"])),
            int(float(row["total_cases"])),
            int(float(row["successful_runs"])),
            int(float(row["total_runs"])),
        )
        if actual != expected_events[str(row["event"])]:
            raise ValueError(f"Table II mismatch for {row['event']}: {actual}")

    expected_methods = {
        "greedy": (144.710, 4.163),
        "greedy_ls": (144.276, 13.344),
        "dynamic_ails": (141.705, 1077.587),
        "global_replan": (146.073, 1188.071),
    }
    methods = {str(row["method"]): row for row in method_summary(records)}
    for method in METHOD_ORDER:
        close(float(methods[method]["cost"]), expected_methods[method][0])
        close(float(methods[method]["time_ms"]), expected_methods[method][1])

    close(
        float(digest["dails_vs_greedy_aggregate_mean_reduction_percent"]),
        2.08,
        tolerance=0.01,
    )
    tradeoff = digest["objective_tradeoff_m_c_p50"]
    if set(tradeoff) != {PRIMARY_MODE, DISRUPTION_MODE}:
        raise ValueError("objective trade-off modes changed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild paper aggregates and figures from published run-level "
            "outputs; this does not run the solver."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="published formal run-level CSV",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="generated output directory",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw = args.input.resolve()
    output = args.output.resolve()
    raw_parent = raw.parent
    if output == raw_parent or raw_parent in output.parents:
        raise ValueError("output must not be inside the raw-data directory")

    records = read_records(raw)
    digest = paper_metrics(records)
    validate_expected_values(records, digest)

    output.mkdir(parents=True, exist_ok=True)
    metrics_dir = output / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    (metrics_dir / "formal_release_paper_metrics.json").write_text(
        json.dumps(digest, indent=2), encoding="utf-8"
    )
    generate_all(records, output)
    summary = {
        "input": str(args.input),
        "release_rows": digest["release_rows"],
        "active_only_static_plans": True,
        "common_feasible_primary_cases": digest[
            "common_feasible_primary_cases"
        ],
        "table_ii": event_case_summary(records),
        "table_iii": method_summary(records),
        "aggregate_mean_reduction_definition": (
            "(baseline mean - alternative mean) / baseline mean * 100"
        ),
        "dails_vs_greedy_aggregate_mean_reduction_percent": digest[
            "dails_vs_greedy_aggregate_mean_reduction_percent"
        ],
        "generated_output": str(args.output),
    }
    (output / "reproduction_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    print("Generated Tables II--III and Figs. 3--4 without running the solver.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
