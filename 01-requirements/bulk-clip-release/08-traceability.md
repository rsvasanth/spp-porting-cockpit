# Traceability

## Source Map

| Area | Source |
| --- | --- |
| Requirement source | Legacy `bulk_clip_release.py`, Bulk Clip Release spec, merged `sheeting-and-cutting` pack |
| Spec | `02-specifications/bulk-clip-release/` |
| Legacy DocType | `shree_polymer_custom_app/.../doctype/bulk_clip_release/` |
| Console process | `BULK_CLIP_RELEASE` |

## FR Mapping

| Requirement IDs | Evidence |
| --- | --- |
| FR-BCR-001 to FR-BCR-007 | Legacy `validate_clip` and Console scan validator spec |
| FR-BCR-008 to FR-BCR-011 | Console backend spec and controller intent |
| FR-BCR-012 | Legacy/Ops behavior: no Stock Entry |
| FR-BCR-013 to FR-BCR-015 | Standard orchestration plus Bridge/Ops barcode drift findings |
| FR-BCR-016 | User correction to process-scoped requirement identity |

## NFR / BR Mapping

| Requirement IDs | Evidence |
| --- | --- |
| NFR-BCR-001 to NFR-BCR-011 | Bulk Clip Release spec risk and backend sections |
| BR-BCR-001 to BR-BCR-010 | Legacy controller, Ops handler, Bridge drift |

## Drift Findings

| ID | Drift | Impact | Required correction |
| --- | --- | --- | --- |
| DRIFT-BCR-001 | Live requirement tree had BCR inside `sheeting-and-cutting`. | BCR wiring risks were hidden inside a broad motion. | Separate `bulk-clip-release` pack. |
| DRIFT-BCR-002 | Merged numbering used `SHC`. | Requirement IDs did not match process code. | Use `BCR`. |
| DRIFT-BCR-003 | Console spec says local create/callback routing may be incomplete. | Audit-first path may not be fully wired. | Keep as requirement gap for implementation review. |
| DRIFT-BCR-004 | Bridge seeder maps child fields that do not match Legacy child JSON. | Declarative document path may create bad child rows. | Test and patch mapping separately. |
| DRIFT-BCR-005 | Direct helper may filter by clip doc name while Dash sends barcode text. | Releases can miss physical barcode scans. | Require barcode-to-doc-name resolution. |

## Change Log

| Date | Change | By |
| --- | --- | --- |
| 2026-05-12 | Split from merged `sheeting-and-cutting` into process-scoped Bulk Clip Release pack. | Codex |
