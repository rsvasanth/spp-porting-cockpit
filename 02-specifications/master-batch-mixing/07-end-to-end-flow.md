# 07 — End-to-end flow (one operator submission, traced)

This file is the **single canonical narrative** that ties layers 02–06
together. If you want to understand what actually happens when an operator
hits "Submit to ERP," read this file. The other layer files have the
details; this one has the choreography.

## Sequence diagram

```
┌──────────────┐  ┌───────────────────┐  ┌───────────────┐  ┌──────────────┐  ┌────────────┐
│ Dash (React) │  │ Console api.py    │  │ Console DocType│  │ Bridge       │  │ Legacy DCR │
│  Mac/iPad    │  │  on sppconsole-dev│  │  controller   │  │  sync_api.py │  │  on spp15  │
└──────┬───────┘  └─────────┬─────────┘  └───────┬───────┘  └──────┬───────┘  └──────┬─────┘
       │                    │                    │                  │                 │
       │  initialize_submission                  │                  │                 │
       ├───────────────────►│                    │                  │                 │
       │                    │ build_transaction_payload             │                 │
       │                    │ create_local_master_batch_mixing      │                 │
       │                    │   _safe_local_create                  │                 │
       │                    │   ├── flags.from_local_cache = True   │                 │
       │                    │   ├── doc.insert(ignore_validate=True)│                 │
       │                    │   └── upsert Console Transaction Log Pending             │
       │                    │ resolve targets (Legacy + Ops)        │                 │
       │                    │ log_transaction × 2 (Pending per leg) │                 │
       │ ◄──── {target_logs, reference_id, transaction_payload} ────┤                 │
       │                                                            │                 │
       │  Promise.all([                                             │                 │
       │    execute_submission_step(legacy_log),                    │                 │
       │    execute_submission_step(ops_log)                        │                 │
       │  ])                                                        │                 │
       │                                                            │                 │
       ├───── execute_submission_step({log, target_info}) ─────────►│                 │
       │                    │ POST {bridge_url}/api/method/...sync_process_transaction│
       │                    ├─────────────────────────────────────►│                  │
       │                    │                                       │ sync_process_transaction
       │                    │                                       │  ├── idempotency check
       │                    │                                       │  ├── get Legacy Sync Mapping
       │                    │                                       │  ├── apply field_mappings (incl. value_map)
       │                    │                                       │  ├── insert DCR Draft        │
       │                    │                                       │  ├── submit DCR             ────►│
       │                    │                                       │  │                              │ on_submit:
       │                    │                                       │  │                              │  validate_final_batches → False (Master Batch)
       │                    │                                       │  │                              │  MB SE creation chain runs (create_master_batch_stock)
       │                    │                                       │  │                              │  ◄── Manufacturing SE submitted
       │                    │                                       │  └── return {status, reference_name, log_name}
       │                    │ ◄──────────────────────────────────── │                              │
       │                    │ db.set_value Console Transaction Log {status, remote_log_name, ...}  │
       │                    │ update_local_domain_record(MASTER_BATCH_MIXING, ref, Success, Legacy)│
       │                    │   ├── lookup Console Master Batch Mixing by reference_id            │
       │                    │   └── doc.apply_bridge_result("Legacy", "Success", remote_name)     │
       │                    │         ├── Step 1: db.set_value legacy_sync_status = Synced        │
       │                    │         ├── Step 2: re-read ops_sync_status + legacy_sync_status     │
       │                    │         ├── Step 3: aggregate (ops=Pending, legacy=Synced → Partial) │
       │                    │         ├── Step 4: self-heal (nothing yet, ops still pending)       │
       │                    │         └── Step 5: don't submit yet (sync_status != Success)        │
       │                    │ apply_stock_updates(impacted_balances) [if any]                     │
       │ ◄── {status: Success, result: {reference_name, impacted_balances}} ─┤
       │                                                                                          │
       │   [meanwhile, Ops leg also resolving in parallel]                                        │
       │                                                                                          │
       ├──── execute_submission_step({log, target_info}) ─────────►│                              │
       │                    │ POST {ops_url}/api/method/...api.process_transaction
       │                    ├──────────────────────────────────────────────────►│ shree_polymer_ops
       │                    │                                                    │  process_transaction
       │                    │                                                    │  ├── MASTER_BATCH_MIXING → TransactionEngine
       │                    │                                                    │  ├── engine.execute()
       │                    │                                                    │  │     ├── idempotency check (MES Log)
       │                    │                                                    │  │     ├── for each step in sequence:
       │                    │                                                    │  │     │     ├── create Work Order
       │                    │                                                    │  │     │     ├── create Job Card
       │                    │                                                    │  │     │     └── create Stock Entry (Manufacture, submit)
       │                    │                                                    │  │     └── return {status, log_name, results, impacted_balances}
       │                    │ ◄──────────────────────────────────────────────────│
       │                    │ db.set_value Console Transaction Log {status, ...}
       │                    │ update_local_domain_record(MASTER_BATCH_MIXING, ref, Success, Ops)
       │                    │   └── doc.apply_bridge_result("Ops", "Success", remote_name)
       │                    │         ├── Step 1: db.set_value ops_sync_status = Synced
       │                    │         ├── Step 2: re-read both legs (now both Synced)
       │                    │         ├── Step 3: aggregate (both Synced → Success)
       │                    │         ├── Step 4: self-heal (no-op, already Success)
       │                    │         └── Step 5: fresh_doc.submit() ← Console doc auto-submits
       │                    │ apply_stock_updates(impacted_balances)
       │                    │   └── update_cache_from_balances → Console Stock Cache refreshed
       │ ◄── {status: Success, result: {impacted_balances, generated_barcodes}} ─┤
       │                                                                          │
       │  setSubmissionResult({status: Success, results: [Legacy, Ops], ...})    │
       │  Dash shows green checkmarks, barcode label, success modal               │
       │                                                                          │
```

## Narrative trace — one MB Mixing submission, step by step

**Setup:** Operator Saravanan (employee `HR-EMP-00101`, role
`Mixing Operator`) is at the Two Roll Mixing Mill. He mixes a 100 kg batch
of `MB_TEST_6122` using 50 kg of `B_TEST_6122` raw material. Console is
open on a tablet.

**T+0:00** — Saravanan scans his badge. Dash's `handleOperatorSelect`
validates against `availableEmployees` (cached from
`get_available_employees`). He selects MB item from the dropdown. Dash
calls `get_bom_for_produced_item` → returns BOM rows. Component renders
the BOMPanel with one expected raw-material row.

**T+0:30** — Saravanan scans the raw material barcode `C_26C03X0`. Dash
calls `validate_rm_barcode` which checks the barcode against current
stock — returns batch_no, spp_batch_no, available qty, source warehouse.
Row added to `scannedItems`.

**T+1:00** — Saravanan enters produced qty `100` (kg). Dash flips to
`currentStep = 'complete'`.

**T+1:15** — Saravanan clicks "Submit to ERP". `handleSubmit` runs:

1. `mixBarcode` is empty → falls back to primary scanned item's
   `mix_barcode` = `C_26C03X0`
2. `generatePayload(C_26C03X0)` produces the canonical payload with
   `reference_id = 1747234567890` (the current `Date.now()`)
3. `initializeSubmission({ payload })` POSTed to Console

**T+1:16** — Console `api.initialize_submission`:

1. `build_transaction_payload` reads `Console Process Template
   "MASTER_BATCH_MIXING"`, resolves warehouses (`Mixing - SPP` for Ops,
   `U3-Store - SPP INDIA` for Legacy), produces canonical payload
2. Routes to `create_local_master_batch_mixing`:
   - `_safe_local_create` inserts `Console Master Batch Mixing` row
     named `MBM-2026-00012`, status=Pending, sync_status=Pending
   - Child `consumption_items` row appended
   - `flags.from_local_cache=True` skips the strict validate
   - `Console Transaction Log` upserted with reference_id, Pending
3. Resolves targets: `sync_strategy = "Both (Parallel)"` → both Legacy and
   Ops targets added
4. Two more `Console Transaction Log` rows created (one per target leg)
5. Returns `{target_logs: [legacy_log, ops_log], reference_id: 1747234567890}`

**T+1:17** — Dash shows the SubmissionResult modal with both rows in
`Pending`. `Promise.all` fires both `executeSubmissionStep` calls in
parallel.

**Legacy leg (T+1:17 → T+1:24, runs in parallel with Ops):**

1. POST to `https://sppmaster.frappe.cloud/api/method/shree_polymer_legacy_bridge.sync_api.sync_process_transaction`
2. Bridge's `sync_process_transaction`:
   - Creates `Legacy Bridge Log` row, status=Pending
   - Idempotency: no existing DCR with this `reference_id`, proceed
   - Loads `Legacy Sync Mapping "MASTER_BATCH_MIXING"`
   - Applies field_mappings → builds DCR with:
     - `reference_id` = 1747234567890
     - `dc_no` = "1747234567890"
     - `dc_receipt_date` = today
     - `operation` = "Master Batch Mixing"
     - `inward_material_type` = "Master Batch" (via value_map)
     - `item_to_manufacture` = "MB_TEST_6122"
     - `bridge_mix_barcode` = "C_26C03X0"
     - `source_warehouse`, `target_warehouse`, `wip_warehouse` from config
     - `dc_items[0]` = {item_code: "B_TEST_6122", qty: 50, batch_no: ..., scan_barcode: "C_26C03X0", dc_no: "1747234567890", operation: "Master Batch Mixing", item_to_manufacture: "MB_TEST_6122"}
   - `legacy_doc.insert()` — DCR created Draft
   - `legacy_doc.submit()` — DCR submitted
   - DCR `on_submit` runs: `validate_final_batches` returns False (it's MB),
     so the FB-Mixing path is skipped. **But** the MB-specific SE creation
     chain (`create_master_batch_stock` / `create_mb_wo` /
     `make_mb_stock_entry`) runs from elsewhere in the legacy flow,
     materialising the Manufacturing Stock Entry with the
     `bridge_mix_barcode` as the FG batch identifier
   - Bridge response: `{status: "Success", reference_name: "DCR-2026-00342", log_name: "BLOG-2026-...", stock_entry_reference: "MAT-STE-2026-..."}`
3. Console `execute_submission_step` receives response:
   - Updates `Console Transaction Log` Legacy row to Success
   - Calls `update_local_domain_record("MASTER_BATCH_MIXING", 1747234567890, "Success", "Legacy", ...)`
   - Looks up `Console Master Batch Mixing` by reference_id → finds `MBM-2026-00012`
   - Calls `doc.apply_bridge_result("Legacy", "Success", "DCR-2026-00342")`
     - Step 1: `legacy_sync_status = Synced`, `legacy_reference = "DCR-2026-00342"`
     - Step 2: re-reads both legs → ops=Pending, legacy=Synced
     - Step 3: aggregate = Partial
     - Step 4: self-heal — no change (correct)
     - Step 5: don't auto-submit (sync_status = Partial, not Success)

**Ops leg (T+1:17 → T+1:21, finishes before Legacy):**

1. POST to `https://newspp.m.frappe.cloud/api/method/shree_polymer_ops.api.process_transaction`
2. Ops `process_transaction`:
   - `process_code = MASTER_BATCH_MIXING` → falls through to TransactionEngine
   - `engine.execute()`:
     - Idempotency: no MES Log with this reference_id, proceed
     - Creates `Shree Polymer MES Log` row, Pending
     - Step 1 of sequence: creates `Work Order` MFG-WO-2026-...
     - Step 2: creates `Job Card` JC-2026-...
     - Step 3: creates `Stock Entry` (Manufacture) — debits raw warehouse,
       credits target with FG batch = `C_26C03X0`
   - Returns `{status: "success", log_name: "MES-LOG-2026-01383", impacted_balances: [...], generated_barcodes: [...]}`
3. Console `execute_submission_step`:
   - Updates `Console Transaction Log` Ops row to Success
   - Saves `mix_barcode`, `fg_item_batch_no`, generates barcode image
   - Calls `update_local_domain_record(..., "Ops", ...)`
   - `doc.apply_bridge_result("Ops", "Success", "MES-LOG-2026-01383")`
     - Step 1: `ops_sync_status = Synced`, `ops_reference = "MES-LOG-..."`
     - Step 2: re-reads both legs → ops=Synced, legacy=**Pending** (still)
     - Step 3: aggregate = Partial
     - Step 4: self-heal — no change yet
     - Step 5: don't auto-submit

**The race window (T+1:21 → T+1:24):**

Ops finished first but its callback wrote `Partial` (because Legacy was
still Pending at that moment). When Legacy finishes (T+1:24) and runs its
own callback, it writes `Synced` for Legacy in step 1, then re-reads
both legs (step 2) to find both = Synced, aggregates to Success (step 3),
self-heals (step 4 — no correction needed since aggregate is already
Success), and auto-submits the fresh doc (step 5).

If the order had been reversed (Legacy first, Ops second), the Ops
callback would have done the same: step 1 sets ops=Synced, step 2 reads
both Synced, step 3 Success, step 5 auto-submits.

**T+1:24** — Dash receives both Promise resolutions. `submissionResult`
flips to `Success`. Modal shows:
- Legacy: ✅ `DCR-2026-00342`
- Ops: ✅ `MES-LOG-2026-01383`
- Generated mix barcode: `C_26C03X0`
- Print label dialog renders the barcode

**Final state (T+1:25):**

| System | Document | State |
|---|---|---|
| Console | `Console Master Batch Mixing MBM-2026-00012` | `docstatus=1`, `sync_status=Success`, `legacy_reference="DCR-2026-00342"`, `ops_reference="MES-LOG-2026-01383"` |
| Console | `Console Transaction Log` (Legacy row) | `status=Success`, `remote_reference_name="DCR-2026-00342"` |
| Console | `Console Transaction Log` (Ops row) | `status=Success`, `remote_reference_name="MES-LOG-2026-01383"` |
| Console | `Console Stock Cache` | Updated with impacted balances |
| Legacy | `Delivery Challan Receipt DCR-2026-00342` | `docstatus=1`, `dc_no="1747234567890"`, `bridge_mix_barcode="C_26C03X0"`, `stock_entry_reference="MAT-STE-2026-..."` |
| Legacy | `Stock Entry MAT-STE-2026-...` | `docstatus=1`, Manufacture purpose, FG row has `mix_barcode="C_26C03X0"` |
| Legacy | `Legacy Bridge Log` | `status=Success`, `reference_name="DCR-2026-00342"` |
| Ops | `Shree Polymer MES Log MES-LOG-2026-01383` | `status=Success`, `result_payload={Work Order, Job Card, Stock Entry names}` |
| Ops | `Work Order MFG-WO-2026-...` | Created |
| Ops | `Job Card JC-2026-...` | Created |
| Ops | `Stock Entry MAT-STE-2026-...` | `docstatus=1`, Manufacture, FG batch = `C_26C03X0` |

## What can go wrong, and at what point

| Failure mode | Where it surfaces | What state is left |
|---|---|---|
| Dash payload missing required field | `initialize_submission` returns Error | No Console doc, no Bridge call, no Ops call |
| Bridge URL not configured | `initialize_submission` throws | Same as above |
| Console Process Template inactive | `build_transaction_payload` throws | Same as above |
| `_safe_local_create` fails | Returns None — orchestration continues | Audit-trail record missing, but Bridge + Ops still fire |
| Legacy leg fails | Console Transaction Log Legacy row = Failed, sync_status = Partial | Ops record exists, Legacy doesn't; operator can retry Legacy leg from Dash |
| Ops leg fails | Same as above, swapped | Legacy record exists, Ops doesn't; operator retries Ops |
| Both legs fail | sync_status = Failed | Operator sees red modal; both retry buttons available |
| Bridge SE creation fails (rare) | `legacy_doc.submit()` throws → Bridge returns Failed | DCR rolled back, no SE — Console sees Legacy Failed |
| Race in `apply_bridge_result` | step 4 self-heal corrects | Final state always correct |
| Auto-submit fails in step 5 | Caught in try/except, logged | Console doc stays Draft (sync_status=Success but docstatus=0) — operator can submit manually |

## Recovery procedures

### Partial sync (one leg failed)

1. Operator opens the failed `Console Transaction Log` from the Dash log
   list
2. Clicks "Retry" — calls `execute_submission_step(log_name)`
3. `execute_submission_step` rebuilds `req_params` from
   `log.request_payload` (RETRY FLOW FIX) — idempotent on Bridge/Ops
4. On success, the second leg's callback runs `apply_bridge_result`,
   step 4 promotes sync_status to Success, step 5 auto-submits

### Console doc stuck in Draft despite both legs Synced

Run:
```python
doc = frappe.get_doc("Console Master Batch Mixing", "MBM-...")
doc.submit()
```

This is rare (step 5 catches exceptions silently and logs) — happens if
some validate gate trips on submit. Check `Error Log` for the
`apply_bridge_result.{doctype}` entry.

### Idempotent re-run

If for any reason Dash retries `initialize_submission` with the same
`reference_id`:
- The Console doctype's unique constraint on `reference_id` makes the
  second insert fail
- `_safe_local_create` catches the exception, returns None, orchestration
  continues
- The Bridge's idempotency check returns the cached `reference_name`
- The Ops engine's idempotency check returns the cached `log_name`
- Both legs' callbacks update the original Console doc — sync_status
  re-confirms Success

This is **why every layer keeps `reference_id` as the cross-system key**.
