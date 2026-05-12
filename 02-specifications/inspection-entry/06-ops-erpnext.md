# 06 — Ops ERPNext — `shree_polymer_ops::process_transaction` for inspection

**File:** `apps/shree_polymer_ops/shree_polymer_ops/api.py`
**Relevant function:** `process_transaction` (inspection routing, TransactionEngine)
**Process:** Inspection Stock Entries on the Ops side.

> For the shared Ops patterns (TransactionEngine, sequence from
> `Console Process Template`, MES Log idempotency), see
> [MB Mixing Ops ERPNext](../master-batch-mixing/06-ops-erpnext.md).
> This file documents only the inspection-specific additions.

## How `process_transaction` handles inspection

The Ops side handles inspection differently depending on inspection type:

- **Line / Patrol / Lot:** No Ops-side Stock Entry creation. The rejection Stock
  Entry is created on the **Legacy side** via `make_stock_entry` (Branch A).
  Ops does not participate in this branch.

- **Incoming / Final:** Same as above — rejection SE is on Legacy via
  `make_inc_stock_entry` (Branch B).

- **Final Visual / PDIR:** The VS/PDIR Stock Entry is created on the **Legacy
  side** via `make_vs_pdir_stock_entry`. The Work Order + Job Card are created
  by the IE controller itself (`create_work_order_vs_entry__only`).

**Conclusion:** The Ops side does **not** currently create any Stock Entries
for Inspection Entry types. The rejection material movement lives entirely on
the Legacy side.

## What the Ops side does for inspection

From the legacy controller's `on_submit` behavior, there is **no Ops leg for
Inspection Entry** in the current implementation. The `sync_strategy` for
`INSPECTION_ENTRY` is likely `"Legacy Bridge Only"` — Console submits to
Legacy Bridge only, and the Legacy controller handles all downstream stock
movement.

If a future wave adds an Ops leg for inspection (e.g., to create Work Orders
for Line/Patrol/Lot on the Ops side as well), it would be structured as:

```
Console initialize_submission
  → create_local_inspection (Console Inspection created)
  → Console Transaction Log: Legacy leg only (Pending)
  → execute_submission_step: Legacy Bridge fires
  → Legacy creates Inspection Entry + rejection SE (draft)
  → Legacy IE on_submit: cascade or finalize
```

## Potential future Ops participation

The one case where Ops might participate in the future is if the system
decides to have a **dual-leg inspection flow** (Legacy for compliance record,
Ops for shop-floor stock movement). This is not in the current spec.

For now, this spec records: **Ops has no inspection-specific code path.**
The `shree_polymer_ops` TransactionEngine handles MB Mixing, FB Mixing,
Sheeting, Cut Bit Transfer, and Blanking DC Entry — but NOT Inspection Entry.

## What Hermes workers can safely change here

| Change | Risk |
|---|---|
| Add an Ops inspection Stock Entry path | **High** — requires re-architecting the rejection SE creation to be dual-leg |
| Change `process_transaction` inspection routing | **High** — affects all inspection types |
| Add inspection to the TransactionEngine sequence | **High** — would require Console Process Template config |