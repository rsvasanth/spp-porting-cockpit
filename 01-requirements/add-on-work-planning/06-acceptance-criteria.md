# Acceptance Criteria

## AC-AWP-001: Create Add-On Plan

| Given | When | Then |
| --- | --- | --- |
| A shift needs extra production | Supervisor submits Add On Work Planning | Supplemental plan is accepted |

## AC-AWP-002: Multiple Add-Ons Same Shift

| Given | When | Then |
| --- | --- | --- |
| One Add On exists for date + shift series | Supervisor submits another valid Add On | System allows it unless explicit config blocks it |

## AC-AWP-003: Missing Target Quantity

| Given | When | Then |
| --- | --- | --- |
| Item lacks target for shift time | Supervisor submits Add On | Submission fails naming missing item/shift |

## AC-AWP-004: Work Order And Job Card Creation

| Given | When | Then |
| --- | --- | --- |
| Submitted Add On has valid rows | Supervisor triggers WO/JC creation | Work Order and Job Cards are created and child rows get Job Card / Lot # |

## AC-AWP-005: No Work Planning Shift Block

| Given | When | Then |
| --- | --- | --- |
| Submitted Work Planning already exists for same shift | Supervisor submits Add On | Add On is allowed as supplemental work |

## AC-AWP-006: Cancellation Before Downstream Use

| Given | When | Then |
| --- | --- | --- |
| Add On has no downstream BBI/MPE | Authorized user cancels | Linked WO/JC/serial rows are cleaned consistently |

## AC-AWP-007: Cancellation Blocked After BBI

| Given | When | Then |
| --- | --- | --- |
| Submitted BBI references Add On Lot # | User cancels Add On | Cancellation is blocked |

## AC-AWP-008: Cancellation Blocked After MPE

| Given | When | Then |
| --- | --- | --- |
| Submitted MPE references Add On Lot # | User cancels Add On | Cancellation is blocked |
