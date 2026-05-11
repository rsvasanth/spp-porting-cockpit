# 10 - Risks and decisions

## Cut Bit-specific plan-vs-reality deltas

| # | Delta | Plan / older docs implied | Reality on disk | My recommendation |
|---|---|---|---|---|
| 1 | Ops execution | Generic Transaction Engine can handle all stock processes | CBT routes to dedicated `submit_cut_bit_transfer` | **Keep** - asset retirement and batch creation are process-specific |
| 2 | Legacy sync from Ops | Dedicated handler may call Bridge directly | Console path passes `run_legacy_sync=False` | **Keep** - prevents duplicate Legacy CBT |
| 3 | Clip mapping side effect | Existing test names say CBT creates clip mappings | Current helper skips clips; only bins are retired/reduced | **Fix tests/docs, not code**, unless production wants clip retirement here |
| 4 | Legacy idempotency | `reference_id` should be enough | Legacy CBT has no stable reference field; Bridge uses barcode + 10 min | **Accept but monitor** |
| 5 | Native batch source | Dash validation can submit enough info | Console-local validation can return empty native batch; wrapper relays at submit | **Keep** |
| 6 | Child SPP batch field | Mapping expects `items.spp_batch_no` | Dash/Console use `spp_batch_number` | **Test and patch mapping if legacy child needs it** |

## Cross-system invariants Hermes must not break

| # | Invariant | Where enforced | Breaks if... |
|---|---|---|---|
| 1 | Console path must not double-call Legacy | Ops `process_transaction` passes `run_legacy_sync=False` | Handler default is used from Console dispatch |
| 2 | Target batch convention is `Cutbit_<item_code>` | Ops and Legacy Stock Entry target rows | Batch naming changes |
| 3 | Target mix barcode is `CB_<item_code>` | Ops and Legacy target rows | Downstream recycling lookup changes |
| 4 | `clip_name` carries scanned barcode to Bridge | Dash payload + Bridge flattening | Frontend stops sending `clip_name` |
| 5 | Legacy batch resolution fails loud | `populate_cutbit_fields` | Fallback silently picks latest wrong batch |
| 6 | Clips are not retired by CBT in Console | `_write_clip_mappings_for_cut_bit` | Someone "fixes" helper name by retiring clips |
| 7 | Bins can be partially consumed | Console helper + Legacy controller | Always-retire behavior replaces qty reduction |

## Operational risks

| Risk | Likelihood | Impact | Existing mitigation |
|---|---|---|---|
| Duplicate Legacy CBT from Ops direct sync | Low after hardening | High | `run_legacy_sync=False` dispatch |
| Legacy idempotency false positive within 10 min | Low | Medium | Uses first scanned barcode and short window |
| Legacy idempotency false negative after 10 min retry | Medium | Medium | Operator likely retries immediately; no stable field available |
| Wrong Legacy batch selected by fallback IBSB lookup | Low/Medium | High | Exact `mix_barcode` lookup tried first; fail-loud if unresolved |
| Console tests drift from current helper behavior | High | Medium | This spec flags it; tests should be updated |
| Legacy child `spp_batch_no` blank due field-name drift | Medium | Medium | Batch resolution may hide it; add Bridge test before changing |
| Clip remains active longer than expected | Medium | Medium | Business rule says Blanking retires clips |
| Bin qty drift between Console and Ops/Legacy | Medium | Medium | Impact callbacks and stock sync update local state |

## Decisions waiting on production overseer

| Question | Trade-off | My recommendation |
|---|---|---|
| Should CBT retire clips on Console, or keep deferring to Blanking? | Retiring early tightens inventory but can break multi-batch clip use | **Keep deferring to Blanking** unless floor confirms clips are single-use at CBT |
| Should Legacy `Cut Bit Transfer` get a real reference field? | Cleaner idempotency, but requires legacy schema change | **Yes later**, not during spec wave |
| Should stale Console tests be corrected now? | Better safety, but this cockpit task is docs-only | **Yes in a separate code/test task** |
| Should `source_warehouse="PreForming - SPP"` in Console bin validation be aligned with Ops `Unit-2 - SPP`? | Consistency vs current production behavior | **Investigate before changing** |

## My opinion

The highest-risk area is not the repack itself; it is identity drift between four names for the same physical thing: scan barcode, clip/bin doctype name, mapping row name, and native batch. The current implementation is appropriately defensive in Bridge and Ops. The weak point is documentation/test drift around clip retirement, which can mislead a future worker into making the wrong "cleanup."
