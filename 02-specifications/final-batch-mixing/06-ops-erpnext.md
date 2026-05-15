# 06 — Ops ERPNext (v15)

> **Identical to MB Mixing.** Read [`../master-batch-mixing/06-ops-erpnext.md`](../master-batch-mixing/06-ops-erpnext.md).

## Architectural Intent vs Reality for FB on Ops

**Architectural Intent:** Like MB Mixing, FB Mixing is handled by the **generic** `TransactionEngine` running the Console Process Template sequence.
`grep "FINAL_BATCH_MIXING" apps/shree_polymer_ops` → 0 hits for direct mapping.

**Current Reality (Tech Debt):** `shree_polymer_ops::process_transaction` does not have a process-specific handler for FB, so it falls through to the generic `TransactionEngine`. However, `shree_polymer_ops/api.py` still contains dead process-specific code from earlier architecture iterations (like `_process_stock_entry_pre_save` and `_generate_mix_barcode`) that exist alongside the generic engine. These hooks do not interfere with modern FBM execution, but any developer auditing the `api.py` file should know this process-specific code is deprecated and slated for removal.

## Sequence steps for FB

The Console Process Template `FINAL_BATCH_MIXING` has `actions` rows that
produce the same sequence shape as MB: Work Order → Job Card → Stock Entry
(Manufacture). Differences:

- The `production_item` for the WO is a Compound (not Master Batch)
- The `bom_no` is the Compound's BOM (which has the MB as one of its
  inputs, plus the additional raw materials)
- The SE items include the MB input row (matched against
  `Console Item.is_batch_item` semantics)

These differences are **data-driven** via the template, not code. From Ops
TransactionEngine's perspective, it's the same engine running with
different parameters.

## What lands on Ops for one FB submission

Same set of documents as MB (per `../master-batch-mixing/06-ops-erpnext.md`):
- `Shree Polymer MES Log` — one row, status=Success
- `Work Order` — production_item = Compound
- `Job Card` — against the WO
- `Stock Entry` (Manufacture) — consuming MB + raw materials, producing
  Compound with `mix_barcode` from Console
- `Stock Ledger Entry` rows
- `Batch` (auto-created for the FG)

The `impacted_balances` response includes deltas for the MB input
(reduced), each raw material (reduced), and the Compound FG (increased).

## Idempotency

Same `Shree Polymer MES Log` lookup by `reference_id` as MB. A retried
`execute_submission_step` with the same reference_id returns the cached
result without re-creating documents.
