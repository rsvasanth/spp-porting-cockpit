> [!WARNING]
> **DECOMMISSIONED REQUIREMENT**
> As of 2026-05-20, the unification requirement is obsolete. The active design of record relies on separate doctypes. Do not follow the patterns described in this file.

# 07 — End-to-end flow

> The base flow for Compound Inspection is the same as Compound Deviation's narrative in [`../compound-deviation/07-end-to-end-flow.md`](../compound-deviation/07-end-to-end-flow.md). This file traces an **Accepted CI submission** (Phase 3 unified) to illustrate the unification dispatch.

## Narrative — one Compound Inspection submission (Accepted)

**Setup:** QI Saravanan inspects a compound batch with `mix_barcode = C_26C03X1`. All readings within spec → status will auto-derive to Accepted.

**T+0:00** — QI scans badge → operator selected.

**T+0:15** — Scans `C_26C03X1` → Dash calls `validate_compound_barcode`; identity + readings spec auto-fill.

**T+0:30** — Enters readings per BOM parameter. System auto-marks Pass/Fail. All Pass.

**T+1:00** — Clicks Submit. `handleSubmit`:

1. Builds payload with `metadata.process_code = "COMPOUND_INSPECTION"`, `compound_inspection_data.*`, readings array
2. Calls `initializeSubmission({ payload })`

**T+1:01** — Console `api.initialize_submission`:

1. `build_transaction_payload(payload)` runs
2. Reads `Console Process Template "COMPOUND_INSPECTION"` → `is_inspection_type=1`
3. Phase 3 dispatch: calls `create_local_inspection(prelim_payload, reference_id)`
4. `create_local_inspection`:
   - Reads `inspection_family="Compound"` from Process Template
   - Extracts identity via Compound family path: `mix_barcode = "C_26C03X1"`, `spp_batch_no`, etc.
   - Builds readings from `compound_inspection_data.readings`
   - Calls `_safe_local_create("Console Inspection", { inspection_type, mix_barcode, ... }, ...)`
   - Console Inspection record created (`INSP-2026-00043`)
   - Controller's `before_insert` runs: auto-fetches `process_code = "COMPOUND_INSPECTION"`, `inspection_family = "Compound"` from template
   - Controller's `validate` (bypassed due to `from_local_cache` flag)
5. Resolves targets:
   - `is_rejected_inspection = False` (status is Accepted in the readings, but Dash hasn't computed it yet — set by validation_dispatch_method)
   - Both Legacy + Ops legs fire
6. Creates Transaction Log rows (Pending) per target

**T+1:02** — Dash fires `Promise.all` on the target_logs.

### Legacy leg (T+1:02 → T+1:07)

1. POST to Bridge: `/api/method/shree_polymer_legacy_bridge.sync_api.sync_process_transaction` with `process_type="COMPOUND_INSPECTION"`
2. Bridge:
   - Idempotency: no existing record with this reference_id
   - Loads `Legacy Sync Mapping "COMPOUND_INSPECTION"` — has populated field_mappings (unlike CD which has empty)
   - Creates `Compound Inspection` legacy doc
   - Applies field_mappings (sets fields from `compound_inspection_data.*` paths)
   - Calls `populate_compound_inspection_fields(legacy_doc, payload_data)`:
     - `_resolve_compound_identity` extracts identity
     - `_lookup_legacy_stock_entry` runs 6-strategy chain → finds source MB Mixing SE
     - `_apply_compound_identity_to_doc` writes stock_id, dc_receipt_id, batch_no
     - `_apply_compound_header_to_doc` writes posting_date, transfer_qty, etc.
     - `_apply_compound_readings_to_doc` creates child reading rows
   - cavity_no fallback fires (active TODO) → sets cavity_no=1
   - `legacy_doc.insert()` + `legacy_doc.submit()`
   - Legacy CI's controller `on_submit` runs status-conditional SE creation (status=Accepted → Material Transfer SE)
3. Bridge returns `{status: Success, reference_name: "CI-2026-...", stock_entry_reference: "MAT-STE-..."}`
4. Console `execute_submission_step` updates Transaction Log + calls `update_local_domain_record`
5. Console `apply_bridge_result("Legacy", "Success", "CI-2026-...")`:
   - **Routes to `Console Inspection`** (via `is_inspection` check + legacy_doctype_map fallback)
   - 5-step dance executes
   - aggregate = Partial (Ops still pending)

### Ops leg (T+1:02 → T+1:05)

1. POST to Ops: `/api/method/shree_polymer_ops.api.process_transaction`
2. Ops `process_transaction` → falls through to `TransactionEngine`
3. Engine reads sequence from Console Process Template
4. `transfer_to_store` action: condition `status == 'Accepted'` → True → creates Material Transfer SE
5. Returns `{status: success, log_name: "MES-LOG-...", impacted_balances: [...]}`
6. Console `apply_bridge_result("Ops", "Success", "MES-LOG-...")`:
   - 5-step dance
   - When Legacy callback has already landed: both legs Synced → aggregate Success → step 5 auto-submits `Console Inspection` to docstatus=1
   - When Ops landed first: aggregate Partial until Legacy callback lands; Legacy's step 4 self-heal promotes to Success + auto-submits

### Race resolution

Same 5-step pattern as MB and CD. Whichever leg's callback lands second triggers the auto-submit.

## Final state for one Accepted CI

| System | Document | State |
|---|---|---|
| Console | `Console Inspection INSP-2026-00043` (Phase 3 unified) | `docstatus=1`, `sync_status="Success"`, `inspection_type="COMPOUND_INSPECTION"`, `inspection_family="Compound"`, `status="Accepted"`, readings child rows populated |
| Legacy | `Compound Inspection CI-2026-...` | `status="Accepted"`, stock_id linked to upstream MB SE, reading child rows |
| Legacy | `Stock Entry` (Material Transfer — compound moves from inspection-WIP to ready warehouse) | `docstatus=1` |
| Ops | `Shree Polymer MES Log` | `status="Success"`, transfer SE created |
| Ops | `Stock Entry` (Material Transfer) | `docstatus=1` |
| Console | Two `Console Transaction Log` rows | Both `Status="Success"` |

## Final state for one Rejected CI (factory-requirement skip)

If readings don't pass and status is derived as Rejected:

| System | Document | State |
|---|---|---|
| Console | `Console Inspection` (Phase 3) | `docstatus=0` (Draft), `sync_status="Partial"`, `inspection_type="COMPOUND_INSPECTION"`, `status="Rejected"` |
| Legacy | NO record (factory-requirement skip) | — |
| Legacy | NO Stock Entry | — |
| Ops | `Shree Polymer MES Log` | `status="Success"`, NO SE created (action skipped by status condition) |
| Ops | NO Stock Entry | — |
| Console | One `Console Transaction Log` row (Ops only — Legacy never POSTed) | `Status="Success"` |

The CI remains in Partial state until a Compound Deviation closes it (per the CD spec's flow).

## Pre-Phase-3 callback flow (legacy record receives a callback)

If a Bridge callback arrives for a pre-cutover record (with `reference_id` matching a `Console Compound Inspection` or `Console Compound Deviation` row), the module-level `apply_bridge_result` finds the parent in the legacy doctype lookup list and calls its controller's `apply_bridge_result`.

This works because:
- `parent_doctypes` list in `api.py::apply_bridge_result` includes `Console Compound Deviation` and `Console Compound Inspection` AFTER `Console Inspection`
- Each pre-Phase-3 doctype's controller implements the same 5-step pattern byte-identically
- The pre-Phase-3 doctype's data shape is identical from the Bridge's perspective (same field names)

**Implication:** Legacy doctype callbacks survive the Phase 3 transition transparently. Pre-cutover records keep working until they're manually cancelled or backfilled.
