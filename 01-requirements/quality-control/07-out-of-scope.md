# 07 — Out of scope

## Compound Inspection / Compound Deviation

QC explicitly does NOT cover the Compound family. Compound Inspection and Compound Deviation continue to live on `Console Inspection` (the Phase 3 unified doctype shipped 2026-05-01). This split is intentional:

- Compound has its own deviation-override workflow (QM signoff) that production-line QC does not need.
- Compound identity resolution is multi-strategy (6-strategy `_resolve_compound_identity` lookup); QC identity is single-strategy (Lot Number → Work Plan).
- Compound runs once per batch; QC types run many times per shift.

See [`../inspection-process/`](../inspection-process/) for the Compound requirements and [`../../02-specifications/console-inspection-unification/`](../../02-specifications/console-inspection-unification/) for its spec.

## Variant of inspection types

The 5 inspection types in scope are exactly `Line`, `Patrol`, `Lot`, `Incoming`, `Final Visual` / `PDIR`. Other inspection forms — first-piece approval, supplier audit, periodic calibration — are NOT in this motion. Add them as future `inspection_type` enum values only after a written extension to this requirements doc.

## Reporting and analytics

`SPP Quality Control` is the system of record; reporting dashboards (yield, reject rate, top-defect-parameter) are downstream consumers built later. Out of scope here.

## Template authoring UI

`SPP QC Parameter` and `SPP QC Template` are authored on Ops via standard ERPNext forms. No Console-side template editor is in scope; templates flow one-way Ops → Console.

## Calibration of testing instruments

The `testing_instrument` field on `SPP QC Template Parameter` is metadata; calibration tracking, due-date alerts, and instrument-out-of-cal blocks are NOT in scope.

## Mobile / offline mode

Shop-floor tablets are assumed online. Full offline-first PWA support (cache submissions locally, replay on reconnect) is out of scope. Brief network blips during submission are handled by the existing Bridge retry mechanism, not by an offline cache.

## Bulk template upload

Templates are authored one-at-a-time on Ops. Spreadsheet bulk-upload is NOT in scope; if needed, use ERPNext's standard import tools manually.

## Auto-rejection actions

Auto-cancellation of a Job Card on `Rejected` status, auto-creation of a Stock Reservation Entry, or any reactive workflow beyond the Stock Entry cascade is OUT of scope.

## Inspector certification gates

"Only certified inspectors can submit X" rules are not in scope. The Permissions matrix in `02-actors-and-roles.md` is role-based, not skill-matrix-based.
