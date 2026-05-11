# 05 - Legacy ERPNext

## Legacy doctype

| Doctype | Path |
|---|---|
| `Cut Bit Transfer` | `/Users/alphaworkz/frappe-bench/apps/shree_polymer_custom_app/shree_polymer_custom_app/shree_polymer_custom_app/doctype/cut_bit_transfer/` |
| Child table used | `Material Transfer Item` in parent JSON |
| Separate old child doctype | `Cut Bit Item` exists, but the parent currently points to `Material Transfer Item` |

Important parent fields:

| Field | Meaning |
|---|---|
| `transfer_from` | `Warming` or `Blanking` |
| `scan_clip__bin` | Legacy UI scan field and Bridge idempotency field |
| `cut_bit_item` | Item being consolidated |
| `employee` | Mandatory legacy operator link |
| `stock_entry_reference` | Hidden reference populated after SE creation |

## Controller hooks

`CutBitTransfer.on_submit()` calls `create_stock_entry(self)` and reloads. `on_cancel()` deletes the Stock Entry safely through `delete_stock_entry_safely`.

This differs from Sheeting's legacy `Material Transfer`: the CBT doctype itself owns the final Stock Entry creation.

## Legacy validation helper

`validate_clip_barcode(batch_no, t_type, warehouse)` is the old Desk scan path. It:

| Step | Behavior |
|---|---|
| 1 | Tries `Item Clip Mapping` joined to `Sheeting Clip` by `barcode_text` |
| 2 | Falls back to `Item Bin Mapping` joined to `Asset` by `barcode_text` |
| 3 | Builds mix key `<compound>_<spp_batch_number.split("-")[0]>` |
| 4 | Looks for submitted `Stock Entry Detail` by `mix_barcode` or `barcode_text` |
| 5 | Resolves stock from `Item Batch Stock Balance` and native batch qty |

Bridge `populate_cutbit_fields` reimplements the necessary parts because Console flow skips the old Desk scan event.

## Stock Entry creation

Legacy `create_stock_entry(mt_doc)` creates one Repack Stock Entry:

| Row pass | Warehouse side | Batch convention |
|---|---|---|
| First loop | Source rows (`s_warehouse`) | Existing resolved batch |
| Second loop | Target rows (`t_warehouse=default_cut_bit_warehouse`) | `Cutbit_<item_code>` when batch exists; otherwise original batch |

Target rows carry:

```python
"mix_barcode": "CB_" + x.item_code
```

The controller saves the Stock Entry with `docstatus = 1` and writes `stock_entry_reference` back to the CBT document.

## Source warehouse rule

Legacy calculates source warehouse per item:

| Item group | Source warehouse |
|---|---|
| `Compound` | `default_sheeting_warehouse` |
| `SPP Settings.blanking_item_group` | `unit_2_warehouse` |
| Else | `default_blanking_warehouse` |

Bridge must match this rule before insert so the child rows already carry resolvable batch data.

## Bin mapping retirement

After Stock Entry creation, legacy retires or reduces `Item Bin Mapping` rows only for items in the blanking item group.

| Condition | Legacy action |
|---|---|
| `mapping.qty == transfer qty` | set `is_retired = 1` |
| `mapping.qty > transfer qty` | reduce `qty` |
| Clip path | no equivalent clip retirement here |

This mirrors the Console-side current rule: bin balances can be consumed in CBT; clip retirement is deferred to Blanking.

## Diagnostic if Legacy path is unclear

Run on the Legacy bench after a CBT submission:

```bash
bench --site spp15.local console
```

```python
ref = "CBT-<timestamp>"
doc = frappe.get_last_doc("Cut Bit Transfer")
print(doc.name, doc.transfer_from, doc.cut_bit_item, doc.stock_entry_reference)
for row in doc.items:
    print(row.item_code, row.batch_no, row.qty, getattr(row, "ct_source_warehouse", None))
se = frappe.get_doc("Stock Entry", doc.stock_entry_reference)
for row in se.items:
    print(row.item_code, row.s_warehouse, row.t_warehouse, row.batch_no, row.mix_barcode)
```

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add read-only trace fields | Low |
| Change `CB_` or `Cutbit_` conventions | High; downstream recycling depends on them |
| Change source warehouse rule | High; Bridge and Ops must stay aligned |
| Change bin retirement semantics | Medium/high; affects Blanking inventory |
| Make `stock_entry_reference` a Link again in Console flow | High; Bridge currently clears bogus links |
