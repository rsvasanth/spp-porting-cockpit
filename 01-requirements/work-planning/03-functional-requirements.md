# Functional Requirements

| ID | Requirement | Why |
| --- | --- | --- |
| FR-WPL-001 | The system shall provide a Work Planning submission flow. | Work Planning is the base shift plan. |
| FR-WPL-002 | Work Planning shall require planning date. | Shift uniqueness depends on date. |
| FR-WPL-003 | Work Planning shall require shift type, shift series, and shift time. | Legacy validates `shift_series` and `shift_time`. |
| FR-WPL-004 | Work Planning shall require scanned supervisor identity. | Legacy uses supervisor scan and employee mapping. |
| FR-WPL-005 | Work Planning shall validate supervisor against active employees mapped to Moulding Supervisor designation. | Prevents unauthorized planning. |
| FR-WPL-006 | Work Planning shall support multiple item rows in one shift plan. | One shift can produce multiple products. |
| FR-WPL-007 | Each item row shall capture item, workstation/press, mould, BOM, Job Card reference, and Lot #. | These fields form downstream production identity. |
| FR-WPL-008 | Work Planning shall prevent duplicate workstation rows within the same plan. | Legacy UI blocks duplicate press for shift. |
| FR-WPL-009 | Work Planning shall prevent duplicate mould rows within the same plan. | Legacy UI blocks duplicate mould for shift. |
| FR-WPL-010 | Work Planning shall reject submission with no item rows. | Legacy throws "Please add items before save." |
| FR-WPL-011 | Work Planning shall validate each item against `Work Plan Item Target` for the selected shift time. | Target quantity drives Work Order quantity. |
| FR-WPL-012 | If target quantity is missing for any planned item and shift time, submission shall fail. | Legacy blocks missing target quantity. |
| FR-WPL-013 | Work Planning shall validate that each item has an active default BOM or selected BOM. | Work Order cannot be created without BOM. |
| FR-WPL-014 | Work Planning shall fetch and expose valid BOM choices per item. | Legacy frontend supports BOM choice/filtering. |
| FR-WPL-015 | Work Planning shall filter items by configured item group. | Legacy uses SPP Settings item group. |
| FR-WPL-016 | Work Planning shall filter workstations by configured allowed workstation list. | Legacy uses SPP Settings workstation list. |
| FR-WPL-017 | Work Planning shall filter moulds by item and active/spare/dev mould specification. | Legacy Work Planning restricts mould lookup by mould status. |
| FR-WPL-018 | Work Planning shall enforce one submitted Work Planning per date + shift series. | This is the base-plan invariant. |
| FR-WPL-019 | After submission, the system shall support Work Order / Job Card creation from the plan. | Legacy uses post-submit helper button. |
| FR-WPL-020 | Work Order quantity shall be calculated from SPP Settings target multiplier and Work Plan Item Target quantity. | Legacy calculates `actual_weight`. |
| FR-WPL-021 | Work Orders shall use Moulding operation with selected workstation and BOM. | Downstream manufacturing depends on this. |
| FR-WPL-022 | Job Cards shall receive Lot #, barcode image/text, shift type, supervisor, mould reference, and mould/press settings. | These values drive downstream scanning and MPE. |
| FR-WPL-023 | The Job Card Lot # shall be written back to the Work Plan Item row. | Child rows must show generated Lot #. |
| FR-WPL-024 | Work Planning cancellation shall block if any Job Card Lot # is used in submitted Blank Bin Issue. | Legacy prevents cancellation after BBI. |
| FR-WPL-025 | Work Planning cancellation shall block if any Job Card Lot # is used in submitted Moulding Production Entry. | Legacy prevents cancellation after MPE. |
| FR-WPL-026 | If cancellation is allowed, related Job Cards, Work Orders, and Moulding Serial No rows shall be deleted/cleared consistently. | Legacy cleanup behavior must be preserved or replaced safely. |
| FR-WPL-027 | Console implementation shall sync Work Planning as its own process, not as Add On. | The business semantics differ. |
| FR-WPL-028 | Console shall expose per-leg sync status and retry without regenerating downstream identity. | Planning identity must survive retries. |

## Required Operator Feedback

| Event | Required feedback |
| --- | --- |
| Duplicate shift plan | Show existing Work Planning document |
| Missing target quantity | Show item and shift type missing target |
| Missing BOM | Show item without active BOM |
| Job Card creation success | Show Job Card and Lot # list |
| Cancellation blocked | Show downstream BBI/MPE document causing block |
