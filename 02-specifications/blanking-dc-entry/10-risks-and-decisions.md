# 10 - Risks and decisions

## Plan-vs-reality deltas

| # | Delta | Plan / expectation | Reality on disk | Recommendation |
|---|---|---|---|---|
| 1 | Callback routing | local BDE should receive target callbacks | `update_local_domain_record` omits `BLANKING_DC_ENTRY` | **Fix with tests** |
| 2 | Callback signature | shared `apply_bridge_result(target,status,remote,error)` | BDE controller defines `apply_bridge_result(intent,target,status,payload)` | **Fix signature before routing** |
| 3 | Ops semantics | BDE is clip -> bin / Asset Movement | Ops creates Cutbit -> PreForming Stock Entry | **Architectural decision needed** |
| 4 | Mapping seeders | one source of truth | Console seeder has field mappings; Bridge seeder says populate-only | **Prefer populate-only or test both** |
| 5 | Plan branch | `move_to_cut_bit_warehouse` branch | not in current BDE Dash/source | **Treat as Blank Bin Inward scope unless confirmed** |

## Invariants

| # | Invariant | Breaks if... |
|---|---|---|
| 1 | Net weight = gross - tare | UI/backend drift |
| 2 | Bin must not already have active mapping | duplicate bin contents |
| 3 | Clip qty must not go negative | over-consumption |
| 4 | Item Bin Mapping is downstream source of truth | fields change silently |
| 5 | Legacy Asset Movement must match physical bin movement | bin location becomes untrustworthy |

## Operational risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Local audit never updates sync status | High today | Medium | callback map + signature fix |
| Ops leg fails due missing `CB_` Cutbit batch | Medium/high | High | decide process semantics |
| Console allows BOM-incompatible item | Medium | Medium | add Console BOM validation or rely on Legacy failure |
| Mapping seeder creates partial wrong rows | Low/medium | Medium | populate clears rows; test it |
| Clip partial consumption mismatch across sites | Medium | High | assert qty after each leg |

## Decisions waiting on production overseer

| Question | Trade-off | My recommendation |
|---|---|---|
| Should Ops BDE model Stock Entry or process-master/bin mapping? | ledger purity vs matching Legacy/Dash | **Align Ops to actual floor story before expanding** |
| Should Console validate BOM at scan time? | earlier feedback vs needing reliable Console BOM | **Yes, if Console BOM data is trustworthy** |
| Should Console seeder remove BDE field mappings? | simpler mapping vs backward compatibility | **Defer until Bridge tests prove populate-only path** |

## My opinion

Blanking DC Entry has the right local UI and process-master behavior, but the target semantics are split. I would fix callback routing first, then make an explicit Ops decision. Quietly letting Ops consume `CB_` Cutbit batches while the operator is scanning sheeting clips is too easy to misread later.
