# 04 — Bridge layer — `shree_polymer_legacy_bridge`

**Pattern:** Same as `Master Batch Mixing` — see
[`../master-batch-mixing/04-bridge-layer.md`](../master-batch-mixing/04-bridge-layer.md)
for the authoritative reference. This file documents MPE-specific behavior only.

## MPE sync in `sync_process_transaction`

The Bridge receives MPE payloads under `process_type = "MOULDING_PRODUCTION_ENTRY"`.

**Key difference from Mixing:** MPE on Legacy is the **terminal doctype** that
creates and submits its own Stock Entry inside `on_submit`. The Bridge's role is:

1. Create the legacy `Moulding Production Entry` document (insert + submit)
2. The `on_submit` controller fires `make_stock_entry()` which creates + submits
   the Manufacturing Stock Entry
3. The Bridge receives `stock_entry_reference` in the response

## Mapping for MPE — `seed_moulding_production_entry_mapping`

```python
def seed_moulding_production_entry_mapping():
    """MOULDING_PRODUCTION_ENTRY → Legacy Moulding Production Entry"""

    field_mappings = [
        # ── Header fields ──────────────────────────────────────────────
        {"console_field": "reference_id",                         "legacy_field": "reference_id"},
        {"console_field": "stock_entry_data.scan_lot_number",       "legacy_field": "scan_lot_number"},
        {"console_field": "job_card_data.job_card",                 "legacy_field": "job_card"},
        {"console_field": "stock_entry_data.posting_date",          "legacy_field": "moulding_date"},
        {"console_field": "metadata.weight",                        "legacy_field": "weight"},
        {"console_field": "metadata.compound",                      "legacy_field": "compound"},
        {"console_field": "metadata.number_of_lifts",               "legacy_field": "number_of_lifts"},
        {"console_field": "metadata.no_of_running_cavities",        "legacy_field": "no_of_running_cavities"},
        {"console_field": "metadata.curing_time",                   "legacy_field": "curing_time"},
        {"console_field": "job_card_data.employee_code",            "legacy_field": "operator"},
        {"console_field": "metadata.batch_details",                 "legacy_field": "batch_details"},
        {"console_field": "metadata.is_injection_moulding",          "legacy_field": "is_injection_moulding"},
        {"console_field": "metadata.purged_compound",               "legacy_field": "purged_compound"},
        {"console_field": "metadata.compound_leakage",              "legacy_field": "compound_leakage"},
        {"console_field": "metadata.balance_bins",                  "legacy_field": "balance_bins"},
        {"console_field": "metadata.mould_reference",               "legacy_field": "mould_reference"},
        {"console_field": "metadata.special_instructions",          "legacy_field": "special_instructions"},
    ]

    _upsert_mapping("MOULDING_PRODUCTION_ENTRY", "Moulding Production Entry", field_mappings)
```

## Idempotency

```python
def find_existing_record(reference_id, payload=None, process_type=None):
    if process_type == "MOULDING_PRODUCTION_ENTRY":
        return {"doctype": "Moulding Production Entry",
                "name": frappe.db.get_value("Moulding Production Entry",
                           {"reference_id": reference_id}, "name")}
    # ... falls through to generic reference_id lookup
```

If `reference_id` already exists on a Legacy MPE, the Bridge returns
`{"status": "Success", "reference_name": existing.name}` immediately without
re-creating.

## Post-submit validation

After `legacy_doc.submit()`, the Bridge checks:

```python
warnings = []
if hasattr(legacy_doc, 'stock_entry_reference') and not legacy_doc.stock_entry_reference:
    warnings.append("No Stock Entry was created during submission")
```

If `stock_entry_reference` is not set after submit, a warning is appended to
the Bridge response. This catches the case where `make_stock_entry()` returned
`{"status": "failed", ...}` and triggered `rollback_entries()` — in that case
the MPE would be rolled back to draft and the Bridge would receive an exception
(not a warning). The warning here is defensive for edge cases.

## What Hermes workers can safely change here

| Change | Risk |
|---|---|
| Add new mapping row | Low — additive |
| Change default_value | Medium — may silently fill missing data |
| Touch idempotency logic | **High** — risk of duplicate MPE on retry |
| Remove post-submit `stock_entry_reference` warning | Low — defensive only |