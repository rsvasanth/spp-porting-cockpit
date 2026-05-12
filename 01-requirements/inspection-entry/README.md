# Inspection Entry — Business Requirements

**Business process:** Unified quality inspection entry across moulding, incoming, final visual, and related inspection flows.
**Console process identity:** `Console Inspection Entry`.
**Legacy DocType target:** `Inspection Entry`.
**Primary downstream records:** Material Transfer rejection Stock Entries, MPE batch cascade, Final Visual / PDIR stock flows, Deflashing Receipt trigger.

This folder is intentionally separate from [Moulding Production Entry](../moulding-production-entry/README.md). MPE consumes inspection results, but Inspection Entry is its own polymorphic DocType with production-scale records and multiple inspection types.

## Current source evidence

| Source | Finding |
|---|---|
| Legacy controller | `inspection_entry.py` handles validation, duplicate prevention, rejection stock entry creation, visual/PDIR flows, and MPE batch cascade. |
| Live `spp15.local` records | 124,197 Inspection Entry records, 120,663 submitted. |
| Live types | Lot, Line, Incoming, Final Visual, Patrol, and Visual Inspection all exist. |
| Child table | `Inspection Entry Item` stores `type_of_defect`, `rejected_qty`, and `rejected_qty_kg`. |
| Spec status | `02-specifications/inspection-entry/` exists but is empty; legacy code and live records are the authority for this pass. |

## Files

| File | What it answers |
|---|---|
| [01-purpose.md](01-purpose.md) | Why Inspection Entry exists and how types differ |
| [02-actors-and-roles.md](02-actors-and-roles.md) | Inspector, QA, production, and system roles |
| [03-functional-requirements.md](03-functional-requirements.md) | `FR-IE-*` outcome requirements |
| [04-non-functional-requirements.md](04-non-functional-requirements.md) | Data integrity, audit, latency, and parity requirements |
| [05-business-rules.md](05-business-rules.md) | Type uniqueness, required fields, rejection stock rules |
| [06-acceptance-criteria.md](06-acceptance-criteria.md) | UAT checks |
| [07-out-of-scope.md](07-out-of-scope.md) | Explicit exclusions |
| [08-traceability.md](08-traceability.md) | Legacy/site/spec mapping and drift findings |

