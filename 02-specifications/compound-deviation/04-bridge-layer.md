# 04 — Bridge layer

> Read [`../master-batch-mixing/04-bridge-layer.md`](../master-batch-mixing/04-bridge-layer.md)
> for the `sync_process_transaction` entry function and mapping engine
> walkthrough. Compound Deviation **bypasses the mapping engine entirely**
> and uses a Python populate function. This file documents that pattern.

## The "empty `field_mappings`" pattern

`console_mapping_seeder.py::seed_compound_deviation_mapping`:

```python
def seed_compound_deviation_mapping():
    """COMPOUND_DEVIATION → Compound Inspection (legacy doctype)

    Field population is handled entirely by populate_compound_deviation_fields()
    in the Legacy Bridge (sync_api.py). The mapping record itself only needs to
    exist with the correct legacy_doctype so the Bridge knows which doc to create.

    Key behaviour in the Bridge populate function:
      • scan_compound  ← mix_barcode  (NOT Ops SABB batch ID)
      • batch_no       ← resolved via SE Detail.spp_batch_number or SE Detail.mix_barcode
      • stock_id       ← SE Detail parent (Stock Entry name on Legacy)
      • source_warehouse ← U3-Store - SPP INDIA
      • quality_approver readings + approver ID set from deviation payload
    """
    _upsert_mapping(
        "COMPOUND_DEVIATION",
        "Compound Inspection",   # Legacy doctype name
        field_mappings=[],       # ← intentionally empty
        is_active=1,
    )
```

**Why empty `field_mappings`?** The Bridge's mapping engine handles
declarative, dot-path → legacy-field transformations well. But Compound
Deviation needs:

1. **Identity resolution via SE lookup** — must call `_resolve_compound_identity` then `_lookup_legacy_stock_entry`. The mapping engine can't run multi-step logic.
2. **Conditional field setting** — only set `cavity_no=1` if currently empty; only override `scan_compound` if Console payload's `mix_barcode` differs from Ops SABB ID
3. **Shared logic with Compound Inspection** — the same identity pipeline applies to both; encoded as Python helpers, not as mapping rows

The empty-mappings approach delegates everything to
`populate_compound_deviation_fields(legacy_doc, payload_data)` in
`sync_api.py:1319`. This is also true for Compound Inspection (which
uses `populate_compound_inspection_fields`).

## What the Bridge does for a Compound Deviation payload

`sync_api.py::sync_process_transaction` flow when `process_type=COMPOUND_DEVIATION`:

```python
# 1. Idempotency — generic lookup
existing = find_existing_record(reference_id, payload, process_type)
if existing: return cached_result

# 2. Get mapping (legacy_doctype = "Compound Inspection")
mapping = frappe.get_doc("Legacy Sync Mapping", "COMPOUND_DEVIATION")

# 3. Build empty Compound Inspection doc
legacy_doc = frappe.new_doc("Compound Inspection")   # not "Compound Deviation"!
legacy_doc.reference_id = reference_id

# 4. Apply field_mappings — list is empty, loop does nothing
for map_row in mapping.field_mappings: ...   # never iterates

# 5. Process-specific enrichment
if process_type == "COMPOUND_DEVIATION":
    populate_compound_deviation_fields(legacy_doc, payload_data)   # ← all the work

# 6. Insert + submit
legacy_doc.insert(...)
legacy_doc.submit()
```

The Python populate function does **all** field population, all identity
resolution, all the cavity_no fallback. The mapping engine just creates
an empty doctype shell.

## Status-conditional target selection

`initialize_submission` (`api.py:1009-1015`) has a **factory requirement**
skip for rejected inspections:

```python
# FACTORY REQUIREMENT: Do not route rejected inspections to Legacy.
# They will be synced later via Deviation.
is_rejected_inspection = (process_code == "COMPOUND_INSPECTION"
                          and context.get("status") == "Rejected")

if sync_strategy in ["Legacy Bridge Only", "Both (Parallel)"]:
    if not bridge_url: frappe.throw("Legacy Bridge URL not configured")
    if not is_rejected_inspection:    # ← skip Legacy leg for rejected CIs
        targets.append({"url": bridge_url, "type": "Legacy", ...})
```

The flow:
- Compound Inspection submission with `status=Rejected` → only Ops leg fires
- Compound Deviation submission (any status) → both legs fire normally
  (because `process_code != "COMPOUND_INSPECTION"`)

This is **why Compound Deviation matters operationally**: it's the surface
that synchronizes rejected compounds to Legacy. Without it, the legacy
Compound Inspection record never gets created for a rejected lot, and
stock ledger reconciliation breaks.

## Bridge response handling

The Bridge returns the standard shape:

```json
{
  "status": "Success",
  "reference_doctype": "Compound Inspection",
  "reference_name": "CI-2026-...",
  "log_name": "BLOG-2026-...",
  "stock_entry_reference": "MAT-STE-..."   // SE created by legacy CI's on_submit
}
```

Console's `execute_submission_step` reads this and runs the standard
callback chain into `apply_bridge_result` — same 5-step dance as MB.

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add a field to `populate_compound_deviation_fields` | Low — adds to existing function; preserve `if not doc.get(field)` idempotency pattern |
| Switch from empty-mapping to populated mapping | **High** — would require duplicating identity logic; defeats the saga's refactor |
| Touch `_resolve_compound_identity` or `_lookup_legacy_stock_entry` | **High** — shared with Compound Inspection; the 6-strategy chain has historical reasons |
| Modify the status-conditional skip in `initialize_submission` | High — factory requirement; needs operations buy-in |
| Change the empty-mapping pattern for OTHER processes (e.g. blanking) | Medium — would mean splitting populate logic across two layers |
