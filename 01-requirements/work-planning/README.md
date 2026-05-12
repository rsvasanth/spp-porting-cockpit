# Work Planning Requirements

## Status

| Field | Value |
| --- | --- |
| Requirement pack | Work Planning |
| Legacy DocType | `Work Planning` |
| Console process target | `WORK_PLANNING` |
| Legacy source | `shree_polymer_custom_app/.../doctype/work_planning/` |
| Business outcome | Create the official one-per-shift production plan and downstream Work Orders / Job Cards |
| Last updated | 2026-05-12 |

## Story

Work Planning is the base production planning document for a shift. It is linked to a shift and may contain multiple products, moulds, and presses to be produced in that shift. Legacy enforces one submitted Work Planning per date and shift series. This makes Work Planning the official shift plan, not just another planning variant.

Add On Work Planning is related, but separate. Add On is for supplemental planning and does not enforce the one-plan-per-shift rule. Console requirements must preserve that business difference.

## Files

| File | Purpose |
| --- | --- |
| `01-purpose.md` | Purpose, boundaries, and process position |
| `02-actors-and-roles.md` | Actors and accountability |
| `03-functional-requirements.md` | Functional requirements |
| `04-non-functional-requirements.md` | Quality and reliability requirements |
| `05-business-rules.md` | Load-bearing business rules |
| `06-acceptance-criteria.md` | UAT criteria |
| `07-out-of-scope.md` | Exclusions |
| `08-traceability.md` | Legacy/spec/code traceability |

## Counts

| Type | Count |
| --- | ---: |
| Functional requirements | 28 |
| Non-functional requirements | 18 |
| Business rules | 16 |
| Acceptance criteria | 10 |
| Out-of-scope items | 12 |
| Drift findings | 6 |

## Critical Legacy Facts

| Fact | Source |
| --- | --- |
| Requires `shift_series` and `shift_time` | `work_planning.py::validate` |
| Enforces one submitted Work Planning per date + shift series | `validate_shift_mould` |
| Requires at least one item row | `validate` |
| Validates target quantity from `Work Plan Item Target` by item + shift time | `validate` |
| Creates Work Order and Job Card records after submit helper | `on_submit_value` / `create_work_order` |
| Generates Lot # / barcode on Job Card | `update_job_cards` |
| Blocks cancellation if downstream BBI or MPE exists | `on_cancel` |

## Refactor Handoff

Use this requirement pack with the Legacy `work_planning` DocType code. Do not satisfy Work Planning by reusing Add On Work Planning unless the one-per-shift invariant is preserved.
