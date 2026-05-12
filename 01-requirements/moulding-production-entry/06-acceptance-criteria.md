# 06 — Acceptance criteria

## AC-MPE-001 — Happy path, non-injection
Given a lot with open Moulding Job Card, submitted Line and Patrol IE, and open Blank Bin Issue rows, when the operator submits MPE with valid weight and bins, then a Manufacture Stock Entry is submitted, the produced batch is linked, Job Card is completed, and bins are closed.

## AC-MPE-002 — Missing Line Inspection
Given Patrol exists but Line does not, when the operator scans the lot for MPE, then the system blocks submission and names Line Inspection as missing.

## AC-MPE-003 — Missing Patrol Inspection
Given Line exists but Patrol does not, when the operator scans the lot for MPE, then the system blocks submission and names Patrol Inspection as missing.

## AC-MPE-004 — No open Blank Bin Issue
Given a valid moulding Job Card but no open submitted Blank Bin Issue items, when MPE validates the lot, then it fails with the no-bin-issue condition.

## AC-MPE-005 — Released bin
Given a bin has no active Item Bin Mapping row, when the operator scans it in MPE, then the system rejects the bin as already released/invalid.

## AC-MPE-006 — Injection moulding
Given the Job Card workstation name contains `INJECTION` or `INJUCTION`, when MPE validates, then `is_injection_moulding` is set and purge/leakage quantities are included in output calculations.

## AC-MPE-007 — Tolerance parity
Given `SPP Settings.production_tolerance` is configured, when produced weight is outside legacy tolerance range, then Console behavior matches legacy: warning vs block must be exactly the signed-off target behavior.

## AC-MPE-008 — Inspection cascade
Given Line/Patrol Inspection Entries have rejection Stock Entry references, when MPE submits and gets a produced batch, then those Stock Entry Detail rows receive the produced batch and draft entries are submitted.

## AC-MPE-009 — Rollback on stock failure
Given source stock is insufficient or Stock Entry submit fails, when MPE submits, then no false Job Card completion or bin closure remains.

