# Business Rules

| ID | Rule | Implication |
| --- | --- | --- |
| BR-WPL-001 | Work Planning is the official base production plan for a shift. | Add On cannot replace it. |
| BR-WPL-002 | Only one submitted Work Planning is allowed per date + shift series. | Duplicate shift plans must be blocked. |
| BR-WPL-003 | A Work Planning document may contain multiple products. | Multiple item rows are expected. |
| BR-WPL-004 | Every planned item must have target quantity for the selected shift time. | Work Order quantity comes from target master data. |
| BR-WPL-005 | Missing target quantity is a hard stop. | Operators must maintain `Work Plan Item Target`. |
| BR-WPL-006 | Every planned item must resolve to an active/default or selected BOM. | Work Order creation depends on BOM. |
| BR-WPL-007 | Duplicate press/workstation within one Work Planning is not allowed. | One press should not be planned twice in the same shift plan. |
| BR-WPL-008 | Duplicate mould within one Work Planning is not allowed. | One mould should not be double-assigned in the same shift plan. |
| BR-WPL-009 | Work Planning creates downstream Work Orders and Job Cards after submission. | It is both a plan and a source for production execution records. |
| BR-WPL-010 | Job Card Lot # is the downstream production identity. | BBI, Inspection, and MPE depend on it. |
| BR-WPL-011 | Work Planning cannot be cancelled after downstream BBI exists. | Material issue against the plan has begun. |
| BR-WPL-012 | Work Planning cannot be cancelled after downstream MPE exists. | Production has begun/completed. |
| BR-WPL-013 | If allowed cancellation happens, linked WO/JC/serial records must be cleaned. | Prevents stale executable records. |
| BR-WPL-014 | Work Planning and Add On Work Planning are separate process identities. | Console must not hide base/add-on difference behind one ambiguous form. |
| BR-WPL-015 | Mould lookup should respect active/spare/dev mould status. | Legacy Work Planning applies this stricter filter. |
| BR-WPL-016 | A Console redesign may improve the UX, but must preserve the shift uniqueness invariant. | Core business rule survives implementation rewrite. |

## Legacy-Derived Identity Rule

| Identity | Legacy field / behavior |
| --- | --- |
| Base plan document | `Work Planning` with series `WRKP-.#####` |
| Child rows | `Work Plan Item` |
| Shift uniqueness key | `date + shift_series` |
| Downstream lot | Job Card `batch_code` generated from date + shift series + serial |
| Downstream guard | Submitted `Blank Bin Issue` / `Moulding Production Entry` block cancel |
