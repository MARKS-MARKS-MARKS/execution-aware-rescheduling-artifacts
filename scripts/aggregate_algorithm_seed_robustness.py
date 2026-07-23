#!/usr/bin/env python3
"""Aggregate the public algorithm-seed runs using only the frozen Greedy baseline."""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS = ROOT / "data" / "raw" / "algorithm_seed_runs.csv"
DEFAULT_FORMAL = ROOT / "data" / "raw" / "formal_release_raw.csv"
DEFAULT_OUTPUT = ROOT / "generated" / "algorithm_seed_robustness"
EXPECTED_CASES = 66
EXPECTED_SEEDS = 10
EXPECTED_RUNS = 1320
TIE_TOLERANCE = 1e-9
BOOTSTRAP_SEED = 20260723
BOOTSTRAP_RESAMPLES = 10_000


def scenario_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    seed = row.get("scenario_seed", row.get("seed", ""))
    instance = Path(row["instance"]).stem
    return instance, row["scenario"], row["progress"], seed


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (position - lower) * (ordered[upper] - ordered[lower])


def distribution(values: list[float], prefix: str) -> dict[str, float]:
    mean = statistics.fmean(values)
    sample_sd = statistics.stdev(values)
    return {
        f"{prefix}_mean": mean,
        f"{prefix}_sample_sd": sample_sd,
        f"{prefix}_median": statistics.median(values),
        f"{prefix}_min": min(values),
        f"{prefix}_max": max(values),
        f"{prefix}_cv": sample_sd / mean if mean else 0.0,
    }


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    fields: list[str] = []
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def baseline_costs(formal_rows: list[dict[str, str]]) -> dict[tuple[str, str, str, str], float]:
    values = {
        scenario_key(row): float(row["final_dynamic_makespan"])
        for row in formal_rows
        if row["objective_mode"] == "minimum_makespan"
        and row["algorithm"] == "greedy"
        and row["status"] == "SUCCESS"
    }
    if len(values) < EXPECTED_CASES:
        raise RuntimeError("formal Greedy baseline has fewer than 66 successful cases")
    return values


def method_metrics(
    method: str,
    scenario_rows: list[dict[str, object]],
) -> dict[str, object]:
    reductions = [float(row["paired_relative_reduction_percent"]) for row in scenario_rows]
    greedy = [float(row["greedy_baseline_cost"]) for row in scenario_rows]
    method_means = [float(row["route_cost_mean"]) for row in scenario_rows]
    wins = sum(m < g - TIE_TOLERANCE for m, g in zip(method_means, greedy))
    losses = sum(m > g + TIE_TOLERANCE for m, g in zip(method_means, greedy))
    ties = len(method_means) - wins - losses
    rng = random.Random(BOOTSTRAP_SEED)
    bootstrap = [
        statistics.fmean(rng.choices(reductions, k=len(reductions)))
        for _ in range(BOOTSTRAP_RESAMPLES)
    ]
    within_sds = [float(row["route_cost_sample_sd"]) for row in scenario_rows]
    return {
        "method": method,
        "scenario_count": len(scenario_rows),
        "algorithm_seeds_per_scenario": EXPECTED_SEEDS,
        "win_count": wins,
        "tie_count": ties,
        "loss_count": losses,
        "mean_paired_relative_reduction_percent": statistics.fmean(reductions),
        "median_paired_relative_reduction_percent": statistics.median(reductions),
        "aggregate_greedy_mean_cost": statistics.fmean(greedy),
        "aggregate_seed_averaged_method_mean_cost": statistics.fmean(method_means),
        "aggregate_mean_reduction_percent": (
            100.0 * (statistics.fmean(greedy) - statistics.fmean(method_means))
            / statistics.fmean(greedy)
        ),
        "bootstrap_ci_low_percent": percentile(bootstrap, 0.025),
        "bootstrap_ci_high_percent": percentile(bootstrap, 0.975),
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "tie_tolerance_absolute": TIE_TOLERANCE,
        "within_seed_sd_mean": statistics.fmean(within_sds),
        "within_seed_sd_median": statistics.median(within_sds),
        "within_seed_sd_min": min(within_sds),
        "within_seed_sd_max": max(within_sds),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--formal-raw", type=Path, default=DEFAULT_FORMAL)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    runs = read_rows(args.runs.resolve())
    if len(runs) != EXPECTED_RUNS:
        raise RuntimeError(f"expected {EXPECTED_RUNS} rows, found {len(runs)}")
    identities = {
        (*scenario_key(row), row["algorithm"], row["algorithm_seed"])
        for row in runs
    }
    if len(identities) != EXPECTED_RUNS:
        raise RuntimeError("duplicate algorithm-seed run")
    numeric_fields = (
        "final_dynamic_makespan", "replanning_time_ms", "reassigned_tasks",
        "changed_candidates", "changed_edges", "ails_iterations"
    )
    for row in runs:
        if row["status"] != "SUCCESS" or any(
            row[field] != "true"
            for field in ("feasible", "prefix_preserved", "dynamic_valid", "legacy_valid")
        ):
            raise RuntimeError(f"invalid run: {row['run_id']}")
        for field in numeric_fields:
            if not math.isfinite(float(row[field])):
                raise RuntimeError(f"non-finite {field}: {row['run_id']}")

    baselines = baseline_costs(read_rows(args.formal_raw.resolve()))
    grouped: dict[tuple[tuple[str, str, str, str], str], list[dict[str, str]]] = defaultdict(list)
    for row in runs:
        grouped[(scenario_key(row), row["algorithm"])].append(row)
    if len(grouped) != EXPECTED_CASES * 2:
        raise RuntimeError(f"expected {EXPECTED_CASES * 2} scenario-method groups")

    scenario_summary: list[dict[str, object]] = []
    for (key, method), rows in sorted(grouped.items()):
        rows.sort(key=lambda row: int(row["algorithm_seed"]))
        seeds = [int(row["algorithm_seed"]) for row in rows]
        if seeds != list(range(1000, 1010)):
            raise RuntimeError(f"algorithm seeds changed for {key} {method}")
        route_costs = [float(row["final_dynamic_makespan"]) for row in rows]
        times = [float(row["replanning_time_ms"]) for row in rows]
        baseline = baselines[key]
        summary: dict[str, object] = {
            "instance": key[0],
            "scenario": key[1],
            "progress": key[2],
            "scenario_seed": key[3],
            "method": method,
            "algorithm_seed_count": len(rows),
            "algorithm_seed_min": min(seeds),
            "algorithm_seed_max": max(seeds),
            "greedy_baseline_cost": baseline,
        }
        summary.update(distribution(route_costs, "route_cost"))
        summary.update(distribution(times, "online_time_ms"))
        summary["paired_relative_reduction_percent"] = (
            100.0 * (baseline - statistics.fmean(route_costs)) / baseline
        )
        scenario_summary.append(summary)

    methods = sorted({str(row["method"]) for row in scenario_summary})
    method_summary = [
        method_metrics(
            method,
            [row for row in scenario_summary if row["method"] == method],
        )
        for method in methods
    ]
    write_rows(output_root / "algorithm_seed_scenario_summary.csv", scenario_summary)
    write_rows(output_root / "algorithm_seed_method_summary.csv", method_summary)

    by_method = {str(row["method"]): row for row in method_summary}
    payload = {
        "study": {
            "description": "fixed-scenario independent algorithm-seed robustness study",
            "formal_release_runs_unchanged": 297,
            "common_feasible_scenarios": EXPECTED_CASES,
            "methods": methods,
            "algorithm_seeds": list(range(1000, 1010)),
            "run_count": EXPECTED_RUNS,
            "scenario_seed_role": "static plans, event manifests, progress states, and scenario identity",
            "algorithm_seed_role": "D-AILS and Global Replan randomized search components",
        },
        "statistics": {
            "route_cost_sd_definition": "sample standard deviation over 10 algorithm seeds within each fixed scenario",
            "tie_tolerance_absolute": TIE_TOLERANCE,
            "bootstrap": {
                "unit": "66 scenario-level paired relative reductions",
                "resamples": BOOTSTRAP_RESAMPLES,
                "seed": BOOTSTRAP_SEED,
                "interval": "percentile 95%",
            },
        },
        "method_metrics": by_method,
    }
    with (output_root / "algorithm_seed_robustness_metrics.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(by_method, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
