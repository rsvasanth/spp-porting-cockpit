# Acceptance Criteria

| ID | Scenario | Pass condition |
| --- | --- | --- |
| AC-BCR-001 | Operator scans active clip barcode. | Row is added with mapping id and material details. |
| AC-BCR-002 | Operator scans same barcode twice in one draft. | Second scan is rejected. |
| AC-BCR-003 | Operator scans already released clip. | System reports no active mapping. |
| AC-BCR-004 | Operator submits release batch. | Console records release intent and target legs execute. |
| AC-BCR-005 | Legacy leg succeeds. | Legacy `Item Clip Mapping.is_retired = 1` for selected mappings. |
| AC-BCR-006 | Ops leg succeeds. | Ops handler reports impacted clips. |
| AC-BCR-007 | Barcode text differs from clip document name. | Release still retires the correct mapping. |

## Sign-Off Bar

Production sign-off requires AC-BCR-001 through AC-BCR-007, especially the barcode/doc-name case.
