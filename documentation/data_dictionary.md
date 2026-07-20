# Data Dictionary

The precise set of columns may vary among the released CSV files.

| Field | Meaning | Unit |
|---|---|---|
| run_id | Unique formal experiment identifier | -- |
| instance | Instance identifier | -- |
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

## Aggregation rules

- Makespan, replanning time, and plan-change means are computed over successful
  runs unless otherwise stated.
- Recovery rates include structurally infeasible cases.
- Forced replacement of an unavailable service location is excluded from the
  optional service-location-change count.
- Error bars in the paper denote one standard deviation, not confidence
  intervals.
