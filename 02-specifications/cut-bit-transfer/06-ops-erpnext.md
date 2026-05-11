# 06 - Ops ERPNext

> Read [`../master-batch-mixing/06-ops-erpnext.md`](../master-batch-mixing/06-ops-erpnext.md) for the generic Transaction Engine. Cut Bit Transfer deliberately bypasses that engine through process-specific routing.

## Dispatch

`shree_polymer_ops.api.process_transaction` routes first:

```python
if process_code == "CUT_BIT_TRANSFER":
    return submit_cut_bit_transfer(context, run_legacy_sync=False)
```

The `run_legacy_sync=False` flag is critical. Console's `execute_submission_step` already sends a separate parallel request to Legacy Bridge. If Ops used its default direct bridge call here, Legacy would receive the same CBT twice.

## Asset validation

`validate_cut_bit_asset(barcode)` resolves both Clips and Bins:

| Priority | Source |
|---|---|
| Clip | `Sheeting Clip` by `barcode_text` or name, then active `Item Clip Mapping` |
| Bin | `Blanking Bin` by `barcode_text` or name, then active `Item Bin Mapping` |
| Stock | `get_batch_for_barcode` + `_get_sabb_qty` in resolved source warehouse |

Warehouse defaults:

| Asset type | Source warehouse |
|---|---|
| Clip | `default_sheeting_warehouse` or `Sheeting - SPP` |
| Bin | `unit_2_warehouse` or `Unit-2 - SPP` |

## Dedicated submit handler

`submit_cut_bit_transfer(payload, run_legacy_sync=True)` accepts JSON string or dict. In Console path, `payload` is the context and `items` are already normalized.

For every item, it creates two Stock Entry rows:

| Row | Fields |
|---|---|
| Source | `s_warehouse`, `batch_no=native_batch_no`, `is_finished_item=0`, `use_serial_batch_fields=1` |
| Target | `t_warehouse=CUTBIT_WH`, `batch_no=Cutbit_<item_code>`, `mix_barcode=CB_<item_code>`, `is_finished_item=1`, `use_serial_batch_fields=1` |

Before appending target rows, the handler ensures the target batch exists:

```python
cutbit_batch_id = f"Cutbit_{i_code}"
if not frappe.db.exists("Batch", cutbit_batch_id):
    frappe.get_doc({
        "doctype": "Batch",
        "batch_id": cutbit_batch_id,
        "item": i_code
    }).insert(ignore_permissions=True)
```

## SABB handling

The handler sets `use_serial_batch_fields=1` on both rows. Its comment says this uses the legacy Stock Ledger batch path and avoids ERPNext v15 Serial and Batch Bundle auto-selection conflicts.

If ERPNext still creates SABB links after insert, it clears `serial_and_batch_bundle`, `batch_no`, `serial_no`, and `use_serial_batch_fields` before reloading and submitting.

## Impact response

After submit, Ops uses `TransactionEngine({}).capture_impact(se)` and returns:

| Field | Consumer |
|---|---|
| `reference_name` | Console Transaction Log / local domain record |
| `reference_doctype="Stock Entry"` | Console display |
| `impacted_balances` | Console stock cache |
| `impacted_clips` | `_backfill_ops_reference_for_clips` for Sheeting/CBT |
| `impacted_bins` | `apply_bin_updates` |

Console treats Sheeting and Cut Bit specially for `impacted_clips`: it backfills existing mapping rows rather than creating new ones.

## Legacy double-hop mode

When called directly outside Console, `run_legacy_sync=True` still invokes:

```python
sync_process_transaction(bridge_payload, "CUT_BIT_TRANSFER", reference_id=se.name)
```

That legacy direct mode is useful for old integrations/tests. It must remain disabled in the Console path.

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add response metadata | Low |
| Change `Cutbit_<item_code>` | High |
| Change `CB_<item_code>` | High |
| Remove `use_serial_batch_fields=1` | High; reopens v15 SABB conflict |
| Remove `run_legacy_sync=False` dispatch | Highest; duplicate Legacy submissions |
