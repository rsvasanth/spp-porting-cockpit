# Purpose

## What Bulk Clip Release Does

Bulk Clip Release retires active clip mappings in bulk. It means the physical clips are no longer considered occupied by sheeting WIP and can move to the next stage.

## Position in the Chain

```text
Sheeting Process creates active clip mappings
  -> Bulk Clip Release retires active mappings
  -> Blanking can consume released clips
```

## Boundary

This pack covers only clip release state. It does not create clips, transfer cut-bit material, or consume clips into blank bins.

## Business Outcome

| Layer | Required outcome |
| --- | --- |
| Console | Validates active local clip mappings and records release intent |
| Legacy | `Bulk Clip Release` retires matching `Item Clip Mapping` rows |
| Ops | Dedicated handler retires matching Ops clip mappings |
| Downstream | Blanking does not see already-released clips as still active sheeting WIP |

## Why This Process Is Load-Bearing

If release misses a mapping, downstream movement can be blocked as "clip not yet released." If it releases the wrong mapping, traceability and stock state become unreliable.
