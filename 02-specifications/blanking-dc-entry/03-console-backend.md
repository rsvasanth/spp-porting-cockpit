# 03 - Console backend

> Read [`../master-batch-mixing/03-console-backend.md`](../master-batch-mixing/03-console-backend.md) for `_safe_local_create`, `initialize_submission`, `execute_submission_step`, and standard callback routing. Blanking DC Entry uses local create, but callback routing is currently incomplete.

## Validators

| Function | Behavior |
|---|---|
| `validate_blanking_clip_barcode(barcode, item_to_produce)` | Resolves active `Console Item Clip Mapping` by scanned clip barcode |
| `validate_blanking_bin_barcode(barcode)` | Resolves active `Console Blanking Bin` and rejects bins already in active mapping |

Clip validation returns `sheeting_clip`, `compound`, `spp_batch_number`, `qty`, and `mapping_name`. It does **not** currently validate BOM compatibility with `item_to_produce`, despite accepting that argument.

Bin validation checks `Console Item Bin Mapping` using:

```python
{"blanking__bin": bin_doc.name, "is_retired": 0}
```

Dash then sends `bin_code: activeBinData.bin_code`, which is `bin_doc.name`, not necessarily physical barcode text.

## Local create

`initialize_submission` has the local-create branch:

```python
elif process_code == "BLANKING_DC_ENTRY":
    create_local_blanking_dc_entry(prelim_payload, reference_id)
```

`create_local_blanking_dc_entry` writes:

| Parent field | Source |
|---|---|
| `entry_date` | posting date or today |
| `posting_date` / `posting_time` | `_backdate_fields(ctx)` |
| `operator_id` | `operator_id` or `metadata.run_as` |
| `item_to_produce` | payload item or `metadata.produced_item` |
| `payload_snapshot` | full transaction payload |

Child rows use `_BLANKING_DC_ITEM_KEYMAP`, which matches the current Dash row keys.

## Console process-master side effects

After local create, Console runs:

| Helper | Effect |
|---|---|
| `_write_bin_mappings_for_blanking_dc` | Creates `Console Item Bin Mapping` for each bin |
| `_consume_clips_for_blanking_dc` | Deducts net weight from active `Console Item Clip Mapping` |

Clip consumption retires a clip mapping only when the remaining qty reaches zero:

```python
new_qty = max(0, flt(mapping.qty) - net_weight)
update_vals = {"qty": new_qty}
if new_qty == 0:
    update_vals["is_retired"] = 1
```

This is the inverse of Bulk Clip Release's full retirement ceremony: BDE supports partial clip consumption.

## Controller drift

`ConsoleBlankingDCEntry.apply_bridge_result` has this signature:

```python
def apply_bridge_result(self, intent, target, status, payload):
```

The shared callback router calls:

```python
doc.apply_bridge_result(target, status, remote_name, detailed_err_val)
```

If Blanking were added to `update_local_domain_record` as-is, arguments would be shifted. Today this is masked because `BLANKING_DC_ENTRY` is missing from `legacy_doctype_map`, so callbacks return early and do not call the controller method.

## Callback routing drift

`update_local_domain_record` omits `BLANKING_DC_ENTRY`. This means Ops/Legacy target logs can complete, but the local `Console Blanking DC Entry` row will not be updated through the standard callback path.

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add Blanking to callback map | Required, but must also fix method signature |
| Add BOM validation to Console clip scan | Medium; needs Console BOM assumptions |
| Change clip consumption timing | High; affects partial consumption |
| Remove local bin mapping write | High; downstream scan availability depends on it |
