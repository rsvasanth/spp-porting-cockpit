# 03 — Console backend — inspection path in `api.py`

**File:** `apps/shree_polymer_console/shree_polymer_console/shree_polymer_console/api.py`
**Relevant functions:** `initialize_submission` (Phase 3 inspection routing),
`create_local_inspection` (local audit), `apply_bridge_result` (5-step atomic
dance), `_pick`, `_backdate_fields`, `_normalize_items`.

> For the shared orchestration patterns (the 5-step `apply_bridge_result` dance,
> `_safe_local_create`, the `reference_id` cross-system key), see
> [MB Mixing Console backend](../master-batch-mixing/03-console-backend.md).
> This file documents only the inspection-specific additions.

## How inspection is routed in `initialize_submission`

From `api.py` lines 74-79 (Phase 3 cutover routing):

```python
is_inspection = bool(frappe.db.get_value(
    "Console Process Template", process_code, "is_inspection_type"
))
if is_inspection:
    create_local_inspection(prelim_payload, reference_id)
elif process_code == "MASTER_BATCH_MIXING":
    create_local_master_batch_mixing(prelim_payload, reference_id)
# ... other dispatch cases
```

The `is_inspection_type` flag on `Console Process Template` routes all
inspection types to `create_local_inspection` regardless of which specific
inspection type. The `inspection_type` field inside the payload discriminates
between Line/Patrol/Lot/Incoming/Final Visual/Visual at the legacy controller
level.

## `create_local_inspection(payload, reference_id)` — local audit

Mirrors the inspection payload locally for audit. Identity = `reference_id`.

```python
def create_local_inspection(payload, reference_id):
    """Mirror inspection payload locally for audit."""
    ctx = payload.get("context", {})
    posting_date, posting_time = _backdate_fields(ctx)
    
    return _safe_local_create(
        "Console Inspection",
        {
            "inspection_type": _pick(ctx, "inspection_type", "metadata.inspection_type"),
            "lot_no":          _pick(ctx, "lot_no", "metadata.lot_no", "batch_code"),
            "product_ref_no":  _pick(ctx, "product_ref_no", "metadata.product_ref_no", "production_item"),
            "inspector_code":  _pick(ctx, "inspector_code", "metadata.inspector_code", "inspector_id"),
            "inspector_name":  _pick(ctx, "inspector_name", "metadata.inspector_name"),
            "operator_name":   _pick(ctx, "operator_name", "metadata.operator_name"),
            "machine_no":      _pick(ctx, "machine_no", "metadata.machine_no", "workstation"),
            "posting_date":    posting_date,
            "posting_time":    posting_time,
            "total_inspected_qty_nos":  _pick(ctx, "total_inspected_qty_nos", "inspected_qty_nos"),
            "total_rejected_qty":       _pick(ctx, "total_rejected_qty"),
            "total_rejected_qty_kg":    _pick(ctx, "total_rejected_qty_kg"),
            "total_rejected_qty_in_percentage": _pick(ctx, "total_rejected_qty_in_percentage"),
            "batch_no":       _pick(ctx, "batch_no", "stock_entry_data.batch_no"),
            "spp_batch_number": _pick(ctx, "spp_batch_number", "mix_barcode"),
            "stock_entry_reference": _pick(ctx, "stock_entry_reference"),
            "sample_or_trial": _pick(ctx, "sample_or_trial", False),
            "process_code": "INSPECTION_ENTRY",
            "payload_snapshot": json.dumps(payload, indent=1),
        },
        reference_id,
        "create_local_inspection",
        child_rows={"items": _normalize_items(
            ctx.get("items", []),
            _INSPECTION_ITEM_KEYMAP
        )},
    )
```

The `_pick(ctx, "a.b", "c.d", ...)` helper tries dot-paths in order, returning
the first non-empty value. This mirrors the MB Mixing pattern exactly.

## `_INSPECTION_ITEM_KEYMAP`

```python
_INSPECTION_ITEM_KEYMAP = {
    "type_of_defect":      "type_of_defect",
    "rejected_qty":        "rejected_qty",
    "rejected_qty_kg":     "rejected_qty_kg",
    "item_code":           "item_code",
    "batch_no":            "batch_no",
    "spp_batch_number":    "spp_batch_no",
}
```

## Type-specific field routing

The `_pick` helper with multiple fallback paths handles the fact that each
inspection type sends a slightly different payload shape:

| Field | Line/Patrol/Lot sends | Incoming sends | Final Visual sends |
|---|---|---|---|
| `total_inspected_qty_nos` | `inspected_qty_nos` (mapped) | `total_inspected_qty_nos` | `total_inspected_qty_nos` |
| `total_rejected_qty_kg` | `total_rejected_qty_kg` (kg) | not sent (nos only) | not sent |
| `vs_pdir_qty` | not sent | not sent | `vs_pdir_qty` |
| `uom` | not sent | not sent | `uom` (Nos/Kgs) |

## `_safe_local_create` — audit-trail invariant

> Fully documented in [MB Mixing Console backend](../master-batch-mixing/03-console-backend.md).
> Key invariants for Inspection:
> - `flags.from_local_cache = True` skips strict validate on audit-trail path
> - `ignore_validate = True` belt-and-braces
> - `ignore_permissions=True` + `ignore_links=True`
> - Returns `None` on failure — Bridge sync continues even if mirror fails
> - Child rows appended **before** insert — atomicity

## `apply_bridge_result` — 5-step atomic dance

> Fully documented in [MB Mixing Console backend](../master-batch-mixing/03-console-backend.md).
> Applied to `Console Inspection` with the same pattern:

```python
# Step 1: atomic per-field write for THIS leg only
frappe.db.set_value("Console Inspection", self.name, {
    f'{field_prefix}_sync_status': leg_status,
    f'{field_prefix}_reference': remote_name,
    f'{field_prefix}_error_message': error,
}, update_modified=False)

# Step 2: re-read BOTH legs from DB (atomic snapshot, no memory)
row = frappe.db.get_value("Console Inspection", self.name,
    ['ops_sync_status', 'legacy_sync_status'], as_dict=True) or {}

# Step 3: aggregate sync_status
# Step 4: self-heal race correction
# Step 5: auto-submit on full success — fetch FRESH doc
```

The `apply_bridge_result` global entry point in `api.py:1946` dispatches
callbacks to `Console Inspection` via the `parent_doctypes` list (where
`Console Inspection` is first).

## What Hermes workers can safely change here

| Change | Risk |
|---|---|
| Add a new `_pick` fallback path | Low — only adds tolerance |
| Add a new field to `_INSPECTION_ITEM_KEYMAP` | Low — unmapped fields dropped |
| Add a new type-specific field routing path | Low — additive |
| Modify the 5-step `apply_bridge_result` | **Highest** — production race-safety; needs architecture review + race-condition tests |
| Touch `_safe_local_create` | **High** — every Console doctype depends on this exact behavior |
| Change the `is_inspection` dispatch condition | **High** — inspects all Console doctypes; must coordinate with Process Template config |