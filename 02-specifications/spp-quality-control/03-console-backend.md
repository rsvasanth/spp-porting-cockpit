# 03 — Console backend specification

## Doctype: `SPP Quality Control`

**Module:** Shree Polymer Console
**App:** `shree_polymer_console`
**Naming series:** `SPP-QC-.YYYY.-.#####`
**Submittable:** Yes (`is_submittable: 1`)

### Parent fields

#### Identifiers & metadata
| Fieldname | Type | Options | Mandatory |
|---|---|---|---|
| `naming_series` | Select | `SPP-QC-.YYYY.-.#####` | 1 |
| `inspection_type` | Select | `Line\nPatrol\nLot\nIncoming\nFinal Visual` | 1 |
| `lot_no` | Data | — | 1 (except Incoming) |
| `item_code` | Link | Item | 1 |
| `workstation` | Link | Workstation | Conditional (Moulding) |
| `mould_reference` | Link | Asset | Conditional (Moulding) |

#### Scanned employee sign-offs
| Fieldname | Type | Options | Mandatory |
|---|---|---|---|
| `inspector` | Link | Employee | 1 |
| `operator` | Link | Employee | 1 |

Both fields resolve via barcode scan against `Console Employee.barcode_text`. The form stores the Employee link, not the raw barcode.

#### Quantities & calculations
| Fieldname | Type | Mandatory | Notes |
|---|---|---|---|
| `total_inspected_qty` | Float | 1 | Pieces (Nos) |
| `total_accepted_qty` | Float | 1 | Pieces (Nos) |
| `total_rejected_qty` | Float | 1 | Pieces (Nos) |
| `one_no_qty_equal_kgs` | Float | Conditional (Moulding) | Snapshotted from `Console Mould Specification` at scan time |
| `total_rejected_qty_kg` | Float | Conditional (Moulding) | `total_rejected_qty * one_no_qty_equal_kgs` |

#### Sync & transaction control
| Fieldname | Type | Options | Mandatory |
|---|---|---|---|
| `status` | Select | `Accepted\nRejected\nRework` | 1 |
| `reference_id` | Data | — | 1 (UUID, idempotency key) |
| `stock_entry_reference` | Data | — | 0 (filled by Bridge response) |
| `ops_sync_status` | Select | `Pending\nSuccess\nFailed` | 0 |
| `legacy_sync_status` | Select | `Pending\nSuccess\nFailed` | 0 |
| `template_sync_hash` | Data | — | 0 (snapshot of the template version used) |

### Child table: `SPP Quality Control Detail`

| Fieldname | Type | Options | Mandatory |
|---|---|---|---|
| `parameter` | Link | Console SPP QC Parameter | 1 |
| `reading_value` | Float | — | 1 |
| `nominal_value` | Float | — | 0 (copied from template) |
| `min_value` | Float | — | 1 (copied from template) |
| `max_value` | Float | — | 1 (copied from template) |
| `reading_status` | Select | `Pass\nFail` | 1 (computed in controller) |

## Cached read-only doctypes

### `Console SPP QC Parameter`
Sync replica of Ops `SPP QC Parameter`. Fields mirror Ops 1:1. Adds `ops_name`, `sync_hash`, `last_synced`.

### `Console SPP QC Template`
Sync replica of Ops `SPP QC Template` including its child parameter table. Fields mirror Ops 1:1. Adds `ops_name`, `sync_hash`, `last_synced`.

Both are non-submittable. Console has `read` only — writes come from the sync worker.

## Controller (`spp_quality_control.py`)

### `validate()`
1. Assert `inspector != operator` (same-person block).
2. Re-resolve `Console SPP QC Template` for `item_code`; raise if missing or `last_synced` older than 24h.
3. For each child row: recompute `reading_status` server-side (`Pass` iff `min <= reading <= max`). Override any frontend value.
4. For Moulding inspections: recompute `total_rejected_qty_kg = total_rejected_qty * one_no_qty_equal_kgs`. Override any frontend value.
5. Assert `total_inspected_qty == total_accepted_qty + total_rejected_qty`.
6. Stamp `template_sync_hash` from the cached template at validate-time.

### `on_submit()`
1. Generate `reference_id` (UUID v4) if not present.
2. Build Bridge payload via `build_transaction_payload` (existing helper in `api.py`).
3. Call `initialize_submission` → `execute_submission_step` for the Ops leg and the Legacy leg.
4. Log every leg into `Console Transaction Log`.

### `on_cancel()`
Cascade per [`07-end-to-end-flow.md`](07-end-to-end-flow.md). Ops first → Legacy second → local docstatus last.

## Whitelisted endpoints

| Endpoint | Methods | Purpose |
|---|---|---|
| `submit_spp_quality_control` | POST | Create + submit from dash |
| `cancel_spp_quality_control` | POST | Supervisor cancel |
| `sync_qc_templates_now` | POST | On-demand template refresh |
| `validate_qc_template_for_item` | POST | Pre-submit gate check |
| `resolve_employee_by_barcode` | POST | Barcode → Employee resolution |

All endpoints declared with `@frappe.whitelist(methods=["POST"])`. No GET-based mutators.

## Permission matrix

| Role | Read | Write | Submit | Cancel |
|---|---|---|---|---|
| Quality Inspector | own | own | own | — |
| Operator | own | — | — | — |
| Supervisor | all | — | — | all |
| System Manager | all | all | all | all |

No `ignore_permissions=True` usage permitted in the QC controller without inline justification.
