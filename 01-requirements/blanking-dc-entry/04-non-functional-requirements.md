# Non-Functional Requirements

| ID | Requirement | Why |
| --- | --- | --- |
| NFR-BDE-001 | Clip/bin scan feedback should return within 2 seconds under normal load. | Floor scanning must stay fast. |
| NFR-BDE-002 | Net weight calculation must be consistent across Dash, Console, Bridge, and Legacy. | Weight is the bin quantity source. |
| NFR-BDE-003 | Asset Movement creation and bin mapping creation must be atomic on Legacy. | Avoids bin without location or location without contents. |
| NFR-BDE-004 | Clip quantity deduction must not allow negative balance. | Prevents over-consumption. |
| NFR-BDE-005 | Concurrent BDE submissions against one clip must serialize or fail one submission. | Same clip cannot be overdrawn. |
| NFR-BDE-006 | Local audit must survive target failure. | Operator can diagnose/retry. |
| NFR-BDE-007 | Error messages must be operator-actionable. | Shop-floor usability. |
| NFR-BDE-008 | Records must be traceable by bin, clip, compound, batch, and `reference_id`. | Audit/reconciliation. |
| NFR-BDE-009 | BDE callback routing must update local sync status reliably. | Current spec flags drift. |
| NFR-BDE-010 | Ops semantics must be explicitly documented when they differ from Legacy. | Prevents wrong refactor assumptions. |
| NFR-BDE-011 | Tests must cover clip partial consumption and full retirement. | Main state mutation risk. |
| NFR-BDE-012 | Requirement/spec/code must stay process-scoped. | Refactor alignment. |
