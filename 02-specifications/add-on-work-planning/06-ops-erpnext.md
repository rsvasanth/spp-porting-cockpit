# 06 — Ops ERPNext (v15) — planned

## Generic engine path (Charter Principle 2)

AOWP uses the **generic TransactionEngine** — no dedicated Ops handler. The standard ERPNext doctypes (`Work Order`, `Job Card`) are well-modeled in the engine's action sequence.

## Planned `Console Process Template` actions

```python
# ADD_ON_WORK_PLANNING template's actions:
[
  {
    "action_id": "create_work_order",
    "action": "create_doc",
    "params": {
      "doctype": "Work Order",
      "company": "{{ config.company }}",
      "production_item": "{{ items[0].item_produced }}",
      "qty": "{{ items[0].target_qty }}",
      "bom_no": "{{ items[0].bom }}",
      "source_warehouse": "{{ config.ops_source_warehouse }}",
      "fg_warehouse": "{{ config.ops_target_warehouse }}",
      "use_multi_level_bom": 0,
      "skip_transfer": 1,
      "transfer_material_against": "Work Order",
      "planned_start_date": "{{ date }}",
      "lot_number": "{{ lot_number }}",   # custom field
      "__submit": True,
    },
    "store_as": "work_order_name"
  },
  # Then for each item row, create a Job Card.
  # The engine supports loops via "for_each" action:
  {
    "action_id": "create_job_cards",
    "action": "for_each",
    "iterate": "items",
    "params": {
      "doctype": "Job Card",
      "work_order": "{{ work_order_name }}",
      "operation": "{{ item.operation }}",
      "workstation": "{{ item.work_station }}",
      "for_quantity": "{{ item.target_qty }}",
      "lot_number": "{{ lot_number }}",
      "__submit": True,
    }
  }
]
```

## Custom field on Ops Work Order

Ops Work Order needs a custom field `lot_number` to receive Console's Lot #. This requires a one-time customization:

```python
# In Ops shree_polymer_ops/customizations or via Customize Form:
{
  "doctype": "Work Order",
  "fieldname": "lot_number",
  "fieldtype": "Data",
  "label": "Lot Number",
  "read_only": 1,
  "in_list_view": 1,
}
```

Similar custom field needed on Ops Job Card.

## Documents created on Ops per AOWP submission

| Document | Quantity |
|---|---|
| `Shree Polymer MES Log` | 1 |
| `Work Order` | 1 (with `lot_number` custom field set) |
| `Job Card` | N (one per AOWP item row, each with `lot_number` set) |

## Idempotency

Standard `Shree Polymer MES Log` lookup by `reference_id`.

## Cross-step output chaining

The Ops engine supports placeholder resolution: Step 1's `work_order_name` output is available in step 2's params as `{{ work_order_name }}`. This is required for Job Card → Work Order linkage.

If the engine doesn't natively support `for_each` action, fallback: list N create_job_card actions explicitly (one per row, looped at build_transaction_payload time).

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add a new field to the Work Order action params | Low |
| Modify the `for_each` items iteration | Medium |
| Bypass the generic engine with a dedicated handler | **High** — violates Charter Principle 2 without justification |
| Remove `lot_number` from Work Order action | **Highest** — breaks Pattern A invariant |
