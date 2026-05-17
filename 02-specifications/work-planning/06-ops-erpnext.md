# 06 — Ops ERPNext target

## Current status

No dedicated Ops Work Planning handler is documented in the cockpit. The Add On Work Planning spec previously assumed generic ERPNext Work Order + Job Card creation via TransactionEngine. That may still be viable, but Work Planning needs its own process identity and duplicate-shift rule.

## Required Ops outcome

| Legacy outcome | Ops equivalent |
| --- | --- |
| Work Planning submitted | Ops planning log or Work Order reference |
| Work Order created | Native ERPNext Work Order |
| Job Card created | Native ERPNext Job Card |
| Lot # on Job Card | Custom field or equivalent scan identity |
| Shift/supervisor/mould metadata | Custom fields where needed |

## Required data preservation

Ops must preserve:

| Field | Why |
| --- | --- |
| Lot # / Job Card batch code | Downstream scan identity |
| shift type / shift series | Production reporting |
| supervisor | Accountability |
| item, BOM, workstation, mould | Execution context |
| reference ID | Retry and reconciliation |

## Bridge vs Ops responsibility split

Bridge handles **Work Planning document sync only** (Console → Legacy).
Ops handles **Work Order + Job Card creation** via TransactionEngine.

| Layer | Responsibility |
| --- | --- |
| Bridge | Sync Console Work Planning to Legacy Work Planning |
| Legacy | Creates WO + Job Cards via `on_submit_value()` after submit |
| Ops | Creates separate WO + Job Cards via TransactionEngine after bridge confirms |

This split avoids double-creating WOs and keeps Legacy as the system of record for the manufacturing planning chain.

## Handler decision

| Option | Risk |
| --- | --- |
| Generic TransactionEngine | Needs for-each Work Order/Job Card support and custom fields |
| Dedicated handler | More code, clearer mapping for planning-specific identity |

## Drift to verify

Before implementation, verify whether Ops already has custom fields for Lot #, shift, mould, supervisor, and Work Planning reference on Work Order / Job Card.
