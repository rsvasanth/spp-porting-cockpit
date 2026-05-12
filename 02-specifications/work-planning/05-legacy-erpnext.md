# 05 — Legacy ERPNext behavior

## DocType identity

| Legacy DocType | Series | Child table |
| --- | --- | --- |
| `Work Planning` | `WRKP-.#####` | `Work Plan Item` |

## Validate

Legacy `validate()` enforces:

| Check | Behavior |
| --- | --- |
| `shift_series` present | Throws if missing |
| `shift_time` present | Throws if missing |
| Amendment reset | Clears `job_card_wo` when amended |
| Shift uniqueness | Calls `validate_shift_mould()` |
| Item rows present | Throws if no rows |
| Target qty exists | Queries `Work Plan Item Target` for each item and selected `shift_time` |

## Shift uniqueness

`validate_shift_mould()` checks for an existing submitted Work Planning with:

| Field | Match |
| --- | --- |
| `date` | Same date |
| `shift_series` | Same shift series |
| `name` | Not current doc |
| `docstatus` | Submitted |

If found, Legacy throws that the shift is already scheduled in the existing plan.

## Work Order creation

`on_submit_value()` calls `validate_bom()` and then `create_work_order()`.

`create_work_order()`:

| Behavior | Detail |
| --- | --- |
| Reads SPP Settings | Requires `target_qty` and `default_time` |
| Resolves BOM | Default active BOM unless child `bom` selected |
| Calculates quantity | `SPP Settings.target_qty * Work Plan Item Target.target_qty` |
| Creates Work Order | `MFG-WO-.YYYY.-`, company `SPP`, source sheeting warehouse, WIP warehouse |
| Adds operation | Operation `Moulding`, workstation from child row |
| Submits via `docstatus = 1` save | Native ERPNext Work Order side effects apply |

## Job Card update

`update_job_cards()`:

| Behavior | Detail |
| --- | --- |
| Fetches Job Cards for Work Order | Native created cards |
| Generates Lot # | Date + month code + day + shift series + serial |
| Generates barcode image/text | Stored on Job Card |
| Sets shift fields | `shift_type`, `shift_supervisor` |
| Sets mould reference and specs | From Mould Specification and Press Mould Specification |
| Writes child row | Updates `Work Plan Item.job_card` and `lot_number` |
| Saves Moulding Serial No | One serial per Job Card |

## Cancel

Before cleanup, Legacy checks each child Job Card Lot #:

| Downstream check | Effect |
| --- | --- |
| Submitted `Blank Bin Issue.scan_production_lot` | Blocks cancellation |
| Submitted `Moulding Production Entry.scan_lot_number` | Blocks cancellation |

If allowed, it cancels/deletes linked Job Cards and Work Orders, deletes Moulding Serial No rows, clears child `job_card`, and commits.

## Technical risk

Legacy uses direct `db_set`, `db.delete`, and manual commits. The business guard is important; the technical deletion pattern should be treated carefully in any port.
