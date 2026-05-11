# 04 — Bridge layer — `shree_polymer_legacy_bridge`

**Apps involved:**
- `apps/shree_polymer_legacy_bridge/shree_polymer_legacy_bridge/sync_api.py` (1455 lines) — the Bridge itself, runs on Legacy bench
- `apps/shree_polymer_console/shree_polymer_console/shree_polymer_console/console_mapping_seeder.py` (515 lines) — seeds the `Legacy Sync Mapping` rows the Bridge reads (runs on Console bench)

The Bridge is a Frappe app installed on the **Legacy** ERPNext v15 bench
(`spp15.local` ↔ `sppmaster.frappe.cloud`). The Console doesn't talk to
Legacy directly — it POSTs to the Bridge, the Bridge reads the
`Legacy Sync Mapping` table, transforms the payload, and creates the legacy
document.

## Bridge endpoint — `sync_process_transaction`

Defined at `sync_api.py:124`. Whitelisted, called by Console's
`execute_submission_step`.

```python
@frappe.whitelist()
def sync_process_transaction(payload, process_type, reference_id=None):
    """Metadata-driven sync engine with end-to-end traceability logging."""
    start_time = time.time()
    raw_payload_str = payload if isinstance(payload, str) else json.dumps(payload, default=str)

    # 0. Initialize Log (one row per call — full traceability)
    bridge_log = frappe.get_doc({
        "doctype": "Legacy Bridge Log",
        "reference_id": reference_id or f"GEN-{process_type}-{int(start_time)}",
        "process_type": process_type,
        "incoming_payload": raw_payload_str,
        "status": "Pending"
    })
    bridge_log.insert(ignore_permissions=True)
    frappe.db.commit()

    try:
        if isinstance(payload, str):
            payload = json.loads(payload)

        # 1. IDEMPOTENCY — generic lookup (legacy doctype has no reference_id field)
        existing = find_existing_record(reference_id, payload=payload, process_type=process_type)
        if existing:
            _legacy_dt = existing.get("doctype") or _get_legacy_doctype(process_type)
            bridge_log.status = "Success"
            bridge_log.result_message = _("Transaction already processed (Idempotent)")
            bridge_log.reference_name = existing.name
            bridge_log.reference_doctype = _legacy_dt
            bridge_log.execution_time = time.time() - start_time
            bridge_log.save(ignore_permissions=True)
            frappe.db.commit()
            return {"status": "Success", "reference_name": existing.name,
                    "message": bridge_log.result_message}

        # 2. Get Mapping (one Legacy Sync Mapping doc per process_type)
        mapping = frappe.get_doc("Legacy Sync Mapping", process_type)
        if not mapping.is_active:
            raise frappe.ValidationError("Mapping is inactive")

        # 3. Build Legacy Document via mapping engine
        legacy_doc = frappe.new_doc(mapping.legacy_doctype)
        legacy_doc.reference_id = reference_id   # carries Console ID into Legacy
        payload_data = payload.get("context", payload)

        # Process-specific item extraction (Sheeting/CutBit have nested item lists)
        if process_type in ("SHEETING_PROCESS", "CUT_BIT_TRANSFER"):
            ...

        # Inject reference_id + target_system for mapping condition evaluation
        payload_data["reference_id"] = reference_id or bridge_log.reference_id
        payload_data["target_system"] = "Legacy"

        # Backward-compat: synthesize consumption_items from items[] if missing
        se_data = payload_data.get("stock_entry_data", {})
        if isinstance(se_data, dict) and not se_data.get("consumption_items"):
            items = se_data.get("items", [])
            if items:
                se_data["consumption_items"] = [it for it in items if not it.get("is_finished_item")]

        # ── Apply field_mappings rows from Legacy Sync Mapping ────────────
        transformed_data = {}
        for map_row in mapping.field_mappings:
            if not _eval_condition(map_row.condition, payload_data):
                continue

            if not map_row.is_child_table:
                # Header field
                value = get_nested_value(payload_data, map_row.console_field)
                if value is None:
                    value = map_row.default_value
                value = _transform_value(value, map_row.value_map, map_row.legacy_field)
                value = _compute_transform(map_row.transform, value, payload_data)
                legacy_doc.set(map_row.legacy_field, value)
                transformed_data[map_row.legacy_field] = value
            else:
                # Child-table row replication — extracts list, iterates, sets per-row field
                # (full implementation handles list extraction, scalar-to-child broadcasting, etc.)
                ...

        # ── Process-specific pre-insert enrichment ────────────────────────
        # MASTER_BATCH_MIXING has no special hook here — falls through.
        # COMPOUND_INSPECTION → populate_compound_inspection_fields (sets stock_id from SE lookup)
        # COMPOUND_DEVIATION → populate_compound_deviation_fields
        # SHEETING_PROCESS / CUT_BIT_TRANSFER / BLANKING_DC_ENTRY → their populate_*_fields
        if process_type == "COMPOUND_INSPECTION":
            populate_compound_inspection_fields(legacy_doc, payload_data)
        elif process_type == "SHEETING_PROCESS":
            populate_sheeting_fields(legacy_doc, payload_data)
        # ... etc.

        bridge_log.transformed_data = json.dumps(transformed_data, indent=4, default=str)
        bridge_log.save(ignore_permissions=True)

        # 4. INSERT + SUBMIT in single transaction (legacy controller's on_submit runs SE creation)
        legacy_doc.insert(ignore_permissions=True)
        legacy_doc.submit()

        # 5. Post-Submit validation — verify SE was created where expected
        legacy_doc.reload()
        warnings = []
        if hasattr(legacy_doc, 'stock_entry_reference') and not legacy_doc.stock_entry_reference:
            warnings.append("No Stock Entry was created during submission")

        # 6. Success Logging
        bridge_log.status = "Success"
        bridge_log.result_message = _("Successfully created legacy {0}").format(legacy_doc.doctype)
        bridge_log.reference_doctype = legacy_doc.doctype
        bridge_log.reference_name = legacy_doc.name

        # 7. Extract generated batch number for response (Sheeting only here)
        legacy_spp_batch_no = None
        if process_type == "SHEETING_PROCESS":
            ...

        result = {
            "status": "Success",
            "reference_doctype": legacy_doc.doctype,
            "reference_name": legacy_doc.name,
            "stock_entry_reference": legacy_doc.get("stock_entry_reference"),
            "legacy_spp_batch_no": legacy_spp_batch_no,
            "log_name": bridge_log.name,
            "message": bridge_log.result_message
        }
        if warnings: result["warnings"] = warnings
        return result

    except Exception as e:
        import traceback
        bridge_log.status = "Error" if isinstance(e, (ConnectionError, RuntimeError)) else "Failed"
        bridge_log.result_message = str(e)
        bridge_log.traceback = traceback.format_exc()
        frappe.log_error(title=f"Bridge Sync Error: {process_type}", message=bridge_log.traceback)
        return {"status": "Failed", "message": str(e), "log_name": bridge_log.name}
    finally:
        bridge_log.execution_time = time.time() - start_time
        bridge_log.save(ignore_permissions=True)
        frappe.db.commit()
```

## The mapping engine — how `field_mappings` becomes a DCR document

The `Legacy Sync Mapping` doctype has a child table `field_mappings` with
rows like:

| Column | Purpose |
|---|---|
| `console_field` | Dot-path into the Console payload (e.g. `metadata.produced_item`) |
| `legacy_field` | Target field on the legacy doctype |
| `is_child_table` | If 1, this row maps into a child-table column instead of a header field |
| `child_table_fieldname` | The legacy child-table fieldname (e.g. `dc_items`) |
| `condition` | Python expression evaluated against payload (skip row if False) |
| `default_value` | Used when `console_field` resolves to None |
| `value_map` | JSON string defining value-substitution table |
| `transform` | Compute expression (rare) |

The engine reads these rows and walks the payload accordingly. For MB
Mixing, the rows are seeded by `seed_mixing_process_mapping` in
`console_mapping_seeder.py`.

## Console mapping seeder for MB Mixing

`console_mapping_seeder.py:105`:

```python
def seed_mixing_process_mapping():
    """MIXING_PROCESS → Delivery Challan Receipt"""
    # value-map for inward_material_type (Legacy needs a literal, payload has the operation)
    inward_material_map = json.dumps({
        "Master Batch Mixing": "Master Batch",
        "Final Batch Mixing":  "Compound",
    })

    field_mappings = [
        # ── Header fields ──────────────────────────────────────────────
        {"console_field": "reference_id",                         "legacy_field": "reference_id"},
        {"console_field": "reference_id",                         "legacy_field": "dc_no"},
        {"console_field": "stock_entry_data.posting_date",        "legacy_field": "dc_receipt_date"},
        {"console_field": "config.operation",                     "legacy_field": "operation"},
        {"console_field": "metadata.produced_item",               "legacy_field": "item_to_manufacture"},
        # Console-generated mix barcode — Legacy DCR uses this INSTEAD of auto-generating
        # when reference_id is set. This is the single barcode authority pattern.
        {"console_field": "mix_barcode",                          "legacy_field": "bridge_mix_barcode"},
        # Derive inward_material_type from operation via value_map (default = Compound)
        {"console_field": "config.operation",                     "legacy_field": "inward_material_type",
         "value_map": inward_material_map, "default_value": "Compound"},
        {"console_field": "config.legacy_source_warehouse",       "legacy_field": "source_warehouse"},
        {"console_field": "config.legacy_target_warehouse",       "legacy_field": "target_warehouse"},
        {"console_field": "config.legacy_wip_warehouse",          "legacy_field": "wip_warehouse"},

        # ── Child table: dc_items (consumption rows) ──────────────────
        {"is_child_table": 1, "child_table_fieldname": "dc_items",
         "console_field": "stock_entry_data.consumption_items.item_code",      "legacy_field": "item_code"},
        {"is_child_table": 1, "child_table_fieldname": "dc_items",
         "console_field": "stock_entry_data.consumption_items.qty",            "legacy_field": "qty"},
        {"is_child_table": 1, "child_table_fieldname": "dc_items",
         "console_field": "stock_entry_data.consumption_items.batch_no",       "legacy_field": "batch_no"},
        {"is_child_table": 1, "child_table_fieldname": "dc_items",
         "console_field": "stock_entry_data.consumption_items.spp_batch_number","legacy_field": "spp_batch_no"},
        {"is_child_table": 1, "child_table_fieldname": "dc_items",
         "console_field": "stock_entry_data.consumption_items.mix_barcode",    "legacy_field": "scan_barcode"},
        # Header-to-child broadcasts (each child row gets the same parent value):
        {"is_child_table": 1, "child_table_fieldname": "dc_items",
         "console_field": "reference_id",                                       "legacy_field": "dc_no"},
        {"is_child_table": 1, "child_table_fieldname": "dc_items",
         "console_field": "config.operation",                                   "legacy_field": "operation"},
        {"is_child_table": 1, "child_table_fieldname": "dc_items",
         "console_field": "metadata.produced_item",                             "legacy_field": "item_to_manufacture"},
    ]

    _upsert_mapping("MASTER_BATCH_MIXING", "Delivery Challan Receipt", field_mappings)
    _upsert_mapping("FINAL_BATCH_MIXING",  "Delivery Challan Receipt", field_mappings)
    print("  ✅ MASTER_BATCH_MIXING and FINAL_BATCH_MIXING mappings seeded")
```

The function is called from `seed_console_mappings()` on bench install /
migrate. `_upsert_mapping` replaces all `field_mappings` rows for the given
process_code (idempotent).

## Idempotency — `find_existing_record(reference_id, payload, process_type)`

Defined at `sync_api.py:405`. The Bridge cannot use `dc_no` as the
idempotency key for MB Mixing because `dc_no` is also a legitimate field
value. Instead it does a generic lookup:

```python
def find_existing_record(reference_id, payload=None, process_type=None):
    if process_type == "COMPOUND_INSPECTION":
        # special: look up Compound Inspection by reference_id + barcode
        ...
    if process_type == "COMPOUND_DEVIATION":
        ...
    if process_type == "SHEETING_PROCESS":
        ...
    if process_type == "BLANKING_DC_ENTRY":
        ...
    # For MASTER_BATCH_MIXING the lookup falls through to a generic search
    # via `reference_id` on the legacy doctype's `reference_id` field
    # (custom field added on legacy DCR for this purpose).
```

For MB Mixing the idempotency check is:
`frappe.db.exists("Delivery Challan Receipt", {"reference_id": reference_id})`

If a previous call from Console already created a DCR with this
reference_id, the Bridge returns Success immediately and does **not**
create a duplicate.

## Value-map evaluation — `_transform_value`

When a mapping row has a `value_map`, the engine does a substitution:

```python
def _transform_value(value, value_map, legacy_field):
    if not value_map: return value
    try:
        mapping = json.loads(value_map) if isinstance(value_map, str) else value_map
        return mapping.get(value, value)   # if not in map, return as-is
    except Exception:
        return value
```

For MB Mixing's `inward_material_type` row, this resolves
`"Master Batch Mixing"` (from `config.operation`) into `"Master Batch"`
(the legacy field's allowed Select value). If the payload's operation
doesn't match any key, the default `"Compound"` kicks in — which is
**defensive but masks bugs** (see `10-risks-and-decisions.md`).

## Condition evaluation — `_eval_condition`

```python
def _eval_condition(condition, payload_data):
    if not condition: return True
    try:
        from frappe.utils.safe_exec import safe_eval
        return bool(safe_eval(condition, None, payload_data))
    except Exception:
        return True   # fail-OPEN: if condition can't evaluate, include the row
```

MB Mixing mapping rows have no conditions — they always apply. This helper
exists for other process types (Sheeting / CutBit) where rows are gated
on `target_system == "Legacy"` etc.

## Callback emission — how the Bridge tells Console "done"

The Bridge does **not** POST a callback to Console. Instead, Console's
`execute_submission_step` reads the Bridge's response **synchronously** —
the response body contains `reference_name`, `reference_doctype`, `status`.
Then Console's own `update_local_domain_record` calls
`doc.apply_bridge_result(target="Legacy", status, remote_name=reference_name, error)`
locally on the Console bench.

So the "callback" is really:
1. Bridge returns 200 with body
2. Console reads body, updates its own Transaction Log
3. Console calls its own `apply_bridge_result` on the doctype controller
4. 5-step atomic dance runs on Console side

This means **the network round-trip is one-way (Console → Bridge → response)**.
No webhook from Bridge back into Console. This simplifies firewall config
(Bridge doesn't need to know how to reach Console) but means the Bridge
can't notify Console asynchronously if something happens later.

## Downstream Bridge functions for the MB Mixing chain

These don't run during MB Mixing itself, but they consume MB Mixing's
output and matter for understanding why MB Mixing's payload shape is what
it is.

### `_resolve_compound_identity(payload_data)` — `sync_api.py:668`

Used by Compound Inspection sync. Extracts the canonical compound identity
from the inspection payload — which means finding the matching MB Mixing's
`mix_barcode` + `spp_batch_no`.

### `_lookup_legacy_stock_entry(identity)` — `sync_api.py:702`

The famous 6-strategy SE lookup. Compound Inspection on Legacy requires
`self.stock_id` to be set — pointing to the manufacturing Stock Entry
created by the **DCR submission** (which MB Mixing creates). If MB Mixing
doesn't write `bridge_mix_barcode` correctly, this lookup fails with the
"Bridge SE Lookup FAILED — DCR may not be synced" error.

Strategies in order:
1. `mix_barcode == spp_batch_no` (most common)
2. `spp_batch_number == stripped spp_batch_no` (Legacy without `C_` prefix)
3. `spp_batch_number == spp_batch_no` (direct match)
4. `mix_barcode == payload mix_barcode` (when different from spp_batch_no)
5. `mix_barcode == "{item_code}_{spp_batch_no}"` (compound format)
6. `batch_no == payload mix_barcode` (last-ditch)

**Each strategy survives because it covers a real production case.** Do
not delete strategies without proving they have zero hits in production
(grep `Console Transaction Log` + `Legacy Bridge Log` for the resolved
`_strategy` field).

## What Hermes workers can safely change here

| Change | Risk |
|---|---|
| Add a new mapping row in `seed_mixing_process_mapping` | Low — purely additive |
| Change a `default_value` | Medium — may mask issues by silently filling missing data |
| Add a value-map entry | Low — additive |
| Remove a mapping row | High — likely breaks legacy DCR insert |
| Touch `_lookup_legacy_stock_entry` | **High** — downstream Compound Inspection depends on every strategy |
| Touch `sync_process_transaction` | **High** — affects every process_type |
| Remove the post-submit `stock_entry_reference` warning check | Low — defensive only |
