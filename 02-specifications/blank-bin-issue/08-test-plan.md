# 08 — Test plan

## Legacy parity tests

| Test | Expected |
|---|---|
| Valid WIP moulding lot + valid bin | BBI submits with one child row. |
| Lot points to non-WIP Job Card | Scan rejected with status message. |
| Lot does not resolve to moulding Job Card | Scan rejected. |
| Bin has retired Item Bin Mapping | Scan rejected. |
| Bin has no `bin_weight` | Scan rejected. |
| Bin is not at `SPP Settings.to_location` | Scan rejected. |
| Bin item differs from Job Card production item | Scan rejected. |
| Bin compound not in active BOM compound list | Scan rejected. |

## Console gap tests

| Test | Current expected result |
|---|---|
| Search `develop` for `Console Blank Bin Issue` DocType | Not found. |
| Search `develop` for `create_local_blank_bin_issue` | Not found. |
| Search Bridge for `BLANK_BIN_ISSUE` mapping | Not found. |
| Search Ops for BBI submit handler | Not found. |
| Inspect live `iyyanarr/shree_polymer_console` branches | No live BBI branch visible on 2026-05-12; current `develop` has no BBI port. |
| Inspect stale local Console prototype evidence | Prototype UI/dummy helpers only; not complete process port. |

## Future port tests

| Layer | Required coverage |
|---|---|
| Dash | Lot scan uses batch_code; bin scan uses Asset barcode. |
| Console backend | Local parent/child create; idempotent reference_id retry. |
| Bridge | Legacy BBI parent and child fields match Desk-created record. |
| Ops | Reservation/log is created without stock ledger movement. |
| Callback | Local sync fields update through standard callback path. |
| MPE integration | MPE sees open BBI rows and marks them complete after consumption. |

## Production data regression

Run read-only checks before and after implementation:

```sql
SELECT COUNT(*) total, SUM(docstatus=1) submitted
FROM `tabBlank Bin Issue`;

SELECT is_completed, COUNT(*)
FROM `tabBlank Bin Issue Item`
GROUP BY is_completed;
```

Use existing live ratios as sanity checks, not exact pass/fail thresholds.
