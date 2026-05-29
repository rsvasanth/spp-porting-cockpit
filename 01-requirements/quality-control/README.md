# Quality Control — Business Requirements

**Business motion:** Shop-floor quality inspection for five distinct inspection types unified under a single Console transaction.
**Console processes covered:** Line, Patrol, Lot, Incoming, Final Visual / PDIR.
**Console doctype target:** `SPP Quality Control` (Console MES app — new, separate from `Console Inspection`).
**Ops master targets:** `SPP QC Parameter`, `SPP QC Template` (already present on Ops).
**Legacy doctype target:** `Inspection Entry` on `spp15.local`.

This document captures what the **business** needs the QC system to do.
Implementation detail lives in [`../../02-specifications/spp-quality-control/`](../../02-specifications/spp-quality-control/).

## Scope decision

QC is delivered as a **separate doctype from `Console Inspection`**. Console Inspection remains scoped to **Compound family only** (Compound Inspection + Compound Deviation). Production-line and incoming/final-visual QC live in a new `SPP Quality Control` doctype with `inspection_type` as the discriminator. See [`07-out-of-scope.md`](07-out-of-scope.md) for the boundary.

## Files in this folder

| File | What it answers |
|---|---|
| `01-purpose.md` | What QC does, where it sits in the chain |
| `02-actors-and-roles.md` | Inspector, Operator, Supervisor, Template Administrator |
| `03-functional-requirements.md` | Scan flow, template gate, calculations, cascades |
| `04-non-functional-requirements.md` | Latency, offline-resilience, sync-freshness, audit |
| `05-business-rules.md` | Strict gate, item-template binding, UoM, submission gates |
| `06-acceptance-criteria.md` | Testable assertions per inspection type |
| `07-out-of-scope.md` | What QC explicitly does NOT cover |
| `08-traceability.md` | Cross-refs to spec + related cockpit docs |
