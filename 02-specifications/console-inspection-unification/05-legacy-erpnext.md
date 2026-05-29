> [!WARNING]
> **DECOMMISSIONED REQUIREMENT**
> As of 2026-05-20, the unification requirement is obsolete. The active design of record relies on separate doctypes. Do not follow the patterns described in this file.

# 05 — Legacy ERPNext (v15)

> Most of the legacy details for the Compound family live in [`../compound-deviation/05-legacy-erpnext.md`](../compound-deviation/05-legacy-erpnext.md). This file focuses on the **unification-specific** legacy aspects.

## Legacy doctype is shared

Both Compound Inspection AND Compound Deviation submissions create rows in the SAME legacy doctype: `Compound Inspection`. Discrimination is via `status` field + `quality_approver_*` populated.

The Phase 3 unification does NOT change anything on Legacy. The legacy schema, controller, and on_submit chain are untouched.

**Why this matters:** Legacy reports query `Compound Inspection` directly. Unification on Console doesn't perturb Legacy reports.

## Status semantics on Legacy

| Console-side context | Legacy `Compound Inspection.status` | Stock Entry created on Legacy |
|---|---|---|
| CI Accepted (auto-derived from readings) | `"Accepted"` | Material Transfer SE (compound → ready warehouse) |
| CI Rejected | (NOT POSTED — factory-requirement skip) | None |
| CD Accepted (QM override) | `"Accepted"` + `quality_approver_*` populated | Material Transfer SE |
| CD Rejected | `"Rejected"` + `quality_approver_*` | Material Issue / write-off SE |
| CD Rework | `"Rework"` + `quality_approver_*` | None |

## Production family — Wave 4 planned legacy

`Inspection Entry` is a **different legacy doctype** from `Compound Inspection`. Wave 4 will add the Bridge mapping (`seed_inspection_entry_mapping`) + populate function (`populate_inspection_entry_fields`) for this doctype.

Production family details (Line / Patrol / Lot):
- Same legacy doctype `Inspection Entry` for all three types (legacy uses `inspection_type` field as discriminator, mirroring Console's pattern)
- Three different on_submit behaviours per type (TBD per Wave 4)
- Type uniqueness per lot enforced at Legacy schema level (unique constraint on (lot_no, inspection_type, docstatus != 2))

## Pre-Phase-3 records on Legacy

Legacy is **unchanged** by the unification. Console's three doctypes (Console Inspection, Console Compound Inspection, Console Compound Deviation) all map to the same Legacy doctype.

Pre-cutover and post-cutover records on Legacy look identical — only their `reference_id` distinguishes them (Phase 3 records carry a Console-generated reference_id; pre-Phase-3 records may have legacy-internal IDs).

## What Hermes workers must NOT touch on legacy

Same as the per-process specs:
- `Compound Inspection` doctype schema (high blast radius — reports + controllers depend)
- `populate_compound_*_fields` helper functions (shared between CI + CD)
- 6-strategy SE lookup
- Legacy `Inspection Entry` doctype (Wave 4 planning surface — changes need cross-program coordination)

## What downstream legacy consumers depend on

- Compound Inspection's `stock_id` → linked to upstream Mixing SE; resolved via 6-strategy chain
- Compound Inspection's `status` → drives downstream SE creation type
- Compound Inspection's `quality_approver_*` fields → signals CD overlay (vs raw CI)
- Inspection Entry's `lot_no` (Wave 4) → cross-motion key referenced by MPE

## Backfill of pre-Phase-3 records

**Not in program scope.** Pre-cutover records remain in their original Console doctypes (Console Compound Inspection, Console Compound Deviation). Backfilling them into `Console Inspection` would require:
1. Read each pre-Phase-3 record
2. Synthesize Phase 3-shape fields (set inspection_type, inspection_family)
3. Insert into Console Inspection with `flags.from_local_cache`
4. Mark original record as "migrated" (or deactivate)

Deferred indefinitely. Co-existence is acceptable.
