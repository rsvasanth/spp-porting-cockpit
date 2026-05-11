# 07 - End-to-end flow

## Intended live-feedback path

| Step | System | Action |
|---|---|---|
| 1 | Dash | Operator selects Mill Operator |
| 2 | Dash | Operator scans clip barcode |
| 3 | Console API | `validate_clip_barcode` verifies local active mapping |
| 4 | Dash | Adds clip to `scannedClips` |
| 5 | Dash | Submits `release_data.clips[]` |
| 6 | Console API | `initialize_submission` builds target logs |
| 7 | Dash | Calls `execute_submission_step` for Legacy and Ops in parallel |
| 8 | Ops | `bulk_release_clips(barcodes=clips)` retires Ops mappings |
| 9 | Legacy | Bridge retires Legacy mappings or creates legacy BCR doc |
| 10 | Console | Local BCR row should aggregate and retire Console mirror after Legacy ack |

## Current observed blockers

| Blocker | Evidence |
|---|---|
| Dash sends `metadata.process_type`, not `metadata.process_code` | `build_transaction_payload` requires `process_code` |
| No local BCR audit creation in `initialize_submission` | no `create_local_bulk_clip_release` branch/function |
| No callback routing for `BULK_CLIP_RELEASE` | `legacy_doctype_map` omits it |
| Bridge mapping child fields don't match Legacy child JSON | maps to `sheeting_clip` / `barcode`; legacy child has `clip_name` / `clip_barcode` |

## Direct relay fallback path

`Console api.py::bulk_release_clips(barcodes)` has a separate path:

| Step | System | Action |
|---|---|---|
| 1 | Console | Retires local Console mapping immediately |
| 2 | Ops | Calls Ops `bulk_release_clips` |
| 3 | Legacy | If Ops success, calls Bridge `bulk_release_clips` |

This path is simpler but does not create per-target Console Transaction Logs or a `Console Bulk Clip Release` parent document.

## Success criteria

| Site | Expected state after release |
|---|---|
| Console | `Console Item Clip Mapping.is_retired = 1` for released clips |
| Ops | `Item Clip Mapping.is_retired = 1` for released clips |
| Legacy | `Item Clip Mapping.is_retired = 1` for released clips |
| Dash | Success modal shows target completion |

## Failure cases

| Failure | Expected behavior |
|---|---|
| Unknown barcode | Scan rejected before submit |
| Already retired mapping | Scan rejected before submit |
| Duplicate in draft | Scan rejected |
| Ops succeeds, Legacy fails | Console should show Partial and not pretend both sites released |
| Console mirror retirement fails after Legacy ack | Log recoverable mirror drift |

## My read

The intended design is sound: BCR is the clip state-machine gate. The current source needs a verification/fix pass before it should be treated as production-clean because the Dash payload, local audit doctype, mapping seeder, and callback routing are not fully aligned.
