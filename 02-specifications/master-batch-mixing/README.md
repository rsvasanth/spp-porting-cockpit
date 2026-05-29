# Master Batch Mixing — Specification (layered, code-level)

**Status:** SHIPPED. In production on `console.m.frappe.cloud` since Wave 1 (2026-05-01).
**Wave:** 1 (head of the production chain)
**Console doctype:** `Console Master Batch Mixing` (`MBM-.YYYY.-.#####`)
**Legacy doctype:** `Delivery Challan Receipt` (`inward_material_type = "Master Batch"`) — ERPNext **v15**
**Ops doctype:** Generic `Stock Entry` via the MES Transaction Engine (no MB-specific Ops code)

**Parity dossier:** See [`../../03-parity-dossiers/mixing-mbm-fbm-dcr-parity.md`](../../03-parity-dossiers/mixing-mbm-fbm-dcr-parity.md) for the MBM/FBM/DCR porting proof, output expectations, failure capture plan, and real-data evidence checklist.

This spec is **authoritative for intent, contract, and what-must-not-break.**
For the latest implementation in any layer, the on-disk code + graphify graph
remain the source of truth. The spec quotes code verbatim only where the
logic is load-bearing for a cross-system invariant.

## Read the layers in order

| File | What it covers | Sample size |
|---|---|---|
| [01-business-context.md](01-business-context.md) | What the operator is doing on the shop floor, why it's first in the chain | small |
| [02-frontend-dash.md](02-frontend-dash.md) | `MasterBatchMixingEntry.tsx` — operator UX, scan flow, payload builder, retry/error handling | large |
| [03-console-backend.md](03-console-backend.md) | Console `api.py` orchestration — `initialize_submission`, `execute_submission_step`, `build_transaction_payload`, `create_local_master_batch_mixing`, `_safe_local_create`, `apply_bridge_result`, helpers | largest |
| [04-bridge-layer.md](04-bridge-layer.md) | `shree_polymer_legacy_bridge/sync_api.py::sync_process_transaction` — idempotency, mapping engine, value-map, callback emission | large |
| [05-legacy-erpnext.md](05-legacy-erpnext.md) | Legacy `Delivery Challan Receipt` controller hooks + SE creation chain + downstream Compound Inspection dependency | large |
| [06-ops-erpnext.md](06-ops-erpnext.md) | Ops `shree_polymer_ops::process_transaction` + `TransactionEngine` for the MB payload | medium |
| [07-end-to-end-flow.md](07-end-to-end-flow.md) | Single sequence diagram + narrative trace of one operator submission → green checkmark | medium |
| [08-test-plan.md](08-test-plan.md) | Unit (shipped + gaps), integration (parked), E2E, smoke, user acceptance | medium |
| [09-rollout-and-history.md](09-rollout-and-history.md) | Deploy history, what changed when, what Hermes can/cannot touch | small |
| [10-risks-and-decisions.md](10-risks-and-decisions.md) | Plan-vs-reality deltas, cross-doctype invariants, decisions waiting on you | small |

## Drift watch

This spec was written 2026-05-11 against:
- Console: `apps/shree_polymer_console` HEAD `a0fc0fc` (2026-05-09)
- Legacy: `apps/shree_polymer_custom_app` HEAD (DCR controller unchanged in recent commits)
- Bridge: `apps/shree_polymer_legacy_bridge` HEAD (post-`1df2de8` refactor)
- Ops: `apps/shree_polymer_ops` HEAD
- Graphify: refreshed 2026-05-11, 4565 nodes / 6566 edges

If any of these advance by more than ~10 commits without a spec review, re-grep
the quoted functions against current code before relying on this document for
a change.
