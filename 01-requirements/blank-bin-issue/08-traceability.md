# Traceability

## Source Map

| Area | Source |
| --- | --- |
| Requirement source | Legacy `blank_bin_issue.py`, `spp15.local` records |
| Spec | `02-specifications/blank-bin-issue/` currently empty |
| Legacy DocType | `shree_polymer_custom_app/.../doctype/blank_bin_issue/` |
| Console process | `BLANK_BIN_ISSUE` |

## FR Mapping

| Requirement IDs | Evidence |
| --- | --- |
| FR-BBI-001 to FR-BBI-005 | Legacy schema and `validate_blank_issue_barcode(scan_production_lot)` |
| FR-BBI-006 to FR-BBI-012 | Legacy `validate_blank_issue_barcode(scan_bin)` and `validate_compound` |
| FR-BBI-013 to FR-BBI-016 | Legacy `validate` and child row rebuild |
| FR-BBI-017 to FR-BBI-018 | Legacy controller absence of Stock Entry/Asset Movement and process split |

## NFR / BR Mapping

| Requirement IDs | Evidence |
| --- | --- |
| NFR-BBI-001 to NFR-BBI-011 | Legacy code and site-record volumes |
| BR-BBI-001 to BR-BBI-011 | Legacy validation and MPE completion field usage |

## Drift Findings

| ID | Drift | Impact | Required correction |
| --- | --- | --- | --- |
| DRIFT-BBI-001 | Old requirement pack grouped BBI under `blanking`. | High-volume issue flow lacked dedicated identity. | Use `blank-bin-issue` pack. |
| DRIFT-BBI-002 | `02-specifications/blank-bin-issue/` is empty. | Requirement cannot trace to spec yet. | Write BBI spec from legacy and site records. |
| DRIFT-BBI-003 | Prior docs framed BBI as not shipped/planned. | Site has 68078 records. | Treat legacy flow as production reality. |
| DRIFT-BBI-004 | Legacy duplicate issue prevention code is commented. | Double-issue behavior must be verified in MPE/ops flow. | Add implementation review item. |
| DRIFT-BBI-005 | Child row is rebuilt from parent fields during validate. | Refactor may miss this implicit copy behavior. | Preserve or replace deliberately. |

## Change Log

| Date | Change | By |
| --- | --- | --- |
| 2026-05-12 | Split BBI from grouped `blanking` requirement pack and checked `spp15.local` records. | Codex |
