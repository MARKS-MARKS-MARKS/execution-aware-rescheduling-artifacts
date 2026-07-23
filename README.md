# Experimental Artifacts for Execution-Aware Multi-Robot Rescheduling

This repository contains the experimental artifacts associated with the paper:

**Execution-Aware Rescheduling for Multi-Robot Inspection with Alternative Service Locations**

## Scope

The repository provides:

- formal run-level outputs from the controlled simulation study;
- aggregate tables used for the reported numerical comparisons;
- instance, scenario, event, and experiment configuration files where available;
- source data and vector figures associated with the experimental results;
- aggregation and plotting scripts for paper Tables II--III and Figs. 3--4;
- metric definitions, numerical-claim audits, and integrity checks.

## Experimental matrix

The study comprises 297 simulation runs covering:

- three joint task/robot scales;
- uniform and clustered spatial layouts;
- task arrival, service-location invalidation, and robot failure;
- event progress values of 25%, 50%, and 75%;
- three random seeds;
- four rescheduling methods.

For every seeded configuration, the pre-event static plan is optimized from
an active-only solver instance. Inactive tasks and their candidate locations
are retained in a separate arrival pool and cannot influence that static
optimization. The formal arrival pool contains 10% as many tasks as the
active set, and a task-arrival event releases the entire pool.

## Main data

- `data/raw/`: run-level formal outputs.
- `data/summaries/`: aggregate method, scale, progress, and objective comparisons.
- `configurations/`: released experimental inputs and manifests.
- `figures/experiment_tradeoffs.*` and `figures/progress_sensitivity.*`:
  current experimental result figures.
- `scripts/`: read-only paper aggregation, table export, and plotting code.
- `documentation/`: artifact scope and numerical-claim audits.
- `checksums/SHA256SUMS.txt`: SHA-256 hashes of released files.

## Reproduce the paper aggregates

The reproduction entry point reads only
`data/raw/formal_release_raw.csv`. It validates the 297-row active-only
Release matrix, reconstructs the common-feasible primary set and paper
metrics, and generates Tables II--III and Figs. 3--4 under the ignored
`generated/` directory:

```text
python -m pip install -r requirements.txt
python scripts/reproduce_paper_artifacts.py
```

Expected outputs include:

- `generated/metrics/formal_release_paper_metrics.json`;
- `generated/tables/event_tradeoff.tex` and `method_results.tex`;
- CSV data for both tables and both figures;
- `generated/figures/experiment_tradeoffs.pdf/.svg`;
- `generated/figures/progress_sensitivity.pdf/.svg`;
- `generated/reproduction_summary.json`.

The scripts require Python 3.8 or later, Matplotlib 3.7--3.x, and Times New
Roman to reproduce the manuscript font. They use relative paths, make no
network requests, do not invoke a solver, and do not overwrite the released
run-level outputs.

Percentage changes reported by the scripts compare aggregate arithmetic
means:

```text
(baseline mean - alternative mean) / baseline mean * 100
```

They are not means of per-case percentages.

## Artifact limitation

This release does **not** include the optimization source code, proprietary or
legacy implementation files, compiled executables, or scripts for rerunning
the optimization algorithms.

The artifact supports traceability and independent reproduction of the paper
aggregates, tables, and experimental figures from the published run-level
outputs. It does not support rerunning the optimization algorithms from
source.

## Reported outcomes

The released data include:

- 99/99 successful task-arrival cases;
- 99/99 successful service-location-invalidation cases;
- 75/99 successful robot-failure cases;
- 24 structurally infeasible robot-failure runs under the stated
  robot-dependent reachability model.

## Citation

Citation metadata are provided in `CITATION.cff`.

## License

The released experimental data and documentation are provided under the
Creative Commons Attribution 4.0 International license.
