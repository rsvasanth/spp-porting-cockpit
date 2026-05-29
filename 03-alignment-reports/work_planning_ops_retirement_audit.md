# Work Planning — Ops Retirement Parity Audit

**Date:** 2026-05-29
**Status:** ❌ Cannot retire Ops doctype yet — Console parity is incomplete.
**Tracked in:** Task #12 (Retire Ops Work Planning + Add-On Work Planning doctypes)
**Companion to:** [`alignment_report_work_planning.md`](alignment_report_work_planning.md) (sync-side gaps)

## 1. Why this audit exists

`shree_polymer_ops/doctype/work_planning/work_planning.py` (396 lines) and `add_on_work_planning/add_on_work_planning.py` (372 lines) hold transactional business logic on the Ops side. Per the two-purpose framework, transactional process records and their validation are a Console concern; Ops should own only masters and native ERPNext transaction execution. These two doctypes are legacy artifacts from 2023 that predate Console.

## 2. Rule-by-rule comparison

| # | Rule on Ops `WorkPlanning.validate()` | Console `ConsoleWorkPlanning` | Status |
|---|---|---|---|
| 1 | `shift_series` must be present | ❌ No `validate()` on Console controller | Missing |
| 2 | `shift_time` must be present | ❌ Same | Missing |
| 3 | **Target qty lookup**: every item must have a non-zero `Work Plan Item Target` row for the active shift; throw with item list if any missing | ❌ Not implemented Console-side | **Core gap** |
| 4 | Duplicate-shift-mould check: no other submitted WP exists with same date + shift_series | ❌ Not implemented Console-side | Missing |
| 5 | At least one item row required | ⚠ Probably enforced by Dash UI but not controller | Partial |
| 6 | `validate_amended` — reset `job_card_wo` flag on amendments | ❌ N/A — amend flow lives Ops-side | N/A |
| 7 | `on_submit_value`: validate BOM, create Work Order, set `job_card_wo` flag | Handled via Console Process Template `WORK_PLANNING` → Ops engine creates WO + JC | ✅ Different mechanism, same outcome |
| 8 | `on_cancel`: check Blank Bin Issue + Moulding Production Entry references before allowing cancel | ❌ Not implemented Console-side | Missing — cancel-safety lost |

**Score: 1 of 8 fully covered.** 7 rules either missing or partially covered Console-side.

## 3. What's already correct on Console

| Aspect | Status |
|---|---|
| Process Template `WORK_PLANNING` declares `create_doc Work Order → get_doc Job Card → update_doc Job Card → call_method Legacy Sync Mapping` | ✅ |
| `Console Work Planning.apply_bridge_result` 4-step (Steps 1-4, no Step 5 auto-submit) | ✅ (Step 5 minor polish needed) |
| `legacy_doctype_map["WORK_PLANNING"]` registered | ✅ |
| Callback routes correctly after submit | ✅ |
| Bridge sync mirrors WP to legacy site | ✅ (assumed; not re-verified) |

## 4. What must be built before retirement

In priority order:

1. **`Console Work Planning.validate()` — implement rules 1, 2, 3, 4, 5, 8.**
   - Rule 3 is the largest piece. With the now-fixed `Work Plan Item Target.shift_type` being a Link, the query simplifies — no more `OR shift_type = self.shift_time` workaround:
     ```python
     items = [r.item for r in self.items]
     covered = frappe.db.sql_list(
         """SELECT item FROM `tabConsole Work Plan Item Target`
            WHERE item IN %(items)s
              AND shift_type = %(st)s
              AND target_qty > 0""",
         {"items": tuple(items), "st": self.shift_type},
     )
     missing = [i for i in items if i not in covered]
     if missing:
         frappe.throw(f"Target qty missing for: {', '.join(missing)}")
     ```
   - Rule 4: `exists()` on `Console Work Planning` with date + shift_series.
   - Rule 8: reads on `Console Blank Bin Issue` + `Console Moulding Production Entry`.
2. **Sync `Work Plan Item Target` master into Console.** Master sync surface already exposes it via `get_work_plan_item_targets`; Console needs a `Console Work Plan Item Target` mirror doctype + handler in `sync_handler.py` to populate it. Then rule 3's query targets the Console mirror.
3. **Add Step 5 (auto-submit) to `Console Work Planning.apply_bridge_result`** — matches MBM canon.
4. **Test pass:** confirm Console-side validation rejects the same cases the Ops controller does.

## 5. Retirement path once parity reaches 100%

| Step | What happens | Risk |
|---|---|---|
| 1. Parity audit ✅ | (this file) | None |
| 2. Build missing Console rules (Section 4) | Console controller starts enforcing the same constraints Ops did | Low — new code, fail-fast in dev |
| 3. **Lock Ops `WorkPlanning` permissions** to System Manager only via Property Setter | No operator can create WP directly via Ops Desk | Low — blocks parallel path |
| 4. **Patch: reject new inserts** unless `flags.from_console_template = True` | Even sysadmin Desk inserts fail | Medium — must confirm Console flow sets the flag |
| 5. Monitor for N weeks | Confirm no Ops-side creates | None — observational |
| 6. **Archive + delete** | Export remaining historical WP rows; drop doctype + controller + child tables; remove from hooks | Medium — data archival decision |

Same plan applies to `Add-On Work Planning`.

## 6. Critical sequencing rule

Do NOT delete the Ops doctype until step 2 is complete. The Ops `validate()` is currently the **only safety net for rule 3 (target-qty enforcement)**. Removing it before Console enforces the rule allows operators to submit Work Planning without target-qty config and silently produce broken Work Orders.

## 7. WPIT schema fix prerequisite — already shipped

[`fix/work-plan-item-target-shift-link`](https://github.com/iyyanarr/shree_polymer_ops/pull/new/fix/work-plan-item-target-shift-link). Migrates legacy `08:00:00`-style values to real Shift Type names. Once merged, the rule 3 port becomes a clean `WHERE shift_type = X`. Already deployed to staging per 2026-05-29 user confirmation.
