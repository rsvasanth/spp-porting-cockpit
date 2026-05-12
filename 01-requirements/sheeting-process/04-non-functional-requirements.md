# Non-Functional Requirements

| ID | Requirement | Why |
| --- | --- | --- |
| NFR-SHT-001 | Source scan feedback should return within 2 seconds under normal load. | Scanner workflow must stay fast. |
| NFR-SHT-002 | Local audit creation must be atomic with `reference_id` assignment. | Prevents orphaned remote sync. |
| NFR-SHT-003 | Inline clip mapping creation must happen before remote target execution. | Prevents downstream scan race. |
| NFR-SHT-004 | Output barcode generation must be deterministic under retry. | Printed labels cannot change. |
| NFR-SHT-005 | The system must tolerate one remote leg failing while preserving the other leg result. | Architecture is eventually consistent. |
| NFR-SHT-006 | Error messages must be operator-actionable. | Floor users need next action, not stack traces. |
| NFR-SHT-007 | Sheeting output rows must remain traceable to the source compound. | QA and stock reconciliation depend on lineage. |
| NFR-SHT-008 | Legacy mapping must fail loudly if required child data is missing. | Silent missing clips break Blanking later. |
| NFR-SHT-009 | Console local cache validation bypass must not skip final submitted validation on real records. | Audit-first pattern must not weaken data quality. |
| NFR-SHT-010 | Sheeting changes must pass unit and integration tests before push. | This process feeds multiple downstream flows. |
| NFR-SHT-011 | Requirement/spec/code comparison must keep Sheeting as a separate review unit. | Avoids reintroducing merged process drift. |
| NFR-SHT-012 | Cross-system records must be searchable by `reference_id` or output barcode. | Support needs fast diagnosis. |
| NFR-SHT-013 | The UI must remain scanner-first and usable on shop-floor screens. | Keyboard-heavy entry slows production. |
