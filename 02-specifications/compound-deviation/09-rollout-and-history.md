# 09 — Rollout and history — The Compound Deviation Saga

This file is the **canonical narrative** of how the Compound Deviation
flow shipped, what broke, and why the architecture looks the way it does.

## Timeline

### 2026-04-29 — Initial Wave 1 shipping window

- `Console Compound Deviation` doctype created
- `console_compound_deviation.py` controller written with **early version**
  of `apply_bridge_result` (2-step pattern: per-leg write + aggregate)
- `populate_compound_deviation_fields` written as **~200 lines of
  inline SE lookup + identity resolution** — separate from
  `populate_compound_inspection_fields`'s pipeline
- Dash component `CompoundDeviationEntry.tsx` deployed
- First production-staging submission lands successfully

### 2026-04-29 (evening) — First race observed

- Operator submits ~6 deviations in rapid succession from a single shift
- Some deviations show `sync_status=Partial` on Console even though both
  Ops and Legacy responded Success
- Diagnosis: Console doctype's in-memory state stale when second callback
  runs — overwrites the first callback's `sync_status=Success` with
  `Partial` (computed against stale `sync_status_*` fields)

### 2026-04-30 (morning) — Fix #1: re-read both legs from DB

Commit (not the final fix): added a re-read step after per-leg write,
aggregate computed against re-read state instead of in-memory `self`.

**Tested manually on staging:** worked for sequential callbacks.
**NOT tested under concurrent callbacks** — the test gate didn't yet exist.

### 2026-04-30 (midday) — Bridge SE lookup bug discovered

A deviation submission failed on Legacy with `MandatoryError: stock_id`.
Investigation:
- `populate_compound_deviation_fields` had its own SE lookup logic
- This logic looked at `compound_deviation_data.mix_barcode`
- But Console's most recent payload refactor moved identity to
  `compound_inspection_data.mix_barcode`
- Bridge couldn't find the SE → `stock_id` never set → legacy
  Compound Inspection's `validate()` threw

### 2026-04-30 (afternoon) — Fix #2: the helper refactor

Commit `1df2de8` (or similar identifier — verify via git log):
- Extracted shared helpers in `sync_api.py`:
  - `_resolve_compound_identity`
  - `_lookup_legacy_stock_entry` (with the 6-strategy chain)
  - `_apply_compound_identity_to_doc` (idempotent)
  - `_apply_compound_readings_to_doc`
  - `_apply_compound_header_to_doc`
- `populate_compound_inspection_fields` rewritten as a thin orchestrator
  calling these helpers in sequence
- `populate_compound_deviation_fields` rewritten as a thin wrapper:
  same pipeline + `_apply_deviation_extras` for QM signoff
- ~200 lines of duplicated code eliminated
- The 6-strategy chain consolidates all the SE-finding logic into ONE
  place

**Tested manually:** worked for both Compound Inspection and Deviation.

### 2026-04-30 (late) — Concurrency race re-emerges

The helper refactor didn't address the Console controller's
`apply_bridge_result`. Multiple deviations submitted in a burst still
showed `Partial` despite both legs succeeding.

### 2026-04-30 (night) — Fix #3: the 5-step pattern

The `apply_bridge_result` controller method on **all six** affected
doctypes (Master Batch Mixing, Final Batch Mixing, Compound Deviation,
Sheeting Process, Cut Bit Transfer, Compound Inspection) was rewritten
to the current 5-step pattern:

1. Atomic per-leg `db.set_value`
2. Re-read both legs from DB
3. Aggregate `sync_status`
4. **Self-heal** — re-read final state; if both legs Synced but
   `sync_status != Success`, correct it
5. **Fresh-doc auto-submit** — `frappe.get_doc(name)` to avoid stale
   in-memory `docstatus`

This pattern was applied byte-identically across all 6 doctypes. The
self-heal step (#4) is what closes the **residual race** that Fix #1
left: two callbacks both compute aggregate against current DB state but
the slower one's step-3 might overwrite the faster one's `Success` with
`Partial` — step 4 catches and corrects.

### 2026-05-01 — Phase 1-4 deploy

The fully-fixed Compound Deviation + Compound Inspection unification
shipped together as "Phases 1-4" on `iyyanarr/develop`. Frappe Cloud
auto-deployed to `console.m.frappe.cloud`.

### 2026-05-01 (post-deploy) — The test gate rule established

User wrote down: **"No code goes out without all tests passing first."**
The saga had shown:
- Multiple sequential fixes shipped without test coverage
- Each fix introduced a new race
- Manual testing missed the concurrent-callback case
- Production-staging operators caught the bugs after each "fix"

The rule was added to `~/.claude/projects/-Users-alphaworkz-frappe-bench-apps-shree-polymer-console/memory/feedback_test_gate.md`.

### 2026-05-02 — Staging bug 1777721078171: `cavity_no` MandatoryError

A Compound Deviation submission failed on Legacy with
`MandatoryError: cavity_no`. Investigation:
- `cavity_no` was declared in Console Process Template + Bridge mapping
- But never wired through Console (no doctype field, no Dash UI)
- Payload didn't carry `cavity_no` → legacy CI's mandatory field unset → validate failed

**Mitigation:** added a fallback in `_apply_deviation_extras` to default
`cavity_no = 1` with a structured `frappe.log_error` log.

**Not yet fixed properly** — the wiring TODO remains. Reference in
`10-risks-and-decisions.md`.

### 2026-05-09 — Commit `a0fc0fc`: "rejected compound inspections not showing in Deviation screen"

Bug: Quality Managers couldn't find rejected Compound Inspections in
the Compound Deviation screen's source-CI dropdown. Cause: the search
endpoint was filtering by `Console Compound Inspection` only, missing
the new `Console Inspection` records (Phase 3 unification).

Fix: updated `get_rejected_compound_inspection` to query both legacy
and Phase 3 doctypes via union. Deployed same day.

### 2026-05-11 — Spec written (this file)

## Lessons from the saga (and how they shaped the cockpit)

| Lesson | Where encoded |
|---|---|
| Concurrent callbacks need DB-level state, not in-memory state | 5-step pattern (steps 2, 4) — byte-identical across 6 doctypes |
| Duplicated logic drifts | Bridge helper extraction (`_resolve_compound_identity` etc.) |
| Manual testing misses concurrency | Test gate rule established |
| Console payload shape changes break Bridge | `_pick` fallback pattern + idempotent helper writes |
| Mandatory fields can be quietly broken | `cavity_no` fallback + structured log |

## Current production status

Shipped to production-staging on `console.m.frappe.cloud`. All known
production races resolved by the 5-step pattern. One known wiring issue
remains (`cavity_no`) but is masked by the fallback.

## What Hermes workers can change without architecture review

| Change | Risk |
|---|---|
| Add a new `_pick` fallback path in `create_local_compound_deviation` | Low |
| Add a status type (e.g. `Conditional Accept`) to the dropdown — Console side | Medium — coordinate with legacy CI's Select field options |
| Tighten the `validate` reason check | Low — operator UX impact |
| Extend `_apply_deviation_extras` with a new field | Low — pattern is idempotent |

## What Hermes workers must escalate

| Change | Why |
|---|---|
| **Touch `apply_bridge_result` 5-step pattern on ANY of the 6 doctypes** | Saga regression risk; needs concurrency test + same change on all 6 in lockstep |
| Touch `_resolve_compound_identity`, `_lookup_legacy_stock_entry`, or `_apply_compound_identity_to_doc` | Shared with Compound Inspection; affects both flows |
| Remove a strategy from the 6-strategy SE lookup | Needs proof of zero hits in production logs (search `_strategy` field in `Legacy Bridge Log`) |
| Modify the factory-requirement skip for rejected CIs | Operations decision; needs production approval |
| Wire `cavity_no` through Console properly | Cross-layer change: doctype + Dash + payload + remove fallback |

## Reviewer worker checklist (when verifying a Compound Deviation change)

- [ ] All Compound Deviation unit tests pass (5 total)
- [ ] If touching `apply_bridge_result`: concurrency test + self-heal test added
- [ ] If touching shared helpers: Compound Inspection tests also pass
- [ ] If touching `populate_compound_deviation_fields`: verify `if not doc.get(field)` idempotency preserved
- [ ] One staging submission per status (Accepted, Rejected, Rework) successful
- [ ] `cavity_no` fallback log entries visible after staging submissions (proves the fallback fires)
- [ ] Obsidian note logged
- [ ] Graphify refreshed
