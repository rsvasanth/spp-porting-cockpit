# Bulk Clip Release - Specification

**Status:** SPEC WRITTEN, but **not staging/prod shipped** per production overseer clarification on 2026-05-12. Schema/controller observations exist, but orchestration path has routing drift to verify.
**Console doctype:** `Console Bulk Clip Release` (`CBCR-.YYYY.-.#####`) + `Console Clip Release Item`
**Legacy doctype:** `Bulk Clip Release` (`CLIPR-.YYYY.-.#####`) + `Clip Release Item`
**Ops handler:** dedicated `bulk_release_clips(barcodes=clips)`; takes a list, not the full payload.

> Read [`../master-batch-mixing/`](../master-batch-mixing/) for shared orchestration. This spec documents Bulk Clip Release deltas and current drift.

## What's substantively different about Bulk Clip Release

| Aspect | Bulk Clip Release | Cut Bit Transfer | Sheeting |
|---|---|---|---|
| Business motion | Releases occupied clips into blanking-eligible pool | Repack material into Cutbit warehouse | Creates clip mappings |
| Primary state change | `Item Clip Mapping.is_retired = 1` | Stock Entry Repack + bin/clip impact | New active clip mapping |
| Payload shape | `release_data.clips: string[]` | `items[]` objects | `items[]` + `tagged_clips[]` |
| Ops handler signature | `bulk_release_clips(barcodes=clips)` | `submit_cut_bit_transfer(context, run_legacy_sync=False)` | generic engine |
| Legacy behavior | Retires `Item Clip Mapping` rows | Creates CBT + Repack SE | Material Transfer |
| Current risk | Console doctype exists but init routing omits it | Weaker Legacy idempotency | Clip mapping timing |

## Deltas at a glance

| Layer | Same as MB? | Delta |
|---|---|---|
| 01-business-context | No | State-machine step between Sheeting and Blanking |
| 02-frontend-dash | No | Scan list of clips; payload is only barcodes |
| 03-console-backend | **No - drift** | Rich doctype/controller exists, but `initialize_submission` does not create it |
| 04-bridge-layer | Mostly simple | Mapping exists, but direct `bulk_release_clips` helper is the actual release primitive |
| 05-legacy-erpnext | No | Legacy `on_submit` updates `Item Clip Mapping.is_retired` |
| 06-ops-erpnext | No | Dedicated handler takes barcode list only |
| 07-end-to-end-flow | Mostly | Parallel path only works if `process_code` and local routing are correct |
| 08-test-plan | Same shape | Must test routing drift and field-name drift |
| 09-rollout-history | No | Wave 2 schema landed; Dash wiring still needs verification |
| 10-risks-decisions | Major | Split-brain API path and process_type/process_code mismatch |

## Files in this folder

| File | What it covers |
|---|---|
| [01-business-context.md](01-business-context.md) | Clip release meaning, state machine, actors |
| [02-frontend-dash.md](02-frontend-dash.md) | `BulkClipReleaseEntry.tsx`, validation, payload shape |
| [03-console-backend.md](03-console-backend.md) | Console doctype/controller, validation helpers, missing local routing |
| [04-bridge-layer.md](04-bridge-layer.md) | Mapping seeder, direct release helper, child field drift |
| [05-legacy-erpnext.md](05-legacy-erpnext.md) | Legacy doctype and mapping retirement |
| [06-ops-erpnext.md](06-ops-erpnext.md) | Ops dedicated barcode-list handler |
| [07-end-to-end-flow.md](07-end-to-end-flow.md) | Actual intended trace and current failure points |
| [08-test-plan.md](08-test-plan.md) | Unit, integration, E2E, UAT checks |
| [09-rollout-and-history.md](09-rollout-and-history.md) | Wave 2 rollout notes and Hermes boundaries |
| [10-risks-and-decisions.md](10-risks-and-decisions.md) | Drift findings, invariants, open decisions |
