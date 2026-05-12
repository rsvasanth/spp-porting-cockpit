# 03 — Console backend — unified `create_local_inspection`

> Shares the same orchestration scaffold as MB Mixing (read [`../master-batch-mixing/03-console-backend.md`](../master-batch-mixing/03-console-backend.md)). This file documents the **unification-specific** function `create_local_inspection` at `api.py:2647` and the controller's family-driven validation.

## Phase 3 dispatch routing

`initialize_submission` (`api.py:985`) checks the Process Template's `is_inspection_type` flag and routes accordingly:

```python
# api.py:985
is_inspection = bool(frappe.db.get_value(
    "Console Process Template", process_code, "is_inspection_type"
))
if is_inspection:
    create_local_inspection(prelim_payload, reference_id)   # ← Phase 3 unified path
elif process_code == "MASTER_BATCH_MIXING":
    create_local_master_batch_mixing(...)
# ... per-type branches for non-inspection processes
```

When any Process Template has `is_inspection_type=1`, its submissions take the unified path. This applies to:
- `COMPOUND_INSPECTION`
- `COMPOUND_DEVIATION`
- Future `LINE_INSPECTION` / `PATROL_INSPECTION` / `LOT_INSPECTION` (Wave 4)
- Future Production-family inspection types

**Pre-Phase-3 functions** (`create_local_compound_inspection`, `create_local_compound_deviation`) still exist in `api.py` but are now unreachable through `initialize_submission` for new submissions. They remain as fallback for hand-coded callsites and historical reference.

## `create_local_inspection(payload, reference_id)` — the unified function

`api.py:2647`. The function:

1. **Reads `process_code`** from payload context
2. **Looks up the Process Template** to determine `inspection_family` (`Compound` / `Production` / other)
3. **Dispatches identity extraction** based on family:
   - Compound: `mix_barcode`, `spp_batch_no` from `compound_inspection_data` or `compound_deviation_data` blocks
   - Production: `lot_no` from top-level or `compound_inspection_data.lot_no`
   - Other: best-effort fallback
4. **Dispatches readings extraction**:
   - Compound: `_build_compound_readings_from_payload` walks `compound_inspection_data.readings`
   - Production: `_build_production_readings_from_payload` walks defect rows
5. **Common header fields** populated regardless of family (item_code, batch_no, inspector_id, quality_approver_id)
6. **Calls `_safe_local_create`** with the unified `Console Inspection` doctype, identity fields, common headers, and child rows

```python
def create_local_inspection(payload, reference_id):
    """Unified audit-trail write for any inspection type."""
    ctx = payload.get("context", {})
    process_code = _pick(ctx, "metadata.process_code", "process_code") or payload.get("process_code")
    if not process_code:
        frappe.log_error(...); return None

    template = frappe.db.get_value(
        "Console Process Template", process_code,
        ["inspection_family", "is_inspection_type"], as_dict=True,
    ) or {}
    family = template.get("inspection_family") or "Compound"

    if family == "Compound":
        identity = {
            "mix_barcode": _pick(ctx,
                "compound_inspection_data.mix_barcode",
                "compound_inspection_data.scan_compound",
                "compound_deviation_data.mix_barcode",
                "mix_barcode"),
            "spp_batch_no": _pick(ctx, ...),
            "lot_no": "",
        }
        readings = _build_compound_readings_from_payload(ctx)
    elif family == "Production":
        identity = {
            "mix_barcode": "",
            "spp_batch_no": "",
            "lot_no": _pick(ctx, "lot_no", "compound_inspection_data.lot_no"),
        }
        readings = _build_production_readings_from_payload(ctx)

    # Common header fields (item_code, batch_no, inspector_id, quality_approver_id, posting_date/time)
    # ... extraction snipped ...

    return _safe_local_create(
        "Console Inspection",
        { ...identity, ...common_headers, "process_code": process_code, "inspection_type": process_code },
        reference_id,
        "create_local_inspection",
        child_rows={"readings": readings, "reading_specs": specs},
    )
```

**Key invariants:**

| Aspect | Detail |
|---|---|
| `inspection_type` field | Set to `process_code` (Link to Process Template — Process Template's name is the process_code) |
| Family-driven identity | Compound vs Production picks different field sets |
| `_pick` fallback paths | Survives Dash payload shape drift across CI / CD / future variants |
| `_safe_local_create` audit-trail bypass | Same `flags.from_local_cache + ignore_validate` invariant as MB |
| Child rows | Polymorphic — `Console Inspection Reading` accommodates any reading_type |

## Controller — `console_inspection.py`

`console_inspection.py:9`. The unified controller:

```python
class ConsoleInspection(Document):
    """Unified Console-side inspection record. Replaces the per-type doctypes
    (Console Compound Inspection, Console Compound Deviation, Console Quality Inspection).
    Discriminated by inspection_type (Link → Console Process Template) — the family
    (Compound / Production) drives identity field selection (mix_barcode vs lot_no),
    Bridge sequence dispatch, and per-type validation."""

    def before_insert(self):
        """Auto-fetch process_code and inspection_family from the linked Process Template."""
        if self.inspection_type:
            tmpl = frappe.db.get_value(
                "Console Process Template", self.inspection_type,
                ["process_code", "inspection_family"], as_dict=True,
            )
            if tmpl:
                if not self.process_code:      self.process_code     = tmpl.process_code
                if not self.inspection_family: self.inspection_family = tmpl.inspection_family
        if not self.submitted_by:
            self.submitted_by = frappe.session.user

    def validate(self):
        """Schema-level invariants + type-specific dispatch."""
        if self.flags.get("from_local_cache"):
            return

        if not self.inspection_type:
            frappe.throw("Inspection Type is mandatory")
        if self.inspection_family == "Compound" and not self.mix_barcode:
            frappe.throw("Mix Barcode is mandatory for Compound family inspections")
        if self.inspection_family == "Production" and not self.lot_no:
            frappe.throw("Lot No is mandatory for Production family inspections")

        # Type-specific dispatch — call the registered validation function
        dispatch = frappe.db.get_value(
            "Console Process Template", self.inspection_type, "validation_dispatch_method"
        )
        if dispatch:
            from frappe.utils import get_attr
            try:
                fn = get_attr(dispatch)   # e.g. "shree_polymer_console.api.validate_compound_inspection"
                fn(self)
            except Exception as e:
                frappe.log_error(f"Inspection dispatch failed: {dispatch}", str(e))
                # Decide: re-raise or soft-fail. Currently logs and continues.

    def on_submit(self):
        # Standard Transaction Log upsert
        ...

    @frappe.whitelist()
    def apply_bridge_result(self, target, status, remote_name=None, error=None, **kwargs):
        """Same 5-step race-safe pattern as MB and CD. Byte-identical implementation."""
        # ... 5 steps ...
```

**Key validation invariants:**

| Invariant | Where |
|---|---|
| `inspection_type` mandatory | Schema-level — set always |
| Compound family → mix_barcode mandatory | Family-driven schema check |
| Production family → lot_no mandatory | Family-driven schema check |
| Type-specific validation via dispatch | Registered Python function per Process Template; called at validate |
| `from_local_cache` bypass | Audit-trail invariant preserved |

## Validation dispatch — how a new inspection_type registers logic

To add type-specific validation for `COMPOUND_INSPECTION`:

1. Define the function in `shree_polymer_console.api`:
   ```python
   def validate_compound_inspection(doc):
       """Compound Inspection-specific validation: status auto-derived from readings."""
       if doc.flags.get("from_local_cache"):
           return
       # BOM-driven reading min/max check
       for reading in doc.readings:
           spec = ...  # fetch from Console Inspection Reading Spec
           if reading.value < spec.min or reading.value > spec.max:
               reading.result = "Fail"
           else:
               reading.result = "Pass"
       # Derive status
       has_fail = any(r.result == "Fail" for r in doc.readings)
       doc.status = "Rejected" if has_fail else "Accepted"
   ```

2. Set on Process Template:
   ```
   Console Process Template "COMPOUND_INSPECTION":
     validation_dispatch_method: "shree_polymer_console.api.validate_compound_inspection"
   ```

3. The controller's `validate()` will pick this up automatically.

**Frappe-native, no DSL.** Validation logic lives in Python with full Frappe API access.

## Apply_bridge_result — same 5-step pattern as other Wave 1+ doctypes

`Console Inspection.apply_bridge_result` implements the byte-identical 5-step pattern:

1. Atomic per-field `db.set_value` for THIS leg only
2. Re-read both legs from DB (atomic snapshot)
3. Aggregate `sync_status`
4. Self-heal — if both legs Synced but `sync_status != Success`, correct it
5. Fresh-doc auto-submit — `frappe.get_doc(name)` to avoid stale in-memory state

> See [`../compound-deviation/03-console-backend.md`](../compound-deviation/03-console-backend.md) §5-step pattern for the full code listing. **Identical byte-for-byte** across all three doctypes (Console Inspection, Console Compound Inspection, Console Compound Deviation).

## Module-level dispatcher includes both unified + legacy

`api.py::apply_bridge_result` (the public Bridge callback entry point at `api.py:1946`) walks a `parent_doctypes` list to find the parent record by `reference_id`. The list:

```python
parent_doctypes = [
    "Console Inspection",                  # Phase 3 unified (new submissions)
    "Console Master Batch Mixing",
    "Console Final Batch Mixing",
    "Console Sheeting Process",
    "Console Cut Bit Transfer",
    "Console Compound Deviation",          # Pre-Phase-3 (legacy)
    "Console Compound Inspection",         # Pre-Phase-3 (legacy)
    "Console Blanking DC Entry",
]
```

**Order matters:** `Console Inspection` is FIRST so Phase 3 records are found quickly. Pre-Phase-3 doctypes are last (they're only checked if no Phase 3 record matches the reference_id).

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add a new inspection_type via Process Template + validation function | Low — pattern is designed for this |
| Modify `create_local_inspection`'s identity extraction for a family | Medium — affects all submissions of that family |
| Touch `apply_bridge_result` 5-step pattern | **Highest** — saga regression risk; needs concurrency test on ALL 3 doctypes |
| Add a new field to `Console Inspection` | Medium — must coordinate with pre-Phase-3 doctypes if cross-doctype reporting matters |
| Deprecate `Console Compound Inspection` / `Console Compound Deviation` | **Architecture review** — depends on backfill epic |
| Change `inspection_family` taxonomy | **Architecture review** — affects identity extraction logic + downstream Bridge dispatch |
