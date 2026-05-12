# Business Rules

| ID | Rule | Rationale |
| --- | --- | --- |
| BR-BDE-001 | BDE fills a bin; it does not issue or consume a bin. | Separate lifecycle stages. |
| BR-BDE-002 | Source clip must have active material mapping. | Physical source must exist. |
| BR-BDE-003 | Produced mat/item must be BOM-compatible with source compound. | Prevents wrong compound from entering moulding chain. |
| BR-BDE-004 | Bin must be available, not already occupied. | Prevents mixed contents. |
| BR-BDE-005 | Bin tare weight is required. | Net weight must be trustworthy. |
| BR-BDE-006 | Net weight is gross minus bin weight. | Legacy computes this directly. |
| BR-BDE-007 | Gross weight must be positive. | Legacy rejects zero/missing gross weight. |
| BR-BDE-008 | Future posting dates are not allowed. | Legacy validation. |
| BR-BDE-009 | Active submit path creates Asset Movement and Item Bin Mapping, not the older commented Work Order path. | Current production reality. |
| BR-BDE-010 | `from_blank_bin_inward` is a special branch and rare in production. | Site records show 25 total records. |
| BR-BDE-011 | Clip retirement belongs to consumption by BDE/Blanking, not Cut Bit Transfer. | Prevents early clip closure. |
| BR-BDE-012 | BDE must remain its own requirement identity. | Refactor comparison. |

## Site Evidence

`spp15.local` shows 13260 BDE records, so this is a mature production flow, not a planned-only process.
