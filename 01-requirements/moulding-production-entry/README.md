# Moulding Production Entry — Business Requirements

**Business process:** Terminal moulding production booking.
**Console process identity:** `Console Moulding Production Entry`.
**Legacy DocType target:** `Moulding Production Entry`.
**Primary downstream records:** ERPNext `Stock Entry` Manufacture, `Job Card`, `Work Order`, inspection rejection Stock Entries.

This folder is intentionally separate from [Inspection Entry](../inspection-entry/README.md). Inspection Entry is a prerequisite and rejection source; Moulding Production Entry is the execution record that consumes issued blank bins and books finished-goods production.

## Current source evidence

| Source | Finding |
|---|---|
| Legacy controller | `moulding_production_entry.py` validates lot, inspections, bins, tolerance, shell/injection variants, stock, and final booking. |
| Live `spp15.local` records | 30,006 MPE records, 28,931 submitted. |
| Injection flag | 613 records marked injection moulding; 29,393 non-injection. |
| Dominant downtime/reason codes | `PLANNING`, `COMPOUND SHORTAGE`, `OPERATOR ISSUE`, `COMPOUND ISSUE`, `MLD CHANGE`; most records have no reason code. |
| Spec status | `02-specifications/moulding-production-entry/` exists but is empty, so legacy code and live records are the authority for this requirement pass. |

## Files

| File | What it answers |
|---|---|
| [01-purpose.md](01-purpose.md) | Why MPE exists and where it sits in the end-to-end flow |
| [02-actors-and-roles.md](02-actors-and-roles.md) | Who scans, verifies, submits, and reviews MPE |
| [03-functional-requirements.md](03-functional-requirements.md) | `FR-MPE-*` outcome requirements |
| [04-non-functional-requirements.md](04-non-functional-requirements.md) | Integrity, latency, concurrency, and audit requirements |
| [05-business-rules.md](05-business-rules.md) | Lot, inspection, bin, tolerance, shell, and batch rules |
| [06-acceptance-criteria.md](06-acceptance-criteria.md) | UAT and implementation checks |
| [07-out-of-scope.md](07-out-of-scope.md) | Explicit exclusions |
| [08-traceability.md](08-traceability.md) | Legacy/site/spec mapping and drift findings |

