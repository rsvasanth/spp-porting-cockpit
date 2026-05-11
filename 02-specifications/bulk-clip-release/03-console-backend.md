# 03 - Console backend

> Read [`../master-batch-mixing/03-console-backend.md`](../master-batch-mixing/03-console-backend.md) for shared orchestration. Bulk Clip Release is mostly interesting because the current code does not fully connect its Console audit doctype to that shared path.

## Frontend-facing functions

| Function | Current role |
|---|---|
| `validate_clip_barcode(barcode, draft_barcodes=None)` | Per-scan validator used by Dash |
| `submit_bulk_release_clips(payload)` | Wrapper around `submit_process`, but Dash does not call it |
| `bulk_release_clips(barcodes=None)` | Direct relay helper near bottom of `api.py` |
| `validate_clip_for_release(barcode)` | Status-style wrapper around `validate_clip_barcode` |

## Scan validator

`validate_clip_barcode` reads only the local Console mirror:

| Check | Failure |
|---|---|
| Empty barcode | `Barcode is empty.` |
| Barcode already in draft list | `already scanned in this release` |
| No `Console Sheeting Clip` by `barcode_text` | `Invalid clip barcode` |
| No active `Console Item Clip Mapping` | `Clip ... is already released` |

Success shape:

```python
{
    "ok": True,
    "source_clip": sc_name,
    "item_code": mapping.compound,
    "batch_no": mapping.spp_batch_number,
    "spp_batch_no": mapping.spp_batch_number,
    "qty": flt(mapping.qty),
    "mapping_name": mapping.name,
}
```

This helper is correctly aligned with Dash's scan UI.

## Missing local-create path

`initialize_submission` creates local audit rows for MB, FB, Sheeting, Cut Bit, Blanking, and inspections. It does **not** include:

```python
elif process_code == "BULK_CLIP_RELEASE":
    create_local_bulk_clip_release(...)
```

There is also no `create_local_bulk_clip_release` function in `api.py`. This means the rich `Console Bulk Clip Release` doctype can be tested directly, but the current live-feedback orchestration does not obviously create a local BCR audit row.

## Missing callback routing

`update_local_domain_record` maps only:

```python
legacy_doctype_map = {
    "MASTER_BATCH_MIXING": "Console Master Batch Mixing",
    "FINAL_BATCH_MIXING":  "Console Final Batch Mixing",
    "SHEETING_PROCESS":    "Console Sheeting Process",
    "CUT_BIT_TRANSFER":    "Console Cut Bit Transfer",
}
```

`BULK_CLIP_RELEASE` is absent. Even if target logs complete, callbacks will not route to `Console Bulk Clip Release.apply_bridge_result` through the standard path.

## Console doctype/controller

The doctype is not a stub. It has real process-specific behavior:

| Hook/method | Behavior |
|---|---|
| `before_insert` | Stamps process code, submitted_by, posting date/time |
| `validate` | Enforces non-empty clips, duplicate rejection, active mappings |
| `_recompute_total_qty` | Sums child qty |
| `on_submit` | Ensures a pending Console Transaction Log exists |
| `apply_bridge_result` | Intent-aware per-leg aggregation and Legacy-ack mirror retirement |
| `_retire_clip_mappings` | Sets `Console Item Clip Mapping.is_retired=1` for released rows |

The controller's apply callback is not the byte-identical 5-step MB pattern. It is BCR-specific and intent-aware, with a mirror flip after Legacy success.

## Direct relay helper

`api.py::bulk_release_clips(barcodes)` does three things:

| Step | Behavior |
|---|---|
| 1 | Retires local Console Item Clip Mapping rows immediately |
| 2 | Calls Ops `bulk_release_clips` |
| 3 | If Ops succeeds, calls Legacy Bridge `bulk_release_clips` |

This helper does not create a `Console Bulk Clip Release` parent row and does not use per-target Transaction Logs. It is a different operational path from Dash's current live-feedback code.

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add `BULK_CLIP_RELEASE` to local create + callback routing | High-value, but code/test task |
| Align Dash payload with doctype fields | Medium; requires local create contract |
| Use direct `bulk_release_clips` helper from Dash | Medium; loses standard target-log orchestration |
| Move local mirror retirement earlier/later | High; affects double-release safety |
