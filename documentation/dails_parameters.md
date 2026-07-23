# D-AILS formal parameters

This document records the parameters used by the formal Release driver. The
manuscript's 297-run benchmark is unchanged. The additional 1320-run study
changes only the algorithm seed; all values below remain fixed.

## Search sequence and budgets

| Component | Formal value | Source in the implementation | Driver override? |
|---|---:|---|---|
| Greedy suffix repair | minimum-makespan or disruption-aware insertion objective | `apps/experiment_main.cpp`, repair setup | Objective-dependent |
| Outer frozen-suffix local search | 3 passes, 50 move evaluations, 20 ms | `apps/experiment_main.cpp`, `local_options` | Yes |
| D-AILS stopping limits | 1000 ms or 1000 iterations, whichever occurs first | formal matrix and `apps/experiment_main.cpp` | Yes; library defaults are 5000 ms/5000 iterations |
| Inner frozen-suffix local search | 1 pass, 1 move evaluation, 2 ms | `apps/experiment_main.cpp`, D-AILS options | Yes |
| Local-search selection | best improvement | `include/cac/solver/FrozenSuffixLocalSearch.h` | No |
| Local-search neighborhoods | candidate change, relocate, swap, within-route 2-opt | `include/cac/solver/FrozenSuffixLocalSearch.h` | No |
| Comparison tolerance | \(10^{-9}\) | `include/cac/solver/FrozenSuffixLocalSearch.h` | No |
| Accepted-move validation | enabled | `include/cac/solver/FrozenSuffixLocalSearch.h` | No |

The outer local search is applied before D-AILS. D-AILS then applies the
inner local-search limits both to its initial refinement and to each repaired
candidate. Global Replan first reconstructs the mutable residual suffix, then
uses the same outer local search and D-AILS phases.

## Destroy and repair

| Parameter | Formal value | Source |
|---|---:|---|
| Destroy operators | random, critical-route, worst-contribution, related, route-segment | `src/solver/AdaptiveOperatorSelector.cpp` |
| Repair operators | best insertion, regret-2 insertion, disruption-aware regret-2 | `src/solver/AdaptiveOperatorSelector.cpp` |
| Minimum removal fraction | 0.05 | `include/cac/solver/DynamicAilsOptions.h` |
| Initial/base removal fraction | 0.15 | `include/cac/solver/DynamicAilsOptions.h` |
| Maximum removal fraction | 0.45 | `include/cac/solver/DynamicAilsOptions.h` |
| Minimum removed tasks | 1 | `include/cac/solver/DynamicAilsOptions.h` |
| Related-removal weights | distance 1.0; same robot 1.0; route position 0.5; same incumbent robot 0.5; rework/task type 0.5 | `include/cac/solver/DynamicDestroyOperators.h` |

Outside massive destruction, the removal fraction increases linearly from
0.15 toward 0.45 as the no-best-improvement count approaches 1200. The count
is rounded up after multiplication by the number of eligible mutable tasks
and is clamped to at least one and at most the eligible count.

## Adaptive operator selection

| Parameter | Formal value | Source |
|---|---:|---|
| Initial operator weight | 1.0 | `include/cac/solver/AdaptiveOperatorSelector.h` |
| Weight-update segment | 50 iterations | same |
| Reaction factor | 0.2 | same |
| Minimum operator weight | 0.05 | same |
| Rejected reward | 0 | same |
| Accepted non-improving reward | 1 | same |
| Current-plan improvement reward | 4 | same |
| New-best-plan reward | 8 | same |

Destroy and repair operators are selected independently by weight-proportional
roulette wheels. At the end of each 50-iteration segment, each used
operator's weight becomes

```text
max(0.05, 0.8 * old_weight + 0.2 * mean_segment_reward).
```

Unused weights are retained.

## Metropolis acceptance and stagnation

| Parameter | Formal value | Source |
|---|---:|---|
| Initial deterioration ratio | 0.01 | `include/cac/solver/MetropolisAcceptance.h` |
| Initial acceptance probability | 0.5 | same |
| Initial temperature | \(-0.01\max(1,|f_0|)/\log(0.5)\) | `src/solver/MetropolisAcceptance.cpp` |
| Cooling multiplier | 0.9995 per iteration | `include/cac/solver/MetropolisAcceptance.h` |
| Minimum temperature | \(10^{-9}\) | same |
| Reheat factor | 0.25 | same |
| Reheat threshold | 500 iterations without a new best | `include/cac/solver/DynamicAilsOptions.h` |
| Massive-destruction threshold | 1200 iterations without a new best | same |
| Soft-restart threshold | 2500 iterations without a new best | same |

The initial-temperature formula makes a deterioration equal to 1% of the
initial scalar objective have Metropolis acceptance probability 0.5. Better
candidates are accepted directly; equivalent candidates use the deterministic
plan-signature tie break.

With the formal 1000-iteration cap, the 500-iteration reheat is reachable.
The 1200-iteration massive-destruction and 2500-iteration soft-restart
thresholds cannot be reached in a formal run. They remain implementation
defaults for longer runs and are not presented as active mechanisms in the
formal results.

## Seed separation

The scenario seed controls instance/scenario identity, the active-only static
plan cache, event manifest, and execution-progress state. When
`--algorithm-seed` is supplied, it controls only the `std::mt19937_64` streams
used by D-AILS operator selection, randomized destroy operations, Metropolis
draws, route-segment selection, and the randomized Global Replan destruction.

If `--algorithm-seed` is absent, the algorithm RNG uses the scenario seed,
preserving the original formal behavior and output schema. The additional
robustness study uses algorithm seeds 1000--1009 while holding every scenario
asset fixed.
