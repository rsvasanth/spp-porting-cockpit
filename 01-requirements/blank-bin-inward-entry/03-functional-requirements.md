# Functional Requirements

| ID | Requirement | Why |
| --- | --- | --- |
| FR-BIE-001 | The system shall provide a Blank Bin Inward Entry submission flow. | BBIE is its own process. |
| FR-BIE-002 | The operator shall scan a bin barcode. | Physical bin is the source identity. |
| FR-BIE-003 | Bin scan shall resolve active `Item Bin Mapping`. | Contents must exist. |
| FR-BIE-004 | Bin scan shall reject retired/empty mappings. | No material to move/repack. |
| FR-BIE-005 | Bin scan shall validate stock availability for the mapped batch. | Legacy validates stock before inward. |
| FR-BIE-006 | The operator shall confirm gross and net weight. | Legacy requires gross weight. |
| FR-BIE-007 | The system shall require at least one child row. | Legacy validation. |
| FR-BIE-008 | The system shall require gross weight on every row. | Legacy validation. |
| FR-BIE-009 | The operator shall choose branch using `move_to_cut_bit_warehouse`. | Core process discriminator. |
| FR-BIE-010 | Normal branch shall create Asset Movement. | Physical bin movement path. |
| FR-BIE-011 | Normal branch shall update active `Item Bin Mapping` qty. | Keeps bin content quantity current. |
| FR-BIE-012 | Cut-bit branch shall require cut-bit batch. | Repack target identity is required. |
| FR-BIE-013 | Cut-bit branch shall create Stock Entry purpose `Repack`. | Legacy active branch. |
| FR-BIE-014 | Cut-bit branch shall move target material into default cut-bit warehouse. | Recycling destination. |
| FR-BIE-015 | Cut-bit branch shall retire the source bin mapping. | Bin contents are removed. |
| FR-BIE-016 | The system shall store created Stock Entry references. | Legacy records comma-separated refs. |
| FR-BIE-017 | Ops implementation shall use a dedicated handler and `run_legacy_sync=False`. | Branching is not generic-template friendly. |
| FR-BIE-018 | BBIE shall remain separate from BDE and BBI requirements. | Refactor alignment. |

## Required Operator Feedback

| Event | Required feedback |
| --- | --- |
| Empty/retired bin | Show no item found |
| Missing stock | Show stock missing |
| Missing gross weight | Identify row |
| Missing cut-bit batch | Block repack submission |
| Branch selected | Show resulting Asset Movement or Repack consequence |
