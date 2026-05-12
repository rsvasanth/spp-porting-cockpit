# Non-Functional Requirements

| ID | Requirement | Target |
| --- | --- | --- |
| NFR-AWP-001 | Add On shall preserve separate identity from Work Planning. | Separate process code and requirement pack |
| NFR-AWP-002 | Add On shall allow multiple supplemental submissions per shift unless explicitly configured otherwise. | No inherited Work Planning uniqueness block |
| NFR-AWP-003 | Work Order / Job Card creation shall be atomic per Add On document. | No partial executable plan |
| NFR-AWP-004 | Job Card Lot # generation shall remain unique for date + shift series. | No duplicate batch code |
| NFR-AWP-005 | Target quantity lookup shall use selected shift time. | Match Legacy |
| NFR-AWP-006 | Cancellation cleanup shall be all-or-nothing. | Avoid orphan rows |
| NFR-AWP-007 | Downstream cancellation guard shall run before destructive cleanup. | Protects BBI/MPE |
| NFR-AWP-008 | Supervisor validation shall complete quickly. | 95% under 1 second locally |
| NFR-AWP-009 | Generated Job Cards and Lot #s shall be visible after creation. | Reviewer clarity |
| NFR-AWP-010 | Retry shall not duplicate Work Orders / Job Cards. | Idempotent by reference/Lot # |
| NFR-AWP-011 | Role checks shall exist at UI and API level. | Authorized supervisors only |
| NFR-AWP-012 | Error messages shall name item, shift, or downstream document. | Quick correction |
| NFR-AWP-013 | Traceability shall connect Add On rows to WO/JC/Lot/downstream records. | Full audit chain |
| NFR-AWP-014 | Any future shift-uniqueness rule for Add On shall require explicit owner approval. | It changes current business behavior |
| NFR-AWP-015 | Add On requirements shall be tested against Add On Legacy code, not Work Planning code. | Avoids wrong inheritance |
