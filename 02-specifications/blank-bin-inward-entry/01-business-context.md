# 01 — Business context

## What this process does

After Blanking DC Entry produces filled bins at the blanking floor, the Material Handler moves them to the Moulding Unit warehouse via Blank Bin Inward Entry. This is **the physical bin movement event** that bridges Blanking and Moulding.

| Variant | Trigger | Bin destination | Documents created |
|---|---|---|---|
| **Bin path (default)** | Filled bin needs to move to Moulding Unit | Moulding Unit warehouse | Asset Movement (Receive Bin) on Legacy + Ops; NO Stock Entry |
| **Cut-bit repack path** | Bin contents are mixed/partial/leftover compound that should be recycled | Cut-bit warehouse with `Cutbit_<item_code>` batch | Stock Entry (Repack) on Legacy + Ops; bin Asset status reset to Available |

The operator toggles `move_to_cut_bit_warehouse` on the Dash to select the path.

## Position in the chain

```
Blanking DC Entry  →  [bin filled at blanking warehouse]
                              │
                              ▼
                BLANK BIN INWARD ENTRY (BBIE)
                              │
                ┌─────────────┼─────────────┐
                │                            │
        move_to_cut_bit=0           move_to_cut_bit=1
                │                            │
                ▼                            ▼
   [bin at Moulding Unit warehouse]   [compound at cut-bit warehouse]
                │                            │
                ▼                            ▼
        Blank Bin Issue              Final Batch Mixing (recycling input)
                │
                ▼
        Moulding Production Entry
```

## Why the cut-bit repack path exists

A bin's contents may not always be suitable for direct moulding consumption:
- The bin was partially filled (less than mould production needs)
- The compound is leftover from a previous shift's blanking with mixed batches
- The compound has been sitting and Quality wants to re-blend it via FB Mixing

In these cases, the Material Handler chooses the repack path. The compound is reclassified as cut-bit material — to be recycled through FB Mixing's standard scan flow — rather than being issued for moulding.

This keeps the cut-bit recycling loop (Sheeting-and-Cutting motion) feedable from yet another source.

## Why a separate process from BDE

It might seem natural to combine BDE + BBIE — the Blanker fills the bin AND moves it inward in one step. But operationally:

- BDE happens at the blanking press (one workstation)
- BBIE happens during a physical bin movement (another workstation / location)
- Different operators may handle each step (Blanker vs Material Handler)
- The time delay between fill and move is operationally significant (allows the compound to cool, allows QA to spot-check, etc.)

Separating them preserves audit clarity and operational flexibility.

## Operational constraints

| Constraint | Why |
|---|---|
| Bin must be in "Filled at <blanking warehouse>" Asset state | Empty bins or already-Inward bins reject |
| Target warehouse defaults to Moulding Unit | Per Console Process Template config |
| Cut-bit path requires the target cut-bit batch identifier | `Cutbit_<item_code>` per cross-motion convention |
| Net weight may be re-verified at Dash | Soft warning if drift > 5% from BDE record |
| Bin asset status transitions atomically | No intermediate "transitioning" state visible |
| Dual-ERP parallel sync | Charter Principle 3 |

## Cross-motion contracts

| Contract | This process's role | Other motion's role |
|---|---|---|
| Bin state machine | BBIE flips Filled → Inward (bin path) OR Filled → Available (repack path) | BDE writes Filled; BBI flips Inward → Issued |
| Cut-bit recycling loop | Cut-bit path contributes `Cutbit_<item>` batches | FB Mixing consumes them |
| Asset Movement audit | Receive Bin AM created | Asset master tracks |

## What the business is NOT asking for

See [10-risks-and-decisions.md](10-risks-and-decisions.md). High-level:

- Real-time bin location tracking
- Automatic decision on bin vs repack path (operator decides)
- Multi-bin batch BBIE (one bin at a time)
- Bin merging across BBIE submissions
