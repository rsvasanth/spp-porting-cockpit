# 01 - Business context

## Process position

Bulk Clip Release sits between Sheeting and Blanking.

```text
Sheeting Process
  -> Console / Legacy Item Clip Mapping is active
  -> Bulk Clip Release
  -> Item Clip Mapping is retired/released
  -> Blanking DC Entry can consume the clip flow without double-release
```

The process is not a manufacturing step. It is a state transition for physical clips and their material mapping.

## Shop-floor meaning

| Term | Meaning |
|---|---|
| Clip | Physical sheeting clip with barcode |
| Active mapping | `Item Clip Mapping.is_retired = 0`; clip still occupied |
| Released clip | Mapping retired; clip is available/released for next stage |
| Bulk release | Operator scans many clips and releases them as one ceremony |

## State machine

| State | Stored as | Produced by | Consumed by |
|---|---|---|---|
| Occupied/sheeted | Active `Item Clip Mapping` | Sheeting Process | Bulk Clip Release scan validation |
| Released | `is_retired = 1` | Bulk Clip Release | Blanking flow / clip reuse checks |

This is why the process is state-machine work, not stock-ledger work. The handler may live near transaction code, but the core effect is mapping retirement.

## Actors

| Actor | Responsibility |
|---|---|
| Mill Operator | Selects operator and scans clips |
| Console Dash | Prevents duplicate scans in one draft batch |
| Console backend | Validates active local mirror mapping |
| Legacy Bridge | Retires Legacy `Item Clip Mapping` rows |
| Ops app | Retires Ops `Item Clip Mapping` rows |

## Operational constraints

| Constraint | Why |
|---|---|
| Clip barcode must exist | Prevents phantom releases |
| Active mapping must exist | Already-released clips must not release again |
| Duplicate scans in same batch must be blocked | Avoids duplicate rows and duplicate messages |
| Release must hit both ERPs when sync strategy says Both | Legacy and Ops clip pools must stay aligned |
| Console mirror must be retired at the right point | Downstream scans depend on local active/retired state |

## Current implementation shape

There are two implementation lines on disk:

| Line | Evidence | Meaning |
|---|---|---|
| Doctype/controller path | `Console Bulk Clip Release` with `released_clips` and `apply_bridge_result` | Intended audit-first cockpit path |
| Direct relay path | `api.py::bulk_release_clips(barcodes)` | Older/simple helper that retires local mirror and calls Ops/Legacy directly |

The Dash currently calls `initialize_submission` / `execute_submission_step`, not the direct relay helper. The spec treats the doctype/controller path as the intended Wave 2 cockpit path and flags the routing drift.

## Cross-links

| Shared concept | Reference |
|---|---|
| Sheeting creates clip mappings | [`../sheeting-process/03-console-backend.md`](../sheeting-process/03-console-backend.md) |
| Cut Bit drift precedent | [`../cut-bit-transfer/10-risks-and-decisions.md`](../cut-bit-transfer/10-risks-and-decisions.md) |
| Shared orchestration | [`../master-batch-mixing/03-console-backend.md`](../master-batch-mixing/03-console-backend.md) |
