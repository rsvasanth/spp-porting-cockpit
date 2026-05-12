# Functional Requirements

| ID | Requirement | Why |
| --- | --- | --- |
| FR-AWP-001 | The system shall provide an Add On Work Planning submission flow. | Supplemental production needs separate capture. |
| FR-AWP-002 | Add On Work Planning shall require planning date. | Downstream lot generation uses date. |
| FR-AWP-003 | Add On Work Planning shall require shift type, shift series, and shift time. | Legacy validates shift fields. |
| FR-AWP-004 | Add On Work Planning shall require scanned supervisor identity. | Accountability is still required. |
| FR-AWP-005 | Add On Work Planning shall validate supervisor against mapped active employees. | Prevents unauthorized add-on planning. |
| FR-AWP-006 | Add On Work Planning shall support multiple item rows. | One supplemental plan can add multiple products. |
| FR-AWP-007 | Each row shall capture item, workstation/press, mould, BOM, Job Card, and Lot #. | Same downstream execution identity as base planning. |
| FR-AWP-008 | Add On shall not enforce one submitted plan per date + shift series by default. | Legacy intentionally comments out this check. |
| FR-AWP-009 | Add On shall reject submission with no item rows. | Legacy requires rows. |
| FR-AWP-010 | Add On shall validate target quantity from `Work Plan Item Target` by item + shift time. | Quantity calculation uses same target master. |
| FR-AWP-011 | Missing target quantity shall block submission. | Prevents bad Work Order quantity. |
| FR-AWP-012 | Add On shall validate active/default or selected BOM per item. | Work Order creation needs BOM. |
| FR-AWP-013 | Add On shall fetch and expose valid BOM choices. | Legacy frontend supports BOM selection. |
| FR-AWP-014 | Add On shall filter items by configured item group. | Legacy uses SPP Settings. |
| FR-AWP-015 | Add On shall filter workstations by configured list. | Legacy uses SPP Settings. |
| FR-AWP-016 | Add On shall support mould lookup by item. | Required for row creation. |
| FR-AWP-017 | Add On shall prevent duplicate workstation rows within the same add-on document. | Legacy UI blocks duplicate press in row set. |
| FR-AWP-018 | Add On shall prevent duplicate mould rows within the same add-on document. | Legacy UI blocks duplicate mould in row set. |
| FR-AWP-019 | Submitted Add On shall support Work Order / Job Card creation. | Add-on work must become executable. |
| FR-AWP-020 | Job Cards shall receive Lot #, barcode, shift type, supervisor, mould reference, and mould/press metadata. | Downstream identity and setup data required. |
| FR-AWP-021 | Job Card and Lot # shall be written back to Add On child rows. | Operator/reviewer must see generated output. |
| FR-AWP-022 | Cancellation shall block if downstream BBI exists. | Add-on plan is already consumed. |
| FR-AWP-023 | Cancellation shall block if downstream MPE exists. | Production already started/completed. |
| FR-AWP-024 | Console shall sync Add On as a separate process from Work Planning. | It has different shift uniqueness semantics. |

## Required Operator Feedback

| Event | Feedback |
| --- | --- |
| Add On submitted for shift that already has Work Planning | Allowed, show it is supplemental |
| Missing target quantity | Show item and shift |
| Job Card creation success | Show added Job Cards and Lot #s |
| Cancellation blocked | Show downstream record causing block |
