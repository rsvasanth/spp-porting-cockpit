# Mixing Porting Parity Dossier: MBM, FBM, and Delivery Challan Receipt

**Status:** Draft parity dossier  
**Scope:** Master Batch Mixing, Final Batch Mixing, and legacy Delivery Challan Receipt  
**Systems:** Console, Legacy Bridge, legacy ERPNext, Ops ERPNext  
**Runtime impact:** Documentation only. No schema, code, or process behavior changes.

## Purpose and Scope

This dossier proves how the legacy `Delivery Challan Receipt` (DCR) mixing business case is achieved in the Console architecture.

The pilot covers:

- Master Batch Mixing (MBM): raw/material mix input to Master Batch output.
- Final Batch Mixing (FBM): Master Batch plus raw/material input to Compound output.
- Legacy DCR: the legacy ERPNext document that still receives the Legacy posting.
- Ops: the new ERPNext posting path through the generic MES `TransactionEngine`.

Downstream processes such as Compound Inspection, Sheeting, Packing, and Invoicing are chain context only. They are not fully audited in this dossier.

## Business Parity Summary

Legacy DCR used one ERPNext document to receive mixed material and then trigger the manufacturing-side work: validation, Work Order, Job Card, Stock Entry, and Delivery Note status updates. Console ports that same business case by splitting responsibilities across layers:

| Concern | Legacy behavior | Console-era behavior |
| --- | --- | --- |
| Operator UX | Desk form for `Delivery Challan Receipt` | React Dash process screen for MBM/FBM |
| Process rules | DCR JS/Python controller | Console Process Template plus Console payload builder |
| Legacy output | Submitted `Delivery Challan Receipt` | Same DCR created by Legacy Bridge |
| Ops output | Not applicable to legacy-only flow | Generic Ops Work Order, Job Card, and Stock Entry |
| Idempotency | Limited by document checks | Shared `reference_id` across Console, Legacy, and Ops |
| Audit trail | ERP document history | Console Transaction Log, Legacy Bridge Log, MES Transaction Log, payload snapshots |

The architectural rule remains: **Console is the process brain; Legacy Bridge and Ops execute generic instructions.**

## Legacy DCR Business Behavior

The legacy controller is `apps/shree_polymer_custom_app/shree_polymer_custom_app/shree_polymer_custom_app/doctype/delivery_challan_receipt/delivery_challan_receipt.py`.

Code-backed behavior:

- `DeliveryChallanReceipt.validate` rejects a future mixing date at lines 10-12.
- `DeliveryChallanReceipt.on_submit` calls `validate_final_batches`, then `create_wo`, then updates Delivery Note status at lines 14-22.
- `validate_final_batches` branches on `inward_material_type == "Compound"` and decides whether the submission is a direct compound path, a combined MB/FB path, or invalid grouping at lines 146-191.
- `create_wo` groups `dc_items` by DC, operation, and item to manufacture, then creates manufacturing work for non-Compound output at lines 413-455.
- `create_wo_final_batch_mixing` performs FB-specific BOM validation and Work Order creation at lines 626-675.
- `make_stock_entry_final_batch` creates the Manufacture Stock Entry for FB and consumes DCR child rows at lines 722-810.
- When the DCR comes from Console through the bridge, `make_stock_entry_final_batch` uses `reference_id` and `bridge_mix_barcode` instead of auto-generating the output barcode at lines 788-799.

Legacy DCR therefore remains the legacy-side contract for mixing receipts. Console does not bypass it for the legacy leg; it feeds it with mapped fields.

## Console Rewrite Behavior

Console ports the old DCR interaction into explicit process templates and React process screens.

Template evidence:

- MBM template is seeded as `MASTER_BATCH_MIXING`, uses `MasterBatchMixingEntry`, has `sync_strategy = "Both (Parallel)"`, and outputs Work Order, Job Card, and Stock Entry at `apps/shree_polymer_console/shree_polymer_console/shree_polymer_console/console_template_seeder.py` lines 16-29.
- MBM Ops actions create Work Order, fetch/update Job Card, and create an Ops Stock Entry only when `target_system == 'Ops'` at lines 54-132.
- MBM legacy action is conditional on `target_system == 'Legacy'` and carries `process_type = MASTER_BATCH_MIXING` plus `reference_id` at lines 134-143.
- FBM template mirrors MBM, uses `FinalBatchMixingEntry`, has `sync_strategy = "Both (Parallel)"`, and targets Compound Inspection in Ops for non-Master-Batch output at lines 162-199.
- FBM Ops and Legacy actions mirror MBM, with `process_type = FINAL_BATCH_MIXING` at lines 200-289.

Frontend evidence:

- MBM payload generation creates `reference_id`, metadata, warehouse config, Work Order data, Job Card data, stock entry consumption rows, finished item row, and top-level `mix_barcode` at `apps/shree_polymer_console/dash/src/components/processes/MasterBatchMixingEntry.tsx` lines 415-509.
- MBM output barcode behavior reuses the scanned input mix barcode if no generated barcode exists, before initializing the submission, at lines 639-655.
- MBM live submission initializes target logs, executes each target, and computes `Success`, `Partial Success`, or `Failed` from per-target results at lines 658-701.
- FBM payload generation has the same shape as MBM at `apps/shree_polymer_console/dash/src/components/processes/FinalBatchMixingEntry.tsx` lines 415-507.
- FBM generates a compound mix barcode through `generateCompoundMixBarcode` before payload creation when no barcode exists at lines 651-670.
- FBM live submission uses the same initialize/execute/result aggregation pattern at lines 673-707.

Important parity distinction:

- MBM output should reuse the scanned input mix barcode when appropriate.
- FBM output uses `generateCompoundMixBarcode`; that generated barcode is the Compound output barcode.

## MBM Parity Trace

1. Operator completes the MBM React flow.
2. `MasterBatchMixingEntry.tsx` builds a payload with:
   - `metadata.process_code = MASTER_BATCH_MIXING`
   - `metadata.produced_item`
   - `config.operation`
   - `work_order_data`
   - `job_card_data`
   - `stock_entry_data.consumption_items`
   - `stock_entry_data.items`
   - top-level `mix_barcode`
3. `initialize_submission` builds the transaction payload and routes `MASTER_BATCH_MIXING` to `create_local_master_batch_mixing` at `apps/shree_polymer_console/shree_polymer_console/shree_polymer_console/api.py` lines 1084-1118.
4. `create_local_master_batch_mixing` writes `Console Master Batch Mixing` with item, quantity, warehouse, workstation, operator, process code, payload snapshot, and normalized `consumption_items` at lines 2377-2413.
5. Console creates one pending `Console Transaction Log` for Legacy and one for Ops when the template is `Both (Parallel)` at lines 1145-1155 and 1215-1249.
6. Legacy Bridge maps the same payload to `Delivery Challan Receipt`.
7. Ops executes the generic transaction sequence through `TransactionEngine`.

Expected MBM outputs:

- `Console Master Batch Mixing`
- `Console Transaction Log` for Legacy
- `Console Transaction Log` for Ops
- Legacy `Delivery Challan Receipt` with `inward_material_type = Master Batch`
- Legacy-side Work Order / Job Card / Stock Entry as driven by DCR
- Ops Work Order / Job Card / Stock Entry
- Legacy Bridge Log
- MES Transaction Log
- Payload snapshot and response payloads for traceability

## FBM Parity Trace

1. Operator completes the FBM React flow after selecting/scanning the required Master Batch and raw/material inputs.
2. `FinalBatchMixingEntry.tsx` ensures a Compound mix barcode exists by calling `generateCompoundMixBarcode` before submission at lines 651-670.
3. The payload carries:
   - `metadata.process_code = FINAL_BATCH_MIXING`
   - Compound produced item
   - scanned consumption rows
   - finished Compound output row
   - top-level generated `mix_barcode`
4. `initialize_submission` routes `FINAL_BATCH_MIXING` to `create_local_final_batch_mixing` at `api.py` lines 1116-1118.
5. `create_local_final_batch_mixing` writes `Console Final Batch Mixing` with the same local audit shape as MBM and `process_code = FINAL_BATCH_MIXING` at lines 2416-2452.
6. Legacy mapping converts the operation to `inward_material_type = Compound`.
7. Legacy DCR's `validate_final_batches` and FB-specific Work Order / Stock Entry path handle Compound behavior.
8. Ops posts the generic Work Order, Job Card, and Stock Entry through the same transaction engine path as MBM.

Expected FBM outputs:

- `Console Final Batch Mixing`
- `Console Transaction Log` for Legacy
- `Console Transaction Log` for Ops
- Legacy `Delivery Challan Receipt` with `inward_material_type = Compound`
- Legacy Work Order / Job Card / Manufacture Stock Entry from the DCR FB path
- Ops Work Order / Job Card / Stock Entry
- Legacy Bridge Log
- MES Transaction Log
- Generated Compound mix barcode recorded in payload/response evidence

## Legacy Posting Trace

Console-side mapping is in `apps/shree_polymer_console/shree_polymer_console/shree_polymer_console/console_mapping_seeder.py`.

- `seed_mixing_process_mapping` maps both MBM and FBM to `Delivery Challan Receipt` at lines 110-166.
- Header fields map `reference_id`, `dc_no`, posting date, operation, produced item, `mix_barcode` to `bridge_mix_barcode`, warehouses, and `inward_material_type` at lines 120-135.
- `inward_material_type` is value-mapped from operation: `Master Batch Mixing -> Master Batch`, `Final Batch Mixing -> Compound` at lines 113-132.
- Child rows map `stock_entry_data.consumption_items` to `dc_items`, including item, qty, batch, SPP batch, scanned mix barcode, DC number, operation, and item to manufacture at lines 137-161.

Legacy Bridge execution is in `apps/shree_polymer_legacy_bridge/shree_polymer_legacy_bridge/sync_api.py`.

- `sync_process_transaction` creates `Legacy Bridge Log` with `reference_id`, process type, raw payload, and `Pending` status at lines 259-275.
- It checks idempotency before creating another legacy document at lines 281-297.
- It creates the target legacy document from `Legacy Sync Mapping`, injects `reference_id`, flattens payload context, and prepares child-table data at lines 299-354.
- `find_existing_record` defaults mixing idempotency to `Delivery Challan Receipt` by `reference_id` at lines 666-674.
- `populate_dc_receipt_fields` can fill missing DCR child fields by calling legacy `validate_barcode`, which preserves behavior that the legacy UI previously performed before submit at lines 783-813.

Drift watch:

- `apps/shree_polymer_legacy_bridge/shree_polymer_legacy_bridge/legacy_bridge_seeder.py` also seeds mixing mappings. It maps `metadata.item_group` to `inward_material_type` and has a child transform for `scan_barcode` fallback at lines 62-116.
- The Console seeder and Legacy Bridge seeder should be kept aligned. If both are used in different environments, this is a known drift risk.

## Ops Posting Trace

Ops entry point is `apps/shree_polymer_ops/shree_polymer_ops/api.py`.

- `process_transaction` accepts the payload, parses JSON, extracts `metadata.process_code`, and delegates to `TransactionEngine` at lines 47-78.
- Business exceptions are returned as structured failure payloads instead of unparseable non-200 responses at lines 79-101.
- `TransactionEngine` stores payload, context, sequence, metadata, and `reference_id`, then marks `target_system = "Ops"` at lines 104-132.
- `execute` checks idempotency, creates `MES Transaction Log`, runs sequence steps with savepoints, commits on success, and fetches impacted balances after commit at lines 141-229.
- Stock Entry documents are logged before save at lines 800-808.
- `create_doc` normalizes Stock Entry batch identifiers before document insert at lines 1370-1387.
- `_ensure_batch_exists` can create missing Batch records when required by ERPNext validation at lines 1399-1414.
- `retry_transaction` reloads the stored MES payload and reruns the engine for failed logs at lines 1548-1571.

Expected Ops result payload must include at least:

- `status`
- `log_name`
- `results`
- `reference_id` where available
- `impacted_balances` when stock posting succeeded
- `impacted_bundles` when serial/batch bundles are affected
- `warnings` or `message` when business validation fails

## Success Response Handling

Console handles submission in two phases:

1. `initialize_submission` builds target-specific payloads and creates pending `Console Transaction Log` records.
2. The Dash calls `execute_submission_step` once per target log and updates the success modal target by target.

Backend details:

- Legacy target receives form data shaped as `payload`, `process_type`, and `reference_id`; Ops receives `payload` only at `api.py` lines 1221-1229.
- `execute_submission_step` rebuilds request parameters from stored log payloads during retry at lines 1303-1317.
- It posts to the target Frappe method, normalizes status from the JSON response, and stores response payload, remote log, remote reference doctype/name, mix barcode, FG batch, barcode image, and detailed error at lines 1321-1393.
- On success, it updates local stock cache from `impacted_balances` at lines 1401-1405.
- `log_transaction` is the local audit entry creator and stores request/response/error fields at lines 3736-3765.
- `retry_transaction` preserves target-specific request shape and writes response fields back to the same `Console Transaction Log` at lines 3888-4017.

Frontend details:

- MBM and FBM set the modal to `Processing`, mark each target as `Pending` then `Processing`, and replace each target result with the returned status.
- Final UI status is:
  - `Success` when all target legs succeed.
  - `Partial Success` when at least one target leg succeeds.
  - `Failed` when no target leg succeeds.

## Error and Failure Handling

Errors that must be captured in parity testing:

| Failure | Expected capture |
| --- | --- |
| Missing batch/barcode | Dash error or failed target response plus Console Transaction Log `detailed_error` |
| Insufficient stock | Ops MES failure response, `MES Transaction Log`, Console Transaction Log response |
| Duplicate `reference_id` | Idempotent Legacy/Ops response, no duplicate DCR/Stock Entry |
| Duplicate serial/batch bundle | Ops structured failed response and MES error details |
| Legacy success, Ops failure | Console final status `Partial Success`, one success log and one failed log |
| Ops success, Legacy failure | Console final status `Partial Success`, Ops stock evidence plus failed Legacy Bridge evidence |
| Both target failures | Console final status `Failed`, both logs failed |
| Retry after failure | Same `reference_id`, same stored request payload, updated response fields |

The serial/batch bundle failure currently seen in staging belongs in the negative case evidence. The test should capture the exact request payload, Ops MES log, traceback/error text, and whether Legacy succeeded for the same `reference_id`.

## Real-Data Test Evidence Plan

Do not run stock-consuming tests as part of documentation generation. When explicitly approved, run the real-data test against staging only.

Recommended evidence folder per run:

```text
spp-porting-cockpit/03-parity-dossiers/evidence/
  YYYY-MM-DD-reference-id/
    input-payload.json
    console-local-document.json
    console-transaction-logs.json
    legacy-bridge-request-response.json
    legacy-dcr.json
    legacy-linked-documents.json
    ops-request-response.json
    ops-mes-transaction-log.json
    ops-linked-documents.json
    stock-movement-evidence.json
    failure-traceback.txt
    summary.md
```

Positive test cases:

- MBM valid raw/material scan creates Master Batch output in both Legacy and Ops.
- FBM valid Master Batch barcode plus raw/material scan creates Compound output in both Legacy and Ops.
- Both legs produce success logs with the same `reference_id`.
- Output barcode expectations hold: MBM reuses scanned input barcode where applicable; FBM uses generated Compound barcode.

Negative test cases:

- Missing barcode/batch.
- Insufficient stock.
- Duplicate `reference_id`.
- Duplicate serial/batch bundle.
- Bridge failure with Ops success.
- Ops failure with Legacy success.
- Manual retry from stored log.

Minimum fields to capture:

- `reference_id`
- process code
- operator/user
- source and target warehouses
- produced item and quantity
- all scanned consumption rows
- output mix barcode
- Console local document name
- DCR name
- Ops Stock Entry name
- Work Order and Job Card names where created
- Legacy Bridge Log name/status/response
- MES Transaction Log name/status/response
- Console Transaction Log names/statuses/request/response
- stock balance deltas or impacted balances

Acceptance rule:

The test is passed only when the same `reference_id` can trace every created document and log across Console, Legacy Bridge, legacy ERPNext, and Ops.

## Known Drift and Risks

- There are two mapping seeders for mixing: Console mapping seeder and Legacy Bridge seeder. They should not diverge in active environments.
- MBM and FBM frontend components are very similar; a fix in one can be missed in the other.
- FBM has stricter legacy behavior because `validate_final_batches` can reject invalid batch/final-batch grouping.
- Legacy DCR still performs important side effects; replacing it requires a separate parity exercise for Work Order, Job Card, Stock Entry, Delivery Note status, and downstream Compound Inspection dependencies.
- Ops must keep the generic `TransactionEngine` pattern. Process-specific Ops branching for MBM/FBM would violate the porting methodology.
- Real-data tests consume or move stock. They must be run only against the agreed staging setup and must leave JSON/Markdown evidence.

