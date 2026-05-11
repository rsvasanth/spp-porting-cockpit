# 04 — Bridge layer

> Read [`../master-batch-mixing/04-bridge-layer.md`](../master-batch-mixing/04-bridge-layer.md)
> for `sync_process_transaction` walkthrough. Sheeting differs in:
> (1) a special item-extraction branch with barcode synthesis,
> (2) two child-table mappings (not one),
> (3) a populated populate function (`populate_sheeting_fields`),
> (4) a different legacy doctype (`Material Transfer`, not `Delivery Challan Receipt`).

## Sheeting-specific item extraction — `sync_api.py:177`

In `sync_process_transaction`, BEFORE applying field_mappings, there's a
special branch for Sheeting/CutBit that **synthesizes the legacy barcode
format** for items that lack `mix_barcode`:

```python
if process_type in ("SHEETING_PROCESS", "CUT_BIT_TRANSFER"):
    source = None
    if payload.get("items"):
        source = payload
    elif payload.get("sequence") and payload["sequence"][0].get("params", {}).get("kwargs", {}).get("payload", {}).get("items"):
        source = payload["sequence"][0]["params"]["kwargs"]["payload"]
    elif payload.get("context", {}).get("legacy_payload", {}).get("items"):
        source = payload["context"]["legacy_payload"]

    if source and source.get("items"):
        payload_data = dict(payload_data)
        payload_data["items"] = source.get("items", [])
        payload_data["operator"] = source.get("operator")

        if process_type == "SHEETING_PROCESS":
            payload_data["sheeting_clip"] = source.get("sheeting_clip", [])
            # Legacy barcode format: [ItemCode]_[OriginalBatch]
            for it in payload_data["items"]:
                if not it.get("mix_barcode") and it.get("spp_batch_number"):
                    batch_no = it.get("spp_batch_number")
                    original_batch = batch_no.rsplit("-", 1)[0] if "-" in batch_no else batch_no
                    it["mix_barcode"] = f"{it.get('item_code', '')}_{original_batch}"
```

**Why this matters:**

1. **Items source resolution** — items can live at `payload.items`,
   inside `payload.sequence[0].params.kwargs.payload.items`, or in
   `payload.context.legacy_payload.items`. The branch tries each in
   priority order. This handles payloads built via different paths
   (direct Dash submit vs sequence-engine generated).

2. **Barcode synthesis** — Console generates output clip barcodes like
   `C_26C03X0-1`, `C_26C03X0-2`. Legacy `Material Transfer Item` needs
   `mix_barcode` in the format `{item_code}_{original_batch}`. This
   loop strips the trailing `-N` from each item's `spp_batch_number`
   (the auto-numbered output barcode) and prepends the item_code.

   Example transformation:
   - Input item: `{item_code: "COMPOUND-A", spp_batch_number: "C_26C03X0-1"}`
   - After loop: also has `mix_barcode: "COMPOUND-A_C_26C03X0"`

3. **`sheeting_clip` extracted to top of payload_data** — so the
   mapping engine can resolve `sheeting_clip` child rows.

## Mapping engine — TWO child tables (`batches` + `sheeting_clip`)

`seed_sheeting_process_mapping` in `console_mapping_seeder.py:199`:

```python
field_mappings = [
    # --- Header fields ---
    {"console_field": "reference_id",      "legacy_field": "stock_entry_ref"},
    {"console_field": "posting_date",      "legacy_field": "transfer_date"},
    {"console_field": "employee_code",     "legacy_field": "employee"},
    {"console_field": "source_item",       "legacy_field": "item"},
    {"console_field": "source_batch",      "legacy_field": "scan_spp_batch_number"},
    {"console_field": "target_qty",        "legacy_field": "qty"},
    {"console_field": "config.legacy_source_warehouse", "legacy_field": "source_warehouse"},
    {"console_field": "config.legacy_target_warehouse", "legacy_field": "target_warehouse"},
    # Literal string injected (note the double-quoted value):
    {"console_field": "\"Transfer Compound to Sheeting Warehouse\"", "legacy_field": "material_transfer_type"},

    # --- Child table: batches (Material Transfer Item rows) ---
    {"is_child_table": 1, "child_table_fieldname": "batches",
     "console_field": "items.item_code",   "legacy_field": "item_code"},
    {"is_child_table": 1, "child_table_fieldname": "batches",
     "console_field": "items.batch_no",    "legacy_field": "batch_no"},
    {"is_child_table": 1, "child_table_fieldname": "batches",
     "console_field": "items.batch_no",    "legacy_field": "scan_barcode"},   # ← batch_no dual-mapped
    {"is_child_table": 1, "child_table_fieldname": "batches",
     "console_field": "items.qty",         "legacy_field": "qty"},

    # --- Child table: sheeting_clip ---
    {"is_child_table": 1, "child_table_fieldname": "sheeting_clip",
     "console_field": "sheeting_clips",    "legacy_field": "sheeting_clip"},
]
_upsert_mapping("SHEETING_PROCESS", "Material Transfer", field_mappings)
```

**Notable mapping facts:**

1. **`"\"Transfer Compound to Sheeting Warehouse\""` as `console_field`**
   — the double-quoted string is a **literal value injection**. The
   mapping engine treats a quoted string as "use this string literal,
   don't walk the payload path." This is how the mapping seeds a
   constant value into a legacy field.

2. **`items.batch_no` mapped to TWO legacy fields** (`batch_no` and
   `scan_barcode`). Material Transfer Item on legacy needs both: one
   for stock identity, one for the scan barcode that ties back to the
   Dash submission.

3. **`sheeting_clip` child table** mapping is a single row that copies
   the entire `sheeting_clips` array (whole payload) into the legacy
   `sheeting_clip` child table. This is a **list-replication** case in
   the mapping engine (see `04-bridge-layer.md` from MB spec for how
   the engine handles this).

## Idempotency — `find_existing_record`

`sync_api.py:460`:

```python
if process_type == "SHEETING_PROCESS":
    # Look up by reference_id on Material Transfer's stock_entry_ref field
    existing = frappe.db.exists("Material Transfer",
        {"stock_entry_ref": reference_id})
    if existing:
        return frappe._dict({"name": existing, "doctype": "Material Transfer"})
```

For Sheeting, the idempotency key is `stock_entry_ref` on `Material Transfer`
(not `dc_no` like MB's DCR).

## `populate_sheeting_fields` — `sync_api.py:1093`

```python
def populate_sheeting_fields(doc, data=None):
    """Ensures critical fields are populated on the legacy Material Transfer for Sheeting."""
    if not doc.material_transfer_type:
        doc.material_transfer_type = "Transfer Compound to Sheeting Warehouse"

    if not doc.source_warehouse:
        doc.source_warehouse = "U3-Store - SPP INDIA"

    if not doc.target_warehouse:
        doc.target_warehouse = "Sheeting Warehouse - SPP INDIA"

    # Legacy requires cutbit_qty on the parent.
    # Also requires is_cut_bit_item flag on each batch row.
    # If the payload came from Ops, it might not have is_cut_bit_item explicitly.
    if hasattr(doc, "batches"):
        cutbit_total = 0
        for row in doc.batches:
            if row.batch_no and "Cutbit_" in row.batch_no:
                row.is_cut_bit_item = 1
                cutbit_total += (row.qty or 0)
            elif getattr(row, "is_cut_bit_item", 0) == 1:
                cutbit_total += (row.qty or 0)
            else:
                row.is_cut_bit_item = 0

        if cutbit_total > 0 and not doc.get("cutbit_qty"):
            doc.cutbit_qty = cutbit_total
```

**Key behaviours:**

| Behavior | Detail |
|---|---|
| Defaults `material_transfer_type` | If mapping didn't set it, defaults to `"Transfer Compound to Sheeting Warehouse"`. The mapping seeder DOES set it via the literal injection, so this is defensive. |
| Defaults source/target warehouses | Hardcoded fallback to `U3-Store - SPP INDIA` and `Sheeting Warehouse - SPP INDIA`. **Same risk as MB's WAREHOUSE_MAP fallback** — masks bugs if config is missing. |
| `is_cut_bit_item` flag reconciliation | Detects cut-bit rows by the `"Cutbit_"` prefix in batch_no. Backfills the flag if missing. |
| `cutbit_qty` aggregation | Sums the qty of all cut-bit rows and sets on the parent. Legacy validation requires this field if any row is cut-bit. |

## Response shape

The Bridge returns the standard shape **plus** `legacy_spp_batch_no` —
the generated batch number on Material Transfer's first batch row.
This is captured into Console's `apply_bridge_result` (see
`03-console-backend.md`).

```python
# sync_api.py:354
legacy_spp_batch_no = None
if process_type == "SHEETING_PROCESS":
    se_name = legacy_doc.get("stock_entry_ref") or legacy_doc.get("stock_entry_reference")
    if se_name:
        legacy_spp_batch_no = frappe.db.get_value(
            "Stock Entry Detail",
            {"parent": se_name, "is_finished_item": 1},
            "spp_batch_number"
        )
```

Wait — this extracts from `Stock Entry Detail`, but Sheeting's legacy
doctype is `Material Transfer`, not Stock Entry. The lookup uses the
`stock_entry_ref` field on Material Transfer (which **does** link to a
Stock Entry that Material Transfer creates on its own submit). The
Material Transfer's on_submit creates a Stock Entry as a side effect;
the generated SE has the FG batch number we want.

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add a new field to `populate_sheeting_fields` defaults | Low |
| Add a new mapping row to `seed_sheeting_process_mapping` | Low |
| Remove the `"Cutbit_"` prefix detection | **High** — Ops-source payloads rely on this backfill |
| Remove the `cutbit_qty` aggregation | High — legacy validation requires it |
| Change the literal string `"Transfer Compound to Sheeting Warehouse"` | Medium — operations might have multiple transfer types; coordinate |
| Touch the barcode synthesis at `sync_api.py:191` | Medium — downstream consumers depend on the `{item_code}_{original_batch}` format |
