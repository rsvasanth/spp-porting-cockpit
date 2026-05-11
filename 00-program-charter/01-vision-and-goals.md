# 01 — Vision and goals

## Why this program exists

SPP's manufacturing operations have run for years on a single legacy ERPNext v15 install (the **Legacy** bench at `sppmaster.frappe.cloud`). All shop-floor transactions — Master Batch Mixing, Compound Inspection, Sheeting, Blanking, Moulding — happened through the standard Frappe Desk UI with custom doctypes layered on top (over 100 custom doctypes in the `shree_polymer_custom_app` app).

That setup worked, but it created persistent friction:

| Friction | What it looked like on the shop floor |
|---|---|
| Desk UI on shop-floor tablets | Slow, mouse-heavy, not optimised for scanner-driven workflow |
| Single point of failure | Legacy ERP outage = no production submissions = shift downtime |
| Custom doctypes everywhere | Every new process required schema design, controller logic, report retraining |
| Cross-system reporting impossible | Production data trapped in Legacy with no clean export path |
| Legacy historical baggage | Schemas optimised for paper-form data entry, not real-time manufacturing |
| No audit trail above the doctype layer | When a submission failed, no record of what was attempted |

The **SPP Console porting program** addresses these pressures with a four-component architecture:

1. **Console** — a custom Frappe app whose primary UI is a React-based "Dash" that runs on shop-floor tablets. Operators submit transactions via scanner-driven flows. Console is the **system of record** for identity, audit, and operator workflow.

2. **Legacy Bridge** — a sync engine living on the Legacy bench. Translates Console payloads into Legacy custom doctype writes. Idempotent. Preserves the existing Legacy install untouched so historical reports keep working.

3. **Ops ERPNext** — a **new** ERPNext v15 install (`newspp.m.frappe.cloud`) built from the ground up for cleanliness. Uses **only native ERPNext doctypes** (Stock Entry, Work Order, Job Card, Batch). No custom per-process doctypes. A generic `TransactionEngine` reads sequence templates and creates the right native documents.

4. **Frappe Cloud deploy** — auto-deploys Console from `iyyanarr/shree_polymer_console:develop` to `console.m.frappe.cloud`.

## Strategic goals

### Goal 1 — Shop-floor velocity

Operators submit transactions **faster and with fewer errors** than under the legacy Desk UI. Concretely:

- A scan-driven flow that requires no typing for the common case
- Per-target Live Feedback so operators see Legacy + Ops status independently
- A retry path that does not require re-entering data
- A printable barcode label rendered at submit time

**Measurable:** target average submission time < 30 seconds wall-clock; operator errors per shift reduced by ≥ 50% vs Desk-era baseline.

### Goal 2 — Architectural cleanness on Ops

Ops becomes the **clean** ERPNext install — no custom per-process doctypes, no bespoke controllers per flow. All process-specific logic is declarative, expressed via `Console Process Template.actions` rows that the generic `TransactionEngine` interprets.

**Why this matters strategically:**

- Future ERPNext version upgrades don't require rewriting controllers
- Standard ERPNext stock ledger, batch traceability, and production reports work out of the box
- Any ERPNext developer can read and reason about Ops data without learning Console-specific schemas
- The long-term option exists to retire Legacy entirely and run on Ops alone

**Measurable:** all manufacturing transactions on Ops produce ONLY these doctype types: `Stock Entry`, `Work Order`, `Job Card`, `Batch`, `Stock Ledger Entry`, `Asset` / `Asset Movement` (for bins). Zero custom per-process doctypes on Ops.

### Goal 3 — Dual-ERP resilience

Either ERP can be unavailable for short windows (planned or unplanned) without halting shop-floor operations. The Console + parallel-sync architecture means:

- Submissions to the available ERP continue to succeed
- Failed-leg records are visible and recoverable via operator retry
- Cross-ERP reconciliation surfaces drift at shift-end

**Measurable:** ≥ 99% of submissions complete on at least one ERP within 30 seconds of submit, even during single-ERP outages of up to 15 minutes.

### Goal 4 — Full manufacturing-chain coverage

The porting program covers the **entire** chain from raw material receipt through finished good production:

```
Raw materials
   → Master Batch Mixing
   → Final Batch Mixing
   → Compound Inspection
        ↘ Compound Deviation (when rejected)
   → Sheeting Process
        ↘ Cut Bit Transfer (recycling loop back to FB Mixing)
   → Bulk Clip Release
   → Blanking DC Entry
   → Blank Bin Inward Entry
   → Add On Work Planning
   → Blank Bin Issue
   → Inspection Entry (Line / Patrol / Lot)
   → Moulding Production Entry
   → Finished goods to warehouse
```

A partial port doesn't deliver value — operators submitting the first half of the chain on Console and the second half on Legacy Desk would be the worst of both worlds. The program is binary: each stage either ships end-to-end or it doesn't.

**Measurable:** all 13 stages have a working Console submission path with successful dual-ERP sync; legacy Desk submissions for these processes are phased out (replaced with read-only legacy views for historical lookups).

### Goal 5 — Auditable, recoverable submissions

Every transaction — successful or failed — leaves a complete audit trail. Concretely:

- `Console <Process>` row with `payload_snapshot` (full payload JSON)
- `Console Transaction Log` rows (one per target ERP) with request + response + status
- `Legacy Bridge Log` rows (one per Bridge call) with transformed payload + traceback on failure
- `Shree Polymer MES Log` rows on Ops with action outputs + impacted balances

**Measurable:** for any submission in the last 90 days, an engineer or auditor can reconstruct the full event chain from a single `reference_id`.

## Non-goals (what this program explicitly does NOT pursue)

| Non-goal | Why |
|---|---|
| Real-time inventory consistency across the two ERPs | Eventual consistency is sufficient; 2PC is too brittle |
| Replacing Legacy with Ops in a single cutover | Hard replacement per stage, on shipping schedule; not big-bang |
| Multi-tenant or multi-site Console | Single-site (SPP India) for v1 |
| Localisation / non-English UI | English-only |
| Integration with PLCs / sensors / IoT | Operator manual entry is the data source |
| Replacement of ERPNext modules outside manufacturing (Accounts, HR, Procurement) | Out of program scope; those modules remain on Legacy unchanged |
| Backfill of pre-Console historical data into Console | Historical legacy records stay on Legacy; Console is forward-looking |

## Program success in one sentence

**The porting program is successful when every shop-floor manufacturing transaction at SPP India is initiated on the Console Dash, lands on both ERPs in parallel, leaves a complete audit trail, and produces the right Stock Ledger movements on Ops using only native ERPNext doctypes — for the full manufacturing chain from raw material receipt to finished goods.**

Anything less is incomplete porting. Anything more (PLC integration, localisation, etc.) is out of scope.

## What the program is NOT trying to prove

This porting effort is not:

- A technology demonstration of multi-ERP sync (the architecture serves SPP's operational needs, not a generic blueprint)
- A research project (every decision serves a measurable business goal)
- A complete rewrite of ERPNext or Frappe (we use both heavily, just with Console as the operator-facing layer)
- A consolidation of ERPNext instances (we deliberately maintain two ERPs for resilience and historical continuity)

If a proposed feature doesn't trace back to one of Goals 1–5, it doesn't belong in this program. Use `06-cutover-and-success-criteria.md §Out of program` to push back when scope creep arrives.
