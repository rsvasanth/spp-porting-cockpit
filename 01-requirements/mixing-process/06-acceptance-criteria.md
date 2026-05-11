# 06 — Acceptance criteria

These are the **plain-language UAT scripts** the production overseer (you) uses to declare the process shipped. Each AC is operator-runnable on staging and verifiable in under 10 minutes.

## AC-MIX-001 — Master Batch Mixing happy path

**Pre-conditions:**
- One operator with role `Mixing Operator` exists on Console + Legacy + Ops
- Raw materials are in stock on all three systems
- A BOM exists for the produced Master Batch item

**Steps:**
1. Operator opens Console Dash, navigates to Master Batch Mixing
2. Scans their employee badge → operator selected
3. Selects a Master Batch item from the produced-item dropdown
4. Scans each raw material's barcode in sequence → each row populates automatically
5. Enters produced qty (e.g. 100 kg) in the qty field
6. Clicks **Submit to ERP**

**Pass conditions:**
- ✅ Within 30 seconds: success modal shows both **✅ Legacy** and **✅ Ops**
- ✅ Console mix barcode (e.g. `C_26C03X1`) is displayed and rendered as a printable label
- ✅ Within 60 seconds: `Console Master Batch Mixing` record has `sync_status="Success"`, `docstatus=1`
- ✅ Legacy `Delivery Challan Receipt` exists with `dc_no = reference_id`, `inward_material_type="Master Batch"`, `bridge_mix_barcode = <Console barcode>`, child `dc_items` row count matches
- ✅ Ops `Stock Entry` (Manufacture) exists with raw materials debited from source warehouse and produced Master Batch credited to target warehouse, FG row carries `mix_barcode = <Console barcode>`
- ✅ Stock Ledger Entries reconcile on both ERPs (qty deltas match Console submission)

## AC-MIX-002 — Final Batch Mixing happy path

**Pre-conditions:**
- AC-MIX-001 has passed (i.e. a Master Batch lot is available)
- The MB lot has stock on both Legacy and Ops
- The MB barcode is scannable on a label or screen
- A BOM exists for the produced Compound item

**Steps:**
1. Operator opens Final Batch Mixing screen
2. Scans badge → operator selected
3. Selects a Compound item from the produced-item dropdown
4. **Scans the Master Batch lot's barcode** (the one from AC-MIX-001) → MB row appears as the first consumption row with `is_batch_item=1`
5. Scans each additional raw material → rows populate
6. Enters produced qty (e.g. 100 kg)
7. Clicks **Submit to ERP**

**Pass conditions:**
- ✅ All conditions from AC-MIX-001 (sync_status=Success, both ERPs have records, etc.)
- ✅ Legacy DCR has `inward_material_type="Compound"`, `dc_items[0].is_batch_item=1` for the MB consumption row
- ✅ Legacy's `validate_final_batches` took the batched-FB path (verified via the Bridge log's transformed_data)
- ✅ The MB lot's stock is reduced on both Legacy and Ops by the consumed qty
- ✅ Ops Stock Entry has the Compound credited to target warehouse with `mix_barcode = <new Console barcode>` (different from the MB's barcode)
- ✅ Downstream Compound Inspection can scan the new Compound's barcode and resolve back to this FBM record

## AC-MIX-003 — Partial sync (Legacy fails, Ops succeeds)

**Pre-conditions:**
- Bridge URL configured to a deliberately-unreachable endpoint (simulating outage)
- Ops site fully reachable

**Steps:**
1. Operator runs AC-MIX-001 steps 1–6

**Pass conditions:**
- ✅ Within 30 seconds: success modal shows **✅ Ops** + **❌ Legacy** with an error message
- ✅ `Console Master Batch Mixing` record has `sync_status="Partial"`, `docstatus=0` (still Draft)
- ✅ Ops Stock Entry exists; Legacy DCR does NOT exist
- ✅ `Console Transaction Log` Legacy row has `status="Failed"` with a readable error message
- ✅ A Retry button is visible on the failure row
- ✅ Operator restores Bridge connectivity, clicks Retry → within 30 seconds, both legs report Success and the Console doc auto-submits to `docstatus=1`

## AC-MIX-004 — Idempotent submission

**Pre-conditions:**
- AC-MIX-001 just passed; the reference_id is known

**Steps:**
1. Manually re-trigger the same `initialize_submission` call with the same `reference_id` (e.g. via bench console or rapid Dash double-click)

**Pass conditions:**
- ✅ The second submission attempt is rejected with a clear duplicate-key error
- ✅ No new records are created on Console, Legacy, or Ops
- ✅ The original successful submission's records remain intact

## AC-MIX-005 — Audit trail for partial payload

**Pre-conditions:**
- A Dash bug or scanner glitch produces an incomplete payload (e.g. zero qty, empty consumption_items)

**Steps:**
1. Submit the malformed payload via Dash

**Pass conditions:**
- ✅ Console still creates a `Console Master Batch Mixing` record (even though it's incomplete)
- ✅ `sync_status="Pending"`, `status="Pending"`
- ✅ `payload_snapshot` field contains the full submitted JSON for replay/diagnostic
- ✅ The Bridge call may fail (acceptable — the audit record exists for incident review)
- ✅ Operator sees a failure message but can investigate via the Transaction Log

## AC-MIX-006 — Backdating restriction enforcement

**Steps:**
1. As a regular Mixing Operator, attempt to submit with `posting_date` = 3 days ago
2. As a System Manager, attempt the same

**Pass conditions:**
- ✅ Regular operator: rejected with "Date can be -1 day or today only"
- ✅ System Manager: accepted; submission completes normally
- ✅ Legacy DCR's `dc_receipt_date` matches the backdated value (for System Manager case)
- ✅ Forward-dating is rejected for both roles

## AC-MIX-007 — Concurrent multi-operator submission

**Pre-conditions:**
- 3 operators (different employee IDs) on 3 workstations

**Steps:**
1. All 3 operators click Submit at approximately the same time (within 1 second of each other)

**Pass conditions:**
- ✅ All 3 submissions complete with `sync_status="Success"` within 30 seconds each
- ✅ Each submission's records are isolated (no cross-contamination of reference_ids, mix_barcodes, or batch numbers)
- ✅ Stock Ledger Entries on both ERPs reflect all 3 production events correctly

## AC-MIX-008 — Race-safe callback handling

**Pre-conditions:**
- Test infrastructure that can fire Ops + Legacy callbacks within milliseconds of each other (via `threading.Barrier` in a unit test)

**Steps:**
1. Run `test_apply_bridge_result_concurrent_callbacks` against `Console Master Batch Mixing`
2. Repeat for `Console Final Batch Mixing`

**Pass conditions:**
- ✅ Both tests pass: final state is `sync_status="Success"`, `docstatus=1`, both leg statuses Synced
- ✅ No errors logged about TimestampMismatchError or stale state
- ✅ The auto-submit step (step 5 of the 5-step pattern) fires exactly once

## AC-MIX-009 — Cut-bit recycling [FBM-only]

**Pre-conditions:**
- A cut-bit batch (prefix `Cutbit_*`) exists from a previous Sheeting submission with available stock

**Steps:**
1. Operator runs AC-MIX-002 but scans a cut-bit batch as one of the additional raw materials

**Pass conditions:**
- ✅ Cut-bit batch is accepted as a valid input
- ✅ Cut-bit stock is reduced on both Legacy and Ops by the consumed qty
- ✅ FBM record's consumption_items shows the cut-bit row alongside fresh raw materials
- ✅ Downstream traceability: from the produced Compound batch, one can walk back via batch lookups to find the Cut-bit's source Sheeting submission

## AC-MIX-010 — Cross-system identity for downstream consumers

**Pre-conditions:**
- AC-MIX-001 and AC-MIX-002 have passed
- The downstream Compound Inspection process is operational on Console

**Steps:**
1. Open the Compound Inspection screen on Dash
2. Scan the FBM-produced Compound's mix barcode

**Pass conditions:**
- ✅ Compound Inspection auto-fills the source compound's identity (item, batch, mix barcode, dc_receipt_id, stock_id)
- ✅ When the CI is submitted, it correctly references the Mixing's manufacturing SE on Legacy
- ✅ The 6-strategy SE lookup resolves cleanly via strategy 1 (`mix_barcode == spp_batch_no`)

## Sign-off bar

The process is declared **production-shipped** when:

- AC-MIX-001, AC-MIX-002, AC-MIX-003, AC-MIX-004, AC-MIX-005, AC-MIX-006 all pass on staging within a single shift
- AC-MIX-007 (concurrent) passes once with 3 operators
- AC-MIX-008 (race-safe) passes in unit tests
- At least one full shift (typically 8 hours of normal operation) elapses without:
  - Any `sync_status="Failed"` Console records
  - Any operator-reported retry loops (Partial → retry → Partial → retry → ...)
  - Any Bridge or Ops uncaught exceptions in error logs
- Production overseer signs off in writing (Obsidian note at `/Users/alphaworkz/claude-obsidian/claude/`)

The process is declared **broken** (and requires rollback) if any of the above pass conditions consistently fail despite operator retry.
