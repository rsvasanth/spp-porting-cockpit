# 05 — Legacy ERPNext (v15) — planned

## Legacy doctype

`Add On Work Planning` — custom legacy doctype.

Fields the Bridge writes:
- `reference_id` / `referenceid` (legacy dual)
- `date`, `shift_type`, `supervisor_id`
- `lot_number` (Console-authored, honored as-is)
- Child table `items` (Add On Work Plan Item) — one row per (item × workstation × target_qty)

## Legacy controller behavior (planned modifications)

```python
class AddOnWorkPlanning(Document):
    def before_insert(self):
        # ── Wave 3 modification: honor Console-provided lot_number ──
        if not self.lot_number:
            self.lot_number = self._generate_legacy_lot_number()
        # else: Console authored it; use as-is

    def validate(self):
        # Standard validation
        ...
        # Validate against Work Plan Item Target if configured
        # (this is operational, not strict block — Console Dash already soft-warned)

    def on_submit(self):
        # Bridge calls create_planning_with_jobcards as a separate whitelisted call.
        # Standard on_submit DOESN'T create Work Order — that happens via Bridge's
        # explicit call. Keeps the legacy controller simpler.
        pass
```

## `create_planning_with_jobcards` whitelisted method

See [04-bridge-layer.md](04-bridge-layer.md) for the full method body. Key behaviors:

| Behavior | Detail |
|---|---|
| Work Order creation | One WO per AOWP submission; production_item = first row's item (TBD if multi-item single WO is valid) |
| Job Card creation | One per AOWP item row; workstation override applied here |
| Atomic rollback | Frappe transaction; any failure rolls back all |
| AOWP child row backreference | Each `Add On Work Plan Item.job_card` filled with the created JC name |

## Workstation override (Mixing Operation master data)

When `Mixing Operation` master data row exists for the `(source_warehouse, operation)` pair, the Legacy method uses the master-data workstation regardless of payload value. The override is silent on Legacy; Console Dash should surface it pre-submit as an Add On Work Planning requirement.

## Documents created on Legacy per AOWP submission

| Document | Created by |
|---|---|
| `Add On Work Planning` | Bridge insert + submit |
| `Work Order` (one per AOWP) | `create_planning_with_jobcards` |
| `Job Card` (one per item row) | `create_planning_with_jobcards` |
| `Add On Work Plan Item` child rows | Bridge child-table mapping |

## Downstream legacy consumers

| Consumer | Reads from AOWP |
|---|---|
| Blank Bin Issue | Scans Lot # → joins to `Add On Work Plan Item.lot_number` → fetches Job Card + BOM input compound |
| Inspection Entry (Wave 4) | References Lot # for type-uniqueness + later batch_no cascade |
| Moulding Production Entry (Wave 5) | References Lot # for full Job Card context + inspection prerequisite check |

## What Hermes workers must NOT touch

- Legacy `Add On Work Planning` schema (cross-program; many reports)
- `create_planning_with_jobcards` without atomic-rollback test passing
- Mixing Operation master data sync (Legacy admin domain)
- Workstation override logic (cross-program invariant)
