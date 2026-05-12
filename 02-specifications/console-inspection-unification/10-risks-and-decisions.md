# 10 — Risks and decisions

## Plan-vs-reality deltas

| # | Delta | Plan said | Reality | My recommendation |
|---|---|---|---|---|
| 1 | Console doctype count for inspections | 3 per-type doctypes (Compound Inspection + Compound Deviation + future Inspection Entry) | 1 unified `Console Inspection` + 3 per-type doctypes preserved for backward compat | **Keep co-existence**; defer pre-Phase-3 doctype deprecation |
| 2 | Wave 4 `Console Inspection Entry` creation | Plan doc instructs creating a new per-type Console doctype | NOT needed — unified `Console Inspection` handles Production family via Process Template rows | **Wave 4 implementation should NOT create a new Console doctype** — supersede the plan-doc instruction |
| 3 | Validation logic location | Plan doc implies validation in controller `validate()` directly | Validation dispatch mechanism via Process Template's `validation_dispatch_method` field | **Keep** — extensible for future types |
| 4 | Reading spec storage | Plan didn't specify | New `Console Inspection Reading Spec` child doctype with declarative min/max per parameter per type | **Keep** — gives operations control without code change |
| 5 | cavity_no proper wiring | Plan didn't surface | Fallback to 1 + structured log (BR-INS-006 from inspection-process requirements) | **Wire properly** — 1-hour effort, recommended |

## Cross-doctype invariants Hermes must NOT break

| # | Invariant | Where enforced | Breaks if… |
|---|---|---|---|
| 1 | All 3 inspection doctypes use byte-identical 5-step `apply_bridge_result` | Per-doctype controllers | Any controller's pattern diverges from the others — saga regression |
| 2 | Module-level `parent_doctypes` list keeps `Console Inspection` FIRST | `api.py::apply_bridge_result` | Order reversed; Phase 3 lookup becomes slower; pre-Phase-3 records may shadow new ones |
| 3 | `inspection_type` ↔ `Console Process Template` Link integrity | DB-level Link constraint | Process Template renamed / deleted without cascade |
| 4 | Factory-requirement skip for Rejected CIs | `initialize_submission` `is_rejected_inspection` check | Rule modified; Legacy starts receiving rejected CIs prematurely |
| 5 | Validation dispatch method is a Frappe-resolvable Python function | Controller `validate()` `get_attr(dispatch)` | Function path becomes stale; type-specific validation silently skipped |
| 6 | Shared Bridge identity helpers (`_resolve_compound_identity` etc.) handle both CI + CD payload shapes | Bridge `populate_*_fields` | One side's payload shape changes without the other adapting |
| 7 | Compound family identity = mix_barcode; Production family identity = lot_no | Family-driven dispatch in `create_local_inspection` | Mixing identity logic between families |
| 8 | cavity_no fallback to 1 + structured log | Bridge `_apply_deviation_extras` | Fallback removed before proper wiring done — Legacy validation throws |

## Operational risks

| Risk | Likelihood | Impact | Existing mitigation |
|---|---|---|---|
| Per-type doctype callbacks fail to find parent (pre-cutover record stale) | Low (all callbacks should be settled by now) | Low — pre-cutover records are read-only in practice | Module-level dispatcher includes pre-Phase-3 doctypes in fallback list |
| Validation dispatch function path stale (e.g. function renamed) | Medium (as code evolves) | Medium — type-specific validation silently skipped | `get_attr` failure caught + logged; not blocking — recommend re-tightening (raise instead of log) |
| Reading Spec child rows out of sync between Process Templates | Medium | Medium — operator sees wrong min/max | Operations responsibility; reconciliation report recommended |
| Race in `apply_bridge_result` (same as MB/CD) | Low | Handled by 5-step pattern | Confirmed working |
| Backward-compat callback returns wrong doctype | Very low | High | `parent_doctypes` list order; new submissions always Phase 3 |
| New inspection_type added without registering Process Template + Dash component + validation function | Medium (developer workflow gap) | Medium | Documentation in this spec + checklist |
| cavity_no fallback masks real multi-cavity production | Confirmed | Medium — data quality | Structured log surfaces each fire |

## Decisions deferred

### Backfill of pre-Phase-3 records into `Console Inspection`

Pre-cutover records remain in their original Console doctypes. Backfilling them:
- Read each Console Compound Inspection / Console Compound Deviation record
- Synthesize Phase 3 fields (inspection_type, inspection_family, polymorphic readings)
- Insert into Console Inspection with `flags.from_local_cache=True`
- Mark original as migrated

**Recommend:** Defer indefinitely. Co-existence works. Backfill is a 1-2 day epic with low operational benefit. Only worth doing if a future analytics need requires single-doctype queries.

### Deprecation of `Console Compound Inspection` / `Console Compound Deviation`

Cannot happen until backfill is done. Sequence:
1. Backfill complete + verified
2. Update `parent_doctypes` to remove the per-type doctypes
3. Mark per-type doctypes as deprecated (custom field warning on Desk)
4. After 90 days of zero callbacks, archive the doctypes

**Recommend:** No active timeline. Revisit annually.

### Wave 4 implementation choices (Production family inspection types)

When Wave 4 lands:

- Use the existing unified `Console Inspection` doctype (do NOT create `Console Inspection Entry`)
- Add Process Template rows: `LINE_INSPECTION`, `PATROL_INSPECTION`, `LOT_INSPECTION` with `inspection_family="Production"` and `is_inspection_type=1`
- Define new validation functions in `shree_polymer_console.api` (one per type or shared)
- Add Reading Spec rows for defect-type / count tracking
- Add Bridge mapping `seed_inspection_entry_mapping` + `populate_inspection_entry_fields` for the legacy doctype
- Add Dash component `InspectionEntryEntry.tsx` with type dropdown
- Register in `processRegistry.tsx`

**No new Console doctype needed.** This is the whole point of unification.

### Validation dispatch tightening

Current: validation dispatch failure is caught and logged, doesn't throw. This is permissive — type-specific validation could silently skip if the function path is stale.

**Recommend:** Tighten to raise after the validation_dispatch_method mechanism is more widely adopted. Currently only Compound family types register functions; raise-on-miss would surface stale-path bugs immediately.

## Questions waiting on production overseer

| Question | Recommendation |
|---|---|
| Wire `cavity_no` through Console properly? | **Yes — 1 hour effort** (same recommendation as CD spec) |
| Validate the validation_dispatch mechanism by adding more per-type validators? | **Yes** for Wave 4 — give Production family types proper validators rather than relying on generic |
| Begin pre-Phase-3 doctype backfill? | **Defer** — no operational pressure |
| Tighten validation dispatch failure handling (log → raise)? | **Yes, after Wave 4** — once more types use the mechanism |
| Add automated reconciliation between Reading Spec and BOM spec? | **Defer** — operational responsibility for now |
| Add monitoring on cavity_no fallback fires? | **Yes** — same monitoring epic as CD |

## My opinion

The unification is the biggest architectural win of the porting program. Before Phase 3, the cockpit would have had 3 separate spec packs for Compound Inspection + Compound Deviation + (future) Inspection Entry — each carrying its own copy of the saga's race-safety pattern, its own identity logic, its own legacy mapping. After Phase 3, **one Console doctype handles all inspections** with type-driven discrimination, and the saga's lessons live in one place.

The cost — three doctypes co-existing during the transition — is real but bounded. Pre-Phase-3 callbacks are essentially settled; only theoretical risk remains.

For Wave 4, the unification means we **skip a doctype creation entirely**. Production-family inspections drop into the existing structure with just Process Template + Bridge mapping work. Saves an estimated 2-3 days of doctype-design work.

For the cockpit, this means **inspection-process motion requirements (CI + CD) and a future Production-family motion will both reference this single unification spec** for the underlying architecture.
