# 04 — Non-functional requirements

## NFR-IE-001 — Type-aware validation parity
Console must preserve required-field and duplicate behavior by inspection type. A rule for one type must not accidentally block another type.

## NFR-IE-002 — High-volume usability
The process must handle production-scale volume; live data already exceeds 124k records.

## NFR-IE-003 — Child-row accuracy
Totals must match child defect rows and preserve rejected nos/kg precision.

## NFR-IE-004 — Audit trail
Audit must reconstruct inspector, lot, inspection type, product, machine, defect rows, rejected quantities, Stock Entry reference, batch update, and downstream trigger.

## NFR-IE-005 — Deferred batch safety
Moulding rejection stock entries must not submit with missing or wrong batch when MPE batch is required.

## NFR-IE-006 — Drift visibility
Where current code comments and SQL differ, requirement/spec must call out the mismatch so refactor does not repeat hidden assumptions.

## NFR-IE-007 — Rollback clarity
Failures must expose the linked Stock Entry or downstream document that was created before rollback.

