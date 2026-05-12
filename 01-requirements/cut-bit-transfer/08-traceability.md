# Traceability

## Source Map

| Area | Source |
| --- | --- |
| Requirement source | Legacy `cut_bit_transfer.py`, Cut Bit spec, merged `sheeting-and-cutting` pack |
| Spec | `02-specifications/cut-bit-transfer/` |
| Legacy DocType | `shree_polymer_custom_app/.../doctype/cut_bit_transfer/` |
| Console process | `CUT_BIT_TRANSFER` |

## FR Mapping

| Requirement IDs | Evidence |
| --- | --- |
| FR-CBT-001 to FR-CBT-009 | Console Cut Bit spec backend and validation flow |
| FR-CBT-010 to FR-CBT-011 | Legacy `CutBitTransfer.on_submit` and `create_stock_entry` |
| FR-CBT-012 to FR-CBT-013 | Ops dedicated handler spec |
| FR-CBT-014 to FR-CBT-018 | Legacy warehouse and identity rules |
| FR-CBT-019 | Console/Legacy bin mapping side effects |

## NFR / BR Mapping

| Requirement IDs | Evidence |
| --- | --- |
| NFR-CBT-001 to NFR-CBT-012 | Cut Bit spec risk, backend, Bridge, Ops sections |
| BR-CBT-001 to BR-CBT-012 | Legacy `create_stock_entry`, Bridge mapping drift, Ops handler |

## Drift Findings

| ID | Drift | Impact | Required correction |
| --- | --- | --- | --- |
| DRIFT-CBT-001 | Live requirement tree had CBT inside `sheeting-and-cutting`. | Refactor worker could mix Sheeting and CBT obligations. | Separate `cut-bit-transfer` pack. |
| DRIFT-CBT-002 | Merged numbering used `SHC`. | Requirement IDs did not match process code. | Use `CBT`. |
| DRIFT-CBT-003 | Helper/test naming can imply clip retirement. | Worker might retire clips too early. | State BR-CBT-010 clearly. |
| DRIFT-CBT-004 | Field drift exists between `spp_batch_no` and `spp_batch_number`. | Legacy child trace can be blank or mis-mapped. | Add mapping test before refactor. |
| DRIFT-CBT-005 | Legacy idempotency is weaker than Console/Ops. | Retry may be harder to prove. | Keep as explicit risk and future schema improvement. |

## Change Log

| Date | Change | By |
| --- | --- | --- |
| 2026-05-12 | Split from merged `sheeting-and-cutting` into process-scoped Cut Bit Transfer pack. | Codex |
