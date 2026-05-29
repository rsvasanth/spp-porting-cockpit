> [!WARNING]
> **DECOMMISSIONED REQUIREMENT**
> As of 2026-05-20, the unification requirement is obsolete. The active design of record relies on separate doctypes. Do not follow the patterns described in this file.

# 04 — Bridge layer

> Read [`../compound-deviation/04-bridge-layer.md`](../compound-deviation/04-bridge-layer.md) for the empty-`field_mappings` pattern and the shared helpers (`_resolve_compound_identity`, `_lookup_legacy_stock_entry`, `_apply_compound_identity_to_doc`, `_apply_compound_readings_to_doc`, `_apply_compound_header_to_doc`). This file documents how the **unified** Console Inspection routes through the Bridge.

## The Bridge sees process_code, not the unified doctype

The Bridge's `sync_process_transaction(payload, process_type, reference_id)` is **process_code-driven**, not doctype-driven. The fact that Phase 3 submissions all land in one Console doctype (`Console Inspection`) is invisible to the Bridge — the Bridge sees the payload's `process_code` (e.g. `COMPOUND_INSPECTION` or `COMPOUND_DEVIATION`) and routes via `Legacy Sync Mapping`.

This means:
- The same `seed_compound_inspection_mapping` and `seed_compound_deviation_mapping` calls still produce the right mapping rows
- `populate_compound_inspection_fields` and `populate_compound_deviation_fields` still run as before
- The Bridge has NO new code path for the unification
- The legacy doctype written is still `Compound Inspection` (single doctype, used by both)

## Mapping seeders unchanged

Per [`../compound-deviation/04-bridge-layer.md`](../compound-deviation/04-bridge-layer.md) §Empty `field_mappings` pattern:

- `seed_compound_inspection_mapping` — populated field_mappings (TBD section in mapping seeder; mirrors mixing pattern)
- `seed_compound_deviation_mapping` — empty `field_mappings`; all population in Python

Both still exist after the unification. New Production-family mappings (Wave 4) will follow the same pattern.

## Shared identity pipeline

The Bridge's `populate_compound_inspection_fields` and `populate_compound_deviation_fields` BOTH call the same helpers:

```python
def populate_compound_inspection_fields(doc, data=None):
    """Pipeline: identity → SE lookup → identity write → readings."""
    if not data: return
    identity  = _resolve_compound_identity(data)
    se_lookup = _lookup_legacy_stock_entry(identity)
    _apply_compound_identity_to_doc(doc, identity, se_lookup)
    _apply_compound_header_to_doc(doc, data)
    _apply_compound_readings_to_doc(doc, data)


def populate_compound_deviation_fields(doc, data=None):
    """Same as CI + deviation extras layered on top."""
    if not data: return
    identity  = _resolve_compound_identity(data)
    se_lookup = _lookup_legacy_stock_entry(identity)
    _apply_compound_identity_to_doc(doc, identity, se_lookup)
    _apply_compound_header_to_doc(doc, data)
    _apply_compound_readings_to_doc(doc, data)
    # ... source warehouse fallback ...
    # ... quantity fields ...
    _apply_deviation_extras(doc, data)
```

**Saga origin:** the helper extraction in 2026-04-30 (commit `1df2de8` family) consolidated 200+ lines of duplicated identity logic into these shared functions. Pre-refactor, CI and CD had separate copies that drifted.

> Detailed walkthrough of each helper in [`../compound-deviation/05-legacy-erpnext.md`](../compound-deviation/05-legacy-erpnext.md).

## Two-block payload pattern

Both CI and CD payloads have:

| Block | Purpose | Required for |
|---|---|---|
| `compound_inspection_data` | Identity (mix_barcode, spp_batch_no, item_code, batch_no, scan_compound, transfer_qty, batch_qty, operator_id) + readings list | CI, CD (mirror) |
| `compound_deviation_data` | QM signoff (status, approver_id, approver_name, deviation_reason) + qty | CD only |

The Phase 3 `create_local_inspection` reads from both blocks for CD; reads only `compound_inspection_data` for CI. **The unified Console doctype stores the same fields regardless** — `quality_approver_*` fields are populated only for CD-type submissions, NULL for CI-type.

## Production family Bridge (Wave 4 planned)

For Production-family inspection types (Line / Patrol / Lot):
- Legacy doctype is `Inspection Entry` (different from `Compound Inspection`)
- Mapping: `seed_inspection_entry_mapping` (TBD)
- Bridge populate function: `populate_inspection_entry_fields` (TBD)
- Identity pipeline: lot_no → Add On Work Plan Item lookup (NOT the compound 6-strategy chain)
- Readings: defect-row driven, not measurement-driven

The unification's design accommodates this — `inspection_family="Production"` drives a different identity extraction in `create_local_inspection`, and the Bridge has separate per-process mappings.

## Factory-requirement skip (same as Compound Deviation spec)

`initialize_submission` skips the Legacy leg when:

```python
is_rejected_inspection = (
    process_code == "COMPOUND_INSPECTION"
    and context.get("status") == "Rejected"
)
```

A Rejected Compound Inspection routes Ops-only; the gap is closed later by a Compound Deviation submission.

This rule was implemented before the unification but survives unchanged. The unification doesn't relax or modify it.

## Bridge response handling

Same as Compound Deviation — synchronous response read, no webhook. Console's `execute_submission_step` reads the Bridge's HTTP response, updates `Console Transaction Log`, calls `update_local_domain_record` which routes to the right doctype's `apply_bridge_result`.

`update_local_domain_record` (`api.py:~2950`) has this routing:

```python
is_inspection = bool(frappe.db.get_value(
    "Console Process Template", process_type, "is_inspection_type"
))

legacy_doctype_map = {
    "MASTER_BATCH_MIXING": "Console Master Batch Mixing",
    "FINAL_BATCH_MIXING":  "Console Final Batch Mixing",
    "SHEETING_PROCESS":    "Console Sheeting Process",
    "CUT_BIT_TRANSFER":    "Console Cut Bit Transfer",
}

doctype = "Console Inspection" if is_inspection else legacy_doctype_map.get(process_type)
```

For any `is_inspection_type=1` process, the callback lands on `Console Inspection`. The pre-Phase-3 fallback lookup happens at the global `apply_bridge_result` level (which scans `parent_doctypes` list including the legacy per-type doctypes).

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add a new Production-family inspection_type | Low — pattern is designed for this; requires new Process Template + mapping seeder + populate function |
| Modify the 6-strategy SE lookup | **High** — affects every Compound family inspection; requires zero-hit proof for any strategy removal |
| Touch `populate_compound_inspection_fields` or `populate_compound_deviation_fields` | High — affects both unified and pre-Phase-3 records |
| Modify the factory-requirement skip | **Architecture review** — operations decision |
| Add a new mapping field for Compound Inspection | Low — additive |
| Remove a populated mapping row | Medium — verify legacy field is no longer required |
