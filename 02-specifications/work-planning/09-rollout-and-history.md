# 09 — Rollout and history

## Why this spec exists

The earlier cockpit planning spec documented only `add-on-work-planning` and claimed Console could collapse Legacy `Work Planning` and `Add On Work Planning` with a `planning_type` discriminator. The production overseer corrected this on 2026-05-12: production planning starts with Work Planning, and only one Work Planning is allowed for a shift.

## Correction made

| Correction | Status |
| --- | --- |
| Create dedicated Work Planning spec | Done |
| Keep Add On Work Planning separate | Done |
| Mark old collapsed assumption as drift | Done |
| Requirements split into `work-planning` and `add-on-work-planning` | Done |

## Migration concern

If Console had implemented only `Console Add On Work Planning`, migration must decide whether to:

| Option | Risk |
| --- | --- |
| Add separate `Console Work Planning` | More schema work, preserves business rule |
| Keep one doctype with discriminator | Must still enforce separate uniqueness and child-table semantics; risk of operator confusion |

The recommended cockpit position is separate process identity.

## Rollout checks

1. Confirm no current Console UI hides Work Planning behind Add On.
2. Confirm Legacy Work Planning data is migrated or referenced correctly.
3. Confirm downstream BBI/MPE can resolve Lot # from both Work Planning and Add On Job Cards.
4. Confirm duplicate-shift block applies only to Work Planning.
