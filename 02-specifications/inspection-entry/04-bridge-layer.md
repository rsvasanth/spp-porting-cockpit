# 04 — Bridge layer — Legacy Bridge `sync_api.py` for Inspection Entry

**File:** `apps/shree_polymer_legacy_bridge/shree_polymer_legacy_bridge/sync_api.py`
**Relevant function:** `sync_process_transaction` (idempotency, mapping engine,
value-map, callback emission) + inspection-specific field mappings.

> For the shared Bridge patterns (idempotency check, get Legacy Sync Mapping,
> apply field_mappings, insert/submit, callback), see
> [MB Mixing Bridge layer](../master-batch-mixing/04-bridge-layer.md).
> This file documents only the inspection-specific additions.

## How `sync_process_transaction` handles `INSPECTION_ENTRY`

The Bridge is dispatched from `api.py` via:

```python
targets.append({
    "url": bridge_url,
    "type": "Legacy",
    "method": "shree_polymer_legacy_bridge.sync_api.sync_process_transaction"
})
```

The Bridge's `sync_process_transaction` receives:
- `payload` — Console's transaction payload
- `process_type` = `"INSPECTION_ENTRY"`
- `reference_id` — cross-system correlation key

## Inspection field mappings

From `Legacy Sync Mapping` for `INSPECTION_ENTRY` (seeded from
`console_mapping_seeder.py`):

| Legacy field | Value source from Console payload |
|---|---|
| `inspection_type` | `context.inspection_type` |
| `lot_no` | `context.lot_no` or `context.batch_code` |
| `inspector_code` | `context.inspector_code` or `context.inspector_id` |
| `inspector_name` | `context.inspector_name` |
| `posting_date` | `context.posting_date` |
| `product_ref_no` | `context.product_ref_no` or `context.production_item` |
| `operator_name` | `context.operator_name` |
| `machine_no` | `context.machine_no` or `context.workstation` |
| `batch_no` | `context.batch_no` (from Job Card SE resolution) |
| `spp_batch_number` | `context.spp_batch_number` or `context.mix_barcode` |
| `stock_entry_reference` | `context.stock_entry_reference` (set post-submit by MPE cascade) |
| `total_inspected_qty_nos` | `context.total_inspected_qty_nos` or `context.inspected_qty_nos` (mapped) |
| `total_inspected_qty_kgs` | `context.total_inspected_qty_kgs` |
| `total_rejected_qty` | `context.total_rejected_qty` |
| `total_rejected_qty_kg` | `context.total_rejected_qty_kg` |
| `total_rejected_qty_in_percentage` | `context.total_rejected_qty_in_percentage` |
| `vs_pdir_qty` | `context.vs_pdir_qty` (Final Visual only) |
| `vs_pdir_qty_after_rejection` | `context.vs_pdir_qty_after_rejection` (Final Visual only) |
| `sample_or_trial` | `context.sample_or_trial` |
| `items` (child rows) | `context.items` (defect rows from child table) |

## Inspection child table mappings

`Inspection Entry Item` child rows mapped from Console's `items` array:

| Legacy field | Value source |
|---|---|
| `type_of_defect` | `type_of_defect` |
| `rejected_qty` | `rejected_qty` (nos) |
| `rejected_qty_kg` | `rejected_qty_kg` (kg, Line/Patrol/Lot only) |
| `item_code` | `item_code` (product ref) |
| `batch_no` | `batch_no` |
| `spp_batch_number` | `spp_batch_number` |

## Type-specific `inspection_type` value-map

The Bridge does **not** transform `inspection_type` values — they pass through
as-is (Line Inspection, Patrol Inspection, Lot Inspection, Incoming Inspection,
Final Visual Inspection, Visual Inspection). The legacy controller branches on
these exact strings.

## MPE cascade helpers in the Bridge

The `submit_inspection_stock_entry_immediately` function is a **static function
on the legacy IE controller**, not a Bridge function. The Bridge does **not**
call it. The cascade fires from:

1. **IE `on_submit`** — after Line/Patrol/Lot IE submission, if the trigger
   condition is met (see Drift Finding #1 in `10-risks-and-decisions.md`),
   IE calls `submit_inspection_stock_entry_immediately(self)`

2. **MPE `on_submit`** — MPE's helper `submit_inspection_stock_entries_from_moulding`
   (documented in `../moulding-production-entry/`) is a separate cascade path
   that also updates Line + Patrol Stock Entries. Both paths are described in
   `10-risks-and-decisions.md` (Critical Drift Finding #2).

The Bridge is responsible only for:
- Writing the `Inspection Entry` to legacy with the Console payload
- Storing `stock_entry_reference` (blank on initial submit for Line/Patrol/Lot)
- The callback that fires `apply_bridge_result` on the Console side

The batch cascade is an **internal legacy-to-legacy orchestration** that happens
after the Bridge has returned its success response.

## `reference_id` for Inspection Entry

`reference_id` is the cross-system correlation key. For Inspection Entry it
correlates:
- Console `Console Inspection.name` (local audit)
- Legacy `Inspection Entry.name` (e.g. `INSP-.#####`)
- `Console Transaction Log.reference_id`

The legacy `Inspection Entry` is named `INSP-.#####` (expression autoname) and
stores `reference_id` as a field (not its primary key — the naming series is).

## Idempotency check

The Bridge checks for an existing `Inspection Entry` with the same `reference_id`.
If found, returns the cached record without creating a new one.

```python
# Approximate pattern:
existing = frappe.db.get_value("Inspection Entry",
    {"reference_id": reference_id}, "name")
if existing:
    return {"status": "success", "reference_name": existing, ...}
```

## What Hermes workers can safely change here

| Change | Risk |
|---|---|
| Add a new field mapping for a new Inspection Entry field | Low — additive |
| Add a new child row mapping | Low — additive |
| Add a new `inspection_type` value to the value-map | Low — pass-through |
| Modify the idempotency check | Medium — must ensure same reference_id returns same record |
| Change `reference_id` usage | **High** — cross-system correlation key; affects all layers |
| Touch the cascade orchestration (MPE→IE batch update) | **Highest** — cascade involves IE, MPE, Stock Entry Detail; see `10-risks-and-decisions.md` |