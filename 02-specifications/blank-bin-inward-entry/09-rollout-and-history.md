# 09 — Rollout and history

## Current status

**NOT YET SHIPPED.** Wave 2 target per plan doc `02_WAVE2.md`.

## Wave 2 deployment plan

Per plan doc — implementation sequence:

1. Create `Console Blank Bin Inward Entry` doctype with fields per [02-frontend-dash.md](02-frontend-dash.md) §Planned payload shape
2. Implement `create_local_blank_bin_inward_entry` in `api.py`
3. Implement controller with `validate`, `before_insert`, `on_submit`, `apply_bridge_result` (5-step byte-identical)
4. Add `seed_blank_bin_inward_entry_mapping` in `console_mapping_seeder.py`
5. Implement Bridge populate function `populate_blank_bin_inward_fields` with branching
6. Implement dedicated Ops handler `submit_blank_bin_inward_entry(context, run_legacy_sync=False)`
7. Add `processRegistry.tsx` entry: `BLANK_BIN_INWARD → BlankBinInwardEntry`
8. Implement `BlankBinInwardEntry.tsx` React component
9. Run all tests, then staging cutover

## What can be reused

| Reuse | Source |
|---|---|
| 5-step `apply_bridge_result` pattern | Copy from MB doctype byte-for-byte |
| `_safe_local_create` audit-trail bypass | Existing helper |
| `_pick` and `_backdate_fields` | Existing helpers |
| Cut-bit `Cutbit_<item>` batch convention | Same as Cut Bit Transfer |
| `use_serial_batch_fields=1` SABB handling | Same as Cut Bit Transfer for Ops Stock Entry |
| Live Feedback Promise.all pattern | Standard for all Wave 1+ |
| `run_legacy_sync=False` Console-path invariant | Same as Cut Bit Transfer |

## What's net new

| New | Why |
|---|---|
| Branching design (bin path vs cut-bit path) | First process with explicit two-path output |
| Asset Movement creation on both ERPs | Ops mirror of Legacy AM; new Ops handler logic |
| Bin Asset state transitions | New Asset-status discipline (Filled → Inward / Available) |
| `move_to_cut_bit_warehouse` flag visibility UX | Operator must see consequence before submit |

## Migration stance

Hard replacement for new BBIE submissions. Pre-Console BBIE submissions on legacy stay on legacy.

## What Hermes workers can change without architecture review

| Change | Risk |
|---|---|
| Add new field to Console BBIE | Low |
| Add new validation in controller | Low |
| Modify Bridge populate function for additional fields | Low |
| Extend Ops handler with metadata | Low |

## What Hermes workers must escalate

| Change | Why |
|---|---|
| Add a third path option (e.g. scrap) | Cross-layer coordination |
| Touch the 5-step pattern | Saga regression |
| Change cut-bit batch convention | Cross-program invariant |
| Modify Asset state taxonomy | Cross-motion impact |
| Remove `run_legacy_sync=False` | Duplicate Legacy submissions |

## Reviewer worker checklist

When BBIE finally ships and changes are PR'd:

- [ ] Unit tests for both paths pass
- [ ] Bridge populate function tested for both branches
- [ ] Ops handler tested with `run_legacy_sync=False`
- [ ] Concurrency test on `apply_bridge_result`
- [ ] Bin state transition test (Filled → Inward; Filled → Available)
- [ ] Cut-bit batch auto-creation tested
- [ ] One staging end-to-end submission per path
