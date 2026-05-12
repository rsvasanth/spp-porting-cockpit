# 10 — Risks and decisions

## Plan-vs-reality deltas

These were intentional simplifications or discoveries during spec writing.
Each needs an explicit decision before any Hermes worker changes behavior.

| # | Delta | Old requirement said | Legacy actually does | Recommendation |
|---|---|---|---|---|
| 1 | Tolerance hardcoding | "hardcoded 1%" | `SPP Settings.production_tolerance` (configurable, returns warning message not throw) | **Configurable warning** — treat `production_tolerance` as authoritative; do not reintroduce 1% hard block without owner sign-off |
| 2 | Batch format | `T-<lot>-<seq>` fixed format | `generate_batch_no(batch_id="T"+scan_lot_number, ...)` contract | **Do not prescribe internal format** — the `generate_batch_no` contract owns this. If format changes, the contract changes, not the MPE spec |
| 3 | SE submission timing | Old requirement assumed deferred submission | Immediate submit inside `make_stock_entry()` | **Immediate submit** — `manual_on_submit` is deprecated; do not implement the deferred pattern |
| 4 | Inspection cascade | "submit inspection SEs" — implicit | `submit_inspection_stock_entries_from_moulding()` updates batch on IE + submits draft SEs | **Documented as MPE-specific** — IE has its own broader cascade; both documented separately, do not conflate |
| 5 | `line_rejection_qty` calculation | "rejection weight" | Piece count × Mould Spec avg_blank_wtproduct_gms (theoretical, not weighed) | **Theoretical weight** — this is by design; the comment in `validate_inspection_qty` confirms the weighed approach was intentionally replaced |
| 6 | Inspection Entry rollback on MPE cancel | Assumed cascade cancel | Commented out in `rollback_entries()` — no rollback of Line/Patrol IE | **No IE rollback** — intentional. If IE is cancelled, downstream traceability breaks. MPE cancel only rolls back SE, JC, WO |
| 7 | BBI + IBM rollback on MPE cancel | Assumed full reversal | `on_cancel` does NOT reverse BBI item `is_completed` or IBM qty/retired state | **No BBI/IBM rollback on cancel** — intentional. The bins were consumed; cancelling MPE cancels the SE but does not undo the physical consumption |

## Cross-doctype invariants Hermes must NOT break

These invariants are load-bearing for the MPE → upstream chain. Breaking one
layer doesn't immediately fail but compounds downstream.

| # | Invariant | Where enforced | Breaks if… |
|---|---|---|---|
| 1 | Lot must resolve to open moulding Job Card with `batch_code` | `validate_lot_number()` (whitelisted API) | Job Card `batch_code` field renamed or removed; operation filter changes |
| 2 | Submitted Line + Patrol Inspection must exist for lot | `validate_lot_number()` — queries `docstatus = 1, inspection_type IN ('Line Inspection', 'Patrol Inspection')` | Inspection Entry doctype renamed; inspection_type values changed |
| 3 | Open BBI rows must map to active (non-retired) IBM | `validate_lot_number()` — `WHERE IB.is_retired = 0 AND BI.is_completed = 0` | IBM `is_retired` field removed or logic changed |
| 4 | Compound in bins must be in active BOM path | `validate_lot_number()` — checks `item_code` against BOM items | BOM structure changed; BOM activation logic modified |
| 5 | `generate_batch_no` contract uses `batch_id = "T" + scan_lot_number` | `make_stock_entry()` line 763 | Prefix `T` changed or removed; scan_lot_number format changed |
| 6 | Produced batch cascades to Line + Patrol IE `batch_no` + `spp_batch_number` | `submit_inspection_stock_entries_from_moulding()` | Inspection Entry schema changed; SE batch update path broken |
| 7 | Bin closure: full bins → IBM `is_retired=1`, partial bins → IBM qty updated | `update_bins()` — two branches | BBI item or IBM field names change; asset movement logic broken |
| 8 | `is_injection_moulding` derived from workstation name on every validate | `validate()` — checks `INJECTION` / `INJUCTION` in workstation_name | Workstation naming convention changes; injection variant not detected |
| 9 | Tolerance is a warning (msgprint), not a throw | `validate()` — `frappe.msgprint(tolerance_val.get("message"))` | Changed to throw; would block legitimate production variances |
| 10 | Stock Entry submitted immediately in `make_stock_entry()` | `make_stock_entry()` — `stock_entry_doc.docstatus = 1; .save()` | Reverted to deferred submission; rollback logic no longer matches |

## What makes this spec hard to change

MPE is a terminal booking — it has **more cross-system dependencies than any
other doctype in the chain**:

```
MPE references:
├── Job Card (workstation → is_injection_moulding, qty, bom_no, etc.)
├── Work Order (source/fg warehouse, production_item, bom_no, operations)
├── Workstation (workstation_name → INJECTION detection)
├── Asset (mould_reference → asset_name for Mould Spec lookup)
├── Mould Specification (avg_blank_wtproduct_gms, shell_weight)
├── Blank Bin Issue Item (consumed bins, is_completed)
├── Item Bin Mapping (is_retired, qty, balance tracking)
├── Inspection Entry (Line + Patrol, lot_no, batch_no, spp_batch_number)
├── Stock Entry (stock_entry_reference → created and submitted SE)
├── SPP Settings (production_tolerance, maximum__allowed_qty, mat_percentage,
│                 from_location, to_location, unit_2_warehouse,
│                 purge_scrap_warehouse, default_sheeting_warehouse)
├── BOM (shell item group check, compound validation)
├── UOM Conversion Detail (shell weight from conversion factor)
└── Batch (batch_id, disabled check, expiry_date check)
```

A single MPE submit touches **15+ doctypes** across the system. Changes to any
of these field names, table structures, or logic can silently break MPE without
an end-to-end test.

## Decisions waiting on you

| Question | Why it matters | Recommendation |
|---|---|---|
| Reinstate hard tolerance throw? | Old requirements mentioned 1% hard block | **No** — configurable warning is the correct behavior. If shop floor needs a hard block, make it a SPP Settings flag (`production_tolerance_strict = 1`). |
| Promote `batch_details` from JSON to Table child? | Better UX, queryable, less fragile | **Defer** — JSON is already working in production with 30K records. Adding a Table requires BBI + IBM schema changes that affect multiple doctypes. |
| Add `manual_on_submit` equivalent for recovery? | Legacy kept it for backward compat | **No** — immediate submit is the correct pattern. If SE submission fails, `rollback_entries()` handles recovery. |
| Should MPE cancel roll back BBI/IBM state? | Current behavior doesn't | **No** — physical consumption happened. If there's a legitimate MPE cancel (wrong entry, data error), BBI/IBM state should stay. Add a separate correction flow if needed. |
| Persist `line_rejection_qty` in Console doc? | Enables traceability + audit | **Yes** — store the calculated value on `Console Moulding Production Entry` for audit trail. Small additive change. |
| Add monitoring for `validate_lot_number` failures? | 30K+ records, inspection prerequisites commonly missing | **Yes** — emit `frappe.log_error` on each lot validation failure with missing inspection type. Track failure rate by inspection type to prioritize IE coverage. |
| Should injection moulding detection be a configuration rather than workstation name substring? | Substring check is fragile | **Defer** — the workstation name check handles both `INJECTION` and `INJUCTION` (typo). A configuration table is cleaner but requires migration. Revisit in Wave 3. |

## When in doubt — pause and ask

This spec covers 1,429 lines of legacy controller logic that evolved over
~2 years of production use. Each apparent inconsistency may be an intentional
design decision. Before changing any behavior:

1. Run graphify on `moulding_production_entry` for the specific function chain
2. Check live `spp15.local` records for the specific scenario
3. Surface a proposal before coding
4. Wait for Reviewer worker + you to sign off

The cost of asking is one turn; the cost of breaking MPE on a live shop floor
