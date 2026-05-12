# 02 — Actors and roles

## Primary actors

| Actor | Role |
|---|---|
| Quality Inspector | Scans inspector, lot/context, records defects and inspected quantities, submits IE. |
| QA Lead | Owns defect type policy, duplicate/exception handling, and inspection method decisions. |
| Moulding Operator | Depends on Line/Patrol completion before MPE; does not normally submit IE. |
| Production Overseer | Reviews failed stock entries, rollback cases, and cross-process mismatches. |

## System actors

| Actor | Responsibility |
|---|---|
| Console Dash | Type-aware inspection form, defect rows, totals, validation feedback. |
| Console Backend | Duplicate gate, required-field validation, audit, and idempotent submission. |
| Legacy Bridge | Maps Console IE fields to legacy `Inspection Entry` and child rows. |
| Moulding Production Entry | Later supplies produced batch to Line/Patrol/Lot rejection stock entries where applicable. |
| Stock Entry | Moves rejected material to configured rejection warehouse or final visual/PDIR target. |

## Decision rights

| Decision | Owner |
|---|---|
| Inspection type | Quality Inspector/QA workflow. |
| Defect type and rejected quantity | Quality Inspector. |
| Whether duplicate inspection is allowed | System blocks duplicates per lot/type except Final Visual. |
| Whether MPE can proceed | System, based on submitted Line and Patrol IE. |
| Manual rollback/correction | Production Overseer / System Manager. |

