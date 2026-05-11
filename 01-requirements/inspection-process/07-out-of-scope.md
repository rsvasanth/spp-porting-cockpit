# 07 — Out of scope

## Out of scope — features

### OOS-INS-001 — General lab management

This requirements pack does not define a full laboratory information system.

**Why not:** It only captures compound QA decisions needed for production flow.

### OOS-INS-002 — New Deviation statuses

Statuses beyond Accepted, Rejected, and Rework are out of scope unless production overseer approves a process change.

### OOS-INS-003 — Automatic root-cause workflow

The system records a reason; it does not manage CAPA, 5-Why, or formal root-cause tasks.

### OOS-INS-004 — Automatic rework recipe generation

Rework disposition does not automatically create a mixing recipe or work order.

### OOS-INS-005 — Historical backfill

Pre-Console legacy Compound Inspection history is not backfilled into Console.

### OOS-INS-006 — Changing legacy QA report structure

Legacy reports are preserved. This pack does not redesign them.

### OOS-INS-007 — Automated reconciliation dashboard

Shift-end reconciliation remains operational unless a future reporting epic adds automation.

### OOS-INS-008 — Moulding Inspection Entry

Line, Patrol, and Lot inspection for moulding belongs to the `moulding/` requirements pack.

### OOS-INS-009 — BOM or recipe editing

Inspection consumes QA limits and item identity; it does not manage BOMs or formulation recipes.

### OOS-INS-010 — PLC / instrument integration

Readings are manually entered. Direct lab instrument integration is a future epic.

## Out of scope — operations

### OOS-INS-020 — Automatic target retry

Failed target legs require explicit retry. The system does not auto-retry in the background.

### OOS-INS-021 — Automatic write-off approval outside QM

Rejected Deviation is the QM decision. Additional finance or inventory approvals are not part of this pack.

### OOS-INS-022 — Cross-shift assignment queue

The pending Deviation list is not a full task assignment system.

### OOS-INS-023 — Removing legacy fallback paths

Old `Console Compound Inspection` and `Console Compound Deviation` records may remain readable. Removing them is a migration epic, not a requirements change here.

## Out of scope — integrations

### OOS-INS-030 — Direct ERP access from Dash

Dash must not query Legacy or Ops directly. Console mediates access.

### OOS-INS-031 — External QA certificate generation

Customer-facing COA or QA certificate generation is not in this motion.

### OOS-INS-032 — BI export

Exporting inspection trends to a data warehouse is outside this transactional requirements pack.

## Related but out of scope

| Related motion | Folder |
|---|---|
| Mixing source batch creation | `../mixing-process/` |
| Sheeting consumes accepted compound | `../sheeting-and-cutting/` |
| Planning and Job Cards | `../production-planning/` |
| Moulding inspections and MPE | `../moulding/` |

## Scope test

A change belongs here if it changes:

1. How compound QA readings are captured.
2. How rejected compound is dispositioned by QM.
3. How inspection/deviation status affects target ERP records.
4. How inspection identity links back to mixed compound.

Otherwise it likely belongs to another requirements pack or a future epic.

