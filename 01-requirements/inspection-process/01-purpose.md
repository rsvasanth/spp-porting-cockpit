# 01 — Purpose

## What this motion does

After a compound is produced (Master Batch or Final Batch Mixing), Quality Assurance must verify the compound meets specification before it can flow into downstream Sheeting/Blanking/Moulding. This motion covers the two coupled flows:

| Process | Trigger | Actor | Outcome |
|---|---|---|---|
| **Compound Inspection (CI)** | After every mixing submission | Quality Inspector | Compound is **Accepted** (moves downstream) or **Rejected** (held pending QM decision) |
| **Compound Deviation (CD)** | After a CI is Rejected | Quality Manager | QM decides: **Accepted** (override CI rejection — material proceeds), **Rejected** (write off / scrap), or **Rework** (return to mixing) |

CI and CD are **two operational forms of the same business event:** "decide what to do with this compound." Legacy stores both as the same `Compound Inspection` doctype, distinguished by `status` and QM signoff fields.

## Position in the chain

```
Master Batch Mixing → Final Batch Mixing
                            │
                            ▼
                  Compound Inspection (CI)   ◀── QI submits
                            │
            ┌───────────────┼───────────────┐
            │               │               │
        Accepted        Rejected            │
            │               │               │
            │               ▼               │
            │     Compound Deviation (CD)   │  ◀── QM submits
            │               │               │
            │     ┌─────────┼─────────┐     │
            │     │         │         │     │
            │  Accepted  Rejected  Rework   │
            │     │         │         │     │
            ▼     ▼         ▼         ▼     │
       Sheeting Process    Scrap   (back to mixing)
```

## Why this is a coupled pair, not two independent processes

1. **Same legacy doctype** — both create rows in `Compound Inspection` on Legacy
2. **Same identity pipeline** — both use `_resolve_compound_identity` + the 6-strategy SE lookup
3. **Same race-safety contract** — both run the 5-step `apply_bridge_result` byte-identically
4. **Same `cavity_no` fallback** — both have the same legacy validation surface
5. **CD only exists because CI can fail** — without CI's Rejected outcome, CD has no input

Treating them as separate motions would force duplication of the saga-derived invariants. Grouping them keeps the saga's lessons in one place.

## Why Console keeps three doctype variants

| Doctype | Used by | Why kept |
|---|---|---|
| `Console Inspection` (Phase 3 unified) | New CI + CD submissions | Single unified entry point; differentiated by `inspection_type` field |
| `Console Compound Deviation` (legacy per-type) | Pre-Phase-3 CD records | Backward compatibility; module-level `apply_bridge_result` routes callbacks to whichever doctype holds the record |
| `Console Compound Inspection` (legacy per-type) | Pre-Phase-3 CI records | Same — preserves historical callback routing |

The Phase 3 unification consolidated the three pre-existing legacy per-type Console doctypes into one. Existing records keep their original doctype; new submissions land in `Console Inspection`. This co-existence is intentional during the transition; eventual deprecation of the per-type doctypes is a future cleanup epic.

## Why CD is on Console (not just an "edit CI" workflow)

On Legacy, a deviation historically was a manual edit to the existing CI row by a QM. The Console architecture deliberately makes CD a **separate submission event** because:

- The QM signoff is an audit-trail-worthy event in its own right
- The decision rights are separate (QI vs QM); separate UI enforces separation cleanly
- The stock-ledger consequence differs by deviation status — Accepted CD creates a Material Transfer SE; Rejected creates Material Issue; Rework creates no SE
- Separating submissions makes the timeline visible: "lot rejected at T+5; QM decided Accept-override at T+12 with reason X"

## Operational constraints

| Constraint | Why |
|---|---|
| CI must reference an existing compound batch via `mix_barcode` | The 6-strategy SE lookup needs identity to resolve the legacy Stock Entry |
| `[CI-only]` Rejected CIs route Ops-only (factory requirement) | Legacy MUST NOT receive a Rejected CI submission — the lot stays in inspection-WIP until CD closes the gap |
| `[CD-only]` CD must reference an existing Rejected CI by `mix_barcode` | Console Dash validates this before allowing submit |
| `[CD-only]` `deviation_reason` must be ≥ 5 characters | Enforced in controller `validate` |
| `[CD-only]` QM role required | Console User must hold `Quality Manager` role |
| Both flows: cavity_no defaults to 1 if missing | Until Console wires it through properly (active TODO) |
| Both flows: identity round-trip via `mix_barcode` to Legacy and Ops | Single barcode authority pattern (Program Charter Principle 1) |

## What the business is NOT asking for

See [07-out-of-scope.md](07-out-of-scope.md). High-level exclusions:

- A separate "QM approval queue" UI (Compound Deviation IS the QM queue)
- Automatic CD creation when CI is Rejected (operator-driven; QM picks up rejected lots)
- Multiple deviations per CI (one CD per CI; enforced at Dash and recommended at backend)
- Real-time alerting to QM when CI rejected (handled operationally, not by code)
