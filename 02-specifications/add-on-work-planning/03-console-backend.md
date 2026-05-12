# 03 — Console backend (planned)

> Shares orchestration scaffold with MB. This file documents AOWP-specific work.

## Planned dispatch

```python
# api.py:initialize_submission
elif process_code == "ADD_ON_WORK_PLANNING":
    create_local_add_on_work_planning(prelim_payload, reference_id)
```

`update_local_domain_record.legacy_doctype_map` extends to include `"ADD_ON_WORK_PLANNING": "Console Add On Work Planning"`.

`apply_bridge_result.parent_doctypes` extends to include `"Console Add On Work Planning"`.

## Planned `create_local_add_on_work_planning`

```python
def create_local_add_on_work_planning(payload, reference_id):
    """Mirror AOWP locally with Lot # generation."""
    ctx = payload.get("context", {})
    posting_date, posting_time = _backdate_fields(ctx)

    # Lot # generation — happens HERE, before legacy/ops sync
    lot_number = _generate_lot_number(posting_date)

    items = ctx.get("items") or []

    res = _safe_local_create(
        "Console Add On Work Planning",
        {
            "planning_type":     "Add On",
            "date":              posting_date,
            "shift_type":        _pick(ctx, "shift_type"),
            "supervisor_id":     _pick(ctx, "supervisor_id"),
            "lot_number":        lot_number,   # ← Console-authored
            "posting_date":      posting_date,
            "posting_time":      posting_time,
            "operator_name":     _pick(ctx, "metadata.run_as"),
            "process_code":      "ADD_ON_WORK_PLANNING",
            "payload_snapshot":  json.dumps(payload, indent=1),
        },
        reference_id,
        "create_local_add_on_work_planning",
        child_rows={"items": _normalize_planning_items(items, lot_number)},
    )
    return res

_PLANNING_ITEM_KEYMAP = {
    "item_produced":  "item_produced",
    "work_station":   "work_station",
    "mould":          "mould",
    "bom":            "bom",
    "target_qty":     "target_qty",
}

def _normalize_planning_items(items, lot_number):
    """Same as _normalize_items but cascades lot_number into each child row."""
    out = []
    for raw in items or []:
        row = {k_dst: raw.get(k_src) for k_src, k_dst in _PLANNING_ITEM_KEYMAP.items() if raw.get(k_src)}
        if row:
            row["lot_number"] = lot_number   # cascade
            out.append(row)
    return out
```

## Lot # generator

```python
def _generate_lot_number(posting_date):
    """Console-authored Lot # generator. Format: LOT-YYYYMMDD-NNN.
    Daily sequence, gapless on success."""
    from frappe.utils import getdate
    date_str = getdate(posting_date).strftime("%Y%m%d")

    # Get the highest existing sequence for this date
    last = frappe.db.sql(
        "SELECT lot_number FROM `tabConsole Add On Work Planning` "
        "WHERE date = %s AND docstatus = 1 "
        "ORDER BY lot_number DESC LIMIT 1",
        posting_date, as_dict=True
    )

    if last and last[0]["lot_number"]:
        last_seq = int(last[0]["lot_number"].split("-")[-1])
        next_seq = last_seq + 1
    else:
        next_seq = 1

    return f"LOT-{date_str}-{next_seq:03d}"
```

**Race-safety concern:** Two concurrent submissions on the same `posting_date` could both compute the same `next_seq`. Mitigations (in order of preference):

1. **DB-level unique constraint** on `Console Add On Work Planning.lot_number` — second insert collides cleanly, returns DuplicateEntryError, retry
2. **Sequence doctype** with row-level locking on a "Lot # Counter" Singleton
3. **SELECT FOR UPDATE** pattern within `_generate_lot_number`

Option 1 is simplest and Frappe-native. Implementation choice TBD.

## Planned controller

```python
class ConsoleAddOnWorkPlanning(Document):
    def validate(self):
        if self.flags.get("from_local_cache"):
            return
        if not self.lot_number:
            frappe.throw("Lot Number is mandatory")
        if not self.shift_type:
            frappe.throw("Shift Type is mandatory")
        if not self.get("items"):
            frappe.throw("At least one item row is required")
        # Cascade lot_number to children
        for item in self.items:
            if not item.lot_number:
                item.lot_number = self.lot_number
        # Multi-BOM rejection per item
        for item in self.items:
            bom_count = frappe.db.count("Console BOM",
                {"item": item.item_produced, "is_active": 1})
            if bom_count > 1:
                frappe.throw(f"Multiple active BOMs for {item.item_produced} — deactivate duplicates")

    def before_insert(self):
        self.process_code = "ADD_ON_WORK_PLANNING"
        if not self.submitted_by:
            self.submitted_by = frappe.session.user

    def on_submit(self):
        # Standard Transaction Log upsert
        ...

    @frappe.whitelist()
    def apply_bridge_result(self, target, status, remote_name=None, error=None):
        # ── 5-step BYTE-IDENTICAL pattern ──
        ...
```

## What Hermes workers can change

| Change | Risk |
|---|---|
| Touch `_generate_lot_number` | **High** — concurrency-sensitive; needs test |
| Add new field to AOWP doctype | Low |
| Modify multi-BOM check (e.g. allow override with reason) | Medium — affects multiple legacy controllers too |
| Touch the 5-step pattern | **Highest** — saga regression |
