# 03 — Console backend — `api.py` orchestration

**File:** `apps/shree_polymer_console/shree_polymer_console/shree_polymer_console/api.py`
**Patterns:** Identical to `Master Batch Mixing` — see [`../master-batch-mixing/03-console-backend.md`](../master-batch-mixing/03-console-backend.md) for the authoritative pattern reference. This file documents MPE-specific deviations only.

MPE in Console follows the same two-step submit pattern as all other Wave 1/2
doctypes:
1. `initialize_submission` — creates local audit record + per-target Transaction Logs
2. `execute_submission_step` — fires Legacy Bridge + Ops in parallel, handles callbacks

## MPE-specific routing in `initialize_submission`

Add to `api.py:958` dispatch chain (currently handles MASTER_BATCH_MIXING,
FINAL_BATCH_MIXING, SHEETING_PROCESS, CUT_BIT_TRANSFER, BLANKING_DC_ENTRY):

```python
elif process_code == "MOULDING_PRODUCTION_ENTRY":
    create_local_moulding_production_entry(prelim_payload, reference_id)
```

## `create_local_moulding_production_entry(payload, reference_id)`

Mirrors the MPE payload locally for audit. Key fields to capture:

```python
def create_local_moulding_production_entry(payload, reference_id):
    ctx = payload.get("context", {})
    posting_date, posting_time = _backdate_fields(ctx)

    return _safe_local_create(
        "Console Moulding Production Entry",
        {
            "scan_lot_number": _pick(ctx, "stock_entry_data.scan_lot_number",
                                     "metadata.scan_lot_number", "lot_number"),
            "job_card": _pick(ctx, "job_card_data.job_card", "job_card",
                               "work_order_data.job_card"),
            "moulding_date": _pick(ctx, "stock_entry_data.posting_date",
                                    "moulding_date", "posting_date"),
            "weight": flt(_pick(ctx, "stock_entry_data.fg_qty", "weight",
                                 "work_order_data.qty_to_manufacture")),
            "compound": _pick(ctx, "metadata.compound", "compound",
                              "stock_entry_data.compound"),
            "number_of_lifts": _pick(ctx, "metadata.number_of_lifts",
                                      "number_of_lifts"),
            "no_of_running_cavities": _pick(ctx, "metadata.no_of_running_cavities",
                                            "no_of_running_cavities"),
            "curing_time": _pick(ctx, "metadata.curing_time", "curing_time"),
            "operator": _pick(ctx, "job_card_data.employee_code", "operator"),
            "batch_details": json.dumps(_pick(ctx, "metadata.batch_details",
                                              "stock_entry_data.batch_details", [])),
            "is_injection_moulding": _pick(ctx, "metadata.is_injection_moulding",
                                            "is_injection_moulding", 0),
            "purged_compound": flt(_pick(ctx, "metadata.purged_compound",
                                          "purged_compound", 0)),
            "compound_leakage": flt(_pick(ctx, "metadata.compound_leakage",
                                          "compound_leakage", 0)),
            "balance_bins": _pick(ctx, "metadata.balance_bins", "balance_bins", []),
            "reference_id": reference_id,
            "process_code": "MOULDING_PRODUCTION_ENTRY",
            "payload_snapshot": json.dumps(payload, indent=1, default=str),
        },
        reference_id,
        "create_local_moulding_production_entry",
    )
```

## `apply_bridge_result` — same 5-step pattern as MB Mixing

MPE uses the identical 5-step atomic dance on `Console Moulding Production Entry`:

```python
# Step 1: Atomic per-field write for THIS leg only
frappe.db.set_value(self.doctype, self.name, {
    f'{field_prefix}_sync_status': leg_status,
    f'{field_prefix}_reference': remote_name,
    f'{field_prefix}_error_message': error,
}, update_modified=False)

# Step 2: Re-read BOTH legs from DB (atomic snapshot)
# Step 3: Aggregate sync_status
# Step 4: Self-heal
# Step 5: Auto-submit on full success
```

See [`../master-batch-mixing/03-console-backend.md`](../master-batch-mixing/03-console-backend.md)
for the full 5-step explanation. MPE inherits the same pattern.

## Console doctype fields — proposed schema

```json
{
  "name": "Console Moulding Production Entry",
  "autoname": "CMPE-.YYYY.-.#####",
  "is_submittable": 1,
  "fields": [
    {"fieldname": "scan_lot_number", "fieldtype": "Data", "label": "Scan Lot Number", "options": "Barcode"},
    {"fieldname": "job_card", "fieldtype": "Link", "options": "Job Card", "label": "Job Card"},
    {"fieldname": "moulding_date", "fieldtype": "Date", "label": "Posting Date"},
    {"fieldname": "weight", "fieldtype": "Float", "label": "Produced Weight (Kg)", "precision": "3"},
    {"fieldname": "compound", "fieldtype": "Link", "options": "Item", "label": "Compound"},
    {"fieldname": "number_of_lifts", "fieldtype": "Int", "label": "Number of Lifts"},
    {"fieldname": "no_of_running_cavities", "fieldtype": "Int", "label": "Running Cavities"},
    {"fieldname": "curing_time", "fieldtype": "Int", "label": "Curing Time"},
    {"fieldname": "operator", "fieldtype": "Link", "options": "Employee", "label": "Operator"},
    {"fieldname": "operator_name", "fieldtype": "Data", "label": "Operator Name", "read_only": 1},
    {"fieldname": "batch_details", "fieldtype": "Long Text", "label": "Batch Details (JSON)", "hidden": 1},
    {"fieldname": "line_rejection_qty", "fieldtype": "Float", "label": "Line Rejection Qty (Kg)", "read_only": 1},
    {"fieldname": "is_injection_moulding", "fieldtype": "Check", "label": "Is Injection Moulding", "hidden": 1},
    {"fieldname": "purged_compound", "fieldtype": "Float", "label": "Purged Compound (Kg)", "precision": "3"},
    {"fieldname": "compound_leakage", "fieldtype": "Float", "label": "Compound Leakage (Kg)", "precision": "3"},
    {"fieldname": "weight_without_shell", "fieldtype": "Float", "label": "Weight Without Shell", "read_only": 1},
    {"fieldname": "stock_entry_reference", "fieldtype": "Data", "label": "Stock Entry Reference", "read_only": 1},
    {"fieldname": "batch_no", "fieldtype": "Link", "options": "Batch", "label": "Batch No", "read_only": 1},
    {"fieldname": "spp_batch_number", "fieldtype": "Data", "label": "SPP Batch Number", "read_only": 1},
    {"fieldname": "mould_reference", "fieldtype": "Data", "label": "Mould Reference", "read_only": 1},
    {"fieldname": "balance_bins", "fieldtype": "Table", "options": "Console Moulding Balance Bin", "label": "Balance Bins"},
    {"fieldname": "supervisor_id", "fieldtype": "Link", "options": "Employee", "label": "Supervisor ID"},
    {"fieldname": "supervisor_name", "fieldtype": "Data", "label": "Supervisor Name", "read_only": 1},
    {"fieldname": "special_instructions", "fieldtype": "Small Text", "label": "Special Instructions"},
    {"fieldname": "amended_from", "fieldtype": "Link", "options": "Console Moulding Production Entry", "label": "Amended From", "read_only": 1, "no_copy": 1},
    {"fieldname": "reference_id", "fieldtype": "Data", "unique": 1, "label": "Reference ID"},
    {"fieldname": "process_code", "fieldtype": "Data", "label": "Process Code", "read_only": 1},
    {"fieldname": "sync_status", "fieldtype": "Select", "options": "Pending\nPartial\nSuccess\nFailed", "label": "Sync Status"},
    {"fieldname": "legacy_sync_status", "fieldtype": "Data", "label": "Legacy Sync Status"},
    {"fieldname": "ops_sync_status", "fieldtype": "Data", "label": "Ops Sync Status"},
    {"fieldname": "legacy_reference", "fieldtype": "Data", "label": "Legacy Reference"},
    {"fieldname": "ops_reference", "fieldtype": "Data", "label": "Ops Reference"},
    {"fieldname": "error_log_summary", "fieldtype": "Data", "label": "Error Log Summary"},
    {"fieldname": "submitted_by", "fieldtype": "Link", "options": "User", "label": "Submitted By"},
    {"fieldname": "payload_snapshot", "fieldtype": "Long Text", "hidden": 1, "label": "Payload Snapshot"},
    {"fieldname": "target_system", "fieldtype": "Data", "label": "Target System"}
  ],
  "permissions": [{"role": "System Manager", "create": 1, "submit": 1, "read": 1, "write": 1}]
}
```

## `Console Moulding Balance Bin` child table

```json
{
  "name": "Console Moulding Balance Bin",
  "fields": [
    {"fieldname": "bin_code", "fieldtype": "Link", "options": "Asset", "label": "Bin Code"},
    {"fieldname": "bin_name", "fieldtype": "Data", "label": "Bin Name", "read_only": 1},
    {"fieldname": "gross_weight", "fieldtype": "Float", "label": "Gross Weight"},
    {"fieldname": "bin_weight", "fieldtype": "Float", "label": "Bin Weight (Tare)"},
    {"fieldname": "net_weight", "fieldtype": "Float", "label": "Net Weight"},
    {"fieldname": "balance_qty", "fieldtype": "Float", "label": "Balance Qty"}
  ]
}
```

## Sync strategy

MPE uses `sync_strategy = "Both (Parallel)"` on the `Console Process Template`,
same as MB Mixing. Both Legacy and Ops fire in parallel.

**Note:** Unlike Mixing, MPE's Legacy leg doesn't create a separate Stock Entry on
Legacy — the Legacy `Moulding Production Entry` **is** the doctype that creates
and submits its own Manufacturing Stock Entry in `on_submit`. The Legacy Bridge
sync here is primarily for audit trail + idempotency. The Manufacturing Stock
Entry creation happens on the **Legacy** bench (in `make_stock_entry()`), not
via the Bridge.

The Ops leg creates the Manufacturing Stock Entry on the Ops bench via the MES
Transaction Engine (same pattern as other processes). Both legs must succeed for
`sync_status = Success`.

## What Hermes workers can safely change here

| Change | Risk |
|---|---|
| Add new `_pick` fallback path for a new field | Low — only adds tolerance |
| Add new child table rows | Low — additive |
| Modify `apply_bridge_result` | **High** — same 5-step race safety as MB Mixing |
| Change `sync_strategy` to single-target | Medium — changes dual-leg behavior; coordinate with ops team |
| Touch `_safe_local_create` | **High** — affects every Wave 1/2 doctype |