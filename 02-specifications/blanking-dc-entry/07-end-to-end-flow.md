# 07 - End-to-end flow

## Operator submission trace

| Step | System | Action |
|---|---|---|
| 1 | Dash | Operator selects Blanker and item to produce |
| 2 | Dash | Operator scans sheeting clip |
| 3 | Console | `validate_blanking_clip_barcode` returns compound, SPP batch, qty |
| 4 | Dash | Operator scans blanking bin |
| 5 | Console | `validate_blanking_bin_barcode` returns bin name and tare weight |
| 6 | Dash | Operator enters gross weight |
| 7 | Dash | Calculates net weight and blocks over-consumption |
| 8 | Dash | Adds draft row |
| 9 | Dash | Submits `BLANKING_DC_ENTRY` payload |
| 10 | Console | `create_local_blanking_dc_entry` writes audit row |
| 11 | Console | Creates `Console Item Bin Mapping` and deducts clip qty |
| 12 | Dash | Executes Ops and Legacy target logs in parallel |
| 13 | Legacy | Bridge creates `Blanking DC Entry`; submit creates bin mapping + Asset Movement |
| 14 | Ops | Creates Material Transfer Stock Entry |
| 15 | Console | Callback should update local sync status, but routing is currently missing |

## Success state

| System | Expected result |
|---|---|
| Console | Local BDE row, active `Console Item Bin Mapping`, clip qty reduced |
| Legacy | Submitted BDE, `Item Bin Mapping`, `Asset Movement` |
| Ops | Submitted Stock Entry transfer |

## Current callback problem

`BLANKING_DC_ENTRY` is missing from `update_local_domain_record`, so target success does not update the local Console BDE row. This is the same family of drift as BCR, with an extra method-signature issue if routing is added naively.

## Failure points

| Failure | Expected |
|---|---|
| Clip has no active mapping | Scan rejected |
| Bin already has active mapping | Scan rejected |
| Net weight exceeds clip qty | Dash rejects row |
| Legacy BOM/stock check fails | Legacy leg fails |
| Ops cannot find `CB_` batch in Cutbit WH | Ops leg fails |
| Callback routing omitted | Local audit stays stale |

## My read

BDE is not a simple "one doc in each ERP" process. It is a bridge between process-master state and stock/asset movement, and the two ERPs currently model it differently. Hermes needs to preserve that distinction when porting.
