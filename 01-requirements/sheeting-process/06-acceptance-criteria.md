# Acceptance Criteria

| ID | Scenario | Pass condition |
| --- | --- | --- |
| AC-SHT-001 | Operator scans accepted compound. | Source details populate and output entry is enabled. |
| AC-SHT-002 | Operator scans rejected or unknown compound. | Submission is blocked with clear reason. |
| AC-SHT-003 | Operator adds clip and cut-bit rows. | Rows retain correct barcode and `is_cut_bit_item` values. |
| AC-SHT-004 | Operator submits with output/source variance. | Warning appears; operator can still submit. |
| AC-SHT-005 | Submission creates Console local record. | Record has `reference_id`, payload snapshot, and child rows. |
| AC-SHT-006 | Submission creates local clip mappings before remote sync completes. | Immediate downstream scan can resolve the clip. |
| AC-SHT-007 | Legacy leg succeeds. | Legacy `Material Transfer` has `batches`, `sheeting_clip`, and sheeting transfer type. |
| AC-SHT-008 | One remote leg fails. | Status shows partial failure and retry keeps same output identities. |

## Sign-Off Bar

Production sign-off requires AC-SHT-001 through AC-SHT-008 to pass on a realistic compound batch with at least one clip row and one cut-bit row.
