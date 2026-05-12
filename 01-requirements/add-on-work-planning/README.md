# Add On Work Planning Requirements

## Status

| Field | Value |
| --- | --- |
| Requirement pack | Add On Work Planning |
| Legacy DocType | `Add On Work Planning` |
| Console process target | `ADD_ON_WORK_PLANNING` |
| Legacy source | `shree_polymer_custom_app/.../doctype/add_on_work_planning/` |
| Business outcome | Create supplemental planning records beyond the official shift Work Planning |
| Last updated | 2026-05-12 |

## Story

Add On Work Planning is not the base shift plan. It is supplemental production planning. Legacy keeps a separate DocType, separate naming series, separate child table, and does not enforce the one-per-shift uniqueness check that Work Planning enforces.

This process can still create Work Orders and Job Cards, but its business meaning is different: it adds work beyond the main shift plan.

## Counts

| Type | Count |
| --- | ---: |
| Functional requirements | 24 |
| Non-functional requirements | 15 |
| Business rules | 14 |
| Acceptance criteria | 8 |
| Out-of-scope items | 10 |
| Drift findings | 5 |

## Critical Legacy Facts

| Fact | Source |
| --- | --- |
| Uses naming series `ADWRKP-.#####` | Add On schema |
| Uses child table `Add On Work Plan Item` | Add On schema |
| Requires shift fields but does not call shift uniqueness validation | Add On `validate` |
| Creates Work Orders / Job Cards like Work Planning | `on_submit_value`, `create_work_order` |
| Job Card child reference is written to `Add On Work Plan Item` | `update_job_cards` |
| Cancellation blocked by downstream BBI/MPE | `on_cancel` |
