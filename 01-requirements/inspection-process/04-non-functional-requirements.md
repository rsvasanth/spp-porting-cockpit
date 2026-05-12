# 04 — Non-functional requirements

## NFR-INS — Performance

### NFR-INS-001 — End-to-end latency
| Phase | Target | Hard limit |
|---|---|---|
| `initialize_submission` | < 500 ms | 2 s |
| Each `execute_submission_step` HTTP roundtrip | < 5 s | 30 s |
| Total wall-clock (Submit → success modal) | < 10 s (CI) / < 12 s (CD with source fetch) | 30 s |
| Auto-submit on Console doc after both legs Synced | < 2 s | 5 s |

### NFR-INS-002 — Concurrent QI throughput
System must support **5 Quality Inspectors submitting CI simultaneously** without race-condition data corruption or latency degradation beyond 2× single-QI baseline.

### NFR-INS-003 — Source-CI fetch latency
The CD entry screen's source-CI fetch (`get_rejected_compound_inspection(mix_barcode)`) must return within **1 second**.

## NFR-INS — Reliability

### NFR-INS-010 — Single-leg failure tolerance
If Ops is unavailable: CI submissions queue locally as Pending; operator retries when Ops returns. If Legacy is unavailable: CD submissions land Ops-only and stay Partial until Legacy returns + retry.

### NFR-INS-011 — Saga regression protection
The 5-step `apply_bridge_result` pattern must be byte-identical across:
- `Console Inspection` (Phase 3 unified)
- `Console Compound Deviation` (legacy per-type)
- `Console Compound Inspection` (legacy per-type)

Drift between these implementations is a regression — covered by NFR-INS-052 below.

### NFR-INS-012 — cavity_no fallback resilience
Until cavity_no is properly wired, every fallback fire must produce a structured `frappe.log_error` entry with: `scan_compound`, `batch_no`, `reference_id`. Fallback must NEVER block the submission — logging failure is silently swallowed.

### NFR-INS-013 — 6-strategy SE lookup integrity
The strategy chain in `_lookup_legacy_stock_entry` must execute in priority order. Each strategy survives because it covers a real production case. Removing a strategy requires proof of zero hits in production `Legacy Bridge Log` for at least 90 days.

## NFR-INS — Data integrity

### NFR-INS-020 — Cross-system referential integrity at steady state
For every successful CI/CD record:
- `sync_status="Success"` Console record ↔ corresponding records exist on both ERPs (CD case) or on Ops only (Rejected CI case)
- `sync_status="Partial"` Console record ↔ exactly one of Legacy/Ops has the record (matching the Partial state's allocation)
- `sync_status="Failed"` Console record ↔ neither ERP has the record

### NFR-INS-021 — Identity consistency
For every successful submission:
- `Console <doctype>.mix_barcode == Legacy Compound Inspection.mix_barcode == Ops Stock Entry items[FG].mix_barcode`
- `Console <doctype>.reference_id == Legacy Compound Inspection.reference_id == Ops MES Log.reference_id`

### NFR-INS-022 — Stock ledger reconciliation
For CI Accepted + CD Accepted + CD Rejected submissions, Stock Ledger Entries on Ops must reflect the appropriate inventory move (within 0.001 kg tolerance). For Rework, no Stock Ledger movement is expected.

### NFR-INS-023 — Idempotency under retry
The system must be safe to retry indefinitely. Multiple retries of the same `reference_id` converge on the same state.

## NFR-INS — Audit

### NFR-INS-030 — Audit trail completeness
For every submission:
- Console doc: `payload_snapshot` JSON, per-leg sync status, `error_log_summary`
- Console Transaction Log: 1-2 rows (1 for Rejected CI; 2 for everything else)
- Legacy Bridge Log: 1 row per Bridge call (with `transformed_data` capturing what was sent to Legacy)
- Ops MES Log: 1 row with `result_payload` showing action outputs

Retention: minimum 90 days for all logs.

### NFR-INS-031 — Saga incident reconstruction
For any submission in the last 90 days, an engineer must be able to reconstruct the full event chain from a single `reference_id`. The chain must show: Dash submit time, per-leg Bridge/Ops call times, callback arrival times, final aggregate state.

### NFR-INS-032 — QM accountability for CD decisions
Every CD record must persistently record the deciding QM (`quality_approver_id`). For audit purposes, this must survive session changes and Console user updates.

## NFR-INS — Security / Access control

### NFR-INS-040 — Role enforcement
- Quality Inspector role: required for CI submit
- Quality Manager role: required for CD submit
- System Manager / Administrator: full access including backdating

Enforced at: Frappe doctype permissions + Dash UI gating + server-side `get_available_employees` filter.

### NFR-INS-041 — Cross-site authentication
Same as Mixing — Console's calls to Bridge and Ops use authenticated channels. Token failures surface as clear errors, not silent retries.

## NFR-INS — Usability

### NFR-INS-050 — Scan-driven workflow
CI: badge scan → mix_barcode scan → readings. Minimal typing.
CD: badge scan → mix_barcode scan → status dropdown → reason text.

### NFR-INS-051 — Error UX (plain English)
Specific to inspection: errors must clearly distinguish "the compound batch was not found" from "the source CI is not rejected" — both common operator confusion points.

### NFR-INS-052 — Status routing visibility
Before CD submission, the Dash must show the operator what will happen on the Ops side based on selected status (Accepted → Material Transfer SE; Rejected → write-off; Rework → no SE). Avoids QM confusion about downstream consequences.

## NFR-INS — Maintainability

### NFR-INS-060 — Spec-and-test alignment
Same rule as Mixing: every code change to inspection-related modules updates corresponding spec sections and `08-traceability.md` in the same PR.

### NFR-INS-061 — Saga story preservation
The Compound Deviation saga timeline (documented in spec `09-rollout-and-history.md`) must remain accurate as the **canonical incident history** for SPP's race-condition mitigation pattern. Future spec edits MUST NOT erase or "tidy up" this narrative.

### NFR-INS-062 — Test gate compliance
- For changes to `apply_bridge_result` on any inspection doctype: concurrency tests must pass before push
- For changes to the 6-strategy SE lookup: per-strategy test must demonstrate the new behavior + production-log evidence for any removed strategy
- For changes to `populate_compound_*_fields`: shared-helper compatibility test (CI + CD both pass)
- For changes to the factory-requirement skip: production overseer sign-off required (operations impact)
