# 01 — Purpose

## What this process produces

A **Compound batch** — a homogeneous polymer/additive mixture ready for downstream sheeting, blanking, and moulding. Production happens in two stages:

| Stage | Input | Output | Console process | Legacy doctype | Item group of output |
|---|---|---|---|---|---|
| Master Batch Mixing | Raw materials (polymer base + pigments + additives) | Master Batch concentrate | `Console Master Batch Mixing` | `Delivery Challan Receipt` (inward_material_type=Master Batch) | Master Batch |
| Final Batch Mixing | One Master Batch lot + additional raw materials | Production-ready Compound | `Console Final Batch Mixing` | `Delivery Challan Receipt` (inward_material_type=Compound) | Compound |

Each submission represents a single operator-supervised mixing event on a single workstation, with one tracked finished-goods barcode.

## Where mixing sits in the chain

```
[Raw materials]
   │
   ▼
Master Batch Mixing  ◀── this requirement
   │
   ▼
Final Batch Mixing  ◀── this requirement
   │
   ▼
Compound Inspection  (QA check; separate requirement)
   │
   ▼
Sheeting → Cut Bit / Blanking → Work Planning → Inspection Entry → Moulding Production Entry
```

Mixing is the **head of the chain**. Every downstream process depends on a successful mixing record existing across all three systems (Console + Legacy + Ops). A failure here cascades.

## Why both MBM and FBM exist

The shop floor distinguishes between:

- **Master Batch** — a concentrated colour/additive carrier, produced in advance and stocked. Has a longer shelf life. Different mixing recipe than the final compound.
- **Final Batch** (Compound) — the production-ready material made just before sheeting. Consumes a Master Batch lot plus additional polymer/chemicals to achieve the final specification.

This two-stage approach gives the business:

| Benefit | Why it matters |
|---|---|
| Inventory flexibility | Master Batches can be made in bulk during slow periods; Final Batches are pulled just in time |
| Quality isolation | If a Master Batch fails QA, all Final Batches made from it are quarantined (Compound Deviation flow) |
| Recipe modularity | Same Master Batch can feed multiple Compound formulations |
| Recycling loop | Cut-bits from downstream Sheeting can be recycled back into Final Batch Mixing as raw input |

## Why DCR is the legacy target

The legacy ERPNext install pre-dates Console. It has used `Delivery Challan Receipt` as the polymorphic doctype for material-receipt events for years. Both Master Batch and Final Batch mixings landed as DCR records on legacy long before the Bridge existed.

When the Console + parallel-sync architecture was designed, the choice was:

| Option | Trade-off |
|---|---|
| Reuse legacy DCR | Minimises migration risk; downstream legacy reports keep working; familiar to ops staff |
| Create new legacy doctypes (one per process) | Cleaner separation, but requires re-pointing every legacy report and retraining ops staff |

**Decision: reuse DCR.** The Bridge writes `inward_material_type = "Master Batch"` or `"Compound"` to distinguish variants. Legacy's on_submit handler branches on this field to take the right sub-path (MB-specific SE creation vs FB-specific Work Order + SE creation).

## Why Ops gets a separate Stock Entry

Ops is the **newer** ERPNext install. It uses standard ERPNext `Stock Entry` (with `stock_entry_type=Manufacture`) — not the legacy DCR pattern. The MES Transaction Engine builds the SE from the Console payload using the action sequence declared on `Console Process Template`.

This duality (DCR on legacy, Stock Entry on ops) is **intentional and load-bearing**. Each ERP keeps its native shape; the Bridge is the only layer that translates.

## Why parallel sync, not sequential

Legacy and Ops are eventually consistent, **not** transactional. The Bridge does NOT run a two-phase commit across them. Reasons:

| Reason | Detail |
|---|---|
| Shop floor speed | Sequential sync (Legacy → wait → Ops) would add 5–10 seconds per submit. Operators submit ~50–100 records per shift. |
| Resilience | If Legacy is briefly unreachable, Ops still records the production. Console's `sync_status="Partial"` surfaces the gap. |
| Decoupled ERPs | Either ERP can be taken down for maintenance without blocking the other. |
| Retry simplicity | Failed leg retries individually via `Console Transaction Log` — no compensating-transaction logic. |

The **cost** of parallel sync is eventual consistency: there is a window (seconds to minutes during a Bridge outage) where the two ERPs disagree. The business accepts this; downstream reconciliation surfaces drift at shift-end reports.

## What the business is NOT asking for

See [07-out-of-scope.md](07-out-of-scope.md). High-level exclusions:

- Real-time inventory consistency across the two ERPs (eventual is fine)
- Transactional rollback on partial sync failure (operator-driven retry is fine)
- Mass-balance enforcement at submit time (deviations are a real production signal)
- Back-fill of pre-Console legacy DCR records into Console (historical data stays on legacy)
