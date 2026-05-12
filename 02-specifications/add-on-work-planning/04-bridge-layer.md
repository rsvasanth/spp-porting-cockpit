# 04 — Bridge layer (planned)

## Planned mapping seeder

```python
def seed_add_on_work_planning_mapping():
    """ADD_ON_WORK_PLANNING → Add On Work Planning (legacy)"""
    field_mappings = [
        {"console_field": "reference_id",    "legacy_field": "reference_id"},
        {"console_field": "reference_id",    "legacy_field": "referenceid"},  # legacy alt spelling
        {"console_field": "date",            "legacy_field": "date"},
        {"console_field": "shift_type",      "legacy_field": "shift_type"},
        {"console_field": "supervisor_id",   "legacy_field": "supervisor_id"},
        {"console_field": "lot_number",      "legacy_field": "lot_number"},   # ← Console-authored
        # Child table items
        {"is_child_table": 1, "child_table_fieldname": "items",
         "console_field": "items.item_produced", "legacy_field": "item_to_manufacture"},
        {"is_child_table": 1, "child_table_fieldname": "items",
         "console_field": "items.work_station", "legacy_field": "work_station"},
        {"is_child_table": 1, "child_table_fieldname": "items",
         "console_field": "items.mould", "legacy_field": "mould"},
        {"is_child_table": 1, "child_table_fieldname": "items",
         "console_field": "items.bom", "legacy_field": "bom"},
        {"is_child_table": 1, "child_table_fieldname": "items",
         "console_field": "items.target_qty", "legacy_field": "target_qty"},
        {"is_child_table": 1, "child_table_fieldname": "items",
         "console_field": "lot_number", "legacy_field": "lot_number"},   # broadcast to children
    ]
    _upsert_mapping("ADD_ON_WORK_PLANNING", "Add On Work Planning", field_mappings)
```

## `create_planning_with_jobcards` — whitelisted Legacy method

The plan doc's recommendation: instead of relying on Bridge sequence engine for multi-step chained creation, add a single Legacy whitelisted method that atomically creates Work Order + Job Cards.

```python
# In shree_polymer_custom_app, exposed as @frappe.whitelist()
@frappe.whitelist()
def create_planning_with_jobcards(payload):
    """Atomic Work Order + Job Cards creation for AOWP.

    Called from the Bridge after the AOWP record is inserted.
    Returns Work Order + Job Card names. Rolls back on any failure."""
    try:
        aowp_doc = frappe.get_doc("Add On Work Planning", payload["aowp_name"])

        # 1. Create Work Order
        wo = frappe.new_doc("Work Order")
        wo.company = "SPP"
        wo.naming_series = "MFG-WO-.YYYY.-"
        wo.production_item = aowp_doc.items[0].item_to_manufacture  # assuming single item or use first
        wo.qty = sum(it.target_qty for it in aowp_doc.items)
        wo.bom_no = aowp_doc.items[0].bom
        wo.source_warehouse = ...
        wo.fg_warehouse = ...
        wo.planned_start_date = aowp_doc.date
        wo.docstatus = 1
        wo.save(ignore_permissions=True)

        # 2. Create Job Cards (one per item row)
        job_cards = []
        for it in aowp_doc.items:
            # Workstation override check
            mo_override = frappe.db.get_value("Mixing Operation",
                {"source_warehouse": ..., "operation": ...},
                ["workstation", "operation"], as_dict=True)
            workstation = (mo_override.workstation if mo_override else it.work_station)
            operation_name = (mo_override.operation if mo_override else "Mixing")

            jc = frappe.new_doc("Job Card")
            jc.work_order = wo.name
            jc.operation = operation_name
            jc.workstation = workstation
            jc.for_quantity = it.target_qty
            jc.time_required = 20  # default minutes
            jc.lot_number = aowp_doc.lot_number
            jc.docstatus = 1
            jc.save(ignore_permissions=True)
            job_cards.append(jc.name)

            # Update AOWP child row with job_card reference
            frappe.db.set_value("Add On Work Plan Item", it.name, "job_card", jc.name)

        return {
            "status": "Success",
            "work_order": wo.name,
            "job_cards": job_cards,
            "lot_number": aowp_doc.lot_number,
        }
    except Exception:
        frappe.db.rollback()   # ← atomic rollback
        return {"status": "Failed", "message": str(frappe.get_traceback())}
```

**Atomicity guarantee:** Frappe rolls back on exception. Partial state (WO created but JCs failed) is rolled back. Bridge sees Failed; Console reports Failed; no orphan WOs on Legacy.

## Idempotency

`find_existing_record` for `ADD_ON_WORK_PLANNING`:

```python
if process_type == "ADD_ON_WORK_PLANNING":
    if reference_id:
        name = frappe.db.get_value(
            "Add On Work Planning",
            {"reference_id": reference_id}, "name"
        )
        if name:
            return frappe._dict({"name": name, "doctype": "Add On Work Planning"})
    return None
```

Standard `reference_id`-based idempotency (similar to MB).

## Legacy auto-generation disabled

When Bridge passes `lot_number` in payload, Legacy `Add On Work Planning.before_insert` (or `validate`) must check: if `lot_number` is present, skip the auto-generator.

```python
# Legacy controller change required
def before_insert(self):
    if not self.lot_number:
        self.lot_number = self._generate_legacy_lot_number()
    # else: honor Console-provided value
```

This is a one-time Legacy controller change as part of the Wave 3 implementation.

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add new mapping rows | Low |
| Modify `create_planning_with_jobcards` workstation override logic | Medium — affects every AOWP submission |
| Change atomic rollback semantics | High |
| Remove `lot_number` mapping | **Forbidden** — Pattern A invariant |
