# Data Dictionary

The precise set of columns may vary among the released CSV files.

| Field | Meaning | Unit |
|---|---|---|
| run_id | Unique formal experiment identifier | -- |
| instance | Instance identifier | -- |
| static_instance | Active-only instance passed to the pre-event static solver | -- |
| static_plan_identifier | Shared active-only static-plan/seed identifier | -- |
| static_input_groups | Number of active groups passed to the static solver | count |
| method | Rescheduling method | -- |
| event_type | Dynamic event type | -- |
| progress | Execution progress when the event is applied | fraction |
| seed | Random seed | -- |
| status | Successful or structurally infeasible terminal outcome | -- |
| makespan | Dynamic completion makespan | normalized distance/time |
| replanning_time_ms | Online replanning time after event application | ms |
| reassigned_tasks | Tasks reassigned to another robot | count |
| changed_locations | Optional service-location changes | count |
| changed_edges | Changed directed residual-suffix edges | count |

The full instance retains both active tasks and the inactive arrival pool.
The separate `*.active.gtsp` input contains exactly the active groups and
candidate nodes used by the pre-event static optimizer.

## Aggregation rules

- Makespan, replanning time, and plan-change means are computed over successful
  runs unless otherwise stated.
- Recovery rates include structurally infeasible cases.
- Forced replacement of an unavailable service location is excluded from the
  optional service-location-change count.
- Error bars in the paper denote one standard deviation, not confidence
  intervals.
