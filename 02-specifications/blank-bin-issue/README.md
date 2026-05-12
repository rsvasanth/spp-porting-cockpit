# Blank Bin Issue — Specification

**Status:** SPEC WRITTEN / LEGACY-SITE DERIVED, but **not staging/prod shipped in Console** per production overseer clarification on 2026-05-12.
**Legacy DocType:** `Blank Bin Issue` (`PE-.#####`) + `Blank Bin Issue Item`.
**Console process target:** `BLANK_BIN_ISSUE` (not present on current `develop`; no live `iyyanarr/shree_polymer_console` BBI branch was visible on 2026-05-12).
**Ops target:** No verified dedicated Ops handler. Ops Work Planning code only checks BBI as a downstream cancellation blocker.

> Read [`../master-batch-mixing/`](../master-batch-mixing/) for shared orchestration. This spec documents the BBI process gap and the legacy behavior that a Console port must preserve.

## What BBI does

Blank Bin Issue assigns a filled physical bin to a moulding Job Card/Lot. It is a logical reservation, not a stock movement. Moulding Production Entry later reads open BBI child rows where `is_completed = 0`, consumes the bin material, and marks the BBI item complete.

## Deltas at a glance

| Layer | Current reality |
|---|---|
| Legacy | Fully live; 68,078 records on `spp15.local`, 67,309 submitted. |
| Console develop | No `Console Blank Bin Issue` DocType, no Dash component, no local create, no mapping. |
| Console branch evidence | A stale local Console remote-tracking ref/commit showed `BlankBinIssueEntry.tsx` and dummy validation functions, but the live `iyyanarr/shree_polymer_console` remote only exposed `develop` when checked on 2026-05-12. Do not treat this as a current Console branch. |
| Bridge | No verified `BLANK_BIN_ISSUE` mapping or populate function. |
| Ops | No submit handler; planning cancellation guards query `Blank Bin Issue`. |
| Downstream | MPE requires submitted BBI open rows and later marks them completed. |

## Files

| File | What it covers |
|---|---|
| [01-business-context.md](01-business-context.md) | Shop-floor purpose and position before MPE |
| [02-frontend-dash.md](02-frontend-dash.md) | Legacy Desk UX plus branch prototype drift |
| [03-console-backend.md](03-console-backend.md) | Current Console gap and target local-create contract |
| [04-bridge-layer.md](04-bridge-layer.md) | Missing Bridge mapping and required legacy field contract |
| [05-legacy-erpnext.md](05-legacy-erpnext.md) | Legacy schema, validation, and MPE dependency |
| [06-ops-erpnext.md](06-ops-erpnext.md) | Ops gap and cancellation guard evidence |
| [07-end-to-end-flow.md](07-end-to-end-flow.md) | End-to-end trace from lot scan to MPE completion |
| [08-test-plan.md](08-test-plan.md) | Tests for legacy parity, Console gap, and future port |
| [09-rollout-and-history.md](09-rollout-and-history.md) | Current shipment boundary and branch history |
| [10-risks-and-decisions.md](10-risks-and-decisions.md) | Drift findings and decisions |
