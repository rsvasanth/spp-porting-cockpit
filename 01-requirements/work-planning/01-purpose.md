# Purpose

## Business Purpose

Work Planning defines the official production plan for a shift. The supervisor decides what products will be produced, on which press/workstation, using which mould, and under which shift. The submitted plan creates the Work Orders and Job Cards that downstream Blank Bin Issue, Inspection Entry, and Moulding Production Entry depend on.

## Process Position

| Upstream | Work Planning | Downstream |
| --- | --- | --- |
| Available blank bins, mould/master data, shift target data | One official shift plan | Job Cards, Blank Bin Issue, Inspection Entry, Moulding Production Entry |

## Why It Is Separate From Add On

| Work Planning | Add On Work Planning |
| --- | --- |
| Base plan for the shift | Additional/supplemental plan |
| One submitted plan per date + shift series | Multiple supplemental plans may be allowed |
| Uses `Work Plan Item` child table | Uses `Add On Work Plan Item` child table |
| Enforces shift uniqueness in Legacy | Shift uniqueness check is commented out in Legacy Add On |

## Outcome

| Outcome | Description |
| --- | --- |
| Shift is planned once | System blocks duplicate submitted Work Planning for same date + shift series |
| Multiple products can be planned | Child rows hold item, workstation, mould, BOM, Job Card, Lot # |
| Work Orders and Job Cards are created | One Work Order/Job Card path per item row |
| Lot # becomes downstream identity | Job Card `batch_code` and barcode text become the production lot |

## Scope Boundary

Work Planning owns the official shift production plan. It does not own supplemental Add On planning, actual moulding production entry, inspection result capture, or blank bin movement.
