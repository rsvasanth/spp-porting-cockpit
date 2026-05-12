# Acceptance Criteria

## AC-WPL-001: Create Base Shift Plan

| Given | When | Then |
| --- | --- | --- |
| No submitted Work Planning exists for date + shift series | Supervisor submits Work Planning with multiple item rows | Plan is accepted and becomes official shift plan |

## AC-WPL-002: Duplicate Shift Block

| Given | When | Then |
| --- | --- | --- |
| A submitted Work Planning exists for date + shift series | Supervisor attempts another Work Planning for same key | Submission is blocked and existing plan is shown |

## AC-WPL-003: Multiple Product Rows

| Given | When | Then |
| --- | --- | --- |
| Supervisor selects multiple item/mould/press combinations | Rows are added | System stores one row per product/mould/press |

## AC-WPL-004: Missing Target Quantity

| Given | When | Then |
| --- | --- | --- |
| An item has no `Work Plan Item Target` for shift time | Supervisor submits plan | Submission fails naming missing item and shift type |

## AC-WPL-005: BOM Validation

| Given | When | Then |
| --- | --- | --- |
| Planned item has no active/default BOM | Supervisor submits plan or creates WO/JC | System blocks with BOM-not-found message |

## AC-WPL-006: Work Order And Job Card Creation

| Given | When | Then |
| --- | --- | --- |
| Submitted Work Planning has valid rows | Supervisor triggers Work Order / Job Card creation | Work Order and Job Cards are created and row Job Card / Lot # fields are updated |

## AC-WPL-007: Job Card Metadata

| Given | When | Then |
| --- | --- | --- |
| Job Card is created | Reviewer opens Job Card | It contains Lot #, barcode, shift type, supervisor, mould reference, and mould/press settings where available |

## AC-WPL-008: Cancel Before Downstream Use

| Given | When | Then |
| --- | --- | --- |
| Work Planning has no BBI or MPE downstream records | Authorized user cancels | Linked Job Cards, Work Orders, and Moulding Serial No rows are cleaned or cancelled consistently |

## AC-WPL-009: Cancel Blocked After BBI

| Given | When | Then |
| --- | --- | --- |
| A submitted Blank Bin Issue references the plan Lot # | User cancels Work Planning | Cancellation is blocked with Job Card / BBI reference |

## AC-WPL-010: Cancel Blocked After MPE

| Given | When | Then |
| --- | --- | --- |
| A submitted Moulding Production Entry references the plan Lot # | User cancels Work Planning | Cancellation is blocked with Job Card / MPE reference |
