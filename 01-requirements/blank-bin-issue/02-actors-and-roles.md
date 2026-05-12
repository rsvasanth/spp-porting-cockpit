# Actors and Roles

| Actor | Responsibility |
| --- | --- |
| Production Supervisor | Scans Lot/Job Card and bin; submits issue |
| Moulding Operator | Consumes issued bin later in MPE |
| Planning Owner | Provides Job Card/Lot through Work Planning or Add On Work Planning |
| Production Overseer | Approves BBI/MPE contract changes |

## System Actors

| System | Responsibility |
| --- | --- |
| Console Dash | Lot scan, bin scan, issue confirmation |
| Console Backend | Local audit and target orchestration |
| Legacy ERPNext | Validates Job Card and bin/BOM match |
| Ops ERPNext | Planned logical assignment mirror |
| MPE | Marks issue item complete/consumed |

## Decision Rights

| Decision | Owner |
| --- | --- |
| Which bin to assign | Production Supervisor |
| Whether Job Card is valid for issue | System validation |
| Whether bin compound matches BOM | System validation |
| Whether issue item is complete | MPE consumption flow |
