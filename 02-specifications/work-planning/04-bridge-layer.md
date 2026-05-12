# 04 — Bridge layer

## Target behavior

Bridge must map Console Work Planning to Legacy `Work Planning`, not `Add On Work Planning`.

## Required mapping

| Console field | Legacy field |
| --- | --- |
| `date` | `date` |
| `shift_type` | `shift_type` |
| `shift_series` | `shift_series` |
| `shift_time` | `shift_time` |
| `scan_supervisor` | `scan_supervisor` |
| `supervisor_id` | `supervisor_id` |
| `supervisor_name` | `supervisor_name` |
| `items[].item` | `items[].item` |
| `items[].work_station` | `items[].work_station` |
| `items[].mould` | `items[].mould` |
| `items[].bom` | `items[].bom` |

## Legacy child table

| Legacy child | Purpose |
| --- | --- |
| `Work Plan Item` | Holds product/workstation/mould/BOM and later Job Card / Lot # |

## Special concern: Work Order / Job Card creation

Legacy creates Work Orders and Job Cards through `submit_workplan()` / `on_submit_value()` rather than plain insert-only behavior. Bridge design must choose one of two approaches:

| Approach | Notes |
| --- | --- |
| Insert/submit Work Planning, then call helper | Closest to Legacy behavior |
| Implement dedicated whitelisted method | Safer for atomic create-and-return |

The previous Add On spec proposed `create_planning_with_jobcards`; for Work Planning this must target `Work Planning` and `Work Plan Item`, not Add On doctypes.

## Idempotency requirements

| Risk | Mitigation |
| --- | --- |
| Duplicate Work Planning for shift | Pre-check date + shift series |
| Duplicate Work Orders / Job Cards on retry | Use reference ID or existing child Job Card checks |
| Lot # regeneration on retry | Reuse existing Job Card / child row values |

## Current drift

No Bridge mapping for `WORK_PLANNING` is documented in current cockpit specs. Add one explicitly rather than routing through Add On.
