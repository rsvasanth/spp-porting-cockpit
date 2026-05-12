# 01 — Purpose

Moulding Production Entry is the terminal manufacturing booking for the porting chain. It turns issued blank-bin material into a finished production batch, records operator/supervisor accountability, creates the manufacturing Stock Entry, completes the moulding Job Card, and closes consumed blank-bin issue rows.

## Process position

```text
Work Planning / Add On Work Planning
  -> Blank Bin Issue
  -> Inspection Entry (Line + Patrol required)
  -> Moulding Production Entry
  -> Finished goods stock and downstream deflashing/packing flows
```

## What MPE must decide

| Decision | Requirement intent |
|---|---|
| Is the scanned lot valid? | Lot must resolve to an open moulding Job Card. |
| Is QA ready? | Submitted Line and Patrol Inspection Entries must exist before production booking. |
| Are bins available? | Open Blank Bin Issue rows must exist and map to active Item Bin Mapping rows. |
| Is material compatible? | Bin compound must match active BOM material for the Job Card. |
| Is quantity credible? | Production tolerance from SPP Settings must be enforced or warned exactly as legacy behavior defines. |
| Is the workstation injection moulding? | Injection presses require purge/leakage accounting. |
| Can stock be booked? | Source stock, shell stock, and batch references must exist before Stock Entry submit. |

## Why this is a separate requirement identity

Inspection Entry and MPE are coupled, but they are not the same process. Inspection Entry captures quality observations and rejection quantities. MPE performs the production booking, consumes blank bins, creates the final batch, and submits or updates inspection rejection stock entries after the final batch exists.

Keeping MPE separate makes refactoring easier because the implementation owner can compare one DocType controller, one Console process, one requirement pack, and one specification folder without mixed IE/MPE rules.

