# 10 — Risks and decisions

## Plan-vs-reality deltas — decisions waiting on you

These were intentional simplifications when MB Mixing shipped. Each needs
an explicit decision before any Hermes worker tries to "fix" them.

| # | Delta | Plan said | Reality | My recommendation |
|---|---|---|---|---|
| 1 | Mass-balance validation | `\|consumed − produced\| / produced < 0.5%` throws | No check at all | **Soft warning only** — log to `error_log_summary`, don't block. Reinstating as a throw will block legitimate small variances; deviation is a real production signal that should flow downstream rather than fail at mix time. |
| 2 | `item_code` field type | Link to `Console Item` | Data (denormalised) | **Defer** — promote only when a concrete report or rule needs FK integrity. Current behavior survives Console Item master data drift. |
| 3 | `operator_name` field | Link to `Console Employee` | Data + `submitted_by` Link to Console User | **Defer** — `submitted_by` already provides audit trail. Adding Console Employee link requires HR master data sync first. |
| 4 | `mixing_start_time` / `mixing_end_time` | Required Datetime fields | Not implemented; only `posting_date` / `posting_time` | **Add as optional** when shop-floor team asks for OEE / mixer utilisation reports. Don't block on it now. |
| 5 | `bom_no` reference | Link to `Console BOM`, required | Not stored on Console doc (BOM only in payload context) | **Defer** — couple this to Wave 3 (Add On Work Planning) when BOM-driven validation becomes essential. |
| 6 | `barcode_image` (Attach) | Stored on doctype | Generated in Dash + Bridge, not persisted | **Defer** — no concrete need to reprint after-the-fact yet. If shop floor asks for reprints, persist the URL in the Console Transaction Log's `barcode_image` field (already exists). |
| 7 | Treat plan doc `01_WAVE1.md` as deprecated? | n/a | Plan is stale on multiple counts | **Yes — supersede.** Mark `01_WAVE1.md` historical; this cockpit spec is authoritative. |

## Cross-doctype invariants Hermes must NOT break

These invariants are load-bearing for the entire MB → MPE chain. Each is
enforced at multiple layers; breaking one layer doesn't immediately fail
but compounds problems downstream.

| # | Invariant | Where enforced | Breaks if… |
|---|---|---|---|
| 1 | `mix_barcode` round-trips Console → Legacy DCR (`bridge_mix_barcode`) → Legacy SE → Compound Inspection's 6-strategy lookup | `console_mapping_seeder.py` row `mix_barcode → bridge_mix_barcode` + `_lookup_legacy_stock_entry` | Mapping changes drop `bridge_mix_barcode`, barcode format diverges, or legacy controller stops honoring it |
| 2 | `reference_id` is the cross-system correlation key | Console doctype unique constraint + Legacy `dc_no` mapping + Ops MES Log idempotency | Either side stops using it, or someone reuses an old reference_id |
| 3 | `sync_status = "Success"` ⇒ Console doc submitted (`docstatus=1`) | `apply_bridge_result` step 5 auto-submit | Auto-submit logic bypassed or made conditional |
| 4 | Audit-trail records exist even for invalid Dash payloads | `_safe_local_create` `flags.from_local_cache` + controller's bypass | `validate` moved before flag is set, or `ignore_validate` removed |
| 5 | Bridge + Ops legs are independently idempotent for the same `reference_id` | Bridge's `find_existing_record` + Ops engine's MES Log lookup | Either side starts re-creating documents on retry |
| 6 | `inward_material_type` value-map has `"Master Batch Mixing" → "Master Batch"` | `seed_mixing_process_mapping` value_map | Value-map deleted; defensive default `"Compound"` will silently route MB mixings into the FB path on legacy |
| 7 | Race-safe parallel callback handling | `apply_bridge_result` 5-step pattern | Any step removed or reordered |

## Operational risks

| Risk | Likelihood | Impact | Existing mitigation |
|---|---|---|---|
| Bridge `sync_via_bridge` HTTP times out mid-flight (Bridge created DCR but Console never got the 200) | Medium | `Console Transaction Log` Legacy row = Pending; sync_status stays Pending | Retry button in Dash + `_safe_local_create` keeps Console record + Bridge's idempotency check returns cached DCR on retry |
| Operator submits same `reference_id` twice (browser glitch) | Low | First submit lands; second hits unique constraint | `_safe_local_create` catches the exception, returns None, orchestration on Bridge/Ops still idempotent |
| `inward_material_type` value-map silently defaults to `"Compound"` | Medium | DCR creates with wrong type → downstream blank-bin / compound-inspection routing breaks | **No active monitoring** — recommended fix: add an alert on `Console Transaction Log` for unmatched operations (`operation not in value_map keys`) |
| `bridge_mix_barcode` empty in payload | Low | Legacy auto-generates its own barcode → Compound Inspection 6-strategy lookup tries and probably succeeds via fallback strategies, but creates traceability gap | Dash always populates `mix_barcode`; backend `create_local_master_batch_mixing` also derives from primary scan |
| 5-step dance step 5 auto-submit fails silently (exception caught + logged) | Low | Console doc stays Draft despite both legs Synced | Manual submit needed; check `Error Log` for `apply_bridge_result.{doctype}` entries |
| Mass balance drift not visible at mix time | Confirmed (no check) | Caught downstream at Compound Inspection / Stock Ledger reconciliation | This is current accepted behavior — decision #1 above |
| Legacy MB SE creation chain not fully traced in this spec | Confirmed | Hermes worker modifying MB → SE materialisation may not know which legacy function actually fires | **Action item:** trace `create_master_batch_stock` trigger empirically before any change to legacy MB path |

## Decisions deferred to a later wave

### Console Employee linkage

`operator_name` is a free-text Data field. To make this a Link to
`Console Employee`, we need:
- Employee master data sync from legacy HR
- Role enforcement on the Link (must have `Mixing Operator` role)
- Audit trail beyond what `submitted_by` (Frappe user) provides

Currently `submitted_by` is good enough. **Revisit when shop floor needs
operator-level production reports beyond what HR system already provides.**

### BOM linkage

`bom_no` is in the payload context but not stored on the Console doc.
The Bridge passes it to legacy; the Ops Work Order is created with it.
**Coupling point with Wave 3 (Add On Work Planning):** when planning
records start referencing the BOM at the lot level, MB Mixing may need
to also store the BOM on its own doc for traceability. Coordinate then.

### Backfill of pre-cutover legacy DCRs into Console

Not on any wave plan. The historical legacy DCRs created before the
Bridge existed don't have `reference_id` and therefore can't be
correlated to Console. If reporting needs this, a separate epic would:
1. Read legacy DCRs, generate synthetic reference_ids
2. Create Console records with `flags.from_local_cache=True`
3. Backfill `legacy_reference` from DCR name
4. Mark these records with `target_system = "Legacy"` only (no Ops leg)

**Recommend keeping this deferred indefinitely** — historical state is
fine to live on legacy.

## What I want you (production overseer) to decide before Hermes starts Wave 2 / FB Mixing spec

| Question | Why it matters | My recommendation |
|---|---|---|
| Reinstate mass-balance check as soft warning? | Affects every shop-floor MB submission + downstream deviation rate | **Yes, as soft warning** — capture in `error_log_summary`, don't block. Monitor for 2 weeks. |
| Promote `item_code` / `operator_name` to Link fields? | Improves data integrity, slows submit (FK lookup), couples to master data freshness | **No, defer.** No concrete report or rule currently needs it. |
| Add `mixing_start_time` / `mixing_end_time`? | Enables OEE / mixer utilisation reports | **No, defer** until shop floor explicitly asks. |
| Persist `barcode_image` URL on Console doc? | Allows reprints after the fact | **Yes, easy win** — store the `barcode_image` field already on `Console Transaction Log` onto `Console Master Batch Mixing` too. Small additive change. |
| Mark `01_WAVE1.md` historical and link to this cockpit? | Source-of-truth confusion | **Yes** — update with header banner pointing to cockpit. |
| Add monitoring on unmatched `operation` value-map keys? | Catch the silent `"Compound"` default | **Yes, as part of monitoring epic** — emit `frappe.log_error` whenever default fires. |
| Empirically trace the MB-specific SE creation chain on legacy and add it to `05-legacy-erpnext.md`? | Hermes workers need this if they ever modify legacy MB path | **Yes, before any legacy-side change.** Run the diagnostic script in `05-legacy-erpnext.md` against a fresh staging submission, capture the call chain, update the spec. |

## When in doubt — pause and ask

This spec is intentionally **not exhaustive** about the legacy side's
internal mechanics. The legacy custom app is 100+ doctypes and has
historical wiring that isn't fully captured here. Hermes workers who
need to modify legacy behavior should:

1. Read this spec end-to-end first
2. Run graphify queries on `shree_polymer_custom_app` for the specific
   function chain they need to change
3. Surface a proposal in the Kanban card BEFORE coding
4. Wait for Reviewer worker + you to sign off

The cost of asking is one turn; the cost of an unauthorised legacy change
that breaks downstream Compound Inspection is hours of recovery on
production-staging.
