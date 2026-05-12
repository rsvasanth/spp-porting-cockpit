# Cut Bit Transfer Requirements

## Status

| Field | Value |
| --- | --- |
| Requirement pack | Cut Bit Transfer |
| Legacy DocType | `Cut Bit Transfer` |
| Console process target | `CUT_BIT_TRANSFER` |
| Requirement identity | Separate from Sheeting and Bulk Clip Release |
| Last updated | 2026-05-12 |

## Story

Cut Bit Transfer consolidates reusable clip/bin material into cut-bit stock. It is a repack and identity-repair process, not fresh production. Its core obligation is to resolve a scanned physical asset, move quantity into the cut-bit warehouse, and preserve the `Cutbit_` / `CB_` conventions that allow Final Batch Mixing to reuse the material.

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
| Functional requirements | 19 |
| Non-functional requirements | 12 |
| Business rules | 12 |
| Acceptance criteria | 8 |
| Out-of-scope items | 8 |
| Drift findings | 5 |

## Critical Legacy Facts

| Fact | Source |
| --- | --- |
| Submit creates ERPNext Stock Entry with purpose `Repack` | `cut_bit_transfer.py::create_stock_entry` |
| Source can resolve from active `Item Clip Mapping` or `Item Bin Mapping` | `validate_clip_barcode` |
| Compound source uses sheeting warehouse | `create_stock_entry` |
| Blanking item group source uses Unit 2 warehouse | `create_stock_entry` |
| Other items use default blanking warehouse | `create_stock_entry` |
| Target warehouse is default cut-bit warehouse | `create_stock_entry` |
| Output mix barcode is `CB_<item_code>` | `create_stock_entry` |

## Refactor Handoff

Use this pack with `02-specifications/cut-bit-transfer/`. Do not satisfy this process by Sheeting output rules or Bulk Clip Release retirement rules.
