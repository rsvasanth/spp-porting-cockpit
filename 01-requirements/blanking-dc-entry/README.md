# Blanking DC Entry Requirements

## Status

| Field | Value |
| --- | --- |
| Requirement pack | Blanking DC Entry |
| Legacy DocType | `Blanking DC Entry` |
| Console process target | `BLANKING_DC_ENTRY` |
| Requirement prefix | `BDE` |
| Requirement identity | Separate from Blank Bin Inward Entry and Blank Bin Issue |
| Last updated | 2026-05-12 |

## Story

Blanking DC Entry is the point where released sheeting clip material is weighed into a physical blanking bin. The process creates the bin-content identity that downstream inward, issue, inspection, and moulding flows depend on.

## Site Reality Check

Read-only query on `spp15.local`:

| Metric | Value |
| --- | ---: |
| Total `Blanking DC Entry` records | 13260 |
| Submitted records | 13186 |
| `from_blank_bin_inward = 0` records | 13235 |
| `from_blank_bin_inward = 1` records | 25 |

## Files

| File | Purpose |
| --- | --- |
| `01-purpose.md` | Purpose, boundary, and process position |
| `02-actors-and-roles.md` | Actors and accountability |
| `03-functional-requirements.md` | Functional requirements |
| `04-non-functional-requirements.md` | Quality and reliability requirements |
| `05-business-rules.md` | Load-bearing business rules |
| `06-acceptance-criteria.md` | UAT criteria |
| `07-out-of-scope.md` | Exclusions |
| `08-traceability.md` | Requirement/spec/code traceability |

## Counts

| Type | Count |
| --- | ---: |
| Functional requirements | 20 |
| Non-functional requirements | 12 |
| Business rules | 12 |
| Acceptance criteria | 8 |
| Out-of-scope items | 8 |
| Drift findings | 5 |

## Critical Legacy Facts

| Fact | Source |
| --- | --- |
| Naming series is `BDCE-.#####` | `blanking_dc_entry.json` |
| Future posting dates are blocked | `BlankingDCEntry.validate` |
| At least one child row is required | `BlankingDCEntry.validate` |
| Gross weight is mandatory per row | `BlankingDCEntry.validate` |
| Net weight is calculated as gross minus bin weight | `BlankingDCEntry.validate` |
| Submit creates `Item Bin Mapping` unless `from_blank_bin_inward` | `create___asset_movement` |
| Submit creates native `Asset Movement` | `create___asset_movement` |
| Clip validation checks active mapping, BOM, stock, and warehouse | `validate_clip_barcode` |

## Refactor Handoff

Use this pack with `02-specifications/blanking-dc-entry/` and the legacy `blanking_dc_entry` DocType. Do not use BBIE or BBI requirements to satisfy BDE.
