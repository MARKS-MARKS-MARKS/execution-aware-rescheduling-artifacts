#!/usr/bin/env python3
"""Run the fixed 66-case algorithm-seed robustness study without touching release outputs."""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMAL_RAW = ROOT / "data" / "raw" / "formal_release_raw.csv"
INSTANCE_ROOT = ROOT / "configurations" / "instances" / "inspection" / "formal"
FROZEN_ROOT = ROOT / "configurations" / "robustness_algorithm_seeds_v1"
SCENARIOS = FROZEN_ROOT / "scenarios_active_only_v1"
STATIC_CACHE = FROZEN_ROOT / "static_cache_active_only_v1"
OUTPUT_ROOT = ROOT / "generated" / "algorithm_seed_robustness"
ALGORITHMS = ("dynamic_ails", "global_replan")
ALGORITHM_SEEDS = tuple(range(1000, 1010))
EXPECTED_CASES = 66
EXPECTED_RUNS = EXPECTED_CASES * len(ALGORITHMS) * len(ALGORITHM_SEEDS)


def safe(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "_", value).rstrip("_")


def progress_token(value: str) -> str:
    return f"p{round(float(value) * 100):03d}"


def scenario_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return row["instance"], row["scenario"], row["progress"], row["seed"]


def scenario_id(row: dict[str, str]) -> str:
    return (
        f"{safe(row['instance'])}__{row['scenario']}__{progress_token(row['progress'])}"
        f"__seed{row['seed']}"
    )


def run_id(row: dict[str, str], method: str, algorithm_seed: int) -> str:
    return (
        f"{scenario_id(row)}__{method}__minimum_makespan"
        f"__algseed{algorithm_seed}"
    )


def read_one(path: Path) -> dict[str, str] | None:
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            return next(csv.DictReader(handle), None)
    except (OSError, csv.Error):
        return None


def fixed_common_cases() -> list[dict[str, str]]:
    with FORMAL_RAW.open(newline="", encoding="utf-8-sig") as handle:
        rows = [
            row for row in csv.DictReader(handle)
            if row["objective_mode"] == "minimum_makespan"
        ]
    grouped: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[scenario_key(row)].append(row)
    cases = []
    for group in grouped.values():
        successful = {
            row["algorithm"] for row in group if row["status"] == "SUCCESS"
        }
        if successful == {"greedy", "greedy_ls", "dynamic_ails", "global_replan"}:
            cases.append(next(row for row in group if row["algorithm"] == "greedy"))
    cases.sort(key=scenario_key)
    if len(cases) != EXPECTED_CASES:
        raise RuntimeError(
            f"frozen common-feasible set changed: expected {EXPECTED_CASES}, found {len(cases)}"
        )
    return cases


def merge_runs(paths: list[Path], output: Path) -> list[dict[str, str]]:
    records = [record for path in paths if (record := read_one(path)) is not None]
    records.sort(key=lambda row: (
        row["instance"], row["scenario"], float(row["progress"]),
        int(row["scenario_seed"]), row["algorithm"], int(row["algorithm_seed"])
    ))
    fields: list[str] = []
    for record in records:
        for field in record:
            if field not in fields:
                fields.append(field)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    return records


def validate(records: list[dict[str, str]]) -> list[dict[str, str]]:
    failures = [row for row in records if row.get("status") != "SUCCESS"]
    if len(records) != EXPECTED_RUNS:
        raise RuntimeError(f"expected {EXPECTED_RUNS} run rows, found {len(records)}")
    identities = {
        (
            row["instance"], row["scenario"], row["progress"],
            row["scenario_seed"], row["algorithm"], row["algorithm_seed"]
        )
        for row in records
    }
    if len(identities) != EXPECTED_RUNS:
        raise RuntimeError("duplicate robustness run identity")
    required_true = ("feasible", "prefix_preserved", "dynamic_valid", "legacy_valid")
    failures.extend(
        row for row in records
        if row.get("status") == "SUCCESS"
        and any(row.get(field) != "true" for field in required_true)
    )
    if failures:
        raise RuntimeError(f"{len(failures)} robustness runs failed validation")
    return failures


def write_failures(failures: list[dict[str, str]], path: Path) -> None:
    fields = [
        "run_id", "instance", "scenario", "progress", "scenario_seed",
        "algorithm_seed", "algorithm", "status", "error_message"
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(failures)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run 66 fixed scenarios x 2 methods x 10 independent algorithm seeds"
    )
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--force", action="store_true", help="rerun existing successful robustness rows")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    executable = args.executable.resolve()
    if not executable.exists():
        print(f"ERROR: missing executable: {executable}", file=sys.stderr)
        return 2

    cases = fixed_common_cases()
    runs_dir = OUTPUT_ROOT / "runs"
    logs_dir = OUTPUT_ROOT / "logs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    expected_paths: list[Path] = []
    total = EXPECTED_RUNS
    started = time.perf_counter()
    index = 0

    for case in cases:
        instance_path = INSTANCE_ROOT / f"{case['instance']}.gtsp"
        static_path = INSTANCE_ROOT / f"{case['instance']}.active.gtsp"
        if not instance_path.exists() or not static_path.exists():
            raise RuntimeError(f"missing released instance files for {case['instance']}")
        manifest = SCENARIOS / f"{scenario_id(case)}.json"
        static_cache = STATIC_CACHE / (
            f"{safe(case['instance'])}__active_only_v1__seed{case['seed']}.plan"
        )
        if not manifest.exists() or not static_cache.exists():
            raise RuntimeError(f"missing frozen scenario asset for {scenario_id(case)}")
        for method in ALGORITHMS:
            for algorithm_seed in ALGORITHM_SEEDS:
                index += 1
                identity = run_id(case, method, algorithm_seed)
                output = runs_dir / f"{identity}.csv"
                log = logs_dir / f"{identity}.log"
                expected_paths.append(output)
                existing = read_one(output)
                if existing and existing.get("status") == "SUCCESS" and not args.force:
                    print(f"[{index}/{total}] RESUME {identity}", flush=True)
                    continue
                command = [
                    str(executable),
                    "--instance", str(instance_path.relative_to(ROOT)),
                    "--static-instance", str(static_path.relative_to(ROOT)),
                    "--scenario", case["scenario"],
                    "--progress", case["progress"],
                    "--algorithm", method,
                    "--objective", "minimum_makespan",
                    "--seed", case["seed"],
                    "--algorithm-seed", str(algorithm_seed),
                    "--ails-time-ms", "1000",
                    "--ails-iterations", "1000",
                    "--scenario-manifest", str(manifest.relative_to(ROOT)),
                    "--static-plan-cache", str(static_cache.relative_to(ROOT)),
                    "--output", str(output.relative_to(ROOT)),
                    "--log", str(log.relative_to(ROOT)),
                ]
                print(f"[{index}/{total}] {'PLAN' if args.dry_run else 'RUN'} {identity}", flush=True)
                if args.dry_run:
                    continue
                completed = subprocess.run(
                    command, cwd=ROOT, capture_output=True, text=True,
                    encoding="utf-8", errors="replace", timeout=120
                )
                with log.open("a", encoding="utf-8") as handle:
                    handle.write(
                        "\nsubprocess_command=" + subprocess.list2cmdline(command)
                        + f"\nsubprocess_returncode={completed.returncode}"
                        + "\n--- stdout ---\n" + completed.stdout
                        + "\n--- stderr ---\n" + completed.stderr
                    )

    if args.dry_run:
        return 0
    records = merge_runs(expected_paths, OUTPUT_ROOT / "algorithm_seed_runs.csv")
    failures = [row for row in records if row.get("status") != "SUCCESS"]
    write_failures(failures, OUTPUT_ROOT / "algorithm_seed_failures.csv")
    validate(records)
    elapsed = time.perf_counter() - started
    print(
        f"robustness rows={len(records)} failures={len(failures)} "
        f"elapsed_seconds={elapsed:.3f}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
