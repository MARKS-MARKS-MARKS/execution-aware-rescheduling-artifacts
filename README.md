# Experimental Artifacts for Execution-Aware Multi-Robot Rescheduling

This repository contains the experimental artifacts associated with the paper:

**Execution-Aware Rescheduling for Multi-Robot Inspection with Alternative Service Locations**

## Scope

The repository provides:

- formal run-level outputs from the controlled simulation study;
- aggregate tables used for the reported numerical comparisons;
- instance, scenario, event, and experiment configuration files where available;
- source data and vector figures associated with the experimental results;
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
- `documentation/`: artifact scope and numerical-claim audits.
- `checksums/SHA256SUMS.txt`: SHA-256 hashes of released files.

## Artifact limitation

This release does **not** include the optimization source code, proprietary or
legacy implementation files, compiled executables, or complete end-to-end
reproduction scripts.

The artifact supports traceability and independent verification of the
reported numerical values, but it does not currently support rerunning the
optimization algorithms from source.

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
