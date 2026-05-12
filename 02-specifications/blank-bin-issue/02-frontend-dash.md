# 02 — Frontend / Dash

## Current Console `develop`

No BBI Dash component was found on current `develop`:

| Search | Result |
|---|---|
| `BlankBinIssueEntry.tsx` | Not present on `develop`. |
| `BLANK_BIN_ISSUE` in Dash source | No hits on `develop`. |
| process registry entry | No BBI registration on `develop`. |

## Stale Console prototype evidence

The live `iyyanarr/shree_polymer_console` remote only exposed `develop` when checked on 2026-05-12. A stale local remote-tracking ref/commit still showed a prototype Dash component:

| File | Finding |
|---|---|
| `dash/src/components/processes/BlankBinIssueEntry.tsx` | Adds a scan screen for operator, Job Card, bin, and actual qty. |
| `dash/src/lib/processRegistry.tsx` | Registers `BLANK_BIN_ISSUE`. |
| `api.py` | Adds dummy `validate_job_card` and `validate_bin` helpers. |

The actual live Bin Issue branches found on 2026-05-12 are in `shree_polymer_custom_app` (`Bin-issue`, `Bin-issue-roleback`, `bin-rollback-issue`), not in the live Console remote branch list.

The component payload shape is:

```ts
{
  reference_id: Date.now().toString(),
  metadata: {
    process_type: "BLANK_BIN_ISSUE",
    process_code: processCode
  },
  context_data: {
    operator_id,
    operator_name,
    date,
    job_card,
    item,
    press,
    mould,
    batch,
    bin,
    compound,
    actual_qty
  },
  run_as: currentUser
}
```

## Prototype drift vs legacy

| Area | Legacy Desk | Branch prototype | Drift |
|---|---|---|---|
| Job Card scan | Scans lot barcode and resolves `Job Card.batch_code` with operation `Moulding`. | Calls `validate_job_card(job_card)` and loads `Console Job Card` by name. | Scans different identity. |
| Job Card status | Requires `Work In Progress`. | Blocks only cancelled/completed. | Missing WIP-only invariant. |
| Bin scan | Resolves `Asset.barcode_text` -> active `Item Bin Mapping`. | Loads `Console Blanking DC Entry` by input. | Scans source document, not physical bin Asset barcode. |
| Location check | Requires Asset location equals `SPP Settings.to_location`. | No location check found. | Missing physical-location invariant. |
| BOM compound check | Validates bin compound against active BOM compound. | Only checks production item equality. | Missing BOM compound invariant. |
| Quantity | Uses `Item Bin Mapping.qty`; parent `qty` copied to child. | Requires user-entered `actual_qty`. | Adds a field not present in legacy BBI schema. |

## Frontend target shape

When ported, the Dash should mirror legacy scan semantics:

| Step | Required lookup |
|---|---|
| Operator | Console employee / role validation. |
| Lot scan | Resolve lot barcode to open moulding Job Card by `batch_code`. |
| Bin scan | Resolve physical bin barcode to Asset + active Item Bin Mapping. |
| Review | Show production item, qty to manufacture, press, mould, bin, bin weight, compound, SPP batch number, qty, bin name. |
| Submit | Send a BBI-specific payload that can create parent + one child issue row. |
