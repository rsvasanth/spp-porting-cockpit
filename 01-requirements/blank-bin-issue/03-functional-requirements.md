# Functional Requirements

| ID | Requirement | Why |
| --- | --- | --- |
| FR-BBI-001 | The system shall provide a Blank Bin Issue submission flow. | BBI is its own process. |
| FR-BBI-002 | The operator shall scan a production Lot/Job Card barcode. | Job Card is the planning identity. |
| FR-BBI-003 | Lot scan shall resolve `Job Card` by `batch_code` and operation `Moulding`. | Legacy behavior. |
| FR-BBI-004 | Lot scan shall require Job Card status `Work In Progress`. | Prevents issue to wrong job state. |
| FR-BBI-005 | The system shall populate production item, target qty, press, mould, and Job Card. | Operator needs confirmation. |
| FR-BBI-006 | The operator shall scan a bin barcode. | Physical material identity. |
| FR-BBI-007 | Bin scan shall resolve active `Item Bin Mapping` through Asset barcode. | Bin contents must exist. |
| FR-BBI-008 | Bin scan shall reject retired/empty bin mappings. | No material available. |
| FR-BBI-009 | Bin scan shall require Asset bin weight. | Issue row stores bin weight. |
| FR-BBI-010 | Bin scan shall validate Asset location equals SPP Settings `to_location`. | Bin must be at moulding location. |
| FR-BBI-011 | Bin's `mat` shall match scanned Job Card production item. | Legacy direct item check. |
| FR-BBI-012 | Bin compound shall match a compound item in the production item's active BOM. | Prevents wrong compound issue. |
| FR-BBI-013 | Submission shall require `scan_production_lot`. | Legacy validation. |
| FR-BBI-014 | Submission shall require `scan_bin`. | Legacy validation. |
| FR-BBI-015 | Submission shall create at least one child issue row. | Legacy on_submit guard. |
| FR-BBI-016 | Issue child row shall carry `is_completed`, defaulting to incomplete until MPE consumption. | MPE contract. |
| FR-BBI-017 | BBI shall not create Stock Entry or Asset Movement. | It is logical assignment. |
| FR-BBI-018 | BBI shall remain separate from BDE and BBIE requirements. | Refactor alignment. |

## Required Operator Feedback

| Event | Required feedback |
| --- | --- |
| Job Card missing | Show Lot not found |
| Job Card not WIP | Show current status |
| Bin wrong location | Show expected location |
| Bin item mismatch | Show bin item and job item |
| BOM compound mismatch | Show bin compound mismatch |
