# Acceptance Criteria

| ID | Scenario | Pass condition |
| --- | --- | --- |
| AC-CBT-001 | Operator scans active clip mapping. | Source resolves with item, batch, qty, and warehouse. |
| AC-CBT-002 | Operator scans active bin mapping. | Source resolves and qty can be partially transferred. |
| AC-CBT-003 | Operator scans unknown barcode. | System returns Failed with clear diagnostic. |
| AC-CBT-004 | Operator submits valid transfer. | Console audit exists and both target legs are started. |
| AC-CBT-005 | Ops leg succeeds. | Repack stock entry exists with cut-bit target identity. |
| AC-CBT-006 | Legacy leg succeeds. | Legacy `Cut Bit Transfer.stock_entry_reference` points to created Stock Entry. |
| AC-CBT-007 | Bin qty is partially consumed. | Mapping qty is reduced, not retired. |
| AC-CBT-008 | Bin qty is fully consumed. | Mapping is marked retired. |

## Sign-Off Bar

Production sign-off requires one clip-source transfer and one bin-source transfer to pass, including verification of warehouse routing and output `CB_` identity.
