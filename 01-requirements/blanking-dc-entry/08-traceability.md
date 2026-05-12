# Traceability

## Source Map

| Area | Source |
| --- | --- |
| Requirement source | Legacy `blanking_dc_entry.py`, BDE spec, `spp15.local` records |
| Spec | `02-specifications/blanking-dc-entry/` |
| Legacy DocType | `shree_polymer_custom_app/.../doctype/blanking_dc_entry/` |
| Console process | `BLANKING_DC_ENTRY` |

## FR Mapping

| Requirement IDs | Evidence |
| --- | --- |
| FR-BDE-001 to FR-BDE-013 | Legacy schema, validation, scan helpers |
| FR-BDE-014 to FR-BDE-016 | Console backend spec |
| FR-BDE-017 to FR-BDE-018 | Legacy `create___asset_movement` |
| FR-BDE-019 to FR-BDE-020 | Standard architecture and process split |

## NFR / BR Mapping

| Requirement IDs | Evidence |
| --- | --- |
| NFR-BDE-001 to NFR-BDE-012 | BDE spec risk/backend/legacy sections |
| BR-BDE-001 to BR-BDE-012 | Legacy controller and site-record branch counts |

## Drift Findings

| ID | Drift | Impact | Required correction |
| --- | --- | --- | --- |
| DRIFT-BDE-001 | Old requirement pack grouped BDE, BBIE, and BBI. | Process-specific refactor comparison was blurred. | Use `blanking-dc-entry` pack. |
| DRIFT-BDE-002 | Console callback routing omits `BLANKING_DC_ENTRY`. | Local sync status may not update. | Fix in code/test task. |
| DRIFT-BDE-003 | BDE controller callback signature differs from standard router expectation. | Adding routing alone can mis-call method. | Align signature before routing. |
| DRIFT-BDE-004 | Ops BDE creates Cutbit-to-PreForming Stock Entry while Legacy/Dash story is clip-to-bin. | Target semantics differ. | Production architecture decision needed. |
| DRIFT-BDE-005 | Console and Bridge seeders disagree on field mappings vs populate-only path. | Tests may hide mapping confusion. | Prefer tested populate contract. |

## Change Log

| Date | Change | By |
| --- | --- | --- |
| 2026-05-12 | Split BDE from grouped `blanking` requirement pack and checked `spp15.local` records. | Codex |
