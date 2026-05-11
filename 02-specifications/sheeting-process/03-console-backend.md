# 03 — Console backend

> Read [`../master-batch-mixing/03-console-backend.md`](../master-batch-mixing/03-console-backend.md)
> for `initialize_submission`, `execute_submission_step`, `_safe_local_create`,
> and the 5-step `apply_bridge_result` pattern. Sheeting shares all of these.

## Dispatch — same pattern

```python
# api.py:994
elif process_code == "SHEETING_PROCESS":
    create_local_sheeting_process(prelim_payload, reference_id)
```

`update_local_domain_record`'s `legacy_doctype_map` has
`"SHEETING_PROCESS": "Console Sheeting Process"`. Module-level
`apply_bridge_result` includes `"Console Sheeting Process"` in
`parent_doctypes` for callback routing.

## `create_local_sheeting_process(payload, reference_id)` — `api.py:2284`

```python
def create_local_sheeting_process(payload, reference_id):
    """Mirror Sheeting payload locally. Identity = mix_barcode of the input compound."""
    ctx = payload.get("context", {})
    posting_date, posting_time = _backdate_fields(ctx)
    items = ctx.get("items") or []    # ← TOP LEVEL items, not inside stock_entry_data
    res = _safe_local_create(
        "Console Sheeting Process",
        {
            "item_code": _pick(ctx,
                "stock_entry_data.item_code", "metadata.produced_item", "item_code"),
            "batch_no": _pick(ctx, "stock_entry_data.batch_no", "batch_no"),
            "spp_batch_no": _pick(ctx,
                "stock_entry_data.spp_batch_number",
                "spp_batch_no", "spp_batch_number", "mix_barcode"),
            "mix_barcode": _pick(ctx,
                "mix_barcode", "stock_entry_data.spp_batch_number"),
            "qty": flt(_pick(ctx, "stock_entry_data.qty", "qty")),
            "from_warehouse": _pick(ctx,
                "config.ops_source_warehouse", "config.source_warehouse",
                "stock_entry_data.from_warehouse", "from_warehouse"),
            "to_warehouse": _pick(ctx,
                "config.ops_target_warehouse", "config.target_warehouse",
                "stock_entry_data.to_warehouse", "to_warehouse"),
            "operator_name": _pick(ctx, "metadata.run_as", "operator_name"),
            "posting_date": posting_date,
            "posting_time": posting_time,
            "process_code": "SHEETING_PROCESS",
            "payload_snapshot": json.dumps(payload, indent=1),
        },
        reference_id,
        "create_local_sheeting_process",
        child_rows={"items": _normalize_items(items, _SHEETING_ITEM_KEYMAP)},
    )
    # BCR-1: Write clip mappings immediately on Console
    _write_clip_mappings_for_sheeting(payload, reference_id)
    return res
```

**Two notable patterns vs MB:**

1. **Items at the top level** (not `stock_entry_data.consumption_items`).
   Sheeting's items represent OUTPUTS, not consumed raw materials.
2. **Post-create call** to `_write_clip_mappings_for_sheeting` — this
   writes `Console Item Clip Mapping` rows linking each output clip's
   barcode to the source compound's batch.

## `_SHEETING_ITEM_KEYMAP` — `api.py:2059`

```python
_SHEETING_ITEM_KEYMAP = {
    "item_code":        "item_code",
    "batch_no":         "batch_no",
    "spp_batch_number": "spp_batch_number",   # NOT renamed (unlike _MIXING_ITEM_KEYMAP)
    "qty":              "qty",
    "s_warehouse":      "s_warehouse",
    "is_cut_bit_item":  "is_cut_bit_item",    # ← Sheeting-only
}
```

Note: unlike `_MIXING_ITEM_KEYMAP` which renames `spp_batch_number` →
`spp_batch_no`, the Sheeting keymap keeps `spp_batch_number` as-is.
This is because Console's Sheeting child doctype uses `spp_batch_number`
directly (not `spp_batch_no`).

## `_write_clip_mappings_for_sheeting(payload, reference_id)` — supporting helper

This function (defined elsewhere in `api.py`, search for the def) writes
`Console Item Clip Mapping` rows for each clip output. The mapping links:
- The new clip's barcode (e.g. `C_26C03X0-1`)
- To the source compound's batch (so downstream blanking can trace back)
- Plus context (warehouse, operator, posting timestamp)

**Why inline at create time** (not as a separate Bridge callback step):

When the operator submits Sheeting, downstream operations (Cut Bit
Transfer, Blanking) may scan a clip barcode within seconds. The clip
mapping must exist on Console **before** those downstream submissions
arrive. Doing it inline in `create_local_sheeting_process` guarantees
the mapping is in place atomically with the Sheeting record.

**BCR-1 reference:** the inline-write was introduced as part of the
Bulk Clip Release fix wave (commit prefix `BCR-1`). Before this, clip
mappings were created by the Ops Bridge callback, which left a
multi-second window where downstream Blanking scans could fail to find
the mapping.

## `apply_bridge_result` — TWO Sheeting-specific extras

`console_sheeting_process.py:44`. Same 5-step pattern as MB, plus:

### Extra 1: `legacy_spp_batch_no` capture

```python
# In step 1 (atomic per-field write), if target=Legacy and kwarg present:
if target == 'Legacy' and kwargs.get('legacy_spp_batch_no'):
    payload['legacy_spp_batch_no'] = kwargs.get('legacy_spp_batch_no')
```

The Bridge response includes `legacy_spp_batch_no` (the generated batch
number on legacy Material Transfer's FG row). Sheeting's controller
captures this onto the Console doc so downstream queries can join
Console ↔ Legacy via batch number.

### Extra 2: BCR-1 backfill on Ops Success

```python
# In step 1, if target=Ops and status=Success and kwargs.impacted_clips:
if target == 'Ops' and status == 'Success' and kwargs.get('impacted_clips'):
    from shree_polymer_console.shree_polymer_console.api import _backfill_ops_reference_for_sheeting
    _backfill_ops_reference_for_sheeting(self.reference_id, kwargs.get('impacted_clips'))
```

The Ops MES Transaction Engine response includes `impacted_clips` — a
list of clip metadata after the Stock Entry submitted. `_backfill_ops_reference_for_sheeting`
updates the `Console Item Clip Mapping` rows with the Ops batch reference,
so each clip now has BOTH Legacy and Ops batch identifiers.

## Validate hook (controller)

```python
def validate(self):
    if self.flags.get("from_local_cache"):
        return
    if not self.item_code:
        frappe.throw("Item Code is mandatory")
    if flt(self.qty) <= 0:
        frappe.throw("Produced Quantity must be greater than zero")
    if not self.get("items"):
        frappe.throw("At least one Sheeting Clip/Item is mandatory")
```

Same `from_local_cache` bypass as other Wave 1 doctypes. Strict checks
on `qty > 0` and at least one output item. Note: `items` is the child
table name on Console Sheeting Process, mapped to the legacy `batches`
child by the Bridge.

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add a new field to `_SHEETING_ITEM_KEYMAP` | Low — additive |
| Modify `_write_clip_mappings_for_sheeting` | Medium — affects downstream Cut Bit + Blanking lookup |
| Tighten `validate` | Low |
| Touch `apply_bridge_result` extras (`legacy_spp_batch_no`, `impacted_clips` backfill) | Medium — BCR-1 dependency; coordinate with `_backfill_ops_reference_for_sheeting` |
| Touch the 5-step pattern | **Highest** — same race-safety story as MB |

## Lookup against the Console Inspection unification

`update_local_domain_record`'s logic:

```python
is_inspection = bool(frappe.db.get_value(
    "Console Process Template", process_type, "is_inspection_type"
))
legacy_doctype_map = {
    "MASTER_BATCH_MIXING": "Console Master Batch Mixing",
    "FINAL_BATCH_MIXING":  "Console Final Batch Mixing",
    "SHEETING_PROCESS":    "Console Sheeting Process",   # ← here
    "CUT_BIT_TRANSFER":    "Console Cut Bit Transfer",
}
doctype = "Console Inspection" if is_inspection else legacy_doctype_map.get(process_type)
```

For Sheeting, `is_inspection_type=0` on the Process Template, so the
legacy_doctype_map's `Console Sheeting Process` is the lookup target.
Sheeting was NOT folded into the Phase 3 unification.
