# Compound Deviation — Specification

**Status:** SHIPPED. Most recent fix: 2026-05-09 (`a0fc0fc` — "rejected compound inspections not showing in Deviation screen").
**Console doctype:** `Console Compound Deviation` (`CDEV-.YYYY.-.#####`)
**Legacy doctype:** `Compound Inspection` (same legacy doctype as Compound Inspection — see `05-legacy-erpnext.md`)
**Ops doctype:** Generic `Stock Entry` via the MES Transaction Engine

> **Read [`../master-batch-mixing/`](../master-batch-mixing/) first** for the shared layers (Console backend pattern, 5-step `apply_bridge_result`, `_safe_local_create`, Live Feedback Dash flow). This spec documents the **deviation-specific** behaviour.

## Why Compound Deviation matters

This process is the **origin of the test-gate rule** and the **5-step
race-safety pattern**. The "Compound Deviation saga" of 2026-04-29 →
2026-05-01 — multiple sequential fixes shipping without test coverage,
each introducing new races — drove these production rules. The 2026-04-30
helper refactor (`1df2de8`) collapsed 200+ lines of duplicated SE lookup
logic into thin wrappers; the 2026-05-09 fix (`a0fc0fc`) closed a
remaining edge in the rejected-CI → Deviation routing.

If a Hermes worker reads only one cockpit spec, this is the one that
teaches the **why** behind the architecture's defensive choices.

## Key architectural facts

| Fact | Detail |
|---|---|
| Legacy doctype is `Compound Inspection`, not "Compound Deviation" | From Legacy's perspective, a Deviation IS a CI with `status` set to `Accepted`/`Rejected`/`Rework` by a QM and `remarks` carrying the reason. No separate legacy doctype. |
| Bridge mapping has **empty** `field_mappings` | `seed_compound_deviation_mapping` seeds the mapping row with `field_mappings=[]` — all population is done by `populate_compound_deviation_fields` in Python (not by the mapping engine) |
| Same identity/SE pipeline as Compound Inspection | `populate_compound_deviation_fields` calls the same `_resolve_compound_identity` → `_lookup_legacy_stock_entry` → `_apply_compound_identity_to_doc` chain as `populate_compound_inspection_fields`. The refactor that made this so is what stabilised the saga. |
| Rejected Compound Inspections route Ops-only | `initialize_submission` has the `FACTORY REQUIREMENT` skip: rejected CIs do NOT POST to Legacy. They later become Compound Deviations which DO POST to both legs. |
| Console Deviation doctype is separate from `Console Inspection` unification | Phase 1-4 unification put Compound Inspection under `Console Inspection`. Compound Deviation was kept separate (`Console Compound Deviation`) because the UX is distinct (QM signoff flow). |

## Deltas at a glance

| Layer | Same as MB? | Delta |
|---|---|---|
| 01-business-context | No | QM signoff workflow, overlay nature, three deviation statuses (Accepted/Rejected/Rework) |
| 02-frontend-dash | No | `CompoundDeviationEntry.tsx` — QM scan, references existing CI, status dropdown, deviation_reason required |
| 03-console-backend | Mostly | Same `_safe_local_create` pattern. `create_local_compound_deviation` has different `_pick` paths (no `consumption_items`; reads from `compound_inspection_data` + `compound_deviation_data` blocks). Controller validates `deviation_reason` (min 5 chars) — slightly stricter than MB |
| 04-bridge-layer | **NO — major** | Empty `field_mappings`; Bridge delegates entirely to `populate_compound_deviation_fields` Python function. **This is the saga's architectural fix.** |
| 05-legacy-erpnext | **NO — major** | Same `Compound Inspection` legacy doctype as CI, with `_apply_deviation_extras` adding QM-specific fields. Active `cavity_no` fallback (bug ref 1777721078171). |
| 06-ops-erpnext | Mostly | Same generic engine. Rejected CIs are NOT routed to Ops either (status-driven gating). |
| 07-end-to-end-flow | No | Different precondition (existing CI must be Rejected first), different routing logic (status-conditional targets) |
| 08-test-plan | Same | Same 3 unit tests + saga-driven concurrency tests |
| 09-rollout-history | **THE SAGA** | 2026-04-29 → 2026-05-01 → 2026-05-02 → 2026-05-09 narrative |
| 10-risks-and-decisions | Different | `cavity_no` wiring is the active TODO |

## Files in this folder

| File | Lines (target) | What it covers |
|---|---|---|
| [01-business-context.md](01-business-context.md) | ~120 | QM signoff workflow, overlay relationship to Compound Inspection, three statuses |
| [02-frontend-dash.md](02-frontend-dash.md) | ~140 | `CompoundDeviationEntry.tsx` flow — fetch rejected CI, QM scan, status + reason, submit |
| [03-console-backend.md](03-console-backend.md) | ~90 | `create_local_compound_deviation` _pick paths, validate hook deltas |
| [04-bridge-layer.md](04-bridge-layer.md) | ~120 | The empty-mapping pattern, the rationale for full Python population |
| [05-legacy-erpnext.md](05-legacy-erpnext.md) | ~220 | `populate_compound_deviation_fields` deep dive, `_apply_deviation_extras`, the cavity_no bug, the WAREHOUSE_MAP fallback |
| [06-ops-erpnext.md](06-ops-erpnext.md) | ~50 | "Same generic engine" + Ops-side status routing |
| [07-end-to-end-flow.md](07-end-to-end-flow.md) | ~150 | CI Rejected → Deviation → both legs trace |
| [08-test-plan.md](08-test-plan.md) | ~120 | Tests + the saga's lessons for concurrency testing |
| [09-rollout-and-history.md](09-rollout-and-history.md) | ~140 | **The saga narrative** — chronological, with every fix's intent |
| [10-risks-and-decisions.md](10-risks-and-decisions.md) | ~100 | `cavity_no` decision, the WAREHOUSE_MAP risk, status-gating gotchas |
