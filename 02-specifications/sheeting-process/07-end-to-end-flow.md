# 07 — End-to-end flow

> Read [`../master-batch-mixing/07-end-to-end-flow.md`](../master-batch-mixing/07-end-to-end-flow.md)
> for the sequence diagram + 5-step race narrative. Sheeting follows the
> same shape with these differences:

## Differences from MB flow

1. **Inline clip-mapping write** during `_safe_local_create` — happens
   BEFORE the Bridge calls fan out
2. **Legacy creates a `Material Transfer`** (not DCR), which on its own
   on_submit creates the actual Stock Entry
3. **Ops side returns `impacted_clips`** — Console's `apply_bridge_result`
   backfills the Item Clip Mapping with Ops batch references
4. **Per-output identity** — each clip + cut-bit has its own barcode,
   batch, and downstream lifecycle

## Narrative trace — one Sheeting submission

**Setup:** Operator Vignesh on the Sheeting Mill. Source compound:
`COMPOUND-A` lot with `mix_barcode = C_26C03X0`, qty 100kg. Mills it into
3 clips (~30kg each) + 1 cut-bit (~10kg).

**T+0:00** — Vignesh scans badge → Sheeting Operator role confirmed.

**T+0:10** — Scans compound barcode `C_26C03X0`. `validate_compound_barcode`
confirms accepted CI, returns identity. Dash auto-fills:
- `item_code: COMPOUND-A`
- `batch_no: BATCH-...`
- `spp_batch_no: C_26C03X0`
- `qty: 100`, `source_warehouse: Compound Inspection Warehouse - SPP`

**T+0:30** — Vignesh adds output rows:
- Clip 1: barcode `C_26C03X0-1`, qty 30
- Clip 2: barcode `C_26C03X0-2`, qty 30
- Clip 3: barcode `C_26C03X0-3`, qty 30
- Cut-bit 1: batch `Cutbit_C_26C03X0-1`, qty 10

Dash validates total output (100) matches source qty (100).

**T+0:45** — Vignesh clicks Submit. `handleSubmit` builds payload with
top-level `items` array + `sheeting_clip` array.

**T+0:46** — Console `initialize_submission`:
1. `build_transaction_payload` reads `Console Process Template "SHEETING_PROCESS"`
2. Routes to `create_local_sheeting_process(payload, reference_id)`:
   - `_safe_local_create("Console Sheeting Process", ...)` — inserts parent + `items` child rows
   - `_write_clip_mappings_for_sheeting(payload, reference_id)` — inserts `Console Item Clip Mapping` rows for the 3 clip outputs (NOT the cut-bit)
3. Creates two Transaction Log rows (Legacy + Ops)

**T+0:47** — Dash fires `Promise.all`.

### Legacy leg (T+0:47 → T+0:53)

1. POST to Bridge
2. Bridge `sync_process_transaction`:
   - Idempotency check passes (no existing Material Transfer with this `stock_entry_ref`)
   - **Sheeting-specific item extraction** (lines 177-200):
     - Reads `payload.items`
     - For each item missing `mix_barcode`: synthesizes `{item_code}_{original_batch}`. E.g. for Clip 1, sets `mix_barcode = "COMPOUND-A_C_26C03X0"` (strips the `-1` suffix from `spp_batch_number`).
     - Extracts `sheeting_clip` to top-level for the mapping engine
   - Loads `Legacy Sync Mapping "SHEETING_PROCESS"` (12 field_mappings rows)
   - Creates `Material Transfer` doc; applies field_mappings:
     - Header: stock_entry_ref, transfer_date, employee, item, scan_spp_batch_number, qty, warehouses, material_transfer_type=`"Transfer Compound to Sheeting Warehouse"` (literal)
     - `batches` child: 4 rows (3 clips + 1 cut-bit), each with item_code, batch_no, scan_barcode (=batch_no), qty
     - `sheeting_clip` child: 3 rows (clips only)
   - `populate_sheeting_fields(legacy_doc, payload_data)`:
     - Defaults applied (no-ops if mapping already set them)
     - Walks `doc.batches`: row 4's batch_no contains `"Cutbit_"` → sets `is_cut_bit_item=1`, adds 10 to cutbit_total
     - Sets `doc.cutbit_qty = 10`
   - `legacy_doc.insert()` + `legacy_doc.submit()`:
     - Material Transfer's on_submit creates a Stock Entry (Material Transfer purpose)
     - SE has 4 items rows with `mix_barcode` synthesized, batch_no, warehouses
     - `stock_entry_ref` field on Material Transfer is set to the SE name
   - Bridge extracts `legacy_spp_batch_no` from the SE's first FG row
   - Returns `{status: Success, reference_name: "MT-2026-...", legacy_spp_batch_no: "..."}`
3. Console `execute_submission_step`:
   - Updates Transaction Log Legacy row
   - Calls `apply_bridge_result("Legacy", "Success", "MT-2026-...", legacy_spp_batch_no="...")`
   - **Step 1** (Sheeting's extra): captures `legacy_spp_batch_no` onto Console doc
   - Standard 5-step dance → aggregate=Partial (Ops still pending)

### Ops leg (T+0:47 → T+0:51)

1. POST to Ops
2. `process_transaction` → falls through to `TransactionEngine`
3. Engine reads sequence from canonical payload
4. Runs `create_stock_entry` action — creates Stock Entry (Manufacture or Material Transfer purpose)
5. Returns `{status: success, log_name: "MES-LOG-...", impacted_balances: [...], impacted_clips: [{barcode: "C_26C03X0-1", batch_no: "...", ...}, {barcode: "C_26C03X0-2", ...}, {barcode: "C_26C03X0-3", ...}]}`
6. Console `execute_submission_step`:
   - Updates Transaction Log Ops row
   - Calls `apply_bridge_result("Ops", "Success", "MES-LOG-...", impacted_clips=[...])`
   - **Step 1** (Sheeting's extra): triggers `_backfill_ops_reference_for_sheeting(reference_id, impacted_clips)` — updates the 3 `Console Item Clip Mapping` rows (created during step T+0:46) with Ops-side batch references
   - Standard 5-step dance → second leg lands, aggregate=Success, fresh-doc auto-submit

### Race resolution

Same as other Wave 1 processes — 5-step pattern handles concurrent
callbacks. Sheeting's pattern is byte-identical to MB's except for the
two extras (legacy_spp_batch_no capture + impacted_clips backfill),
which run within step 1 BEFORE the aggregation.

## Final state for one Sheeting submission

| System | Document | State |
|---|---|---|
| Console | `Console Sheeting Process CSHT-2026-...` | `docstatus=1`, `sync_status=Success`, both legs Synced, `legacy_spp_batch_no` populated |
| Console | `Console Sheeting Item` (4 child rows) | One per output (3 clips + 1 cut-bit) |
| Console | `Console Item Clip Mapping` × 3 | One per clip, with Console + Ops batch refs |
| Console | `Console Stock Cache` | Updated for compound (debit) + 3 clips + 1 cut-bit (credit) |
| Legacy | `Material Transfer MT-2026-...` | `docstatus=1`, has batches + sheeting_clip children, cutbit_qty=10 |
| Legacy | `Stock Entry` (auto-created by MT.on_submit) | Has 4 items rows; FG rows have mix_barcode synthesized format |
| Legacy | `Sheeting Clip` records × 3 | Linked to source compound |
| Legacy | `Stock Ledger Entry` × N | One per item per warehouse change |
| Ops | `Shree Polymer MES Log` | `status=Success`, includes `impacted_clips` array |
| Ops | `Stock Entry` (Material Transfer or similar) | Same shape as legacy SE |

## Recovery procedures

### Clip mapping race (the BCR-1 bug)

Before the BCR-1 fix (early Wave 1), `_write_clip_mappings_for_sheeting`
ran from the Ops Bridge callback (not at create time). This left a
multi-second window where downstream Blanking scans could miss the
mapping. The fix moved the mapping write inline with
`create_local_sheeting_process`, so mappings exist on Console **before**
any Bridge call.

Hermes workers should not move the clip-mapping write back to a callback
path.

### Cut-bit flag drift

If `populate_sheeting_fields`'s `"Cutbit_"` prefix detection misses a
cut-bit row (e.g. operator used a different prefix), legacy validation
fails with cutbit_qty mismatch. Recovery: manually correct the batch_no
on legacy or fix the Dash to enforce the prefix.

### Mass balance miss

Console enforces mass balance (5% tolerance) only at Dash submit-time.
If a payload bypasses the Dash check (rare), the Console + Legacy + Ops
will all accept the imbalanced submission. Reconciliation surfaces at
the Stock Ledger level.
