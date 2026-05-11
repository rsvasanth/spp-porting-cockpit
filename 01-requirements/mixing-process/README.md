# Mixing Process — Business Requirements

**Business motion:** Compound production via mixing on the shop floor.
**Console processes covered:** Master Batch Mixing (MBM), Final Batch Mixing (FBM).
**Legacy doctype target:** `Delivery Challan Receipt` (DCR) with `inward_material_type ∈ {"Master Batch", "Compound"}`.
**Ops doctype target:** ERPNext `Stock Entry` via the generic MES Transaction Engine.

This document captures what the **business** needs the system to do. It is intentionally implementation-agnostic where possible. For "how it actually works today," see the matching specifications:

- [`../../02-specifications/master-batch-mixing/`](../../02-specifications/master-batch-mixing/)
- [`../../02-specifications/final-batch-mixing/`](../../02-specifications/final-batch-mixing/)

## Why MBM + FBM share one requirements folder

Both processes are the same business motion (operator mixes raw materials → produces a tracked compound batch) on the same workstations, using the same legacy doctype (DCR), and with the same parallel-sync constraints. They differ only in **what gets consumed** (raw materials only for MB; one MB lot + raw materials for FB) and **what gets produced** (a "Master Batch" item group for MB; a "Compound" item group for FB).

Grouping them keeps shared requirements (parallel sync, audit trail, idempotency, role permissions) in one place. Variant-specific requirements are tagged `MBM-only` or `FBM-only` within each file.

## Files in this folder

| File | What it answers |
|---|---|
| [01-purpose.md](01-purpose.md) | Why this process exists, what production outcome it produces, where it sits in the chain |
| [02-actors-and-roles.md](02-actors-and-roles.md) | Who interacts with the system, what they need, who decides what |
| [03-functional-requirements.md](03-functional-requirements.md) | Numbered requirements (FR-MIX-NNN). Each is individually testable. |
| [04-non-functional-requirements.md](04-non-functional-requirements.md) | Speed, reliability, audit, multi-system consistency, security |
| [05-business-rules.md](05-business-rules.md) | The "why" behind decisions encoded in specs (value-maps, defaults, constraints) |
| [06-acceptance-criteria.md](06-acceptance-criteria.md) | How you (production overseer) declare the process "shipped" — plain-language UAT |
| [07-out-of-scope.md](07-out-of-scope.md) | What this requirement does NOT cover — prevents scope creep |
| [08-traceability.md](08-traceability.md) | Maps each requirement to the spec section(s) that implement it |

## How to use this folder

- **Business stakeholders / shop floor leads:** Read `01-purpose.md` + `02-actors-and-roles.md` + `06-acceptance-criteria.md`. Skip the rest.
- **Production overseer (you):** Read all 8 files. Use `08-traceability.md` when reviewing spec changes — verify each FR still has a working spec section.
- **Hermes workers / Reviewer:** Read `03-functional-requirements.md` + `05-business-rules.md` to understand intent BEFORE touching code. When in doubt about whether a change is in-scope, check `07-out-of-scope.md`.
- **Drift hunters:** Cross-read this folder against the specs. If a spec describes behaviour with no matching requirement, either the requirement is missing OR the spec describes a bug. Flag in `08-traceability.md`.

## Versioning note

Requirements are **stable**. Code drifts; requirements should not. If a requirement is found to be wrong (e.g. the business actually does want mass balance enforced), it gets an explicit edit with a dated changelog entry — not a quiet rewrite. See `08-traceability.md` for the change log.
