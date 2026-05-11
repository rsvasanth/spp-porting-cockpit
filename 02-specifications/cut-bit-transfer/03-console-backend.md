# 03 - Console backend

> Read [`../master-batch-mixing/03-console-backend.md`](../master-batch-mixing/03-console-backend.md) for `initialize_submission`, `execute_submission_step`, `_safe_local_create`, and the 5-step `apply_bridge_result` pattern. Cut Bit Transfer shares those mechanics.

## Dispatch

`initialize_submission` routes non-inspection process code `CUT_BIT_TRANSFER` to:

```python
elif process_code == "CUT_BIT_TRANSFER":
    create_local_cut_bit_transfer(prelim_payload, reference_id)
```

`update_local_domain_record` maps the process to `Console Cut Bit Transfer`, so callbacks land on the local audit doctype rather than the unified inspection doctype.

## Wrapper: `submit_cut_bit_transfer(payload)`

This is the frontend-facing entry point. It is not a thin alias.

| Step | Behavior | Why it exists |
|---|---|---|
| 1 | Forces `metadata.process_code = "CUT_BIT_TRANSFER"` | Process template lookup and routing |
| 2 | Hoists `metadata.reference_id` to top-level `reference_id` | Shared idempotency path expects top-level too |
| 3 | Relays missing native batches through Ops `validate_cut_bit_asset` | Ops submit needs real ERPNext batch |
| 4 | Builds `stock_entry_data.items` with source + target rows | Makes template payload resolvable |
| 5 | Calls `submit_process(payload)` | Enters standard Console orchestrator |

The native-batch relay is load-bearing:

```python
if not it.get("native_batch_no") and not it.get("batch_no"):
    barcode = it.get("clip_name") or it.get("asset_id", "")
    if barcode:
        ops_res = call_ops_api(
            "shree_polymer_ops.api.validate_cut_bit_asset",
            barcode=barcode
        )
        if ops_res and ops_res.get("status") == "Success":
            it["native_batch_no"] = ops_res.get("native_batch_no", "")
```

Without this, Console-local mappings that return `native_batch_no = ""` can create a local audit row but fail the Ops dedicated handler.

## `stock_entry_data.items`

The wrapper emits two rows per scanned asset:

| Row | Key fields |
|---|---|
| Consumption | `s_warehouse`, `batch_no`, `scan_barcode`, `clip_name`, `asset_type`, `is_finished_item=0` |
| Production | `t_warehouse="Cutbit - SPP"`, `batch_no="Cutbit_<item_code>"`, `is_finished_item=1` |

This shape is useful for payload/template visibility, but Ops does not rely on the generic engine for CBT. Ops dispatches to a dedicated handler.

## Validation relay: `validate_cut_bit_asset(barcode)`

Console validation runs in this order:

| Priority | Source | Notes |
|---|---|---|
| 1 | `Console Sheeting Clip` by `barcode_text` then `Console Item Clip Mapping` | Resolves physical barcode to clip name first |
| 2 | `Console Item Bin Mapping` by `blanking__bin` | Bin barcode path |
| 3 | Ops relay | Backward compatibility and native batch resolution |
| 4 | Legacy Bridge relay | Final fallback |

For a local mapping hit, Console returns:

```python
{
    "status": "Success",
    "asset_type": asset_type,
    "asset_id": barcode,
    "mapping_name": mapping.name,
    "item_code": mapping.item_code,
    "spp_batch_number": mapping.spp_batch_number,
    "qty": mapping.qty,
    "available_qty": mapping.qty,
    "source_warehouse": source_warehouse,
    "native_batch_no": ""
}
```

The empty `native_batch_no` is intentional for Console-local mappings and is resolved later by the submit wrapper.

## `create_local_cut_bit_transfer(payload, reference_id)`

The local audit identity comes from `items[0]`, and the parent qty is an aggregate:

```python
items = ctx.get("items") or []
first = items[0] if items else {}
total_qty = sum(flt(i.get("qty")) for i in items)
```

Parent fields:

| Console field | Source |
|---|---|
| `item_code` | first item `item_code`, fallback context `item_code` |
| `batch_no` | first item `batch_no` or `native_batch_no` |
| `spp_batch_no` | first item `spp_batch_number` |
| `qty` | sum of all `items[].qty` |
| `from_warehouse` | first item `source_warehouse` |
| `to_warehouse` | template/config target warehouse |
| `operator_name` | `metadata.run_as` |
| `payload_snapshot` | full built payload |

Child rows use `_CUT_BIT_ITEM_KEYMAP`:

```python
_CUT_BIT_ITEM_KEYMAP = {
    "item_code": "item_code",
    "batch_no": "batch_no",
    "native_batch_no": "native_batch_no",
    "spp_batch_number": "spp_batch_number",
    "qty": "qty",
    "asset_id": "asset_id",
    "asset_type": "asset_type",
    "clip_name": "clip_name",
    "mapping_name": "mapping_name",
    "source_warehouse": "source_warehouse",
}
```

## Local mapping side effect

After `_safe_local_create`, Console calls `_write_clip_mappings_for_cut_bit`. The function name is misleading in current code: it is a Bin mapping consumption helper.

| Asset type | Current behavior |
|---|---|
| Clip | `continue`; no local retirement |
| Bin | Find active `Console Item Bin Mapping`; reduce qty or mark retired |

This is a plan-vs-reality delta worth preserving. Some test names still say "creates clip mappings", but current source comments say clips are retired at Blanking DC Entry, not at Cut Bit Transfer.

## Controller

`console_cut_bit_transfer.py` has the standard Wave 1 validate bypass:

```python
if self.flags.get("from_local_cache"):
    return
```

Desk inserts require `item_code`, `qty > 0`, and at least one child `items` row. The controller's `apply_bridge_result` is the standard 5-step race-safe pattern, with no Sheeting-style extra kwargs.

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add fields to `_CUT_BIT_ITEM_KEYMAP` | Low if additive |
| Rename `clip_name` / `asset_id` | High; Bridge and Dash use both |
| Change `_write_clip_mappings_for_cut_bit` clip behavior | High; affects business rule for clip retirement timing |
| Remove native batch relay | High; Ops dedicated handler can fail |
| Simplify `apply_bridge_result` | Highest; shared race-safety invariant |
