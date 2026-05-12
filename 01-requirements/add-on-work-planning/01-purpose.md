# Purpose

## Business Purpose

Add On Work Planning records supplemental production work that is added beyond the official Work Planning shift plan. It uses similar item, mould, press, BOM, Work Order, and Job Card mechanics, but it intentionally does not enforce one plan per shift.

## Position In Chain

| Upstream | Add On Work Planning | Downstream |
| --- | --- | --- |
| Base shift Work Planning, supervisor decision, extra demand | Supplemental plan | Additional Job Cards, BBI, Inspection, MPE |

## Difference From Work Planning

| Work Planning | Add On Work Planning |
| --- | --- |
| Official base shift plan | Extra/supplemental plan |
| One per date + shift series | Additional records allowed |
| `WRKP-.#####` | `ADWRKP-.#####` |
| `Work Plan Item` | `Add On Work Plan Item` |

## Scope Boundary

Add On Work Planning should not be used to hide or replace the base shift planning rule. It may produce additional executable Job Cards, but only as add-on work.
