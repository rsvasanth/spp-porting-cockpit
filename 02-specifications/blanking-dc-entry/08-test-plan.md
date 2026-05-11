# 08 - Test plan

## Console tests

Existing doctype test:

```bash
bench --site sppconsole-dev.local run-tests --module shree_polymer_console.shree_polymer_console.doctype.console_blanking_dc_entry.test_console_blanking_dc_entry
```

Add or verify:

| Test | Expected |
|---|---|
| valid clip barcode | returns compound, `spp_batch_number`, qty |
| zero-qty clip mapping | rejected |
| valid bin barcode | returns bin name and tare |
| bin already in active mapping | rejected |
| local create from Dash payload | creates `Console Blanking DC Entry` |
| local create side effects | creates `Console Item Bin Mapping`; deducts clip qty |
| partial clip consumption | mapping qty reduced, not retired |
| full clip consumption | mapping retired |

## Routing tests

| Test | Expected |
|---|---|
| `initialize_submission` with `BLANKING_DC_ENTRY` | local row created and target logs created |
| target callback | local BDE sync fields update |
| current source | expected to fail because callback map omits BDE |
| after adding map | expected to fail unless `apply_bridge_result` signature is fixed |

These are must-have tests before any BDE wiring code ships.

## Bridge tests

| Test | Expected |
|---|---|
| empty `items[]` | `populate_blanking_dc_fields` throws |
| bin barcode/name resolution | legacy child `bin_code` is a valid Asset |
| mapping-engine rows | cleared and rebuilt |
| `items.qty` missing | child still uses `net_weight` |
| partial clip use | Legacy `Item Clip Mapping.qty` reduced |
| full clip use | Legacy mapping retired |

## Ops tests

| Test | Expected |
|---|---|
| payload with one item | Stock Entry has source + target rows |
| batch convention | both rows use `CB_<compound>_<spp_batch>` |
| no items | Failed response |
| missing compound/batch/qty | Failed response |
| no Cutbit stock | clear failure message |

## End-to-end smoke

| Step | Expected |
|---|---|
| Seed clip mapping and blanking bin | Dash scan succeeds |
| Submit one row | Console bin mapping created |
| Legacy leg | BDE submitted and Asset Movement exists |
| Ops leg | Stock Entry submitted or clear Cutbit batch failure |
| Callback | Local sync status updates after code fix |

## UAT checklist

| Check | Pass condition |
|---|---|
| Clip scan after operator/item selection | resolved and focus moves to bin |
| Bin scan | tare weight displayed |
| Gross weight | net weight shown |
| Overweight row | blocked |
| Success modal | target statuses visible |

## Test gate

If BDE code is changed later, do not push with only syntax checks. This path touches local process masters, Legacy Asset Movement, and Ops Stock Entry semantics.
