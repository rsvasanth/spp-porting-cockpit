# 10 — Risks and decisions

## Sheeting-specific plan-vs-reality deltas

| # | Delta | Plan said | Reality | My recommendation |
|---|---|---|---|---|
| 1 | Mass-balance enforcement | n/a | Dash-side soft check (5% tolerance); backend doesn't enforce | **Keep** — operational pattern is consistent across MB/FB/Sheeting |
| 2 | `cutbit_qty` aggregation location | Plan didn't specify | Bridge's `populate_sheeting_fields` aggregates from `batches` rows | **Keep** — backfill pattern survives payloads from multiple sources |
| 3 | Clip child table on Console | Plan: inline child of Console Sheeting Process | Implemented as separate `Console Item Clip Mapping` doctype | **Keep** — cleaner for downstream scan lookups |
| 4 | Sheeting → Final Batch recycling loop | Not explicit in plan | Cut-bits go back to FB via the same Console Compound Item references | **Document** — currently implicit; should be in cockpit |

## Cross-doctype invariants Hermes must NOT break

| # | Invariant | Where enforced | Breaks if… |
|---|---|---|---|
| 1 | Clip barcode round-trips Console → Ops → backfill into Item Clip Mapping | `_write_clip_mappings_for_sheeting` + `_backfill_ops_reference_for_sheeting` | Either side stops using the same `clip_barcode` field |
| 2 | Cut-bit prefix `"Cutbit_"` triggers `is_cut_bit_item=1` on legacy | `populate_sheeting_fields` loop | Prefix changes, or operator uses a different prefix |
| 3 | Mix barcode synthesis `{item_code}_{original_batch}` for items missing it | `sync_api.py:191` | Format changes — downstream Compound Inspection's strategy 5 misses |
| 4 | Inline clip-mapping write happens BEFORE Bridge calls | `create_local_sheeting_process` | Mapping moved to callback path (BCR-1 regression) |
| 5 | `material_transfer_type = "Transfer Compound to Sheeting Warehouse"` literal | Mapping seeder + populate fallback | Either source changes the string |
| 6 | `legacy_spp_batch_no` captured from Bridge response | Bridge response extraction + Sheeting `apply_bridge_result` kwarg | Bridge stops returning it, or `apply_bridge_result` drops the kwarg |
| 7 | 5-step race-safe pattern | Controller method | Pattern simplified |

## Operational risks

| Risk | Likelihood | Impact | Existing mitigation |
|---|---|---|---|
| Clip barcode collision (operator submits same input compound twice) | Low | Medium — second submission's clip barcodes overlap with first | `reference_id` unique constraint blocks; operator gets clean error |
| Cut-bit batch not properly recycled back to FB | Low | Medium — cut-bit material orphaned in inventory | Cut-bit batches show up in Compound stock; FB scan validates |
| Item Clip Mapping race (downstream scan before mapping written) | **Was real before BCR-1** | High | BCR-1 fix: inline write at create time |
| Mass-balance soft check skipped (payload bypass) | Low | Medium — output qty drift on stock ledger | Stock Ledger reconciliation catches; no automated alert |
| `cutbit_qty` mismatch (Bridge backfill fails to detect prefix) | Low | High — legacy validation fails, submission fails | Multiple detection paths (prefix + explicit flag); fail-loud on miss |
| Race in `apply_bridge_result` with new kwargs | Low | Medium — `legacy_spp_batch_no` or clip backfill lost | 5-step pattern handles aggregation race; kwargs ride in step 1 (before race-prone aggregate) |
| WAREHOUSE_MAP hardcoded fallback masks misconfig | Medium | Medium — wrong source/target warehouse on legacy | No active monitoring |

## Decisions deferred to a later wave

### Document the cut-bit recycling loop

Cut-bits from Sheeting feed back into Final Batch Mixing. Currently:
- Cut-bits get `is_cut_bit_item=1` on legacy
- FB Mixing's Dash can scan a cut-bit barcode as a raw material input
- Identity links: cut-bit batch (`Cutbit_C_*`) → original compound's batch

**Recommend:** add a dedicated section in cockpit's `01-requirements/`
or `03-context/` documenting this loop. Not a code change, just docs.

### `_backfill_ops_reference_for_sheeting` retry handling

Currently the function logs but doesn't retry if the Item Clip Mapping
record can't be updated (e.g. DB lock). Same risk as other inline writes.

**Recommend:** add structured error log + manual retry script. Low
priority — the failure surface is narrow.

### Cut-bit qty traceability beyond Sheeting

When cut-bits are consumed in downstream FB Mixing, the parent FB
Mixing's `consumption_items` row points to the cut-bit batch but not
explicitly to its source Sheeting submission. To trace "this FB mixing
consumed cut-bits from which Sheeting?", you have to walk through the
batch number's prefix.

**Recommend:** defer — only matters for forensic analysis. Add a
`source_sheeting_reference_id` field on FB child rows if reports
require it.

## Questions waiting on production overseer

| Question | My recommendation |
|---|---|
| Add monitoring on `_backfill_ops_reference_for_sheeting` failures? | **Yes**, as part of monitoring epic |
| Add monitoring on WAREHOUSE_MAP fallback frequency? | **Yes**, same epic |
| Add explicit `source_sheeting_reference_id` to FB child rows for cut-bit traceability? | **Defer** until reports need it |
| Move auto-numbering from Dash to backend? | **No** — Dash generation is fast, backend generation introduces a Console-side state machine for sequence numbers |
| Document the cut-bit recycling loop in cockpit `03-context/`? | **Yes** — small effort, high doc value |
