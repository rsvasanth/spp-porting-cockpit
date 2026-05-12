# 09 — Rollout and history

## What changed when

This spec is the first formal write of the Inspection Entry spec. Before
this pass, IE was covered under a grouped moulding pack that treated IE as
only three moulding variants (Line, Patrol, Lot) and called it "unshipped."
Both assumptions were wrong — live `spp15.local` has 124,197 IE records and
6 active inspection types.

| Date | Change | Evidence |
|---|---|---|
| 2023-03-28 | `Inspection Entry` DocType created | `creation` in `inspection_entry.json` |
| 2023-10-20 | Last modification to `inspection_entry.json` | `modified` in JSON |
| 2026-05-12 | This spec written | From `inspection_entry.py` (1534 lines) + live data |

## Drift from prior understanding

The prior grouped moulding pack had two significant errors about IE:

1. **IE treated as only 3 moulding variants.** Live data shows 6 inspection
   types with 27k–30k records each for Lot, Line, Incoming, Final Visual.
   The spec must cover all 6 types.

2. **IE called "unshipped."** Live `spp15.local` has 124,197 IE records,
   120,663 submitted. IE is in production, not planned. The spec is a
   **retroactive documentation** of live production behavior, not a design
   for a future system.

## What this spec supersedes

- `spp-porting-cockpit/01-requirements/inspection-entry/` — requirement
  capture (source for this spec)
- Any prior grouped moulding pack references to "IE only has Line/Patrol/Lot"

## What Hermes can and cannot touch

| Artifact | Can Hermes modify? | Why |
|---|---|---|
| Legacy `inspection_entry.py` controller | **NO** | Load-bearing for all 6 inspection types + MPE cascade |
| Legacy `inspection_entry.json` schema | **NO** | Defines field structure used by all inspection types |
| Legacy `Inspection Entry Item` child table | **NO** | Shared across all inspection types |
| Console `Console Inspection` doctype | YES (with review) | New layer, not yet in production |
| Console `create_local_inspection` | YES (with review) | Audit trail; change must preserve `_safe_local_create` invariants |
| Bridge `sync_process_transaction` for IE | YES (with review) | Mapping layer; change must preserve idempotency |
| MPE batch cascade (`submit_inspection_stock_entry_immediately`) | **NO** | Cascade is load-bearing cross-doctype invariant; see `10-risks-and-decisions.md` |

## Relationship to MPE rollout

IE and MPE are rolled out together. MPE requires submitted Line + Patrol IE
for a lot before MPE can be submitted (enforced in MPE's `validate()`).
Therefore:

- IE must be live and tested for Line + Patrol before MPE can be used in
  production
- The MPE batch cascade (`submit_inspection_stock_entry_immediately`) must
  be tested with IE rejection Stock Entries in draft state

## Relationship to Deflashing Receipt Entry

Incoming Inspection triggers `Deflashing Receipt Entry.manual_on_submit`
when submitted. This cross-Doctype dependency means:

- DRE must be tested and stable before Incoming Inspection is tested
- DRE's `manual_on_submit` behavior must be preserved during any DRE refactor

## When in doubt — pause and ask

Hermes workers who need to modify any layer that touches IE should:

1. Read this spec end-to-end first
2. Run graphify queries on `shree_polymer_custom_app` for the specific
   function chain they need to change
3. Check the two critical drift findings in `10-risks-and-decisions.md`
4. Surface a proposal in the Kanban card BEFORE coding
5. Wait for Reviewer worker + production overseer to sign off

The cost of asking is one turn; the cost of an unauthorised change to the
IE `on_submit` branching or the MPE cascade is hours of recovery on
production-staging.