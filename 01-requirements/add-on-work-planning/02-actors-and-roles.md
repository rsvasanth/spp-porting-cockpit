# Actors And Roles

| Actor | Responsibility |
| --- | --- |
| Production Supervisor | Adds supplemental products/workstations/moulds beyond the base shift plan |
| Moulding Supervisor | Scanned/validated supervisor identity |
| Planning Reviewer | Reviews added Job Cards and Lot #s |
| System Administrator | Maintains shift targets, mould/workstation filters, and mappings |

## System Actors

| System | Responsibility |
| --- | --- |
| Console | Future Add On Work Planning submission and sync owner |
| Legacy ERPNext | Current Add On Work Planning behavior |
| Ops ERPNext | Target for equivalent additional Work Orders / Job Cards |
| Bridge | Maps Add On payload to Legacy and Ops |

## Decision Rights

| Decision | Owner |
| --- | --- |
| Need for additional production | Production Supervisor |
| Item/mould/press selection | Production Supervisor |
| Allow multiple add-ons in a shift | Allowed by Add On semantics unless process owner changes it |
| Cancel add-on after downstream use | Not allowed |
