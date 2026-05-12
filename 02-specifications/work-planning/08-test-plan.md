# 08 — Test plan

## Unit tests

| Test | Expected |
| --- | --- |
| Missing shift_series | Validation fails |
| Missing shift_time | Validation fails |
| No item rows | Validation fails |
| Missing Work Plan Item Target | Validation fails with item and shift |
| Duplicate submitted date + shift_series | Validation fails with existing plan |
| Missing BOM | Work Order creation fails |
| Duplicate workstation in one draft | UI/API rejects |
| Duplicate mould in one draft | UI/API rejects |

## Integration tests

| Test | Expected |
| --- | --- |
| Valid multi-row Work Planning | Submitted plan accepted |
| Create Work Order / Job Card | WO and Job Cards created for rows |
| Child row backfill | `Work Plan Item.job_card` and `lot_number` populated |
| Job Card metadata | Lot #, barcode, shift, supervisor, mould metadata present |
| Cancel before downstream use | WO/JC/serial cleanup succeeds |
| Cancel after BBI | Cancellation blocked |
| Cancel after MPE | Cancellation blocked |

## Porting tests

| Test | Expected |
| --- | --- |
| Console process code routes to Work Planning | Does not route to Add On |
| Bridge mapping child table | Uses `Work Plan Item` |
| Retry after target failure | Does not duplicate WO/JC |
| Ops custom fields | Lot # and planning identity preserved |

## Regression tests against Add On confusion

| Test | Expected |
| --- | --- |
| Work Planning duplicate shift | Blocked |
| Add On duplicate shift | Allowed unless separately configured |
| Work Planning child doctype | `Work Plan Item` |
| Add On child doctype | `Add On Work Plan Item` |
