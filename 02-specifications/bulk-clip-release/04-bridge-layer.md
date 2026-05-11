# 04 - Bridge layer

> Read [`../master-batch-mixing/04-bridge-layer.md`](../master-batch-mixing/04-bridge-layer.md) for the shared mapping engine. Bulk Clip Release is unusual because a direct whitelisted helper exists alongside the declarative mapping.

## Mapping seed

`seed_bulk_clip_release_mapping()` creates:

| Console field | Legacy field |
|---|---|
| `metadata.reference_id` | `reference_id` |
| `metadata.run_as` | `employee` |
| `posting_date` | `release_date` |
| `release_data.clips` | child `sheeting_clip` |
| `release_data.clips` | child `barcode` |

## Field-name drift

Legacy `Clip Release Item` fields are:

| Legacy child field | Exists? |
|---|---|
| `clip_name` | yes |
| `compound` | yes |
| `clip_barcode` | yes |
| `spp_batch_number` | yes |
| `item_clip_mapping_id` | yes |

The seeder maps to `sheeting_clip` and `barcode`, which are not fields on the legacy child JSON. This is a stronger drift than Cut Bit's `spp_batch_no` issue: unless the mapping engine or legacy meta tolerates unknown child fields, declarative creation of `Bulk Clip Release` rows cannot populate the intended child table correctly.

## Direct Bridge helper

`sync_api.py::bulk_release_clips(barcodes)` is simpler and likely closer to the real release primitive:

```python
targets = frappe.db.get_all(
    "Item Clip Mapping",
    filters={
        "sheeting_clip": ["in", barcodes],
        "is_retired": 0
    },
    pluck="name"
)
```

It then sets each target mapping `is_retired = 1` and commits.

## Barcode/name drift

Bridge direct helper filters `Item Clip Mapping.sheeting_clip IN barcodes`. Dash sends scanned barcode text (`clip_name: barcode`). Legacy Desk validation resolves `Sheeting Clip` by `barcode_text` first. If physical barcode text is not equal to the legacy `Sheeting Clip.name`, the direct helper misses rows.

This mirrors a known class of drift:

| Layer | Value |
|---|---|
| Dash | barcode text |
| Legacy `Sheeting Clip` | document name |
| Legacy `Item Clip Mapping.sheeting_clip` | document name |

The direct Bridge helper should be tested with barcode text that differs from doc name before any code is trusted.

## `sync_process_transaction` path

There is an `elif process_type == "BULK_CLIP_RELEASE": pass` hook in the normal document-creation flow. No `populate_bulk_clip_release_fields` exists. That means the mapping seeder must be accurate if the document path is used.

Given the field drift above, the direct helper may work for same-name clips, while the declarative doc path is suspect.

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add a `populate_bulk_clip_release_fields` resolver | Medium/high; needs tests |
| Fix mapping fields to legacy child JSON | High-value, code/test task |
| Resolve barcode text to `Sheeting Clip.name` inside direct helper | High-value, code/test task |
| Keep direct helper only | Low complexity, but bypasses Legacy audit document |
