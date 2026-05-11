# 06 — Acceptance criteria

These are plain-language UAT scripts for staging.

## AC-INS-001 — Accepted Compound Inspection happy path

**Pre-conditions:**
- A Final Batch Mixing compound exists with stock on both ERPs.
- Quality Inspector user exists and can access Compound Inspection.

**Steps:**
1. Open Compound Inspection.
2. Scan the compound mix barcode.
3. Enter all required readings within spec.
4. Submit.

**Pass conditions:**
- Console creates a `Console Inspection` with `process_code=COMPOUND_INSPECTION`.
- Status is Accepted.
- Legacy and Ops target feedback reach Success.
- Downstream stock movement matches an accepted inspection.
- The record is traceable by `reference_id` and mix barcode.

## AC-INS-002 — Rejected Compound Inspection skips Legacy

**Steps:**
1. Open Compound Inspection.
2. Scan a valid compound.
3. Enter at least one out-of-spec reading.
4. Submit.

**Pass conditions:**
- Status is Rejected.
- Legacy leg is intentionally not attempted.
- Ops leg succeeds or shows a clear failure.
- The rejected inspection appears in the Deviation queue.
- The operator can explain why Legacy is absent: factory requirement skip, not outage.

## AC-INS-003 — Deviation Accepted override

**Pre-conditions:**
- AC-INS-002 has produced a rejected CI.
- A Quality Manager is available.

**Steps:**
1. Open Compound Deviation.
2. Select the rejected CI.
3. Scan Quality Manager badge.
4. Choose Accepted.
5. Enter a meaningful reason.
6. Submit.

**Pass conditions:**
- One Deviation record is created on Console.
- Legacy `Compound Inspection` exists with QM fields and remarks populated.
- Ops runs the Accepted status action where configured.
- Final sync status reaches Success.
- The source CI remains unchanged as the source lab result.

## AC-INS-004 — Deviation Rejected disposition

**Steps:**
1. Repeat AC-INS-003 but choose Rejected.

**Pass conditions:**
- Legacy receives final Rejected disposition.
- Ops does not create an Accepted transfer.
- Any skipped Ops action is visible as a successful conditional skip, not an unexplained failure.
- Material is not available for downstream Sheeting.

## AC-INS-005 — Deviation Rework disposition

**Steps:**
1. Repeat AC-INS-003 but choose Rework.

**Pass conditions:**
- Deviation lands with status Rework.
- No forward stock movement is created.
- The lot remains visible for operational rework handling.

## AC-INS-006 — Deviation validation gates

**Steps:**
1. Try to submit a Deviation without a source CI.
2. Try to submit for an Accepted source CI.
3. Try without QM scan.
4. Try with a reason shorter than 5 characters.

**Pass conditions:**
- Each attempt is blocked with a clear message.
- No target ERP document is created for invalid attempts.
- Console keeps enough audit detail for troubleshooting when the attempt enters the audit path.

## AC-INS-007 — Duplicate Deviation blocked

**Pre-conditions:**
- A source rejected CI already has an active Deviation.

**Steps:**
1. Attempt to create a second Deviation for the same source CI.

**Pass conditions:**
- The UI excludes the source CI from pending list, or backend validation blocks it.
- No second active Deviation is created.

## AC-INS-008 — Race-safe callback handling

**Pre-conditions:**
- Test harness can fire Legacy and Ops callbacks nearly simultaneously.

**Steps:**
1. Run concurrent callback test for an inspection/deviation record requiring both target legs.

**Pass conditions:**
- Final state is deterministic.
- If both required legs are Synced, aggregate status is Success.
- Auto-submit fires once.

## AC-INS-009 — Cavity number visibility

**Steps:**
1. Submit a CI or Deviation where `cavity_no` is present.
2. Submit one where it is missing.

**Pass conditions:**
- Present value is preserved to target where supported.
- Missing value does not block production if fallback is active.
- Fallback is visible in logs or drift reports.

## Sign-off bar

Inspection Process is production-shipped when:

- AC-INS-001 through AC-INS-008 pass on staging.
- At least one Accepted, Rejected, and Rework Deviation path is tested.
- No false Partial appears when both required target legs succeed.
- Quality Manager signs off that Deviation reason and pending queue behavior are acceptable.
- Production overseer signs off in writing.

