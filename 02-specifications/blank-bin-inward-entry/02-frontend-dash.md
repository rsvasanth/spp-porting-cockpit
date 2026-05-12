# 02 — Frontend (Dash) — `BlankBinInwardEntry.tsx` (planned)

> Read [`../master-batch-mixing/02-frontend-dash.md`](../master-batch-mixing/02-frontend-dash.md) for the shared scaffold. This file documents the planned BBIE-specific UX.

## Planned flow

```
Open Blank Bin Inward Entry
   │
   ▼
Scan Material Handler badge → operator selected
   │
   ▼
Scan filled bin barcode
   ├─► validate_blank_bin_inward({barcode}) — fetches Asset state + contents
   ├─► Bin must be in "Filled at <blanking warehouse>" status
   └─► Display: item, batch, compound, net weight from BDE
   ▼
Toggle: move_to_cut_bit_warehouse (default: 0)
   │
   ├─► If 0 (bin path):
   │     Target: Moulding Unit warehouse (from Process Template)
   │     Show: "This bin will arrive at Moulding Unit warehouse"
   │
   └─► If 1 (cut-bit repack):
         Scan or auto-derive cut-bit batch: Cutbit_<item_code>
         Show: "This bin will be repacked to cut-bit warehouse with Cutbit_<item>"
   ▼
Optional: Re-confirm net weight (soft warning if drift > 5%)
   ▼
Submit
   ├─► initializeSubmission + Promise.all execution
   └─► Live Feedback per-target status
```

## Planned state model

```tsx
const [operator, setOperator] = useState('')
const [scannedBin, setScannedBin] = useState<BinInfo | null>(null)
const [moveToCutBit, setMoveToCutBit] = useState(false)
const [cutBitBatch, setCutBitBatch] = useState('')
const [reConfirmedNetWeight, setReConfirmedNetWeight] = useState('')
const [weightDriftWarning, setWeightDriftWarning] = useState(false)
```

`BinInfo` includes: `bin_code`, `item_code`, `batch_no`, `spp_batch_number`, `net_weight_from_bde`, `source_warehouse`, `compound_item`.

## Planned backend calls

| Call | When | Purpose |
|---|---|---|
| `validate_blank_bin_inward(barcode)` | On bin scan | Fetch bin Asset state + contents from BDE record |
| `get_available_employees({required_role: "Material Handler"})` | Mount | Material Handler dropdown |
| `initialize_submission` | On submit | Standard pattern |
| `execute_submission_step` | Per target | Standard pattern |

## Planned payload shape

```tsx
return {
  reference_id: referenceID,
  metadata: {
    process_code: "BLANK_BIN_INWARD",
    entry_role: "Material Handler",
    produced_item: scannedBin.item_code,
  },
  config: {
    legacy_source_warehouse: scannedBin.source_warehouse,
    legacy_target_warehouse: moveToCutBit ? "Cut-Bit Warehouse - SPP INDIA" : "Moulding Unit Warehouse - SPP INDIA",
    ops_target_warehouse: moveToCutBit ? "Cut-Bit - SPP" : "Moulding Unit - SPP",
    operation: "Blank Bin Inward",
  },
  bin_code: scannedBin.bin_code,
  move_to_cut_bit_warehouse: moveToCutBit ? 1 : 0,
  cut_bit_batch: moveToCutBit ? `Cutbit_${scannedBin.item_code}` : null,
  gross_weight_kgs: parseFloat(reConfirmedNetWeight || scannedBin.net_weight_from_bde),
  net_weight_kgs: parseFloat(reConfirmedNetWeight || scannedBin.net_weight_from_bde),
  spp_batch_number: scannedBin.spp_batch_number,
  item: scannedBin.item_code,
  // ... standard tracking fields
}
```

## Branching UX visibility (load-bearing per FR-BLK-053)

The Dash MUST surface the downstream consequence of the `move_to_cut_bit_warehouse` toggle BEFORE submit. Two visual states:

- Toggle off: green panel "This bin will arrive at Moulding Unit warehouse. Bin remains Filled."
- Toggle on: yellow panel "This bin will be REPACKED. Compound moves to cut-bit warehouse with `Cutbit_<item>` batch. Bin will return to Available status."

This prevents post-submit operator surprise.

## Same as MB Mixing pattern

- Live Feedback Promise.all submit
- Retry from log UI
- Backdating for System Manager / Administrator
- Per-target status modal

## Where to extend safely

If a third path emerges (e.g. "move to scrap warehouse"), add another toggle option and corresponding config block. The Bridge populate function reads the flag and branches accordingly.
