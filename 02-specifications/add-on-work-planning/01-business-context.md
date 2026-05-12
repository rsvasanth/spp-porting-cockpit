# 01 — Business context

## What this process produces

| Outcome | Where it lives |
|---|---|
| Lot # | Console-authored `LOT-YYYYMMDD-NNN`; written to Legacy + Ops |
| Work Order | Legacy: created by `create_planning_with_jobcards`; Ops: created by TransactionEngine |
| Job Card(s) | One per item row (Workstation × Produced Item) |

Downstream Blanking, Inspection Entry, and Moulding Production Entry all reference the Lot # / Job Card identity.

## Position in the chain

```
... Sheeting → Cut Bit / BCR → Blanking DC → Blank Bin Inward ...
                                                       │
                                                       ▼
                                              ADD ON WORK PLANNING
                                                       │
                                                       ▼
                                              Blank Bin Issue (consumes Lot #)
                                                       │
                                                       ▼
                                              Inspection Entry + MPE (Wave 4-5)
```

## Why Add On remains separate from Work Planning

Legacy has both `Work Planning` and `Add On Work Planning`. They share much of their schema, but the business rule is different: Work Planning is the official one-per-shift base plan, while Add On Work Planning is supplemental. Legacy Work Planning calls the duplicate-shift validator; Add On Work Planning does not.

Therefore Console should keep a separate Add On Work Planning process identity. Do not use Add On as a hidden replacement for Work Planning.

## Why Console-first Lot # generation (Pattern A from plan doc)

Per Charter Principle 1 (Console as system of record):
- Console serializes Lot # generation via daily counter
- Bridge passes value to Legacy; legacy auto-generator disabled when `lot_number` is provided
- Ops Work Order has custom field `lot_number` receiving the same value
- Retry on either leg reuses the same Lot # (no regeneration)

Pattern B (Legacy-first) was rejected — would make Console an observer instead of authority, complicate retry semantics.

## Operational constraints

| Constraint | Why |
|---|---|
| Console-first Lot # generation | Charter principle |
| Lot # format `LOT-YYYYMMDD-NNN` | Daily gapless sequence |
| Single active BOM per produced item | Legacy invariant |
| Atomic Work Order + Job Cards creation on Legacy | Partial state unacceptable |
| Each row → one Job Card | 1:1 row-to-JC mapping |
| Mixing Operation master data overrides workstation | Master data authority |
| ±10% target_qty drift → soft warning | Operator override allowed |

## What this motion is NOT asking for

- Production scheduling optimization (operator decides)
- Demand forecasting (operator uses Work Plan Item Target)
- Multi-day horizon (one shift per submission)
- Approval workflow (Supervisor signs off via submission)
- Planning amendment (re-plan = new submission)

See [`../../01-requirements/add-on-work-planning/`](../../01-requirements/add-on-work-planning/) for Add On requirements and [`../../01-requirements/work-planning/`](../../01-requirements/work-planning/) for the base shift-plan requirements.
