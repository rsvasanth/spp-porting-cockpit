> [!WARNING]
> **DECOMMISSIONED REQUIREMENT**
> As of 2026-05-20, the unification requirement is obsolete. The active design of record relies on separate doctypes. Do not follow the patterns described in this file.

# 01 — Business context

> **Scope narrowed (2026-05-19):** This unification now covers **Compound family only** (Compound Inspection + Compound Deviation). The Production family (Line / Patrol / Lot) and the "Other" family (Incoming, Final Visual / PDIR) moved to a separate doctype, `SPP Quality Control`, specified in [`../spp-quality-control/`](../spp-quality-control/). See [`10-risks-and-decisions.md`](10-risks-and-decisions.md) for the rationale.

## What "inspection" means at SPP

Every material handoff in the manufacturing chain has a quality decision attached:

| Family | Variants | Where in chain | Spec |
|---|---|---|---|
| **Compound** | Compound Inspection (initial QA) + Compound Deviation (QM override) | Between Final Batch Mixing and Sheeting | **This spec** |
| **Production** | Line / Patrol / Lot | During and at end of Moulding run | [`../spp-quality-control/`](../spp-quality-control/) |
| **Other** | Incoming raw materials, Final Visual / PDIR | Receipt; pre-dispatch | [`../spp-quality-control/`](../spp-quality-control/) |

This spec covers **Compound family inspections only** as a single Console doctype (`Console Inspection`) with family-driven discrimination.

## Why unify

Before Phase 3, three Console doctypes existed with mostly-duplicate schema:

| Pre-Phase-3 doctype | Purpose |
|---|---|
| `Console Compound Inspection` | QI's initial QA decision on a mixed compound |
| `Console Compound Deviation` | QM's override decision on a Rejected compound |
| `Console Quality Inspection` | Other QA flows (out of porting scope but in same conceptual family) |

Duplication created three problems:

1. **Saga drift surface** — the 2026-04-30 helper refactor consolidated Bridge-side identity logic into shared functions (`_resolve_compound_identity`, `_lookup_legacy_stock_entry`, `_apply_compound_identity_to_doc`). Console-side controllers still had per-type copies of the 5-step `apply_bridge_result` pattern. Any future race-safety fix would need to be applied to three places — high drift risk.

2. **Schema drift surface** — adding a new field to "inspection" required coordinated updates across three doctypes. Operators saw three different forms for what felt like one decision.

3. **Reporting friction** — "show me all inspections this shift" required UNION queries across three doctypes.

Phase 3 collapsed these into one `Console Inspection` doctype with:
- `inspection_type` Link → `Console Process Template` (each type has its own template row)
- `inspection_family` Select discriminator (`Compound` / `Production` / `Other`)
- Polymorphic readings child table

## The family taxonomy

| Family | Identity field | Bridge target | Examples |
|---|---|---|---|
| **Compound** | `mix_barcode` (resolves to upstream Mixing SE via 6-strategy lookup) | Legacy `Compound Inspection` | Compound Inspection, Compound Deviation |
| **Production** | `lot_no` (references Add On Work Planning Lot #) | Legacy `Inspection Entry` (Wave 4 — not yet shipped) | Line Inspection, Patrol Inspection, Lot Inspection |
| **Other** | Whatever fits (`mix_barcode` OR `lot_no` OR custom) | TBD per future inspection_type | (Future — incoming raw QC, dispatch QC, etc.) |

**Implication:** `Console Inspection` is a polymorphic doctype. Different inspection_types have different identity fields populated and different downstream Bridge targets. The `inspection_family` field tells the system which axis the record lives on.

## Why three per-type Console doctypes still exist

Pre-Phase-3 records — submissions made before the unification went live on 2026-05-01 — were already in their original per-type doctypes. Backfilling them into `Console Inspection` was deferred (separate epic, out of program scope).

The module-level `apply_bridge_result` dispatcher (`api.py:~1980`) includes ALL of these in its `parent_doctypes` lookup list so any **callback** for a pre-cutover record still finds its parent. New submissions land in `Console Inspection`; old submissions are read-only and still callback-routable.

## Position in the chain

Compound family:

```
Final Batch Mixing → (compound batch in inspection-WIP warehouse)
                                  │
                                  ▼
              Compound Inspection (CI — initial QA decision)
                       │
            ┌──────────┼──────────┐
            │                      │
        Accepted               Rejected
            │                      │
            │                      ▼
            │              Compound Deviation (CD — QM override)
            │                      │
            │           ┌──────────┼──────────┐
            │           │                      │
            │       Accepted  Rejected  Rework
            │           │          │      │
            ▼           ▼          ▼      ▼
       Sheeting Process          Scrap   (back to mixing)
```

Production family (Wave 4 — not shipped, planned):

```
Add On Work Planning (Lot # generated)
                │
                ▼
      Line / Patrol / Lot Inspections (concurrent during moulding run)
                │
                ▼
      Moulding Production Entry (MPE — terminal; cascades batch_no back to IEs)
```

## What success looks like for the operator

For Compound Inspection / Deviation (Compound family — code/spec inspected; shipment status follows the through-Sheeting boundary):
1. QI or QM opens Console Dash, selects the appropriate inspection_type (controlled by their role)
2. Scans badge + compound barcode → source compound identity auto-fills
3. Enters readings (CI) or status + reason (CD)
4. Submit → both Legacy + Ops sync within 30 seconds

For Inspection Entry (Production family — Wave 4 planned):
1. Quality Inspector opens Console Dash
2. Selects inspection_type (Line / Patrol / Lot — three Process Template rows; same `inspection_family=Production`)
3. Scans badge + Lot # → Job Card context auto-fetches
4. Enters per-defect-type rejection counts
5. Submit → eventually consistent across Legacy + Ops

## Operational constraints

| Constraint | Why |
|---|---|
| Each submission MUST have an `inspection_type` (Link to Process Template) | Drives family, validation, Bridge sequence |
| `inspection_family="Compound"` → `mix_barcode` required | Identity invariant |
| `inspection_family="Production"` → `lot_no` required | Identity invariant |
| Per-type validation dispatch MUST be Python function | Frappe-native; no DSL or runtime eval |
| Pre-Phase-3 records remain in their original doctype (read-only after cutover) | Backward compat |
| New submissions land in `Console Inspection` (Phase 3 path) | Unification target |
| All three doctypes use the same 5-step `apply_bridge_result` pattern | Saga invariant preserved |

## Why the validation dispatch pattern

Different inspection_types need different validation logic:
- Compound Inspection: BOM-driven reading specs; auto-derive Accepted/Rejected
- Compound Deviation: QM signoff required; min reason length
- Line Inspection: type uniqueness per Lot; readings against per-cavity defect catalog
- Patrol Inspection: similar but separate sampling cycle
- Lot Inspection: `inspected_qty_nos > 0` mandatory; final QA gate

Encoding this in the controller's `validate()` would create a giant if/elif tree. Instead, each `Console Process Template` row registers a Python function name in `validation_dispatch_method`. The controller calls it at validate time, passing the doc.

This stays Frappe-native (no DSL, no eval) and keeps inspection_type specifics in their own functions.

## What the business is NOT asking for from this unification

- A unified UI screen for all inspection types (each type has its own Dash component for UX clarity)
- Automatic migration of pre-Phase-3 records (backfill is a separate epic)
- A new doctype per inspection_type (the unification's whole point is to AVOID this)
- Real-time SPC charts (analytics layer; out of program)
