# 07 — End-to-end flow

## Legacy Desk flow

| Step | Actor/system | Action |
|---|---|---|
| 1 | Operator | Opens Blank Bin Issue. |
| 2 | Operator | Scans moulding lot / Job Card barcode into `scan_production_lot`. |
| 3 | Legacy JS | Calls `validate_blank_issue_barcode(..., "scan_production_lot")`. |
| 4 | Legacy Python | Resolves open moulding Job Card and returns production context. |
| 5 | Operator | Scans physical bin barcode into `scan_bin`. |
| 6 | Legacy JS | Calls `validate_blank_issue_barcode(..., "scan_bin", production_item)`. |
| 7 | Legacy Python | Resolves Asset + Item Bin Mapping, checks location/item/BOM compound. |
| 8 | Legacy JS | Copies returned values to parent fields. |
| 9 | Legacy validate | Rebuilds `items` child table from parent fields. |
| 10 | Operator | Submits BBI. |
| 11 | Legacy | Parent submitted; child row remains `is_completed = 0`. |

## MPE continuation

| Step | Actor/system | Action |
|---|---|---|
| 12 | MPE lot validation | Requires submitted Line + Patrol IE. |
| 13 | MPE lot validation | Queries submitted BBI child rows for lot with `is_completed = 0`. |
| 14 | MPE | Builds bin consumption list from BBI + Item Bin Mapping. |
| 15 | MPE submit | Creates Manufacture Stock Entry and updates Job Card/Work Order. |
| 16 | MPE `update_bins` | Marks BBI item complete and retires/reduces Item Bin Mapping. |

## Future Console flow

| Step | Expected target |
|---|---|
| Dash scan | Must use lot barcode and bin barcode, not hidden document names. |
| Console local create | Creates local audit parent and child row. |
| Bridge | Creates Legacy BBI with identical parent/child semantics. |
| Ops | Creates reservation/log equivalent, not Stock Entry. |
| Callback | Updates Console sync state; does not mark BBI complete. |
| MPE | Owns completion of BBI child rows. |

