# Non-Functional Requirements

| ID | Requirement | Target |
| --- | --- | --- |
| NFR-WPL-001 | Shift duplicate validation shall be deterministic. | No two submitted Work Planning records for same date + shift series |
| NFR-WPL-002 | Work Order / Job Card creation shall be atomic per plan. | No partial WO/JC state without visible failure |
| NFR-WPL-003 | Lot # / barcode generation shall be unique for date + shift series. | No duplicate Job Card batch code |
| NFR-WPL-004 | Target quantity lookup shall use the selected shift time. | Matches Legacy query behavior |
| NFR-WPL-005 | Mould filtering shall avoid inactive moulds. | Active/spare/dev only, as Legacy Work Planning does |
| NFR-WPL-006 | Cancellation cleanup shall be all-or-nothing. | No orphan Job Card / Work Order / serial rows |
| NFR-WPL-007 | Downstream cancellation block shall be checked before destructive cleanup. | Protects BBI/MPE audit |
| NFR-WPL-008 | Supervisor validation shall complete quickly enough for scan UX. | 95% under 1 second locally |
| NFR-WPL-009 | Planning records shall expose generated Job Cards and Lot #s for downstream review. | Visible after creation |
| NFR-WPL-010 | Console-to-Legacy sync shall preserve Work Planning identity separate from Add On. | Separate process code |
| NFR-WPL-011 | Retry shall not create duplicate Work Orders / Job Cards. | Idempotent by reference/Lot # |
| NFR-WPL-012 | Role checks shall exist at UI and API levels. | Authorized supervisors only |
| NFR-WPL-013 | Error messages shall include item, shift, or downstream document causing failure. | Supervisor can correct quickly |
| NFR-WPL-014 | Traceability shall connect Work Planning row to Work Order, Job Card, Lot #, and downstream BBI/MPE. | Full audit chain |
| NFR-WPL-015 | Mould/press metadata copied to Job Card shall be reproducible from master data. | Avoid hidden manual edits |
| NFR-WPL-016 | Console requirements shall be tested against Legacy Work Planning code, not only Add On code. | Prevents recurrence of collapse error |
| NFR-WPL-017 | Any intentional deviation from Legacy one-shift rule shall require explicit owner sign-off. | It changes business behavior |
| NFR-WPL-018 | Requirement/spec/code alignment shall mark current Add On-only spec as incomplete for Work Planning. | Visible drift |
