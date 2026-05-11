# 09 — Rollout and history

## Current production status

Shipped to production-staging on `console.m.frappe.cloud` as part of the
same Wave 1 cohort as MB Mixing (2026-05-01). Same deploy pipeline:
`iyyanarr/shree_polymer_console:develop` → Frappe Cloud auto-deploy.

## Deploy timeline

| Date | Event | Impact |
|---|---|---|
| 2026-04-29 | `Console Final Batch Mixing` doctype created (`creation: 2026-04-29 14:24:37`) | First materialisation |
| 2026-04-30 | `Console Final Batch Item` child added | Consumption rows persisted |
| 2026-04-30 | `console_mapping_seeder.py::seed_mixing_process_mapping` added `_upsert_mapping("FINAL_BATCH_MIXING", ...)` | Bridge can route FB submissions |
| 2026-05-01 | Phase 1-4 deploy | FB Mixing went live alongside MB |
| 2026-05-02 | Bridge refactor (`1df2de8`) | No direct FB impact (refactor was Compound Inspection) |
| 2026-05-09 | Compound Deviation fix (`a0fc0fc`) | Affects FB output when QA rejects the resulting Compound |
| 2026-05-11 | Spec written | Documentation handoff |

## How this shipped — same as MB

Same workflow as MB Mixing per [`../master-batch-mixing/09-rollout-and-history.md`](../master-batch-mixing/09-rollout-and-history.md).
Both processes shipped in the same commit window with shared code.

## Migration stance — hard replacement

Same as MB Mixing. Pre-Console FB submissions (DCRs created directly on
legacy before the Bridge existed) remain historical data on legacy
ERPNext and are NOT back-filled into Console.

## What Hermes workers can change without architecture review

| Change | Risk |
|---|---|
| Add FB-specific fields to `Console Final Batch Mixing` | Low — same pattern as MB; remember to also touch MB if cross-process consistency matters |
| Add new value-map entry for a new operation variant | Low — additive |
| Add unit tests | Low |
| Extend Dash UX (e.g. MB-scan confirmation step) | Low |

## What Hermes workers must escalate

| Change | Why |
|---|---|
| Touch the 5-step `apply_bridge_result` on FB controller | **Must touch MB's too in same PR** — they are duplicated logic |
| Touch shared `field_mappings` in `seed_mixing_process_mapping` | Affects both MB and FB; possibly diverge them if FB needs different behavior |
| Modify legacy `validate_final_batches` | **Affects all Compound DCRs**, not just FB |
| Modify `create_wo_final_batch_mixing` or `make_stock_entry_final_batch` | Affects FB production; high blast radius |
| Modify `rollback_wo_se_jc` | Used by FB AND other DCR flows |

## What Hermes workers must NOT do

Same as MB — see [`../master-batch-mixing/09-rollout-and-history.md`](../master-batch-mixing/09-rollout-and-history.md).
Plus:

- Do NOT remove `is_batch_item` from the FB payload — it's the only signal
  that distinguishes batched vs non-batched FB paths on legacy
- Do NOT change the FB `inward_material_type` value-map output from
  `"Compound"` — every downstream consumer (Compound Inspection,
  Sheeting) relies on this exact value
- Do NOT merge the FB controller with MB's without first proving they
  can stay 100% identical (or refactoring both to share a base class)

## Drift vs plan

Same drift pattern as MB:
- Naming `CFBM-` in plan; shipped as `FBM-`
- Many planned fields not implemented (same omissions as MB)
- Plan-doc `01_WAVE1.md` is partially stale — this spec supersedes
- **Plan-doc difference:** the plan mentioned `master_batch_input` (Link
  to `Console Master Batch Mixing` row by mix_barcode) — not implemented.
  Instead the MB lot is captured as the first row of `consumption_items`
  with `is_batch_item=1`. This is simpler but loses the explicit Link
  for traceability/reports.

## Related cockpit specs

- [`../master-batch-mixing/`](../master-batch-mixing/) — the upstream process this depends on
- Compound Inspection (cockpit spec pending) — the next downstream consumer; reads FB's mix_barcode
- Compound Deviation (cockpit spec pending) — handles FB lots rejected at Compound Inspection

## Reviewer worker checklist (when verifying an FB change)

Before promoting "Tests Passing" → "Pushed":

- [ ] All 3 shipped FB unit tests pass
- [ ] If touching `apply_bridge_result`: MB's was touched in same PR + concurrency test added
- [ ] If touching mapping seeder: both MB and FB value-map tests pass
- [ ] If touching Dash: at least one E2E happy-path (with MB scan) passes
- [ ] One staging end-to-end FB submission completes with `sync_status=Success`
- [ ] **The produced Compound's `mix_barcode` is verified to round-trip to the legacy SE's FG row** (this is the FB-specific assertion)
- [ ] Obsidian note logged
- [ ] Graphify refreshed; quoted functions checked for AST drift
