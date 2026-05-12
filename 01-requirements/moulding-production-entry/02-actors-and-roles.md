# 02 — Actors and roles

## Primary actors

| Actor | Role in MPE | Required capability |
|---|---|---|
| Moulding Operator | Scans lot, bins, operator badge, and production weight. | Create/submit MPE from floor UI. |
| Production Supervisor | Confirms production booking accountability. | Co-sign or verify supervisor badge where required by Console. |
| Quality Inspector | Does not submit MPE, but must submit Line/Patrol IE first. | Submit prerequisite Inspection Entries. |
| Production Overseer | Reviews failures, exceptional corrections, and tolerance behavior. | Admin review, not normal override. |

## Non-human actors

| Actor | Responsibility |
|---|---|
| Console Dash | Scan-led MPE form, lot context, inspection status, bin list, balance-bin entry, injection fields, submit gating. |
| Console Backend | Local validation, audit, idempotent submit request, and target sync orchestration. |
| Legacy Bridge | Maps Console data to `Moulding Production Entry` and preserves legacy validation semantics. |
| ERPNext Stock | Executes Manufacture Stock Entry and stock ledger updates. |

## Decision rights

| Decision | Owner |
|---|---|
| Whether a lot is ready for MPE | System gate from submitted Line + Patrol IE and open Blank Bin Issue rows. |
| Produced weight and balance bin weight | Moulding Operator, verified by supervisor process. |
| Injection moulding flag | Legacy derives from workstation name containing `INJECTION` or `INJUCTION`; Console may make this explicit but must match legacy. |
| Tolerance override | No operator override. Any policy change belongs to SPP Settings / process owner approval. |
| Manual correction after failed stock booking | Production Overseer / System Manager only. |

