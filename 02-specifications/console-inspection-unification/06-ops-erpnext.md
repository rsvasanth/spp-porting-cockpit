> [!WARNING]
> **DECOMMISSIONED REQUIREMENT**
> As of 2026-05-20, the unification requirement is obsolete. The active design of record relies on separate doctypes. Do not follow the patterns described in this file.

# 06 — Ops ERPNext (v15)

> Read [`../compound-deviation/06-ops-erpnext.md`](../compound-deviation/06-ops-erpnext.md) for the generic TransactionEngine pattern. The unification doesn't introduce a dedicated Ops handler — both Compound and Production families stay on the generic engine.

## Architectural Intent vs Reality for Inspection on Ops

**Architectural Intent:** All inspection processing (Compound Inspection, Compound Deviation) flows through `TransactionEngine` completely agnostically. 
`grep "COMPOUND_INSPECTION\|COMPOUND_DEVIATION\|LINE_INSPECTION" apps/shree_polymer_ops` → 0 hits for direct process mapping.

**Current Reality (Tech Debt):** While the inspection logic itself is properly agnostic, `shree_polymer_ops/api.py` still contains dead process-specific code (e.g., `_process_stock_entry_pre_save`, `_handle_sheeting_pre_save`) from earlier architecture iterations. These hooks do not interfere with inspection, but any developer auditing the `api.py` file should be aware that process-specific code in Ops is deprecated and slated for removal.

## Status-conditional Ops behavior (unchanged from CD spec)

Same pattern documented in [`../compound-deviation/06-ops-erpnext.md`](../compound-deviation/06-ops-erpnext.md):

| Status | Ops SE created? | SE Purpose |
|---|---|---|
| `Accepted` (CI or CD) | Yes | Material Transfer (compound → ready warehouse) |
| `Rejected` (CD only — CI Rejected doesn't reach Ops at submit time per factory-requirement skip) | Yes | Material Issue / write-off |
| `Rework` (CD only) | No | Compound stays in inspection-WIP |

Conditions are evaluated by `TransactionEngine._eval_condition` against payload context. The Ops `Console Process Template` action rows have `condition: "status == 'Accepted'"` etc.

## Production family Ops (Wave 4 planned)

Inspection Entry submissions (Line / Patrol / Lot):
- No Stock Entry at IE submit time (rejection SEs deferred to MPE)
- Ops MES Log entry is created
- `result_payload` records the inspection metadata (defect counts, inspector_id)

The Ops handler signature stays generic-engine; no dedicated handler needed for inspections per current architecture (Charter Principle 2).

## Cross-step output chaining for MPE cascade

When MPE submits and triggers `submit_inspection_stock_entries_from_moulding` (Wave 5):
- Ops receives the cascade call with `(lot_no, batch_no)`
- Looks up IE records with `rejection_se_pending=1`
- For each, materialises a Stock Entry (Material Issue) with the now-known batch_no

This is the deferred-SE-creation pattern at work. Ops is involved only when MPE's cascade fires; IE submissions themselves don't create SEs on Ops.

## Idempotency

`Shree Polymer MES Log` lookup by `reference_id`. Retried submissions return cached result.

## Documents produced on Ops per type

| Submission | Ops doctypes created |
|---|---|
| CI Accepted | MES Log + Material Transfer SE |
| CI Rejected | MES Log only (factory-requirement skip means Ops-only call; the Process Template's action skips the SE creation when status=Rejected) |
| CD Accepted | MES Log + Material Transfer SE |
| CD Rejected | MES Log + Material Issue SE |
| CD Rework | MES Log only |
| IE Line / Patrol / Lot (Wave 4) | MES Log only (rejection SEs deferred to MPE cascade) |
