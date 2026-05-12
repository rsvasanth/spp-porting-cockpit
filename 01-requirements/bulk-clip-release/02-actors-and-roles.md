# Actors and Roles

| Actor | Responsibility |
| --- | --- |
| Blanker / release operator | Scans clips and submits release batch |
| Blanking Operator | Depends on released clip state |
| Shop Floor Supervisor | Reviews release bottlenecks |
| Production Overseer | Decides audit path vs direct helper behavior |

## System Actors

| System | Responsibility |
| --- | --- |
| Console Dash | Multi-clip scan and duplicate prevention |
| Console Backend | Validates active mirror mapping and orchestrates targets |
| Legacy Bridge | Creates/updates Legacy release state |
| Legacy ERPNext | Retires `Item Clip Mapping` by mapping id |
| Ops ERPNext | Dedicated `bulk_release_clips` handler |

## Decision Rights

| Decision | Owner |
| --- | --- |
| Which clips to release together | Release operator |
| Whether release uses rich audit doctype or direct helper | Production Overseer |
| Barcode/doc-name resolver changes | Engineering Lead with tests |
| Whether release should create stock entry | Not allowed; process owner decision would be required |
