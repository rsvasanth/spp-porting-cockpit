# Final Batch Mixing — Specification (delta from Master Batch Mixing)

**Status:** SHIPPED. Same Wave 1 cohort as MB Mixing.
**Console doctype:** `Console Final Batch Mixing` (`FBM-.YYYY.-.#####`)
**Legacy doctype:** `Delivery Challan Receipt` (`inward_material_type = "Compound"`) — ERPNext v15
**Ops doctype:** Generic `Stock Entry` via the MES Transaction Engine

> **Read [`../master-batch-mixing/`](../master-batch-mixing/) first.** FB Mixing is **architecturally identical to MB Mixing across 5 of the 7 layers**: same Dash pattern, same Console backend pattern, same controller (literal byte-for-byte copy of MB's controller with `MASTER_BATCH_MIXING` → `FINAL_BATCH_MIXING`), same Bridge mapping table (literally shares the same `field_mappings` rows seeded by `seed_mixing_process_mapping`), same Ops generic TransactionEngine path.
>
> This spec documents **only the deltas** from MB Mixing. If a layer is not mentioned here, the MB Mixing spec applies verbatim.

## The deltas at a glance

| Layer | Same as MB? | Delta |
|---|---|---|
| 01-business-context | No | FB consumes a previously-created MB + raw materials; produces a "Compound" group item. Different role: still `Mixing Operator` but on a different workstation (Avon Kneader is common). |
| 02-frontend-dash | Mostly | `FinalBatchMixingEntry.tsx`: extra **MB scan** step (operator scans the MB lot's mix barcode first); `allowedItemGroups` defaults to `['Compound']` not `['Master Batch']`. |
| 03-console-backend | **Yes** | `create_local_final_batch_mixing` is a literal copy of `create_local_master_batch_mixing` with `process_code` swapped. Controller is byte-identical. Refer to MB spec. |
| 04-bridge-layer | **Mostly** | Same `Legacy Sync Mapping` field_mappings (literally shared via `_upsert_mapping` calls for both process_codes). **Value-map output differs:** `"Final Batch Mixing"` → `"Compound"` (not `"Master Batch"`). |
| 05-legacy-erpnext | **NO — major** | This is THE FB-specific story. Legacy DCR's `validate_final_batches` returns **True** for FB (not False like MB), triggering `create_wo` → `create_wo_final_batch_mixing` → `make_stock_entry_final_batch`. This is a 200+ line legacy code path that doesn't exist for MB. |
| 06-ops-erpnext | **Yes** | Same generic TransactionEngine path. No FB-specific Ops code. |
| 07-end-to-end-flow | Mostly | Same flow + an extra prerequisite step (MB lot must already exist on legacy + ops with matching `mix_barcode`). |
| 08-test-plan | Mostly | Same 3 unit tests with FB doctype names. Extra test recommended: BOM validation (FB has stricter BOM check than MB). |
| 09-rollout-history | Same wave | Shipped together with MB; the Compound Deviation saga affected both |
| 10-risks-decisions | Different list | FB has its own decisions: BOM strictness, multi-BOM rejection, workstation auto-resolution |

## Files in this folder

| File | What it covers |
|---|---|
| [01-business-context.md](01-business-context.md) | FB-specific shop-floor meaning, MB-input prerequisite |
| [02-frontend-dash.md](02-frontend-dash.md) | Dash deltas (MB scan, allowed item groups) |
| [03-console-backend.md](03-console-backend.md) | "Same as MB" pointer + literal-copy proof |
| [04-bridge-layer.md](04-bridge-layer.md) | Shared mapping, different value-map output |
| [05-legacy-erpnext.md](05-legacy-erpnext.md) | **The FB-specific deep dive** — `validate_final_batches` → `create_wo_final_batch_mixing` → `make_stock_entry_final_batch` |
| [06-ops-erpnext.md](06-ops-erpnext.md) | Pointer to MB spec; no Ops delta |
| [07-end-to-end-flow.md](07-end-to-end-flow.md) | Narrative with MB-prerequisite step |
| [08-test-plan.md](08-test-plan.md) | FB unit tests + recommended additions |
| [09-rollout-and-history.md](09-rollout-and-history.md) | Deploy notes |
| [10-risks-and-decisions.md](10-risks-and-decisions.md) | FB-specific open questions |
