# 05 — Legacy ERPNext (v15) — planned

## Legacy doctype

`Blank Bin Inward Entry` — custom legacy doctype on `shree_polymer_custom_app`.

Key fields (per plan doc):
- `bin_code` — Link to Asset
- `item` — the compound contained
- `spp_batch_number`
- `gross_weight_kgs` / `net_weight_kgs`
- `target_warehouse`
- `move_to_cut_bit_warehouse` — Check (1 = repack path)
- `cut_bit_batch` — Data (only used when move_to_cut_bit_warehouse=1)
- `stock_entry_reference` — Hidden; populated after submit

## Controller behavior (planned)

`BlankBinInwardEntry.on_submit()`:

```python
def on_submit(self):
    if self.move_to_cut_bit_warehouse:
        # Cut-bit repack path
        se = make_repack_to_cut_bit(self)
        if se:
            self.db_set("stock_entry_reference", se.name)
            # Reset bin Asset status
            frappe.db.set_value("Asset", self.bin_code, "status", "Available")
    else:
        # Bin path
        am = make_receive_bin_asset_movement(self)
        if am:
            self.db_set("stock_entry_reference", am.name)  # repurposed field for AM ref
            # Bin Asset status flips: Filled at blanking → Inward at Moulding Unit
            frappe.db.set_value("Asset", self.bin_code, "status", f"Inward at {self.target_warehouse}")
    self.reload()
```

## Asset Movement (Receive Bin) — bin path

Legacy creates a Frappe-native `Asset Movement` record:

```python
def make_receive_bin_asset_movement(bbie_doc):
    am = frappe.new_doc("Asset Movement")
    am.purpose = "Receipt"
    am.transaction_date = bbie_doc.posting_date
    am.append("assets", {
        "asset": bbie_doc.bin_code,
        "source_location": bbie_doc.source_warehouse,
        "target_location": bbie_doc.target_warehouse,
    })
    am.docstatus = 1
    am.save(ignore_permissions=True)
    return am
```

## Stock Entry (Repack) — cut-bit path

Legacy creates a Frappe-native `Stock Entry` (purpose: Repack):

```python
def make_repack_to_cut_bit(bbie_doc):
    se = frappe.new_doc("Stock Entry")
    se.stock_entry_type = "Repack"
    se.purpose = "Repack"
    se.posting_date = bbie_doc.posting_date
    # Source: bin's current warehouse
    se.append("items", {
        "item_code": bbie_doc.item,
        "qty": bbie_doc.net_weight_kgs,
        "batch_no": bbie_doc.spp_batch_number,
        "s_warehouse": bbie_doc.source_warehouse,
        "is_finished_item": 0,
    })
    # Target: cut-bit warehouse with Cutbit_<item> batch
    cutbit_batch_id = f"Cutbit_{bbie_doc.item}"
    if not frappe.db.exists("Batch", cutbit_batch_id):
        frappe.get_doc({"doctype": "Batch", "batch_id": cutbit_batch_id, "item": bbie_doc.item}).insert(ignore_permissions=True)
    se.append("items", {
        "item_code": bbie_doc.item,
        "qty": bbie_doc.net_weight_kgs,
        "batch_no": cutbit_batch_id,
        "t_warehouse": "Cut-Bit Warehouse - SPP INDIA",
        "is_finished_item": 1,
    })
    se.docstatus = 1
    se.save(ignore_permissions=True)
    return se
```

## Downstream consumers

| Consumer | Reads from BBIE |
|---|---|
| Blank Bin Issue (Wave 3) | Bin Asset status must be "Inward at Moulding Unit" for BBI to issue |
| FB Mixing (recycling) | `Cutbit_<item>` batches from cut-bit path are recyclable inputs |
| Stock Ledger reports | Asset Movement or Stock Entry per path; standard ERPNext mechanisms |

## What Hermes workers must NOT touch

- `Asset Movement` doctype (ERPNext native — out of program scope)
- `Stock Entry` (Repack) purpose handling (ERPNext native)
- `Batch` auto-creation pattern (standard ERPNext)
- Bin Asset status taxonomy (cross-motion invariant)
