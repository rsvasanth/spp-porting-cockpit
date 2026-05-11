# 01 — Business context

## What FB Mixing is

A Final Batch (FB) — also called a "Compound" in legacy terminology — is
the production-ready material that gets sheeted, blanked, and moulded into
finished parts. FB Mixing **consumes** a Master Batch (MB) plus additional
raw materials and produces a homogeneous Compound.

Compared to MB Mixing:
- MB Mixing: raw materials → MB (a concentrate)
- FB Mixing: MB + raw materials → Compound (production-ready material)

## Workstation difference

MB Mixing typically runs on a **Two Roll Mixing Mill**. FB Mixing usually
runs on a **Two Roll Mixing Mill** or an **Avon Kneader** (heavier
machine), depending on the compound. The legacy `Mixing Operation` master
data table holds the workstation-to-source-warehouse mapping that
`create_wo_final_batch_mixing` reads (see `05-legacy-erpnext.md`).

## Position in the chain

```
Master Batch Mixing  →  Final Batch Mixing  →  Compound Inspection
                                                       │
                                                       ▼
                                            Sheeting Process → Cut Bit Transfer →
                                            Blanking → ... → MPE
```

**FB blocks downstream Sheeting/Compound Inspection** in the same way MB
blocks FB. The chain is strictly sequential at the lot level.

## Prerequisite: an MB lot must already exist

This is the **major business difference** from MB Mixing:

| MB Mixing prerequisites | FB Mixing prerequisites |
|---|---|
| Raw materials with valid batches in source warehouse | Raw materials with valid batches **AND** a previously-completed MB lot with a scannable `mix_barcode` |

If an operator tries to submit an FB without scanning a real MB lot, the
upstream MB row in `consumption_items` will have an invalid `mix_barcode`
and:
- The Console-side audit record still lands (`from_local_cache` bypass)
- The Bridge call will succeed at the DCR-insert step
- The Legacy `validate_final_batches → create_wo_final_batch_mixing` path
  will fail at `validate_bom_items` because the MB row doesn't match an
  existing batch
- Net result: legacy DCR sits in Failed state, Console sees `Failed`,
  Compound never materialises

## What success looks like for the operator

1. Operator scans badge → operator selected
2. Selects produced item (a **Compound** item group)
3. **Scans the MB lot's barcode** to identify the master batch being consumed
4. Scans each additional raw material's barcode
5. Enters produced qty
6. Hits Submit — same Live Feedback UX as MB Mixing
7. Sees the new FB compound's barcode displayed + printable label

## Roles

Same role matrix as MB Mixing:
- Mixing Operator (submits)
- Quality Inspector / Quality Manager (inspects + sign-off on rejections)
- System Manager / Administrator (backdate)

## Operational constraints

| Constraint | Difference from MB |
|---|---|
| Operator must have role "Mixing Operator" | Same |
| BOM must exist for the produced item | Same — but FB BOM check is **stricter**: legacy `validate_bom_items` ensures EVERY BOM input item is in `dc_items` (MB doesn't strict-check this) |
| **Multi-BOM rejection** | `create_wo_final_batch_mixing` throws if multiple active BOMs exist for the same produced item; MB has no such check |
| Mass balance NOT enforced | Same — not enforced on Console side |
| Workstation resolution | Legacy auto-resolves workstation from `Mixing Operation` master data by source_warehouse; Console payload's `workstation` value gets overridden if a Mixing Operation row exists |

## Why this matters for porting

FB's legacy code path is **the main code that runs when a DCR submits**.
For MB, the on_submit branch returns early (`validate_final_batches → False`).
For FB, the on_submit branch is the **active** path that:
1. Validates the BOM
2. Creates an ERPNext Work Order
3. Creates a Job Card
4. Creates a Manufacturing Stock Entry

When Hermes workers touch the Bridge for any "Mixing Process" change, the
FB path is the one that actually exercises `create_wo` → all its children
functions. MB only exercises the SE creation chain via a different code
path that this spec acknowledges is not fully traced (`05-legacy-erpnext.md`
in MB spec).
