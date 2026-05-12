# 08 — Test plan

## Unit tests (legacy controller — `inspection_entry.py`)

### Shipped (verified behavior from live code)

| Test case | Covered by | Method |
|---|---|---|
| Future posting date throws | `validate()` line 16 | Inline |
| Missing lot_no throws | `validate()` line 18 | Inline |
| Missing inspector_code throws | `validate()` line 20 | Inline |
| Missing items throws | `validate()` line 22 | Inline |
| Duplicate Line IE for same lot blocked | `validate()` line 25-28 | Inline |
| Duplicate Patrol IE for same lot blocked | `validate()` line 25-28 | Inline |
| Duplicate Lot IE for same lot blocked | `validate()` line 25-28 | Inline |
| Final Visual duplicate NOT blocked (exempt) | `validate()` line 25 (excluded) | Inline |
| Incoming duplicate blocked | `validate()` line 25-28 | Inline |
| Line qty required (inspected_qty_nos) | `validate()` line 29-31 | Inline |
| Patrol qty required | `validate()` line 29-31 | Inline |
| Lot qty required | `validate()` line 29-31 | Inline |
| Incoming qty required (total_inspected_qty_nos) | `validate()` line 32-34 | Inline |
| Final qty required | `validate()` line 32-34 | Inline |
| `vs_pdir_qty_after_rejection` computed | `validate()` line 36-39 | Inline |
| `make_stock_entry` creates draft Material Transfer | Line 641-684 | Inline |
| `make_stock_entry` no-op when rejected kg = 0 | Line 678-680 | Inline |
| `make_inc_stock_entry` creates draft Material Transfer | Line 686-728 | Inline |
| `make_vs_pdir_stock_entry` creates + submits SE | Line 577-639 | Inline |
| `submit__vs_pdir` calls LRT.make_wo_stock_entry | Line 78-109 | Inline |
| `submit__vs_pdir_no_rejection` updates LRT qty | Line 111-154 | Inline |
| `rollback_entries` clears docstatus + stock_entry_reference | Line 337-353 | Inline |
| `rollback_vs_pdir` clears docstatus + vs_pdir_stock_entry_ref | Line 160-170 | Inline |
| `submit_deflash_receipt_entry` triggers DRE | Line 325-335 | Inline |
| `submit_moulding_entry` is deprecated (logs + returns) | Line 172-183 | Inline |

### Gaps (no automated coverage)

| Gap | Risk | Recommendation |
|---|---|---|
| `submit_inspection_stock_entry_immediately` cascade logic | High — complex batch cascade | Add unit test with mock MPE + mock IE list |
| `validate_lot_number` for each inspection type | Medium — complex branching | Add integration test per type |
| `create_work_order_vs_entry__only` + `update_job_cards_vs_entry__only` | High — Work Order creation chain | Add test with mocked `get_workstation_by_operation` |
| `check_available_stock` edge cases (batch_no null, zero qty) | Medium | Add parameterized test |
| LRT `rollback_____` method existence | Low — exists on LRT controller | Verify in LRT spec |

## Integration tests (Console → Bridge → Legacy)

### Shipped (phase 3 inspection path)

| Test case | Covered by | Method |
|---|---|---|
| Console `create_local_inspection` writes audit record | Phase 3 inspection routing | Manual + log inspection |
| `_safe_local_create` skips validate with `flags.from_local_cache` | `_safe_local_create` invariant | Manual |
| `apply_bridge_result` 5-step atomic dance | MB Mixing pattern, reused | Manual |
| Bridge idempotency — retry with same reference_id returns cached IE | `sync_process_transaction` | Manual |
| `Console Transaction Log` updated on callback | `execute_submission_step` | Manual |

### Gaps

| Gap | Risk | Recommendation |
|---|---|---|
| Full Line Inspection: Console → Bridge → Legacy IE submitted → SE created → MPE cascade | **Highest** — end-to-end polymorphic test | Add Playwright E2E test |
| Full Patrol Inspection: same path | High | Add Playwright E2E test |
| Full Lot Inspection: requires MPE exists (blocking validation) | **High** — Lot IE won't submit without MPE | Add test fixture with MPE submitted |
| Full Incoming Inspection: + Deflashing Receipt trigger | **High** — cross-Doctype chain | Add test fixture with DRE |
| Full Final Visual: + LRT + Work Order + SE + Job Card | **Highest** — most complex path | Add Playwright E2E test |
| MPE batch cascade to multiple IE rejection SEs | **Highest** — critical path | Add test with Line + Lot + Patrol IE all with draft SEs |

## E2E (Playwright — dash + backend + legacy)

### Smoke tests (production-scale)

| Test case | Expected result |
|---|---|
| Line Inspection: scan inspector → scan lot → add defect row → submit → IE submitted + SE created | IE docstatus=1, SE stock_entry_reference set |
| Patrol Inspection: same flow | IE docstatus=1, SE stock_entry_reference set |
| Lot Inspection: same flow (MPE must exist first) | IE docstatus=1, SE stock_entry_reference set |
| Incoming Inspection: lot with DRE → submit → SE created + DRE triggered | DRE Stock Entry submitted |
| Final Visual with rejection: lot with LRT → submit → SE submitted + WO created + LRT updated | SE submitted, LRT qty updated |
| Final Visual no rejection: submit → LRT qty updated + WO created | LRT qty_after_rejection_nos updated |
| Duplicate Line Inspection blocked | Frappe throw: "Inspection Entry for lot ... already exists" |
| Final Visual duplicate allowed (BR-IE-001) | Second Final Visual IE submitted |
| Future posting date blocked | Frappe throw: "Posting Date can't be greater than Today" |

### Volume test

| Test case | Expected result |
|---|---|
| Submit 100 Line Inspections in sequence | All succeed, no race condition |
| Submit 100 Patrol Inspections in parallel (5 concurrent) | All succeed, sync_status converges |
| MPE cascade with 50+ IE SEs to update | All SEs submitted, all batch_no set |

## User acceptance testing (UAT)

| Scenario | Steps | Pass criteria |
|---|---|---|
| Happy path Line | 1. Select Line Inspection 2. Scan inspector 3. Scan lot 4. Enter qty 5. Add defect row 6. Submit | Green checkmark, IE name shown, rejection SE visible in stock ledger |
| Duplicate Patrol blocked | 1. Submit Patrol IE for lot X 2. Try to submit another Patrol IE for lot X | Blocked with error message |
| Final Visual re-inspection allowed | 1. Submit Final Visual IE for lot Y 2. Submit another Final Visual IE for lot Y | Both submitted |
| MPE cascade | 1. Submit Line IE + Lot IE (draft SEs exist) 2. Submit MPE 3. Check IE batch_no updated + SEs submitted | IE.batch_no = MPE batch, SE.docstatus=1 |
| Incoming Deflashing trigger | 1. Submit Incoming IE for lot Z (has DRE) 2. Check DRE Stock Entry submitted | DRE Stock Entry docstatus=1 |

## What Hermes workers can safely add tests for

| Test | Risk of adding |
|---|---|
| Unit test for `submit_inspection_stock_entry_immediately` | Low — isolated function, mock MPE + Stock Entries |
| Unit test for `validate_lot_number` per type | Low — pure function, mock Job Card, LRT, DRE |
| Integration test for MPE → IE cascade | Medium — needs MPE fixture + IE fixtures + Stock Entry state |
| E2E for Final Visual with rejection | Medium — needs LRT fixture + Work Order cleanup |

## What requires architecture review before testing

| Test | Why |
|---|---|
| Adding a new inspection type | Would require new `on_submit` branch + new SE creation path |
| Changing the cascade trigger (Line+Lot vs Line+Lot+Patrol) | Would change the critical invariant documented in `10-risks-and-decisions.md` |
| Adding an Ops leg for inspection | Would require re-architecting the rejection SE creation pattern |