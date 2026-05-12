# Actors and Roles

| Actor | Responsibility |
| --- | --- |
| Material Handler | Scans bin, confirms weight, chooses inward or cut-bit path |
| Blanker | Provides filled bins from BDE |
| Mixing Operator | Consumes repacked cut-bit output later |
| Production Overseer | Owns branch semantics and cut-bit convention |

## System Actors

| System | Responsibility |
| --- | --- |
| Console Dash | Bin scan, weight confirmation, branch toggle |
| Console Backend | Local audit and process orchestration |
| Legacy Bridge | Maps BBIE payload and enriches branch fields |
| Legacy ERPNext | Creates Asset Movement or Repack Stock Entry |
| Ops ERPNext | Planned dedicated branch handler |

## Decision Rights

| Decision | Owner |
| --- | --- |
| Whether bin goes normal inward or cut-bit repack | Material Handler |
| Cut-bit batch selection | Material Handler, validated by system |
| Branch default | Production Overseer |
| Any new branch such as scrap | Production Overseer only |
