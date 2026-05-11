# 09 — Rollout and history

## Current production status

**Shipped to production-staging** on `console.m.frappe.cloud` via
`iyyanarr/shree_polymer_console:develop`. Auto-deployed by Frappe Cloud
from `iyyanarr/develop` whenever rsvasanth's fork is manually synced to
iyyanarr.

## Deploy timeline (chronological)

| Date | Commit / Event | Impact on MB Mixing |
|---|---|---|
| 2026-04-29 | `Console Master Batch Mixing` doctype created (`creation: 2026-04-29 14:24:36`) | First materialisation of the doctype on disk |
| 2026-04-30 | `Console Master Batch Item` child added | Consumption rows now persisted alongside parent |
| 2026-04-30 | Legacy Bridge helper refactor (commit `1df2de8`) | Extracted `_resolve_compound_identity`, `_lookup_legacy_stock_entry`, `_apply_compound_identity_to_doc`. Downstream Compound Inspection now uses the 6-strategy chain to find this MB's SE |
| 2026-05-01 | Phase 1-4 deploy of Console Inspection unification | MB Mixing was already in dev; the inspection-unification work ran in parallel |
| 2026-05-02 | Bridge refactor (`1df2de8`) deployed | Production switched to the 6-strategy lookup |
| 2026-05-09 | Compound Deviation fix (`a0fc0fc`) | Affects MB Mixing output when QA rejects the resulting compound — deviation flow now correctly references this MB record |
| 2026-05-11 | Spec written (this file) | Documenting current state for Hermes handoff |

## How this shipped (workflow)

| Step | Owner | Mechanism |
|---|---|---|
| Doctype JSON + controller | rsvasanth | Committed on `rsvasanth/develop` |
| `_safe_local_create` helper | rsvasanth | Same commit window |
| `console_mapping_seeder.py::seed_mixing_process_mapping` | rsvasanth | Idempotent upsert; runs on Console install |
| Dash component `MasterBatchMixingEntry.tsx` (1068 lines) | rsvasanth | Built + tested locally before commit |
| Built dash assets in `shree_polymer_console/public/dash/assets/` | GitHub Actions `build-dash.yml` | Auto-built + auto-committed on push |
| Frappe Cloud deploy | Automatic | Reads `iyyanarr/develop` after manual sync from rsvasanth |
| Production validation | rsvasanth + shop-floor operator | Live submission on `console.m.frappe.cloud` |

## Migration stance

**Hard replacement.** Pre-Console MB mixings (i.e. DCRs created directly
on legacy before the Bridge existed) remain as historical data on legacy
ERPNext. They are **not** back-filled into Console.

**Implication for reporting:** querying "all MB mixes for batch X" must
check both:
- `Console Master Batch Mixing` (new records, have `reference_id`)
- Legacy `Delivery Challan Receipt` (pre-cutover records, no `reference_id`)

Until a back-fill epic runs (no plans currently), Console is **not
exhaustive** for the full history of MB lots.

## What Hermes workers can change without architecture review

| Change | Risk |
|---|---|
| Add new field to `Console Master Batch Mixing` (with corresponding `_pick` path + Bridge mapping + Dash payload) | Low — additive, follows established pattern |
| Add a value-map entry to the `inward_material_type` row | Low — additive |
| Add unit tests | Low — purely positive |
| Extend Dash UX (extra fields, better error messages, retry UX) | Low — surface-only |
| Add a new `_pick` fallback path in `create_local_master_batch_mixing` | Low — tolerance only |

## What Hermes workers must escalate (Reviewer worker + you sign off)

| Change | Why |
|---|---|
| Touch the 5-step `apply_bridge_result` controller method | Production race-safety, originated from Compound Deviation saga; needs concurrency tests |
| Touch `_safe_local_create` flag pattern (`from_local_cache`, `ignore_validate`) | Audit-trail invariant relied on by all 7 shipped Console doctypes |
| Touch `_lookup_legacy_stock_entry` strategy chain in Bridge | Downstream Compound Inspection depends on every strategy; deletion needs proof of zero hits |
| Reinstate or change mass-balance validation | Operational impact on shop floor (block vs warn) — see `10-risks-and-decisions.md` |
| Change `legacy_doctype_map` in `update_local_domain_record` | Affects multiple Console doctypes, not just MB |
| Modify legacy `Delivery Challan Receipt` controller | Affects ALL inbound material flows, not just MB |

## What Hermes workers must NOT do

| Action | Reason |
|---|---|
| Remove `reference_id` uniqueness constraint | Breaks cross-system correlation invariant |
| Change the meaning of `sync_status = "Success"` | Currently means: both legs synced AND Console doc auto-submitted. Changing this breaks every downstream consumer that uses sync_status as a proxy for "ready to consume." |
| Bypass Legacy or Ops for performance | Parallel sync is load-bearing for eventual consistency |
| Add direct Legacy → Console webhooks | Current model is one-way (Console pulls); reversing this needs full architecture review |
| Remove `bridge_mix_barcode` override on Legacy DCR | Breaks single-barcode-authority invariant; downstream Compound Inspection breaks |

## Drift vs the porting plan

The original wave doc (`/Users/alphaworkz/frappe-bench/spp_process_docs/console_porting/01_WAVE1.md`,
dated 2026-04-29) is **partially stale**:

- Naming series specified as `CMBM-` in plan; shipped as `MBM-`
- ~18 process fields planned; ~13 shipped (simpler)
- Mass-balance check planned; deliberately not implemented
- `produced_item` planned as Link; shipped as Data
- `operator_id` planned as Link; shipped as `operator_name` Data
- `mixing_start_time` / `end_time` planned; not implemented
- `barcode_image` Attach planned; not stored (rendered live in Dash)
- `bom_no` planned as Link; not stored

**This cockpit spec supersedes the wave doc.** Going forward, the
authoritative reference for MB Mixing is this folder. The wave doc should
be marked historical (decision pending in `10-risks-and-decisions.md`).

## Related cockpit specs

- **Final Batch Mixing** (Wave 1 sibling) — same pattern with slightly
  different value-map and the FB-specific `validate_final_batches` path
  on legacy. Cockpit spec pending.
- **Compound Inspection** (downstream consumer) — depends on this MB's
  `mix_barcode` round-trip and `_lookup_legacy_stock_entry` strategies.
  Cockpit spec pending; the existing Console Inspection unification (5
  shipped doctypes) is what landed instead of the planned
  `Console Compound Inspection` per-type doctype.
- **Compound Deviation** (sibling) — overlay on rejected Compound
  Inspection; cockpit spec pending. Its production race saga is the origin
  of the 5-step pattern documented in this spec.

## Reviewer worker checklist (when verifying a MB Mixing change)

Before promoting a PR's "Tests Passing" card to "Pushed":

- [ ] All 3 shipped unit tests pass on `sppconsole-dev.local`
- [ ] If touching `apply_bridge_result`: concurrency test added + passing
- [ ] If touching mapping seeder: value-map test passes + smoke test green
- [ ] If touching Dash: at least one E2E happy-path passes
- [ ] One staging end-to-end submission completes with `sync_status=Success`
- [ ] Obsidian note logged at `/Users/alphaworkz/claude-obsidian/claude/`
- [ ] Graphify refreshed; cockpit spec snippets cross-checked against new
      AST (if any quoted function changed signature, this spec needs an
      update in the same PR)
