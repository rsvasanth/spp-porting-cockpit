# Functional Requirements

| ID | Requirement | Why |
| --- | --- | --- |
| FR-CBT-001 | The system shall provide a Cut Bit Transfer submission flow. | Recycling must be process-scoped. |
| FR-CBT-002 | The operator shall scan a clip, bin, or eligible source barcode. | Source identity starts from physical scan. |
| FR-CBT-003 | The system shall validate scanned source against active local Console mappings first. | Gives fast shop-floor feedback. |
| FR-CBT-004 | If Console misses, the system shall relay validation to Ops and Legacy as needed. | Some mappings may exist only remotely. |
| FR-CBT-005 | The system shall return item, batch, quantity, UOM, and source warehouse after validation. | Operator needs the resolved source. |
| FR-CBT-006 | The operator shall enter transfer quantity per source row. | Partial bin transfer is allowed. |
| FR-CBT-007 | Transfer quantity shall not exceed available source quantity. | Prevents negative or false stock. |
| FR-CBT-008 | The system shall create a local Console audit record before remote sync. | Keeps failed attempts reviewable. |
| FR-CBT-009 | The Console path shall resolve native batch when local mapping lacks it. | Ops stock entry needs real ERPNext batch. |
| FR-CBT-010 | The Bridge shall create Legacy `Cut Bit Transfer`. | Legacy remains a record target. |
| FR-CBT-011 | Legacy submit shall create a `Stock Entry` with purpose `Repack`. | That is the legacy business effect. |
| FR-CBT-012 | Ops shall use the dedicated cut-bit transfer handler. | Generic template cannot express all side effects cleanly. |
| FR-CBT-013 | Console-to-Ops call shall use `run_legacy_sync=False`. | Console already owns parallel Legacy sync. |
| FR-CBT-014 | Source warehouse shall route by item group: Compound to sheeting warehouse. | Legacy rule. |
| FR-CBT-015 | Source warehouse shall route by blanking item group to Unit 2 warehouse. | Legacy rule. |
| FR-CBT-016 | Other items shall route from default blanking warehouse. | Legacy fallback rule. |
| FR-CBT-017 | Target warehouse shall be default cut-bit warehouse. | Cut-bit stock must land in one place. |
| FR-CBT-018 | Output identity shall preserve `Cutbit_<item_code>` batch and `CB_<item_code>` mix barcode conventions. | Final Batch Mixing scan path depends on them. |
| FR-CBT-019 | Bin mappings shall reduce qty or retire when fully consumed; clip mappings shall not retire here. | Current business ownership separates CBT from release/blanking. |

## Required Operator Feedback

| Event | Required feedback |
| --- | --- |
| Unknown scan | Show which validation layers missed |
| Qty too high | Show available qty |
| Missing batch | Show source and remediation |
| Partial sync | Show target status and retry path |
