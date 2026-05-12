# Non-Functional Requirements

| ID | Requirement | Why |
| --- | --- | --- |
| NFR-BCR-001 | Scan validation should return within 2 seconds for local mappings. | Batch scanning must stay fast. |
| NFR-BCR-002 | Release must be idempotent enough to retry safely. | Avoid double-release confusion. |
| NFR-BCR-003 | Barcode text must be resolved to clip document name before mapping update where required. | Prevents missed retirements. |
| NFR-BCR-004 | No stock ledger side effects shall occur. | Release is not stock movement. |
| NFR-BCR-005 | Release audit must show operator, date/time, and clip list. | Accountability. |
| NFR-BCR-006 | Error messages must be shop-floor readable. | Operator actionability. |
| NFR-BCR-007 | Console, Ops, and Legacy clip states must reconcile by barcode. | Cross-system integrity. |
| NFR-BCR-008 | Process wiring drift must be captured before implementation refactor. | Current spec shows several gaps. |
| NFR-BCR-009 | Tests must cover barcode text != document name. | This is the main identity risk. |
| NFR-BCR-010 | Requirements/spec/code must remain process-scoped. | Prevents mixed handoff. |
| NFR-BCR-011 | Changes must pass focused tests before push. | Small process, high downstream impact. |
