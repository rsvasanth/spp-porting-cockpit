# 09 — Rollout and history

## Current status

**NOT YET SHIPPED.** Wave 3 target per plan doc `03_WAVE3.md`.

## Wave 3 deployment plan

1. Add `lot_number` custom field to Ops `Work Order` + `Job Card`
2. Modify Legacy `Add On Work Planning.before_insert` to honor Console-provided `lot_number`
3. Create `Console Add On Work Planning` doctype as the supplemental planning process
4. Implement `_generate_lot_number(posting_date)` helper in `api.py`
5. Add DB-level unique constraint on `Console Add On Work Planning.lot_number` (recommended for race-safety)
6. Implement `create_local_add_on_work_planning` in `api.py`
7. Implement controller with 5-step apply_bridge_result byte-identical
8. Add `seed_add_on_work_planning_mapping` in `console_mapping_seeder.py`
9. Implement Bridge populate function (lightweight — mapping engine does most work)
10. Implement Legacy `create_planning_with_jobcards` whitelisted method (atomic rollback critical)
11. Configure Ops `Console Process Template` actions sequence (WO + for_each JCs)
12. Implement `AddOnWorkPlanningEntry.tsx` React component with workstation override + target drift UX
13. Add Lot # generation log doctype `Console Lot Number Generation Log` (optional but recommended for audit)
14. Run all tests including concurrency
15. Staging cutover

## What can be reused

| Reuse | Source |
|---|---|
| 5-step `apply_bridge_result` pattern | Copy from MB byte-for-byte |
| `_safe_local_create` | Existing helper |
| `_pick`, `_backdate_fields`, `_normalize_items` | Existing helpers |
| Generic Ops `TransactionEngine` | Existing |
| Live Feedback Promise.all pattern | Standard |
| Multi-BOM rejection logic | Mirror MB controller's pattern |

## What's net new

| New | Why |
|---|---|
| Lot # generator with daily sequence | First Console-authored cross-system identity (after mix_barcode) |
| Race-safe Lot # generation | New invariant; concurrency test mandatory |
| Legacy `before_insert` honor-Console-Lot # | Wave 3 controller modification |
| `create_planning_with_jobcards` whitelisted method | Atomic WO + JC creation |
| Ops Work Order custom field `lot_number` | Custom field; ERPNext customization needed |
| `for_each items` engine action | Iteration support in TransactionEngine (verify capability) |
| Separate Add On identity | Preserves Work Planning one-per-shift base-plan rule |
| Workstation override transparency UX | Pre-submit transparency |

## Migration stance

Hard replacement for new AOWP submissions. Legacy Work Planning submissions on Desk (pre-Console) remain as historical.

## What Hermes workers can change without architecture review

| Change | Risk |
|---|---|
| Add new field to Console AOWP | Low |
| Add new mapping rows | Low |
| Tighten validation | Low |
| Extend Lot # generation log | Low |

## What Hermes workers must escalate

| Change | Why |
|---|---|
| Touch `_generate_lot_number` | Concurrency-sensitive; needs test |
| Modify `create_planning_with_jobcards` | Atomicity invariant |
| Touch 5-step pattern | Saga regression |
| Change Lot # format | Cross-program invariant |
| Remove workstation override | Master data authority broken |

## Reviewer worker checklist

When AOWP ships:

- [ ] Lot # concurrency test passes (100 simultaneous, no duplicates)
- [ ] Atomic rollback test passes (force JC failure mid-flight)
- [ ] Multi-BOM rejection test passes
- [ ] Target drift warning UX verified
- [ ] Workstation override transparency UX verified
- [ ] One staging E2E with multi-row submission
- [ ] Downstream BBI can scan generated Lot #
- [ ] Saga concurrency test on apply_bridge_result
