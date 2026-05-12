# Blanking DC Entry - Specification

**Status:** SPEC WRITTEN, but **not staging/prod shipped** per production overseer clarification on 2026-05-12. Schema/Dash/local-create observations exist, but callback routing and Ops-vs-Legacy semantics need verification.
**Console doctype:** `Console Blanking DC Entry` (`BDC-.YYYY.-`) + `Console Blanking DC Item`
**Legacy doctype:** `Blanking DC Entry` (`BDCE-.#####`) + `Blanking DC Item`
**Ops handler:** dedicated `submit_blanking_dc_entry(context)`

> Read [`../master-batch-mixing/`](../master-batch-mixing/) for shared orchestration. This spec documents Blanking DC Entry deltas and drift.

## What's substantively different about Blanking DC Entry

| Aspect | Blanking DC Entry | Bulk Clip Release | Cut Bit Transfer |
|---|---|---|---|
| Business motion | Clip material enters a blanking bin | Clip mapping is released | Material moves to Cutbit warehouse |
| Main physical object | Blanking Bin asset | Sheeting Clip | Clip/Bin asset |
| Console side effect | Creates `Console Item Bin Mapping`; deducts clip mapping qty | Retires clip mapping | Retires/reduces bin mapping |
| Legacy side effect | Creates `Item Bin Mapping` + `Asset Movement` | Retires clip mapping | Creates CBT + Stock Entry |
| Ops side effect | Stock Entry transfer Cutbit -> PreForming | Mapping retirement | Repack Stock Entry |
| Primary risk | Ops semantics differ from Legacy/Dash clip flow | Routing drift | Batch resolution |

## Deltas at a glance

| Layer | Same as MB? | Delta |
|---|---|---|
| 01-business-context | No | Converts released clip material into bin mapping for blanking |
| 02-frontend-dash | No | Three-step scan: clip -> bin -> gross weight |
| 03-console-backend | Mostly | Local create exists, but callback routing omits BDE |
| 04-bridge-layer | No | `populate_blanking_dc_fields` rebuilds rows and resolves bin Asset |
| 05-legacy-erpnext | No | Legacy `on_submit` creates Item Bin Mapping + Asset Movement |
| 06-ops-erpnext | No | Dedicated Stock Entry handler consumes `CB_<compound>_<spp_batch>` from Cutbit WH |
| 07-end-to-end-flow | Mostly | Parallel legs have different business effects |
| 08-test-plan | Same shape | Must test routing, batch semantics, bin/clip side effects |
| 09-rollout-history | Wave 2 | Docs/plans still mention branches not present in current Dash |
| 10-risks-decisions | Major | Callback signature and Ops-vs-Legacy semantic drift |

## Files in this folder

| File | What it covers |
|---|---|
| [01-business-context.md](01-business-context.md) | Shop-floor meaning, clip/bin transition, roles |
| [02-frontend-dash.md](02-frontend-dash.md) | `BlankingDCEntry.tsx`, scan state, payload |
| [03-console-backend.md](03-console-backend.md) | Validators, local create, bin/clip side effects, callback drift |
| [04-bridge-layer.md](04-bridge-layer.md) | Mapping seeder, populate function, field-name drift |
| [05-legacy-erpnext.md](05-legacy-erpnext.md) | Legacy controller, Item Bin Mapping, Asset Movement |
| [06-ops-erpnext.md](06-ops-erpnext.md) | Dedicated handler and Stock Entry semantics |
| [07-end-to-end-flow.md](07-end-to-end-flow.md) | Operator submission trace and failure points |
| [08-test-plan.md](08-test-plan.md) | Unit/integration/E2E/UAT checks |
| [09-rollout-and-history.md](09-rollout-and-history.md) | Wave 2 rollout and Hermes boundaries |
| [10-risks-and-decisions.md](10-risks-and-decisions.md) | Drift findings, invariants, decisions |
