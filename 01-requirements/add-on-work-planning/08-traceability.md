# Traceability

## Legacy Source Map

| Area | Source |
| --- | --- |
| Controller | `shree_polymer_custom_app/.../doctype/add_on_work_planning/add_on_work_planning.py` |
| Schema | `shree_polymer_custom_app/.../doctype/add_on_work_planning/add_on_work_planning.json` |
| Client behavior | `shree_polymer_custom_app/.../doctype/add_on_work_planning/add_on_work_planning.js` |
| Child table | `doctype/add_on_work_plan_item/add_on_work_plan_item.json` |
| Target master | `doctype/work_plan_item_target/work_plan_item_target.json` |

## Requirement Mapping

| Requirement IDs | Legacy evidence |
| --- | --- |
| FR-AWP-001 to FR-AWP-009 | Add On schema and `validate` |
| FR-AWP-010 to FR-AWP-018 | Target/BOM validation and client row behavior |
| FR-AWP-019 to FR-AWP-021 | `on_submit_value`, `create_work_order`, `update_job_cards` |
| FR-AWP-022 to FR-AWP-024 | `on_cancel` and process identity correction |
| BR-AWP-001 to BR-AWP-014 | Legacy behavior compared against Work Planning |

## Drift Findings

| ID | Drift | Impact | Required correction |
| --- | --- | --- | --- |
| DRIFT-AWP-001 | Existing cockpit requirements collapse Work Planning and Add On. | Add On semantics become confused with base plan. | Keep separate Add On pack. |
| DRIFT-AWP-002 | Existing Add On spec claims it can route both `Add On` and `Original`. | Risks hiding Legacy's one-shift Work Planning rule. | Remove "collapsed" assumption or mark as redesign requiring approval. |
| DRIFT-AWP-003 | Add On Legacy has shift uniqueness function but does not call it. | This is intentional supplemental behavior. | Do not enforce Work Planning duplicate block on Add On by default. |
| DRIFT-AWP-004 | Add On mould lookup is looser than Work Planning. | Behavior differs despite similar screens. | Document and decide whether Console should tighten it. |
| DRIFT-AWP-005 | Console/Ops implementation status for Add On is planned/unclear. | Requirement vs code alignment needs later code check. | Mark implementation not verified. |

## Current Alignment Assessment

| Layer | Status |
| --- | --- |
| Requirement vs Legacy | Aligned from direct code read |
| Requirement vs current Add On spec | Partially aligned; collapse assumption is wrong |
| Requirement vs Console code | Not verified |
| Requirement vs Work Planning | Intentionally separate |
