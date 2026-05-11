# 01 — Business context

## What Compound Deviation is

When QA performs a Compound Inspection on a freshly mixed Compound (the
output of Final Batch Mixing or downstream Sheeting), the inspection
yields one of three outcomes:

| Inspection result | Meaning | Next step |
|---|---|---|
| **Accepted** | All readings within spec | Compound moves to Sheeting / next stage normally |
| **Rejected** | Readings out of spec | QA cannot consume the compound — a **Quality Manager** must intervene |
| (No third state at CI level) | | — |

When a Compound Inspection is **Rejected**, the operator does NOT directly
re-route the material. Instead, a **Quality Manager (QM)** opens a
**Compound Deviation** record where they decide the disposition:

| QM decision (Compound Deviation status) | Meaning | Material disposition |
|---|---|---|
| **Accepted** (override) | QM signs off that the deviation is acceptable | Material proceeds to next stage despite failing CI |
| **Rejected** | Material genuinely cannot be used | Material is scrapped or sold; stock removed from inventory |
| **Rework** | Material can be reprocessed (e.g. blended with a good lot) | Material returned to mixing area for rework |

## Position in the chain

Compound Deviation is an **overlay**, not a primary stage. The chain runs:

```
Final Batch Mixing → Compound Inspection
                           │
                ┌──────────┼──────────┐
                │          │          │
            Accepted    Rejected      │
                │          │          │
                │          ▼          │
                │   Compound Deviation (QM)
                │          │          │
                │     ┌────┼────┐     │
                │     │    │    │     │
                │  Accept Reject Rework
                │     │    │    │     │
                ▼     ▼    ▼    ▼     │
            Sheeting Process  (back to mixing) (out of inventory)
```

## Why it's an overlay (not a primary process)

The Compound Deviation **does not produce new material** — it produces a
**decision** about existing material. From a stock-ledger perspective:

- Accepted Compound Inspection → submits a Material Transfer SE (move
  from inspection-WIP to ready-to-use warehouse)
- Compound Deviation:
  - Accepted → submits same Material Transfer SE (override the rejection)
  - Rejected → submits a different SE (move to scrap warehouse or write-off)
  - Rework → no SE; material stays in current warehouse pending re-mixing

This means the **legacy doctype** that gets created is the **same**
`Compound Inspection` doctype — but with different `status`, `remarks`,
QM signoff fields, and downstream SE behavior.

## Why Console has a SEPARATE `Console Compound Deviation` doctype

Despite legacy treating it as a CI variant, Console keeps a dedicated
`Console Compound Deviation` doctype because:

1. **Operator role is different** — only Quality Manager (or higher) can
   submit a deviation; Compound Inspection is open to Quality Inspector
2. **UX is different** — Deviation screen shows the **existing rejected
   CI** as read-only context, plus QM-specific inputs (status dropdown,
   approver scan, deviation reason)
3. **Audit separation** — keeping the records separate makes "how many
   deviations did we have last month?" trivially queryable

## Roles

| Role | Permission on Compound Deviation |
|---|---|
| Mixing Operator | No access |
| Quality Inspector | No submit permission (read may exist for visibility) |
| **Quality Manager** | Full submit permission — this is the only role that creates deviations |
| System Manager / Administrator | Full access including backdate |

## Operational constraints

| Constraint | Why |
|---|---|
| Source Compound Inspection must exist and be Rejected | Console Dash fetches the source CI by `mix_barcode` and validates `status == "Rejected"` before allowing deviation submit |
| `deviation_reason` must be ≥ 5 characters | Enforced in controller `validate` (when not in audit-trail bypass mode); ensures QM provides actual reasoning |
| QM scan validates against Console Employee role | Dash blocks if scanned employee doesn't have "Quality Manager" role |
| One deviation per CI | Console enforces this at the dash layer (button hidden if existing deviation found); legacy doesn't have a hard constraint |
| Status drives target system routing | If status=Rejected: no SE on Ops (material is scrap); if Accepted: full Material Transfer SE; if Rework: no SE at all |

## What makes Compound Deviation high-stakes

1. **Stock impact differs by status** — getting the status wrong creates
   ghost stock or unintentional write-offs
2. **Race condition history** — the saga of 2026-04-29 → 2026-05-01 was
   driven by Compound Deviation submissions where Ops and Legacy callbacks
   landed simultaneously and the aggregate `sync_status` regressed
3. **QM accountability** — every deviation must be traceable to a specific
   QM. The `quality_approver_id` field is mandatory and validated by the
   Dash before submit
4. **Cross-doctype identity** — must lock onto the same `mix_barcode` /
   `stock_id` / `dc_receipt_id` as the original Compound Inspection.
   Getting this wrong creates two legacy CIs claiming the same compound
   batch — Stock Ledger reconciliation breaks
