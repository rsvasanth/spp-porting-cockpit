# Non-Functional Requirements

| ID | Requirement | Why |
| --- | --- | --- |
| NFR-BBI-001 | Lot and bin scan feedback should return within 2 seconds under normal load. | Moulding floor speed. |
| NFR-BBI-002 | BBI must be traceable by Job Card, Lot, bin, compound, and batch. | MPE and audit. |
| NFR-BBI-003 | BBI must not mutate stock ledger. | It is logical assignment. |
| NFR-BBI-004 | BBI must prevent issue to non-WIP Job Cards. | Production state integrity. |
| NFR-BBI-005 | BBI must prevent wrong-location bins. | Physical bin availability. |
| NFR-BBI-006 | BBI must prevent BOM-incompatible compounds. | Product quality. |
| NFR-BBI-007 | `is_completed` transition must be reserved for MPE. | Consumption authority. |
| NFR-BBI-008 | Open issue item queries must stay fast. | MPE depends on them. |
| NFR-BBI-009 | Error messages must be operator-actionable. | Shop-floor usability. |
| NFR-BBI-010 | Spec gap must be visible until `02-specifications/blank-bin-issue/` is written. | Refactor safety. |
| NFR-BBI-011 | Requirement/spec/code must stay process-scoped. | Refactor alignment. |
