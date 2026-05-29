# SPP Quality Control — Specification

**Console doctype:** `SPP Quality Control` (new, separate from `Console Inspection`).
**Inspection types covered:** Line, Patrol, Lot, Incoming, Final Visual / PDIR.
**System of record:** Console MES (`shree_polymer_console`).
**Ops masters:** `SPP QC Parameter`, `SPP QC Template` (already on Ops; sync to Console as read-only caches).
**Legacy mirror:** `Inspection Entry` on `spp15.local` via the Legacy Bridge.

## Why a separate doctype from Console Inspection

Console Inspection (Phase 3, shipped 2026-05-01) was originally scoped to absorb production-family inspections as a `Compound | Production | Other` polymorphic doctype. That direction was reversed in 2026-05 after re-evaluation against shop-floor business requirements:

- Compound and production-line QC have fundamentally different lifecycles, identity-resolution strategies, and actor roles.
- The polymorphic discriminator was breeding type-specific branches in the unified controller — same pain it was supposed to eliminate.
- Splitting cleanly into two doctypes lets each evolve independently.

**Decision:** Console Inspection stays scoped to Compound family only. QC gets its own doctype, `SPP Quality Control`.

See [`10-risks-and-decisions.md`](10-risks-and-decisions.md) for the full reasoning.

## Files in this folder

| File | What it covers |
|---|---|
| `01-business-context.md` | Architecture, topology, decoupling invariants |
| `02-frontend-dash.md` | Shop-floor React UI, scan flow, color feedback |
| `03-console-backend.md` | `SPP Quality Control` doctype schema, controller validation |
| `04-bridge-layer.md` | Orchestration, idempotency, retry semantics |
| `05-legacy-erpnext.md` | Inspection Entry mirror on `spp15.local` |
| `06-ops-erpnext.md` | Master data (Parameter + Template), Stock Entry creation/cancellation |
| `07-end-to-end-flow.md` | Scan → submit → cascade → cancel sequence walkthrough |
| `08-test-plan.md` | Unit + integration + E2E test coverage |
| `09-rollout-and-history.md` | M1–M6 milestones + delivery sequence |
| `10-risks-and-decisions.md` | Open risks, ADRs, why-not alternatives |

## Authority

This spec is governed by [`../../00-program-charter/`](../../00-program-charter/) and the requirements at [`../../01-requirements/quality-control/`](../../01-requirements/quality-control/). When this spec and the requirements conflict, the requirements win.
