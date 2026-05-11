# 10 — Risks and decisions

## FB-specific plan-vs-reality deltas

Most MB deltas apply to FB identically (mass-balance not enforced,
denormalised Data fields, etc.). FB-specific ones:

| # | Delta | Plan said | Reality | My recommendation |
|---|---|---|---|---|
| 1 | `master_batch_input` Link field | Required Link to `Console Master Batch Mixing` row by mix_barcode | Not implemented; MB captured as first row of `consumption_items` with `is_batch_item=1` | **Defer** — the row-level approach works and matches the legacy DC Item shape. Promoting to Link adds FK pressure on a process that's already shipped. |
| 2 | Mandatory `compound_specification` field | Required field for compound formula | Not implemented; formula is implied by BOM | **Defer** — operators rarely need to override the BOM-defined formula. Add only when shop-floor requests deviation tracking. |
| 3 | FB-specific naming series | `CFBM-` | `FBM-` | **Same as MB** — accept the shorter name. |
| 4 | Multi-BOM rejection moved to Console? | n/a | Currently legacy-side (`validate_bom_items`, `create_wo_final_batch_mixing`) | **Defer** — moving validation to Console means duplicating BOM data sync. Legacy is the BOM owner; let it own validation. |

## FB-specific cross-doctype invariants

In addition to MB's invariants (all of which apply to FB), FB has:

| # | Invariant | Where enforced | Breaks if… |
|---|---|---|---|
| 1 | `is_batch_item=1` on FB's MB consumption row drives `validate_final_batches` branching | Dash payload `consumption_items[0].is_batch_item` + Bridge mapping + Legacy controller | Dash forgets to set the flag → non-batched path runs even when MB is the input |
| 2 | FB's `value_map` resolves `"Final Batch Mixing" → "Compound"` | `seed_mixing_process_mapping`'s `inward_material_map` JSON | Mapping deleted or modified → legacy routes FB into wrong DCR branch |
| 3 | FB produced item has exactly ONE active BOM | Legacy `create_wo_final_batch_mixing` line 637 + `validate_final_batches` line 181 | Two active BOMs → submission fails with "Multiple BOM's found"; recoverable only by deactivating the duplicate BOM |
| 4 | `Mixing Operation` master data has a row for the `source_warehouse` | Legacy `create_wo_final_batch_mixing` line 643 | Missing row → workstation defaults to `"Two Roll Mixing Mill"` regardless of Console payload's workstation value (silent override) |

## FB-specific operational risks

| Risk | Likelihood | Impact | Existing mitigation |
|---|---|---|---|
| Multi-BOM exists for produced Compound | Medium (legacy data quality) | FB submission fails with "Multiple BOM's found" | Legacy BOM cleanup required; no Console-side fix |
| MB lot scanned has stock=0 | Medium | Ops Stock Entry fails on `validate_warehouse_stock` | Operator sees Ops Failed; retry after restocking |
| `Mixing Operation` master data missing for shop floor's source warehouse | Low | Legacy silently defaults to "Two Roll Mixing Mill" | Add `Mixing Operation` row; not a code fix |
| Race in `apply_bridge_result` (same as MB) | Low | Handled by 5-step pattern | Confirmed working in production |
| Legacy `rollback_wo_se_jc` partial cleanup fails | Low | Stale WO/JC/SE on legacy after a failed FB submit | `frappe.db.rollback()` in catch block + manual cleanup script |
| FB submission's MB consumption doesn't actually decrement MB stock | Low | Stock ledger drift between Console + legacy | Per-system reconciliation script; not automated |

## Decisions deferred to a later wave

### Promote MB input to explicit Link field

`master_batch_input` as a Link to `Console Master Batch Mixing`. Pros:
- Reporting becomes simple ("which FBs consumed which MBs?")
- FK integrity catches typos

Cons:
- FK enforcement slows submit (one extra DB lookup)
- Migration: existing FB records have MB as a free-text `mix_barcode` in
  the child row; back-fill is needed to populate the new Link field

**Recommend:** add when reporting needs it. Currently the `mix_barcode`
in child row #0 is sufficient for trace.

### Workstation override discipline

Legacy auto-resolves workstation from `Mixing Operation` master data,
ignoring Console's value. This is fine when the master data is right;
breaks operator expectations when shop floor uses a different workstation
than what master data says.

**Recommend:** add a Dash-side check that warns the operator when the
selected workstation differs from `Mixing Operation`'s mapping. Don't
block — just inform.

### Consolidate MB+FB controllers

The two controllers are byte-identical Python. Could refactor to a shared
base class or mixin. Pros: single source of truth for the 5-step pattern.
Cons: makes the controller harder to read in isolation, and breaks the
1:1 mapping between Console process_code and file location that's
currently expected.

**Recommend:** defer. The duplication is acknowledged and tracked here.
Resolve when a third Wave 1-style "mixing-like" process appears (it
won't — the pattern is fully covered by MB + FB).

## Questions waiting on production overseer

Same five MB questions from `../master-batch-mixing/10-risks-and-decisions.md`,
plus:

| Question | My recommendation |
|---|---|
| Add a Dash-side warning when workstation override differs from `Mixing Operation` master data? | **Yes, soft warning** — log + show, don't block |
| Reconsider `master_batch_input` as explicit Link? | **No, defer** until reporting needs |
| Refactor MB+FB controllers into shared base? | **No, defer** indefinitely |
| Add automated stock reconciliation check between Console and Legacy? | **Yes** — separate epic, not blocking |
