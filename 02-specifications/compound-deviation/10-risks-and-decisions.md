# 10 — Risks and decisions

## The `cavity_no` TODO — highest priority

**Decision needed:** wire `cavity_no` through Console properly, or keep
the default-to-1 fallback indefinitely?

| Aspect | Current state | If wired properly |
|---|---|---|
| Console doctype | No `cavity_no` field on `Console Inspection` | Add field |
| Dash UI | No input | Add input on `CompoundDeviationEntry.tsx` + `CompoundInspectionEntry.tsx` |
| Payload | Doesn't include `cavity_no` | `compound_inspection_data.cavity_no` included |
| Bridge populate | Falls back to `1` + structured log | Reads from payload; no fallback needed |
| Legacy mandatory validation | Bypassed by the fallback | Honored end-to-end |
| Multi-cavity moulds | Recorded as single-cavity (data quality bug) | Recorded correctly |

**My recommendation:** wire properly. Multi-cavity moulds are rare but
non-zero, and the structured log already proves we're losing the signal.
Estimated effort: 1 hour (doctype field + Dash input + payload include).

## Other plan-vs-reality deltas

| # | Delta | Plan said | Reality | My recommendation |
|---|---|---|---|---|
| 1 | Separate `Console Compound Deviation` doctype | Specified | Implemented as separate doctype, but Phase 3 dispatch routes new records to unified `Console Inspection` instead. Two doctypes co-exist. | **Consolidate** when feasible — the separate doctype is now legacy-path-only. Can be deprecated after a back-fill epic. |
| 2 | `deviation_reason` field | Required | Required + 5-char minimum in validate | **Keep** — minimum length came from the saga (some operators submitted "ok" as reason). |
| 3 | `cavity_no` field | Specified in template + mapping | Not wired through Console | **Wire properly** (see top of file) |
| 4 | Multi-deviation per CI | Plan didn't address | Dash blocks via UI but no backend constraint | **Add backend uniqueness** — `Console Compound Deviation`'s `source_compound_inspection` should be unique among non-cancelled records. |

## Cross-doctype invariants Hermes must NOT break

In addition to MB's invariants:

| # | Invariant | Where enforced | Breaks if… |
|---|---|---|---|
| 1 | Compound Deviation creates a legacy `Compound Inspection`, not "Compound Deviation" | Bridge's `mapping.legacy_doctype = "Compound Inspection"` | Mapping seeder changes the legacy_doctype |
| 2 | Bridge `field_mappings` is empty; all logic in `populate_compound_deviation_fields` | `seed_compound_deviation_mapping` seeds `field_mappings=[]` | Someone adds mapping rows here (would duplicate Python logic) |
| 3 | Identity resolution uses the same pipeline as Compound Inspection | Shared helpers `_resolve_compound_identity` + `_lookup_legacy_stock_entry` + `_apply_compound_identity_to_doc` | Deviation diverges with its own identity logic (this was the pre-saga state) |
| 4 | The 6-strategy SE lookup survives intact | `_lookup_legacy_stock_entry` | Strategies removed without zero-hit proof |
| 5 | Rejected CIs do NOT route to Legacy (factory requirement) | `initialize_submission` skip | Skip removed; Legacy CIs get duplicate records (one from rejected CI, one from later Deviation) |
| 6 | 5-step `apply_bridge_result` race-safe pattern | Controller method (byte-identical across 6 doctypes) | Pattern simplified or steps removed |
| 7 | `_apply_deviation_extras` idempotent writes (only set if currently empty) | `if not doc.get(field):` guards | Pattern weakened — re-runs would overwrite QM signoff or status |
| 8 | `cavity_no` fallback to 1 + structured log | `_apply_deviation_extras` | Fallback removed before wiring is done — Legacy validation throws |

## Operational risks

| Risk | Likelihood | Impact | Existing mitigation |
|---|---|---|---|
| Concurrent callbacks from Ops + Legacy regress sync_status | Confirmed (was the saga) | High — operator sees `Partial` despite both legs Success | 5-step pattern with self-heal in step 4 |
| Multi-cavity production runs incorrectly recorded as single-cavity | Low (multi-cavity is rare) | Medium — data quality bug surfaces in QC reports | Structured log every fallback; manual correction post-hoc |
| QM enters short or generic deviation_reason | Medium (operator UX shortcut) | Low — audit trail less useful | 5-char minimum + UI hint |
| Same CI deviated twice (two QMs racing) | Low | High — duplicate Legacy CI created; stock ledger drift | Dash UI blocks (no backend gate yet — see #4 above) |
| WAREHOUSE_MAP miss falls through to U3-Store | Medium (when new warehouses added) | Medium — wrong warehouse on legacy SE | No active monitoring; needs alert |
| 6-strategy SE lookup misses entirely (DCR not synced upstream) | Low | High — Deviation submit fails with "Bridge SE Lookup FAILED" | Structured error message points operator to upstream MB / DCR fix |
| `cavity_no` fallback breaks (e.g. field renamed on legacy) | Very low | High — all Deviation submits fail | No fallback for the fallback — would require code change |

## Decisions deferred to a later wave

### Backend uniqueness constraint on `source_compound_inspection`

Add a unique constraint such that a single Compound Inspection can only
have one (non-cancelled) Deviation. Currently the Dash blocks it but
nothing enforces it at the DB level.

**Recommend:** add when next Console doctype migration runs. Low priority
because the UI gate has held in production.

### Consolidate `Console Compound Deviation` into `Console Inspection`

Phase 3 routes new Deviations to `Console Inspection`. The standalone
`Console Compound Deviation` doctype is now legacy-only. Deprecation
plan:
1. Confirm zero new submissions hit `Console Compound Deviation` (Console Transaction Log analytics)
2. Back-fill old records into `Console Inspection` with `inspection_type="Deviation"`
3. Migrate `Console Compound Deviation` to read-only
4. Remove from `parent_doctypes` lookup in module-level `apply_bridge_result`

**Recommend:** defer until full Console Inspection unification spec is
written (separate cockpit folder for that work). Don't touch the
standalone doctype in isolation.

### Shared mixin for the 5-step pattern

The 118-line `apply_bridge_result` is duplicated across 6 controllers.
Could refactor to a shared mixin or base class. Pros: single source of
truth. Cons: hides production-critical logic behind inheritance.

**Recommend:** defer indefinitely. The duplication is documented; touching
one without the other is the real risk, and the cockpit's review
checklist catches that. A refactor would need full concurrency testing
across all 6 doctypes simultaneously — high cost, low benefit.

## Questions waiting on production overseer

| Question | My recommendation |
|---|---|
| Wire `cavity_no` through Console properly? | **Yes — 1 hour effort, high data-quality benefit** |
| Add backend uniqueness for source_compound_inspection on Deviation? | **Yes, low priority** |
| Begin Phase 3 cleanup migration of `Console Compound Deviation` → `Console Inspection`? | **Defer** until full unification cockpit spec exists |
| Add monitoring on `cavity_no` fallback log frequency? | **Yes, as part of monitoring epic** |
| Add monitoring on WAREHOUSE_MAP miss frequency? | **Yes, as part of monitoring epic** |
| Refactor 5-step pattern into shared mixin? | **No, defer indefinitely** |
