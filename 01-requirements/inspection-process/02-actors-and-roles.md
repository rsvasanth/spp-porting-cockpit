# 02 — Actors and roles

## Primary actors

### Quality Inspector

Submits Compound Inspections. Inspects every compound batch produced by mixing.

| Aspect | Detail |
|---|---|
| Console role name | `Quality Inspector` |
| Where active | Compound Inspection lab; near the Two Roll Mixing Mill / Avon Kneader |
| Console access | Dash UI only (no Desk access) |
| Console permissions on CI | Create + Submit on `Console Inspection` (with `inspection_type="Compound Inspection"`) |
| Console permissions on CD | **None** — explicitly disallowed at the Dash layer |
| Decision rights | Selects status (Accepted / Rejected); records readings; cannot override a prior QM decision |

**What the Quality Inspector needs from the system:**

- A scan-driven UI to select the compound batch by `mix_barcode`
- BOM-driven reading template (item-specific spec parameters with min/max)
- Auto-calculate Pass/Fail per reading; auto-derive overall status
- Submit button enabled only when all required readings are entered
- Clear indication of next step if rejected ("Lot will be held; notify QM")

### Quality Manager

Submits Compound Deviations on rejected lots. Decides material disposition.

| Aspect | Detail |
|---|---|
| Console role name | `Quality Manager` |
| Where active | Lab / QA office |
| Console access | Dash + limited Desk |
| Console permissions on CI | Read (for context) + create + submit (rare; for backdated CI corrections) |
| Console permissions on CD | Create + Submit on `Console Inspection` (with `inspection_type="Compound Deviation"`) OR `Console Compound Deviation` |
| Decision rights | Status: Accepted (override) / Rejected (scrap) / Rework (return to mixing); records `deviation_reason` |

**What the Quality Manager needs from the system:**

- A scan-driven entry point: scan the rejected compound's barcode → fetch the source CI's full context
- Read-only view of the original CI readings (so QM can verify the rejection rationale)
- Status dropdown with three options
- Required reason field (min 5 chars) — forces QM to articulate decision rationale
- Approver scan + signoff (QM's own badge captured as `quality_approver_id`)
- Clear indication of downstream consequence per status choice

## Secondary actors

### Mixing Operator (upstream)

Doesn't submit CI or CD, but their submission triggers CI. Operator may need to scan a Rejected lot's barcode to identify it for handover to QA — a downstream-visibility concern, not a participation concern.

### Shop Floor Supervisor

Reviews CI / CD throughput and rejection rates at shift end.

**What they need from this motion:**

- Per-shift count of CI submissions by outcome (Accepted / Rejected)
- Per-shift count of CD submissions by status (Accepted / Rejected / Rework)
- Drill-down from a CD back to its source CI for root-cause review
- Visibility into recurring rejection reasons

### Compound QA Lead

Owns the inspection spec rules. Indirect actor — defines the BOM-attached parameter specs that CI readings are validated against.

**What they need:**

- Confidence that every CI submission's readings are checked against current BOM parameters
- Visibility into per-parameter pass/fail rates

### Production Overseer (you)

| Aspect | Detail |
|---|---|
| Role | `System Manager` / `Administrator` |
| Special capability | Backdate `posting_date` arbitrarily; correct historical CI/CD records |
| Usage pattern | Audit reconstruction; rare manual override |

## Non-human actors (system roles)

### Console Dash

| Responsibility | What it must guarantee |
|---|---|
| QI-facing UI | Scan + reading entry with BOM-spec validation per parameter |
| QM-facing UI | Source-CI fetch, read-only display, status + reason, approver scan |
| Role gating | QI cannot see CD submit button; QM sees CD button only if source CI was Rejected |
| Live Feedback | Same Promise.all parallel target pattern as Mixing |

### Console Backend

| Responsibility | What it must guarantee |
|---|---|
| Local audit record | Both CI and CD land a `Console Inspection` (Phase 3) or per-type record |
| Phase 3 dispatch | `is_inspection_type` flag on Process Template routes to unified path |
| Identity capture | `mix_barcode` carried through every payload layer |
| Race-safe callback | The 5-step `apply_bridge_result` saga pattern |
| Factory-requirement skip | Rejected CIs do NOT POST to Legacy; only Ops |

### Legacy Bridge

| Responsibility | What it must guarantee |
|---|---|
| `populate_compound_inspection_fields` | CI path: shared identity helpers + reading sync |
| `populate_compound_deviation_fields` | CD path: same shared helpers + `_apply_deviation_extras` |
| 6-strategy SE lookup | Every strategy preserved; fail-loud on miss |
| Empty `field_mappings` for CD | All population in Python; mapping doctype shell only exists for routing |
| cavity_no fallback to 1 | With structured log every fire |

### Ops MES Transaction Engine

| Responsibility | What it must guarantee |
|---|---|
| Status-conditional SE creation | Accepted CI/CD → Material Transfer SE; Rejected → Material Issue or write-off; Rework → no SE |
| Idempotency via MES Log | `reference_id` key |
| Generic engine (no dedicated handler) | This motion stays on the generic path |

## Decision rights matrix

| Decision | Who decides |
|---|---|
| When to submit a CI | Quality Inspector (after mixing event lands) |
| What status (Accepted/Rejected) a CI gets | Quality Inspector based on reading thresholds |
| When to open a CD | Quality Manager (operationally — they're notified when CI rejects) |
| What status (Accepted/Rejected/Rework) a CD gets | Quality Manager based on lot inspection + business context |
| When to skip routing rejected CIs to Legacy | **Factory requirement, NOT a per-submission choice** — fixed business rule |
| Whether to wire `cavity_no` properly | Production Overseer + Engineering Lead (active TODO) |
| When to deprecate per-type Console doctypes | Production Overseer (separate epic; depends on backfill of pre-Phase-3 records) |
| When to consolidate CI + CD into a single workflow on Dash | Production Overseer — currently kept separate for audit/separation-of-concerns |
