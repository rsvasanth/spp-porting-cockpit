# Traceability

## Source Map

| Area | Source |
| --- | --- |
| Requirement source | Legacy `material_transfer.py`, Sheeting spec, merged `sheeting-and-cutting` pack |
| Spec | `02-specifications/sheeting-process/` |
| Legacy DocType | `shree_polymer_custom_app/.../doctype/material_transfer/` |
| Console process | `SHEETING_PROCESS` |

## FR Mapping

| Requirement IDs | Evidence |
| --- | --- |
| FR-SHT-001 to FR-SHT-004 | Sheeting Dash/spec flow |
| FR-SHT-005 to FR-SHT-009 | `Material Transfer Item` and Sheeting spec output rows |
| FR-SHT-010 to FR-SHT-011 | Dash mass-balance behavior in spec |
| FR-SHT-012 to FR-SHT-013 | `create_local_sheeting_process` and `_write_clip_mappings_for_sheeting` |
| FR-SHT-014 to FR-SHT-017 | Bridge `populate_sheeting_fields` and Legacy `Material Transfer` |
| FR-SHT-018 to FR-SHT-020 | Standard orchestration and user correction to process-scoped identity |

## NFR / BR Mapping

| Requirement IDs | Evidence |
| --- | --- |
| NFR-SHT-001 to NFR-SHT-013 | Sheeting spec backend, Bridge, test/risk sections |
| BR-SHT-001 to BR-SHT-012 | Legacy validation plus BCR-1 spec decision |

## Drift Findings

| ID | Drift | Impact | Required correction |
| --- | --- | --- | --- |
| DRIFT-SHT-001 | Live requirement tree had merged `sheeting-and-cutting`. | Refactor handoff could compare one implementation against mixed requirements. | Replace with separate `sheeting-process` pack. |
| DRIFT-SHT-002 | Merged requirements used `SHC` numbering. | IDs did not match process-specific spec identity. | Use `SHT`. |
| DRIFT-SHT-003 | Legacy `Material Transfer.validate_sheeting_clips` checks clip release state. | The Sheeting spec/requirements must make clear this is a downstream gate, not BCR behavior. | Keep cross-link only. |
| DRIFT-SHT-004 | BCR-1 inline mapping can look like implementation detail. | Future refactor might move it behind callback and reopen scan race. | Make it BR-SHT-006. |
| DRIFT-SHT-005 | `mix_barcode` synthesis depends on legacy lookup format. | Missing this can break Compound Inspection downstream lookup. | Keep as FR-SHT-017. |

## Change Log

| Date | Change | By |
| --- | --- | --- |
| 2026-05-12 | Split from merged `sheeting-and-cutting` into process-scoped Sheeting pack. | Codex |
