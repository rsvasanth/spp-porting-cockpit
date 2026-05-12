# Purpose

## What BDE Does

Blanking DC Entry records material transfer from a released sheeting clip into a physical blanking bin. The operator scans the clip, scans the bin, records gross weight, and the system derives net compound weight.

| Input | Process | Output |
| --- | --- | --- |
| Released sheeting clip + available bin | Blanking DC Entry | Active bin-content mapping and Asset Movement |

## Position in the Chain

```text
Sheeting Process
  -> Bulk Clip Release
  -> Blanking DC Entry
  -> Blank Bin Inward Entry
  -> Blank Bin Issue
  -> Moulding Production Entry
```

## Boundary

BDE owns bin filling. It does not move the bin to the moulding floor, issue the bin to a Job Card, or consume the bin in moulding.

## Business Outcome

| Layer | Required outcome |
| --- | --- |
| Console | Audit record, bin mapping mirror, clip quantity deduction |
| Legacy | `Blanking DC Entry`, `Item Bin Mapping`, `Asset Movement` |
| Ops | Target-side material movement per current implementation |
| Downstream | A scannable bin with compound, batch, qty, mat/item trace |

## Why This Process Is Load-Bearing

Every downstream bin operation trusts the `Item Bin Mapping` created here. If the compound, batch, bin, or net weight is wrong, BBI can issue the wrong material and MPE can consume the wrong input.
