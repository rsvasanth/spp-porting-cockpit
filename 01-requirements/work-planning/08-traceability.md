# Traceability

## Legacy Source Map

| Area | Source |
| --- | --- |
| Controller | `shree_polymer_custom_app/.../doctype/work_planning/work_planning.py` |
| Schema | `shree_polymer_custom_app/.../doctype/work_planning/work_planning.json` |
| Client behavior | `shree_polymer_custom_app/.../doctype/work_planning/work_planning.js` |
| Child table | `doctype/work_plan_item/work_plan_item.json` |
| Target master | `doctype/work_plan_item_target/work_plan_item_target.json` |

## Requirement Mapping

| Requirement IDs | Legacy evidence |
| --- | --- |
| FR-WPL-001 to FR-WPL-010 | Work Planning schema and client row behavior |
| FR-WPL-011 to FR-WPL-018 | `validate`, target quantity query, `validate_shift_mould` |
| FR-WPL-019 to FR-WPL-023 | `on_submit_value`, `create_work_order`, `update_job_cards` |
| FR-WPL-024 to FR-WPL-026 | `on_cancel`, `delete_serial_no` |
| FR-WPL-027 to FR-WPL-028 | Requirement correction from Legacy comparison |
| BR-WPL-001 to BR-WPL-016 | Legacy business behavior extracted from controller and client |

## Drift Findings

| ID | Drift | Impact | Required correction |
| --- | --- | --- | --- |
| DRIFT-WPL-001 | Existing cockpit requirements collapsed Work Planning into Add On Work Planning. | Base one-per-shift rule was hidden. | Keep separate `work-planning` requirements. |
| DRIFT-WPL-002 | Existing Add On spec says `planning_type` can discriminate Original/Add On. | This does not preserve Legacy separate DocType behavior cleanly. | Require separate process identity unless explicitly redesigned. |
| DRIFT-WPL-003 | No current `02-specifications/work-planning/` folder exists. | Spec layer is missing for base plan. | Create Work Planning spec from Legacy code. |
| DRIFT-WPL-004 | Add On spec is forward-looking while Work Planning legacy is real code. | Requirements must not treat planned Add On as source of truth for Work Planning. | Use Legacy Work Planning code as authority. |
| DRIFT-WPL-005 | Console/Ops implementation status for Work Planning is unclear. | Requirement vs code alignment cannot be proven. | Mark implementation as not verified until code review. |
| DRIFT-WPL-006 | Legacy cancellation deletes submitted WO/JC records via direct DB operations. | This is risky but existing behavior. | Console should preserve business guard while improving technical safety. |

## Current Alignment Assessment

| Layer | Status |
| --- | --- |
| Requirement vs Legacy | Aligned from direct code read |
| Requirement vs current spec | Missing dedicated Work Planning spec |
| Requirement vs Console code | Not verified |
| Requirement vs Add On plan | Intentionally separated |
