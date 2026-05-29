# 06 — Ops ERPNext

## Master data (already exists)

The following doctypes already exist on Ops (`shree_polymer_ops` app) — no new schema work required:

- `SPP QC Parameter`
- `SPP QC Template`
- `SPP QC Template Parameter` (child)

### `SPP QC Parameter` (Ops master)

| Field | Type | Notes |
|---|---|---|
| `parameter_name` | Data, Unique | e.g., `Hardness`, `Specific Gravity`, `TS2`, `TC90` |
| `uom` | Link to UOM | e.g., `Shore A`, `g/cc`, `Minutes` |
| `description` | Small Text | Testing instructions |

### `SPP QC Template` (Ops master)

| Field | Type | Notes |
|---|---|---|
| `template_name` | Data, Unique | — |
| `item_code` | Link to Item | Mandatory; binds template to a single Item |
| `is_active` | Check | Inactive templates are not synced to Console |
| `parameters` | Table of `SPP QC Template Parameter` | Tolerance bands |

### `SPP QC Template Parameter` (child)

| Field | Type | Mandatory |
|---|---|---|
| `parameter` | Link to `SPP QC Parameter` | 1 |
| `nominal_value` | Float | 0 |
| `min_value` | Float | 1 |
| `max_value` | Float | 1 |
| `testing_instrument` | Data | 0 |

## Sync (Ops → Console)

A scheduled job pulls incremental updates of `SPP QC Parameter` and `SPP QC Template` (plus child rows) from Ops to Console via authenticated REST API.

| Trigger | Cadence | Mechanism |
|---|---|---|
| Scheduled | Hourly | Frappe scheduler on Console |
| Manual | On-demand | Console admin UI button + dash modal "Sync templates now" |

Sync is incremental — diffed by `modified` timestamp. Soft-deleted (`is_active = 0`) templates are tombstoned on Console (kept as record but excluded from gate checks).

The Console-side sync handler updates `Console SPP QC Parameter` and `Console SPP QC Template` records, stamping `last_synced` and a `sync_hash` for round-trip verification.

## Stock Entry creation

QC submission triggers a Stock Entry create via Bridge POST to a new Ops endpoint:

`shree_polymer_ops.api.spp_quality_control.create_stock_entry_from_qc(payload)`

### Stock Entry shape (per inspection type)

| Inspection type | Stock Entry type | docstatus on create | s_warehouse | t_warehouse | qty UOM |
|---|---|---|---|---|---|
| Line | Material Transfer | 0 (Draft) | Source (from template) | Rejection (from template) | Kg |
| Patrol | Material Transfer | 0 (Draft) | Source | Rejection | Kg |
| Lot | Material Transfer | 0 (Draft) | Source | Rejection | Kg |
| Incoming | Material Transfer | 0 (Draft) | Source | Rejection | Nos |
| Final Visual / PDIR | Material Transfer | 1 (Submitted) | Source | Target/PDIR | Nos |

### Idempotency

The Ops endpoint stamps `custom_reference_id` (= incoming `reference_id`) on the SE at create time. Before creating, it checks for an existing SE with the same `custom_reference_id` and returns that one if found (no duplicate).

### Draft SE closer

Line / Patrol / Lot / Incoming SEs are created at `docstatus = 0`. The closer is:

- **Default:** end-of-shift batch job (`spp_quality_control.close_pending_draft_ses`) that submits all QC-originated draft SEs for the shift.
- **Override:** Supervisor manual submit via Ops UI.
- **Cancellation path:** on Console QC cancel before the draft is closed, the draft SE is deleted (drafts can be deleted; submitted SEs require cancel).

The closer is configured per Process Template via a `draft_close_strategy` parameter; default value `end_of_shift_batch`.

### Cancellation endpoint

`shree_polymer_ops.api.spp_quality_control.cancel_stock_entry_from_qc(reference_id)`

Behavior:
- Find SE by `custom_reference_id`.
- If `docstatus = 0` → delete.
- If `docstatus = 1` → attempt cancel; raise on stock-consumed / ledger-locked errors.
- Return structured error code (`ok` / `stock_consumed` / `not_found` / `permission_denied`).

## What Ops does NOT do

- Does NOT define QC templates beyond the master schema (no template authoring UI added in this motion).
- Does NOT mirror to Legacy (that's the Console's Bridge orchestration responsibility).
- Does NOT enforce QC business rules — the Console controller is the authoritative validator.

## Zero-Logic Ops invariant

Per the Zero-Logic Ops architectural principle (see `02-specifications/work-planning/04-bridge-layer.md` and the `00-program-charter`), the Ops endpoint MUST be a thin wrapper over native ERPNext APIs:

- Create / cancel / delete Stock Entry via `frappe.get_doc(...).insert()` / `.submit()` / `.cancel()` / `.delete()`.
- No business rules in the Ops handler. All QC validation lives on the Console.
- The Ops endpoint's only logic is idempotency + structured error reporting.
