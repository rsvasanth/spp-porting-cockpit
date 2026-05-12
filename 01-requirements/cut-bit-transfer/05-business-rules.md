# Business Rules

| ID | Rule | Rationale |
| --- | --- | --- |
| BR-CBT-001 | Cut Bit Transfer is repack/recycling, not new production. | It repairs material identity for reuse. |
| BR-CBT-002 | Source scan resolution starts from active clip/bin mappings. | Physical assets carry the source identity. |
| BR-CBT-003 | `Cutbit_<item_code>` is the target batch convention. | Downstream mixing depends on it. |
| BR-CBT-004 | `CB_<item_code>` is the target mix barcode convention. | Scan identity must be recognizable. |
| BR-CBT-005 | Compound items source from default sheeting warehouse. | Legacy rule. |
| BR-CBT-006 | Blanking item group sources from Unit 2 warehouse. | Legacy rule. |
| BR-CBT-007 | Other items source from default blanking warehouse. | Legacy fallback. |
| BR-CBT-008 | Target warehouse is default cut-bit warehouse. | One inventory pool for cut bits. |
| BR-CBT-009 | Console path must not let Ops perform duplicate Legacy sync. | Prevents duplicate records. |
| BR-CBT-010 | CBT does not retire clip mappings. | Release/blanking own clip retirement. |
| BR-CBT-011 | CBT reduces or retires bin mappings based on consumed quantity. | Bin material is consumed by repack. |
| BR-CBT-012 | `spp_batch_no` / `spp_batch_number` naming drift must be tested before refactor. | Field drift can silently drop trace fields. |

## Future Consideration

Add a real Legacy reference field for stronger idempotency, but do not block current requirement sign-off on that schema change.
