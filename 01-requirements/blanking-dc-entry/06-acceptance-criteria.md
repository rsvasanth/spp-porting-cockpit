# Acceptance Criteria

| ID | Scenario | Pass condition |
| --- | --- | --- |
| AC-BDE-001 | Operator scans valid clip and valid available bin. | Clip and bin details populate. |
| AC-BDE-002 | Operator scans BOM-incompatible clip for selected item. | Scan is rejected with compound/item reason. |
| AC-BDE-003 | Operator scans occupied bin. | Scan is rejected. |
| AC-BDE-004 | Operator enters gross weight. | Net weight calculates as gross minus tare. |
| AC-BDE-005 | Operator submits valid BDE. | Console audit exists and target legs execute. |
| AC-BDE-006 | Legacy leg succeeds. | `Blanking DC Entry`, `Item Bin Mapping`, and `Asset Movement` exist. |
| AC-BDE-007 | Clip is partially consumed. | Remaining clip qty is reduced and mapping stays active. |
| AC-BDE-008 | Clip is fully consumed. | Clip mapping is retired. |

## Sign-Off Bar

BDE sign-off requires AC-BDE-001 through AC-BDE-008 on a real released clip and physical blanking bin.
