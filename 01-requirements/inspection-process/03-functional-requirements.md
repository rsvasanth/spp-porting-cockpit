# 03 — Functional requirements

Each item is individually testable. Tags: `[CI-only]` for Compound Inspection, `[DEV-only]` for Compound Deviation.

## FR-INS — Compound Inspection submission

### FR-INS-001 [CI-only] — Scan compound identity
A Quality Inspector must be able to scan a compound mix barcode and resolve the source compound identity: item, batch, mix barcode, source warehouse, available quantity, and upstream stock reference.

### FR-INS-002 [CI-only] — Capture required readings
The system must capture the required compound readings at minimum: Hardness, Specific Gravity, TS2, and TC 90. Each reading must store observed value, allowed limits, unit, and pass/fail status.

### FR-INS-003 [CI-only] — Derive inspection status from readings
The inspection status must be:

| Reading state | Status |
|---|---|
| All required readings within spec | Accepted |
| One or more required readings out of spec | Rejected |

The operator must not manually mark a failed reading set as Accepted without the Deviation process.

### FR-INS-004 [CI-only] — Accepted CI syncs to both ERPs
An Accepted Compound Inspection must create the expected Console audit record and sync to both Legacy and Ops according to the normal parallel-sync model.

### FR-INS-005 [CI-only] — Rejected CI skips Legacy
A Rejected Compound Inspection must not be sent to Legacy immediately. It must sync to Ops only and remain visible for Quality Manager disposition through Compound Deviation.

### FR-INS-006 [CI-only] — Rejected CI remains discoverable
A rejected inspection must appear in the Deviation queue until an active Deviation exists for it.

## FR-INS — Compound Deviation submission

### FR-INS-010 [DEV-only] — Source must be rejected CI
A Compound Deviation must link to exactly one submitted Rejected Compound Inspection. Deviations cannot be created for Accepted, Draft, cancelled, missing, or non-compound inspection records.

### FR-INS-011 [DEV-only] — QM signoff required
Before submit, the system must capture and validate a Quality Manager identity. A Deviation without Quality Manager scan is not a valid business decision.

### FR-INS-012 [DEV-only] — Deviation reason required
The Quality Manager must enter a deviation reason with at least 5 non-whitespace characters.

### FR-INS-013 [DEV-only] — Supported dispositions
A Compound Deviation must support exactly these business statuses unless production overseer approves a change:

| Status | Business meaning |
|---|---|
| Accepted | QM override; material may proceed |
| Rejected | Material cannot be used |
| Rework | Material needs reprocessing before use |

### FR-INS-014 [DEV-only] — One active Deviation per source CI
The system must prevent more than one active Deviation for the same source Compound Inspection. Cancelled records may be excluded from this check.

### FR-INS-015 [DEV-only] — Identity continuity
The Deviation must carry the same mix barcode as the source CI. A mismatch must block strict submission.

### FR-INS-016 [DEV-only] — Read-only source context
The Deviation screen must show the source CI readings and identity as read-only context. The QM decision must not mutate the original inspection readings.

## FR-INS — Target behavior

### FR-INS-020 — Status-driven stock behavior
The downstream material movement must follow the final status:

| Final status | Required behavior |
|---|---|
| Accepted CI or Accepted Deviation | Material can move to the next ready warehouse |
| Rejected Deviation | Material is removed, scrapped, or otherwise blocked from production |
| Rework Deviation | No forward movement; material remains pending rework |

### FR-INS-021 — Legacy Deviation representation
Compound Deviation must land on Legacy as `Compound Inspection`, with QM fields and remarks populated. There must not be a separate legacy `Compound Deviation` target.

### FR-INS-022 — Ops status conditions
Ops actions must be conditional on status. A status-skipped run can still be a successful sync when no Stock Entry is required.

### FR-INS-023 — Cross-system identity round-trip
For every successful Accepted CI or Deviation, Console, Legacy, and Ops records must be traceable by `reference_id` and mix barcode.

### FR-INS-024 — Retry without duplication
Retrying a failed inspection or deviation leg must reuse the same `reference_id` and must not create duplicate target documents.

### FR-INS-025 — Partial state visibility
When only one required target leg succeeds, Console must show Partial or target-aware Success according to the target intent, and the failed or skipped leg must be explainable from Transaction Log.

## FR-INS — Audit and observability

### FR-INS-030 — Full payload audit
Every submission attempt must store the full payload snapshot on Console, even when strict validation would reject the Desk-path document.

### FR-INS-031 — Per-leg logs
Every attempted target leg must have a Console Transaction Log row with target, request, response, status, and error summary.

### FR-INS-032 — Saga-safe callback handling
Concurrent Ops and Legacy callbacks must converge to the correct final state. The business requirement is deterministic status, not a particular code pattern.

### FR-INS-033 — Source lookup diagnostics
If the Bridge cannot resolve the upstream Stock Entry for a CI or Deviation, the failure must be visible enough for engineering to identify whether the upstream Mixing/DCR sync is missing.

### FR-INS-034 — Cavity number capture
The system should preserve `cavity_no` from the original inspection through Deviation. If it cannot, the fallback must be visible as a data-quality drift item.

