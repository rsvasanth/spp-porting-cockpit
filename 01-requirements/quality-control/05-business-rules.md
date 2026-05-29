# 05 — Business rules

Format: `BR-QC-<n>`. Business rules are invariants — they hold regardless of UI state, network state, or who is logged in.

## Master data invariants

**BR-QC-01** — Ops site (`25spp.local`) is the SOLE master of `SPP QC Parameter` and `SPP QC Template`. Console copies are read-only caches.

**BR-QC-02** — Every `SPP QC Template` MUST link to exactly one Item via `item_code` (mandatory).

**BR-QC-03** — Every template parameter MUST have non-null `min_value` and `max_value` (mandatory). `nominal_value` is optional but recommended.

## Strict template gate

**BR-QC-04** — No inspection MAY be submitted for an Item that lacks an active `SPP QC Template`. No generic fallback template, no default tolerances. The gate is hard.

**BR-QC-05** — A reading is `Pass` iff `min_value <= reading_value <= max_value`. Inclusive on both bounds. Outside the range, `Fail`. There is no half-pass.

## Inspection type matrix

| Type | UoM logged | Rejection SE type (Ops) | SE submission gate | Warehouse movement |
|---|---|---|---|---|
| Line | `Nos` → converted to `Kg` | Material Transfer | Draft (`docstatus=0`) | Source → Rejection |
| Patrol | `Nos` → converted to `Kg` | Material Transfer | Draft (`docstatus=0`) | Source → Rejection |
| Lot | `Nos` → converted to `Kg` | Material Transfer | Draft (`docstatus=0`) | Source → Rejection |
| Incoming | `Nos` | Material Transfer | Draft (`docstatus=0`) | Source → Rejection |
| Final Visual / PDIR | `Nos` | Material Transfer | Submitted (`docstatus=1`) | Source → Target / PDIR |

**BR-QC-06** — Draft Stock Entries (Line/Patrol/Lot/Incoming) MUST have a defined closer. Acceptable closers: end-of-shift batch job, supervisor manual submit, or auto-submit on cancellation of QC. The spec MUST name the closer; this requirement does not mandate which.

**BR-QC-07** — Source, Target, and Rejection warehouses MUST be sourced from `Console Process Template` parameters. No hardcoding; no global default.

## Calculation invariants

**BR-QC-08** — For Moulding types (`Line`, `Patrol`, `Lot`):
```
total_rejected_qty_kg = total_rejected_qty (Nos) * one_no_qty_equal_kgs
```
Where `one_no_qty_equal_kgs` is sourced from `Console Mould Specification` at scan time and SNAPSHOTTED onto the `SPP Quality Control` record. Changes to Mould Spec after submission do NOT propagate.

**BR-QC-09** — For Incoming and Final Visual: the Stock Entry `qty` field MUST equal `total_rejected_qty` in `Nos` (no conversion).

## Identity invariants

**BR-QC-10** — `reference_id` is a UUID generated on the Console at submit time. It is the idempotency key for Ops orchestration: Ops MUST reject duplicate `reference_id` payloads.

**BR-QC-11** — `Inspector` and `Operator` MUST be different `Employee` records. Same-person inspections are blocked.

## Cancellation invariants

**BR-QC-12** — A `SPP Quality Control` MAY only be cancelled if its linked Ops Stock Entry can be cancelled. Stock consumed by downstream operations = cancellation blocked.

**BR-QC-13** — Cancellation cascades in fixed order: Ops first, Legacy second, Console last. Failure at any step halts the cascade and surfaces a recoverable error.
