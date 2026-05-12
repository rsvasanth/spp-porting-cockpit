# Purpose

## What BBIE Does

Blank Bin Inward Entry processes a bin after BDE created the bin-content mapping. It either moves the bin through asset movement or repacks the bin contents into cut-bit stock.

| Path | Trigger | Outcome |
| --- | --- | --- |
| Normal inward | Filled bin moves location | Asset Movement and IBM qty update |
| Cut-bit repack | Bin contents should recycle | Repack Stock Entry and IBM retirement |

## Position in the Chain

```text
Blanking DC Entry
  -> Blank Bin Inward Entry
       -> normal inward path
       -> cut-bit repack path
  -> Blank Bin Issue or Final Batch Mixing recycling
```

## Boundary

BBIE does not fill the bin and does not issue it to a Job Card. It owns the state transition after BDE and before BBI or recycling.

## Business Outcome

| Layer | Required outcome |
| --- | --- |
| Console | Audit record for inward/repack decision |
| Legacy | `Blank Bin Inward Entry`, Asset Movement or Repack Stock Entry |
| Ops | Dedicated handler should mirror the same branch |
| Downstream | Bin is either available/repacked or ready for issue path |

## Why This Process Is Load-Bearing

The branch choice changes the material's future. A normal inward path keeps bin contents for moulding. A cut-bit path removes material from the bin and makes it reusable in Final Batch Mixing.
