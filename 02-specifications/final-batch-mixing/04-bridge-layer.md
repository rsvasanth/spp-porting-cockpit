# 04 — Bridge layer

> Refer to [`../master-batch-mixing/04-bridge-layer.md`](../master-batch-mixing/04-bridge-layer.md)
> for the full mapping engine walkthrough. FB shares the same Bridge
> entry (`sync_process_transaction`) and the same mapping rows.

## Shared mapping with MB Mixing

The Console mapping seeder calls `_upsert_mapping` twice with the **same
`field_mappings` list**:

```python
# console_mapping_seeder.py:159-160
_upsert_mapping("MASTER_BATCH_MIXING", "Delivery Challan Receipt", field_mappings)
_upsert_mapping("FINAL_BATCH_MIXING",  "Delivery Challan Receipt", field_mappings)
```

This produces two `Legacy Sync Mapping` rows (one per process_code) but
with identical `field_mappings` child tables. The Bridge sees two distinct
mapping configs but they resolve to the same field-level behavior.

## The value-map difference

The `inward_material_type` mapping row applies to both:

```python
inward_material_map = json.dumps({
    "Master Batch Mixing": "Master Batch",
    "Final Batch Mixing":  "Compound",
})
field_mappings = [
    ...
    {"console_field": "config.operation", "legacy_field": "inward_material_type",
     "value_map": inward_material_map, "default_value": "Compound"},
    ...
]
```

For an FB payload, `config.operation` is `"Final Batch Mixing"`, so the
value-map resolves it to `"Compound"`. This is what triggers legacy's
`validate_final_batches` to take the **FB branch** (see `05-legacy-erpnext.md`).

**The defensive default (`"Compound"`) means a payload with an unrecognised
operation silently goes into the FB path on legacy.** This is the silent
bug surface mentioned in MB spec's `10-risks-and-decisions.md` decision #6
— for FB the default is benign (same as expected output) but it masks
bugs for other process types that might accidentally use this mapping
(no current consumers, but the risk is structural).

## FB-specific payload elements that flow to Legacy

| Console payload path | Legacy DCR field | FB-specific consideration |
|---|---|---|
| `stock_entry_data.consumption_items[0].is_batch_item = 1` | `dc_items[0].is_batch_item` | This triggers the "batched FB" path (`create_master_batch_stock` + `create_compound_stock`) in `validate_final_batches`; if absent or 0, takes simpler `create_wo_final_batch_mixing` path |
| `stock_entry_data.consumption_items[0].mix_barcode` (the MB's barcode) | `dc_items[0].scan_barcode` | The same field used by MB to push its own `bridge_mix_barcode`; for FB this is the **input MB's** barcode, used by `create_master_batch_stock` to look up the MB's batch |
| `metadata.produced_item` | `dc_items[*].item_to_manufacture` | The Compound being produced (FG item) — broadcast to every child row |
| `config.operation = "Final Batch Mixing"` | `operation` (header + child) | Drives value-map and the `Mixing Operation` master data lookup |

## Idempotency — identical to MB

`find_existing_record` for `FINAL_BATCH_MIXING` falls through to the
generic `frappe.db.exists("Delivery Challan Receipt", {"reference_id": ...})`
check. Same behavior as MB.

## Bridge post-submit warning

The Bridge checks `legacy_doc.stock_entry_reference` after submit and warns
if empty. For FB, `stock_entry_reference` gets populated by the
`make_stock_entry_final_batch` call inside `create_wo_final_batch_mixing`
— it appends the SE name via `update_stock_ref`. **If this warning fires
for an FB submission, it likely means the Work Order or Job Card creation
failed silently and the SE was never made** — investigation point for
Hermes Reviewer worker.

## What Hermes workers can change

Same advice as MB. **Additional caveat:** any mapping change ripples
through both `MASTER_BATCH_MIXING` and `FINAL_BATCH_MIXING` because they
share the `field_mappings` list. If you need to diverge them, switch from
the shared `_upsert_mapping` calls to two separate seed functions.
