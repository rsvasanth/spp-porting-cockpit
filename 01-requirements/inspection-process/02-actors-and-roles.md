# 02 — Actors and roles

## Primary actors

### Quality Inspector

The Quality Inspector records compound readings after mixing.

| Aspect | Detail |
|---|---|
| Console role | `Quality Inspector` |
| Main screen | Compound Inspection |
| Decision | Accepted or Rejected based on readings |
| Cannot do | Override a rejected lot without QM signoff |

What the Quality Inspector needs:

- Scan a compound batch and resolve its identity
- Enter required readings without hunting through Desk forms
- See whether each reading is within limits
- Submit an Accepted or Rejected result with clear downstream status
- Avoid duplicating lab records for the same batch

### Quality Manager

The Quality Manager decides what happens to rejected compound.

| Aspect | Detail |
|---|---|
| Console role | `Quality Manager` |
| Main screen | Compound Deviation |
| Decision | Accepted override, Rejected, or Rework |
| Mandatory evidence | QM badge scan and deviation reason |

What the Quality Manager needs:

- See only rejected inspections that still need disposition
- See source readings as read-only context
- Scan their own badge to authorize the decision
- Record a reason that is meaningful enough for audit
- Know that the decision landed on both ERPs or is visible for retry

### Production Overseer

The production overseer owns sign-off and drift decisions.

| Decision | Overseer role |
|---|---|
| Whether to wire `cavity_no` fully | Approves cross-layer work |
| Whether rejected CIs skip Legacy | Owns factory rule |
| Whether Deviation statuses change | Coordinates QA + stock behavior |
| Whether a shipped state is acceptable | Signs off UAT and monitoring |

## Secondary actors

### Mixing Operator

The Mixing Operator does not submit inspection records, but their mixed batch is the subject of inspection. The inspection flow must be able to trace back to the Mixing record by mix barcode.

### Shop Floor Supervisor

The supervisor needs shift-level visibility:

| Question | Where answered |
|---|---|
| Which batches are waiting on Deviation? | Console rejected inspection list |
| Which deviations were accepted by QM? | Console Inspection / Deviation records |
| Which syncs are Partial or Failed? | Console Transaction Log |

### Inventory / Stock Controller

The stock controller verifies the material movement implied by inspection outcomes.

| Outcome | Expected stock behavior |
|---|---|
| Accepted CI | Material moves forward to ready warehouse |
| Rejected CI | Legacy leg is intentionally skipped until Deviation |
| Accepted Deviation | Material moves forward by QM override |
| Rejected Deviation | Material is removed/scrapped per configured route |
| Rework Deviation | No forward stock movement; material remains pending rework |

## Non-human actors

### Console Dash

| Responsibility | Must guarantee |
|---|---|
| Compound scan | Resolves batch identity and available readings context |
| Reading capture | Calculates pass/fail status from limits |
| QM signoff | Validates Quality Manager badge |
| Submission orchestration | Runs target legs and shows per-target feedback |

### Console Backend

| Responsibility | Must guarantee |
|---|---|
| Unified inspection write | Writes `Console Inspection` for inspection-type templates |
| Strict validation path | Enforces required readings and Deviation source rules outside audit bypass |
| Callback aggregation | Converges concurrent target callbacks correctly |
| Deviation uniqueness | Blocks a second active Deviation for the same source CI |

### Legacy Bridge

| Responsibility | Must guarantee |
|---|---|
| Legacy CI creation | Creates `Compound Inspection`, not a new Deviation doctype |
| Identity lookup | Resolves the source Stock Entry using the shared lookup chain |
| Reading transfer | Rebuilds legacy reading rows faithfully |
| Deviation extras | Adds QM signoff, status, remarks, and `cavity_no` fallback when needed |

### Ops Transaction Engine

| Responsibility | Must guarantee |
|---|---|
| Accepted material movement | Creates Material Transfer when configured |
| Status conditions | Skips actions when status does not allow movement |
| Idempotency | Reuses existing MES Log on retry |
| Audit | Records action results even when actions are conditionally skipped |

## Decision rights matrix

| Decision | Owner |
|---|---|
| Lab reading value | Quality Inspector |
| Override rejected material | Quality Manager |
| Add or change reading specification | QA Lead + Production Overseer |
| Add a Deviation status | Production Overseer + QA Lead + Engineering |
| Change rejected-CI Legacy skip | Production Overseer |
| Change callback pattern | Engineering Lead + test gate approval |

