# Blank Bin Issue Requirements

## Status

| Field | Value |
| --- | --- |
| Requirement pack | Blank Bin Issue |
| Legacy DocType | `Blank Bin Issue` |
| Console process target | `BLANK_BIN_ISSUE` |
| Requirement prefix | `BBI` |
| Requirement identity | Separate from BDE and BBIE |
| Last updated | 2026-05-12 |

## Story

Blank Bin Issue binds a physical bin to a moulding Job Card. It is not a stock movement. It is the logical reservation that tells Moulding Production Entry which bin material can be consumed for a Lot.

## Site Reality Check

Read-only query on `spp15.local`:

| Metric | Value |
| --- | ---: |
| Total `Blank Bin Issue` records | 68078 |
| Submitted records | 67309 |
| Open issue items with `is_completed = 0` | 287 |
| Completed issue items with `is_completed = 1` | 67719 |

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
| Naming series is `PE-.#####` | `blank_bin_issue.json` |
| `scan_production_lot` is required | schema and `validate` |
| `scan_bin` is required | schema and `validate` |
| Validate rewrites child table from parent fields | `BlankBinIssue.validate` |
| Lot scan finds `Job Card` by `batch_code` and operation `Moulding` | `validate_blank_issue_barcode` |
| Job Card must be `Work In Progress` | `validate_blank_issue_barcode` |
| Bin scan validates location against `SPP Settings.to_location` | `validate_blank_issue_barcode` |
| Bin compound must match production item BOM compound | `validate_compound` |

## Refactor Handoff

Use this pack with the legacy `blank_bin_issue` DocType. `02-specifications/blank-bin-issue/` is currently empty, so this pack records a spec gap.
