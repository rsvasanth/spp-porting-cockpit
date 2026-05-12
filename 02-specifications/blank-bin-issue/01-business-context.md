# 01 — Business context

## Shop-floor meaning

Blank Bin Issue is the handoff between blank-bin availability and moulding consumption. The operator scans:

1. A moulding lot / Job Card barcode.
2. A physical bin barcode.

The record says: "this bin is now issued to this moulding Job Card." It does not move stock, create an Asset Movement, or create a Stock Entry.

## Position in chain

```text
Work Planning / Add On Work Planning
  -> Blanking DC Entry
  -> Blank Bin Inward Entry
  -> Blank Bin Issue
  -> Inspection Entry (Line + Patrol)
  -> Moulding Production Entry
```

## Why BBI is not BBIE

| Process | Meaning | Side effect |
|---|---|---|
| Blank Bin Inward Entry | Bin arrives / is moved to moulding-side availability. | Asset Movement or cut-bit repack path in legacy. |
| Blank Bin Issue | Bin is assigned to a moulding Job Card/Lot. | Logical reservation row with `is_completed = 0`. |
| Moulding Production Entry | Bin material is consumed into finished goods. | Manufacture Stock Entry; BBI item completed. |

## Live site reality

Read-only `spp15.local` evidence:

| Metric | Value |
|---|---:|
| `Blank Bin Issue` total records | 68,078 |
| Submitted records | 67,309 |
| Cancelled records | 330 |
| Draft records | 439 |
| Open child issue rows (`is_completed = 0`) | 287 |
| Completed child issue rows (`is_completed = 1`) | 67,719 |
| Duplicate submitted lot/bin pairs | 820 |

The duplicate count is important: old duplicate-prevention code is commented out, so production reality permits repeated lot/bin pairs over time or under some operational cases. A Console port must not add a strict uniqueness rule without business signoff.

