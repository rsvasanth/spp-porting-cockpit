# 07 - End-to-end flow

## One operator submission

| Step | System | Action |
|---|---|---|
| 1 | Dash | Operator selects Blanker |
| 2 | Dash | Operator scans Clip/Bin barcode |
| 3 | Console API | `validate_cut_bit_asset` checks Console mapping, then Ops, then Legacy |
| 4 | Dash | Adds row with item, SPP batch, available qty, source warehouse |
| 5 | Dash | Operator adjusts transfer qty |
| 6 | Dash | Submits payload with `reference_id = CBT-<Date.now()>` |
| 7 | Console API | `submit_cut_bit_transfer` forces process code and hoists reference id |
| 8 | Console API | Missing native batch is relayed through Ops validation |
| 9 | Console API | Builds `stock_entry_data.items` source/target rows |
| 10 | Console API | `submit_process` -> `initialize_submission` |
| 11 | Console API | `create_local_cut_bit_transfer` writes local audit row and child rows |
| 12 | Console API | `_write_clip_mappings_for_cut_bit` reduces/retires Bin mappings only |
| 13 | Dash orchestration | Calls Legacy and Ops targets in parallel |
| 14 | Ops | `process_transaction` dispatches to `submit_cut_bit_transfer(context, run_legacy_sync=False)` |
| 15 | Ops | Creates Repack Stock Entry into `Cutbit - SPP` |
| 16 | Bridge | Creates legacy `Cut Bit Transfer` |
| 17 | Legacy | `on_submit` creates legacy Repack Stock Entry |
| 18 | Console callback | Each leg calls `apply_bridge_result`; aggregate becomes Success when both synced |

## Clip path trace

| Field | Example shape | Where it goes |
|---|---|---|
| Dash scan | `LAZTZ9A2` | `asset_id`, `clip_name` |
| Console mapping | `Console Item Clip Mapping.sheeting_clip` | validation only |
| Bridge row | `scan_barcode=LAZTZ9A2` | Legacy batch resolution |
| Legacy source | `default_sheeting_warehouse` | source Stock Entry row |
| Target batch | `Cutbit_<item_code>` | Legacy and Ops target row |
| Target mix barcode | `CB_<item_code>` | recycling trace |

Clip mappings are not retired by Console CBT. They remain active for the Blanking path unless another process retires them.

## Bin path trace

| Field | Example shape | Where it goes |
|---|---|---|
| Dash scan | bin barcode | `asset_id`, `clip_name` |
| Console mapping | `Console Item Bin Mapping.blanking__bin` | validation and local retirement |
| Bridge row | `scan_barcode=<bin>` | Legacy batch resolution |
| Legacy source | `unit_2_warehouse` or blanking warehouse by item group | source Stock Entry row |
| Target batch | `Cutbit_<item_code>` | Legacy and Ops target row |

Bin mappings can be partially reduced. If transfer qty is greater than or equal to active mapping qty, Console marks the bin mapping retired and qty zero.

## Parallel target behavior

| Leg | Native document | Completion signal |
|---|---|---|
| Ops | `Stock Entry` | `reference_name` plus impacted balances/assets |
| Legacy | `Cut Bit Transfer` + Stock Entry | Bridge success envelope |

The two legs are intentionally independent. A Legacy failure after Ops success should leave the Console local record `Partial`, not roll back the Ops Stock Entry.

## Failure examples

| Failure | Expected result |
|---|---|
| Invalid barcode | Dash shows validation error; no local audit row |
| Qty exceeds available | Dash blocks submit |
| Console-local mapping has no native batch | Submit wrapper relays to Ops; if still missing, Ops fails |
| Legacy cannot resolve batch | Legacy leg fails; Console aggregate becomes Failed or Partial |
| Ops succeeds while Legacy fails | Console records Ops reference and Legacy error |

## Idempotent retry

Console retry uses `reference_id` for its local record and Transaction Log rows. Legacy retry uses first scanned asset plus 10-minute creation window because the legacy CBT doctype has no stable reference field. This mismatch is acceptable but should stay documented.
