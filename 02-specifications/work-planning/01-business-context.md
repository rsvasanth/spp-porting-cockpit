# 01 — Business context

## Process role

Work Planning is the official production planning document for a shift. It defines the planned products, press/workstation, mould, and BOM choices for the shift. It is the first planning identity that downstream production execution depends on.

## Position in the production chain

```
Blank Bin Inward / available material
        │
        ▼
Work Planning  (official shift plan, one per shift)
        │
        ▼
Work Order + Job Card(s)
        │
        ├─ Blank Bin Issue
        ├─ Inspection Entry
        └─ Moulding Production Entry
```

## Legacy business rule

| Rule | Evidence |
| --- | --- |
| One official Work Planning per shift | `validate_shift_mould()` checks submitted `date + shift_series` |
| Multiple products in one plan | Child table `Work Plan Item` |
| Target quantity from shift master | `Work Plan Item Target` lookup by item + `shift_time` |
| Job Card Lot # is downstream identity | `update_job_cards()` sets `batch_code`, barcode, and child `lot_number` |
| Downstream use blocks cancellation | `on_cancel()` checks `Blank Bin Issue` and `Moulding Production Entry` |

## Difference from Add On Work Planning

| Area | Work Planning | Add On Work Planning |
| --- | --- | --- |
| Business meaning | Base shift plan | Supplemental plan |
| Shift uniqueness | Enforced | Not called in `validate()` |
| Naming | `WRKP-.#####` | `ADWRKP-.#####` |
| Child table | `Work Plan Item` | `Add On Work Plan Item` |
| Cancellation guard | BBI/MPE guard | BBI/MPE guard |

## What this process is not

- It is not Add On Work Planning.
- It is not a demand-forecasting optimizer.
- It is not Moulding Production Entry.
- It does not consume stock directly; it creates planning/execution records.
