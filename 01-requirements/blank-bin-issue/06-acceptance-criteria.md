# Acceptance Criteria

| ID | Scenario | Pass condition |
| --- | --- | --- |
| AC-BBI-001 | Operator scans WIP Moulding Lot. | Job Card details populate. |
| AC-BBI-002 | Operator scans non-WIP Lot. | Scan is rejected with Job Card status. |
| AC-BBI-003 | Operator scans valid bin at moulding location. | Bin details populate. |
| AC-BBI-004 | Operator scans bin at wrong location. | Scan is rejected. |
| AC-BBI-005 | Operator scans bin with wrong mat/production item. | Scan is rejected. |
| AC-BBI-006 | Operator scans bin with compound not in BOM. | Scan is rejected. |
| AC-BBI-007 | Operator submits valid BBI. | Legacy `Blank Bin Issue` and child row exist. |
| AC-BBI-008 | MPE consumes issued bin later. | Issue child `is_completed` changes to completed/consumed state. |

## Sign-Off Bar

BBI sign-off requires a WIP Job Card and a real filled bin, plus negative tests for wrong location and BOM mismatch.
