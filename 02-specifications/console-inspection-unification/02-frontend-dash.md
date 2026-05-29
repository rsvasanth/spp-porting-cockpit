> [!WARNING]
> **DECOMMISSIONED REQUIREMENT**
> As of 2026-05-20, the unification requirement is obsolete. The active design of record relies on separate doctypes. Do not follow the patterns described in this file.

# 02 — Frontend (Dash)

> The unification keeps **per-type React components** — there is NO single "unified inspection" screen. Each inspection_type gets its own component because UX requirements differ meaningfully (readings table for CI; QM signoff for CD; per-defect grid for Inspection Entry).

## Component → inspection_type mapping

| Console Process Template | React component | inspection_family |
|---|---|---|
| `COMPOUND_INSPECTION` | `CompoundInspectionEntry.tsx` | Compound |
| `COMPOUND_DEVIATION` | `CompoundDeviationEntry.tsx` | Compound |
| `LINE_INSPECTION` (Wave 4) | `InspectionEntryEntry.tsx` with type=Line | Production |
| `PATROL_INSPECTION` (Wave 4) | Same component; type=Patrol | Production |
| `LOT_INSPECTION` (Wave 4) | Same component; type=Lot | Production |

The `processRegistry.tsx` map keys components by `process_code`. Type-specific UX lives in the component file; family-level commonalities live in shared hooks/utilities.

> See [`../compound-deviation/02-frontend-dash.md`](../compound-deviation/02-frontend-dash.md) for the CD component walkthrough (the most complete shipped example of an inspection screen).

## Compound family — common UX patterns

Both `CompoundInspectionEntry.tsx` and `CompoundDeviationEntry.tsx` share:

1. **Barcode scan as primary entry point** — operator scans the compound's `mix_barcode`; Dash fetches identity + readings spec via `validate_compound_barcode` or `get_rejected_compound_inspection`.

2. **Read-only identity display** — once scanned, the compound's item_code / batch_no / spp_batch_no / source_warehouse are read-only on screen.

3. **Per-parameter reading inputs** — BOM-attached parameter specs render as a table. Operator enters reading per parameter; system auto-marks Pass/Fail against min/max from `Console Inspection Reading Spec`.

4. **Auto-derived status** (CI) or **manual status selection** (CD) — CI derives Accepted/Rejected from per-parameter Pass/Fail; CD requires explicit QM choice (Accepted/Rejected/Rework).

5. **Two-block payload shape** — both emit `compound_inspection_data` + (CD only) `compound_deviation_data`. CD's `compound_inspection_data` mirrors an Accepted CI's shape exactly so the Bridge can run the same identity pipeline.

## Production family — Wave 4 planned UX

`InspectionEntryEntry.tsx` (planned per `04_WAVE4.md`):

1. **Type dropdown at top** — Line / Patrol / Lot. Operator picks; the rest of the form adapts (e.g. Lot Inspection adds inspected_qty_nos required field).

2. **Lot # scan** — auto-fetches Job Card context (production_item, BOM, one_no_qty_equal_kgs).

3. **Defect multi-row entry** — operator adds rows: (defect_type, rejected_nos). System auto-calculates rejected_kg per row + totals.

4. **No identity readings table** — production inspections focus on rejection counts, not measurement readings (defect catalog drives the form).

5. **Submit gating** — Lot Inspection requires inspected_qty_nos > 0; Line/Patrol allow zero (no rejections observed is a valid submission).

## Shared scaffolding across all inspection types

All inspection components inherit:

- **Live Feedback Promise.all pattern** — `Promise.all([executeStep(legacy), executeStep(ops)])` per the standard Console orchestration. Per-target row visible in submission modal.

- **Retry UX** — failed leg row shows error + Retry button; retry rebuilds `req_params` from `Console Transaction Log.request_payload`.

- **Backdating** — System Manager / Administrator can backdate; regular operators clamped to "today or yesterday".

- **`reference_id` generation** — `Date.now()` 13-digit ms timestamp. Pre-Phase-3 Compound Deviation prefixed with `CDEV-` historically; new submissions use raw timestamp.

- **Role-based screen access** — Quality Inspector sees CI; Quality Manager sees CD; both see read-only access to the other type's records.

## Process Template drives the screen selection

The unification's UX choice — per-type component instead of one screen — is enabled by `Console Process Template`:

- Each inspection_type has its own Process Template row
- The Template's `dash_component` field names the React component to mount (e.g. `"CompoundDeviationEntry"`)
- `processRegistry.tsx` resolves this to the actual component class

This means **adding a new inspection_type requires:**
1. New Process Template row with `is_inspection_type=1`, `inspection_family`, `dash_component`, `validation_dispatch_method`
2. New React component (if family or UX is novel) OR reuse existing
3. No new doctype, no new Console controller — the unified `Console Inspection` handles it

## What the unification DOES change in Dash

| Change | Effect |
|---|---|
| Component → doctype mapping | Both `CompoundInspectionEntry` and `CompoundDeviationEntry` now write to `Console Inspection` (Phase 3) for new submissions instead of their per-type doctypes |
| Payload shape | New `inspection_type` field at top level (or inside metadata) of the payload; Bridge uses this for routing |
| Process Template lookups | The component reads `inspection_family` from Process Template to know which identity fields to show |
| Reading spec | Components read `Console Inspection Reading Spec` (linked from Process Template) instead of BOM directly — gives operations control over inspection rules without code change |

## What the unification does NOT change in Dash

- Existing components keep their files and names
- `processRegistry.tsx` still resolves by `process_code` exactly as before
- The Live Feedback submission pattern is unchanged
- Operator workflow is identical (same scans, same fields, same submit button)

## Where to extend safely

Adding a new inspection_type:
1. Add a `Console Process Template` row with `is_inspection_type=1`, appropriate family, validation_dispatch_method
2. Define readings spec via `Console Inspection Reading Spec` child rows
3. Add the React component if novel UX needed; otherwise reuse + parameterise
4. Add the Python validation function in `shree_polymer_console.api`
5. Register in `processRegistry.tsx`
6. No Console doctype changes; no Bridge mapping changes (unless legacy doctype differs from existing Compound Inspection)
