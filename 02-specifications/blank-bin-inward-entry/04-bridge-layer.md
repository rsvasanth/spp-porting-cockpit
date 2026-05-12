# 04 — Bridge layer (planned)

> Read [`../master-batch-mixing/04-bridge-layer.md`](../master-batch-mixing/04-bridge-layer.md) for the shared `sync_process_transaction` lifecycle. This file documents BBIE-specific Bridge work.

## Planned mapping seeder

```python
def seed_blank_bin_inward_entry_mapping():
    """BLANK_BIN_INWARD → Blank Bin Inward Entry (legacy)"""
    field_mappings = [
        {"console_field": "reference_id", "legacy_field": "stock_entry_reference"},
        {"console_field": "posting_date", "legacy_field": "posting_date"},
        {"console_field": "config.operation", "legacy_field": "operation"},
        {"console_field": "bin_code", "legacy_field": "bin_code"},
        {"console_field": "item", "legacy_field": "item"},
        {"console_field": "spp_batch_number", "legacy_field": "spp_batch_number"},
        {"console_field": "gross_weight_kgs", "legacy_field": "gross_weight_kgs"},
        {"console_field": "net_weight_kgs", "legacy_field": "net_weight_kgs"},
        {"console_field": "config.legacy_target_warehouse", "legacy_field": "target_warehouse"},
        {"console_field": "move_to_cut_bit_warehouse", "legacy_field": "move_to_cut_bit_warehouse"},
        {"console_field": "cut_bit_batch", "legacy_field": "cut_bit_batch"},
    ]
    _upsert_mapping("BLANK_BIN_INWARD", "Blank Bin Inward Entry", field_mappings)
```

## Planned `populate_blank_bin_inward_fields`

```python
def populate_blank_bin_inward_fields(doc, data=None):
    """Bridge enrichment for legacy Blank Bin Inward Entry.

    Handles two paths:
      Default — bin path: produces Asset Movement (Receive Bin)
      Repack — cut-bit path: produces Stock Entry (Repack) instead
    """
    if not data: return

    # Defensive: ensure operator/employee is set
    if not doc.get("employee"):
        doc.employee = (data.get("operator") or data.get("run_as")
                        or data.get("operator_id") or frappe.session.user)

    # Branch path resolution
    move_to_cut_bit = bool(data.get("move_to_cut_bit_warehouse"))

    if move_to_cut_bit:
        # Cut-bit repack: validate cut-bit batch is present
        if not data.get("cut_bit_batch"):
            frappe.throw("cut_bit_batch is required when move_to_cut_bit_warehouse=1")
        # Target warehouse override to cut-bit warehouse
        doc.target_warehouse = spp_settings.default_cut_bit_warehouse
    else:
        # Bin path: target = Moulding Unit warehouse
        if not doc.target_warehouse:
            doc.target_warehouse = spp_settings.default_moulding_unit_warehouse

    # Validate bin exists and is in correct state
    if doc.bin_code:
        asset_status = frappe.db.get_value("Asset", doc.bin_code, "status")
        if asset_status != "Filled":
            frappe.throw(f"Bin {doc.bin_code} is not in Filled state (current: {asset_status})")
```

## Idempotency

`find_existing_record` for `BLANK_BIN_INWARD` uses `stock_entry_reference` (= reference_id) on the legacy doctype:

```python
if process_type == "BLANK_BIN_INWARD":
    if reference_id:
        name = frappe.db.get_value(
            "Blank Bin Inward Entry",
            {"stock_entry_reference": reference_id}, "name"
        )
        if name:
            return frappe._dict({"name": name, "doctype": "Blank Bin Inward Entry"})
    return None
```

Standard reference_id-based idempotency (similar to MB / FB / Sheeting).

## Legacy on_submit chain

Legacy `Blank Bin Inward Entry` controller's `on_submit`:
- Branches on `move_to_cut_bit_warehouse`
- If 0 (bin path): creates `Asset Movement` (Receive Bin) moving the bin Asset to the target warehouse
- If 1 (cut-bit path): creates `Stock Entry` (Repack) with the bin's compound qty into the cut-bit warehouse under `Cutbit_<item>` batch; bin Asset status reset to Available

The Bridge response includes the created Asset Movement name OR Stock Entry name in `reference_name`.

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add a new path branch (e.g. "move to scrap") | Medium — requires Console + Bridge + Ops coordination |
| Modify Asset state transition logic | High — affects bin lifecycle across multiple motions |
| Change cut-bit batch convention | **Architecture review** — cross-program invariant |
