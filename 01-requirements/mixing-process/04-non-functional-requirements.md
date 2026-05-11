# 04 — Non-functional requirements

These are quality attributes that the system must satisfy across all functional requirements. Each is testable.

## NFR-MIX — Performance

### NFR-MIX-001 — End-to-end latency
Under normal load (one operator, no contention), a successful Mixing submission must complete within these limits:

| Phase | Target | Hard limit |
|---|---|---|
| `initialize_submission` (Console-side prep) | < 500 ms | 2 s |
| Each `execute_submission_step` HTTP roundtrip (per leg) | < 5 s | 30 s |
| Total wall-clock submission (Submit click → success modal) | < 10 s | 30 s |
| Auto-submit on Console doc (after both legs Synced) | < 2 s | 5 s |

**Measurement:** `Console Transaction Log.creation` → final state, parsed from log timestamps.

### NFR-MIX-002 — Concurrent operator throughput
The system must support at least **10 operators submitting simultaneously** across different workstations without:
- Race-condition data corruption (verified by FR-MIX-042)
- Latency degradation beyond 2× single-operator latency
- Transaction Log row collisions

### NFR-MIX-003 — Scan-to-validation latency
A raw material barcode scan must surface a validation result (success or failure) within **1 second** under normal load. Slow validation degrades operator throughput unacceptably.

## NFR-MIX — Reliability

### NFR-MIX-010 — Single-leg failure tolerance
If one ERP (Legacy or Ops) is unavailable for up to 15 minutes:
- Submissions to the available ERP must continue to succeed
- Console records must enter `sync_status = "Partial"` and remain submittable as Draft
- When the unavailable ERP comes back online, the operator must be able to retry the failed leg and reach `Success`

### NFR-MIX-011 — Bridge availability assumption
The Legacy Bridge must be highly available (> 99% during shift hours). Bridge downtime degrades the entire process. Bridge failures must surface clearly in `Console Transaction Log` so operators can escalate quickly.

### NFR-MIX-012 — Stale state recovery
If a submission is interrupted (browser refresh, network drop) mid-flight:
- The Console audit record must already exist (per FR-MIX-004)
- The operator must be able to resume from the `Console Transaction Log` list view by finding the reference_id and pressing Retry

### NFR-MIX-013 — Bridge-side rollback safety
If a Bridge-side submission fails mid-creation (e.g. DCR submits but Stock Entry creation fails), legacy must roll back the DCR + any partial documents (see legacy `rollback_wo_se_jc`). The Bridge must return a clear failure response so Console doesn't claim Legacy success.

## NFR-MIX — Data integrity

### NFR-MIX-020 — Cross-system referential integrity
At any steady-state moment (>60s after submission):
- For every successful Console Mixing record (`sync_status = "Success"`), corresponding records MUST exist on both Legacy and Ops
- For every `Partial` Console record, exactly one of Legacy / Ops must exist (the one that succeeded)
- `Failed` Console records must have NO records on either ERP

### NFR-MIX-021 — Stock ledger reconciliation
For every successful Mixing submission, the Stock Ledger Entries on Legacy and Ops must agree (within 0.001 kg tolerance for floating-point drift):
- Raw materials debited from source warehouses
- Finished good credited to target warehouse
- Item Batch Stock Balance updated on both sides

Reconciliation runs at shift-end; any discrepancies must be visible in a reconciliation report.

### NFR-MIX-022 — Idempotency under retry
The system must be safe to retry indefinitely. Multiple retries of the same `reference_id` must converge on the same state — never accumulate duplicate documents on any ERP.

## NFR-MIX — Audit

### NFR-MIX-030 — Audit trail completeness
For every submission (successful or failed):
- The full Dash payload must be stored in `Console <Mixing>.payload_snapshot` (JSON)
- The Bridge request + response must be stored in `Legacy Bridge Log` (full traceback on failure)
- The Ops engine outputs must be stored in `Shree Polymer MES Log` (`result_payload`, `error_message`, `traceback`)

Retention: minimum 90 days for all logs.

### NFR-MIX-031 — Identity traceability
For every submitted Mixing record, a query starting from either:
- The Console mix barcode, OR
- The Legacy DCR name, OR
- The Ops Stock Entry name

...must be able to reach the other two within 2 hops (via Bridge logs).

### NFR-MIX-032 — Operator accountability
Every submission must record the submitting Console User (`submitted_by`). For audit purposes, this must persist independent of session changes.

## NFR-MIX — Security / Access control

### NFR-MIX-040 — Role enforcement
- Mixing Operator role: required to submit
- Quality Inspector role: read-only
- Quality Manager: read + override (used during Compound Deviation flow)
- System Manager / Administrator: full access including backdating

These permissions must be enforced at:
- The Console doctype permissions layer (Frappe permission rows)
- The Dash UI (button gating)
- Server-side validation on `initialize_submission`

### NFR-MIX-041 — Cross-site authentication
Console's calls to Bridge and Ops must use authenticated channels:
- Legacy Bridge: API key + signature (managed via `Console Device Settings.legacy_bridge_url` and OAuth client)
- Ops: per-user OAuth token (relayed from operator's session)

Token failures must surface as clear errors, not silent retries.

### NFR-MIX-042 — Production-staging isolation
The Bridge and Ops URLs configured in `Console Device Settings` must not be confusable between staging and production environments. Misrouted submissions are a high-severity incident.

## NFR-MIX — Usability

### NFR-MIX-050 — Single-pass scan workflow
The operator must be able to complete a happy-path submission with **only a barcode scanner** — no typing required:
- Badge scan → operator
- Item dropdown click → produced item (acceptable since this is a small list)
- Raw material barcode scans → BOM rows
- Click "Submit" → done

### NFR-MIX-051 — Error UX
Every error message presented to the operator must:
- Be in plain English
- Avoid Frappe internal language (`ValidationError`, `frappe.throw`, tracebacks)
- Suggest a recoverable next action where possible

### NFR-MIX-052 — Network awareness
The Dash UI must visually indicate when the device is offline. Offline submissions are NOT supported — the operator must know not to submit until connectivity restores.

## NFR-MIX — Maintainability

### NFR-MIX-060 — Spec-and-test alignment
Every functional requirement must trace to a spec section ([08-traceability.md](08-traceability.md)). Every shipped code change that affects a spec section must update both the spec AND the corresponding traceability entry in the same PR.

### NFR-MIX-061 — Reversibility of customisations
The Mixing process implementation must remain understandable to a Frappe developer who knows ERPNext but is new to Console. Custom invariants (5-step `apply_bridge_result`, `from_local_cache` flag pattern) must be documented in specs with their rationale.

### NFR-MIX-062 — Test gate compliance
No code change to Mixing-related modules ships without:
- Relevant unit tests passing
- For changes to the 5-step pattern: a concurrency test added
- For changes to mapping seeders: a smoke test verifying the seeded mapping
- For changes to legacy code: explicit production overseer approval

This is the test-gate rule from `~/.claude/projects/-Users-alphaworkz-frappe-bench-apps-shree-polymer-console/memory/feedback_test_gate.md`.
