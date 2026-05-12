# Business Rules

| ID | Rule | Implication |
| --- | --- | --- |
| BR-AWP-001 | Add On Work Planning is supplemental to Work Planning. | It must not replace the base shift plan. |
| BR-AWP-002 | Add On Work Planning does not enforce one submitted document per shift by default. | Multiple add-ons may exist for the same date + shift series. |
| BR-AWP-003 | Add On may contain multiple item rows. | Extra work can include multiple products. |
| BR-AWP-004 | Every item must have target quantity for selected shift time. | Quantity calculation depends on target master. |
| BR-AWP-005 | Missing target quantity is a hard stop. | Master data must be maintained. |
| BR-AWP-006 | Every item must resolve to an active/default or selected BOM. | Work Order needs BOM. |
| BR-AWP-007 | Duplicate press/workstation within one Add On document is not allowed. | Avoids duplicate row assignments. |
| BR-AWP-008 | Duplicate mould within one Add On document is not allowed. | Avoids duplicate mould assignment. |
| BR-AWP-009 | Add On creates Work Orders and Job Cards after submission. | Supplemental plan becomes executable. |
| BR-AWP-010 | Job Card Lot # is the downstream identity. | BBI/Inspection/MPE rely on it. |
| BR-AWP-011 | Add On cannot be cancelled after downstream BBI exists. | Material issue has started. |
| BR-AWP-012 | Add On cannot be cancelled after downstream MPE exists. | Production has started/completed. |
| BR-AWP-013 | Work Planning and Add On Work Planning are separate process identities. | Console should not hide both behind one ambiguous process. |
| BR-AWP-014 | If Add On is linked to a base Work Planning in future, that link must be explicit. | Prevents unclear supplemental context. |

## Legacy-Derived Identity Rule

| Identity | Legacy field / behavior |
| --- | --- |
| Add-on document | `Add On Work Planning` with series `ADWRKP-.#####` |
| Child rows | `Add On Work Plan Item` |
| Shift uniqueness | Not enforced because call is commented out |
| Downstream lot | Job Card `batch_code` |
| Downstream guard | Submitted BBI/MPE block cancel |
