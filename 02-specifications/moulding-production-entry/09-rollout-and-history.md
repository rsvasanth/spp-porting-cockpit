# 09 — Rollout and history

## Rollout sequence (Wave 2)

MPE is Wave 2, after MB Mixing (Wave 1) and before Final Batch Mixing. The
ordering reflects dependency:

```
Wave 1 (shipped):
  └── Master Batch Mixing — head of chain

Wave 2 (this spec):
  ├── Blank Bin Issue — MPE consumes BBI rows
  ├── Inspection Entry — MPE validates Line + Patrol prerequisites
  └── Moulding Production Entry — terminal booking (depends on BBI + IE)

Wave 3 (future):
  └── Final Batch Mixing — consumes MPE output (finished goods batch)
```

**Dependency note:** BBI and IE must ship before MPE integration tests can
run. BBI provides the consumed bin rows; IE provides the inspection prerequisite
validation. Both are preconditions, not components, of MPE.

## Pre-conditions for MPE rollout

Before MPE can ship, the following must be verified:

1. **BBI shipped and stable** — `blank_bin_issue_item_name` and `item_bin_mapping_name`
   references in `update_bins()` require BBI doctype to exist and be populated
2. **IE (Line + Patrol) shipped and stable** — `validate_lot_number()` queries
   `Inspection Entry` by `lot_no` with `inspection_type IN ('Line Inspection', 'Patrol Inspection')`
3. **SPP Settings populated** — `production_tolerance`, `maximum__allowed_qty`,
   `mat_percentage`, `from_location`, `to_location`, `unit_2_warehouse`,
   `purge_scrap_warehouse` all referenced by MPE validate + submit functions
4. **Mould Specification populated** — `avg_blank_wtproduct_gms` and `shell_weight`
   used for rejection weight calculation and shell qty; need active records for
   all active moulds
5. **Workstation naming convention stable** — `is_injection_moulding` detection
   uses `INJECTION` / `INJUCTION` substring; if workstation names change, detection breaks

## What changed in the legacy MPE controller (recent iterations)

Based on code review of the controller, these changes were made in recent iterations:

### Added `validate_actual_warehouse_stock()` (later iteration)

This was added after the initial rollout to catch the case where bin weights
are correct but actual warehouse stock is insufficient. The original
`validate_comsumption_details()` only checked the scanned bin weights, not
actual stock. This is a **backward-compatible addition** — it adds a new guard
in the submit chain without changing existing behavior.

### Changed to immediate SE submit (new flow vs manual_on_submit)

The original pattern had:
1. `on_submit` → creates SE draft
2. `manual_on_submit` → submits SE (separate button or API call)

The new pattern (current):
1. `on_submit` → creates SE draft → immediately submits → cascade

The `manual_on_submit` is kept for backward compatibility but logs a deprecation
warning. **Console must implement the immediate-submit pattern only.**

### Added `is_injection_moulding` detection from workstation name

This was added to handle the injection moulding variant where `purged_compound`
and `compound_leakage` are mandatory and output weight calculation differs. The
check handles both `INJECTION` and `INJUCTION` (historical typo in the database).

### Added `validate_get_line_ins_qty()` for rejection weight

This replaced a commented-out `validate_inspection_qty()` that used weighed
rejection. The current implementation uses theoretical weight
(piece count × avg_blank_wtproduct_gms). The change was made because physical
weighing of rejected pieces was unreliable.

## What Hermes can/cannot touch without architecture review

| What | Can Hermes touch? | Notes |
|---|---|---|
| `validate_lot_number()` precondition checks | **Yes** — additive changes only | Adding new checks is safe; removing or modifying existing checks risks breaking upstream dependencies |
| Tolerance value and behavior | **Yes** — via SPP Settings | Tolerance is configurable, not hardcoded; changes to `production_tolerance` take effect immediately |
| `is_injection_moulding` detection logic | **No** — architecture review | Substring check is fragile but production-validated; any change risks breaking injection detection for 613 existing records |
| `make_stock_entry()` immediate submit | **No** — architecture review | Pattern change would break rollback logic and Console callback coordination |
| Inspection cascade (`submit_inspection_stock_entries_from_moulding`) | **No** — architecture review | Batch update to IE must match; changing this breaks traceability |
| Bin closure (`update_bins`) | **No** — architecture review | BBI + IBM state machine; changes affect upstream BBI and downstream inventory accuracy |
| `rollback_entries()` behavior | **No** — architecture review | Failure recovery is complex; changes risk leaving inconsistent state |
| Whitelisted API signatures | **Yes** — careful addition | Adding new parameters is safe; removing or renaming risks breaking Dash calls |

## Staging verification checklist before production rollout

- [ ] BBI doctype exists and has > 0 submitted records
- [ ] IE (Line + Patrol) has submitted records for a known lot
- [ ] SPP Settings has all required fields populated
- [ ] At least one active Mould Specification exists for a known mould + compound combination
- [ ] Workstation with "INJECTION" in name exists (for injection variant testing)
- [ ] Workstation without "INJECTION" exists (for compression variant testing)
- [ ] BOM with Shell item group exists (for shell variant testing)
- [ ] `production_tolerance` set to a non-zero value for tolerance testing
- [ ] `maximum__allowed_qty` set for over-consumption guard testing
- [ ] At least one open moulding Job Card exists for testing
- [ ] `validate_lot_number` returns correct response for valid lot
- [ ] `validate_lot_number` returns correct error for missing inspection
- [ ] Submit MPE end-to-end on staging with both Legacy + Ops legs
- [ ] Verify SE docstatus = 1, batch_no set, JC + WO completed
- [ ] Verify IE batch_no updated after MPE submit
- [ ] Verify BBI items is_completed = 1 after MPE submit
- [ ] Cancel MPE and verify SE cancelled, JC/WO reset, BBI state unchanged
- [ ] Retry scenario: kill one leg, retry, verify both succeed
- [ ] Partial sync: one leg fails, operator can retry from Dash

## Post-production monitoring (first 30 days)

| Metric | Target | Alert threshold |
|---|---|---|
| MPE submission rate | > 50/day on peak shift | < 10/day for 3 consecutive days |
| `validate_lot_number` failure rate | < 5% (expected: missing IE on new lots) | > 15% |
| Tolerance warning rate | < 10% of submissions trigger warning | > 25% |
| Rollback rate | < 0.5% of submissions trigger rollback | > 2% |
| Sync failure rate (Legacy leg) | < 1% | > 5% |
| Sync failure rate (Ops leg) | < 1% | > 5% |
| Cancel rate | < 1% of submitted MPEs cancelled | > 3% |
| `stock_entry_reference` not set after submit | 0 (should never happen) | Any occurrence |