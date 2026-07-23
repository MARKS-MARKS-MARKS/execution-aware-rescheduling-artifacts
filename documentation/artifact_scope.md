# Artifact Scope

## Included

- formal run-level experimental results;
- aggregate result tables;
- experimental instance and event configuration files where available;
- experimental figures and figure source data;
- paired full and active-only static-optimization instance definitions;
- active-only release integrity and old-vs-new event-target audits;
- metric and numerical-claim audit documentation;
- read-only aggregation scripts for the paper metrics and Tables II--III;
- plotting scripts for paper Figs. 3--4;
- a unified run-level-output reproduction entry point;
- 1320 additional fixed-scenario algorithm-seed runs, their summaries, and
  an independently executable aggregation script;
- frozen event manifests and active-only static-plan caches used by the
  algorithm-seed study;
- D-AILS formal parameters and implementation-faithful pseudocode;
- a robustness protocol runner for use with a separately built compatible
  executable;
- SHA-256 integrity hashes.

## Not included

- optimization source code;
- C++ application, library, or header files;
- legacy or archived implementations;
- compiled binaries;
- build products;
- debugging logs;
- local development-environment files;
- third-party paper illustrations;
- the optimization executable or complete end-to-end algorithm reproduction.

## Reproducibility statement

The released artifact supports result traceability and independently rebuilds
the paper metrics, Tables II--III, and Figs. 3--4 from the published 297
active-only run-level outputs by running:

```text
python scripts/reproduce_paper_artifacts.py
```

The scripts never invoke the solver and write only to `generated/`. Because
the optimization implementation is not included, the artifact does not
provide complete end-to-end computational reproducibility of the 297 solver
runs.

The separate 1320-run robustness statistics can be rebuilt from the published
CSV and formal Greedy baseline by running:

```text
python scripts/aggregate_algorithm_seed_robustness.py
```

This reconstruction validates the released rows and writes only to
`generated/algorithm_seed_robustness/`. The protocol runner documents the
exact 66 x 2 x 10 command matrix but requires a separately built compatible
executable.
