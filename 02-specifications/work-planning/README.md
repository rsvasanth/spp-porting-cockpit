# Work Planning — Specification

**Status:** Legacy-shipped, Console/Ops port not verified.
**Legacy DocType:** `Work Planning` (`WRKP-.#####`)
**Legacy controller:** `shree_polymer_custom_app/.../doctype/work_planning/work_planning.py`
**Requirement pack:** [`../../01-requirements/work-planning/`](../../01-requirements/work-planning/)

## What this process produces

Work Planning creates the official shift production plan. One submitted Work Planning is allowed for a given `date + shift_series`. After submission, the legacy form exposes a "Create Work Order/Job Card" action that creates native ERPNext Work Orders and Job Cards. The generated Job Card `batch_code` is the Lot # used downstream by Blank Bin Issue, Inspection Entry, and Moulding Production Entry.

## Key facts

| Fact | Detail |
| --- | --- |
| Official shift plan | Yes |
| Duplicate shift block | Enforced for submitted `date + shift_series` |
| Multiple products | Yes, via `Work Plan Item` child rows |
| Child table | `Work Plan Item` |
| Target master | `Work Plan Item Target` by item + shift time |
| Work Order creation | Legacy helper after submit |
| Job Card creation | Native ERPNext Job Card generated from Work Order |
| Lot # source | Job Card `batch_code`, generated from date + shift series + serial |
| Cancellation guard | Blocks if downstream BBI or MPE exists |

## Files

| File | Purpose |
| --- | --- |
| [01-business-context.md](01-business-context.md) | Shop-floor role and business meaning |
| [02-frontend-dash.md](02-frontend-dash.md) | Legacy Desk UX and Console target implications |
| [03-console-backend.md](03-console-backend.md) | Console target shape and current gap |
| [04-bridge-layer.md](04-bridge-layer.md) | Bridge target requirements and mapping |
| [05-legacy-erpnext.md](05-legacy-erpnext.md) | Legacy DocType/controller behavior |
| [06-ops-erpnext.md](06-ops-erpnext.md) | Ops target expectations |
| [07-end-to-end-flow.md](07-end-to-end-flow.md) | End-to-end trace |
| [08-test-plan.md](08-test-plan.md) | Test scenarios |
| [09-rollout-and-history.md](09-rollout-and-history.md) | Correction history |
| [10-risks-and-decisions.md](10-risks-and-decisions.md) | Drift and decisions |

## Critical correction

Do not collapse Work Planning into Add On Work Planning. The legacy code proves the business difference: Work Planning calls `validate_shift_mould()` and blocks duplicate submitted plans for a shift; Add On Work Planning has the same method but does not call it.
