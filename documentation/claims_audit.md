# Final quantitative claims audit

All final experimental values are derived from the refreshed 297-run Release dataset generated on 2026-07-23 after active-only pre-event static planning.

| Claim family | Final value(s) | Authoritative source |
|---|---|---|
| Experiment matrix | 297 runs | `formal_release_raw.csv` |
| Event recovery | arrival 99/99; invalidation 99/99; failure 75/99 | `formal_release_summary.csv`, `formal_release_paper_metrics.json` |
| Structural failures | 24 `NO_FEASIBLE_INSERTION` outcomes, confined to six S-U/S-C robot-failure scenario cases and shared by all methods | `formal_release_raw.csv` |
| Minimum-makespan comparison | 66 common feasible cases per method; 91.67% feasible rate | `formal_release_paper_metrics.json` |
| Mean maximum cumulative route cost | Greedy 144.710, Greedy+LS 144.276, D-AILS 141.705, Global Replan 146.073 | Arithmetic means over the same 66 common cases |
| Mean online replanning time | Greedy 4.163, Greedy+LS 13.344, D-AILS 1077.587, Global Replan 1188.071 ms | Same common-case filter |
| Mean plan-change counts | Greedy: reassigned 1.955, locations 1.333, edges 11.091; Greedy+LS: reassigned 1.955, locations 2.015, edges 13.091; D-AILS: reassigned 2.682, locations 3.288, edges 22.061; Global Replan: reassigned 4.727, locations 10.530, edges 44.758 | Same common-case filter |
| D-AILS aggregate-mean reduction vs Greedy | 2.08% | `formal_release_paper_metrics.json` |
| Objective trade-off on M-C at 50% | changed edges 21.444 to 7.667 (-64.25%); reassignment 3.111 to 2.222 (-28.6%); cost 134.719 to 136.675 (+1.45%) | `formal_release_disruption_case.csv`, `formal_release_paper_metrics.json` |
| Progress sensitivity on M-C (25%, 50%, 75%) | Greedy 4.332, 1.850, 0.834 ms; Greedy+LS 12.061, 7.953, 5.154 ms; D-AILS 1062.640, 1030.800, 1009.850 ms; Global Replan 1156.432, 1079.790, 1027.467 ms | `formal_release_progress_sensitivity.csv` |
| Scale timing at 50% (S, M, L) | Greedy 0.197, 1.805, 10.745 ms; Greedy+LS 2.046, 8.086, 30.872 ms; D-AILS 1003.086, 1025.093, 1221.091 ms; Global Replan 1005.790, 1082.100, 1511.683 ms | `formal_release_scalability.csv` |
| Platform | Windows 11; i7-13620H; 15.8 GB RAM; MSVC 19.43; one algorithm thread; x64 Release | `platform_metadata.txt` |

Figure 3 and Table III use the same 66 common feasible cases and arithmetic means. Percentage reduction is computed from unrounded aggregate means as `(baseline - alternative) / baseline * 100`; increase uses `(alternative - baseline) / baseline * 100`. These are not means of per-case percentages.
