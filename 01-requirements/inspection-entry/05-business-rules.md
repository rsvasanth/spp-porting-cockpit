# 05 — Business rules

## BR-IE-001 — Final Visual is duplicate-exempt
Legacy duplicate prevention excludes Final Visual Inspection; other types are unique per `lot_no + inspection_type` once submitted.

## BR-IE-002 — Line and Patrol are MPE prerequisites
MPE requires submitted Line and Patrol IE for the lot. Lot Inspection is part of IE but is not the MPE prerequisite enforced by current MPE validation.

## BR-IE-003 — Rejection kg drives stock movement
For moulding-related Line/Patrol/Lot entries, a rejection Stock Entry is created only when `total_rejected_qty_kg > 0`.

## BR-IE-004 — MPE owns final batch for moulding rejection SE
Inspection rejection Stock Entries may be created before the produced batch exists. MPE later updates batch_no and submits pending entries.

## BR-IE-005 — Mould Specification owns piece-to-kg conversion
For moulding inspections, one-piece kg comes from active Mould Specification. Missing spec is a blocking data-quality issue.

## BR-IE-006 — Incoming and Final Visual are not moulding prerequisites
Incoming Inspection and Final Visual Inspection are real live types, but they do not satisfy MPE's Line/Patrol gate.

## BR-IE-007 — Comments are not authority
The current legacy file has comments saying a query includes Patrol while the trigger query checks Line + Lot. The executable SQL is authority; the mismatch must be treated as drift.

