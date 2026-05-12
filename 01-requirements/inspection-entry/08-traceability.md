# 08 — Traceability

## Requirement to source mapping

| Requirement | Source evidence |
|---|---|
| FR-IE-001 | `Inspection Entry.inspection_type` live values and controller branching. |
| FR-IE-002 to FR-IE-005 | `InspectionEntry.validate()`. |
| FR-IE-006 to FR-IE-008 | Type-specific required fields in `validate()`. |
| FR-IE-009 | `tabInspection Entry Item` schema: defect type, rejected qty, rejected kg. |
| FR-IE-010 to FR-IE-011 | `validate_lot_number(batch_no, docname, inspection_type)`. |
| FR-IE-012 | `make_stock_entry(self)` for Line/Patrol/Lot kg rejection transfer. |
| FR-IE-013 | `submit_inspection_stock_entry_immediately()` and MPE cascade helper. |
| FR-IE-014 | `make_inc_stock_entry()` and `submit_deflash_receipt_entry()`. |
| FR-IE-015 | `submit__vs_pdir()`, `make_vs_pdir_stock_entry()`, and no-rejection visual path. |

## Live site anchors

| Query result | Interpretation |
|---|---|
| 124,197 total records; 120,663 submitted | IE is a production-scale process, not only a planned Wave 4 screen. |
| 6 live inspection type values | Requirement must not collapse IE to Line/Patrol/Lot only. |
| Lot/Line/Incoming/Final Visual each exceed 27k records | Multiple branches are operationally significant. |
| Patrol has 9,820 records | Patrol is real and is required by MPE. |

## Drift findings

| Drift | Impact |
|---|---|
| Old grouped requirement treated IE as only three moulding variants | It missed Incoming, Final Visual, and Visual live branches. |
| Old grouped requirement called IE unshipped | Live site has 124k IE records. |
| IE `on_submit` comment says Patrol is included in trigger query, but SQL checks Line + Lot | Refactor must choose executable behavior or deliberately fix with approval. |
| MPE helper cascades Line + Patrol, while IE helper cascades Line + Lot + Patrol after MPE exists | There are two overlapping cascade paths that need spec alignment. |
| Spec folder is empty | Requirement is based on legacy controller and site records until spec is written. |

## Change log

| Date | Change |
|---|---|
| 2026-05-12 | Split from grouped moulding pack into standalone Inspection Entry requirements using legacy code and `spp15.local` evidence. |

