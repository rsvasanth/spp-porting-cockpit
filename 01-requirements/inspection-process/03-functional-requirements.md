# 03 — Functional requirements

Each requirement is **numbered**, **individually testable**, and **traced to specs** in `08-traceability.md`. Variant-specific requirements are tagged `[CI-only]` or `[CD-only]`; everything else applies to both.

## FR-INS — Submission flow

### FR-INS-001 — Single-actor submission
A Quality Inspector (for CI) or Quality Manager (for CD) must be able to submit by:
1. Scanning their employee badge (validates role membership in `Quality Inspector` or `Quality Manager`)
2. Scanning the compound's `mix_barcode` (CI) or the rejected compound's barcode (CD)
3. Reviewing source-CI context (CD-only)
4. Entering readings (CI) or selecting status + reason (CD)
5. Pressing Submit

Submission must complete and surface success/failure feedback within **30 seconds** under normal load.

### FR-INS-002 — Phase 3 unified routing
New submissions for both CI and CD must land in the unified `Console Inspection` doctype. The `inspection_type` field discriminates the variant. Pre-Phase-3 records remain in per-type Console doctypes (`Console Compound Inspection`, `Console Compound Deviation`) for read access.

### FR-INS-003 — Parallel multi-system sync
A successful CI/CD submission must produce equivalent records on:
- **Legacy** ERPNext: a `Compound Inspection` record with appropriate `status` + `quality_approver_*` fields populated
- **Ops** ERPNext: a status-conditional `Stock Entry` (per FR-INS-021)

Both records must use the same Console-generated `reference_id`.

### FR-INS-004 — Audit trail invariant
Every submission attempt — including those with incomplete payloads — must leave a record on Console for diagnostic purposes. The `payload_snapshot` field must contain the full submitted payload as JSON for replay.

### FR-INS-005 — Identity round-trip via mix_barcode
Both CI and CD must use the upstream Mixing's `mix_barcode` as the cross-system identity key. Bridge's 6-strategy SE lookup uses this value to resolve the underlying manufacturing Stock Entry on Legacy. Identity must NEVER be regenerated downstream.

## FR-INS — CI-specific

### FR-INS-010 [CI-only] — Reading capture against BOM spec
For each CI submission, the operator must record readings for every parameter defined on the compound's BOM. Each reading must be validated against the BOM-attached min/max spec:

- Reading within spec → Pass for that parameter
- Reading outside spec → Fail for that parameter

### FR-INS-011 [CI-only] — Auto-derived status
The overall CI status must be auto-derived from the per-parameter pass/fail results:
- All parameters Pass → `status = "Accepted"`
- Any parameter Fail → `status = "Rejected"`

The Quality Inspector may not manually override this derivation.

### FR-INS-012 [CI-only] — Factory-requirement skip on Rejected
A Rejected CI must NOT POST to the Legacy Bridge. Only the Ops leg fires. The Console record's `target_system` is set to `"Ops"` (not `"Both"`), and `sync_status="Partial"` is **not an error** — it's the expected steady state until a CD closes the Legacy gap.

### FR-INS-013 [CI-only] — Material Transfer SE on Accepted
A successful Accepted CI must create a Stock Entry on Ops with purpose `Material Transfer` — moving the compound from inspection-WIP warehouse to ready-for-Sheeting warehouse. A Rejected CI must NOT create any Stock Entry on Ops at submit time (deferred until a CD closes it).

### FR-INS-014 [CI-only] — Source SE linkage
The CI record must link back to the upstream Mixing's manufacturing Stock Entry via the Bridge's `_lookup_legacy_stock_entry` 6-strategy chain. The resolved `stock_id` is mandatory on Legacy CI submission.

## FR-INS — CD-specific

### FR-INS-020 [CD-only] — Source CI prerequisite
A CD submission must reference an existing CI with `status="Rejected"`. Dash blocks submission if no such CI exists for the scanned compound barcode.

### FR-INS-021 [CD-only] — Status-conditional Ops behavior
- `status="Accepted"` → Ops creates a Material Transfer SE (overrides the original rejection; compound moves to ready warehouse)
- `status="Rejected"` → Ops creates a Material Issue / write-off SE (compound removed from inventory)
- `status="Rework"` → Ops creates NO Stock Entry (compound stays in inspection-WIP; operator returns it to mixing manually)

### FR-INS-022 [CD-only] — Deviation reason capture
The `deviation_reason` field must be required (minimum 5 characters) at the Console controller layer. Empty or trivial reasons are rejected. The reason is mapped to legacy `remarks` on the Compound Inspection record.

### FR-INS-023 [CD-only] — QM signoff capture
Each CD must record the submitting QM as `quality_approver_id` + `quality_approver_name`. These fields are mapped to legacy `scan_quality_approver`, `quality_approver_id`, `quality_approver_name`.

### FR-INS-024 [CD-only] — Both legs fire (no factory-requirement skip)
Unlike CI, a CD submission MUST fire BOTH Ops and Legacy legs regardless of status. This is what closes the Legacy gap for previously-rejected CIs.

## FR-INS — Cross-flow

### FR-INS-030 — Reference ID round-trip
Console must generate a unique `reference_id` (13-digit ms timestamp). The ID must:
- Be unique on the Console Inspection doctype
- Round-trip to Legacy as the CI's `reference_id` field
- Round-trip to Ops as the MES Log's `reference_id` field
- Be respected as the idempotency key on retry

### FR-INS-031 — cavity_no fallback (active TODO)
Until `cavity_no` is wired through Console's `Console Inspection` doctype + Dash UI + payload, the Bridge's `_apply_deviation_extras` must default `cavity_no = 1` on legacy submission. Every fallback fire must emit a structured log entry for ops awareness.

### FR-INS-032 — Idempotent submission
A second submission with the same `reference_id` must be cleanly rejected:
- Console: unique constraint violation surfaces as a clean error to the operator
- Legacy: `find_existing_record` returns the cached CI; no duplicate created
- Ops: `Shree Polymer MES Log` lookup returns cached result; no duplicate SE

### FR-INS-033 — Idempotent leg retry
A retry of a failed leg (`Console Transaction Log` row in `Failed` status):
- Reuses the same `reference_id`
- Legacy/Ops deduplicate; existing record returned
- On second success, Console's `apply_bridge_result` promotes `sync_status` from `Partial`/`Failed` to `Success` and auto-submits the Console doc

### FR-INS-034 — Concurrent callback safety (saga invariant)
When Ops and Legacy callbacks land near-simultaneously, the final state of the Console record must be deterministic: `sync_status` correctly aggregated from per-leg DB state (not in-memory), and `docstatus=1` after auto-submit. This is the load-bearing requirement that drove the 5-step `apply_bridge_result` pattern. **Any change to callback handling must preserve this.**

## FR-INS — UX

### FR-INS-040 — Role-based screen access
- `Quality Inspector` role: sees CI submission screen; cannot access CD submit
- `Quality Manager` role: sees CD submission screen + read access to CI
- Both roles: must be able to view the `Console Transaction Log` for their own submissions

### FR-INS-041 — Source-CI fetch on CD entry
When a QM scans a compound barcode in CD entry, the Dash must call a backend lookup that:
- Finds the source CI (Console Inspection with `status="Rejected"`)
- Returns the CI's full identity + readings as read-only context
- Blocks CD submission if no Rejected CI is found

### FR-INS-042 — Live Feedback per-target status
Same Live Feedback pattern as Mixing: per-target row transitioning Pending → Processing → Success/Failed. Visible within 1 second of each transition.

### FR-INS-043 — Backdating restrictions
- Regular QI/QM: `posting_date` clamped to "today or yesterday"
- System Manager / Administrator: arbitrary backdating allowed
- Forward-dating rejected for all roles

## FR-INS — Logging and observability

### FR-INS-050 — Per-leg transaction log
Every submission produces one `Console Transaction Log` row per target ERP (1 row for Rejected CI; 2 rows for everything else). Each row records: target ERP, request payload, response, final status, timing.

### FR-INS-051 — Error visibility to operator
On any leg failure, the operator must see: which leg failed, a plain-English error summary, a Retry button that does not require re-entering data.

### FR-INS-052 — Saga regression test coverage
A concurrency test must exist for the 5-step `apply_bridge_result` on both Console Inspection and Console Compound Deviation doctypes. The test simulates two threads firing Ops + Legacy callbacks simultaneously and asserts final state is correctly aggregated.
