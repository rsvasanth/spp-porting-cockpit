# Actors And Roles

## Human Actors

| Actor | Responsibility |
| --- | --- |
| Production Supervisor | Creates and submits the official shift Work Planning document |
| Moulding Supervisor | Scanned/validated supervisor identity in Legacy |
| Planning Reviewer | Reviews planned products, Job Cards, and Lot #s |
| System Administrator | Maintains shift types, target quantities, mould/workstation filters, and mappings |

## System Actors

| System | Responsibility |
| --- | --- |
| Console | Future system of record for Work Planning submission and sync |
| Legacy ERPNext | Current source of truth for Work Planning behavior |
| Ops ERPNext | Target for equivalent Work Order / Job Card planning records |
| Bridge | Maps Console Work Planning into Legacy/Ops target documents |

## Decision Rights

| Decision | Owner |
| --- | --- |
| Which items to plan for shift | Production Supervisor |
| Which mould and workstation to use | Production Supervisor within configured filters |
| Whether duplicate shift plan is allowed | Not allowed for Work Planning |
| Whether extra production is needed | Add On Work Planning process |
| Cancellation after downstream use | Blocked by downstream records |

## Permission Expectations

| Action | Allowed role |
| --- | --- |
| Create draft Work Planning | Production Supervisor |
| Submit Work Planning | Production Supervisor |
| Create Work Order / Job Card from submitted plan | Production Supervisor / authorized system |
| Cancel before downstream use | Production Supervisor / System Administrator |
| Cancel after BBI or MPE exists | Not allowed |
