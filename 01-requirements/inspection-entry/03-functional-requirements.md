# 03 — Functional requirements

## FR-IE-001 — Unified inspection type
The system must support legacy `Inspection Entry.inspection_type` as a discriminator, not assume a separate DocType per inspection type.

## FR-IE-002 — Required lot/context
Inspection Entry must require `lot_no` and inspector code before save/submit.

## FR-IE-003 — Required child rows
Inspection Entry must require at least one child item row before save.

## FR-IE-004 — Future posting date block
Posting date must not be later than the current business date.

## FR-IE-005 — Duplicate prevention
For all inspection types except Final Visual Inspection, only one submitted Inspection Entry may exist for the same `lot_no + inspection_type`.

## FR-IE-006 — Moulding inspection quantity
Line, Patrol, and Lot Inspection must require `inspected_qty_nos`.

## FR-IE-007 — Incoming/final quantity
Incoming Inspection and Final Inspection must require `total_inspected_qty_nos`.

## FR-IE-008 — Final Visual quantity-after-rejection
Final Visual Inspection must calculate quantity after rejection from inspected quantity minus rejected quantity.

## FR-IE-009 — Defect child rows
Each `Inspection Entry Item` row must capture defect type and rejected quantity; rejected weight must be stored where calculated.

## FR-IE-010 — Moulding lot lookup
For Line and Patrol, lot validation must resolve the Job Card by `batch_code`, return mould reference, workstation, Work Order, Job Card, production item, and MPE completion status.

## FR-IE-011 — One-piece weight lookup
For moulding inspections, the system must derive `one_no_qty_equal_kgs` from active Mould Specification using mould reference and production item.

## FR-IE-012 — Rejection stock entry
For Line, Patrol, and Lot inspections with rejected kg, the system must create a draft rejection Material Transfer Stock Entry to the configured rejection warehouse.

## FR-IE-013 — MPE batch cascade
When a corresponding MPE is available, inspection rejection Stock Entries must receive the MPE produced batch before submission.

## FR-IE-014 — Incoming inspection stock entry
Incoming/final inspection rejection must use its own Stock Entry path and may trigger Deflashing Receipt submission behavior.

## FR-IE-015 — Final Visual / PDIR path
Final Visual Inspection must support its legacy stock movement path, including rejection transfer and no-rejection production path where applicable.

## FR-IE-016 — Rollback
When stock entry creation or downstream submission fails, the system must clear target references or revert docstatus in the same recoverable way as legacy.

