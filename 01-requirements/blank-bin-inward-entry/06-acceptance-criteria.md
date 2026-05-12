# Acceptance Criteria

| ID | Scenario | Pass condition |
| --- | --- | --- |
| AC-BIE-001 | Operator scans active filled bin. | Bin contents and IBM id populate. |
| AC-BIE-002 | Operator scans retired/empty bin. | Scan is rejected. |
| AC-BIE-003 | Operator submits normal inward path. | Asset Movement exists and IBM qty is updated. |
| AC-BIE-004 | Operator submits cut-bit path without cut-bit batch. | Submission is blocked. |
| AC-BIE-005 | Operator submits cut-bit path with valid batch. | Repack Stock Entry exists. |
| AC-BIE-006 | Cut-bit path succeeds. | Source IBM is retired and stock ref is stored. |
| AC-BIE-007 | Failure during submit. | IBM state is rolled back. |
| AC-BIE-008 | Ops leg executes from Console path. | Ops does not duplicate Legacy sync. |

## Sign-Off Bar

BBIE sign-off requires both branches to pass, with special emphasis on cut-bit path because production records show it is the dominant path.
