# Blank Bin Inward Entry — Specification (forward-looking, Wave 2 target)

**Status:** NOT YET SHIPPED. Wave 2 target per plan doc `02_WAVE2.md`.
**Console doctype (planned):** `Console Blank Bin Inward Entry` (`CBBIE-.YYYY.-.#####`)
**Legacy doctype:** `Blank Bin Inward Entry` (custom legacy doctype on Legacy v15)
**Ops doctype targets:** Native ERPNext `Asset Movement` (Receive Bin) for default bin path, OR `Stock Entry` (Repack) for the cut-bit warehouse branch.

> **This spec describes the PLANNED shape.** When implementation lands, sections will be revised against actual shipped code (drift findings expected). For shipped patterns, read [`../master-batch-mixing/`](../master-batch-mixing/) (orchestration). `blanking-dc-entry/` is useful as a sibling drift template but is not staging/prod shipped yet.

## What this process does

Once a bin is filled with blanked compound at the blanking floor (via Blanking DC Entry), it must be moved to the **Moulding Unit warehouse** so the Moulding Operator can consume it during MPE. This is BBIE's job — a physical bin movement event.

Two paths:
- **Bin path (default):** Bin moves intact from blanking warehouse → Moulding Unit warehouse. Asset Movement (Receive Bin) created on both ERPs.
- **Cut-bit repack path:** Operator toggles `move_to_cut_bit_warehouse=1`. Bin contents extracted to cut-bit warehouse with `Cutbit_<item_code>` batch convention. Bin itself returns to "Available" status.

## Architectural facts (planned)

| Fact | Detail |
|---|---|
| Naming series | `CBBIE-.YYYY.-.#####` |
| Two-path branching | `move_to_cut_bit_warehouse` flag drives SE vs Asset Movement creation |
| Default path | Asset Movement (Receive Bin) on Legacy + Ops |
| Cut-bit repack path | Stock Entry (Repack) with `Cutbit_<item_code>` batch — same convention as Cut Bit Transfer |
| Identity | Bin's Asset name + barcode |
| Net weight re-verification | Optional soft warning if drift > 5% from BDE-recorded weight |
| Dedicated Ops handler (likely) | Asset Movement creation + branching can't be expressed in generic engine — Charter Principle 2 exception |
| Same 5-step apply_bridge_result | Inherited saga pattern |

## Files in this folder

| File | What it covers |
|---|---|
| [01-business-context.md](01-business-context.md) | Shop-floor meaning, bin lifecycle position, branching rationale |
| [02-frontend-dash.md](02-frontend-dash.md) | Planned Dash UX — bin scan + warehouse toggle + transparency |
| [03-console-backend.md](03-console-backend.md) | Planned api.py function shape; inherited orchestration |
| [04-bridge-layer.md](04-bridge-layer.md) | Bridge mapping + planned populate function with branching logic |
| [05-legacy-erpnext.md](05-legacy-erpnext.md) | Legacy doctype + Asset Movement creation chain |
| [06-ops-erpnext.md](06-ops-erpnext.md) | Dedicated Ops handler design + Asset Movement on Ops |
| [07-end-to-end-flow.md](07-end-to-end-flow.md) | Trace narrative for both paths |
| [08-test-plan.md](08-test-plan.md) | Tests including branching coverage |
| [09-rollout-and-history.md](09-rollout-and-history.md) | Wave 2 deployment plan |
| [10-risks-and-decisions.md](10-risks-and-decisions.md) | Branching design risks, weight re-verification policy |
