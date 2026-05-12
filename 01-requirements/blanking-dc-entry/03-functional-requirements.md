# Functional Requirements

| ID | Requirement | Why |
| --- | --- | --- |
| FR-BDE-001 | The system shall provide a Blanking DC Entry submission flow. | BDE is a separate process. |
| FR-BDE-002 | The operator shall select or scan the item/mat to produce. | BOM validation needs target item. |
| FR-BDE-003 | The operator shall scan a sheeting clip barcode. | Source material identity comes from clip. |
| FR-BDE-004 | Clip scan shall resolve an active `Item Clip Mapping`. | Released/available clip material is required. |
| FR-BDE-005 | Clip scan shall validate the source compound against the produced item BOM. | Wrong compound must not enter a bin for that mat. |
| FR-BDE-006 | Clip scan shall confirm stock exists in the sheeting warehouse for the resolved batch. | Legacy validation requires physical stock. |
| FR-BDE-007 | The operator shall scan a blanking bin asset. | Destination is a physical bin. |
| FR-BDE-008 | Bin scan shall reject bins with active unreleased bin mappings. | Prevents filling an occupied bin. |
| FR-BDE-009 | Bin scan shall require bin tare weight. | Net weight depends on tare. |
| FR-BDE-010 | The operator shall enter gross weight per row. | Legacy requires gross weight. |
| FR-BDE-011 | The system shall calculate `net_weight = gross_weight - bin_weight`. | Legacy controller enforces it. |
| FR-BDE-012 | The system shall reject no-item submissions. | Legacy validation. |
| FR-BDE-013 | The system shall reject future posting dates. | Legacy validation. |
| FR-BDE-014 | Submission shall create a local Console audit record before target sync. | Audit-first invariant. |
| FR-BDE-015 | Submission shall create active bin mapping rows for downstream scans. | BBIE/BBI depend on them. |
| FR-BDE-016 | Submission shall reduce or retire source clip quantity according to net weight. | Prevents over-consuming one clip. |
| FR-BDE-017 | Legacy submit shall create native `Asset Movement`. | Bin location tracking depends on ERPNext Asset Movement. |
| FR-BDE-018 | Legacy submit shall create `Item Bin Mapping` unless `from_blank_bin_inward` is set. | Re-entry branch avoids duplicate mappings. |
| FR-BDE-019 | Submission shall sync to Legacy and Ops with one `reference_id`. | Cross-system traceability. |
| FR-BDE-020 | BDE shall remain separate from BBIE and BBI in requirements and refactor work. | Different business effects. |

## Required Operator Feedback

| Event | Required feedback |
| --- | --- |
| Invalid clip | Show inactive/missing clip reason |
| BOM mismatch | Show compound and item/mat mismatch |
| Invalid bin | Show occupied/missing/tare missing reason |
| Gross weight missing | Identify row |
| Partial sync | Show failed target and retry path |
