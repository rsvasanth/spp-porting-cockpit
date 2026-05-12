# 03 — Functional requirements

## FR-MPE-001 — Lot scan validation
The system must validate a scanned lot against an open `Job Card` with operation `Moulding`. Completed moulding Job Cards must be rejected.

## FR-MPE-002 — Inspection prerequisite
The system must block MPE submission unless submitted `Line Inspection` and submitted `Patrol Inspection` records exist for the same lot.

## FR-MPE-003 — Blank Bin Issue dependency
The system must require at least one submitted `Blank Bin Issue` item for the lot with `is_completed = 0`.

## FR-MPE-004 — Bin active-state validation
Each issued bin must resolve to an active `Item Bin Mapping` row. Manually released or retired bins must block submission.

## FR-MPE-005 — BOM compound compatibility
The bin compound must be valid for the active BOM of the item being produced by the Job Card.

## FR-MPE-006 — Required production fields
MPE must require produced weight, Job Card, compound, batch details, curing time, number of lifts, running cavities, operator, and moulding date.

## FR-MPE-007 — Future date block
Moulding date must not be later than the current business date.

## FR-MPE-008 — Balance-bin handling
If `no_balance_bin` is false, at least one balance-bin row must be captured. Balance bin gross/net validation must prevent impossible remainder weights.

## FR-MPE-009 — Production tolerance check
The system must apply the same tolerance behavior as legacy `validate_tolerance`: compare produced weight against issued bin quantity using `SPP Settings.production_tolerance`. The current legacy function returns a message rather than a hard failure, so Console requirements must not silently convert this to a hard 1% throw without owner approval.

## FR-MPE-010 — Line/Patrol rejection weight
The system must calculate line rejection weight from submitted Line and Patrol Inspection Entry rejected piece counts and active Mould Specification average product weight.

## FR-MPE-011 — Injection moulding variant
The system must detect injection moulding from workstation data and include `purged_compound` and `compound_leakage` in output weight calculations when applicable.

## FR-MPE-012 — Shell item variant
When the BOM/mould specification requires shell consumption, the system must locate shell source warehouse, batch, kg, nos, and item before booking production.

## FR-MPE-013 — Source stock validation
Before creating the manufacturing Stock Entry, the system must validate actual warehouse stock for required source material.

## FR-MPE-014 — Manufacturing Stock Entry
On submit, MPE must create and submit an ERPNext `Stock Entry` with purpose/type `Manufacture`, source warehouse from the Work Order, target warehouse from the Work Order, consumed source lines, and finished item line.

## FR-MPE-015 — Finished batch generation
The system must use the legacy batch generator contract for the produced item. Legacy currently calls `generate_batch_no(batch_id="T" + scan_lot_number, item=production_item, qty=weight + line_rejection_qty)` and then links the generated batch to the Stock Entry.

## FR-MPE-016 — Job Card completion
After successful Stock Entry submit, the system must update Job Card time logs, completed quantity, number of lifts, running cavities, curing time, status, and docstatus according to legacy behavior.

## FR-MPE-017 — Work Order completion
After successful production booking, the system must complete the linked Work Order when legacy does so.

## FR-MPE-018 — Inspection stock-entry cascade
After MPE Stock Entry submit, the system must update submitted Line and Patrol Inspection Entries with the produced batch and submit their pending rejection Stock Entries when present.

## FR-MPE-019 — Bin closure
After successful Stock Entry submit, consumed `Blank Bin Issue Item` rows must be marked completed and the bin/material mapping updated according to legacy `update_bins`.

## FR-MPE-020 — Failure rollback
If stock entry creation, batch linking, stock validation, or cascade submission fails, the process must rollback or leave a clearly recoverable state with the failed target reference visible.

