# 05 — Legacy ERPNext mirror

## Target doctype

`Inspection Entry` on `spp15.local` (defined in `shree_polymer_custom_app`). This is the polymorphic 53-field legacy inspection doctype with 6 inspection_types — same target as the prior Wave 4 plan, but the source is now `SPP Quality Control` rather than `Console Inspection`.

## Sync direction

Console → Legacy, one-way. Legacy `Inspection Entry` is a historical/reporting mirror; no Legacy edits propagate back to Console.

## Mirror lifecycle

- **On Console submit (`docstatus = 1`)** → Legacy Bridge creates an `Inspection Entry` with matching field values, `docstatus = 1`.
- **On Console cancel (`docstatus = 2`)** → Legacy Bridge cancels the mirror `Inspection Entry` (`docstatus = 2`).

If the Legacy create fails:
- Console `legacy_sync_status` = Failed.
- The local Console record stays at `docstatus = 1`.
- Retry via the standard `Console Transaction Log` retry button.

## Field mapping (Console → Legacy)

| `SPP Quality Control` field | `Inspection Entry` field | Notes |
|---|---|---|
| `naming_series`-derived name | `name` | Legacy uses its own naming; Console name stored in `console_reference` |
| `inspection_type` | `inspection_type` | Direct map (string values must match Legacy enum) |
| `lot_no` | `lot_no` | Direct map |
| `item_code` | `item_code` | Direct map |
| `workstation` | `workstation` | Direct map (Moulding only) |
| `mould_reference` | `mould_no` | Field rename |
| `inspector` (Employee) | `inspected_by_id` + `inspected_by_name` | Resolve Employee → name on the Bridge side |
| `operator` (Employee) | `operator_id` + `operator_name` | Same pattern |
| `total_inspected_qty` | `total_inspected_qty` | Direct map |
| `total_accepted_qty` | `total_accepted_qty` | Direct map |
| `total_rejected_qty` | `total_rejected_qty` | Direct map |
| `total_rejected_qty_kg` | `total_rejected_qty_kg` | Conditional (Moulding) |
| `status` | `status` | Direct map (`Accepted` / `Rejected` / `Rework`) |
| `reference_id` | `console_reference_id` | For round-trip diagnostics |
| `stock_entry_reference` | `ops_stock_entry_reference` | For round-trip diagnostics |
| (child) reading rows | (child) reading rows | Map parameter + reading_value + reading_status |

## Sync engine

Handled by `shree_polymer_legacy_bridge` (the existing app). QC adds a new handler module:

`shree_polymer_legacy_bridge/handlers/spp_quality_control.py` exposing:

- `create_inspection_entry_from_qc(payload)`
- `cancel_inspection_entry_from_qc(legacy_name)`
- `_apply_qc_identity_to_doc(doc, payload)` — mirror of the existing `_apply_compound_identity_to_doc` helper pattern from the 2026-04-30 refactor

## Identity resolution

Unlike Compound, QC identity is single-strategy:
- `lot_no` → resolve Legacy `Job Card` by lot → resolve Legacy `Work Order` → derive any needed Legacy references.

The 6-strategy `_resolve_compound_identity` lookup chain is NOT applicable. QC's Legacy handler has its own simpler `_resolve_qc_identity` function.

## What QC does NOT do on Legacy

- Does NOT write Legacy `Stock Entry` (Ops owns stock).
- Does NOT write Legacy `Compound Inspection` (that's Compound family only).
- Does NOT trigger Legacy workflow rules beyond the standard `Inspection Entry` submit hook.

## Schema version coupling

Legacy `Inspection Entry` is on `shree_polymer_custom_app` (ERPNext v14). Any field rename on the Legacy side requires a coordinated update in this mapping table. The Bridge handler MUST fail loudly (not silently skip) on missing target fields.
