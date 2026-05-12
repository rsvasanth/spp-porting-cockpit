# Non-Functional Requirements

| ID | Requirement | Why |
| --- | --- | --- |
| NFR-CBT-001 | Validation should return within 3 seconds when local mapping exists. | Scanner workflow must stay quick. |
| NFR-CBT-002 | Remote relay validation must fail with clear diagnostics. | Operators need to know whether asset is missing or remote failed. |
| NFR-CBT-003 | Batch resolution must fail loudly when no usable native batch exists. | Silent wrong batch corrupts stock. |
| NFR-CBT-004 | Repack stock entries must use serial/batch fields compatible with ERPNext v15. | Avoids SABB conflicts. |
| NFR-CBT-005 | The system must be idempotent under retry where target supports it. | Avoid duplicate repacks. |
| NFR-CBT-006 | Weak Legacy idempotency must be documented and tested. | Legacy lacks a clean reference field. |
| NFR-CBT-007 | Source warehouse routing must be deterministic. | Stock ledger correctness. |
| NFR-CBT-008 | Local bin qty updates must be transactionally consistent with submission result. | Prevents bin qty drift. |
| NFR-CBT-009 | Error messages must avoid raw stack traces. | Shop-floor usability. |
| NFR-CBT-010 | Requirements/spec/code must remain process-scoped. | Refactor alignment. |
| NFR-CBT-011 | Changes must pass targeted tests before push. | Repack and stock impact are high-risk. |
| NFR-CBT-012 | Records must be traceable by source barcode and output cut-bit identity. | Recycling audit. |
