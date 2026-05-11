# 01 - Business context

## Process position

Cut Bit Transfer is the consolidation step for reusable compound material that already exists in shop-floor assets.

```text
Master Batch Mixing
  -> Final Batch Mixing
    -> Compound Inspection
      -> Sheeting Process
        -> Cut Bit Transfer
          -> Cutbit warehouse stock
            -> Final Batch Mixing recycling path

Blanking / Bin flows
  -> Bin with compound balance
    -> Cut Bit Transfer
      -> Cutbit warehouse stock
```

It does not manufacture a new compound identity. It repacks existing material into a standard cut-bit batch convention so downstream mixing can consume it again.

## Shop-floor meaning

| Term | Meaning in this process |
|---|---|
| Clip | Sheeting-floor holder mapped by `Item Clip Mapping` / `Console Item Clip Mapping` |
| Bin | Blanking-side holder mapped by `Item Bin Mapping` / `Console Item Bin Mapping` |
| Cutbit warehouse | Consolidated reusable stock location |
| `Cutbit_<item_code>` | Batch convention used by Ops and Legacy target rows |
| `CB_<item_code>` | Mix barcode convention on target Stock Entry rows |

## Why this process is not just Sheeting in reverse

Sheeting creates clip mappings. Cut Bit Transfer consumes from occupied clips/bins and produces a reusable cut-bit batch. The business rule is asymmetric:

| Asset type | Console local mapping behavior | Why |
|---|---|---|
| Clip | Not retired by Cut Bit Transfer | A clip can span multiple CBT batches until Blanking consumes the compound |
| Bin | Retired or reduced by Cut Bit Transfer | Bins represent a directly consumed blanking-side balance |

That rule is encoded in `_write_clip_mappings_for_cut_bit`, despite the helper name. The code comments say "Console-native Bin Mapping writer" and explicitly skip `asset_type == "Clip"`.

## Actors

| Actor | System role |
|---|---|
| Blanker / operator | Selects operator, scans Clip/Bin barcode, adjusts transfer qty |
| Console Dash | Validates asset and builds `items[]` payload |
| Console backend | Creates local audit row and fans out Legacy + Ops calls |
| Legacy Bridge | Creates legacy `Cut Bit Transfer`, which submits into a Stock Entry |
| Ops app | Creates Ops `Stock Entry` Repack directly through dedicated handler |

## Operational constraints

| Constraint | Why it matters |
|---|---|
| Scan must resolve to active mapping | Prevents moving material from empty or retired assets |
| Qty must be `> 0` and `<= available_qty` in Dash | Avoids over-consuming mapped asset quantity |
| Native batch must reach Ops | Ops handler validates `native_batch_no` or `batch_no` |
| Legacy batch may need re-resolution | Console/Ops native batch can be invalid on Legacy |
| Dedicated Ops handler must not call Legacy in Console path | Console already calls Bridge in parallel |

## Cross-links

| Shared concept | Reference |
|---|---|
| Parallel orchestration | [`../master-batch-mixing/03-console-backend.md`](../master-batch-mixing/03-console-backend.md) |
| Sheeting clip creation | [`../sheeting-process/03-console-backend.md`](../sheeting-process/03-console-backend.md) |
| Cut-bit recycling loop note | [`../sheeting-process/10-risks-and-decisions.md`](../sheeting-process/10-risks-and-decisions.md) |

## The unique story

Cut Bit Transfer is a dual-destination repack with identity repair at both ends. Console collects scanned asset context, Ops creates a `Stock Entry` Repack directly, and Legacy creates a legacy `Cut Bit Transfer` that then creates its own Repack Stock Entry. The fragile part is not the Stock Entry shape; it is keeping Clip/Bin identity, batch resolution, and duplicate Legacy sync separated cleanly.
