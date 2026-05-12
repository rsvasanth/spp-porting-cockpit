# 06 — Acceptance criteria

Plain-language UAT scripts. Each is operator-runnable on staging and verifiable in under 15 minutes.

## AC-INS-001 — CI Accepted happy path

**Pre-conditions:**
- A successful Mixing submission (MB or FB) exists with a known `mix_barcode`
- The compound's stock is in the inspection-WIP warehouse on both Legacy and Ops
- BOM with reading-spec parameters exists for the produced item

**Steps:**
1. Quality Inspector opens Console Dash → Compound Inspection screen
2. Scans QI badge → operator selected
3. Scans the compound's `mix_barcode` → identity auto-fills (item, batch, spp_batch_no, source warehouse)
4. Records readings for each BOM parameter, all within spec → per-parameter Pass indicators
5. System derives overall `status="Accepted"`
6. Clicks Submit

**Pass conditions:**
- ✅ Within 30 seconds: success modal shows **✅ Legacy** + **✅ Ops**
- ✅ `Console Inspection` record has `sync_status="Success"`, `docstatus=1`, `inspection_type="Compound Inspection"`, `status="Accepted"`
- ✅ Legacy `Compound Inspection` exists with `status="Accepted"`, identity fields populated (mix_barcode, batch_no, stock_id, dc_receipt_id)
- ✅ Ops Stock Entry (Material Transfer) created moving compound from inspection-WIP → ready warehouse
- ✅ Console Transaction Log: 2 rows, both `Status="Success"`
- ✅ Downstream Sheeting can scan this compound and find it available in the ready warehouse

## AC-INS-002 — CI Rejected, then CD Accepted override

**Pre-conditions:**
- A compound batch exists in inspection-WIP

**Steps (Part 1 — CI Rejected):**
1. QI submits a CI with at least one reading outside BOM spec
2. System derives `status="Rejected"`
3. QI submits

**Pass conditions (Part 1):**
- ✅ Within 30 seconds: success modal shows **✅ Ops** + **(skipped) Legacy**
- ✅ Console Inspection record has `sync_status="Partial"`, `docstatus=0` (Draft — NOT auto-submitted)
- ✅ Ops has the CI record but **no Material Transfer SE** (since status=Rejected)
- ✅ Legacy has NO Compound Inspection record (factory-requirement skip)
- ✅ Console Transaction Log: 1 row (Ops only), `Status="Success"`

**Steps (Part 2 — CD Accept-override):**
4. Quality Manager opens CD screen, scans the same compound's barcode
5. Source CI is auto-fetched and displayed read-only
6. QM scans badge, selects `status="Accepted"`, enters reason "Hardness reading at boundary; acceptable per shift agreement"
7. Clicks Submit

**Pass conditions (Part 2):**
- ✅ Within 30 seconds: success modal shows **✅ Legacy** + **✅ Ops**
- ✅ Console Inspection record (the CD) has `sync_status="Success"`, `docstatus=1`, `inspection_type="Compound Deviation"`, `status="Accepted"`, `quality_approver_id` populated
- ✅ Legacy Compound Inspection now exists for the lot with `status="Accepted"`, `quality_approver_*` fields filled, `remarks` containing the reason, `cavity_no=1` (fallback)
- ✅ Bridge logs show `cavity_no` fallback fired with structured warning
- ✅ Ops Stock Entry (Material Transfer) created — compound moves to ready warehouse despite earlier rejection
- ✅ Original CI Console record remains in `sync_status="Partial"` (intentional — the CD is the closure)

## AC-INS-003 — CD Rejected (scrap)

**Pre-conditions:** A Rejected CI exists per Part 1 of AC-INS-002.

**Steps:**
1. QM opens CD screen, scans compound, scans badge, selects `status="Rejected"`, enters reason "Contamination detected; cannot rework"
2. Submits

**Pass conditions:**
- ✅ Within 30 seconds: ✅ Legacy + ✅ Ops
- ✅ Legacy Compound Inspection has `status="Rejected"`, QM signoff fields populated
- ✅ Ops Stock Entry (Material Issue) created — compound removed from inventory (moved to scrap warehouse or written off)
- ✅ Stock Ledger reflects the inventory loss on both ERPs

## AC-INS-004 — CD Rework (return to mixing)

**Pre-conditions:** A Rejected CI exists.

**Steps:**
1. QM opens CD, scans, selects `status="Rework"`, enters reason "Mixing time too short; reblend"
2. Submits

**Pass conditions:**
- ✅ Within 30 seconds: ✅ Legacy + ✅ Ops
- ✅ Legacy Compound Inspection has `status="Rework"`, QM fields populated
- ✅ Ops MES Log exists with `result_payload.results={}` — **no Stock Entry created** (action skipped by status condition)
- ✅ Compound stays in inspection-WIP warehouse on both ERPs (no movement)
- ✅ Operator can physically return compound to mixing area and re-blend

## AC-INS-005 — CI Partial sync recovery (Ops fails)

**Pre-conditions:** Ops site temporarily unreachable.

**Steps:**
1. QI submits an Accepted CI (Ops should fire alongside Legacy — but Legacy is skipped because... wait, Accepted CI fires both)
2. Ops fails (simulated by unreachable URL)

**Pass conditions:**
- ✅ Console Inspection has `sync_status="Partial"`, `docstatus=0`
- ✅ Ops Transaction Log row `Status="Failed"` with error
- ✅ Operator restores Ops connectivity, clicks Retry on the failed leg
- ✅ Retry uses same `reference_id`; Ops creates the Material Transfer SE
- ✅ Console auto-submits to `docstatus=1`, `sync_status="Success"`

## AC-INS-006 — CD idempotent retry

**Pre-conditions:** A CD submission's Legacy leg failed; record is `sync_status="Partial"`.

**Steps:**
1. Operator clicks Retry on the Legacy leg
2. Bridge's `find_existing_record` finds no prior CI for the reference_id; proceeds to create it
3. Legacy `populate_compound_deviation_fields` runs the full pipeline

**Pass conditions:**
- ✅ Legacy Compound Inspection created with all fields populated correctly
- ✅ Bridge log shows the call succeeded
- ✅ Console aggregate promotes to `sync_status="Success"`, auto-submit fires

## AC-INS-007 — Concurrent callback safety (saga regression test)

**Pre-conditions:** A test environment with `threading.Barrier` infrastructure.

**Steps:**
1. Run `test_apply_bridge_result_concurrent_callbacks` for:
   - `Console Inspection` (Phase 3)
   - `Console Compound Deviation` (legacy per-type)
   - `Console Compound Inspection` (legacy per-type)

**Pass conditions:**
- ✅ All three tests pass: final state is `sync_status="Success"`, `docstatus=1`, both leg statuses `Synced`
- ✅ No `TimestampMismatchError` errors logged
- ✅ Auto-submit fires exactly once per record

## AC-INS-008 — Source-CI fetch correctness

**Steps:**
1. QM opens CD screen and scans a compound barcode for which NO Rejected CI exists
2. Submit button must be disabled with a clear error message

**Pass conditions:**
- ✅ Dash shows "No rejected Compound Inspection found for this compound" (plain English)
- ✅ Submit button is disabled
- ✅ Operator can rescan a different barcode without screen reload

## AC-INS-009 — Backdating restriction

**Steps:**
1. Regular QI attempts to submit CI with `posting_date` 3 days ago → rejected
2. System Manager attempts same → accepted

**Pass conditions:**
- ✅ Regular role: rejected with "Date can be -1 day or today only"
- ✅ System Manager: succeeds; Legacy CI's `posting_date` matches the backdated value
- ✅ Forward-dating rejected for both roles

## AC-INS-010 — Identity round-trip across all three systems

**Pre-conditions:** AC-INS-001 has passed.

**Steps:**
1. Query `Console Inspection` by `mix_barcode` → returns the record
2. Query Legacy `Compound Inspection` by `mix_barcode` → returns the corresponding record
3. Query Ops Stock Entry by `mix_barcode` → returns the corresponding FG row

**Pass conditions:**
- ✅ All three queries return records linked by the same `mix_barcode`
- ✅ All three records share the same `reference_id`
- ✅ Legacy CI's `stock_id` resolves to a valid Manufacturing Stock Entry on Legacy

## Sign-off bar

The inspection-process motion is declared **production-shipped** when:

- AC-INS-001 through AC-INS-006 pass on staging within a single shift
- AC-INS-007 (saga regression) passes in unit tests
- AC-INS-008, AC-INS-009 pass functionally
- AC-INS-010 verified manually for at least 3 lots
- One full shift (~8 hours) elapses without:
  - Any `sync_status="Failed"` records on inspection doctypes
  - Any unmitigated cavity_no fallback fires (until wiring is done — then this is automatic)
  - Any operator-reported retry loops
- Production overseer signs off in writing (Obsidian note)

The motion is declared **broken** (requires rollback) if the saga-style race-condition regressions reappear despite the 5-step pattern.
