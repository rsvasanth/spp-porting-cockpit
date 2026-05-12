# Purpose

## What BBI Does

Blank Bin Issue assigns a filled bin to a moulding Job Card/Lot. It records which compound, batch, bin, press, and mould are linked to the moulding run.

| Input | Process | Output |
| --- | --- | --- |
| Work-in-progress Moulding Job Card + filled bin | Blank Bin Issue | Bin reserved for MPE consumption |

## Position in the Chain

```text
Work Planning / Add On Work Planning
  -> Job Card Lot #
  -> Blank Bin Issue
  -> Inspection Entry
  -> Moulding Production Entry
```

## Boundary

BBI does not fill bins, move bins, or consume bins. It creates the logical assignment. MPE later marks issue items completed/consumed.

## Business Outcome

| Layer | Required outcome |
| --- | --- |
| Console | Audit record and issue items |
| Legacy | `Blank Bin Issue` with child issue row |
| Ops | Equivalent logical assignment when ported |
| Downstream | MPE can find issued bins by Lot/Job Card and `is_completed`/consumption state |

## Why This Process Is Load-Bearing

BBI is the bridge between planning and physical material. A wrong BBI lets a moulding run consume the wrong compound or an already-consumed bin.
