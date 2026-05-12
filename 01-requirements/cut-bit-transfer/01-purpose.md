# Purpose

## What Cut Bit Transfer Does

Cut Bit Transfer moves reusable material from clips or bins into cut-bit stock. It consumes available quantity from the source asset and creates a repack stock entry so the material can later be scanned as cut-bit input.

## Position in the Chain

```text
Sheeting / Blanking leftovers
  -> Cut Bit Transfer
  -> Cutbit warehouse
  -> Final Batch Mixing recycling input
```

## Boundary

This pack starts when an operator scans a clip/bin or cut-bit source asset. It ends when the cut-bit warehouse has the repacked material and local mappings are updated for bin consumption. It does not create sheeting clips and does not release clips for Blanking.

## Business Outcome

| Layer | Required outcome |
| --- | --- |
| Console | Local audit and validation against known asset state |
| Legacy | `Cut Bit Transfer` record and `Stock Entry` reference |
| Ops | Dedicated Cut Bit Transfer handler creates repack stock entry |
| Downstream | Final Batch Mixing can scan `CB_<item_code>` / `Cutbit_<item_code>` identity |

## Why This Process Is Load-Bearing

Cut Bit Transfer is the recycling bridge. If it misroutes warehouse, batch, or source quantity, reusable material either disappears from stock or becomes unscannable for mixing.
