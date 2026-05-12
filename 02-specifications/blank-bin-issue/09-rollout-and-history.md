# 09 — Rollout and history

## Current status

| Area | Status |
|---|---|
| Legacy production process | Live and high volume on `spp15.local`. |
| Console `develop` port | Not found. |
| Console branch check | Live `iyyanarr/shree_polymer_console` remote only exposed `develop` on 2026-05-12; no live BBI branch was visible. |
| Stale local Console evidence | Old local remote-tracking evidence has prototype UI and dummy API helpers only. |
| Custom app branch check | Live `shree_polymer_custom_app` has Bin Issue branches (`Bin-issue`, `Bin-issue-roleback`, `bin-rollback-issue`). |
| Bridge/Ops | No verified BBI target implementation. |
| Staging/prod shipment | Not shipped; shipment boundary is through Sheeting only. |

## Branch history note

Stale Console prototype commit:

| Evidence | Commit note |
|---|---|
| Local remote-tracking ref/commit, not live branch as of 2026-05-12 | `blank bin issue ui and dummy functions in api.py` |

This evidence should be treated as exploration only. It adds a React screen and two scan helper functions, but it does not complete the Console/Bridge/Ops port.

## Rollout sequence for future implementation

| Phase | Work |
|---|---|
| 1 | Create Console local parent/child DocTypes and local create function. |
| 2 | Replace prototype scan helpers with legacy-parity lot/bin validation. |
| 3 | Add Bridge mapping or populate helper for Legacy `Blank Bin Issue`. |
| 4 | Decide Ops representation: custom reservation DocType vs generic log. |
| 5 | Add callback mapping and standard `apply_bridge_result`. |
| 6 | Run MPE integration test: open BBI -> MPE consumption -> child completion. |

## What Hermes can touch

| Safe | Avoid |
|---|---|
| New BBI Console port files in a focused task. | Changing MPE consumption semantics while writing BBI. |
| Tests documenting current missing routes. | Treating BBI as a Stock Entry. |
| Bridge populate/mapping for BBI. | Adding strict duplicate prevention without owner approval. |
