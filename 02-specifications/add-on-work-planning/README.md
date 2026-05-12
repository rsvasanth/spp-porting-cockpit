# Add On Work Planning — Specification (forward-looking, Wave 3 target)

**Status:** NOT YET SHIPPED. Wave 3 target per plan doc `03_WAVE3.md`.
**Console doctype (planned):** `Console Add On Work Planning` (`CADWRKP-.YYYY.-.#####`) — supplemental planning only.
**Legacy doctype:** `Add On Work Planning` + auto-generated `Work Order` + `Job Card`(s).
**Ops doctype targets:** Native ERPNext `Work Order` + `Job Card`(s) via the generic MES Transaction Engine.

> Read [`../work-planning/`](../work-planning/) first. Work Planning is the official one-per-shift base plan. This folder is only for Add On Work Planning, the supplemental plan.

## What this process produces

A production schedule artifact — Lot # + Work Order + Job Cards — that downstream Blanking, Inspection, and Moulding processes consume.

## Architectural facts (planned)

| Fact | Detail |
|---|---|
| Naming series | `CADWRKP-.YYYY.-.#####` |
| Lot # format | `LOT-YYYYMMDD-NNN` (Console-authored, Pattern A) |
| Cross-system identity | Lot # propagates to Legacy Job Card + Ops Work Order custom field |
| Legacy chain | `create_planning_with_jobcards` whitelisted method (Work Order + JCs in one transaction) |
| Multi-BOM rejection | Same single-BOM invariant as mixing |
| Work Plan Item Target | ±10% drift soft warning |
| Workstation auto-override | From Mixing Operation master data |
| Process identity | Separate from Work Planning; no `planning_type` collapse |
| Generic Ops engine | Charter Principle 2 — no dedicated handler needed |
| Same 5-step apply_bridge_result | Saga pattern inherited |

## Files in this folder

| File | What it covers |
|---|---|
| [01-business-context.md](01-business-context.md) | Production planning role; Lot # generation rationale |
| [02-frontend-dash.md](02-frontend-dash.md) | Multi-row planning UX |
| [03-console-backend.md](03-console-backend.md) | `create_local_add_on_work_planning` + Lot # generator |
| [04-bridge-layer.md](04-bridge-layer.md) | Mapping + `create_planning_with_jobcards` whitelisted method on Legacy |
| [05-legacy-erpnext.md](05-legacy-erpnext.md) | Work Order + Job Card chain + workstation override |
| [06-ops-erpnext.md](06-ops-erpnext.md) | Generic TransactionEngine sequence for WO + JC creation |
| [07-end-to-end-flow.md](07-end-to-end-flow.md) | Trace narrative |
| [08-test-plan.md](08-test-plan.md) | Tests including Lot # concurrency + atomic WO+JC rollback |
| [09-rollout-and-history.md](09-rollout-and-history.md) | Wave 3 plan |
| [10-risks-and-decisions.md](10-risks-and-decisions.md) | Lot # authority + workstation override transparency |

## Critical correction

An earlier version of this spec said Console could collapse Legacy Work Planning and Add On Work Planning into one doctype using `planning_type`. Legacy code does not support that as a safe default: Work Planning enforces one submitted plan per shift, while Add On Work Planning does not call that uniqueness validation. Treat them as separate process identities.
