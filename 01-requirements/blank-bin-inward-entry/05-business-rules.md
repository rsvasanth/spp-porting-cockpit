# Business Rules

| ID | Rule | Rationale |
| --- | --- | --- |
| BR-BIE-001 | BBIE processes already-filled bins. | BDE owns filling. |
| BR-BIE-002 | Child rows are mandatory. | Legacy validation. |
| BR-BIE-003 | Gross weight is mandatory. | Legacy validation. |
| BR-BIE-004 | `move_to_cut_bit_warehouse` is a major branch, not an edge case. | Site records show 1859 repack vs 86 normal. |
| BR-BIE-005 | Normal path creates Asset Movement. | Bin location changes. |
| BR-BIE-006 | Repack path creates Stock Entry `Repack`. | Material identity changes to cut-bit stock. |
| BR-BIE-007 | Repack path retires source `Item Bin Mapping`. | Bin contents are removed. |
| BR-BIE-008 | Repack target uses `Cutbit_<item>` convention. | Final Batch Mixing recycling depends on it. |
| BR-BIE-009 | Rollback must restore IBM state. | Current legacy rollback protects production data. |
| BR-BIE-010 | Dedicated Ops handler is justified. | Branching crosses document types. |
| BR-BIE-011 | BBIE remains its own requirement identity. | Distinct from BDE and BBI. |

## Site Evidence

`spp15.local` shows the cut-bit branch dominates BBIE production usage. Treating it as optional/rare would be wrong.
