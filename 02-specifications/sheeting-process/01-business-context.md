# 01 — Business context

## What Sheeting Process is

After Final Batch Mixing produces a Compound, the compound goes to a
**Sheeting Mill**. The mill rolls the compound into thin sheets, which are
then cut into smaller pieces — either **clips** (for later blanking) or
**cut bits** (for direct re-mixing).

Operator flow:
1. Scan the input Compound's barcode
2. Confirm Compound details (item, batch, qty, source warehouse)
3. Operate the sheeting mill, producing multiple output rows:
   - Multiple **clips** with auto-numbered barcodes
   - Optional **cut-bit** rows (waste edges or rework pieces)
4. Each output row gets a Console-generated barcode
5. Submit → fans out to Legacy (Material Transfer) + Ops (Stock Entry)

## Output: clips vs cut-bits

Sheeting can produce **two distinct output types** in a single submission:

| Output type | What it is | Where it goes next | Legacy field flag |
|---|---|---|---|
| **Clip** | Sheet piece that's the right shape for blanking | Blanking floor | `is_cut_bit_item = 0` |
| **Cut bit** | Waste edge or pieces that can't go to blanking | Recycled back into mixing (Final Batch) | `is_cut_bit_item = 1` |

This duality drives much of the Sheeting code's complexity:
- Two different child-table mappings on Legacy (`batches` for items, `sheeting_clip` for clip-specific metadata)
- `cutbit_qty` aggregation on the legacy parent
- Two different downstream consumers (Blanking vs Final Batch Mixing)

## Position in the chain

```
Final Batch Mixing → Compound Inspection (Accepted)
                            │
                            ▼
                    Sheeting Process
                    │              │
                    ▼              ▼
                  Clips          Cut bits
                    │              │
                    ▼              ▼
            Cut Bit Transfer    (back to Final Batch Mixing)
                    │
                    ▼
            Bulk Clip Release
                    │
                    ▼
             Blanking DC Entry
                    │
                    ▼
            Blank Bin Inward / etc.
```

Sheeting is the **branching point** of the chain — output splits between
the main forward path (clip → blanking) and the recycling loop (cut bit
→ back to mixing).

## What success looks like for the operator

1. Operator scans badge + input Compound barcode
2. Sees Compound details auto-fill (item, batch, source warehouse, qty)
3. Adds rows for each clip + cut-bit produced (each gets auto-numbered barcode)
4. Submits → real-time per-target status (Ops + Legacy)
5. Each clip's barcode is printed as a label for downstream blanking scan
6. Cut-bit rows show up in the Final Batch Mixing scannable barcodes list

## What success looks like upstream

1. `Console Sheeting Process` row exists, `sync_status=Success`, `docstatus=1`
2. **Console Sheeting Clip child rows** exist with `mix_barcode` populated for each clip
3. **Console Item Clip Mapping** rows exist linking each clip's barcode to the source compound's batch
4. Legacy `Material Transfer` exists with:
   - `material_transfer_type = "Transfer Compound to Sheeting Warehouse"`
   - `batches` child rows for each output item with correct `is_cut_bit_item` flag
   - `sheeting_clip` child rows for clip metadata
   - `cutbit_qty` set to sum of cut-bit row qtys
4. Ops Stock Entry exists with corresponding stock moves

## Operational constraints

| Constraint | Why |
|---|---|
| Input Compound must be from an **Accepted** Compound Inspection | Sheeting only runs on QA-approved compound; Rejected compounds go through Compound Deviation first |
| Clip barcodes auto-numbered by sequence | Console generates `C_<barcode>-1`, `C_<barcode>-2`, etc. for each clip from one compound input |
| Cut-bit rows must reference the **original compound's batch** | Cut bits go back into mixing as raw material; tracking back to source batch is essential |
| Operator can mix clips + cut-bits in one submission | One Compound input → many clip outputs + zero or more cut-bit outputs in one Sheeting submission |

## Why Sheeting has two child tables on legacy

Legacy `Material Transfer`'s schema:
- `batches` — Material Transfer Item rows, one per output line. Has `item_code`, `qty`, `batch_no`, `scan_barcode`, `is_cut_bit_item` flag
- `sheeting_clip` — Sheeting Clip rows, one per clip. Has clip-specific metadata (presumably barcode, position, dimensions)

Both must be populated for a Sheeting submission. The Bridge mapping has
rows for both, and `populate_sheeting_fields` reconciles the `is_cut_bit_item`
flag across them.

## Roles

| Role | Action |
|---|---|
| Sheeting Operator (a Mixing Operator variant) | Runs the submission |
| Quality Inspector | (No direct interaction — checks happened upstream at Compound Inspection) |
| System Manager / Administrator | Backdating |

## What makes Sheeting more complex than MB/FB

1. **Multiple outputs per submission** (1 input → N outputs)
2. **Two child tables on legacy** (not just one)
3. **Console-side post-processing** (`_write_clip_mappings_for_sheeting` writes clip-to-batch mapping records inline with the local create)
4. **Bridge-side item extraction logic** (rebuilds `mix_barcode` for items missing it, using legacy format `{item_code}_{original_batch}`)
5. **Two distinct downstream paths** (clip path + cut-bit path) — both must be traceable end-to-end
