# 10 — Risks and decisions

## Plan-vs-reality deltas

| # | Delta | Plan said | Reality (planned) | Recommendation |
|---|---|---|---|---|
| 1 | Lot # generation authority | Pattern A vs B open question | Pattern A locked | **Keep Pattern A** — Charter Principle 1 |
| 2 | WO + JC chaining mechanism | Bridge sequence engine cross-step references OR single whitelisted method | Single whitelisted method preferred (simpler, atomic) | **Use whitelisted method** |
| 3 | Lot # gapless sequence | Plan implied gapless | Implementation may have rare gaps on failure | **Tolerate occasional gaps; documented** |
| 4 | DB-level unique constraint on Lot # | Not explicit | Recommended for race-safety | **Yes, add at implementation time** |
| 5 | Ops Work Order Lot # custom field | Plan didn't address | Required for cross-system identity round-trip | **Yes, custom field at Wave 3 deploy** |
| 6 | Work Planning collapse | Earlier cockpit text collapsed Work Planning + Add On | Legacy business rules differ: Work Planning enforces one per shift; Add On does not | **Do not collapse** — keep separate process identities |

## Cross-doctype invariants Hermes must NOT break

| # | Invariant | Where enforced | Breaks if… |
|---|---|---|---|
| 1 | Console-authored Lot # honored by Legacy | Legacy `before_insert` controller modification | Legacy regenerates Lot # despite Console value |
| 2 | Lot # cascades to all child rows | Console controller `validate` | Child rows have inconsistent `lot_number` |
| 3 | Lot # uniqueness within day | DB-level constraint + sequence generation | Collision; downstream BBI confused |
| 4 | Atomic WO + JC creation | `create_planning_with_jobcards` rollback | Partial state on Legacy |
| 5 | Workstation override silent on Legacy, transparent on Console Dash | Bridge + Dash | Inconsistent — operator confusion |
| 6 | Custom field `lot_number` on Ops Work Order + Job Card | ERPNext customization | Cross-system identity broken |
| 7 | 5-step race-safety pattern | Controller | Saga regression |
| 8 | Add On remains supplemental | Legacy Add On does not call duplicate-shift validator | Add On starts blocking base-shift duplicates like Work Planning |

## Operational risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Concurrent Lot # collision | Low (with DB constraint) | High — submission failure | DB unique constraint + retry |
| Lot # gap on failure | Medium | Low — operationally tolerated | Gap explained in change log |
| Multi-BOM not rejected on Console (only Legacy) | Medium | Medium | Mirror legacy check in Console controller |
| Stale `Console Work Plan Item Target` data | Medium | Low — soft warning only | Operational responsibility |
| Workstation override surprises operator | Medium | Low — operational training | Pre-submit transparency banner |
| Ops `for_each` engine capability missing | Low | Medium — fallback to explicit listing | Verify engine support before Wave 3 ship |

## Decisions deferred

### Lot # gap handling

If a Lot # is generated and then the Console doc fails to insert (DB constraint violation, validation failure):
- Counter "wastes" that sequence number
- Gap appears in the day's Lot # sequence

**Recommendation:** Tolerate occasional gaps. They're rare and visible. Building a recovery mechanism (compact-fill the gap on next submission) adds complexity for low benefit.

### Multi-MPE Lot # support (cross-motion)

Per Moulding Production Entry's MPE batch-generation rules: one Lot # may have multiple MPE submissions, but the exact batch_no format must follow the legacy `generate_batch_no` contract rather than an invented fixed string pattern.

This means AOWP's Lot # gets reused across multiple MPEs within the same lot. AOWP doesn't need to know about this; the MPE motion handles the cascading sequence.

### `Console Lot Number Generation Log` doctype

Optional. Provides audit of every Lot # generated:
- generated_value
- submission_reference_id
- generation_timestamp
- generating_user
- success_or_gap

**Recommendation:** Implement at Wave 3 for forensic capability. Low effort, high value.

## Questions waiting on Production Overseer

| Question | Recommendation |
|---|---|
| DB-level unique constraint on Lot #? | **Yes** — race-safety |
| `for_each` action in TransactionEngine — capability verified? | **Verify before Wave 3 ship** |
| Custom field on Ops Work Order + Job Card? | **Yes** — Pattern A cross-system round-trip |
| `Console Lot Number Generation Log` doctype? | **Yes** — implement at Wave 3 |
| Add planning amendment UI later? | **No, defer indefinitely** — re-plan or add-on plan should be a new submission |
| Tighten validation_dispatch_method failure handling | n/a here — AOWP doesn't use validation dispatch |

## Correction log

On 2026-05-12, the production overseer clarified that production planning starts with Work Planning, and Work Planning is one per shift. Direct Legacy code review confirmed the distinction. This Add On spec is now scoped to supplemental Add On Work Planning only.
