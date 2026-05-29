# 04 — Non-functional requirements

Format: `NFR-QC-<n>`.

## Performance

**NFR-QC-01** — Scan-to-render latency for the parameter grid MUST be <500ms on a typical shop-floor tablet (Chrome/Android, 4G).

**NFR-QC-02** — Submit-to-confirmation latency MUST be <3s for the happy path (Ops + Legacy reachable).

## Resilience

**NFR-QC-03** — Submit MUST be async at the Bridge layer (existing `initialize_submission` + `execute_submission_step` pattern). The Console UI MUST NOT block the user thread on Ops or Legacy round-trips beyond the synchronous-Bridge handshake already used by other processes.

**NFR-QC-04** — A failed Ops or Legacy leg MUST be retryable via the existing `Console Transaction Log` retry mechanism without operator re-entry.

**NFR-QC-05** — Cancellation MUST be async at the cascade layer; intermediate failures MUST leave the system in a recoverable state, never a silent half-cancel.

## Sync freshness

**NFR-QC-06** — `Console SPP QC Template` cache MUST display its `last_synced` timestamp prominently when the inspector is blocked by a missing template.

**NFR-QC-07** — On-demand sync (FR-QC-07) MUST complete or timeout within 5s.

**NFR-QC-08** — Scheduled template sync MUST run at least hourly (NOT daily) on Console-side cron.

## Auditability

**NFR-QC-09** — `Console Transaction Log` MUST capture: request payload, response payload, employee identities scanned, template version (sync_hash) used.

**NFR-QC-10** — A cancelled `SPP Quality Control` MUST remain queryable with all original fields preserved (`docstatus=2`, no destructive delete).

## Security

**NFR-QC-11** — All `SPP Quality Control` whitelisted endpoints MUST be restricted to `methods=["POST"]`.

**NFR-QC-12** — All `frappe.db.sql` usage in QC code paths MUST use parameter binding (`%(name)s`); no f-string user-value interpolation.

**NFR-QC-13** — Permissions MUST follow the role matrix in `02-actors-and-roles.md`. Any `ignore_permissions=True` usage MUST be documented inline with its rationale.

## Compatibility

**NFR-QC-14** — Shop-floor scanners are HID keyboard-wedge by default. The UI MUST handle both Tab and Enter terminators interchangeably.

**NFR-QC-15** — Backend MUST tolerate variant Items: a template bound to a template-Item MUST resolve for scanned variant-Items unless the Item Group explicitly disables this (configured per-template).
