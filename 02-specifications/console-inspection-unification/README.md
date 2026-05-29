# Console Inspection Unification — Specification [DECOMMISSIONED]

> [!CAUTION]
> **OBSOLETE / DECOMMISSIONED (2026-05-20)**
> The Console Inspection Unification requirement is officially **no longer valid**. 
> By direction of the product overseer, the system will continue to use distinct, dedicated doctypes (`Console Compound Inspection` and `Console Compound Deviation`) instead of a single unified `Console Inspection` doctype.
> 
> This folder is preserved purely for historical context. Refer to:
> - [`../compound-deviation/`](../compound-deviation/) for Deviation requirements.
> - [`../inspection-process/`](../inspection-process/) for Compound Inspection requirements.

**Status:** DECOMMISSIONED / HISTORICAL ONLY. Do **not** implement or reference.
**Combined coverage:** 5 Console doctypes (`Console Inspection`, `Console Inspection Reading`, `Console Inspection Reading Spec`, `Console Compound Inspection`, `Console Compound Inspection Reading`).
**Naming series:** `INSP-.YYYY.-.#####` (unified parent).
**Legacy doctype:** `Compound Inspection` (single doctype on Legacy, shared with Compound Deviation).
**Ops doctype:** ERPNext `Stock Entry` (status-conditional Material Transfer / Issue) via the generic MES Transaction Engine.

> **Read [`../master-batch-mixing/`](../master-batch-mixing/) first** for the shared orchestration backbone (`initialize_submission`, `_safe_local_create`, the 5-step `apply_bridge_result` pattern). This spec documents the **unification-specific** architecture: one doctype, multiple types, polymorphic readings, family-driven identity.
>
> **Read [`../compound-deviation/`](../compound-deviation/)** for the **saga narrative** that motivated this unification (`09-rollout-and-history.md` §The Saga).

## What this spec covers

The Phase 1–4 unification consolidated three pre-existing legacy per-type Console doctypes into one **polymorphic** `Console Inspection` doctype. The driving idea: from the business perspective, "compound inspection," "compound deviation," and "quality inspection" are **variants of one event** (a QA decision recorded against a material or production lot). Maintaining three separate doctypes duplicated schema, controller logic, and the saga's race-safety pattern.

The unification:
- Replaced 3 per-type Console doctypes with 1 unified doctype
- Added **`inspection_type`** Link to Process Template (Console-level type discriminator)
- Added **`inspection_family`** (Compound / Production) — drives identity selection
- Added **polymorphic readings child table** (`Console Inspection Reading`) capturing measurements / defect counts / visual / dimensional values via a `reading_type` field
- Added **`Console Inspection Reading Spec`** child — declarative spec rules per inspection_type
- Implemented a **validation dispatch method** mechanism — each inspection_type registers a Python function in `Console Process Template.validation_dispatch_method` for type-specific validation

## Co-existence with pre-Phase-3 per-type doctypes

Three pre-existing Console doctypes still exist for **backward compatibility with records created before the Phase 3 cutover**:

| Pre-Phase-3 doctype | Replaced by | Why preserved |
|---|---|---|
| `Console Compound Inspection` | `Console Inspection` (inspection_family=Compound) | Pre-cutover records keep their original doctype; their `apply_bridge_result` callbacks must still resolve |
| `Console Compound Inspection Reading` | `Console Inspection Reading` (reading_type=Compound) | Pre-cutover child rows preserved |
| `Console Compound Deviation` | `Console Inspection` (inspection_type=Compound Deviation per Process Template) | Same |

The module-level `apply_bridge_result` dispatcher in `api.py` includes ALL of these in its `parent_doctypes` lookup list, so callbacks for pre-cutover records still find their parent.

**Eventual deprecation:** these legacy per-type doctypes will be retired after a backfill epic — out of program scope. For now, three doctypes co-exist.

## Architectural facts unique to this unification

| Fact | Detail |
|---|---|
| Single unified parent | `Console Inspection` (naming `INSP-.YYYY.-.#####`) — co-exists with pre-Phase-3 doctypes |
| `inspection_type` Link | Points to `Console Process Template`; carries denormalised `process_code` and `inspection_family` |
| `inspection_family` discriminator | `Compound` / `Production` — selects identity fields (mix_barcode vs lot_no) and Bridge sequence |
| Polymorphic readings child | `Console Inspection Reading` with `reading_type` Select: `Measurement`/`Defect Count`/`Visual`/`Dimensional` |
| Reading spec child | `Console Inspection Reading Spec` declares min/max/expected per parameter per type |
| Validation dispatch | Each type can register a Python function (`shree_polymer_console.api.<func_name>`) via Process Template field |
| Phase 3 dispatch | `is_inspection_type=1` on Process Template routes `initialize_submission` to `create_local_inspection` (unified) |
| Same legacy doctype | `Compound Inspection` on Legacy receives both CI and CD via shared `populate_*_fields` helpers (see CD spec §05) |
| Same 6-strategy SE lookup | Used by both CI and CD via shared identity helpers |
| Same 5-step apply_bridge_result | Saga pattern preserved byte-identically |
| Same factory-requirement skip | Rejected CIs route Ops-only |
| Same cavity_no fallback | The active TODO from CD spec applies here too |

## Files in this folder

| File | What it covers |
|---|---|
| [01-business-context.md](01-business-context.md) | What "inspection" means at SPP; family taxonomy (Compound vs Production); why unify |
| [02-frontend-dash.md](02-frontend-dash.md) | Per-type React component pattern; how Process Template drives UI component selection |
| [03-console-backend.md](03-console-backend.md) | `create_local_inspection` unified path; family-driven identity extraction; validation dispatch; 5-step `apply_bridge_result` |
| [04-bridge-layer.md](04-bridge-layer.md) | Phase 3 dispatch via Process Template flag; shared helpers with CD spec; Bridge mapping inheritance |
| [05-legacy-erpnext.md](05-legacy-erpnext.md) | Legacy `Compound Inspection` doctype shared between CI + CD; backward compat with per-type Console doctypes |
| [06-ops-erpnext.md](06-ops-erpnext.md) | Generic TransactionEngine with status-conditional actions |
| [07-end-to-end-flow.md](07-end-to-end-flow.md) | Trace of one Compound Inspection submission (Accepted vs Rejected paths) |
| [08-test-plan.md](08-test-plan.md) | Tests including the family-discrimination, validation-dispatch, and 5-step saga regression for all 3 doctypes |
| [09-rollout-and-history.md](09-rollout-and-history.md) | Phase 1-4 deploy timeline + how this relates to the Compound Deviation saga |
| [10-risks-and-decisions.md](10-risks-and-decisions.md) | Co-existence drift, validation dispatch hygiene, per-type doctype deprecation path |
