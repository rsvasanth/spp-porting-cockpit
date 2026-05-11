# Sheeting Process — Specification

**Status:** SHIPPED. Wave 1 cohort.
**Console doctype:** `Console Sheeting Process` (`CSHT-.YYYY.-.#####`) + 2 children (`Console Sheeting Item`, `Console Sheeting Clip`)
**Legacy doctype:** `Material Transfer` (a **distinct legacy doctype**, NOT a Stock Entry subtype) — ERPNext v15
**Ops doctype:** Generic `Stock Entry` via the MES Transaction Engine (no dedicated Ops handler)

> Read [`../master-batch-mixing/`](../master-batch-mixing/) first for shared layers. This spec documents Sheeting's deltas.

## What's substantively different about Sheeting

| Aspect | Sheeting | MB / FB Mixing | Compound Deviation |
|---|---|---|---|
| Legacy doctype | `Material Transfer` (custom legacy doctype) | `Delivery Challan Receipt` (DCR) | `Compound Inspection` |
| Bridge field_mappings | Populated (header + 2 child tables) | Populated (shared MB+FB rows) | Empty (all Python) |
| Bridge populate function | Short — defaults only | None (mapping engine does all work) | Long — delegates to shared helpers |
| Child tables | Two (`batches` + `sheeting_clip` on legacy) | One (`dc_items`) | None |
| Ops dedicated handler | No (generic engine) | No (generic engine) | No (generic engine) |
| Special Console post-processing | `_write_clip_mappings_for_sheeting` runs after `_safe_local_create` | None | None |
| `apply_bridge_result` extras | Captures `legacy_spp_batch_no` kwarg + triggers `_backfill_ops_reference_for_sheeting` on Ops Success | Standard 5-step | Standard 5-step |

## Deltas at a glance

| Layer | Same as MB? | Delta |
|---|---|---|
| 01-business-context | No | Compound → sheets → clips workflow; 2 different output paths (clips + cut-bits) |
| 02-frontend-dash | Mostly | `SheetingProcessEntry.tsx`: scans compound input, produces multiple clips with auto-numbered barcodes |
| 03-console-backend | Mostly | `create_local_sheeting_process` reads `ctx.items` (not `consumption_items`); calls `_write_clip_mappings_for_sheeting` post-insert. Controller's `apply_bridge_result` has the `legacy_spp_batch_no` and `impacted_clips` kwargs |
| 04-bridge-layer | **No — major** | Different legacy doctype (`Material Transfer`); two child-table mappings (`batches` + `sheeting_clip`); item extraction logic synthesizes legacy barcode format `{item_code}_{original_batch}` |
| 05-legacy-erpnext | No | `Material Transfer` doctype semantics; `material_transfer_type` field; `cutbit_qty` aggregation; the `is_cut_bit_item` flag pattern |
| 06-ops-erpnext | Mostly | Generic engine; clip tracking via `impacted_clips` response |
| 07-end-to-end-flow | Mostly | Different terminal documents (Material Transfer on legacy, not DCR + SE) |
| 08-test-plan | Same shape | Plus tests for clip mapping creation, cut-bit flag detection |
| 09-rollout-history | Same wave | Shipped together with other Wave 1 |
| 10-risks-and-decisions | Different | `material_transfer_type` hardcode, `cutbit_qty` aggregation drift, clip-mapping write race |

## Files in this folder

| File | Lines target | What it covers |
|---|---|---|
| [01-business-context.md](01-business-context.md) | ~110 | Sheeting workflow, clip vs cut-bit dual output, position in chain |
| [02-frontend-dash.md](02-frontend-dash.md) | ~150 | Component flow, multi-clip output handling, barcode auto-numbering |
| [03-console-backend.md](03-console-backend.md) | ~150 | `create_local_sheeting_process` + `_write_clip_mappings_for_sheeting` + the apply_bridge_result extras |
| [04-bridge-layer.md](04-bridge-layer.md) | ~180 | Two child tables, item extraction with barcode synthesis, the Sheeting-only branch in `sync_process_transaction` |
| [05-legacy-erpnext.md](05-legacy-erpnext.md) | ~150 | Material Transfer doctype, populate_sheeting_fields, cutbit_qty aggregation |
| [06-ops-erpnext.md](06-ops-erpnext.md) | ~70 | Generic engine + clip tracking via response |
| [07-end-to-end-flow.md](07-end-to-end-flow.md) | ~140 | Trace narrative with clip-mapping writes |
| [08-test-plan.md](08-test-plan.md) | ~140 | Including clip mapping + cut-bit flag tests |
| [09-rollout-and-history.md](09-rollout-and-history.md) | ~90 | Deploy notes |
| [10-risks-and-decisions.md](10-risks-and-decisions.md) | ~100 | Sheeting-specific risks |
