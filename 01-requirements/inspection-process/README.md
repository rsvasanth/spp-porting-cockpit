# Inspection Process — Business Requirements

**Business motion:** Quality acceptance + deviation workflow for compound batches.
**Console processes covered:** Compound Inspection (CI) + Compound Deviation (CD).
**Legacy doctype target:** `Compound Inspection` (single doctype; CD writes the same doctype with status set by QM).
**Ops doctype target:** ERPNext `Stock Entry` (status-conditional: Material Transfer if Accepted, Material Issue if Rejected, none if Rework) via the generic MES Transaction Engine.

This document captures what the **business** needs the system to do. It is intentionally implementation-agnostic where possible. For "how it actually works today," see:

- [`../../03-parity-dossiers/compound-inspection-parity.md`](../../03-parity-dossiers/compound-inspection-parity.md) — CI porting proof across Console, Legacy Bridge, legacy ERPNext, and Ops
- [`../../02-specifications/compound-deviation/`](../../02-specifications/compound-deviation/) — particularly the Saga narrative in §09
- [`../../02-specifications/console-inspection-unification/`](../../02-specifications/console-inspection-unification/) — decommissioned design history; current runtime uses dedicated CI/CD doctypes

## Why CI + CD share one requirements folder

From Legacy's perspective, **CD is a CI**. Both produce the same legacy doctype (`Compound Inspection`) — they differ only in `status` field value, `quality_approver_*` fields, and downstream Stock Entry behavior. They share:

- The same compound identity resolution pipeline (`_resolve_compound_identity` + `_lookup_legacy_stock_entry` + the 6-strategy chain)
- Dedicated Console doctypes with shared Bridge identity-resolution invariants (`Console Compound Inspection` and `Console Compound Deviation`)
- The same Bridge populate pipeline (CD uses CI's helpers + `_apply_deviation_extras`)
- The same race-safe 5-step callback pattern (saga-validated)

Grouping them keeps the shared invariants in one place. Variant-specific requirements are tagged `[CI-only]` or `[CD-only]` within each file.

## The saga origin

**This motion is where the 5-step `apply_bridge_result` pattern and the program's test-gate rule were forged.** The Compound Deviation saga of 2026-04-29 → 2026-05-01 — multiple sequential fixes shipping without test coverage, each introducing new race conditions — drove the cockpit's production rules. Read [`../../02-specifications/compound-deviation/09-rollout-and-history.md`](../../02-specifications/compound-deviation/09-rollout-and-history.md) for the full timeline before touching anything in this motion.

## Files in this folder

| File | What it answers |
|---|---|
| [01-purpose.md](01-purpose.md) | Why CI + CD exist as a coupled pair; position in the manufacturing chain |
| [02-actors-and-roles.md](02-actors-and-roles.md) | Quality Inspector vs Quality Manager authority; decision rights |
| [03-functional-requirements.md](03-functional-requirements.md) | Numbered FRs (`FR-INS-NNN`). Variant tags `[CI-only]` / `[CD-only]` |
| [04-non-functional-requirements.md](04-non-functional-requirements.md) | Performance, reliability, audit, security |
| [05-business-rules.md](05-business-rules.md) | The "why" behind invariants: factory-requirement skip, empty-mapping pattern, status-conditional routing, 5-step pattern, cavity_no fallback |
| [06-acceptance-criteria.md](06-acceptance-criteria.md) | Plain-language UAT scripts for CI Accepted, CI Rejected, CD Accept-override, CD Reject, CD Rework |
| [07-out-of-scope.md](07-out-of-scope.md) | Explicit exclusions |
| [08-traceability.md](08-traceability.md) | FR ↔ Spec, NFR ↔ Spec, BR ↔ Spec mappings + drift findings + change log |

## Versioning note

The saga rules are **load-bearing**. The 5-step pattern, the empty-mapping pattern, the factory-requirement skip — these survived production race conditions. Do not relax them without re-running the concurrency tests.
