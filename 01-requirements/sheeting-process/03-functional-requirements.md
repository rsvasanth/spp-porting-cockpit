# Functional Requirements

| ID | Requirement | Why |
| --- | --- | --- |
| FR-SHT-001 | The system shall provide a Sheeting Process submission flow. | Sheeting is its own Console process. |
| FR-SHT-002 | The operator shall scan an approved compound source. | Sheeting must not run on unapproved compound. |
| FR-SHT-003 | The system shall display source item, batch, quantity, and warehouse details after scan. | Operator needs confirmation before output entry. |
| FR-SHT-004 | The operator shall enter multiple output rows in one submission. | One compound input can produce many outputs. |
| FR-SHT-005 | Each output row shall capture item, batch/barcode, quantity, and cut-bit flag. | Legacy `batches` rows need these fields. |
| FR-SHT-006 | The system shall support normal clip rows. | Clips move forward to Blanking. |
| FR-SHT-007 | The system shall support cut-bit rows with `is_cut_bit_item = 1`. | Cut bits follow the recycling path. |
| FR-SHT-008 | The system shall generate deterministic clip barcodes. | Downstream scans depend on stable identity. |
| FR-SHT-009 | The system shall preserve `Cutbit_` naming for cut-bit outputs. | Recycling flow depends on prefix recognition. |
| FR-SHT-010 | The system shall warn when output quantity differs materially from source quantity. | Sheeting needs soft mass-balance visibility. |
| FR-SHT-011 | Quantity mismatch warnings shall not block submission by default. | Physical process variance is real. |
| FR-SHT-012 | The system shall create local Console audit before remote sync. | Failed remote legs must still be reviewable. |
| FR-SHT-013 | The system shall write Console clip mappings inline during local create. | Closes downstream scan race. |
| FR-SHT-014 | The Bridge shall create Legacy `Material Transfer` for Sheeting. | Legacy remains a system of record. |
| FR-SHT-015 | Legacy `Material Transfer` shall include `batches` child rows. | Stock entry creation depends on batch rows. |
| FR-SHT-016 | Legacy `Material Transfer` shall include `sheeting_clip` child rows. | Legacy validation requires clips for sheeting transfer. |
| FR-SHT-017 | The Bridge shall synthesize missing `mix_barcode` for Sheeting rows using the documented legacy format. | Downstream lookup strategies depend on it. |
| FR-SHT-018 | The system shall sync to Legacy and Ops with one Console `reference_id`. | Cross-system traceability. |
| FR-SHT-019 | The system shall expose per-target status and retry without changing output identities. | Labels and scans must remain stable. |
| FR-SHT-020 | Sheeting shall remain separate from Cut Bit Transfer and Bulk Clip Release in requirements and specs. | Refactor workers need one process identity. |

## Required Operator Feedback

| Event | Required feedback |
| --- | --- |
| Source scan failed | Show why the compound cannot be sheeted |
| No output rows | Ask operator to add at least one row |
| Quantity <= 0 | Identify the bad row |
| Sync failure | Show failed target and retry path |
