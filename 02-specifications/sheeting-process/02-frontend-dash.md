# 02 — Frontend (Dash) — `SheetingProcessEntry.tsx`

**File:** `apps/shree_polymer_console/dash/src/components/processes/SheetingProcessEntry.tsx`

> Read [`../master-batch-mixing/02-frontend-dash.md`](../master-batch-mixing/02-frontend-dash.md)
> for the shared scaffold. Sheeting differs in the output-row model: one
> input Compound → many output rows (clips + cut-bits) with auto-numbered
> barcodes.

## Flow summary

```
Open Sheeting Entry
   │
   ▼
Scan operator badge (Sheeting Operator / Mixing Operator role)
   │
   ▼
Scan Compound input barcode
   ├─► validate_compound_barcode({barcode}) — confirms accepted CI + available qty
   ├─► Sets sourceCompound: { item_code, batch_no, spp_batch_no, qty, mix_barcode, source_warehouse }
   ▼
Add output rows (operator builds the produced clip + cut-bit list)
   ├─► For each clip row:
   │     - Auto-generate clip barcode: e.g. `${sourceMixBarcode}-${index}` 
   │     - qty (typically equal among all clips, but operator can adjust)
   │     - is_cut_bit_item = 0
   ├─► For each cut-bit row:
   │     - Auto-generate cut-bit batch: e.g. `Cutbit_${sourceMixBarcode}-${index}` 
   │     - qty (the waste/rework portion)
   │     - is_cut_bit_item = 1
   ▼
Validate: sum(qty) of output rows ≤ source qty (mass balance check)
   ▼
Submit
   ├─► initializeSubmission({ payload })
   ├─► Promise.all([executeSubmissionStep(legacy), executeSubmissionStep(ops)])
   └─► Success modal
```

## Payload shape — `generatePayload()`

Different from MB Mixing — uses `items` (not `consumption_items`):

```tsx
return {
    reference_id: referenceID,
    metadata: {
        process_type: template?.template_name || "Sheeting Process",
        process_code: "SHEETING_PROCESS",
        entry_role: getStepValidations('Operator')?.required_role || "Sheeting Operator",
        produced_item: producedItem,
        run_as: operatorName,
    },
    config: {
        source_warehouse: sourceCompound.source_warehouse,
        ops_source_warehouse: opsSourceWarehouse,
        ops_target_warehouse: opsTargetWarehouse,
        legacy_source_warehouse: legacySourceWarehouse,
        legacy_target_warehouse: legacyTargetWarehouse,
        operation: "Sheeting",
        scan_barcode: sourceCompound.mix_barcode,
    },
    stock_entry_data: {
        posting_date: postingDate,
        posting_time: postingTime,
        item_code: producedItem,
        batch_no: sourceCompound.batch_no,
        spp_batch_number: sourceCompound.spp_batch_no,
        qty: sourceCompound.qty,
        from_warehouse: opsSourceWarehouse,
        to_warehouse: opsTargetWarehouse,
    },
    // ← Sheeting-specific: items list at TOP LEVEL (not inside stock_entry_data)
    items: outputRows.map((row, idx) => ({
        item_code:        row.item_code,
        batch_no:         row.batch_no,
        spp_batch_number: row.spp_batch_no,
        qty:              row.qty,
        s_warehouse:      sourceCompound.source_warehouse,
        is_cut_bit_item:  row.is_cut_bit_item ? 1 : 0,
        // mix_barcode is NOT set here — Bridge synthesizes it from spp_batch_number
        // see 04-bridge-layer.md for the {item_code}_{original_batch} reconstruction
    })),
    sheeting_clip: clipRows.map(row => ({
        scan_barcode: row.clip_barcode,
        clip_name:    row.clip_name,
        // ... other clip-specific metadata
    })),
    mix_barcode: sourceCompound.mix_barcode,
}
```

**Two new top-level blocks** vs MB:
- `items` (NOT nested inside `stock_entry_data`) — Bridge's special
  extraction logic reads from here for Sheeting/CutBit
- `sheeting_clip` — clip-specific metadata that maps to the legacy
  `sheeting_clip` child table

## Auto-numbering convention

Console generates output barcodes by appending `-{N}` to the source mix_barcode:

| Output | Generated barcode | Example |
|---|---|---|
| Clip 1 | `{source_mix_barcode}-1` | `C_26C03X0-1` |
| Clip 2 | `{source_mix_barcode}-2` | `C_26C03X0-2` |
| Cut bit 1 | `Cutbit_{source_mix_barcode}-1` | `Cutbit_C_26C03X0-1` |
| Cut bit 2 | `Cutbit_{source_mix_barcode}-2` | `Cutbit_C_26C03X0-2` |

The Legacy Bridge's `populate_sheeting_fields` checks for the `Cutbit_`
prefix to backfill the `is_cut_bit_item` flag if a row missed it (e.g.
when the payload came from Ops directly). This is a defensive backup —
the Dash always sets the flag.

## Mass balance check (operator-facing only)

```tsx
const totalOutputQty = outputRows.reduce((sum, r) => sum + r.qty, 0)
const drift = Math.abs(totalOutputQty - sourceCompound.qty) / sourceCompound.qty
if (drift > 0.05) {  // 5% tolerance
    setError(`Output total (${totalOutputQty}) differs > 5% from input qty (${sourceCompound.qty})`)
    return
}
```

This is **Dash-side only**. Console backend and Bridge do not enforce mass
balance — same operational decision as MB/FB.

## Backend calls

| Call | When | Purpose |
|---|---|---|
| `validate_compound_barcode` | On Compound scan | Confirms accepted CI + available qty |
| `get_available_employees` | Mount | Sheeting Operator list |
| `generate_compound_mix_barcode` | (Not used here — barcodes derived from source) | n/a |
| `initialize_submission` | Submit | Standard |
| `execute_submission_step` | Per target | Standard |

## Same as MB Mixing

- Live Feedback Promise.all pattern
- Retry from log UI (rebuilds req_params)
- Backdating UX
- Success modal with per-target status

## Where to extend safely

If a Hermes worker needs to add an output type or clip metadata:
1. Add to component state + form UI for new field
2. Include in `generatePayload`'s `items` or `sheeting_clip` array
3. Update `_SHEETING_ITEM_KEYMAP` in `api.py` if it should land on Console child rows
4. Update `seed_sheeting_process_mapping` in mapping seeder if it should flow to legacy
5. Run tests + one staging E2E with both clip + cut-bit rows
