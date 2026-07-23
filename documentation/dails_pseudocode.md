# Execution-aware D-AILS pseudocode

The pseudocode below follows the released implementation and its formal
driver. It describes the minimum-makespan mode; the disruption-aware mode
uses the same control flow with the fixed plan-change penalties reported in
the paper.

```text
INPUT
    execution state with incumbent plan
    active-only static plan and fixed event realization
    scenario seed and optional independent algorithm seed
    time and iteration limits

BUILD RESIDUAL STATE
    keep every completed route prefix immutable
    use each operational robot's current node as its fixed virtual depot
    retain each robot's designated return depot
    release only unfinished required tasks
    prohibit failed robots from receiving future tasks
    reject the instance if a required residual task has no available,
        reachable service location for any operational robot

FEASIBILITY-FIRST INITIALIZATION
    remove invalid mutable-suffix visits
    greedily insert every pending task using operational robots and
        available/reachable candidate locations
    if complete repair fails: report structural infeasibility
    apply outer frozen-suffix local search
        (candidate change, relocate, swap, within-route 2-opt)
    set the resulting feasible plan as the D-AILS input

INITIALIZE D-AILS
    apply bounded inner frozen-suffix local search to the input plan
    current <- refined input
    best <- current
    set all destroy and repair weights to 1
    initialize Metropolis temperature
    initialize the algorithm RNG from algorithm_seed when supplied,
        otherwise from scenario_seed

FOR iteration = 1 ... iteration_limit
    stop if elapsed D-AILS time reaches time_limit

    update reachable stagnation controls
        reheat once after 500 iterations without a new best
        (the 1200 massive-destruction and 2500 restart thresholds are
         unreachable under the formal 1000-iteration cap)

    independently select one destroy operator and one repair operator
        using weight-proportional roulette wheels
    determine removal count from mutable-task count and stagnation

    destroy only tasks after completed-prefix boundaries
        never remove completed tasks
        never move virtual depots or designated return depots

    repair all removed tasks
        use only operational robots
        use only available and robot-reachable candidate locations
        insert only after frozen boundaries and before return depots
    if repair is complete and feasible
        apply bounded inner frozen-suffix local search
        validate frozen prefixes, task coverage, robot status,
            candidate availability/reachability, and route structure
        apply Metropolis acceptance to update current
        if candidate improves best: best <- candidate

    assign reward 0/1/4/8 for rejected/accepted non-improving/
        current-improving/new-best outcome
    every 50 iterations, update used operator weights
    cool the temperature

RETURN best only if it remains a complete feasible plan
```

Completed prefixes are excluded from every destroy and local-search
neighborhood. Virtual depots and designated return depots are fixed. Failed
robots retain their incurred completed-prefix cost but receive no residual
tasks.
