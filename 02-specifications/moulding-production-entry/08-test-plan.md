# 08 — Test plan

## Unit tests (gaps — not yet shipped)

### Legacy controller — `moulding_production_entry.py`

| Test | Status | Notes |
|---|---|---|
| `validate()` — injection detection | **NOT TESTED** | `is_injection_moulding` derived from workstation name on every validate. No test for `INJECTION` / `INJUCTION` substring detection. |
| `validate()` — date block (future date) | **NOT TESTED** | No test that verifies `moulding_date > today` throws |
| `validate()` — required fields (weight, job_card, compound, batch_details, curing_time, lifts, cavities) | **NOT TESTED** | Each field throws on empty. No test for all fields together. |
| `validate()` — balance bin gate | **NOT TESTED** | No test for `no_balance_bin == 0` requiring at least one balance_bin row |
| `validate()` — tolerance warning (soft block) | **NOT TESTED** | `validate_tolerance()` returns message not throw; no test verifies the warning fires without blocking |
| `validate_get_line_ins_qty()` — rejection weight calculation | **NOT TESTED** | No test for piece_count × avg_blank_wtproduct_gms formula |
| `validate_shell()` — shell detection, sourcing, UOM conversion | **NOT TESTED** | No test for shell item group detection, batch selection, qty calculation |
| `validate_shell()` — missing Unit-2 warehouse | **NOT TESTED** | Throws if `spp_settings.unit_2_warehouse` not set |
| `on_submit()` — five-gate chain | **NOT TESTED** | No test for the validate_cavity → validate_mat_qty → validate_comsumption_details → validate_actual_warehouse_stock → make_stock_entry chain |
| `validate_cavity()` — running cavities > cavity count | **NOT TESTED** | No test for the throw when running cavities exceed MSPEC cavity count |
| `validate_cavity()` — missing no_of_cavity_in_mspec | **NOT TESTED** | No test for the throw when MSPEC cavity count not fetched |
| `validate_mat_qty()` — total_available vs total_required | **NOT TESTED** | No test for the over-consumption guard against `maximum__allowed_qty` |
| `validate_mat_qty()` — maximum__allowed_qty = 0 (strict) | **NOT TESTED** | No test for the strict mode when SPP Setting is 0 |
| `validate_comsumption_details()` — proportional share | **NOT TESTED** | Complex proportional share logic; no test covers balance bins vs fresh bins |
| `validate_comsumption_details()` — shortage block | **NOT TESTED** | `weight > compound_available_qty` should throw |
| `validate_actual_warehouse_stock()` — insufficient stock | **NOT TESTED** | Added later; no test for the HTML shortage table response |
| `make_stock_entry()` — batch generation | **NOT TESTED** | No test for `generate_batch_no(batch_id="T"+scan_lot_number, ...)` call |
| `make_stock_entry()` — immediate submit pattern | **NOT TESTED** | No test that verifies SE is submitted immediately inside `make_stock_entry()` |
| `make_stock_entry()` — FG row fields | **NOT TESTED** | `spp_batch_number`, `batch_no`, `barcode_attach`, `source_ref_document/id` not tested |
| `make_stock_entry()` — consumption rows (with purge deduction) | **NOT TESTED** | `append_source_details` with `purged_compound` + `compound_leakage` deduction not tested |
| `make_stock_entry()` — scrap row (injection moulding) | **NOT TESTED** | `is_scrap_item=1` for purge/leakage; `purge_scrap_warehouse` not tested |
| `make_stock_entry()` — shell item row | **NOT TESTED** | Shell transfer from Unit-2 warehouse not tested |
| `submit_inspection_stock_entries_from_moulding()` — batch update | **NOT TESTED** | No test for `batch_no` update on Line + Patrol IE and their SE rows |
| `submit_inspection_stock_entries_from_moulding()` — SE submit | **NOT TESTED** | No test for draft SE submission for inspection with rejections |
| `update_bins()` — balance bin path | **NOT TESTED** | `is_completed=1` on BBI item; qty + job_card update on IBM |
| `update_bins()` — full bin path | **NOT TESTED** | `is_retired=1` on IBM; `is_completed=1` on BBI item; asset movement |
| `update_bins()` — asset movement (not at from_location) | **NOT TESTED** | `make_asset_movement` triggered when last movement not at `from_location` |
| `on_cancel()` — SE cancel + JC/WO reset | **NOT TESTED** | No test for `docstatus=2` on SE, `Not Started` on WO, `Work In Progress` on JC |
| `rollback_entries()` — full rollback | **NOT TESTED** | Complex rollback; no test covers SE delete + JC/WO reset + MPE draft + batch delete |
| `sort_bins_for_print()` — numeric sort | **NOT TESTED** | Non-load-bearing for production; low priority |

### Whitelisted APIs

| Test | Status | Notes |
|---|---|---|
| `validate_lot_number()` — valid lot, open JC, inspections present, BBI open | **NOT TESTED** | Full happy path not tested |
| `validate_lot_number()` — invalid lot barcode | **NOT TESTED** | No test for "invalid lot" response |
| `validate_lot_number()` — completed Job Card | **NOT TESTED** | No test for completed JC rejection |
| `validate_lot_number()` — missing Line Inspection | **NOT TESTED** | No test for the missing inspection message |
| `validate_lot_number()` — missing Patrol Inspection | **NOT TESTED** | No test for the missing inspection message |
| `validate_lot_number()` — no open BBI rows | **NOT TESTED** | No test for "no entry for BBI" response |
| `validate_lot_number()` — mould reference missing | **NOT TESTED** | No test for mould reference validation |
| `validate_lot_number()` — cavity count missing | **NOT TESTED** | No test for cavity count validation |
| `validate_lot_number()` — retired bin | **NOT TESTED** | No test for released/retired bin response |
| `validate_lot_number()` — batch not found | **NOT TESTED** | No test for batch resolution failure paths |
| `validate_lot_number()` — compound not in BOM | **NOT TESTED** | No test for BOM compatibility check |
| `validate_bin()` — valid bin, active IBM | **NOT TESTED** | No test |
| `validate_bin()` — already released bin | **NOT TESTED** | No test |
| `validate_bin_weight()` — gross < tare | **NOT TESTED** | No test |
| `validate_bin_weight()` — net > remaining | **NOT TESTED** | No test |
| `validate_operator()` — valid operator | **NOT TESTED** | No test |
| `validate_operator()` — supervisor with designation mapping | **NOT TESTED** | No test |
| `validate_operator()` — invalid barcode | **NOT TESTED** | No test |

### Tolerance validation (FR-MPE-009)

| Test | Status | Notes |
|---|---|---|
| `production_tolerance = 0` → no check | **NOT TESTED** | No test that verifies tolerance check is skipped when setting is 0 |
| `production_tolerance = 5` (custom value) | **NOT TESTED** | No test that verifies the 5% boundary is used |
| Weight within tolerance → msgprint, not throw | **NOT TESTED** | Soft warning behavior not verified |
| Weight outside tolerance → warning | **NOT TESTED** | No test for the boundary condition |

### Injection moulding (FR-MPE-011)

| Test | Status | Notes |
|---|---|---|
| Workstation name with "INJECTION" → `is_injection_moulding = 1` | **NOT TESTED** | No test |
| Workstation name with "INJUCTION" (typo) → `is_injection_moulding = 1` | **NOT TESTED** | No test |
| Workstation name without injection substring → `is_injection_moulding = 0` | **NOT TESTED** | No test |
| No Job Card → `is_injection_moulding = 0` | **NOT TESTED** | No test |
| `purged_compound` + `compound_leakage` included in output weight | **NOT TESTED** | No test |
| `purge_scrap_warehouse` used for scrap row | **NOT TESTED** | No test |

## Integration tests (parked — requires BBI + IE)

MPE integration tests require:
- [Blank Bin Issue](../blank-bin-issue/) shipped and stable
- [Inspection Entry](../inspection-entry/) shipped and stable (Line + Patrol submissions)

These are parked until both dependencies ship.

## E2E tests (parked)

| Test scenario | Precondition | Priority |
|---|---|---|
| Happy path: scan lot → fill form → submit → SE created + JC completed + bins closed | BBI + IE shipped | P1 |
| Injection moulding path with purge/leakage | BBI + IE shipped + workstation with "INJECTION" in name | P1 |
| Shell consumption path | BOM includes Shell item group | P2 |
| Tolerance warning (soft block) path | `SPP Settings.production_tolerance > 0` | P2 |
| Cancel path: MPE cancel → SE cancelled → JC/WO reset | MPE submitted first | P2 |
| Rollback path: SE creation fails → `rollback_entries()` fires | Force SE creation failure | P3 |
| Retry path: one leg fails → retry → both succeed | One target down | P2 |

## Smoke tests (post-rollout)

After MPE ships to production:

| Test | Frequency | Expected result |
|---|---|---|
| Submit MPE with no balance bin | Per shift | SE created, batch generated, JC completed |
| Submit MPE with balance bins | Per shift | BBI items marked completed, IBM qty updated |
| Submit injection moulding MPE | Per shift (injection operators) | Scrap row created, `purge_scrap_warehouse` credited |
| Submit MPE with shell consumption | Per shift (shell-enabled BOMs) | Shell transferred from Unit-2 warehouse |
| Operator scans invalid lot | Per error scenario | `validate_lot_number` returns error without creating MPE |
| Submit MPE without Line Inspection | Per error scenario | `validate_lot_number` returns error |
| Submit MPE without Patrol Inspection | Per error scenario | `validate_lot_number` returns error |
| Cancel submitted MPE | Ad-hoc correction | SE cancelled, JC/WO reset, BBI/IBM state unchanged |
| Retry failed Legacy leg | After Legacy downtime | SE created on Legacy, both legs Synced |
| Retry failed Ops leg | After Ops downtime | SE created on Ops, both legs Synced |

## User acceptance criteria

| # | Criterion | Test method |
|---|---|---|
| UAT-1 | Operator can scan lot barcode and see Job Card + mould reference + compound pre-filled | Manual — scan known lot on staging |
| UAT-2 | MPE blocks when Line Inspection not submitted | Create MPE without Line IE; expect error |
| UAT-3 | MPE blocks when Patrol Inspection not submitted | Create MPE without Patrol IE; expect error |
| UAT-4 | MPE blocks when no open BBI rows for lot | Create MPE without BBI; expect error |
| UAT-5 | MPE blocks when bins are retired/released | Retire a bin; try to create MPE; expect error |
| UAT-6 | Tolerance warning fires but doesn't block (soft warning) | Set `production_tolerance = 5`; submit with weight slightly outside range; verify msgprint but submission proceeds |
| UAT-7 | Injection moulding detection works from workstation name | Assign a press with "INJECTION" in workstation name; create MPE; verify `is_injection_moulding = 1` and purge/leakage fields active |
| UAT-8 | Manufacturing SE created and submitted on MPE submit | Submit MPE; verify SE exists with `docstatus = 1` and correct FG + consumption rows |
| UAT-9 | Batch number generated and linked to SE | Submit MPE; verify `batch_no` on SE FG row; verify `stock_entry_reference` on MPE |
| UAT-10 | Job Card completed after MPE submit | Submit MPE; verify JC `status = Completed`, `docstatus = 1` |
| UAT-11 | Work Order completed after MPE submit | Submit MPE; verify WO `status = Completed` |
| UAT-12 | Line + Patrol IE `batch_no` updated after MPE submit | Submit MPE; query IE for lot; verify `batch_no` and `spp_batch_number` populated |
| UAT-13 | Inspection SEs submitted (if any draft rejections) | Submit MPE with rejection records; verify linked SEs `docstatus = 1` |
| UAT-14 | BBI items marked `is_completed = 1` after MPE submit | Submit MPE; query BBI items for lot; verify `is_completed = 1` |
| UAT-15 | Full bins: IBM `is_retired = 1`; partial bins: IBM qty updated | Submit MPE; inspect IBM rows for consumed bins |
| UAT-16 | MPE cancel rolls back SE + JC + WO but not BBI/IBM state | Cancel submitted MPE; verify SE cancelled, JC/WO reset; verify BBI items still completed |
| UAT-17 | Rollback fires when SE creation fails | Force failure; verify MPE rolled back to draft, SE deleted, JC/WO reset, batch deleted |
| UAT-18 | Both Legacy + Ops legs succeed in parallel | Submit MPE; verify both `Console Transaction Log` rows `status = Success` |
| UAT-19 | Partial sync: one leg fails, operator can retry | Kill one target mid-submit; retry; verify both legs succeed |
| UAT-20 | Sync status reaches `Success` and Console MPE auto-submits | Submit MPE; wait; verify Console MPE `docstatus = 1`, `sync_status = Success` |