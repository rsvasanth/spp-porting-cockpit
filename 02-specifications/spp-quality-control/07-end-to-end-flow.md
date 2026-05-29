# 07 — End-to-end flow

## Happy path: submission

```
Inspector scans badge
  └─ Console resolves Employee via Console Employee.barcode_text

Operator scans badge
  └─ Console resolves Employee

Lot scan
  └─ Console queries Console Work Plan Item cache
      └─ resolves item_code, workstation, mould_reference
      └─ queries Console Mould Specification → one_no_qty_equal_kgs

Template gate check
  └─ Console queries Console SPP QC Template for item_code
      ├─ MISSING → block modal with "Sync templates now" button
      │             └─ if sync resolves it → continue
      │             └─ if still missing → hard block
      └─ PRESENT → render parameter grid

Inspector enters reading values
  └─ Frontend color-codes in real time (presentational only)

Inspector clicks SUBMIT
  └─ Console controller validate():
      ├─ inspector != operator
      ├─ template re-resolved + fresh
      ├─ reading_status recomputed per row (server authoritative)
      ├─ total_rejected_qty_kg recomputed (Moulding only)
      ├─ totals reconcile (inspected = accepted + rejected)
      └─ template_sync_hash stamped

  └─ Console controller on_submit():
      ├─ generate reference_id (UUID v4)
      ├─ build_transaction_payload()
      ├─ initialize_submission() → returns target_logs for Ops + Legacy
      │
      ├─ execute_submission_step(Ops):
      │   ├─ Ops idempotency check on custom_reference_id
      │   ├─ create Stock Entry per inspection_type matrix
      │   ├─ return ops_se_name + status
      │   └─ apply_bridge_result → ops_sync_status = Success, stock_entry_reference set
      │
      └─ execute_submission_step(Legacy):
          ├─ Legacy Bridge creates Inspection Entry mirror
          ├─ return legacy_name + status
          └─ apply_bridge_result → legacy_sync_status = Success

  └─ docstatus = 1 (Submitted)
  └─ Console Transaction Log entries persisted for each leg
  └─ Frontend shows success toast, resets to idle state
```

## Failure paths: submission

| Failure point | System state | User experience |
|---|---|---|
| Template missing, sync fails | No record created | Modal blocks; supervisor escalation |
| validate() fails | No record created | Inline error; QI corrects |
| Ops leg fails | docstatus=1, ops_sync_status=Failed, no Legacy attempt | Banner: "Ops sync failed, retry from Transaction Log" |
| Ops leg times out after SE creation | Console retries on next submit; Ops idempotency returns same SE | No duplicate; eventual consistency |
| Legacy leg fails | docstatus=1, ops_sync_status=Success, legacy_sync_status=Failed | Banner: "Legacy mirror failed, retry from Transaction Log" |

## Happy path: cancellation

```
Supervisor opens submitted SPP Quality Control on Console
  └─ Clicks CANCEL

Console controller on_cancel():
  ├─ Stage 1 — Ops cancel
  │   └─ Bridge call cancel_stock_entry_from_qc(reference_id)
  │       ├─ Ops finds SE by custom_reference_id
  │       ├─ if docstatus=0 → delete; return ok
  │       ├─ if docstatus=1 → cancel; return ok or stock_consumed
  │       └─ Console updates ops_sync_status
  │
  │   ├─ If stock_consumed → HALT cascade
  │   │   ├─ local docstatus stays at 1
  │   │   ├─ Transaction Log: Ops cancel failed (stock_consumed)
  │   │   └─ Supervisor sees: "Stock already consumed downstream; cancellation blocked"
  │   │
  │   └─ If ok → proceed to Stage 2
  │
  ├─ Stage 2 — Legacy cancel
  │   └─ Bridge call cancel_inspection_entry_from_qc(legacy_name)
  │       ├─ Legacy cancels Inspection Entry → docstatus=2
  │       └─ Console updates legacy_sync_status
  │
  │   ├─ If Legacy fails → HALT cascade
  │   │   ├─ local docstatus stays at 1
  │   │   ├─ ops_sync_status reflects already-cancelled SE
  │   │   └─ Supervisor sees: "Ops cancelled but Legacy mirror failed; retry from Transaction Log"
  │   │
  │   └─ If ok → proceed to Stage 3
  │
  └─ Stage 3 — local flip
      └─ docstatus = 2
      └─ Console Transaction Log: cancellation_complete
      └─ Supervisor sees: "Cancellation successful"
```

The cascade is **strictly ordered** (Ops → Legacy → local) and **leg-level async** (each leg is a separate Bridge call with its own retry surface). Total wall-time is the sum of legs.

## Sequence summary

For a quick mental model — the cancellation contract is:

> *"If we can't cancel the Stock Entry on Ops, we don't pretend we did."*

Any partial-cancel state is observable in `Console Transaction Log` and is retryable. There is never a silent half-cancel.
