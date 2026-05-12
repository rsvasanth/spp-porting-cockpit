# 08 — Traceability

## Requirement to source mapping

| Requirement | Source evidence |
|---|---|
| FR-MPE-001 | `validate_lot_number(batch_no)` checks Moulding Job Card by `batch_code`. |
| FR-MPE-002 | `validate_lot_number` checks submitted Line and Patrol Inspection Entries. |
| FR-MPE-003 | `validate_lot_number` joins `Blank Bin Issue Item`, `Job Card`, and `Blank Bin Issue` with `is_completed = 0`. |
| FR-MPE-004 | `validate_lot_number` / `validate_bin` check active `Item Bin Mapping`. |
| FR-MPE-005 | BOM checks in `validate_lot_number`. |
| FR-MPE-006 | `validate()` required field checks. |
| FR-MPE-009 | `validate_tolerance()` uses `SPP Settings.production_tolerance`. |
| FR-MPE-010 | `validate_get_line_ins_qty()` sums Line/Patrol rejection pieces and Mould Specification average weight. |
| FR-MPE-011 | `validate()` derives injection flag from Workstation name. |
| FR-MPE-014 to FR-MPE-019 | `make_stock_entry()`, `submit_inspection_stock_entries_from_moulding()`, and `update_bins()`. |

## Live site anchors

| Query result | Interpretation |
|---|---|
| 30,006 MPE records; 28,931 submitted | MPE is not theoretical; requirement must reflect production reality. |
| 613 injection records | Injection path is real but small compared with non-injection. |
| 25,069 records with no reason code | Reason code cannot be mandatory for ordinary happy path. |

## Drift findings

| Drift | Impact |
|---|---|
| Old grouped moulding requirement merged IE and MPE | Refactor analysis was harder because one pack covered two controllers. |
| Old requirement called MPE unshipped Wave 5 | Live site has substantial MPE production records. |
| Old requirement hard-coded 1% mass-balance throw | Current legacy code uses `production_tolerance` and returns a message, not a failed status. |
| Old requirement assumed fixed `T-<lot>-<seq>` format | Legacy uses `generate_batch_no`; docs should describe generator contract rather than invented string format. |
| MPE cascade covers Line/Patrol in one helper | Inspection Entry has separate broader cascade behavior; both must be documented separately. |

## Change log

| Date | Change |
|---|---|
| 2026-05-12 | Split from grouped moulding pack into standalone MPE requirements using legacy code and `spp15.local` evidence. |

