# 07 — End-to-end flow (one operator submission, traced)

This file is the **single canonical narrative** tying layers 02–06 together.
For the detailed sequence diagram and per-step trace, the pattern follows
[`../master-batch-mixing/07-end-to-end-flow.md`](../master-batch-mixing/07-end-to-end-flow.md)
exactly. This file covers MPE-specific deviations from the standard MB Mixing
pattern.

## How MPE differs from the standard MB Mixing pattern

| Aspect | MB Mixing | MPE |
|---|---|---|
| Trigger | Operator scans raw material barcodes | Operator scans finished-goods lot barcode |
| Pre-validation | BOM item validation | `validate_lot_number()` — Job Card + inspections + BBI |
| Cascade depth | 1 system (SE → consumed material) | 5 systems in one submit (SE + JC + WO + IE + Bins) |
| Inspection dependency | None | Line + Patrol must be submitted |
| Bin state dependency | None | Active IBM rows required |
| Failure rollback | None | `rollback_entries()` tears back SE + JC + WO + Batch |
| Auto-submit pattern | Both legs → auto-submit Console doc | Same — but both legs include MPE's own SE creation |

## Narrative trace — one MPE submission, step by step

**Setup:** Operator Raju at a compression moulding press. The lot `T-LOT-6122`
has passed Line + Patrol inspections. The BBI has been issued. Raju opens the
Console Dash and selects Moulding Production Entry.

**T+0:00** — Raju scans lot barcode `T-LOT-6122`. Dash calls
`validate_lot_number("T-LOT-6122")`:

1. Resolves `batch_code = "T-LOT-6122"` → finds open moulding Job Card `JC-2026-01432` (status = `Work In Progress`)
2. Checks submitted Line Inspection for this lot → found `IE-LIN-2026-00821`
3. Checks submitted Patrol Inspection for this lot → found `IE-PAT-2026-00845`
4. Checks open BBI rows → finds `BBI-2026-00312` with 4 open items
5. For each bin: checks active IBM, resolves batch_no, validates compound in BOM
6. Returns `{"status": "Success", "message": [bin_objects...]}` — the batch detail list

**T+0:15** — Dash receives the bin list. Raju sees:
- Mould reference: `Mould-A12`
- Compound: `C-6122-FB`
- Running cavities: 8
- Balance bins section

**T+0:30** — Raju enters produced weight `48.5` kg. Dash validates in real-time:
- Tolerance check: `48.5` within `production_tolerance` of total bin qty
- Balance bin (if any): `no_balance_bin = 0` → Raju scans balance bin
- Weight without shell: calculated after shell validation (if applicable)

**T+0:45** — Raju clicks "Submit to ERP". `handleSubmit` runs:

1. `generatePayload()` builds the MPE payload with `reference_id = 1747234567890`
2. `initializeSubmission({ payload })` → Console `api.initialize_submission`
3. `create_local_moulding_production_entry` inserts `Console Moulding Production Entry CMPE-2026-00004`, Pending
4. Two `Console Transaction Log` rows created (Legacy + Ops, both Pending)
5. Returns `{target_logs, reference_id}` to Dash

**T+0:46** — Dash shows both rows as `Pending`. `Promise.all` fires both
`executeSubmissionStep` calls in parallel.

**Legacy leg (T+0:46 → T+0:52, runs in parallel with Ops):**

1. POST to `https://sppmaster.frappe.cloud/api/method/shree_polymer_legacy_bridge.sync_api.sync_process_transaction`
2. Bridge's `sync_process_transaction`:
   - Idempotency: no existing MPE with `reference_id = 1747234567890`
   - Loads `Legacy Sync Mapping "MOULDING_PRODUCTION_ENTRY"`
   - Applies field_mappings → builds legacy MPE with all field values
   - `legacy_doc.insert()` — MPE created Draft
   - `legacy_doc.submit()` → `make_stock_entry()` fires:
     - Creates Manufacturing Stock Entry `MAT-STE-2026-02841`
     - Generates batch via `generate_batch_no(batch_id="T"+"T-LOT-6122", ...)`
     - **Submits Stock Entry immediately** (`docstatus = 1`)
     - `submit_inspection_stock_entries_from_moulding()` — updates IE batch_no, submits draft IE SEs
     - `update_bins()` — closes BBI items, retires or updates IBM
     - Job Card `JC-2026-01432` → `status = Completed`, `docstatus = 1`
     - Work Order `MFG-WO-2026-01312` → `status = Completed`
   - Bridge response: `{status: "Success", reference_name: "MLDPE-2026-00142", stock_entry_reference: "MAT-STE-2026-02841"}`
3. Console `execute_submission_step` receives response:
   - Updates `Console Transaction Log` Legacy row to Success
   - `update_local_domain_record` → `doc.apply_bridge_result("Legacy", "Success", "MLDPE-2026-00142")`
   - Leg sync status = Synced; re-reads both legs (Ops still Pending) → aggregate Partial

**Ops leg (T+0:46 → T+0:50, finishes before Legacy):**

1. POST to `https://newspp.m.frappe.cloud/api/method/shree_polymer_ops.api.process_transaction`
2. Ops `process_transaction` → `TransactionEngine`:
   - Creates `Shree Polymer MES Log`, Pending
   - Creates Work Order + Job Card (idempotent by reference_id)
   - Creates Stock Entry (Manufacture) with FG batch from `scan_lot_number`
   - Returns `{status: "success", log_name: "MES-LOG-2026-01400", impacted_balances: [...]}`
3. Console `execute_submission_step`:
   - Updates `Console Transaction Log` Ops row to Success
   - `update_local_domain_record` → `doc.apply_bridge_result("Ops", "Success", "MES-LOG-2026-01400")`
   - Leg sync status = Synced; re-reads both legs (Legacy now Synced too) → aggregate **Success** → auto-submit Console MPE

**T+0:52** — Both callbacks processed. `apply_bridge_result` step 4 self-heals
(no correction needed). Step 5 auto-submits the Console MPE document.

**Final state (T+0:53):**

| System | Document | State |
|---|---|---|
| Console | `Console Moulding Production Entry CMPE-2026-00004` | `docstatus=1`, `sync_status=Success`, `legacy_reference="MLDPE-2026-00142"`, `ops_reference="MES-LOG-2026-01400"` |
| Console | `Console Transaction Log` (Legacy row) | `status=Success` |
| Console | `Console Transaction Log` (Ops row) | `status=Success` |
| Legacy | `Moulding Production Entry MLDPE-2026-00142` | `docstatus=1`, `stock_entry_reference="MAT-STE-2026-02841"` |
| Legacy | `Stock Entry MAT-STE-2026-02841` | `docstatus=1`, Manufacture, FG batch = `T-LOT-6122`, consumed compound lines |
| Legacy | `Job Card JC-2026-01432` | `docstatus=1`, `status=Completed` |
| Legacy | `Work Order MFG-WO-2026-01312` | `status=Completed` |
| Legacy | `Inspection Entry IE-LIN-2026-00821` | `batch_no` updated to produced batch, `spp_batch_number` set |
| Legacy | `Inspection Entry IE-PAT-2026-00845` | `batch_no` updated, SE submitted if any draft |
| Legacy | `Blank Bin Issue Item` rows from `BBI-2026-00312` | `is_completed = 1` |
| Legacy | `Item Bin Mapping` rows | Retired or qty updated |
| Ops | `Shree Polymer MES Log MES-LOG-2026-01400` | `status=Success` |
| Ops | `Stock Entry MAT-STE-2026-...` | `docstatus=1`, Manufacture |

## What can go wrong, and at what point

| Failure mode | Where it surfaces | What state is left |
|---|---|---|
| Lot barcode invalid | `validate_lot_number()` → Dash shows error | No MPE created |
| Line or Patrol inspection missing | `validate_lot_number()` → Dash shows error | No MPE created |
| Open BBI rows missing | `validate_lot_number()` → Dash shows error | No MPE created |
| Tolerance exceeded | `validate()` → msgprint warning (not throw) | Operator can still submit |
| `make_stock_entry` fails | `on_submit` → `rollback_entries()` called | MPE rolled back to draft, SE deleted, JC/WO reset, batch deleted |
| Stock Entry submit fails | `make_stock_entry` → `rollback_entries()` | Same as above |
| Inspection cascade fails | `submit_inspection_stock_entries_from_moulding()` → logged, not thrown | MPE + SE succeed; IE batch update may be incomplete |
| Bin closure fails | `update_bins()` → logged, not thrown | MPE + SE succeed; BBI/IBM state may be stale |
| Legacy Bridge times out | Console Transaction Log Legacy row = Pending | Ops succeeds; Legacy stuck — retry available |
| Ops leg fails | Console Transaction Log Ops row = Failed | Legacy succeeds; Ops stuck — retry available |
| Both legs fail | sync_status = Failed | Operator sees both retry buttons; MPE stays Draft |

## Recovery procedures

### Partial sync (one leg failed)

Same as MB Mixing:
1. Operator opens `Console Transaction Log` from Dash
2. Clicks "Retry" on the failed leg
3. `execute_submission_step` rebuilds `req_params` from `log.request_payload`
4. On success, second callback runs `apply_bridge_result`, promotes to Success

### MPE submission fails and `rollback_entries` fires

This is the most complex recovery scenario:

1. `rollback_entries()` runs inside the failed `on_submit`
2. It deletes the SE, resets JC/WO, rolls back MPE to draft, deletes batch
3. Operator sees the error message (`frappe.throw(msg)` at end of `rollback_entries`)
4. Operator can correct the issue and re-submit
5. On re-submit: `validate_lot_number()` passes (Job Card still open), inspection prerequisite still met

**Note:** If the rollback itself fails (exception caught), the MPE document
is reloaded but `stock_entry_reference` may still be set. Check `Error Log`
for `rollback_entries` entries. Manual intervention may be required.

### Idempotent re-run

If operator re-submits with the same `reference_id`:
- Console doctype unique constraint on `reference_id` blocks second insert
- `_safe_local_create` catches exception, returns None
- Legacy Bridge's idempotency check returns cached `MLDPE-2026-00142`
- Ops engine's idempotency check returns cached `MES-LOG-2026-01400`
- Both callbacks update the original Console doc

## What cannot be rolled back by MPE

The following state changes are **not reversed** by MPE cancel or rollback:

| State | Why not rolled back |
|---|---|
| Inspection Entry `batch_no` + `spp_batch_number` | Set by `submit_inspection_stock_entries_from_moulding()` which is called after SE submit — both are already in a committed state by then |
| `Blank Bin Issue Item`.`is_completed` | Physical material consumption already occurred; cancelling the manufacturing SE doesn't undo physical bin usage |
| `Item Bin Mapping`.`is_retired` or `qty` | Same as above — physical consumption happened |
| Asset Movement records | Created when bins are consumed and returned; cancelling MPE doesn't recall the bins |

If a MPE needs to be corrected after the fact, a **separate correction flow**
