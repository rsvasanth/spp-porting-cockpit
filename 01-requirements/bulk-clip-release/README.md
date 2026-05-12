# Bulk Clip Release Requirements

## Status

| Field | Value |
| --- | --- |
| Requirement pack | Bulk Clip Release |
| Legacy DocType | `Bulk Clip Release` |
| Console process target | `BULK_CLIP_RELEASE` |
| Requirement identity | Separate from Sheeting and Cut Bit Transfer |
| Last updated | 2026-05-12 |

## Story

Bulk Clip Release is a clip state transition. It does not manufacture material and it should not create stock entries. The operator scans multiple sheeted clips and releases their active mappings so downstream Blanking does not see them as still occupied in sheeting WIP.

## Files

| File | Purpose |
| --- | --- |
| `01-purpose.md` | Purpose and boundaries |
| `02-actors-and-roles.md` | Actors and accountability |
| `03-functional-requirements.md` | Functional requirements |
| `04-non-functional-requirements.md` | Reliability and integrity requirements |
| `05-business-rules.md` | Load-bearing rules |
| `06-acceptance-criteria.md` | UAT scenarios |
| `07-out-of-scope.md` | Exclusions |
| `08-traceability.md` | Requirement/spec/code traceability |

## Counts

| Type | Count |
| --- | ---: |
| Functional requirements | 16 |
| Non-functional requirements | 11 |
| Business rules | 10 |
| Acceptance criteria | 7 |
| Out-of-scope items | 8 |
| Drift findings | 5 |

## Critical Legacy Facts

| Fact | Source |
| --- | --- |
| Validation requires at least one clip child row | `bulk_clip_release.py::validate` |
| Scan helper resolves `Sheeting Clip` by `barcode_text` | `validate_clip` |
| Active `Item Clip Mapping` is required | `validate_clip` |
| Submit retires mappings by `item_clip_mapping_id` | `on_submit` |
| No Stock Entry is created | Legacy controller |

## Refactor Handoff

Use this pack with `02-specifications/bulk-clip-release/`. This process is small in business logic but high-risk in wiring because barcode text, clip document name, and mapping row name can drift.
