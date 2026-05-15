# 06 — Ops ERPNext (v15)

> Refer to [`../master-batch-mixing/06-ops-erpnext.md`](../master-batch-mixing/06-ops-erpnext.md)
> for the generic TransactionEngine pattern. Compound Deviation runs on
> the same engine.

## Architectural Intent vs Reality for Deviation on Ops

**Architectural Intent:** The Ops side has no process-specific handler for Compound Deviation; it falls through to the generic `TransactionEngine`.
`grep "COMPOUND_DEVIATION" apps/shree_polymer_ops` → 0 hits for direct mapping.

**Current Reality (Tech Debt):** While Compound Deviation executes perfectly via the generic engine, `shree_polymer_ops/api.py` still contains dead process-specific code from earlier architecture iterations (e.g., `_process_stock_entry_pre_save`, `_handle_sheeting_pre_save`). These hooks do not interfere with CD execution, but any developer auditing the `api.py` file should know this process-specific code is deprecated and slated for removal.

## Status-driven Ops behavior

The Console Process Template `COMPOUND_DEVIATION` has different action
rows than MB Mixing. Specifically, the `transfer_to_store` action has a
condition:

```python
{
    "action_id": "transfer_to_store",
    "condition": "status == 'Accepted'",
    "payload_template": json.dumps({
        "doctype": "Stock Entry",
        "stock_entry_type": "Material Transfer",
        "from_warehouse": "{{from_warehouse}}",
        "to_warehouse": "{{to_warehouse}}",
        "__submit": True,
        "items": [{...}],
    })
}
```

This means:
- **`status=Accepted` deviation** → Material Transfer SE created on Ops
  (moves compound from inspection-WIP to ready warehouse)
- **`status=Rejected` deviation** → action skipped (no SE; compound stays
  in inspection-WIP, manual write-off needed)
- **`status=Rework` deviation** → action skipped (compound stays put;
  operator returns to mixing area)

The condition is evaluated by `TransactionEngine._eval_condition` against
the payload context. The Ops engine reads `context.status` from the
canonicalised payload built by `build_transaction_payload`.

## Ops MES Log

Same shape as MB — one row per Deviation submission. `result_payload`
includes the action outputs (empty if all actions were status-skipped).

## Idempotency

Same `Shree Polymer MES Log` lookup by `reference_id`. Retried submission
returns cached result.

## What lands on Ops

| Document | Created when | Notes |
|---|---|---|
| `Shree Polymer MES Log` | Always | `status=Success` even if no SE created (status-skipped actions still produce a successful run) |
| `Stock Entry` (Material Transfer) | Only if `status=Accepted` | Moves compound from inspection-WIP to ready warehouse |
| `Stock Ledger Entry` × N | If SE created | Standard Frappe-generated |

## Why this matters operationally

A Hermes worker reading `Console Transaction Log` for a Rejected
Deviation will see `sync_status=Success` but **no impacted_balances** in
the Ops response. This is correct behaviour — the action was conditionally
skipped — but can look surprising if they're used to MB's pattern (always
produces balances).
