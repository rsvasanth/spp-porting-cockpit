# Moulding Production Entry — Specification

**Status:** PORTING PHASE 2. Not yet shipped. Live on `spp15.local` as legacy `Moulding Production Entry` (`MLDPE-.#####`).
**Wave:** 2 (terminal production booking — closes the production chain)
**Console doctype:** `Console Moulding Production Entry` (planned)
**Legacy doctype:** `Moulding Production Entry` (`MLDPE-.#####`) — ERPNext **v15** custom doctype
**Ops doctype:** `Console Moulding Production Entry` via the MES Transaction Engine (planned)

This spec is **authoritative for intent, contract, and what-must-not-break.**
For the latest implementation, on-disk code + graphify graph remain the source
of truth. The spec quotes code verbatim only where the logic is load-bearing
for a cross-system invariant.

> **Relationship to other specs:** MPE is the **terminal production booking**
> in the shop-floor chain. It consumes open [Blank Bin Issue](../blank-bin-issue/)
> rows (FR-MPE-003/004), validates [Inspection Entry](../inspection-entry/)
> Line/Patrol prerequisites (FR-MPE-002), applies production tolerance from
> `SPP Settings` (not hardcoded), creates/submits the Manufacture Stock Entry,
> completes Job Card and Work Order, and cascades the produced batch to
> inspection rejection Stock Entries. For the shared orchestration layers
> (Console backend, Bridge mapping, Ops engine), see the analogous sections in
> [Master Batch Mixing](../master-batch-mixing/) — patterns are identical,
> differences are noted per section.

## Read the layers in order

| File | What it covers | Size |
|---|---|---|
| [01-business-context.md](01-business-context.md) | What the operator is doing, why it's the last link in the production chain | small |
| [02-frontend-dash.md](02-frontend-dash.md) | Dash UX, scan flow, payload builder, retry/error handling (planned) | medium |
| [03-console-backend.md](03-console-backend.md) | Console `api.py` orchestration + `make_stock_entry` cascade | large |
| [04-bridge-layer.md](04-bridge-layer.md) | Legacy Bridge mapping + post-submit cascade behavior | medium |
| [05-legacy-erpnext.md](05-legacy-erpnext.md) | Legacy `Moulding Production Entry` controller — full validate + on_submit | largest |
| [06-ops-erpnext.md](06-ops-erpnext.md) | Ops `shree_polymer_ops::process_transaction` for MPE payload | medium |
| [07-end-to-end-flow.md](07-end-to-end-flow.md) | Single sequence diagram + narrative trace of one operator submission | medium |
| [08-test-plan.md](08-test-plan.md) | Unit (gaps), integration (parked), E2E, smoke, user acceptance | medium |
| [09-rollout-and-history.md](09-rollout-and-history.md) | Deploy history, what changed when | small |
| [10-risks-and-decisions.md](10-risks-and-decisions.md) | Plan-vs-reality deltas, drift findings, decisions waiting on you | medium |

## Drift watch

This spec was written 2026-05-12 against:
- Legacy: `apps/shree_polymer_custom_app` HEAD `Moulding Production Entry` controller (30,006 records on `spp15.local`, 28,931 submitted)
- Requirements: `spp-porting-cockpit/01-requirements/moulding-production-entry/` (8 files, 305 lines)
- Reference spec: [Master Batch Mixing](../master-batch-mixing/) (authoritative template)

**Key drift findings from requirements vs legacy code:**

1. **FR-MPE-009 / BR-MPE-005 tolerance:** Old requirement said "hardcoded 1%." Legacy controller `validate_tolerance()` uses `SPP Settings.production_tolerance` — configurable, not hardcoded. Legacy returns a warning message rather than a hard throw. This spec treats `production_tolerance` as authoritative.

2. **FR-MPE-015 batch format:** Old requirement assumed fixed `T-<lot>-<seq>` format. Legacy uses `generate_batch_no(batch_id="T"+scan_lot_number, ...)` contract — the format is owned by `shree_polymer_custom_app.api::generate_batch_no`. This spec does not prescribe the internal format.

3. **MPE cascade vs IE cascade:** Both cascade inspection stock entries, but MPE's `submit_inspection_stock_entries_from_moulding()` covers Line/Patrol in one helper, while Inspection Entry's cascade is broader (including Lot Inspection, separate SE creation path). Both documented separately; do not conflate.

4. **`manual_on_submit` deprecated:** Legacy controller has `manual_on_submit()` kept for backward compat but the new flow submits the Stock Entry immediately inside `make_stock_entry()`. Console must implement the immediate-submit pattern, not the deferred `manual_on_submit` pattern.

5. **Injection flag derivation:** `is_injection_moulding` is set from workstation name (`INJECTION` / `INJUCTION` substring check) in `validate()`, not from a separate field or configuration.

## Cross-doctype relationships

```
Blank Bin Issue (BBI) ──► Inspection Entry (Line + Patrol) ──► Moulding Production Entry
     │                              │                                │
     │ consumed by FR-MPE-003       │ required by FR-MPE-002         │
     │ active bin check FR-MPE-004  │ rejection weight FR-MPE-010   │
     └──────────────────────────────┴───────────────────────────────┘
                                          │
                                          ▼
                              Manufacture Stock Entry (created + submitted)
                                          │
                                          ▼
                              Job Card completed │ Work Order completed
                              Bin closure (update_bins) │ Inspection cascade
```

> **Dependency note:** BBI spec lives at `../blank-bin-issue/`. Inspection Entry
> spec lives at `../inspection-entry/`. Both must be shipped before MPE
> integration tests can run. See `09-rollout-and-history.md` for sequencing.