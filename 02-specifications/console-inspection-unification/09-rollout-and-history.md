> [!WARNING]
> **DECOMMISSIONED REQUIREMENT**
> As of 2026-05-20, the unification requirement is obsolete. The active design of record relies on separate doctypes. Do not follow the patterns described in this file.

# 09 — Rollout and history

## Current production status

Phase 1–4 unification exists in the inspected Console code, but after the production-overseer clarification on 2026-05-12 this spec must not treat it as staging/prod shipped beyond the "through Sheeting" shipment boundary. The unification work and the Compound Deviation saga (documented in CD spec) were related engineering efforts.

## Deploy timeline

| Date | Event | Impact |
|---|---|---|
| 2026-04-29 | Console Compound Inspection + Console Compound Deviation doctypes already shipped (pre-Phase-3) | Per-type doctypes operational |
| 2026-04-29 (evening) | Compound Deviation saga begins (race observed) | Triggers the 5-step pattern + helper extraction |
| 2026-04-30 (morning) | Fix #1: re-read both legs from DB | Partial fix |
| 2026-04-30 (midday) | Bridge SE lookup bug discovered | Drift surface revealed |
| 2026-04-30 (afternoon) | Fix #2: helper refactor (commit `1df2de8` family) | `_resolve_compound_identity`, `_lookup_legacy_stock_entry`, `_apply_compound_identity_to_doc`, `_apply_compound_readings_to_doc`, `_apply_compound_header_to_doc` extracted as shared helpers |
| 2026-04-30 (night) | Fix #3: 5-step pattern across all affected doctypes | Saga race-safety complete |
| 2026-05-01 | **Phase 3 unification deployed** — `Console Inspection` doctype + children + `create_local_inspection` + dispatch routing via `is_inspection_type` Process Template flag | New inspection submissions land in unified doctype |
| 2026-05-01 | Phase 4: per-type Console doctypes preserved for backward compat; module-level `apply_bridge_result` updated to include unified + per-type in `parent_doctypes` list | Co-existence model active |
| 2026-05-02 | Staging bug 1777721078171: `cavity_no` MandatoryError | Fallback to `cavity_no=1` + structured log added |
| 2026-05-09 | Fix `a0fc0fc`: rejected compound inspections not showing in Deviation screen | Bug in lookup query (filtering by old per-type doctype only); fixed to query unified + per-type via UNION |
| 2026-05-12 | Spec written (this document) | Documentation handoff |

## What the unification shipped

Across multiple commits on 2026-05-01:

1. **New unified doctype** `Console Inspection` (`INSP-.YYYY.-.#####`) with `inspection_type` Link + `inspection_family` Select + polymorphic readings child
2. **`create_local_inspection`** function in `api.py:2647` — replaces `create_local_compound_inspection` (now legacy fallback)
3. **Phase 3 dispatch** in `initialize_submission` (`api.py:985`) — routes based on `is_inspection_type` Process Template flag
4. **Validation dispatch mechanism** — `Console Process Template.validation_dispatch_method` Python function pointer; called from controller's `validate()`
5. **`Console Inspection Reading`** child doctype — polymorphic with `reading_type` discriminator (Measurement / Defect Count / Visual / Dimensional)
6. **`Console Inspection Reading Spec`** child doctype — declarative spec rules per inspection_type, per parameter
7. **Module-level `apply_bridge_result` dispatcher** updated to include `Console Inspection` FIRST in `parent_doctypes` list, with per-type fallbacks after

## What was preserved (not broken)

- Pre-Phase-3 `Console Compound Inspection` and `Console Compound Deviation` doctypes — schemas unchanged
- Pre-Phase-3 controllers — `apply_bridge_result` byte-identical to unified
- Legacy `Compound Inspection` doctype — completely unchanged
- Bridge `populate_compound_inspection_fields` + `populate_compound_deviation_fields` — same code, called by Bridge for the corresponding `process_code` regardless of where the Console record lives
- All existing inspection-related React components and `processRegistry.tsx` keys

## What changed in operator workflow

Nothing visible. Operators continue to use:
- `CompoundInspectionEntry.tsx` for CI
- `CompoundDeviationEntry.tsx` for CD

The form fields, scan flow, submit pattern — identical. The only difference is **where the Console record lands** (Console Inspection instead of Console Compound Inspection / Console Compound Deviation), and that's invisible to operators.

## What changed for engineers / Hermes workers

A new pattern to learn:
- "Inspection types are Process Template rows, not doctypes"
- "Family drives identity; type drives validation"
- "Pre-Phase-3 doctypes exist for backward compat only — don't add new code to them"
- "All three inspection doctypes have byte-identical apply_bridge_result — coordinate any change"

## Migration stance — hard cutover for new submissions; pre-cutover records read-only

- Submissions on or after 2026-05-01 land in `Console Inspection`
- Submissions before 2026-05-01 remain in their original Console Compound Inspection / Console Compound Deviation doctype
- Pre-cutover records are read-only in practice (no UI re-submission path)
- Pre-cutover record callbacks (rare — should be settled by now) still route via module-level dispatcher

## What Hermes workers can safely change

| Change | Risk |
|---|---|
| Add a new inspection_type (Process Template + validation function) | Low |
| Add a new reading_type to `Console Inspection Reading` | Low |
| Add a new field to `Console Inspection` | Medium — coordinate with pre-Phase-3 doctypes if reporting needs alignment |
| Modify validation dispatch mechanism | Medium — affects all types that use it |
| Touch `create_local_inspection` family-driven dispatch | Medium |
| Touch `apply_bridge_result` 5-step pattern on Console Inspection | **Highest** — saga regression risk; needs same change on Console Compound Inspection + Console Compound Deviation byte-identically |

## What Hermes workers must escalate

| Change | Why |
|---|---|
| Deprecate Console Compound Inspection / Console Compound Deviation | Backfill epic dependency |
| Modify `populate_compound_*_fields` Bridge helpers | Shared between unified + pre-Phase-3 flows |
| Modify the 6-strategy SE lookup | Affects every Compound family inspection |
| Add a new `inspection_family` value | Requires `create_local_inspection` extension + Bridge mapping for new legacy doctype |

## Drift vs plan

The original plan docs (`00_PORTING_PLAN.md`) framed inspections as separate Wave 4 work (Inspection Entry as the next thing to port after Wave 3 Production Planning). Phase 1–4 happened **ahead of schedule** as the saga-driven refactor work that consolidated 3 legacy per-type Console doctypes into the unified shape.

This means:
- Wave 4 (`04_WAVE4.md`) plan-doc references to "Console Inspection Entry" as the Wave 4 target are partially obsolete
- Production-family inspection types (Line / Patrol / Lot) will use the unified `Console Inspection` doctype when Wave 4 implements them
- No new Console doctype is needed for Wave 4 — only Process Template rows + Bridge mapping for the legacy `Inspection Entry` doctype

This spec supersedes the plan doc's "create a Console Inspection Entry doctype" instruction.

## Reviewer worker checklist

Before promoting an inspection-related PR's "Tests Passing" → "Pushed":

- [ ] All 3 doctypes' unit tests pass
- [ ] If touching `apply_bridge_result`: concurrency test runs on ALL 3 doctypes
- [ ] If touching `create_local_inspection`: family-driven identity test passes
- [ ] If touching validation dispatch: registered function called correctly
- [ ] If touching `populate_compound_*_fields`: CI + CD scenarios both pass
- [ ] If touching factory-requirement skip: Rejected CI scenario passes
- [ ] One staging end-to-end submission per affected inspection_type
- [ ] Cavity_no fallback log entries visible (until TODO closed)
- [ ] Obsidian note logged
- [ ] Graphify refreshed
