# 07 — Out of scope

| Item | Reason |
|---|---|
| PLC or machine sensor integration | Legacy process is scan/manual-entry driven. |
| Real-time cavity-level production analytics | MPE records lot-level production; cavity analytics is a separate program. |
| Predictive maintenance from reason codes | Reason codes are captured but maintenance workflow is outside this pack. |
| Customer labeling / packing rules | Downstream packing/dispatch owns customer labels. |
| Rewriting batch-number policy | Requirement preserves legacy generator contract unless process owner approves change. |
| Relaxing inspection prerequisites | Line + Patrol gate is a current legacy invariant. |
| Combining MPE with Inspection Entry | Separate identities are required for refactor analysis. |

## Related processes

| Related process | Folder |
|---|---|
| Inspection Entry | `01-requirements/inspection-entry/` |
| Blank Bin Issue | `01-requirements/blank-bin-issue/` |
| Work Planning | `01-requirements/work-planning/` |
| Add On Work Planning | `01-requirements/add-on-work-planning/` |

