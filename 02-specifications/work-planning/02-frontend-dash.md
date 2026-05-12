# 02 — Frontend / Desk behavior

## Current legacy UI

Legacy uses a Frappe Desk form, not Console Dash.

| UI element | Behavior |
| --- | --- |
| `date` | Required planning date |
| `shift_type` | Required shift type |
| `shift_series` | Hidden/read-only shift key used for uniqueness and lot generation |
| `shift_time` | Hidden/read-only shift time used for target lookup |
| `scan_supervisor` | Barcode scan for supervisor |
| `item_produced` | Product to add to plan row |
| `work_station` | Press/workstation |
| `mould` | Mould asset |
| `add` button | Adds a row to `Work Plan Item` |
| `items` | Child table with item, workstation, mould, BOM, Job Card, Lot # |

## Legacy client validations

| Validation | Legacy behavior |
| --- | --- |
| Supervisor scan | Calls `validate_supervisor`; fills employee ID/name or clears scan |
| Item filter | Filters by SPP Settings `item_group` |
| Workstation filter | Filters by SPP Settings workstation list |
| Mould filter | Calls `get_mould_list(item)` and filters Asset by mould references |
| Duplicate workstation | Blocks same press/workstation twice in the same plan |
| Duplicate mould | Blocks same mould twice in the same plan |
| BOM selection | Fetches valid BOMs and defaults child BOM |

## Post-submit action

When the Work Planning doc is submitted and `job_card_wo` is false, the form exposes "Create Work Order/Job Card". This calls `submit_workplan(docname, doctype, doc_info)`.

For Work Planning specifically, `doc_info` is passed from the child rows and then the helper writes selected BOM values back into `Work Plan Item`.

## Console target implication

Console should not model this as the Add On screen with a discriminator. A Work Planning Dash screen should make the one-per-shift base-plan rule visible:

| Console behavior | Requirement |
| --- | --- |
| Shift selection | Show if a submitted Work Planning already exists |
| Row entry | Support multiple item/mould/press rows |
| Duplicate row prevention | Keep duplicate press/mould validation |
| Job Card creation | Show generated Job Card and Lot # list |
| Downstream guard | Explain why cancellation is blocked |
