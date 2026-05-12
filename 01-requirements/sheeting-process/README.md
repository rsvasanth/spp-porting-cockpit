# Sheeting Process Requirements

## Status

| Field | Value |
| --- | --- |
| Requirement pack | Sheeting Process |
| Legacy DocType | `Material Transfer` with `material_transfer_type = "Transfer Compound to Sheeting Warehouse"` |
| Console process target | `SHEETING_PROCESS` |
| Requirement identity | Separate from Cut Bit Transfer and Bulk Clip Release |
| Last updated | 2026-05-12 |

## Story

Sheeting is the branch point after approved compound. One accepted compound batch is converted into multiple sheeted outputs: normal clips that move toward Blanking, and cut-bit rows that become recycling input later. The business requirement is not just "move stock"; it is to create durable clip identities before downstream operators can scan them.

## Files

| File | Purpose |
| --- | --- |
| `01-purpose.md` | Purpose, boundaries, and process position |
| `02-actors-and-roles.md` | Operators and accountability |
| `03-functional-requirements.md` | Functional requirements |
| `04-non-functional-requirements.md` | Quality, reliability, and integrity requirements |
| `05-business-rules.md` | Load-bearing business rules |
| `06-acceptance-criteria.md` | UAT criteria |
| `07-out-of-scope.md` | Exclusions |
| `08-traceability.md` | Requirement-to-spec traceability and drift |

## Counts

| Type | Count |
| --- | ---: |
| Functional requirements | 20 |
| Non-functional requirements | 13 |
| Business rules | 12 |
| Acceptance criteria | 8 |
| Out-of-scope items | 8 |
| Drift findings | 5 |

## Critical Legacy Facts

| Fact | Source |
| --- | --- |
| Legacy target is `Material Transfer`, not a dedicated Sheeting DocType | `material_transfer.py` |
| `Transfer Compound to Sheeting Warehouse` requires `sheeting_clip` child rows | `MaterialTransfer.validate` |
| Child item rows must have positive qty | `MaterialTransfer.validate` |
| Legacy submit validates release state of selected sheeting clips | `validate_sheeting_clips` |
| Submit creates a sheeting stock entry | `create_sheeting_stock_entry` |
| Console writes clip mappings inline before sync completes | `02-specifications/sheeting-process/03-console-backend.md` |

## Refactor Handoff

Use this pack with `02-specifications/sheeting-process/`. Do not use Cut Bit Transfer or Bulk Clip Release requirements to satisfy Sheeting. Cross-process dependencies are links only.
