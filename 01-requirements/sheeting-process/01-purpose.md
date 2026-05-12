# Purpose

## What Sheeting Does

Sheeting takes compound that has passed inspection and turns it into physical sheeted outputs. Some outputs become clips for Blanking. Some outputs are cut-bit material that can later re-enter Final Batch Mixing through Cut Bit Transfer.

| Input | Process | Output |
| --- | --- | --- |
| Accepted compound batch | Sheeting mill operation | Clip rows and optional cut-bit rows |

## Position in the Chain

```text
Final Batch Mixing
  -> Compound Inspection / accepted deviation
  -> Sheeting Process
       -> clips for Bulk Clip Release / Blanking
       -> cut-bit rows for later Cut Bit Transfer
```

## Boundary

This pack covers only the creation of sheeted output identities. It does not cover releasing clips, repacking cut bits, or consuming clips in Blanking. Those are separate process identities.

## Business Outcome

The operator must be able to scan one approved compound source, enter all produced outputs, and submit a record that creates:

| Layer | Required outcome |
| --- | --- |
| Console | `Console Sheeting Process` audit record and local clip mappings |
| Legacy | `Material Transfer` with batch rows and sheeting clip child rows |
| Ops | Stock movement representing the sheeting transfer |
| Downstream | Scannable clip identities available before Blanking or release scans begin |

## Why This Process Is Load-Bearing

Sheeting creates the identities used by downstream scans. If clip mappings are late or incomplete, Bulk Clip Release, Cut Bit Transfer, and Blanking can fail even though the physical material exists. That is why the BCR-1 inline mapping behavior is a requirement, not an implementation detail.
