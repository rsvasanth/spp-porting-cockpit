# 05 — Business rules

## BR-MPE-001 — Line and Patrol are mandatory
MPE cannot proceed unless Line Inspection and Patrol Inspection are submitted for the lot. Lot Inspection may exist but is not the prerequisite enforced by legacy MPE lot validation.

## BR-MPE-002 — Open Blank Bin Issue is mandatory
The lot must have submitted Blank Bin Issue rows where `is_completed = 0`. Without open issued bins, there is no material to consume.

## BR-MPE-003 — Retired or released bins are invalid
If `Item Bin Mapping` cannot find an active row for the scanned bin, the bin is treated as released/retired and must block MPE.

## BR-MPE-004 — BOM owns material compatibility
The issued compound must be present in the active BOM path for the Job Card's production item. Operator selection cannot override the BOM.

## BR-MPE-005 — Tolerance source is SPP Settings
Legacy tolerance uses `SPP Settings.production_tolerance` against total issued bin quantity. The older grouped requirement's fixed 1% hard-block statement is not proven by current controller code and must be treated as drift until owner-confirmed.

## BR-MPE-006 — Injection moulding detection follows workstation
Legacy sets `is_injection_moulding = 1` when the workstation name contains `INJECTION` or the historical spelling `INJUCTION`.

## BR-MPE-007 — Produced output includes inspection rejection
For manufacturing booking, completed quantity uses `weight + line_rejection_qty`; line rejection quantity is derived from Line/Patrol rejected pieces and Mould Specification average weight.

## BR-MPE-008 — Shell consumption adjusts output weight
If shell item is found, `weight_without_shell` is reduced by shell kg while shell source batch and quantities are captured.

## BR-MPE-009 — MPE submits Stock Entry immediately
Legacy now submits the manufacture Stock Entry immediately in `make_stock_entry`; deferred-only language is stale.

## BR-MPE-010 — MPE closes the production chain
Successful MPE marks Job Card completed, completes the Work Order in current legacy behavior, closes consumed bins, and enables downstream finished-goods flows.

