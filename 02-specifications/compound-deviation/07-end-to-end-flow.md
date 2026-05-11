# 07 — End-to-end flow

> Read [`../master-batch-mixing/07-end-to-end-flow.md`](../master-batch-mixing/07-end-to-end-flow.md)
> for the full sequence diagram + race-condition narrative. Compound
> Deviation's flow differs in:
>
> 1. **Precondition:** a Rejected Compound Inspection must exist (Ops-side
>    submitted, Legacy-side never submitted per factory requirement)
> 2. **Legacy side creates a `Compound Inspection`** (not Compound Deviation)
> 3. **Ops side action is status-conditional** — only fires for Accepted

## Precondition narrative

Before a Deviation can be submitted:

1. An operator submitted a Compound Inspection on Dash
2. QC readings put the inspection into `status=Rejected`
3. `initialize_submission` ran the **factory requirement** skip — only
   the Ops leg POSTed; Legacy leg was suppressed
4. Console Inspection record on `console.m.frappe.cloud` has
   `sync_status=Partial` (Ops Synced, Legacy never attempted)
5. Ops has the rejected CI record; Legacy has nothing for this batch
6. Quality Manager is notified (via report or operator escalation) that
   a rejected lot needs a deviation decision

## Deviation submission narrative

**T+0:00** — QM opens Compound Deviation Entry on Dash. Scans the
rejected compound's `mix_barcode` (e.g. `C_26C03X1`).

**T+0:10** — `getRejectedCompoundInspection({mix_barcode})` fetches the
source CI. Dash renders the readings + identity as read-only. QM verifies
this is the right batch.

**T+0:20** — QM scans their own badge. `getAvailableEmployees({required_role: "Quality Manager"})` confirms role. `approverId` + `approverName` set.

**T+0:30** — QM selects status: `Rejected` (in this example — scrap
decision). Enters deviation reason: "Hardness reading 12 points below
spec; root cause: incorrect curing time per shift log."

**T+0:45** — QM clicks Submit. `handleSubmit` builds the payload with
`compound_inspection_data` (CI identity) + `compound_deviation_data`
(QM decision).

**T+0:46** — Console `initialize_submission`:
1. `build_transaction_payload` reads `Console Process Template "COMPOUND_DEVIATION"`. Template's `is_inspection_type=1`, so the unified `Console Inspection` row is created via `create_local_inspection` (Phase 3 path).
2. Resolves targets: status is not Rejected-CI (`process_code != "COMPOUND_INSPECTION"`), so both Legacy + Ops legs fire.
3. Two `Console Transaction Log` rows created, Pending.
4. Returns target_logs.

**T+0:47** — Dash fires `Promise.all([executeSubmissionStep(legacy), executeSubmissionStep(ops)])`.

### Legacy leg (T+0:47 → T+0:53)

1. POST to `sppmaster.frappe.cloud` Bridge endpoint
2. Bridge's `sync_process_transaction`:
   - Idempotency: no existing CI with this `reference_id`, proceed
   - `mapping = Legacy Sync Mapping "COMPOUND_DEVIATION"` — has empty `field_mappings`
   - `legacy_doc = frappe.new_doc("Compound Inspection")` (note: NOT Compound Deviation)
   - For-loop over `mapping.field_mappings` does nothing (empty)
   - `populate_compound_deviation_fields(legacy_doc, payload_data)`:
     - `_resolve_compound_identity` extracts mix_barcode + spp_batch_no from `compound_inspection_data` block
     - `_lookup_legacy_stock_entry` runs 6-strategy chain — strategy 1 (mix_barcode == spp_batch_no) hits on the SE created by the original DCR → returns `{stock_id, dc_receipt_id, batch_no}`
     - `_apply_compound_identity_to_doc` writes `scan_compound`, `mix_barcode`, `spp_batch_no`, `batch_no`, `stock_id`, `stock_entry_reference`, `dc_receipt_id`, `item_code`, `compound_ref`
     - `_apply_compound_header_to_doc` writes posting_date, inspection_date, batch_qty, transfer_qty
     - `_apply_compound_readings_to_doc` creates reading child rows
     - WAREHOUSE_MAP fallback → `source_warehouse = "U3-Store - SPP INDIA"`
     - `_apply_deviation_extras`:
       - `doc.status = "Rejected"` (QM's decision)
       - `doc.scan_quality_approver = approverId`
       - `doc.quality_approver_id = approverId`
       - `doc.quality_approver_name = approverName`
       - `doc.remarks = "Hardness reading 12 points below spec..."`
       - `doc.cavity_no = 1` ← fallback fires; structured log emitted
   - `legacy_doc.insert()` + `legacy_doc.submit()` — legacy Compound Inspection submits
   - Legacy CI's controller `on_submit` runs status-conditional SE creation:
     - For `status=Rejected`: creates a Stock Entry of purpose "Material Issue" → scrap warehouse (or write-off; depends on legacy config)
3. Bridge returns `{status: Success, reference_name: "CI-2026-...", stock_entry_reference: "MAT-STE-..."}`
4. Console `execute_submission_step` updates Transaction Log, calls `apply_bridge_result("Legacy", "Success", "CI-2026-...")`
5. 5-step dance: `legacy_sync_status=Synced`, aggregate=Partial (Ops still pending)

### Ops leg (T+0:47 → T+0:50)

1. POST to `newspp.m.frappe.cloud` Ops endpoint
2. `process_transaction` → `TransactionEngine`
3. Engine reads `sequence` from canonical payload
4. For the `transfer_to_store` action: condition `status == 'Accepted'` evaluates to **False** (status is Rejected) → action skipped
5. Engine returns `{status: success, log_name: "MES-LOG-...", results: {}, impacted_balances: []}`
6. Console `execute_submission_step` updates Transaction Log, calls `apply_bridge_result("Ops", "Success", "MES-LOG-...")`
7. 5-step dance: `ops_sync_status=Synced`. **Race window: Legacy still in flight.** Aggregate computed against current DB state — if Legacy already finished (race won by Legacy), aggregate=Success, auto-submit fires. If Legacy still Pending, aggregate=Partial.

### Race resolution (T+0:53)

When Legacy's callback runs after Ops:
1. Step 1: `legacy_sync_status=Synced`
2. Step 2: re-read both — both now Synced
3. Step 3: aggregate=Success
4. Step 4: self-heal — if Ops's earlier callback wrote Partial after winning step 3, this step corrects to Success
5. Step 5: fresh-doc auto-submit on `Console Inspection`

**This is the exact code path the 5-step pattern was designed for.** Both
legs near-simultaneously resolving; whichever's callback computes the
aggregate first may write a stale value; the second callback's step 4
self-heal corrects.

## Final state for one Rejected Deviation

| System | Document | State |
|---|---|---|
| Console | `Console Inspection CIN-2026-...` (Phase 3 unified path) | `docstatus=1`, `sync_status=Success`, both legs Synced |
| Console | Original `Console Inspection` for the source Rejected CI | Unchanged — still `sync_status=Partial` (Legacy was suppressed by factory req) |
| Legacy | `Compound Inspection CI-2026-...` (Deviation manifests as a CI) | `docstatus=1`, `status="Rejected"`, `quality_approver_id` populated, `remarks` carries reason |
| Legacy | `Stock Entry` (Material Issue / write-off) | `docstatus=1`, compound qty removed from inventory |
| Ops | `Shree Polymer MES Log MES-LOG-...` | `status=Success`, `result_payload.results={}` (no actions ran) |
| Ops | No new Stock Entry | Correct — action was skipped by status condition |

## Final state for an Accepted Deviation

Same as above except:
- Legacy CI has `status="Accepted"`, downstream behaviour treats compound
  as good
- Legacy SE is a Material Transfer (not Material Issue) — compound moves
  to ready warehouse
- Ops MES Log `result_payload.results` includes the `transfer_to_store`
  action output with `impacted_balances` populated

## Recovery procedures

### Identity lookup miss (the saga's main bug)

If `_lookup_legacy_stock_entry` returns None for all 6 strategies, the
Bridge logs a structured error and `_apply_compound_identity_to_doc` is
called with `se_lookup=None`. The legacy doc is then missing `stock_id`,
which is required by `Compound Inspection.validate()` → submit fails →
Bridge returns Failed.

**Root cause is almost always: upstream MB Mixing or DCR didn't sync to
Legacy.** Recovery is to find and resubmit the upstream record so the
SE materialises, then retry the Deviation from Dash.

### `cavity_no` validation failure

If the `_apply_deviation_extras` fallback fails (e.g. `doc.cavity_no = 1`
raises because the field doesn't exist on this legacy doctype), the
submission fails. Currently no documented recovery — would require
manual `frappe.db.set_value` on the legacy bench. Flagged in
`10-risks-and-decisions.md` as a wiring TODO.
