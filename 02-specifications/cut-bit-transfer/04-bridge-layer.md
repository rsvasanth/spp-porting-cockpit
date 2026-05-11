# 04 - Bridge layer

> Read [`../master-batch-mixing/04-bridge-layer.md`](../master-batch-mixing/04-bridge-layer.md) for the shared `sync_process_transaction` lifecycle, log creation, mapping engine, and idempotent response shape.

## Mapping seed

`seed_cut_bit_transfer_mapping()` creates `CUT_BIT_TRANSFER -> Cut Bit Transfer`.

| Mapping type | Console field | Legacy field |
|---|---|---|
| Header | `reference_id` | `stock_entry_reference` |
| Header | `employee` | `employee` |
| Header | `transfer_from` | `transfer_from` |
| Header | `source_warehouse` | `source_warehouse` |
| Header | `target_warehouse` | `target_warehouse` |
| Child `items` | `items.item_code` | `item_code` |
| Child `items` | `items.batch_no` | `batch_no` |
| Child `items` | `items.spp_batch_no` | `spp_batch_no` |
| Child `items` | `items.qty` | `qty` |
| Child `items` | `items.scan_barcode` | `scan_barcode` |
| Child `items` | `items.sheeting_clip` | `sheeting_clip` |

The declarative mapping alone is not enough. `populate_cutbit_fields` repairs several fields after mapping and before insert.

**Field-name drift to verify:** the mapping row uses `items.spp_batch_no`, while the Dash payload and Console child doctype use `spp_batch_number`. Current legacy batch resolution mostly relies on mapping lookups and repaired `batch_no`, but `spp_batch_no` can be blank on the legacy child row unless another transform supplies it. Treat this as a test target before changing code.

## Payload flattening

`sync_process_transaction` has a shared extraction branch for Sheeting and Cut Bit:

```python
if process_type in ("SHEETING_PROCESS", "CUT_BIT_TRANSFER"):
    ...
    elif process_type == "CUT_BIT_TRANSFER":
        for it in payload_data["items"]:
            if not it.get("scan_barcode") and it.get("clip_name"):
                it["scan_barcode"] = it["clip_name"]
                it["sheeting_clip"] = it["clip_name"]
```

This is why the Dash payload must preserve `clip_name: asset_id`. It becomes the legacy scan barcode.

## Idempotency

Legacy `Cut Bit Transfer` has no reliable `reference_id` field. Bridge uses a pragmatic composite:

| Key | Rule |
|---|---|
| `scan_clip__bin` | First item `clip_name` or `asset_id` |
| Time window | Existing row created in last 10 minutes |

The code comment is explicit: a retry should arrive within seconds; a legitimate reuse of the same clip should be minutes/hours later.

This is weaker than MB/FB `reference_id` idempotency and should be treated as a production invariant, not a generic pattern.

## `populate_cutbit_fields`

This is the load-bearing Bridge function for the process. It handles:

| Concern | Behavior |
|---|---|
| Link validation | Sets `doc.flags.ignore_links = True` and clears bogus `stock_entry_reference` |
| Employee fallback | Uses `operator`, `run_as`, `operator_id`, then session user |
| `cut_bit_item` | Derives from first payload item |
| `transfer_from` | `"Warming"` for Clip, `"Blanking"` for Bin |
| Source warehouse | Per-row 3-way route by Item Group |
| Batch repair | Resolves Legacy batch via mapping + `Stock Entry Detail`/IBSB lookup |
| Failure mode | Throws if batch cannot be resolved |

## Three-way warehouse routing

| Item group condition | Legacy source warehouse |
|---|---|
| `item_group == "Compound"` | `SPP Settings.default_sheeting_warehouse` |
| `item_group == blanking_item_group` | `SPP Settings.unit_2_warehouse` |
| Else | `SPP Settings.default_blanking_warehouse` |

This intentionally does not use one header warehouse for all rows. The legacy controller's own `create_stock_entry` repeats the same business rule, so Bridge mirrors that behavior before insert.

## Batch resolution strategy

| Asset path | Resolution |
|---|---|
| Clip | Join `Item Clip Mapping` to `Sheeting Clip` by barcode text |
| Bin | Read `Item Bin Mapping` by `blanking__bin` barcode |
| Mix key | `<compound>_<spp_batch_number.split("-")[0]>` |
| Priority 1 | `Stock Entry Detail.batch_no` where `mix_barcode = mix_key` and `t_warehouse = row_source_wh` |
| Priority 2 | Latest `Item Batch Stock Balance` row with positive qty in `row_source_wh` |

If neither path resolves, Bridge raises:

```text
Cut Bit Transfer: cannot resolve Legacy batch for <item_code>
```

That fail-loud behavior is correct. Silent fallback would create a legacy Stock Entry against the wrong batch.

## Bridge result callback

After insert and submit, Bridge returns the standard success envelope consumed by Console's `execute_submission_step`. The local Console controller then records the Legacy leg through `apply_bridge_result`.

Unlike Sheeting, Cut Bit does not capture extra Bridge kwargs such as `legacy_spp_batch_no`.

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add extra child mappings | Low if populate function still wins for batch repair |
| Change idempotency time window | Medium; affects retry vs legitimate rescan split |
| Change `scan_barcode` source | High; breaks Clip/Bin lookup |
| Remove `ignore_links` correction | High; Console reference IDs are not real legacy Stock Entries |
| Collapse 3-way warehouse routing | High; breaks Compound vs Blanking source rules |
