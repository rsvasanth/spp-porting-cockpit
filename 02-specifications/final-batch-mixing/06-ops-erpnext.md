# 06 — Ops ERPNext (v15)

> **Identical to MB Mixing.** Read [`../master-batch-mixing/06-ops-erpnext.md`](../master-batch-mixing/06-ops-erpnext.md).

## No FB-specific Ops code

`grep "FINAL_BATCH_MIXING" apps/shree_polymer_ops` → 0 hits.

`shree_polymer_ops::process_transaction` does not have a process-specific
handler for FB, so the request falls through to the generic
`TransactionEngine` — the same path MB uses.

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
