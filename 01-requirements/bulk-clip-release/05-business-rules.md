# Business Rules

| ID | Rule | Rationale |
| --- | --- | --- |
| BR-BCR-001 | Bulk Clip Release is state transition, not manufacturing. | No material is transformed. |
| BR-BCR-002 | At least one clip is required. | Legacy validation enforces it. |
| BR-BCR-003 | Only active clip mappings can be released. | Already released clips should not change again. |
| BR-BCR-004 | Scan validation starts from barcode text. | Operators scan printed labels. |
| BR-BCR-005 | Retirement uses mapping identity when available. | Legacy `on_submit` updates by `item_clip_mapping_id`. |
| BR-BCR-006 | Release shall not create Stock Entry. | Stock quantity is not moving here. |
| BR-BCR-007 | Console mirror retirement timing must be intentional. | Too early or too late causes bad scan behavior. |
| BR-BCR-008 | Ops handler accepts a barcode list. | It is not a generic transaction payload. |
| BR-BCR-009 | Barcode/doc-name drift must be resolved before trusting direct helper paths. | Direct filters can miss rows. |
| BR-BCR-010 | Bulk Clip Release remains its own requirement identity. | It has distinct state-machine behavior. |

## Future Consideration

The preferred future direction is a rich audit-first path with correct mapping fields. Direct helper release can remain a fallback, but should not erase the need for release audit.
