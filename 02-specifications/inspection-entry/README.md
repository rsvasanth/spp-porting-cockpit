# Inspection Entry — Specification (layered, code-level)

**Status:** EMPIRICAL DRAFT. Written from legacy `inspection_entry.py` (1534 lines),
`inspection_entry.json` schema, and live `spp15.local` evidence (124,197 total records,
120,663 submitted).

**Wave:** Planned (not yet shipped). Phase 3 consolidation target.

**Console doctype:** `Console Inspection` (unified inspection entry, replacing
legacy `Inspection Entry` for Line/Patrol/Lot/Incoming/Final Visual types).

**Legacy doctype:** `Inspection Entry` (`INSP-.#####`) on `spp15.local` —
polymorphic quality record with 6 live inspection type branches.

**Cascade partner:** `Moulding Production Entry` (`MPE`) supplies the produced batch
to Line/Patrol/Lot rejection Stock Entries. See `../moulding-production-entry/`
for MPE's side of the cascade contract.

## Read the layers in order

| File | What it covers |
|---|---|
| [01-business-context.md](01-business-context.md) | What the inspector does on the shop floor, 6-type polymorphic anatomy, production volumes |
| [02-frontend-dash.md](02-frontend-dash.md) | `InspectionEntry.tsx` — type-aware form, defect rows, totals, scan flow |
| [03-console-backend.md](03-console-backend.md) | Console `api.py` inspection path — `create_local_inspection`, `apply_bridge_result`, type routing |
| [04-bridge-layer.md](04-bridge-layer.md) | Legacy Bridge `sync_api.py` for `INSPECTION_ENTRY` mapping + cascade helpers |
| [05-legacy-erpnext.md](05-legacy-erpnext.md) | Legacy `Inspection Entry` controller — validate, on_submit, stock entry creation, MPE cascade |
| [06-ops-erpnext.md](06-ops-erpnext.md) | Ops `shree_polymer_ops::process_transaction` for inspection Stock Entries |
| [07-end-to-end-flow.md](07-end-to-end-flow.md) | Sequence diagrams — Line/Patrol submit → rejection SE, MPE cascade, Final Visual path |
| [08-test-plan.md](08-test-plan.md) | Unit (legacy + gaps), integration, E2E, smoke, UAT |
| [09-rollout-and-history.md](09-rollout-and-history.md) | What changed when, what Hermes can/cannot touch |
| [10-risks-and-decisions.md](10-risks-and-decisions.md) | Two critical drift findings, Patrol inclusion decision, MPE cascade alignment |

## Drift watch

This spec was written 2026-05-12 against:
- Legacy controller: `apps/shree_polymer_custom_app` HEAD (`inspection_entry.py`, 1534 lines)
- Legacy JSON: `inspection_entry.json` (437 lines, last modified 2023-10-20)
- Live site: `spp15.local` — 124,197 total IE records, 120,663 submitted, 6 inspection types
- Requirements: `spp-porting-cockpit/01-requirements/inspection-entry/` (275 lines)

If any of these advance significantly without a spec review, re-verify the
branching logic and stock entry paths against current code before relying on
this document.

## Relationship to MPE spec

IE and MPE are deeply coupled. MPE is the **consumer** of IE's Line + Patrol
completion; IE is the **precondition** for MPE submission. Additionally, MPE
produces the batch that cascades back to update IE's rejection Stock Entries.
The cascade alignment is documented in `10-risks-and-decisions.md` (Critical
Drift Finding #2).

For shared orchestration patterns (the 5-step `apply_bridge_result` dance, the
`_safe_local_create` audit-trail invariant, the `reference_id` cross-system
key), see `../master-batch-mixing/03-console-backend.md`. IE does not repeat
those patterns; this spec cross-links to them.