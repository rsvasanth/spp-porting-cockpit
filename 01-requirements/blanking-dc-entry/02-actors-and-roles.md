# Actors and Roles

| Actor | Responsibility |
| --- | --- |
| Blanker | Scans clip and bin, enters gross weight, submits BDE |
| Material Handler | Uses BDE-created bin mapping later in BBIE |
| Production Supervisor | Uses BDE-created bin state later in BBI |
| Production Overseer | Approves changes to bin mapping and Asset Movement semantics |

## System Actors

| System | Responsibility |
| --- | --- |
| Console Dash | Scan order, weight entry, inline net calculation |
| Console Backend | Local audit, bin mapping mirror, clip qty deduction |
| Legacy Bridge | Reconstructs legacy child rows and resolves Asset |
| Legacy ERPNext | Validates and submits BDE; creates `Item Bin Mapping` and `Asset Movement` |
| Ops ERPNext | Dedicated handler for target-side movement |

## Decision Rights

| Decision | Owner |
| --- | --- |
| Which clip to blank | Blanker |
| Which bin to fill | Blanker, subject to bin availability |
| Whether item/BOM association is valid | System validation using BOM |
| Asset Movement semantics | Production Overseer and Engineering Lead |
