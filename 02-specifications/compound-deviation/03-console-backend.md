# 03 — Console backend

> Shares the **same orchestration scaffold** as MB Mixing (read [`../master-batch-mixing/03-console-backend.md`](../master-batch-mixing/03-console-backend.md)).
> `initialize_submission` / `execute_submission_step` / `_safe_local_create`
> / `apply_bridge_result` (the 5-step dance) are byte-identical between
> processes. This file documents only the `create_local_compound_deviation`
> function and the controller's stricter validate hook.

## Dispatch

`initialize_submission` does NOT have an explicit `elif process_code == "COMPOUND_DEVIATION"` branch — Compound Deviation falls through the dispatch because `is_inspection` is True for it (Console Process Template flag `is_inspection_type=1`). The dispatch routes to `create_local_inspection` (the unified Phase 3 path), which writes to the unified `Console Inspection` doctype.

**Wait — but `Console Compound Deviation` doctype exists separately?**

This is the key subtlety. The dispatch logic is:

```python
# api.py:985
is_inspection = bool(frappe.db.get_value(
    "Console Process Template", process_code, "is_inspection_type"
))
if is_inspection:
    create_local_inspection(prelim_payload, reference_id)
elif process_code == "MASTER_BATCH_MIXING":
    create_local_master_batch_mixing(...)
...
```

For Compound Deviation, `is_inspection_type` is set to 1 on the
`Console Process Template "COMPOUND_DEVIATION"`. So
`create_local_inspection` runs and writes to `Console Inspection`.

**However,** `create_local_compound_deviation` still exists at
`api.py:2474` as a **legacy code path** for pre-Phase-3 records.
The module-level `apply_bridge_result` (api.py:1980) has
`Console Compound Deviation` in its `parent_doctypes` lookup list,
so existing records can still receive callbacks.

So the current state is:
- **New deviations** → `Console Inspection` (Phase 3 unification path)
- **Pre-Phase-3 deviations** → `Console Compound Deviation` (legacy path)
- Both surfaces are supported simultaneously

## `create_local_compound_deviation(payload, reference_id)` — legacy path

`api.py:2474`. Still callable; would run if a Process Template ever has
`is_inspection_type=0` (none currently). Documented because the existing
records on production were created by this function.

```python
def create_local_compound_deviation(payload, reference_id):
    """Mirror Compound Deviation payload locally.

    Today's refactor (commit 458eb5c onwards) emits compound_inspection_data
    + a thin compound_deviation_data block. Identity comes from the CI block
    (which now matches an Accepted CI's shape exactly), deviation specifics
    from the deviation block."""
    ctx = payload.get("context", {})
    return _safe_local_create(
        "Console Compound Deviation",
        {
            # Identity — try CI block first (preferred), fall back to deviation block
            "item_code": _pick(ctx,
                "compound_inspection_data.item_code",
                "compound_deviation_data.item_code",
                "item_code"),
            "batch_no": _pick(ctx,
                "compound_inspection_data.batch_no",
                "compound_deviation_data.batch_no",
                "batch_no"),
            "spp_batch_no": _pick(ctx,
                "compound_inspection_data.spp_batch_no",
                "compound_deviation_data.spp_batch_no",
                "spp_batch_no"),
            "mix_barcode": _pick(ctx,
                "compound_inspection_data.mix_barcode",
                "compound_inspection_data.scan_compound",
                "compound_deviation_data.mix_barcode",
                "mix_barcode"),
            # Quantity — prefer CI's transfer_qty (sample is already removed)
            "qty": flt(_pick(ctx,
                "compound_inspection_data.transfer_qty",
                "compound_inspection_data.batch_qty",
                "transfer_qty", "qty")),
            # Deviation-specific
            "deviation_reason": _pick(ctx,
                "compound_deviation_data.deviation_reason", "deviation_reason"),
            "quality_approver": _pick(ctx,
                "compound_deviation_data.approver_name",
                "compound_deviation_data.approver_id",
                "compound_inspection_data.quality_approver_name"),
            "operator_name": _pick(ctx,
                "compound_inspection_data.operator_name", "operator_name"),
            "status": _pick(ctx, "compound_deviation_data.status", "status") or "Pending",
            "process_code": "COMPOUND_DEVIATION",
            "payload_snapshot": json.dumps(payload, indent=1),
        },
        reference_id,
        "create_local_compound_deviation",
    )
```

## Differences from MB's local-create

| Aspect | MB | Compound Deviation |
|---|---|---|
| Source blocks | `metadata`, `stock_entry_data`, `work_order_data`, `job_card_data`, `config` | `compound_inspection_data` + `compound_deviation_data` + `config` |
| Child rows | `consumption_items` from `stock_entry_data.consumption_items` | **None** — Deviation has no child rows |
| Identity priority | `metadata.produced_item` first | CI block fields first, then deviation block |
| QM signoff | n/a | `quality_approver` field captured |
| Status | Auto-set to `"Completed"` via doctype default | Set from `compound_deviation_data.status` payload (Accepted/Rejected/Rework) |
| BOM linkage | Implicit in BOM lookup | n/a — Deviation doesn't reference a BOM |

## Controller — stricter `validate`

`console_compound_deviation.py:9`:

```python
def validate(self):
    if self.flags.get("from_local_cache"):
        return
    if not self.item_code:
        frappe.throw("Item Code is mandatory")
    if flt(self.qty) <= 0:
        frappe.throw("Deviation Quantity must be greater than zero")
    if not self.deviation_reason or len(self.deviation_reason.strip()) < 5:
        frappe.throw("A valid Deviation Reason (min 5 chars) is mandatory")
```

Adds the `deviation_reason` minimum-length check on top of MB's pattern.
The `from_local_cache` bypass works the same way — audit-trail path
skips strict checks.

## `apply_bridge_result` — IDENTICAL to MB's 5-step pattern

The 118-line controller method is **byte-identical** to MB's. Same race-
safety story applies. **This is the file that gave the pattern its name
— the "Compound Deviation saga" tested this exact code under parallel
Ops + Legacy callback storms.**

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add a `_pick` fallback path for new payload locations | Low |
| Add new field to `Console Compound Deviation` (also update `Console Inspection` since new deviations land there) | Medium — coordinated change across two doctypes |
| Tighten `validate` (e.g. reason min length) | Low — operator UX impact |
| Loosen `validate` | **High** — was set after the saga; defends against missing QM reasoning |
| Touch `apply_bridge_result` | **Highest** — was last touched 2026-04-30, has shipped under race tests in prod |
