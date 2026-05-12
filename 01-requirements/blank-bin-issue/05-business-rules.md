# Business Rules

| ID | Rule | Rationale |
| --- | --- | --- |
| BR-BBI-001 | BBI assigns a bin to a Job Card; it does not move or consume stock. | Logical reservation only. |
| BR-BBI-002 | Lot scan must find a Moulding Job Card. | BBI is moulding-input preparation. |
| BR-BBI-003 | Job Card must be `Work In Progress`. | Legacy rejects other states. |
| BR-BBI-004 | Bin must be in SPP Settings `to_location`. | It must physically be at moulding location. |
| BR-BBI-005 | Bin `mat` must match production item. | Direct legacy validation. |
| BR-BBI-006 | Bin compound must match active BOM compound. | Quality and production correctness. |
| BR-BBI-007 | Scan production lot and scan bin are mandatory. | Schema and validation. |
| BR-BBI-008 | Child issue row mirrors parent fields. | Legacy validate rebuilds child row. |
| BR-BBI-009 | `is_completed=0` means still available for MPE consumption. | Site has 287 open issue items. |
| BR-BBI-010 | MPE is the authority that completes/consumes issue rows. | Site has 67719 completed issue items. |
| BR-BBI-011 | BBI remains its own requirement identity. | Distinct planning/material contract. |

## Site Evidence

`spp15.local` has 68078 BBI records. This is one of the highest-volume legacy flows and deserves its own process-specific requirement pack.
