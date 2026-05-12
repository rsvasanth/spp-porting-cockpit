# 01 — Business context

## What Inspection Entry is (shop floor)

Inspection Entry (IE) is the **polymorphic quality gate** for moulding and
related production flows. A Quality Inspector:

1. Selects an inspection type (Line, Patrol, Lot, Incoming, Final Visual, Visual)
2. Scans their employee badge (inspector code)
3. Scans the production lot (lot_no / batch_code from Job Card)
4. Enters inspected quantities and defect rows
5. Hits submit — which creates rejection Stock Entries and may trigger the
   MPE batch cascade or Final Visual / PDIR production path

IE is **not only a MPE precondition screen**. It is a production-scale record
with 124,197 total records in live production. Its 6-type polymorphic design
covers the full quality lifecycle from incoming material through moulding to
final visual inspection.

## The 6 inspection types

| Type | Count (total) | Count (submitted) | UOM | Downstream |
|---|---|---|---|---|
| Lot Inspection | 29,615 | 28,474 | Nos (inspected_qty_nos) | Rejection SE → MPE batch cascade |
| Line Inspection | 29,487 | 29,201 | Nos (inspected_qty_nos) | Rejection SE → MPE batch cascade |
| Incoming Inspection | 27,891 | 27,718 | Nos or Kg (total_inspected_qty_nos) | Rejection SE → Deflashing Receipt trigger |
| Final Visual Inspection | 27,378 | 25,597 | Nos (vs_pdir_qty) | VS/PDIR Stock Entry → Work Order → LRT update |
| Patrol Inspection | 9,820 | 9,667 | Nos (inspected_qty_nos) | Rejection SE → MPE batch cascade |
| Visual Inspection | 6 | 6 | — | Likely pre-unification test entries |

**Volume interpretation:** Each type exceeds 25k records except Patrol (9.8k)
and Visual (6). All types are operationally real. The spec must not collapse
IE to only the three moulding variants (Line/Patrol/Lot).

## Why IE is process-adjacent to MPE but different

MPE consumes the outputs of moulding. IE is where the **quality data itself
lives**. The relationship:

```
Blank Bin Issue → Work Planning → Blank Bin Issue → Moulding
                                                       │
                               ┌───────────────────────┼───────────────────────┐
                               │                       │                       │
                           Line IE               Patrol IE                Lot IE
                               │                       │                       │
                               └───────────────────────┴───────────────────────┘
                                                       │
                                              MPE submits
                                    (MPE requires submitted Line + Patrol IE)
                                                       │
                                              MPE produces batch
                                                       │
                              ┌────────────────────────┴────────────────────────┐
                              │  IE's submit_inspection_stock_entry_immediately  │
                              │  receives batch and submits draft rejection SEs   │
                              └──────────────────────────────────────────────────┘
```

IE also has two **non-moulding** branches:

- **Incoming Inspection** — incoming material from deflashing; creates rejection
  Stock Entry and triggers Deflashing Receipt submission
- **Final Visual Inspection** — end-of-line visual quality gate; creates VS/PDIR
  Stock Entry, Work Order, Job Card, and updates Lot Resource Tagging

## What success looks like for Line / Patrol / Lot

1. Inspector scans inspector badge → inspector_name + inspector_code populated
2. Scans production lot → lot_no populated, system resolves Job Card,
   mould reference, workstation, production item, and MPE completion status
3. Mould Specification resolves `one_no_qty_equal_kgs` (piece weight in kg)
4. Inspector enters inspected quantity (nos) and adds defect rows
5. Totals computed: `total_rejected_qty`, `total_rejected_qty_kg` (from child rows)
6. Inspector submits → IE submitted, draft Stock Entry created if rejected kg > 0
7. (Later, when MPE submits) batch cascades back, rejection SEs receive batch and submit

## What success looks like for Incoming / Final Inspection

1. Inspector scans lot (which must have a Deflashing Receipt Entry)
2. System resolves Job Card, production item from Deflashing Receipt's Stock Entry
3. Inspector enters inspected qty (nos or kg depending on UOM field)
4. Defect rows added → rejection Stock Entry created
5. If Incoming: `submit_deflash_receipt_entry` fires, which calls
   `Deflashing Receipt Entry.manual_on_submit`

## What success looks like for Final Visual Inspection

Two paths depending on whether there is rejection:

**With rejection:**
1. Inspector scans lot (must exist in Lot Resource Tagging with docstatus=1)
2. System checks BOM operations sequence — Final Visual must not be first
3. Inspector enters `vs_pdir_qty` (available qty) and defect rows
4. `total_rejected_qty` drives rejection transfer
5. `vs_pdir_qty_after_rejection` = inspected - rejected (precomputed in validate)
6. On submit: `submit__vs_pdir()` runs — creates rejection SE, finds/creates
   Work Order, creates Job Card, submits SE, updates LRT

**Without rejection (no-rejection path):**
1. Same lot scan and BOM check
2. Inspector enters `vs_pdir_qty` with no defect rows
3. On submit: `submit__vs_pdir_no_rejection()` runs — checks stock availability,
   updates LRT's `qty_after_rejection_nos`, creates Work Order + SE (no rejection transfer)

## Who interacts with this process

| Role | What they do |
|---|---|
| Quality Inspector | Scans inspector, lot, records defects, submits IE. Handles all 6 types. |
| QA Lead | Owns defect type policy, duplicate exception decisions (Final Visual allowed to duplicate) |
| Moulding Operator | Depends on Line + Patrol completion before MPE; not an IE submitter |
| Production Overseer | Reviews failed stock entries, rollback cases, cross-process mismatches |

## Operational constraints

| Constraint | Reason |
|---|---|
| Inspector code required | BR-IE-002 / FR-IE-002 — inspector identity must be on record |
| Lot + type uniqueness (except Final Visual) | BR-IE-001 — prevents double-inspection of same lot |
| Mould Specification required for moulding types | BR-IE-005 — piece weight needed to compute rejected kg |
| Posting date cannot be future | FR-IE-004 — backdating allowed only for System Manager |
| Rejection SE created only when rejected kg > 0 | BR-IE-003 — zero-rejection submits don't create Stock Entries |

## Relationship to upstream/downstream

```
BLANKING → Blank Bin Inward → Work Planning → Blank Bin Issue → MOULDLING
                                                                │
                                                    Line IE, Patrol IE, Lot IE
                                                                │
                                                         MPE submits
                                                                │
                                                      MPE produces batch
                                                                │
                                     ┌──────────────────────────┴──────────────────────────┐
                                     │                                                         │
                            Incoming IE ←── DEFLASHING                                       │
                                     │                                 Final Visual IE       │
                                     │                                      (LRT entry exists) │
                                     ↓                                      │                  │
                            Deflashing Receipt Entry                            ↓                  │
                            (triggered by submit_deflash_receipt_entry)    LRT (Lot Resource Tagging)    │
                                                                              │                  │
                                                                              └──────────────────┘