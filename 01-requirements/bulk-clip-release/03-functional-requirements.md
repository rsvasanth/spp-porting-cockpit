# Functional Requirements

| ID | Requirement | Why |
| --- | --- | --- |
| FR-BCR-001 | The system shall provide a Bulk Clip Release submission flow. | Release is its own process. |
| FR-BCR-002 | The operator shall scan multiple clip barcodes into one release batch. | Legacy supports child rows for many clips. |
| FR-BCR-003 | The system shall reject empty release batches. | Legacy validation requires clips. |
| FR-BCR-004 | The system shall reject duplicate scans in the same draft. | Prevents duplicate child rows. |
| FR-BCR-005 | Each scan shall resolve `Sheeting Clip` by physical `barcode_text`. | Operators scan barcode labels, not document names. |
| FR-BCR-006 | Each scan shall require an active `Item Clip Mapping`. | Already released clips must not release again. |
| FR-BCR-007 | Successful validation shall return mapping id, compound, clip, batch, and qty. | Legacy child rows need mapping id. |
| FR-BCR-008 | Submission shall create or preserve an audit record for the release. | Release is an accountable state change. |
| FR-BCR-009 | Legacy release shall retire mappings by `item_clip_mapping_id`. | Legacy controller behavior. |
| FR-BCR-010 | Ops release shall retire mappings through the dedicated `bulk_release_clips` handler. | No Stock Entry required. |
| FR-BCR-011 | Console local mirror retirement timing shall be explicit and testable. | Avoid stale active clips. |
| FR-BCR-012 | Release shall not create Stock Entry records. | This is a state transition. |
| FR-BCR-013 | The system shall expose per-target success/failure. | Dual ERP sync can partially fail. |
| FR-BCR-014 | Retry shall not release a different physical clip. | Barcode identity must stay stable. |
| FR-BCR-015 | Barcode text and clip document name shall be resolved deliberately in Bridge/Ops. | They may not be equal. |
| FR-BCR-016 | Bulk Clip Release shall remain separate from Sheeting and Cut Bit Transfer. | Refactor review requires process identity. |

## Required Operator Feedback

| Event | Required feedback |
| --- | --- |
| Invalid barcode | Show invalid clip message |
| Already released | Show that active mapping was not found |
| Duplicate draft scan | Show duplicate warning |
| Partial sync | Show which target failed |
