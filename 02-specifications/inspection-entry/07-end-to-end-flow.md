# 07 — End-to-end flow (one inspector submission, traced)

This file is the **single canonical narrative** for the 3 main inspection
paths. If you want to understand what actually happens when an inspector
submits, read this file. The other layer files have the details; this one
has the choreography.

## Path A — Line / Patrol / Lot Inspection with rejection

```
┌──────────────┐  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐
│ Dash (React) │  │ Console api.py  │  │ Bridge       │  │ Legacy IE    │
│  Tablet/iPad  │  │                 │  │ sync_api.py  │  │ on spp15     │
└──────┬───────┘  └────────┬────────┘  └──────┬───────┘  └──────┬───────┘
       │                   │                   │                 │
       │ initialize_submission                 │                 │
       ├──────────────────►│                   │                 │
       │                   │ create_local_inspection             │
       │                   │ _safe_local_create                  │
       │                   │                                     │
       │  {target_logs, reference_id} ◄───────┤                 │
       │                                                             │
       │  execute_submission_step(legacy_log)                       │
       ├─────────────────────────────────────►│                   │
       │                   │                   │ sync_process_transaction
       │                   │                   │  ├── idempotency check
       │                   │                   │  ├── get Legacy Sync Mapping
       │                   │                   │  ├── apply field_mappings
       │                   │                   │  ├── insert IE Draft
       │                   │                   │  └── submit IE ──────────────────►│
       │                   │                   │                  │ on_submit fires:
       │                   │                   │                  │  Branch A: make_stock_entry
       │                   │                   │                  │  → rejection Material Transfer SE (Draft)
       │                   │                   │                  │  → stock_entry_reference stored on IE
       │                   │                   │                  │  → exe_insp query (Line+Lot, NOT Patrol)
       │                   │                   │                  │  → if len(exe_insp) >= 2:
       │                   │                   │                  │       submit_inspection_stock_entry_immediately
       │                   │                   │                  │       (cascade batch from MPE to all IE SEs)
       │                   │ ◄────────────────────────────────────│
       │                   │ update Console Transaction Log {status, remote_name}
       │                   │ update_local_domain_record → apply_bridge_result (5-step)
       │ ◄── {status: Success, result: {reference_name, stock_entry_reference}}
       │                                                             │
       │  (Later — when MPE is submitted for this lot)               │
       │                                                             ▼
       │                                    MPE.on_submit fires:
       │                                    submit_inspection_stock_entries_from_moulding
       │                                             │
       │                                             ▼
       │                                    IE.submit_inspection_stock_entry_immediately
       │                                             │
       │                                    ┌────────┴────────┐
       │                                    │ Gets MPE's produced batch
       │                                    │ Updates batch_no on:
       │                                    │   - Stock Entry Detail (all Line/Lot/Patrol SEs)
       │                                    │   - Inspection Entry.batch_no
       │                                    │ Submits each draft Stock Entry
       │                                    └──────────────────────────────────────┘
```

### Narrative trace — Line Inspection with rejection

**Setup:** Inspector Priya (employee `HR-EMP-00312`) is at the moulding
machine. She scans her badge, selects "Line Inspection", scans lot `M-2604123`.
The system resolves the Job Card, MPE status (already submitted), and mould
specification piece weight (`one_no_qty_equal_kgs = 0.042`). She enters
inspected qty `500` nos, adds 3 defect rows (total rejected `18` nos).
Total rejected kg = `18 * 0.042 = 0.756 kg`.

**T+0:00** — Priya hits submit. Dash calls `initialize_submission`.

**T+0:01** — Console `create_local_inspection` inserts `Console Inspection`
record (Draft, Pending). `_safe_local_create` with `flags.from_local_cache=True`
skips strict validate.

**T+0:02** — Console Transaction Log (Legacy leg) created with status=Pending.

**T+0:03** — `execute_submission_step` fires Legacy Bridge call:
`POST {bridge_url}/api/method/sync_process_transaction`
payload includes `inspection_type: "Line Inspection"`, `lot_no: "M-2604123"`,
`total_rejected_qty: 18`, `total_rejected_qty_kg: 0.756`, child rows.

**T+0:04** — Bridge `sync_process_transaction`:
- Idempotency check: no existing IE with this `reference_id`, proceed
- Loads `Legacy Sync Mapping "INSPECTION_ENTRY"`
- Applies field mappings → builds legacy IE doc
- `legacy_doc.insert()` → IE created Draft, named `INSP-.02341`
- `legacy_doc.submit()` → IE submitted

**T+0:05** — IE `on_submit` fires (Branch A):
- `make_stock_entry(self)` creates draft Material Transfer SE:
  - `from_warehouse`: Unit-2 warehouse
  - `to_warehouse`: Rejection warehouse
  - `item_code`: product ref
  - `transfer_qty`: 0.756 kg
  - `source_ref_document`: "Inspection Entry", `source_ref_id`: `INSP-.02341`
- `stock_entry_reference` stored on IE = `MAT-STE-2026-01342` (Draft)
- `exe_insp` query: looks for Line + Lot Inspections for lot `M-2604123`
  - **NOTE:** Patrol is NOT in this trigger query (see Drift Finding #1)
- At this point, Lot Inspection for `M-2604123` is already submitted.
  So `len(exe_insp) == 2` → `submit_inspection_stock_entry_immediately(self)` fires

**T+0:06** — `submit_inspection_stock_entry_immediately`:
- Finds MPE for lot `M-2604123` (already submitted)
- Gets `target_batch` from MPE's Stock Entry finished item row
- Finds ALL inspection entries (Line + Lot + Patrol) for the lot
- For the Line IE's SE: updates `batch_no` in `Stock Entry Detail`
  (where `source_ref_document = 'Inspection Entry' AND source_ref_id = 'INSP-.02341'`)
- Updates `Inspection Entry.batch_no = target_batch`
- Submits the draft Stock Entry → `MAT-STE-2026-01342` now submitted
- Same for Lot IE's rejection SE

**T+0:07** — Bridge returns: `{status: "Success", reference_name: "INSP-.02341"}`

**T+0:08** — Console callback `apply_bridge_result`:
- Step 1: `legacy_sync_status = Synced`
- Step 2: re-read both legs → Legacy=Synced, Ops=Pending (no Ops leg)
- Step 3: `sync_status = Partial` (but this is Legacy-only routing, so effectively Success)
- Step 5: auto-submit Console Inspection → `docstatus = 1`

**Final state:**
- Console `Console Inspection`: submitted, `sync_status = Success`, `legacy_reference = INSP-.02341`
- Legacy `Inspection Entry INSP-.02341`: submitted, `batch_no = MPE-batch`, `stock_entry_reference = MAT-STE-2026-01342`
- Legacy `Stock Entry MAT-STE-2026-01342`: submitted, batch set, rejection material in Rejection warehouse

## Path B — Incoming Inspection with rejection + Deflashing Receipt trigger

```
Inspector scans lot (must have Deflashing Receipt Entry)
         │
         ▼
IE submitted → on_submit Branch B fires
         │
         ├─► make_inc_stock_entry → Material Transfer SE (nos, Draft)
         │
         └─► submit_deflash_receipt_entry
                   │
                   ▼
             Deflashing Receipt Entry.manual_on_submit fires
                   │
                   ▼
             Deflashing Receipt's Stock Entry submitted
```

**Narrative trace — Incoming Inspection:**

**T+0:00** — Inspector scans lot `D-2605101`. System finds Deflashing Receipt Entry
for this lot. Inspector enters inspected qty `200` nos, adds 1 defect row
(rejected `7` nos). No kg conversion needed.

**T+0:01** — Submit. Console → Bridge → Legacy IE submitted.

**T+0:02** — `on_submit` Branch B fires:
- `make_inc_stock_entry(self)` creates draft Material Transfer SE:
  - `stock_uom: "Nos"`, `qty: 7`, `spp_batch_number` carried
  - `source_ref_document: "Inspection Entry"`
- `submit_deflash_receipt_entry(self)`:
  - Finds `Deflashing Receipt Entry` for lot `D-2605101`
  - Calls `mould__prod.run_method('manual_on_submit')`
  - Deflashing Receipt's linked Stock Entry submitted

## Path C — Final Visual Inspection with rejection

```
Inspector scans lot (must exist in LRT)
         │
         ▼
IE submitted → on_submit Branch C fires
         │
         ├─► make_vs_pdir_stock_entry → Material Transfer SE (submitted immediately)
         │
         ▼
submit__vs_pdir()
         │
         ├─► make_vs_pdir_stock_entry → rejection SE to pdir_visual_t__warehouse
         │
         ├─► LRT.make_wo_stock_entry → Work Order + Job Card created
         │
         ├─► SE submitted, posting_date updated
         │
         └─► LRT qty_after_rejection_nos updated
```

**Narrative trace — Final Visual with rejection:**

**T+0:00** — Inspector scans lot `LRT-2605151`. System finds LRT entry
(docstatus=1). BOM sequence checked — Final Visual is not the first operation.

**T+0:01** — Inspector enters `vs_pdir_qty = 180` (available qty),
adds defect rows (total rejected `12` nos). `vs_pdir_qty_after_rejection`
precomputed in `validate()` as `180 - 12 = 168`.

**T+0:02** — Submit. Console → Bridge → Legacy IE submitted.

**T+0:03** — `on_submit` Branch C fires:
- `submit__vs_pdir()`:
  - `make_vs_pdir_stock_entry(self)` creates Material Transfer SE:
    - `from_warehouse`: Unit-2 or LRT's warehouse
    - `to_warehouse`: `pdir_visual_t__warehouse` (PDIR Visual Rejection warehouse)
    - `transfer_qty: 12` (rejected nos)
    - Immediately submitted (unlike Branch A's draft SE)
  - Finds LRT for lot → calls `lrt.make_wo_stock_entry()`
  - Work Order + Job Card created (Final Visual operation, qty = `vs_pdir_qty_after_rejection = 168`)
  - SE submitted, posting_date set from IE
  - LRT `qty_after_rejection_nos` updated to `168`
  - LRT reloaded

**Final state:**
- Legacy `Inspection Entry`: submitted, `vs_pdir_stock_entry_ref` set
- Legacy `Stock Entry`: submitted, rejection material in PDIR warehouse
- Legacy `Work Order`: submitted, for 168 nos
- Legacy `Job Card`: submitted, time log completed
- LRT: `qty_after_rejection_nos = 168`

## What can go wrong, and at what point

| Failure mode | Where it surfaces | What state is left |
|---|---|---|
| Lot not found in Job Card | `validate_lot_number` returns Failed | No IE submitted |
| Inspector barcode invalid | `validate_inspector_barcode` returns Failed | No IE submitted |
| MPE not found for Lot Inspection | `validate_lot_number` throws | No IE submitted |
| Duplicate (same lot + type) | `validate()` throws | No IE submitted |
| Rejection SE creation fails | `make_stock_entry` returns Failed → `rollback_entries` | IE docstatus=0, stock_entry_reference cleared |
| MPE batch cascade fails | `submit_inspection_stock_entry_immediately` throws | IE submitted but draft SE left unsubmitted |
| Final Visual: stock not available | `submit__vs_pdir_no_rejection` throws | IE docstatus=0 |
| Final Visual: no LRT found | `submit_vs_entry__only` fires | Work Order + SE created via alternate path |
| Deflashing Receipt not found | `submit_deflash_receipt_entry` throws | IE submitted, Incoming SE created, but deflashing trigger missed |

## Recovery procedures

### Line/Patrol/Lot IE submitted but draft SE left unsubmitted (MPE not yet submitted)

1. Operator waits for MPE to be submitted (MPE is the batch source)
2. MPE `on_submit` fires `submit_inspection_stock_entries_from_moulding`
3. This path (documented in `../moulding-production-entry/`) updates batch and submits

### IE submitted but no MPE exists (Lot Inspection validation required MPE)

If MPE was not submitted before Lot Inspection: Lot Inspection validation would
have thrown `"There is no <b>Moulding Production Entry</b> found..."`. So this
case cannot happen for Lot Inspection. For Line/Patrol, MPE check is optional.

### Incoming IE submitted but Deflashing Receipt not found

Re-submit Incoming IE for the lot after ensuring Deflashing Receipt exists.

### Final Visual: SE submitted but LRT not found

Run `rollback__vs_entry__only` or manually delete the Work Order + SE.
Re-submit IE with correct lot that has LRT entry.