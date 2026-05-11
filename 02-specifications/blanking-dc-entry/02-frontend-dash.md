# 02 - Frontend Dash

> Shared target execution is documented in [`../master-batch-mixing/02-frontend-dash.md`](../master-batch-mixing/02-frontend-dash.md). Blanking DC Entry follows the same live-feedback submit loop after building its draft items.

## Component

| File | Role |
|---|---|
| `/Users/alphaworkz/frappe-bench/apps/shree_polymer_console/dash/src/components/processes/BlankingDCEntry.tsx` | Three-step scan UI for clip -> bin -> gross weight |

## State model

| State | Meaning |
|---|---|
| `draftItems` | Rows queued for submission |
| `operator` | Selected Blanker |
| `itemToProduce` | Selected `Console Item` with `item_group='Compound'` filter |
| `activeClipData` | Result of clip validation |
| `activeBinData` | Result of bin validation |
| `grossWeight` | Operator-entered scale value |

## Scan sequence

| Step | Input | Backend |
|---|---|---|
| 1 | Sheeting clip barcode | `validate_blanking_clip_barcode` |
| 2 | Blanking bin barcode | `validate_blanking_bin_barcode` |
| 3 | Gross weight | local calculation |
| 4 | Add draft row | no backend call |

The UI prevents:

| Guard | Check |
|---|---|
| Missing operator/item | cannot scan clip |
| Duplicate clip in draft | `draftItems.find(d => d.sheeting_clip === barcode)` |
| Duplicate bin in draft | `draftItems.find(d => d.bin_code === barcode)` |
| Gross <= tare | local error |
| Net > clip qty | local error |

## Payload

Current submit payload:

```ts
const payload = {
  metadata: {
    process_code: 'BLANKING_DC_ENTRY',
    reference_id: `BDC-${Date.now()}`,
    run_as: operator,
    produced_item: itemToProduce,
  },
  item_to_produce: itemToProduce,
  items: draftItems.map(d => ({
    sheeting_clip: d.sheeting_clip,
    compound: d.compound,
    spp_batch_number: d.spp_batch_number,
    bin_code: d.bin_code,
    bin_weight: d.bin_weight,
    gross_weight: d.gross_weight,
    net_weight: d.net_weight,
    item_to_produce: d.item_to_produce,
  })),
}
```

This is correctly using `metadata.process_code`, unlike Bulk Clip Release.

## Field-name drift

| Layer | Field |
|---|---|
| Dash draft item | `net_weight` |
| Console child doctype | `net_weight` |
| Legacy child doctype | `net_weight` |
| Console mapping seeder | `items.qty -> qty` |

The seeder maps `items.qty`, but Dash never sends `qty`. Bridge `populate_blanking_dc_fields` compensates by rebuilding child rows and using `net_weight`. This should remain a test target.

## Plan drift

Wave 2 planning docs mention `move_to_cut_bit_warehouse` / `scan_cut_bit_batch` branching, but current `BlankingDCEntry.tsx` has no such controls. That branch appears to belong to a related Blank Bin Inward flow, not current BDE Dash.

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add explicit `qty: net_weight` to payload | Low/high-value for mapping resilience |
| Add duplicate check by resolved `source_clip` instead of barcode text | Medium |
| Add BOM validation to Console scan helper | Medium/high; legacy does it, Console does not |
| Add cut-bit branch controls | High; not present in current process shape |
