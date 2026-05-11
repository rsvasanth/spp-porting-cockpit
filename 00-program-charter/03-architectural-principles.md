# 03 — Architectural principles

This file expands the three pillars introduced in [README](README.md) into binding architectural principles. Each principle is **stated**, **rationalised**, and explicit about **what it rules in/out**.

When a Hermes worker proposes a change that violates one of these principles, the Reviewer worker must block it and escalate to the production overseer.

---

## Principle 1 — Console is the system of record

**Statement:** The Console application owns the canonical identity, audit trail, and operator-facing workflow for every shop-floor transaction. Both ERPs (Legacy and Ops) are downstream consumers that mirror Console's intent.

### What this means concretely

| Aspect | Console owns | Both ERPs receive |
|---|---|---|
| Transaction identifier | `reference_id` (13-digit ms timestamp) | Same value, written to Legacy `dc_no` and Ops MES Log |
| Mix barcode | `mix_barcode` (`C_YYMMDDXn` format) | Same value, honored as-is via Legacy `bridge_mix_barcode` and Ops SE FG row |
| Lot # (Wave 3+) | Console-generated sequential | Both ERPs accept; Legacy `create_planning_with_jobcards` uses it |
| Submission audit | `payload_snapshot` JSON | (Not duplicated downstream) |
| Per-leg sync status | `ops_sync_status`, `legacy_sync_status`, `sync_status` aggregate | (Not duplicated downstream) |
| Operator identity | `submitted_by` (Console User) | Mapped to legacy `employee` and Ops `created_by` |

### Rationale

1. **Decouples shop-floor velocity from ERP complexity.** Operators don't wait for either ERP to round-trip before seeing success — they see Console's status, with parallel Live Feedback.

2. **Survives single-ERP outages.** If Legacy is briefly unavailable, the operator's Console submission still lands locally + flows to Ops. Recovery is operator-driven retry, not a database recovery exercise.

3. **Unifies cross-system reporting.** Reports that need "all production for date X across both ERPs" can query Console alone — no need to reconcile two different identity schemes.

4. **Future-proofs the architecture.** If either ERP gets replaced (e.g. Legacy retired, or Ops upgraded to a future ERPNext major version), Console is the stable anchor.

### What this rules in

- Adding any new identity to a transaction (e.g. a new batch convention) starts on Console
- Audit trail enhancements live on Console first; ERPs receive what they need to mirror
- Console doctype schema changes are coordinated across Bridge + Ops mapping; the Console doctype is the source of canonical field names

### What this rules out

- Generating identity on either ERP (e.g. legacy auto-generating a mix barcode when Console provides one)
- Having only one ERP know about a transaction (every successful submission must land on BOTH or be marked Partial)
- Routing operator submissions directly to an ERP without going through Console
- Using a non-`reference_id` cross-system key

### Existing implementation patterns that enforce this

- The `bridge_mix_barcode` honor pattern on Legacy DCR controller (BR-MIX-005)
- The unique constraint on `Console <Process>.reference_id`
- The 5-step `apply_bridge_result` race-safe aggregation (BR-MIX-014)
- The `_safe_local_create` audit-trail bypass (BR-MIX-011)

---

## Principle 2 — Native ERPNext on Ops (no custom per-process doctypes)

**Statement:** The Ops ERPNext install must use only **standard ERPNext document types** for all manufacturing transactions. No custom per-process doctypes. Process-specific behavior is expressed declaratively via `Console Process Template.actions` rows that a generic `TransactionEngine` interprets.

### Allowed doctypes on Ops (whitelist)

| ERPNext doctype | Purpose in SPP |
|---|---|
| `Stock Entry` (Material Transfer, Material Receipt, Manufacture, Repack purposes) | All inventory movements |
| `Work Order` | Production planning + completion |
| `Job Card` | Operator-level work tracking |
| `Batch` (auto-created) | Lot identification |
| `Stock Ledger Entry` (auto-generated) | Inventory ledger |
| `Asset` + `Asset Movement` | For bins (physical containers) |
| `Item Batch Stock Balance` | Frappe-native batch balance |
| `Shree Polymer MES Log` | Ops-side transaction logging (the ONE exception; not a per-process doctype but a generic audit log) |

### Banned on Ops

- Any doctype named `Ops <Process>` or similar
- Any custom controller written specifically for a single process flow (with the exceptions listed below)
- Any custom child doctype used only by one process

### Rationale

1. **ERPNext community alignment.** Any developer who knows ERPNext can read the Ops install without learning Console-specific schemas. Onboarding time drops.

2. **Version-upgrade safety.** ERPNext releases break custom doctypes far more often than native ones. Sticking to native means Ops can upgrade with minimal rework.

3. **Standard reporting works.** ERPNext's built-in stock ledger, batch traceability, production order reports, and analytics dashboards function out of the box on Ops. No need to write custom reports for production data.

4. **Future migration option preserved.** If SPP ever wants to retire the Legacy install entirely and run on Ops alone, the Ops data model is already aligned with standard ERPNext — no de-customisation needed.

5. **Forces clean abstractions.** When you can't add a per-process doctype, you have to express the process declaratively via the Console Process Template. This forces meta-thinking about what's truly variant vs invariant.

### Permitted exceptions (current state)

Dedicated Ops handlers exist only where the generic TransactionEngine genuinely can't express the logic. Each exception has a documented reason:

| Handler | Reason for exception |
|---|---|
| `submit_cut_bit_transfer(context, run_legacy_sync=False)` | Asset retirement + batch auto-creation patterns specific to legacy expectations |
| `bulk_release_clips(barcodes=[...])` | Clip state machine (sheeted → released → blanking-eligible) needs imperative logic |
| `submit_blanking_dc_entry(context)` | Asset Movement (Receive Bin) + branching for cut-bit repack mode |

**All other processes** (Mixing, Inspection, Sheeting) use the generic `TransactionEngine`. New processes default to the generic engine; a dedicated handler must be justified in a `10-risks-and-decisions.md` entry before being added.

### What this rules in

- Adding a new process: write a new `Console Process Template` with appropriate `actions` rows; the generic engine creates the right native documents
- Adding a new action verb to the engine (e.g. `submit_sub_lot`) when the existing verbs can't express something
- Using native ERPNext features (Batch auto-creation, Stock Ledger reconciliation, Production Plan reports)

### What this rules out

- Creating an Ops doctype like `Ops Compound Mixing` or `Ops Cut Bit Entry`
- Adding a custom controller hook on Stock Entry that branches on the source process
- Bypassing the TransactionEngine for performance reasons without architecture review

---

## Principle 3 — Parallel sync, eventual consistency

**Statement:** Legacy and Ops sync legs run in parallel via separate HTTP calls from the Dash. There is NO two-phase commit. Console's `sync_status` aggregate is the single source of truth for "did both legs land." Operator-driven retry is the recovery mechanism.

### What this means concretely

| Scenario | System behavior |
|---|---|
| Both legs succeed | `sync_status="Success"`, `docstatus=1` (auto-submit), operator sees ✅ ✅ |
| Both legs fail | `sync_status="Failed"`, `docstatus=0`, operator sees ❌ ❌ + retry buttons |
| One succeeds, one fails | `sync_status="Partial"`, `docstatus=0`, operator sees ✅ ❌ + retry for failed leg |
| Successful leg's record exists on its ERP; failed leg's record does NOT exist | This is correct — no transactional rollback |
| Retry attempt on failed leg | Idempotent: same `reference_id` returns cached result if it succeeded somehow; otherwise re-attempts |

### Rationale

1. **Shop-floor speed.** Sequential sync (Legacy → wait → Ops) would double submission latency. At 50–100 submissions per shift, that's 5–15 minutes of operator wait time daily. Parallel halves it.

2. **Either-ERP independence.** Either bench can be taken down for maintenance without blocking the other. Legacy upgrades, Ops upgrades, Bridge restarts — none halt operations entirely.

3. **Simple recovery model.** Compensating-transaction logic across two ERPs is high-risk. Operator-driven retry with idempotent legs is verifiable and debuggable.

4. **Eventual consistency is acceptable for SPP's data model.** Inventory levels diverge by seconds during normal operation. Shift-end reconciliation surfaces persistent drift.

### What this rules in

- Per-leg failure modes (Partial state is normal, not exceptional)
- Operator-driven retry from the Dash success modal or `Console Transaction Log` list view
- Idempotency at every layer (Console doctype unique constraint, Bridge `find_existing_record`, Ops MES Log lookup)
- The 5-step race-safe pattern in `apply_bridge_result` (every Wave 1+ Console doctype uses it byte-identically)

### What this rules out

- Two-phase commit across Legacy and Ops
- Automatic rollback of a successful leg when the other leg fails
- Blocking submissions while one ERP is unavailable
- Treating `sync_status="Partial"` as a system failure (it's an operationally normal state)

### The trade-off this principle accepts

- A window of seconds-to-minutes during ERP outages where the two ERPs disagree on state
- Operator awareness required for retry (not auto-retry — see [01 §Non-goals](01-vision-and-goals.md))
- Periodic reconciliation needed (currently manual; future automated dashboard)

---

## Principle 4 — Legacy preservation (read-only future, not deleted)

**Statement:** The Legacy ERPNext install remains operational for the duration of the porting program and for the foreseeable future after. Legacy is the **historical reference** install. Custom doctypes are preserved; reports keep working; pre-Console submissions remain visible.

### Why we don't delete Legacy

1. **Years of historical data.** Production records, customer transactions, audit trails — all of it lives in Legacy. Migrating it is a separate epic (out of program scope).

2. **Downstream reports.** Many internal and external reports query Legacy doctypes directly. Re-pointing them is a separate epic.

3. **Modules out of program scope.** Accounting, HR, Procurement, and Sales modules run on Legacy and are not part of the manufacturing porting effort.

4. **Risk mitigation during cutover.** Keeping Legacy live means any unforeseen issue with Console or Ops can be resolved by falling back to legacy Desk submission temporarily (operator-initiated, not automated).

### Eventual state (post-program)

- Legacy custom doctypes for ported processes (DCR, Compound Inspection, Material Transfer, Cut Bit Transfer, Blanking DC Entry, MPE) become **read-only** — populated only by the Bridge, never directly by operators
- Legacy Desk forms for these doctypes either remain accessible for read-only viewing OR are hidden via permissions
- Historical legacy records remain queryable
- No removal of any legacy doctype during the program (preserves report compatibility)

### What this rules in

- Bridge writes to Legacy with full fidelity (legacy doctype semantics preserved)
- Legacy controllers continue to fire on submit (e.g. `create_master_batch_stock`, `create_wo_final_batch_mixing`, etc.)
- Legacy Stock Ledger Entries continue to be authoritative for legacy reports

### What this rules out

- Disabling legacy doctype submission during the porting program
- Removing legacy custom controllers or replacing them with no-ops
- Deleting historical legacy records "to make space"

---

## Principle 5 — Test gate before production push

**Statement:** No code change to Console / Bridge / Ops ships to `iyyanarr/develop` (or equivalent) without all relevant tests passing first.

### Test surfaces

| Layer | Test types |
|---|---|
| Console doctype controller | Unit (`bench run-tests --module ...`); concurrency tests for `apply_bridge_result` changes |
| Console api.py functions | Unit + integration |
| Console mapping seeder | Smoke (verify mappings seeded after install) |
| Console Dash React component | E2E (Playwright happy path) |
| Bridge `sync_process_transaction` + populate functions | Unit on the Legacy bench |
| Ops `process_transaction` + dedicated handlers | Unit on the Ops bench |
| Cross-system integration | Per-process scenario test (see `06_INTEGRATION_TESTS_TODO.md`) |

### Rationale

The Compound Deviation saga of 2026-04-29 → 2026-05-01 (documented in [`../02-specifications/compound-deviation/09-rollout-and-history.md`](../02-specifications/compound-deviation/09-rollout-and-history.md)) established the test gate after multiple sequential fixes shipped without coverage, each introducing new races.

### What this rules in

- Concurrency tests for any `apply_bridge_result` change
- A smoke test after every Bridge mapping seeder change
- An E2E happy path for any Dash component change
- One staging end-to-end submission per change before push

### What this rules out

- Syntax-check-only validation as a substitute for tests
- "Quick fix, no tests" pushes
- Pushes from worktrees without a bench attached to run tests (commit locally, prepare test command, wait for user go-ahead)

---

## Principle 6 — Spec + requirement alignment (cockpit hygiene)

**Statement:** Every code change to a manufacturing-chain module must update the corresponding cockpit spec AND traceability entry in the same PR. The cockpit is a living document, not an after-the-fact archive.

### Workflow

1. Hermes worker proposes a change
2. Reviewer identifies affected spec sections (via `02-specifications/<process>/`) AND affected requirements (via `01-requirements/<motion>/08-traceability.md`)
3. PR must include:
   - The code change
   - Updates to affected spec sections
   - Updates to `08-traceability.md` if any requirement's implementation status changed
   - A drift-findings entry if a new gap is discovered

### What this rules in

- Spec + traceability updates as part of the change (not "we'll document it later")
- New requirements created when shipped behavior introduces intent not previously captured

### What this rules out

- "Pure code" PRs that bypass cockpit updates
- Cockpit-only PRs that document changes that haven't shipped yet (cockpit reflects shipped reality; planned behavior is in plan docs)

---

## When principles conflict

If two principles seem to conflict, the order of authority is:

**Principle 1 (Console as SoR) > Principle 5 (Test gate) > Principle 2 (Native ERPNext) > Principle 3 (Parallel sync) > Principle 4 (Legacy preservation) > Principle 6 (Cockpit hygiene)**

Example conflict: a Wave 5 MPE requirement could benefit from a custom Ops doctype to express partial-bin handling cleanly (violating Principle 2). The resolution: stick to Principle 2 (use the generic engine or a dedicated handler with documented justification), don't add a custom Ops doctype. Principle 2 wins over expedience.
