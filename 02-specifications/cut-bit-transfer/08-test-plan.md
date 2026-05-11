# 08 - Test plan

## Scope

Cut Bit Transfer needs tests across three surfaces:

| Surface | Why |
|---|---|
| Console | Local audit row, validation relay, bin mapping side effects |
| Bridge/Legacy | Batch resolution, 3-way warehouse routing, legacy Stock Entry creation |
| Ops | Dedicated handler, SABB-safe Stock Entry, duplicate Legacy guard |

## Console unit tests

| Test | Expected |
|---|---|
| `create_local_cut_bit_transfer` with two rows | Parent qty equals sum of child qty |
| Partial payload with no items | Local audit row still lands through `_safe_local_create` |
| Desk insert with no item/qty/items | Validation fails |
| Clip item passed to `_write_clip_mappings_for_cut_bit` | No Console clip mapping retirement |
| Bin item partial qty | Active `Console Item Bin Mapping.qty` is reduced |
| Bin item full qty | Bin mapping `is_retired=1`, `qty=0` |
| Duplicate `reference_id` retry | No duplicate local parent |

Existing file:

```bash
bench --site sppconsole-dev.local run-tests --module shree_polymer_console.shree_polymer_console.doctype.console_cut_bit_transfer.test_console_cut_bit_transfer
```

Important: the current test names/text around "creates clip mappings" appear stale against current source. The expected behavior should be updated to match code: clips are skipped; bins are consumed locally.

## Console integration tests

| Test | Setup | Expected |
|---|---|---|
| Local Console Clip mapping hit | `Console Sheeting Clip` + active `Console Item Clip Mapping` | `validate_cut_bit_asset` returns Success with `native_batch_no=""` |
| Local Console Bin mapping hit | active `Console Item Bin Mapping` | Success with `source_warehouse="PreForming - SPP"` in current Console code |
| Ops fallback | no Console mapping, valid Ops mapping | Success from Ops relay |
| Legacy fallback | no Console/Ops mapping, valid Legacy mapping | Success from Bridge relay |
| Missing barcode everywhere | Failed response, no exception leak |

## Ops tests

Existing direct tests live in:

```bash
bench --site 25spp.local run-tests --module shree_polymer_ops.tests.test_cut_bit
```

Minimum assertions:

| Test | Expected |
|---|---|
| validate Clip | `asset_type="Clip"`, source `Sheeting - SPP` |
| validate Bin | `asset_type="Bin"`, source `Unit-2 - SPP` |
| submit polymorphic Clip + Bin | One Repack Stock Entry with four rows |
| target rows | `batch_no=Cutbit_<item_code>`, `mix_barcode=CB_<item_code>` |
| impacted response | includes balances, clips, bins |

## Ops duplicate-sync guard

Patch or spy `shree_polymer_legacy_bridge.sync_api.sync_process_transaction` and call:

```python
process_transaction({
    "metadata": {"process_code": "CUT_BIT_TRANSFER"},
    "context": {"metadata": {"process_code": "CUT_BIT_TRANSFER"}, "items": [...]}
})
```

Expected: Ops creates its Stock Entry, but does not call Legacy because dispatch passes `run_legacy_sync=False`.

## Bridge/Legacy tests

| Test | Expected |
|---|---|
| Clip payload with only `clip_name` | Bridge sets `scan_barcode` and `sheeting_clip` |
| Payload with `spp_batch_number` only | Legacy child `spp_batch_no` is either populated or explicitly proven unused |
| `stock_entry_reference=CBT-...` | Bridge clears it before insert if no Stock Entry exists |
| Compound item group | Source warehouse = `default_sheeting_warehouse` |
| Blanking item group | Source warehouse = `unit_2_warehouse` |
| Other item group | Source warehouse = `default_blanking_warehouse` |
| Missing Legacy batch resolution | `frappe.throw`, no silent insert |
| Retry same clip within 10 min | Bridge returns existing record idempotently |

Diagnostic command:

```bash
bench --site spp15.local run-tests --module shree_polymer_custom_app.shree_polymer_custom_app.doctype.cut_bit_transfer.test_cut_bit_transfer
```

Only use this if the legacy test module is still compatible with current fixtures.

## End-to-end smoke

| Step | Expected |
|---|---|
| Create active Sheeting Clip mapping on all relevant sites | Validation succeeds |
| Submit CBT from Dash | Console local row created |
| Ops leg completes | Ops Stock Entry Repack submitted |
| Legacy leg completes | Legacy CBT submitted and has `stock_entry_reference` |
| Console aggregate | `sync_status=Success`, doc submitted |
| Stock check | Cutbit warehouse has qty under `Cutbit_<item_code>` |

## UAT checklist

| User check | Pass condition |
|---|---|
| Scanner focus after operator selection | Barcode field active |
| Duplicate scan | Clear error, no duplicate row |
| Qty edit | Allows partial transfer within available qty |
| Success modal | Shows both target systems |
| Start next batch | Clears staged rows but keeps flow usable |

## Non-negotiable gate

No code should be pushed from this cockpit work. If Hermes later changes code, run real tests before push. Syntax/JSON checks do not satisfy the SPP test gate.
