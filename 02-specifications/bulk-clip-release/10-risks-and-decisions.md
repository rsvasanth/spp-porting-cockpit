# 10 - Risks and decisions

## Plan-vs-reality deltas

| # | Delta | Plan / expectation | Reality on disk | Recommendation |
|---|---|---|---|---|
| 1 | Process key | Wave 2 said Dash must submit `process_code` | Dash sends `metadata.process_type` | **Fix Dash/test in separate task** |
| 2 | Local audit | Console doctype implies local audit row | No `create_local_bulk_clip_release` branch/function | **Add wiring in separate task** |
| 3 | Callback routing | Controller has BCR `apply_bridge_result` | `update_local_domain_record` omits BCR | **Add routing in separate task** |
| 4 | Bridge child mapping | Seeder should match Legacy child fields | Maps to `sheeting_clip`/`barcode`; Legacy has `clip_name`/`clip_barcode` | **Test and patch mapping** |
| 5 | Barcode identity | Helpers should handle physical barcode vs doc name | Bridge direct helper filters `sheeting_clip IN barcodes` | **Resolve barcode to clip name before update** |

## Invariants

| # | Invariant | Breaks if... |
|---|---|---|
| 1 | Scan validation must use active mapping | Already-released clips can be released twice |
| 2 | Console/Ops/Legacy must retire the same physical clips | Barcode/doc-name drift is ignored |
| 3 | BCR must not create stock entries | Handler gets replaced with generic stock action |
| 4 | Local mirror retirement timing must be explicit | Dash accepts stale active clips |
| 5 | `release_data.clips[]` remains the canonical handler input | Handler starts expecting full payload without wrapper |

## Operational risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Dash submit fails before logs | High if current TSX is deployed | High | Add `process_code` test |
| Console audit row missing | High | Medium/high | Add local create path |
| Ops/Legacy retire but Console mirror stays active | Medium | High | Callback routing or direct mirror update must be tested |
| Bridge direct helper misses barcode-text scans | Medium | High | Resolve barcode to clip doc name |
| Legacy document path creates bad child rows | Medium | Medium | Fix mapping or use populate function |

## Decisions waiting on production overseer

| Question | Trade-off | My recommendation |
|---|---|---|
| Should BCR use rich Console doctype path or direct relay helper? | Auditability vs simplicity | **Use rich doctype path**; fix wiring |
| Should local mirror retire immediately or after Legacy ack? | Fast UX vs cautious cross-system truth | **After Legacy ack** until Legacy retirement is complete |
| Should Bridge create legacy BCR documents or call direct helper? | Audit trail vs fewer moving parts | **Create documents** if mapping is fixed; direct helper only as fallback |

## My opinion

Bulk Clip Release is the least cockpit-clean process so far. The business logic is simple, but the wiring drift is not. I would not let Hermes treat this as a solved port until a focused code/test pass proves the Dash payload, Console audit doctype, Bridge mapping, and barcode identity all line up.
