# 06 — Ops ERPNext (v15)

> Read [`../master-batch-mixing/06-ops-erpnext.md`](../master-batch-mixing/06-ops-erpnext.md)
> for the generic `TransactionEngine` pattern. Sheeting uses the same
> generic engine — no dedicated handler.

## Architectural Intent vs Reality for Sheeting on Ops

**Architectural Intent:** Sheeting should use the same generic engine — no dedicated handler.
`grep "SHEETING_PROCESS" apps/shree_polymer_ops` → 0 hits for direct mapping.

**Current Reality (Tech Debt):** `shree_polymer_ops/api.py` still contains legacy process-specific code for sheeting (specifically, the `_handle_sheeting_pre_save` method). While modern Sheeting payloads are pre-resolved by the Console and this hook is effectively dead weight that falls through or acts as a redundant safety net, any developer auditing the `api.py` file should be aware that process-specific code in Ops is deprecated and slated for removal.

## What the Ops engine does for Sheeting

The Console Process Template's action rows for `SHEETING_PROCESS`
typically include:

1. **`create_stock_entry`** action — purpose = Material Transfer or Repack
   - Items list includes one row per output clip/cut-bit
   - FG rows have `is_finished_item=1` and Console-generated barcodes
   - Source warehouse from `config.ops_source_warehouse`
   - Target warehouse from `config.ops_target_warehouse`

The engine applies placeholder resolution (`{{ context.field }}`) and
runs the action. Sheeting's payload has `items` at the top level (not
inside `stock_entry_data`), so the action template must reference
`{{ items }}` or use a context-aware template.

## Response — `impacted_clips`

The Ops side returns `impacted_clips` in the response specifically for
Sheeting (and Cut Bit Transfer):

```python
# After SE creation succeeds, Ops gathers per-clip info
result = {
    "status": "success",
    "log_name": "MES-LOG-...",
    "results": { ... },
    "impacted_balances": [...],
    "impacted_clips": [
        {"item_code": "...", "batch_no": "...", "barcode": "...",
         "warehouse": "...", "qty": ...},
        ...
    ],
}
```

This `impacted_clips` array drives:
1. Console's `_backfill_ops_reference_for_sheeting` (in
   `apply_bridge_result` extra) — updates `Console Item Clip Mapping`
   with the Ops batch references
2. The Dash component's success modal — displays each clip's Ops-side
   batch number to the operator

## Idempotency

Same `Shree Polymer MES Log` lookup by `reference_id`.

## Documents on Ops for one Sheeting submission

| Document | Notes |
|---|---|
| `Shree Polymer MES Log` | One row, status=Success |
| `Stock Entry` (purpose: Material Transfer or Repack) | One per submission; items include all output rows |
| `Stock Ledger Entry` × N | Auto by Frappe |
| `Batch` records | Per FG item if `has_batch_no=1` |

## Why no dedicated handler

Sheeting was an early-Wave process. Its sequence (single Stock Entry
with multiple item rows) fits the generic engine's capabilities. The
processes that DO have dedicated handlers (Cut Bit, Bulk Clip Release,
Blanking) have either:
- Stateful side effects (Asset Movement on bins, clip-state machine)
- Validation that the generic engine can't express
- Batch auto-creation patterns specific to legacy expectations

Sheeting needs none of these. The generic path is sufficient.

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add a new action to the `SHEETING_PROCESS` template (e.g. notification email) | Low — engine reads templates declaratively |
| Change the SE purpose from Material Transfer to Manufacture | High — affects Ops Stock Ledger semantics; coordinate with shop floor |
| Add a process-specific handler bypassing the engine | Medium — diverges from architecture; needs strong reason |
