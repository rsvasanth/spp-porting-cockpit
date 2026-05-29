# 02 — Actors and roles

## Shop-floor actors

| Actor | Scans | Does |
|---|---|---|
| **Quality Inspector (QI)** | Own Employee badge, Lot barcode | Initiates inspection, enters parameter readings, submits |
| **Operator** | Own Employee badge | Co-signs the inspection (proves which operator was running the line) |
| **Supervisor** | — | Cancels submitted inspections (subject to Ops stock-availability check) |

Both Inspector and Operator are resolved as `Employee` (Frappe HR) via scanned badge barcode. The Console caches employee identity in `Console Employee`; barcode resolution happens against `Console Employee.barcode_text`.

## Back-office actors

| Actor | Where | Does |
|---|---|---|
| **Template Administrator** | Ops site (`25spp.local`) | Authors `SPP QC Parameter` + `SPP QC Template` records; binds templates to Items |
| **Sync Operator** | Ops + Console | Triggers manual template sync from the Console admin UI when an urgent template change is published |

## Permission boundaries

- QI: create + submit `SPP Quality Control` (own inspections only).
- Operator: read-only on `SPP Quality Control`.
- Supervisor: cancel submitted `SPP Quality Control`.
- Template Administrator: edit `SPP QC Template` on Ops; no Console access required.
- System Manager: full access to both sides.

All `ignore_permissions=True` usages on `SPP Quality Control` MUST be enumerated in the spec with written rationale. Default posture is RBAC, not bypass.

## Out-of-band actors

- **Legacy ERPNext users** — see `Inspection Entry` mirror created on `spp15.local`; no Console interaction.
- **Reporting users** — read `SPP Quality Control` via Frappe Report Builder; no direct doctype mutation.
