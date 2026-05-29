# 06 - Ops ERPNext

> Status updated 2026-05-29. Prior versions of this file described a `submit_blanking_dc_entry(context)` dedicated handler and a Cutbit→PreForming Stock Entry creation path. **Both are stale**: no such function exists in `shree_polymer_ops/api.py` and no template action creates a Stock Entry for BDE. See the Change Note at the bottom of this file.

> Read [`../master-batch-mixing/06-ops-erpnext.md`](../master-batch-mixing/06-ops-erpnext.md) for the generic TransactionEngine pattern. **Blanking DC Entry now runs on the generic engine** — no dedicated handler.

## Dispatch

`shree_polymer_ops/api.py::process_transaction` has zero process-specific branches. It instantiates `TransactionEngine` and calls `execute()`. There is no `elif process_code == "BLANKING_DC_ENTRY"` — that code was deleted along with the `submit_blanking_dc_entry` function before May 2026.

## Console Process Template — BLANKING_DC_ENTRY

The active template on `sppconsole-dev.local` declares two actions:

| # | action | target_doctype | Purpose |
|---|---|---|---|
| 1 | `create_doc` | `Asset Movement` | Move scanned bins from `from_location` to SPP Settings `to_location` |
| 2 | `call_method` | `Legacy Sync Mapping` | Trigger the Bridge populate leg |

That's the entire Ops side. No Item Bin Mapping write, no Stock Entry, no Work Order. Bin mapping lives in Console (`Console Item Bin Mapping`); legacy site mirror is written by the Bridge via `populate_blanking_dc_fields`.

## Why declarative Asset Movement creation works

When the engine executes `create_doc → Asset Movement`, two helper hooks fire automatically inside `_create_doc` ([api.py:758-766](../../apps/shree_polymer_ops/shree_polymer_ops/api.py:758)):

```python
if doc.doctype == "Asset Movement":
    self._prepare_asset_movement_reference(doc, params)
    self._normalise_asset_movement_locations(doc)
    if not doc.get("assets"):
        return {"status": "Skipped", "message": "No asset movement required"}
```

| Helper | Role |
|---|---|
| `_prepare_asset_movement_reference` | Sets `reference_doctype` / `reference_name` for the dynamic link; nulls them if the doctype doesn't exist locally (so Console-only doctypes don't break Ops insert) |
| `_normalise_asset_movement_locations` | For each row: reads `Asset.location` and uses it as `source_location`; **skips rows where source == target** (matches legacy LR-BDE-19/20 semantics) |

These are doctype-quirk handlers, not process_code-specific branches. They're the reason the BDE template can stay declarative (one `create_doc` action) instead of needing custom Python — they implement the legacy "read current bin location per row, skip no-ops" rule generically for any Asset Movement payload.

## What Ops produces per BDE submission

| Output | When |
|---|---|
| `Asset Movement` (submitted) | Always, unless every row had `source_location == target_location` after lookup |
| `MES Transaction Log` row | Always — engine-internal audit |
| Stock Ledger Entry / Bin / Batch | None — BDE moves the physical asset's location only, not stock |
| `Item Bin Mapping` | **Never on Ops** — that's Console-state (`Console Item Bin Mapping`) and Legacy-mirror (Bridge writes it on the legacy site) |
| `Stock Entry` | **Never** — the historical "Cutbit → PreForming SE" path is gone |

## Idempotency

Inherited from `TransactionEngine`:
- Each submission carries a `reference_id` (Console-generated)
- Engine checks `Shree Polymer MES Log` for `reference_id + status=Success`; on hit, returns the cached `result_payload` without re-creating anything
- Retried submissions therefore don't create duplicate Asset Movements

## Response shape

Standard engine response. The relevant fields Console reads on the callback:

| Field | Meaning |
|---|---|
| `status` | `Success` / `Failed` |
| `log_name` | `Shree Polymer MES Log.name` (Ops) |
| `reference_name` | Same as `log_name` (the Console callback uses this as the `ops_reference` on the parent record) |
| `results.<step_store_as>` | Step output dict; for the Asset Movement step it includes `.name` |
| `impacted_balances` | Empty for BDE (no stock movement) |

## Asset master prerequisite

For Console to emit a complete Asset Movement payload (correct `source_location`, `bin_weight` validation, etc.), Console needs the bin's full Asset record locally. That sync is now in place:
- Ops `get_assets(last_sync_time)` returns `Asset` rows filtered to `asset_category in ("Blanking Bin", "Mould")`
- Console `_sync_assets` upserts them into `Console Asset` with `bin_weight`, `location`, `asset_category`
- `Asset.on_update` push-notifies Console so location changes propagate in realtime

Before Asset sync shipped (May 2026), Console used a lazy stub at `api.py:5798` that inserted empty Console Asset rows. That code path has been removed; missing-asset cases now log a warning instead of fabricating data.

## What Hermes workers can safely change

| Change | Risk |
|---|---|
| Add a new `create_doc` action to the BDE template | Low — template is declarative |
| Modify Asset Movement helper logic in `_create_doc` | **High** — affects every process_type that emits Asset Movement |
| Re-introduce a `submit_blanking_dc_entry` dedicated handler | Forbidden — see ADR-006 |
| Change the `asset_category` filter on `get_assets` | Medium — Console UX may rely on knowing all Blanking Bins + Moulds |

## Change Note — 2026-05-29

Prior to this update, this file described:
- A `submit_blanking_dc_entry(context)` dedicated handler
- Hardcoded `CUTBIT_WH` and `BLANKING_WH` warehouse names
- Synthesized batch convention `CB_<compound>_<spp_batch>`
- A "semantic drift" between Console clip-to-bin and Ops Stock Entry

All four claims were stale — they described code that was removed prior to May 2026. The current implementation uses the generic TransactionEngine with the two-action template documented above. ADR-005 (Ops BDE = Stock Entry vs Legacy BDE = Asset Movement) is resolved by the current code in favor of Legacy semantics: Ops creates Asset Movement, never Stock Entry, matching the legacy `on_submit` contract.
