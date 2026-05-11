# 01 — Purpose

## What this motion produces

The Inspection Process produces a **quality disposition** for a compound batch.

| Step | Input | Output | Who decides |
|---|---|---|---|
| Compound Inspection | Mixed compound batch from Final Batch Mixing | Accepted or Rejected lab result | Quality Inspector, based on readings |
| Compound Deviation | Rejected Compound Inspection | Accepted override, Rejected scrap/write-off, or Rework decision | Quality Manager |

The motion does not create new compound. It decides whether existing compound can continue through Sheeting and downstream production.

## Where it sits in the chain

```text
Final Batch Mixing
   -> Compound Inspection
      -> Accepted: proceed to Sheeting
      -> Rejected: hold for Compound Deviation
            -> Accepted: proceed by QM override
            -> Rejected: remove / scrap
            -> Rework: return to mixing path
```

Inspection is the quality gate between compound production and physical transformation. If it is wrong, every downstream stage inherits bad material state.

## Why the Deviation step exists

Rejected compound is not always waste. A failed reading can mean:

| Case | Business meaning |
|---|---|
| Minor deviation | Material may still be usable with QM signoff |
| Confirmed failure | Material must be scrapped or written off |
| Correctable material | Material can be reworked or blended |

The Quality Manager decision preserves this nuance. A simple Accepted/Rejected lab result would either block useful material or allow risky material without accountability.

## Why Legacy still receives `Compound Inspection`

Legacy has historical reports and stock behavior built around the `Compound Inspection` doctype. Even a Deviation lands as a legacy `Compound Inspection` with extra signoff fields populated.

| Option | Reason rejected or accepted |
|---|---|
| New legacy `Compound Deviation` doctype | Rejected; would break historical reports and duplicate stock logic |
| Reuse legacy `Compound Inspection` | Accepted; preserves reports and controller behavior |
| Model Deviation only on Console | Rejected; Legacy stock ledger would miss rejected material dispositions |

## Why unified Console Inspection matters

The current Console direction is a unified `Console Inspection` doctype. It uses `inspection_type` and `inspection_family` to represent multiple inspection flavors without creating a new Console doctype for every QA form.

This is a business benefit, not just a technical cleanup:

| Benefit | Why stakeholders care |
|---|---|
| One inspection record shape | Easier reporting across QA events |
| One reading child table | Test readings can evolve without new doctypes |
| One callback pattern | Avoids the race that caused false Partial states |
| One place for Deviation linking | Prevents duplicate QM decisions on one rejected CI |

## What the business is protecting

| Protected thing | Requirement implication |
|---|---|
| Material quality | Failed readings cannot silently proceed |
| QM accountability | Every override needs a named approver and reason |
| Stock truth | Status must drive the correct material movement |
| Traceability | Every decision must link back to the source mixed batch |
| Recovery | Partial syncs must be visible and retryable |

## What this motion is not

Inspection is not a production planning step, not a moulding inspection pack, and not a generic lab management system. It is the compound quality gate for the SPP production chain.
