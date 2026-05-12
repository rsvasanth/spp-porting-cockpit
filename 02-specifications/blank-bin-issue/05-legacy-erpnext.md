# 05 — Legacy ERPNext

## DocTypes

| DocType | Role |
|---|---|
| `Blank Bin Issue` | Submitted parent reservation record. |
| `Blank Bin Issue Item` | One child row carrying Job Card/bin/material context and `is_completed`. |

Parent naming series is `PE-.#####`.

## Legacy validation

`BlankBinIssue.validate()` performs three important actions:

| Behavior | Detail |
|---|---|
| Rebuilds child rows | Clears `self.items` and appends one row copied from parent fields. |
| Preserves completion flag | If an existing child had `is_completed`, the rebuilt row carries it forward. |
| Requires scans | Throws if `scan_production_lot` or `scan_bin` is missing. |

This child rebuild is odd but load-bearing: parent fields are the scan workspace; child row is the durable issue line MPE reads.

## Lot scan

`validate_blank_issue_barcode(barcode, "scan_production_lot", docname)`:

| Check | Legacy behavior |
|---|---|
| Job Card lookup | `Job Card` where `batch_code = barcode` and `operation = "Moulding"`. |
| Status | Must be `Work In Progress`. |
| Response | Returns Job Card name, production item, quantity, workstation, mould reference, status. |
| Duplicate issue check | Present but commented out. |

## Bin scan

`validate_blank_issue_barcode(barcode, "scan_bin", docname, production_item)`:

| Check | Legacy behavior |
|---|---|
| Bin lookup | `Asset.barcode_text` joined to active/latest `Item Bin Mapping`. |
| Retired bin | `is_retired = 1` returns "No item found in Scanned Bin." |
| Bin weight | Asset `bin_weight` must exist. |
| Location | Asset location must equal `SPP Settings.to_location`. |
| Item match | `Item Bin Mapping.mat` must equal Job Card production item. |
| Compound match | `Item Bin Mapping.compound` must match a Compound item in active BOM for the production item. |

## MPE dependency

MPE uses BBI as a hard gate:

| MPE behavior | Evidence |
|---|---|
| Requires open BBI rows | Query joins `Blank Bin Issue Item`, `Job Card`, and `Blank Bin Issue` where `BI.is_completed = 0` and parent submitted. |
| Uses BBI row identity | Pulls child row name as `blank_bin_issue_item_name`. |
| Completes BBI rows | `update_bins()` sets `Blank Bin Issue Item.is_completed = 1` after consumption. |
| Updates Item Bin Mapping | Fully consumed bins are retired; balance bins keep reduced qty. |

## Planning cancellation dependency

Legacy/Ops Work Planning and Add On Work Planning cancellation guards block cancellation if a submitted BBI exists for the Lot's Job Card batch code. This makes BBI a downstream commitment, not just a temporary scan form.

