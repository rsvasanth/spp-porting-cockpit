# Inspection Process — Business Requirements

**Business motion:** QA disposition of compound after mixing.
**Console processes covered:** Compound Inspection and Compound Deviation.
**Legacy doctype target:** `Compound Inspection`.
**Ops doctype target:** ERPNext `Stock Entry` through the generic MES Transaction Engine.

This folder captures what the business needs from compound QA: decide whether a mixed compound can proceed, and when it cannot, make a Quality Manager decision that is auditable and recoverable.

For the technical reality, read:

- [`../../02-specifications/compound-deviation/`](../../02-specifications/compound-deviation/)
- `../../02-specifications/console-inspection-unification/` once written

## Why CI + Deviation share one requirements folder

Compound Inspection and Compound Deviation are one business motion. The first records the lab result. The second records the Quality Manager disposition when the lab result rejects the material.

| Process | Business role | Main decision |
|---|---|---|
| Compound Inspection | Quality Inspector | Is this compound within spec? |
| Compound Deviation | Quality Manager | What happens to rejected compound? |

The legacy system also treats Deviation as a variant of `Compound Inspection`, not a separate legacy doctype. Grouping the requirements here keeps that business truth visible.

## Files in this folder

| File | What it answers |
|---|---|
| [01-purpose.md](01-purpose.md) | Why inspection exists and how it protects the production chain |
| [02-actors-and-roles.md](02-actors-and-roles.md) | Quality Inspector, Quality Manager, production overseer, and system actors |
| [03-functional-requirements.md](03-functional-requirements.md) | Numbered requirements `FR-INS-NNN` |
| [04-non-functional-requirements.md](04-non-functional-requirements.md) | Speed, reliability, audit, data integrity, maintainability |
| [05-business-rules.md](05-business-rules.md) | Load-bearing decisions and why they exist |
| [06-acceptance-criteria.md](06-acceptance-criteria.md) | Plain-language UAT scripts |
| [07-out-of-scope.md](07-out-of-scope.md) | Explicit exclusions |
| [08-traceability.md](08-traceability.md) | Requirement-to-spec mapping and drift findings |

## How to use this folder

| Audience | Read first |
|---|---|
| QA / shop-floor leads | `01-purpose.md`, `02-actors-and-roles.md`, `06-acceptance-criteria.md` |
| Production overseer | All files, especially `05-business-rules.md` and `08-traceability.md` |
| Hermes workers | `03-functional-requirements.md`, `05-business-rules.md`, `08-traceability.md` |
| Reviewer worker | `08-traceability.md` before approving any inspection-related change |

## Versioning note

Requirements state the intended business behavior. Current code can be ahead of, behind, or different from these requirements; those differences belong in `08-traceability.md` as drift findings.

