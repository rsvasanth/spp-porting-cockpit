# 03 — Console backend target

## Current status

No verified Console Work Planning process was found in the cockpit specs. Existing Add On Work Planning spec had incorrectly proposed collapsing Work Planning into Add On with `planning_type`. This spec treats Work Planning as its own required Console process.

## Target process code

| Field | Value |
| --- | --- |
| Process code | `WORK_PLANNING` |
| Local parent | `Console Work Planning` |
| Local child | `Console Work Plan Item` |
| Legacy target | `Work Planning` |
| Ops target | Work Order + Job Card equivalents |

## Required local fields

| Field | Source / purpose |
| --- | --- |
| `reference_id` | Cross-system transaction spine |
| `date` | Planning date |
| `shift_type` | Shift label |
| `shift_series` | Shift uniqueness + Lot # generation |
| `shift_time` | Target quantity lookup |
| `scan_supervisor` | Operator scan |
| `supervisor_id` | Employee link |
| `supervisor_name` | Display/audit |
| `job_card_wo` | Whether WO/JC has been created |

## Required child fields

| Field | Purpose |
| --- | --- |
| `item` | Planned product |
| `work_station` | Press/workstation |
| `mould` | Mould asset |
| `bom` | BOM to use |
| `job_card` | Generated Job Card |
| `lot_number` | Generated Job Card batch code |

## Required validations

| Validation | Legacy source |
| --- | --- |
| Required `shift_series` | `validate()` |
| Required `shift_time` | `validate()` |
| At least one item row | `validate()` |
| Target quantity exists for item + shift time | `validate()` query on `Work Plan Item Target` |
| One submitted Work Planning per date + shift series | `validate_shift_mould()` |
| Active/default BOM exists | `validate_bom()` |
| Supervisor exists and designation mapped | `validate_supervisor()` |

## Required orchestration

Console should follow the cockpit local-first pattern:

1. Validate source fields and child rows.
2. Create local `Console Work Planning` and child rows.
3. Start transaction log legs.
4. Sync Legacy `Work Planning`.
5. Sync Ops Work Order / Job Card equivalents.
6. Apply callbacks with the standard race-safe pattern.

## Drift to close

| Drift | Required correction |
| --- | --- |
| No dedicated Work Planning spec existed | This folder closes spec gap |
| Add On spec collapse assumption | Do not reuse for Work Planning |
| Console implementation unknown | Mark as not verified until code review |
