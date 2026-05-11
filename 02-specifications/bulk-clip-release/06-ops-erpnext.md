# 06 - Ops ERPNext

> Read [`../master-batch-mixing/06-ops-erpnext.md`](../master-batch-mixing/06-ops-erpnext.md) for generic engine behavior. Bulk Clip Release has a dedicated handler and does not need the generic engine.

## Dispatch

`process_transaction` routes:

```python
elif process_code == "BULK_CLIP_RELEASE":
    clips = context.get("release_data", {}).get("clips") or []
    return bulk_release_clips(barcodes=clips)
```

The handler receives only a list of barcodes. It ignores the full payload, operator, and reference id.

## Validation helper

`validate_clip_for_release(barcode)` resolves:

| Step | Behavior |
|---|---|
| 1 | Find `Sheeting Clip` by `barcode_text`, fallback direct doc name |
| 2 | Find active `Item Clip Mapping` for that clip |
| 3 | Return material mapping or Failed |

Dash does not call this directly; Dash uses Console's local `validate_clip_barcode` for instant feedback.

## Bulk release handler

`bulk_release_clips(barcodes=None)`:

| Step | Behavior |
|---|---|
| 1 | Parse JSON string list if needed |
| 2 | For each barcode, resolve `Sheeting Clip` by `barcode_text`, fallback direct name |
| 3 | Update all active `Item Clip Mapping` rows for that clip to `is_retired = 1` |
| 4 | Return `impacted_clips` list |

Unlike Cut Bit Transfer, there is no Stock Entry creation here. The "transaction" is state mutation on clip mappings.

## Response shape

| Field | Meaning |
|---|---|
| `status` | `Success` or `Failed` |
| `impacted_clips` | Resolved clip names |
| `message` | Count of released clips |

Console's standard post-step cache update path looks for `impacted_clips`; however, BCR local mirror behavior is currently split between the doctype callback and the direct relay helper.

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add reference id logging | Low/medium |
| Return barcode + clip name pairs | Low/high-value |
| Retire by barcode without resolving clip name | High; barcode/doc-name drift |
| Convert to generic engine action | Medium; current dedicated handler is clearer |
