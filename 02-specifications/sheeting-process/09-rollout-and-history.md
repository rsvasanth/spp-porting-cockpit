# 09 — Rollout and history

## Current production status

Shipped on `console.m.frappe.cloud` in Wave 1 cohort (~2026-05-01).

## Deploy timeline

| Date | Event | Impact |
|---|---|---|
| 2026-04-29 | `Console Sheeting Process` doctype created | First materialisation |
| 2026-04-30 | `Console Sheeting Item` + `Console Sheeting Clip` children added | Multi-output handling enabled |
| 2026-04-30 | BCR-1 fix: `_write_clip_mappings_for_sheeting` moved to inline-with-create | Closed the window where downstream Blanking scans missed clip mappings |
| 2026-05-01 | Wave 1 deploy | Sheeting went live |
| 2026-05-02 | Bridge refactor (`1df2de8`) | No direct Sheeting impact (refactor focused on Compound Inspection helpers) |
| 2026-05-11 | Spec written | This document |

## How this shipped — same workflow

Same as MB Mixing (see [`../master-batch-mixing/09-rollout-and-history.md`](../master-batch-mixing/09-rollout-and-history.md)).
Sheeting has more moving parts (3 doctypes, 2 child tables on legacy,
clip mapping records) but the deploy pipeline is identical.

## BCR-1 fix — the inline clip-mapping write

Before BCR-1 (early Wave 1):
- Sheeting submission → Console record created
- Bridge fans out → Ops returns `impacted_clips`
- Callback writes `Console Item Clip Mapping` rows
- **Multi-second window** where downstream Blanking scans for the new
  clips would miss the mapping → "Clip not found" errors

After BCR-1:
- `create_local_sheeting_process` calls
  `_write_clip_mappings_for_sheeting` inline
- Clip mappings exist on Console **before** any Bridge call
- Downstream Blanking scans can find them immediately
- Ops callback later backfills the `ops_batch_no` field via
  `_backfill_ops_reference_for_sheeting`

The fix is **load-bearing for the downstream chain** — touching this
ordering reintroduces the window.

## Migration stance — hard replacement

Pre-Console Sheeting records (legacy Material Transfer documents created
directly on `sppmaster.frappe.cloud` before the Bridge existed) remain
historical data. Not back-filled into Console.

## What Hermes workers can change without architecture review

| Change | Risk |
|---|---|
| Add a new `_pick` fallback path | Low |
| Add a new field to `_SHEETING_ITEM_KEYMAP` | Low |
| Add a new mapping row to `seed_sheeting_process_mapping` | Low |
| Extend `populate_sheeting_fields` with new default fields | Low |
| Extend Dash with additional clip metadata (e.g. dimensions, weight) | Medium — must coordinate with `sheeting_clip` mapping |

## What Hermes workers must escalate

| Change | Why |
|---|---|
| Move `_write_clip_mappings_for_sheeting` to a callback path | **BCR-1 regression risk** — high impact |
| Touch the barcode synthesis at `sync_api.py:191` | Downstream consumers depend on `{item_code}_{original_batch}` format |
| Remove `"Cutbit_"` prefix detection | High — Ops-sourced payloads break |
| Touch the 5-step `apply_bridge_result` | **Highest** — same saga risk as MB |
| Change `material_transfer_type` literal | Medium — affects legacy controller branching |
| Modify `_backfill_ops_reference_for_sheeting` | Medium — affects clip mapping data quality |

## What Hermes workers must NOT do

- Remove the inline call to `_write_clip_mappings_for_sheeting` from
  `create_local_sheeting_process`
- Change the auto-numbering format `{source_mix_barcode}-{N}` for clips
- Change the `Cutbit_` prefix convention for cut-bit batch numbers
- Modify the `Material Transfer` legacy controller without explicit
  go-ahead from production overseer

## Drift vs plan

`01_WAVE1.md` planned `CSHT-` naming series — shipped as `CSHT-` (match).
Many planned fields not implemented (consistent with the lean-doctype
pattern across Wave 1). The biggest plan-vs-reality delta:

- Plan called for `Console Sheeting Clip` as the per-clip child of
  `Console Sheeting Process` — implemented, but the relationship is
  through `Console Item Clip Mapping` (a separate doctype) rather than
  an inline child table. This is cleaner because the mapping is what
  downstream processes scan.

## Reviewer worker checklist

Before promoting "Tests Passing" → "Pushed":

- [ ] All Sheeting unit tests pass (5+ recommended)
- [ ] If touching `apply_bridge_result`: concurrency test added with both kwargs paths exercised
- [ ] If touching `_write_clip_mappings_for_sheeting`: BCR-1 invariant test passes
- [ ] If touching mapping seeder: smoke test passes
- [ ] One staging submission with 3 clips + 1 cut-bit successful
- [ ] Verify `legacy_spp_batch_no` populated on Console doc within 30 seconds
- [ ] Verify `Console Item Clip Mapping` rows have both Console and Ops batch refs
- [ ] Obsidian note logged
- [ ] Graphify refreshed
