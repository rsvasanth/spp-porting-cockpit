# 04 — Bridge layer specification

## Reuse, don't reinvent

QC plugs into the existing Bridge orchestration pattern in `shree_polymer_console/shree_polymer_console/api.py`:

1. `build_transaction_payload(payload, target_system)` — builds the canonical sequence-based payload.
2. `initialize_submission(payload)` — creates `Pending` log entries, returns target list.
3. `execute_submission_step(log_name, target_info)` — executes one leg (Ops or Legacy).
4. `apply_bridge_result(reference_id, target, status, ...)` — applies the result back to the local doctype.

No new Bridge primitive is required for QC. The existing 4-stage pipeline is exactly what QC needs.

## Process Template configuration

QC requires one `Console Process Template` per inspection type:

| Process code | Inspection type | sync_strategy |
|---|---|---|
| `SPP_QC_LINE` | Line | Both (Parallel) |
| `SPP_QC_PATROL` | Patrol | Both (Parallel) |
| `SPP_QC_LOT` | Lot | Both (Parallel) |
| `SPP_QC_INCOMING` | Incoming | Both (Parallel) |
| `SPP_QC_FINAL_VISUAL` | Final Visual | Both (Parallel) |

Each Process Template carries warehouse parameters (resolved by `resolve_warehouse_config`):

- `source_warehouse`
- `target_warehouse` (used by Final Visual; null for others)
- `rejection_warehouse` (used by Line/Patrol/Lot/Incoming)

And an `is_quality_control_type` boolean flag (analogous to the existing `is_inspection_type` flag for Compound family).

## Dispatch registration

`initialize_submission` currently dispatches via a 14-arm `elif` chain on `process_code`. QC adds 5 new arms:

```python
elif process_code in ("SPP_QC_LINE", "SPP_QC_PATROL", "SPP_QC_LOT",
                      "SPP_QC_INCOMING", "SPP_QC_FINAL_VISUAL"):
    create_local_spp_quality_control(prelim_payload, reference_id)
```

(Once the planned Bridge dispatch registry refactor lands — see api.py review — these arms become 5 registrations against the registry. For now, the elif is the dispatch.)

## Idempotency

**Console side:** before invoking `initialize_submission`, the QC controller MUST query `Console Transaction Log` for an existing `Pending` or `Success` entry with the same `reference_id`. If present:
- `Success` → reuse the stored `stock_entry_reference`, do NOT re-submit.
- `Pending` → call `execute_submission_step` against the existing log_name; do NOT create a new log.

**Ops side:** the Ops endpoint receiving the Bridge payload MUST check for an existing Stock Entry whose `custom_reference_id` field equals the incoming `reference_id`. If found, return the existing SE name with `status=Success` rather than creating a duplicate.

This pattern matches what's already done for `MASTER_BATCH_MIXING` via `mix_barcode` dedup; QC formalizes it via `reference_id`.

## Retry semantics

Failed Bridge legs follow the existing `retry_pending_transactions` job. No QC-specific retry primitive.

A QC submission whose Ops leg succeeds but Legacy leg fails:
- Local docstatus = 1 (Submitted).
- `ops_sync_status` = Success.
- `legacy_sync_status` = Failed.
- Retry-eligible via the existing transaction log retry button.

## Cancellation cascade

Cancellation is a separate orchestration. The Bridge primitives are reused but the dispatch is:

1. Console calls a new `apply_cancel_step(log_name, target_info)` analogous to `execute_submission_step` but for cancellation.
2. Ops cancels the SE → returns `Success` or `Stock Consumed` error.
3. If Ops `Success` → Console calls Legacy cancel.
4. If Legacy `Success` → Console flips local docstatus to 2.
5. Any intermediate failure halts the cascade; local stays at docstatus=1; the failure is logged and supervisor-visible.

The cascade is async at the leg level (each leg is a separate Bridge call) but ordered (each leg waits for prior leg's result before proceeding). Total wall-time is the sum of legs, not parallel.

## Payload schema (Bridge to Ops)

```json
{
  "reference_id": "<uuid>",
  "metadata": {
    "process_code": "SPP_QC_LINE",
    "process_name": "SPP Quality Control",
    "reference_doctype": "Job Card",
    "reference_name": "<job_card_name>",
    "inspection_type": "Line"
  },
  "context": {
    "item_code": "...",
    "lot_no": "...",
    "inspector": "EMP-001",
    "operator": "EMP-002",
    "total_rejected_qty": 5,
    "total_rejected_qty_kg": 0.250,
    "template_sync_hash": "..."
  },
  "stock_entry_data": {
    "stock_entry_type": "Material Transfer",
    "docstatus_target": 0,
    "items": [
      {
        "item_code": "...",
        "qty": 0.250,
        "uom": "Kg",
        "s_warehouse": "<source>",
        "t_warehouse": "<rejection>",
        "batch_no": "..."
      }
    ]
  }
}
```

Exact shape negotiated with the Ops handler implementer.
