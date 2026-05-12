# 07 — Out of scope

## Out of scope — features

### OOS-INS-001 — Real-time alerting to QM on CI rejection
The system does NOT push notifications (email, SMS, app alert) to QMs when a CI is Rejected. The QM monitors the rejected-CI queue via the Dash or Console Transaction Log filter.

**Why not:** Notifications require an additional alerting layer (separate epic). The Dash queue is operationally sufficient.

### OOS-INS-002 — Multiple CDs per CI
The system enforces (via Dash UI) one CD per Rejected CI. A use case requiring multiple overlapping CDs would need explicit cancellation of the prior CD and a new submission.

**Why not:** Multiple CDs would create ambiguous final disposition. The audit-critical decision is the final QM call.

### OOS-INS-003 — QM batch-decision UI
The system does NOT support deciding multiple lots' CDs in one bulk action. Each CD is a separate submission with its own reason.

**Why not:** Per-lot accountability is the audit requirement. Batch decisions blur the trail.

### OOS-INS-004 — Reading-spec drift detection
The system does NOT automatically detect when BOM parameter specs change and flag inconsistencies with historical readings.

**Why not:** BOM evolution is normal operational practice. Reports surface drift; the QA Lead is responsible for spec curation.

### OOS-INS-005 — QM authentication beyond role check
The system does NOT require additional QM authentication (PIN, biometric) beyond the Console User session + role check.

**Why not:** Session security is sufficient. Additional auth would slow operator throughput.

### OOS-INS-006 — Quality Inspection (non-compound) workflow
This motion covers **Compound Inspection** specifically. Quality Inspections for other purposes (incoming raw material QC, finished good QC pre-dispatch) are separate doctypes (`Quality Inspection`, `Quality Inspection Template`, etc.) and out of this motion's scope.

**Why not:** Different operator role, different timing in the workflow, different doctype. Conflating would dilute the motion's clarity.

### OOS-INS-007 — Automated rework verification
When a CD with `status="Rework"` is submitted, the system does NOT automatically verify that the reblending happened. Operators handle the physical reblending and submit a new mixing event.

**Why not:** Reblending happens at the mill; tracking it as a re-mixing event captures the audit trail correctly without coupling CD to mixing.

### OOS-INS-008 — Cavity-level inspection
This motion does NOT track inspection at the individual cavity level. Inspection is per-lot. (The `cavity_no` field on legacy CI defaults to 1 today; this represents single-cavity-equivalent recording.)

**Why not:** Cavity-level tracking is part of MPE (Moulding Production Entry), not Compound Inspection. Mixing-and-inspecting-by-cavity is not how SPP operates.

### OOS-INS-009 — Statistical Process Control (SPC) charts
The system does NOT include real-time SPC charting on inspection readings.

**Why not:** SPC tooling belongs to an analytics layer. Readings are captured in audit-friendly format; analysis happens downstream.

## Out of scope — operations

### OOS-INS-020 — Automatic retry of failed legs
Same as Mixing — operators must explicitly press Retry.

### OOS-INS-021 — Cross-shift QM handoff
The system does NOT automatically reassign rejected-CI queue ownership between shifts. QMs at shift handoff coordinate via operational practices.

### OOS-INS-022 — Approval workflow above QM
There is no second-level approval above the QM's CD decision. QM signoff is final.

**Why not:** Adding approval layers slows the QA decision and rarely surfaces additional value. QM accountability is sufficient.

## Out of scope — integrations

### OOS-INS-030 — LIMS (Laboratory Information Management System) integration
The system does NOT integrate with a separate LIMS. All readings are entered manually on the Dash.

**Why not:** SPP does not currently operate a LIMS. Future integration would be a separate epic.

### OOS-INS-031 — Direct BOM editing from Dash
Operators cannot modify BOM specs from the Dash. BOMs are managed in Legacy by the QA Lead.

**Why not:** BOM curation is a deliberate, audited operation that requires QA Lead authority — not a shop-floor concern.

### OOS-INS-032 — Inspection data export to BI
Not part of this motion. Future analytics epic.

## Related but out of scope (link to other motions)

| Related process | Owned by |
|---|---|
| Master Batch Mixing / Final Batch Mixing (upstream) | `01-requirements/mixing-process/` |
| Sheeting Process (downstream clip creation) | `01-requirements/sheeting-process/` |
| Cut Bit Transfer (downstream recycling route) | `01-requirements/cut-bit-transfer/` |
| Bulk Clip Release (downstream clip release) | `01-requirements/bulk-clip-release/` |
| Moulding Production Entry | `01-requirements/moulding-production-entry/` |
| Moulding / production Inspection Entry | `01-requirements/inspection-entry/` |
| Stock reconciliation | future `01-requirements/reconciliation/` |
| Cavity_no proper wiring | This motion's BR-INS-006 (active TODO); implementation is a code task, not a new requirement |

## When in doubt

Test for in-scope:
1. Does the change affect QI or QM submission flow?
2. Does it change CI/CD records on Console / Legacy / Ops?
3. Does it touch cross-system invariants (mix_barcode, reference_id, saga 5-step pattern)?

If yes to any — in scope. If no to all — likely out of scope, belongs to another motion.
