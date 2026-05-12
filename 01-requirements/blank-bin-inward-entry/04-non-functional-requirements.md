# Non-Functional Requirements

| ID | Requirement | Why |
| --- | --- | --- |
| NFR-BIE-001 | Bin validation should return within 2 seconds under normal load. | Material movement workflow. |
| NFR-BIE-002 | Branch choice must be visible before submit. | Operator must understand consequence. |
| NFR-BIE-003 | Repack Stock Entry and IBM retirement must be atomic. | Prevents material disappearing. |
| NFR-BIE-004 | Asset Movement and IBM qty update must be atomic in normal branch. | Prevents location/content drift. |
| NFR-BIE-005 | Rollback must restore IBM qty/retirement state on failure. | Legacy has rollback logic. |
| NFR-BIE-006 | Cut-bit batch validation must fail clearly. | Prevents wrong batch target. |
| NFR-BIE-007 | `move_to_cut_bit_warehouse` path must be tested as primary path. | Site records show it dominates. |
| NFR-BIE-008 | Cross-system records must be traceable by bin and IBM id. | Audit/reconciliation. |
| NFR-BIE-009 | Dedicated Ops handler must not duplicate Legacy sync. | Parallel architecture invariant. |
| NFR-BIE-010 | Error messages must be operator-actionable. | Shop-floor usability. |
| NFR-BIE-011 | Requirement/spec/code must stay process-scoped. | Refactor alignment. |
