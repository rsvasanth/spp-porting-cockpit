# Cut Bit Transfer - Specification

**Status:** SPEC WRITTEN / SOURCE-VERIFIED, but **not staging/prod shipped** per production overseer clarification on 2026-05-12. Earlier "shipped" wording was incorrect for production status beyond Sheeting.
**Console doctype:** `Console Cut Bit Transfer` (`CBT-.YYYY.-.#####`) + `Console Cut Bit Item`
**Legacy doctype:** `Cut Bit Transfer` (`CBT-.#####`) in `shree_polymer_custom_app`
**Ops document:** dedicated `Stock Entry` Repack via `submit_cut_bit_transfer(context, run_legacy_sync=False)`

> Read [`../master-batch-mixing/`](../master-batch-mixing/) first for shared orchestration. This spec documents only Cut Bit Transfer deltas.

## What's substantively different about Cut Bit Transfer

| Aspect | Cut Bit Transfer | Sheeting | MB / FB Mixing |
|---|---|---|---|
| Business motion | Consolidates reusable material into Cutbit warehouse | Produces sheets/clips from compound | Produces compound batches |
| Scanned asset | Clip or Bin | Compound batch + output clips | Raw materials / DCR inputs |
| Console validation | `validate_cut_bit_asset` checks Console mappings, then Ops, then Legacy | Sheeting scan paths | Stock / mix validation |
| Local post-processing | Retires or reduces Console Bin mappings only; clips are skipped | Creates clip mappings | None |
| Legacy enrichment | Long `populate_cutbit_fields` with warehouse + batch resolution | Short defaults | Mapping engine mostly enough |
| Ops handler | Dedicated `submit_cut_bit_transfer` | Generic engine | Generic engine |
| Duplicate-sync guard | `run_legacy_sync=False` when called through `process_transaction` | n/a | n/a |

## Deltas at a glance

| Layer | Same as MB? | Delta |
|---|---|---|
| 01-business-context | No | Leftover/reusable material moves from Warming/Blanking into Cutbit warehouse |
| 02-frontend-dash | No | Operator scans Clip/Bin barcode; rows are editable by qty before submit |
| 03-console-backend | Mostly | `submit_cut_bit_transfer` normalizes payload and relays native batch numbers before orchestration |
| 04-bridge-layer | **No - major** | `populate_cutbit_fields` resolves legacy batches and 3-way source warehouses |
| 05-legacy-erpnext | No | Legacy controller creates its own Repack Stock Entry on submit |
| 06-ops-erpnext | **No - major** | Dedicated handler creates `Cutbit_<item_code>` batches and returns impacted assets |
| 07-end-to-end-flow | Mostly | Dual Stock Entry creation: one on Ops, one on Legacy |
| 08-test-plan | Same shape | Must cover Clip and Bin paths, duplicate Legacy guard, batch resolution |
| 09-rollout-history | Same wave | Wave 1 audit doctype plus Wave 1.5 dedicated-handler hardening |
| 10-risks-decisions | Different | Test/code drift around clip mappings; legacy idempotency composite key |

## Files in this folder

| File | What it covers |
|---|---|
| [01-business-context.md](01-business-context.md) | Shop-floor meaning, position after Sheeting/Blanking, Clip vs Bin behavior |
| [02-frontend-dash.md](02-frontend-dash.md) | `CutBitTransferEntry.tsx`, scan flow, editable transfer qty, payload shape |
| [03-console-backend.md](03-console-backend.md) | Console wrapper, validation relay, local audit doctype, bin-mapping retirement |
| [04-bridge-layer.md](04-bridge-layer.md) | Mapping rows, flattening, idempotency, `populate_cutbit_fields` |
| [05-legacy-erpnext.md](05-legacy-erpnext.md) | Legacy `Cut Bit Transfer` controller and Stock Entry creation |
| [06-ops-erpnext.md](06-ops-erpnext.md) | Dedicated Ops handler, SABB bypass, `run_legacy_sync=False` |
| [07-end-to-end-flow.md](07-end-to-end-flow.md) | Single operator submission trace |
| [08-test-plan.md](08-test-plan.md) | Unit, integration, E2E, smoke, UAT checks |
| [09-rollout-and-history.md](09-rollout-and-history.md) | What the source/spec shows, what Hermes can touch |
| [10-risks-and-decisions.md](10-risks-and-decisions.md) | Plan-vs-reality deltas, invariants, open decisions |
