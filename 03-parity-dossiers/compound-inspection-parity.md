# Compound Inspection Porting Parity Dossier

**Status:** Draft parity dossier  
**Scope:** Compound Inspection only  
**Systems:** Console, Legacy Bridge, legacy ERPNext, Ops ERPNext  
**Runtime impact:** Documentation only. No schema, code, or process behavior changes.

## Purpose and Scope

This dossier proves how the legacy `Compound Inspection` business case is achieved in the Console architecture.

The pilot covers:

- Console Compound Inspection operator flow.
- Console local audit record creation.
- Legacy Bridge posting to legacy `Compound Inspection`.
- Ops posting through the generic MES `TransactionEngine`.
- Accepted vs Rejected routing.
- Success, partial success, failure, retry, and evidence capture.

Compound Deviation is related because it writes the same legacy doctype, but it is not fully audited here. Downstream Sheeting, Packing, and Invoicing are chain context only.

## Business Parity Summary

Legacy Compound Inspection validates a compound batch after Final Batch Mixing. It checks maturation, captures QC readings, enforces approver scans when readings or aging are outside limits, submits the upstream DCR Stock Entry, creates a Quality Inspection, and releases or blocks the compound for the next stage.

Console ports that behavior by splitting responsibilities across layers:

| Concern | Legacy behavior | Console-era behavior |
| --- | --- | --- |
| Operator UX | Desk `Compound Inspection` form | React Dash `CompoundInspectionEntry` |
| Compound lookup | Legacy `validate_compound_barcode` checks Stock Entry/DCR state | Console validates the compound barcode and builds a normalized payload |
| Reading rules | Legacy controller compares hardness, SG, TS2, TC90 | Console pre-computes readings/OOR flags; Legacy still re-validates its copy |
| Accepted output | Submit DCR Stock Entry and create Quality Inspection | Ops creates Quality Inspection and Material Transfer; Legacy creates legacy CI where routed |
| Rejected output | Requires approver/deviation handling | Console factory rule routes rejected CI to Ops only; Legacy sync happens later through Deviation |
| Audit trail | ERP document history | Console Transaction Log, Console Compound Inspection, Legacy Bridge Log, MES Transaction Log |

The architectural rule remains: **Console is the process brain; Legacy Bridge and Ops execute prepared payloads.**

## Legacy Compound Inspection Behavior

Legacy controller: `apps/shree_polymer_custom_app/shree_polymer_custom_app/shree_polymer_custom_app/doctype/compound_inspection/compound_inspection.py`.

Code-backed behavior:

- `CompoundInspection.compare_parameters` checks Hardness, SG, TS2, and TC90 against min/max and sets `no_enough_*` flags at lines 10-82.
- `validate` requires `stock_id` and all observed readings, computes maturation status through `get_aging_diff`, and re-runs parameter comparison at lines 84-107.
- `on_submit` requires maturation approver when aging is insufficient, requires quality approver when any reading is out of range, requires `dc_receipt_id`, and then calls `submit_dc_receipt_stock` at lines 108-130.
- `get_aging_diff` derives maturation from the linked `Delivery Challan Receipt` mixing date/time, falling back to Stock Entry posting date/time where needed, at lines 131-172.
- `submit_dc_receipt_stock` submits the linked draft Stock Entry, aligns posting date/time with DCR, then creates the Quality Inspection at lines 214-247.
- `create_quality_inspection_entry` creates and submits ERPNext `Quality Inspection` readings for hardness, SG, TS2, and TC90 at lines 248-308.
- `validate_compound_barcode` blocks duplicate inspections, requires a draft Stock Entry, verifies the source DCR is submitted, and fetches the item quality inspection template at lines 310-366.
- `validate_inspector_barcode` checks the employee barcode and designation mapping at lines 368-398.

Legacy therefore remains the legacy-side contract for accepted Compound Inspection records. Console does not remove legacy validation; it prepares data so the legacy controller can submit cleanly.

## Console Rewrite Behavior

Frontend screen: `apps/shree_polymer_console/dash/src/components/processes/CompoundInspectionEntry.tsx`.

Template evidence:

- `COMPOUND_INSPECTION` is seeded as a Quality process, uses `CompoundInspectionEntry`, outputs `Stock Entry, Quality Inspection`, and has `sync_strategy = "Both (Parallel)"` at `apps/shree_polymer_console/shree_polymer_console/shree_polymer_console/console_template_seeder.py` lines 309-320.
- Warehouse routing is status-aware: source is Compound Inspection, accepted target is Compound store, rejected target is Scrap at lines 321-344.
- Ops creates `Quality Inspection` for all CI submissions at lines 345-365.
- Ops creates Material Transfer only when `status == 'Accepted' and target_system == 'Ops'` at lines 366-389.
- Legacy sync action runs only when `target_system == 'Legacy'` at lines 390-399.
- The template records the intended inspection family/config at lines 413-425, but the active runtime uses the dedicated `Console Compound Inspection` doctype rather than the decommissioned unified inspection doctype.

Frontend payload evidence:

- Warehouse selection follows template purpose and status at `CompoundInspectionEntry.tsx` lines 173-192.
- Operator scan requires `Compound Inspector`; approver scan requires `Quality Executive` at lines 196-208 and 262-270.
- Compound barcode scan validates the batch, loads QC parameter specs, builds readings, and checks aging at lines 211-259.
- Payload creation builds `reference_id`, metadata, config, flat Ops placeholder keys, `compound_inspection_data`, `quality_inspection_data`, and accepted-only `stock_entry_data` at lines 280-390.
- Submit validates operator, compound, sample weight, cavity number, aging approver, readings, and retest reason before posting at lines 395-408.
- Submit initializes target logs, executes each target concurrently, and computes `Success`, `Partial Success`, or `Failed` at lines 410-463.
- On full success, the UI saves a label/history payload for reprint at lines 468-495.

Important routing distinction:

- Accepted CI can target both Legacy and Ops.
- Rejected CI is intentionally Ops-only in Console initialization; Legacy sync happens later through Compound Deviation.

## Console Local Audit Trace

Console backend: `apps/shree_polymer_console/shree_polymer_console/shree_polymer_console/api.py`.

- `initialize_submission` builds the transaction payload and routes `COMPOUND_INSPECTION` to `create_local_compound_inspection` at lines 1084-1110.
- It implements the factory rule: rejected Compound Inspections are not routed to Legacy at lines 1142-1149.
- It records the actual target intent on `Console Compound Inspection` as `Both`, `Ops`, or `Legacy` at lines 1157-1190.
- It creates one pending `Console Transaction Log` per target, storing target-specific request payloads at lines 1215-1249.
- `create_local_compound_inspection` mirrors the payload locally into `Console Compound Inspection`, including item, batch, SPP batch, mix barcode, qty, warehouse, inspector, status, posting date/time, remarks, payload snapshot, and child readings at lines 2091-2139.
- `update_local_domain_record` maps `COMPOUND_INSPECTION` callbacks to `Console Compound Inspection` and calls `apply_bridge_result` when present at lines 3626-3687.

Expected Console outputs:

- `Console Compound Inspection`
- `Console Compound Inspection Reading` child rows
- `Console Transaction Log` for Ops
- `Console Transaction Log` for Legacy only when accepted
- Stored request payload, response payload, remote reference, and detailed error fields
- Optional saved inspection label/history data after full success

## Legacy Posting Trace

Console mapping seeder: `apps/shree_polymer_console/shree_polymer_console/shree_polymer_console/console_mapping_seeder.py`.

- `seed_compound_inspection_mapping` maps `COMPOUND_INSPECTION` to legacy `Compound Inspection` at lines 169-201.
- Header mappings include scan compound, operator, compound ref, posting date, sample weight, cavity number, and source warehouse at lines 172-181.
- Reading mappings include hardness, SG, TS2, TC90 observed values and out-of-range flags at lines 182-193.
- Status and quality approver fields map to legacy quality-approver fields at lines 195-198.

Legacy Bridge: `apps/shree_polymer_legacy_bridge/shree_polymer_legacy_bridge/sync_api.py`.

- `sync_process_transaction` creates a `Legacy Bridge Log`, checks idempotency, loads `Legacy Sync Mapping`, creates the legacy document, injects `reference_id`, and transforms mapped fields at lines 259-354.
- `find_existing_record` prevents duplicate legacy CI by `scan_compound + posting_date` for `COMPOUND_INSPECTION` at lines 554-580.
- `_resolve_compound_identity` normalizes identity from `compound_inspection_data`, deviation data, or top-level payload at lines 838-865.
- `_lookup_legacy_stock_entry` finds the upstream draft/submitted Stock Entry created by DCR/mixing using six strategies and logs detailed diagnostics on miss at lines 868-970.
- `_apply_compound_identity_to_doc` writes `stock_id`, `stock_entry_reference`, `dc_receipt_id`, batch, barcode, compound ref, and item identity at lines 973-1016.
- `_apply_compound_header_to_doc` copies legacy-mandatory header fields such as operator, batch, posting date/time, qty, and cavity number at lines 1018-1063.
- `_apply_compound_readings_to_doc` writes readings, spec ranges, OOR flags, and quality approver fallback readings at lines 1065-1135.
- `populate_compound_inspection_fields` orchestrates identity lookup, header population, and readings population for Console CI payloads at lines 1209-1223.

Expected Legacy outputs for accepted CI:

- `Legacy Bridge Log`
- legacy `Compound Inspection`
- submitted legacy upstream Stock Entry, if still draft
- legacy `Quality Inspection`
- linked `qc_inspection_ref` on legacy CI

Rejected CI should not create a legacy `Compound Inspection` from the direct CI submission. It should be handled through the Deviation process when the business decision is made.

## Ops Posting Trace

Ops entry point: `apps/shree_polymer_ops/shree_polymer_ops/api.py`.

- `process_transaction` parses the payload and delegates to `TransactionEngine` at lines 47-78.
- Business failures return a structured failed payload with partial results, log name, reference id, and warnings at lines 79-101.
- `TransactionEngine` stores context, sequence, metadata, reference id, and sets `target_system = "Ops"` at lines 104-132.
- `execute` checks idempotency, creates `MES Transaction Log`, executes sequence actions with savepoints, commits on success, and fetches impacted balances after commit at lines 141-229.
- Quality Inspection enrichment fills reference Stock Entry, item template, batch, status, SPP batch, remarks, readings, mandatory `value`, and string reading values at lines 700-799.
- Stock Entry structure is logged before save at lines 800-808.
- Generic `create_doc` normalizes Stock Entry batch identifiers before insert at lines 1370-1387.

Expected Ops outputs:

- `MES Transaction Log`
- ERPNext `Quality Inspection` for the inspected compound
- ERPNext `Stock Entry` Material Transfer only when status is `Accepted`
- `impacted_balances` for successful stock movement
- `impacted_bundles` if serial/batch bundles are affected
- structured failure response if Quality Inspection or Stock Entry validation fails

## Success Response Handling

Console uses the same two-stage live-feedback pattern as Mixing:

1. `initialize_submission` creates local audit record and pending target logs.
2. The Dash calls `execute_submission_step` for each target and updates the modal target by target.

Backend behavior:

- Legacy requests are shaped as `payload`, `process_type`, and `reference_id`; Ops receives `payload` only at `api.py` lines 1221-1229.
- `execute_submission_step` rebuilds request params from stored log payloads during retry at lines 1303-1317.
- It posts to the target Frappe method, normalizes status, and stores response payload, remote log, remote reference doctype/name, mix barcode, FG batch, barcode image, and detailed error at lines 1321-1393.
- On success, it updates local stock cache from `impacted_balances` at lines 1401-1405.

Frontend behavior:

- The modal starts as `Processing`.
- Each target starts `Pending`, moves to `Processing`, then becomes `Success` or `Failed`.
- Final status is:
  - `Success` when all target legs succeed.
  - `Partial Success` when at least one leg succeeds.
  - `Failed` when no target leg succeeds.

## Error and Failure Handling

Errors that must be captured in parity testing:

| Failure | Expected capture |
| --- | --- |
| Invalid operator | Dash error from role validation |
| Invalid compound barcode | Dash error from compound barcode validation |
| Duplicate legacy CI | Legacy/Bridge failure or idempotency evidence for same compound/date |
| DCR missing/not submitted | Legacy Bridge diagnostic and legacy validation failure |
| Upstream Stock Entry not found | `Bridge SE Lookup FAILED` diagnostic with attempted strategies |
| Missing Quality Inspection template | Dash/Legacy/Ops failure with item code and template evidence |
| Aging insufficient without approver | Dash validation or legacy `on_submit` failure |
| Reading out of range without quality approver | Dash validation or legacy `on_submit` failure |
| Rejected direct CI | Ops-only target intent; no Legacy target log |
| Ops serial/batch bundle error | MES failed response and Console Transaction Log detailed error |
| Legacy success, Ops failure | `Partial Success`, one synced log and one failed log |
| Ops success, Legacy failure | `Partial Success`, Ops stock/QI evidence plus failed Legacy Bridge evidence |
| Retry after failure | Same `reference_id`, same stored request payload, updated response fields |

## Real-Data Test Evidence Plan

Do not run stock-consuming tests as part of documentation generation. When explicitly approved, run against staging only.

Recommended evidence folder per run:

```text
spp-porting-cockpit/03-parity-dossiers/evidence/
  YYYY-MM-DD-ci-reference-id/
    input-payload.json
    console-compound-inspection.json
    console-transaction-logs.json
    legacy-bridge-request-response.json
    legacy-compound-inspection.json
    legacy-linked-documents.json
    ops-request-response.json
    ops-mes-transaction-log.json
    ops-quality-inspection.json
    ops-stock-entry.json
    stock-movement-evidence.json
    failure-traceback.txt
    summary.md
```

Positive test cases:

- Accepted CI with valid compound barcode, valid aging, in-range readings.
- Accepted CI with out-of-range reading and valid Quality Executive approval.
- Accepted CI where both Legacy and Ops succeed with same `reference_id`.
- Rejected CI routes Ops-only and leaves no direct Legacy target log.

Negative test cases:

- Invalid operator role.
- Invalid or already inspected compound barcode.
- Missing Quality Inspection Template.
- Upstream DCR not submitted.
- Upstream Stock Entry lookup miss on Legacy Bridge.
- Aging insufficient without approver.
- Out-of-range QC reading without approver.
- Duplicate `reference_id`.
- Ops serial/batch bundle failure.
- Partial success and manual retry.

Minimum fields to capture:

- `reference_id`
- status (`Accepted` / `Rejected`)
- operator and approver ids
- compound barcode / mix barcode / SPP batch number
- item code and native batch number
- source and target warehouses
- sample weight and transfer quantity
- cavity number
- all QC readings and min/max limits
- Console local document name
- Legacy Compound Inspection name when routed
- Ops Quality Inspection name
- Ops Stock Entry name when accepted
- Legacy Bridge Log name/status/response
- MES Transaction Log name/status/response
- Console Transaction Log names/statuses/request/response
- stock balance deltas or impacted balances

Acceptance rule:

The test passes only when the same `reference_id` can trace the intended target legs across Console, Legacy Bridge, legacy ERPNext, and Ops. For rejected direct CI, the accepted trace is Console + Ops only; Legacy must be absent by design.

## Known Drift and Risks

- `console-inspection-unification` is decommissioned. Current CI uses dedicated `Console Compound Inspection`, not unified `Console Inspection`.
- Rejected CI routing is intentionally Ops-only; testers must not treat the missing Legacy target as a failure.
- Legacy Bridge depends on finding the upstream DCR Stock Entry. If MBM/FBM/DCR did not sync to Legacy, CI Legacy posting will fail even if the CI payload is correct.
- Legacy Compound Inspection still submits the upstream Stock Entry and creates a legacy Quality Inspection, so legacy side effects must be tested with real staging data before cutover confidence.
- Quality Inspection readings need mandatory `value` fields and string-safe readings on Ops; the TransactionEngine contains defensive enrichment for this.
- Serial and Batch Bundle failures are Ops engine/ERPNext validation failures; the dossier requires capturing the exact MES log and request payload for those cases.

