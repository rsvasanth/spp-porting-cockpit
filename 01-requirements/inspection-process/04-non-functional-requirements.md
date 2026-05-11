# 04 — Non-functional requirements

## NFR-INS — Performance

### NFR-INS-001 — Scan lookup latency
Scanning a compound barcode must return identity and stock context within 1 second under normal load.

### NFR-INS-002 — Reading entry responsiveness
Pass/fail state for readings must update immediately enough for the inspector to understand whether the batch is trending Accepted or Rejected before submit.

### NFR-INS-003 — Deviation queue responsiveness
The pending Deviation list must load rejected inspections within 2 seconds under normal shift volume.

### NFR-INS-004 — Submit latency
Normal successful submissions should complete within 30 seconds wall-clock, including target feedback.

## NFR-INS — Reliability

### NFR-INS-010 — Single-leg failure tolerance
If one ERP is unavailable, the available leg must still be allowed to complete when the business target intent allows it.

### NFR-INS-011 — Rejected-CI target clarity
Rejected CIs intentionally skip Legacy. The system must make this distinguishable from an accidental Legacy failure.

### NFR-INS-012 — Deviation recovery
A failed Deviation sync must be retryable without forcing the QM to re-enter source readings or reason.

### NFR-INS-013 — Concurrent callback safety
The callback aggregation must be reliable under near-simultaneous target responses. False Partial after both target legs succeed is unacceptable.

## NFR-INS — Data integrity

### NFR-INS-020 — Reading completeness
Required readings must not be silently omitted on strict submission.

### NFR-INS-021 — Identity consistency
Mix barcode, source inspection, batch identity, and `reference_id` must remain consistent across Console, Legacy, Bridge logs, and Ops logs.

### NFR-INS-022 — Deviation immutability
Once a Deviation is submitted, its QM decision, reason, and source link must be treated as audit facts. Corrections require cancellation/replacement, not silent edit.

### NFR-INS-023 — No duplicate disposition
One rejected CI must not receive two active QM dispositions.

### NFR-INS-024 — Cavity data quality
`cavity_no` must be treated as meaningful QA metadata. Defaulting it to 1 is acceptable only as a documented temporary mitigation.

## NFR-INS — Audit

### NFR-INS-030 — QM accountability
Every Deviation must identify the Quality Manager who authorized it.

### NFR-INS-031 — Reason quality
Deviation reason must be long enough to show intent and must be visible on the target Legacy record.

### NFR-INS-032 — Cross-log reconstruction
For any inspection or deviation in the last 90 days, engineering must be able to reconstruct the event from Console doc, Console Transaction Log, Legacy Bridge Log, and Ops MES Log.

### NFR-INS-033 — Fallback observability
Temporary fallbacks, especially `cavity_no = 1`, must emit structured logs or appear in drift reports.

## NFR-INS — Security and access

### NFR-INS-040 — Role enforcement
Only Quality Inspectors should submit Compound Inspections. Only Quality Managers or higher should authorize Compound Deviations.

### NFR-INS-041 — No operator self-override
The same operator who performed a regular inspection must not be able to convert a rejection into acceptance unless they also hold Quality Manager authority.

### NFR-INS-042 — Target credential isolation
Calls to Legacy Bridge and Ops must use configured authenticated channels. Credential failures must surface as target-leg failures, not ambiguous validation errors.

## NFR-INS — Maintainability

### NFR-INS-050 — Unified inspection extensibility
Adding a new inspection type should prefer the unified `Console Inspection` model with a Process Template, validation dispatch method, and reading specs.

### NFR-INS-051 — Shared helper preservation
Compound Inspection and Deviation identity resolution must remain shared. Forking the lookup logic creates drift risk.

### NFR-INS-052 — Test gate compliance
Any change to inspection validation, target routing, Bridge identity helpers, or callback aggregation must include relevant tests before push.

### NFR-INS-053 — Cockpit traceability
Every durable inspection behavior must trace to this requirements pack and the corresponding spec sections. Missing spec coverage is a drift item.

