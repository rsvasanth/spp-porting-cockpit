# Blank Bin Inward Entry Requirements

## Status

| Field | Value |
| --- | --- |
| Requirement pack | Blank Bin Inward Entry |
| Legacy DocType | `Blank Bin Inward Entry` |
| Console process target | `BLANK_BIN_INWARD` |
| Requirement prefix | `BIE` |
| Requirement identity | Separate from BDE and BBI |
| Last updated | 2026-05-12 |

## Story

Blank Bin Inward Entry handles the filled bin after BDE. In production, it is primarily the route that releases/reclassifies bin contents into cut-bit stock, while still supporting a normal asset movement path.

## Site Reality Check

Read-only query on `spp15.local`:

| Metric | Value |
| --- | ---: |
| Total `Blank Bin Inward Entry` records | 1945 |
| Submitted records | 1919 |
| `move_to_cut_bit_warehouse = 0` records | 86 |
| `move_to_cut_bit_warehouse = 1` records | 1859 |

## Files

| File | Purpose |
| --- | --- |
| `01-purpose.md` | Purpose and process position |
| `02-actors-and-roles.md` | Actors and accountability |
| `03-functional-requirements.md` | Functional requirements |
| `04-non-functional-requirements.md` | Quality requirements |
| `05-business-rules.md` | Load-bearing rules |
| `06-acceptance-criteria.md` | UAT criteria |
| `07-out-of-scope.md` | Exclusions |
| `08-traceability.md` | Traceability and drift |

## Counts

| Type | Count |
| --- | ---: |
| Functional requirements | 18 |
| Non-functional requirements | 11 |
| Business rules | 11 |
| Acceptance criteria | 8 |
| Out-of-scope items | 8 |
| Drift findings | 5 |

## Critical Legacy Facts

| Fact | Source |
| --- | --- |
| Naming series is `BBIE-.#####` | `blank_bin_inward_entry.json` |
| Child rows are required | `BlankBinInwardEntry.validate` |
| Gross weight is required per child row | `validate` |
| `move_to_cut_bit_warehouse` drives submit branch | `on_submit` |
| Repack branch creates `Stock Entry` purpose `Repack` | `make_stock_entry` |
| Normal branch creates native `Asset Movement` | `asset_movement` |
| Repack branch retires `Item Bin Mapping` | `asset_movement(..., "release")` |

## Refactor Handoff

Use this pack with `02-specifications/blank-bin-inward-entry/` and the legacy `blank_bin_inward_entry` DocType.
