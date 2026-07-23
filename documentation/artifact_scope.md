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
- solver rerun scripts and complete end-to-end algorithm reproduction.

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
