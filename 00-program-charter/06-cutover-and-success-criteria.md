# 06 — Cutover and success criteria

This file defines how the porting program ends — what "done" looks like, what stays out of scope, and what triggers a program-level decision.

## Cutover model

### Per-stage cutover (the standard)

For each stage in the manufacturing chain:

1. **Build phase** — Console doctype + Dash component + Bridge mapping + Ops sequence/handler implemented
2. **Local test phase** — All unit tests pass; smoke test on `sppconsole-dev.local` succeeds
3. **Integration test phase** — Per-process scenario test passes across all three sites (Console + Ops + Legacy)
4. **Staging cutover** — Deployed to `console.m.frappe.cloud`; operators start submitting on Dash; legacy Desk submission still available as fallback
5. **Monitoring phase** — Minimum 2 weeks of operations. Watch:
   - `Console Transaction Log` for `Failed` / `Partial` rate
   - Reconciliation reports for Stock Ledger drift
   - Operator feedback on UX pain points
6. **Hard cutover** — Legacy Desk submission for that stage is disabled (operators must use Dash). Legacy doctype becomes read-only (populated only by Bridge).

### What this is NOT

- **Not a big-bang cutover** for all 13 stages at once
- **Not a parallel-running indefinite period** where operators choose Dash or Desk freely
- **Not a feature-by-feature rollout** within a stage — each stage cuts over as a complete unit

### Why per-stage

- Bounded blast radius if issues emerge
- Operators learn one new flow at a time
- Reconciliation surfaces stage-specific issues before the next stage cuts over
- Failure of one stage doesn't block the others (e.g. MB Mixing can be live while Sheeting is still in build phase)

## Program-level success criteria

The porting program is declared **successful** when ALL of the following hold:

### Functional success

- ✅ All 13 manufacturing stages (Stages 1–12 plus Compound Deviation overlay) have:
  - A working Console Dash submission flow
  - Successful dual-ERP sync (Legacy + Ops) under normal conditions
  - Integration test coverage (per-process scenario passing)
- ✅ No operator at SPP India submits any of these stages on legacy Desk for routine production (Desk available only for historical lookup)
- ✅ Stock Ledger Entries on Legacy and Ops agree (within tolerance) at shift-end for at least 4 consecutive weeks
- ✅ Every successful submission produces a complete audit trail (Console doc + 2 Transaction Logs + Legacy Bridge Log + Ops MES Log)

### Architectural success

- ✅ Ops contains **only native ERPNext doctypes** for manufacturing transactions (Stock Entry, Work Order, Job Card, Batch, Asset/Asset Movement) — verified by audit
- ✅ Console Process Template + generic TransactionEngine handles all process types except the documented exceptions (Cut Bit, Bulk Clip Release, Blanking DC Entry)
- ✅ The 5-step race-safe `apply_bridge_result` pattern is implemented byte-identically across all Wave 1+ Console doctypes
- ✅ Console-generated identifiers (`reference_id`, `mix_barcode`, `Lot #`, MPE batch `T-...`) round-trip to both ERPs without drift

### Operational success

- ✅ Bridge uptime > 99% during shift hours (monitored)
- ✅ Average end-to-end submission latency < 30 seconds (measured)
- ✅ Operator-reported error rate per submission < 1% (tracked via Console Transaction Log Failed status)
- ✅ Mean Time to Recovery for Partial sync state < 5 minutes (operator-driven retry)
- ✅ Production overseer signs off in writing (Obsidian note at `/Users/alphaworkz/claude-obsidian/claude/`)

### Cockpit completion

- ✅ All 13 specifications in `02-specifications/` are complete and accurate against shipped code
- ✅ All 6 requirements motions in `01-requirements/` are complete with stakeholder-validated business rules
- ✅ Traceability tables show ≥ 95% of requirements implemented (the remaining 5% are intentionally-deferred decisions, documented as such)
- ✅ This charter is signed off as the authoritative program statement

## Program-level failure criteria

The porting program would be declared **failed** (rollback to legacy-only) if any of the following persist despite mitigation:

- Submission success rate drops below 95% for any stage across a full week
- Stock Ledger drift between Legacy and Ops cannot be reconciled within tolerance for 2+ consecutive weeks
- Operator productivity declines vs the pre-port baseline (measured at 3 months post-cutover)
- A single-source-of-failure issue causes data loss not recoverable from logs
- Architecture fundamentals (Console as SoR, native ERPNext on Ops) cannot be sustained without violating principles

Failure is unlikely given the existing shipped state (Waves 1 + Phases 1-4 are operational); this section exists for completeness and to define the rollback bar.

## What's explicitly NOT in this program (out of scope)

### Out of scope — features

- **Real-time inventory consistency across ERPs** — eventual consistency accepted (Principle 3)
- **Automatic rollback on Partial sync** — operator retry is the recovery mechanism
- **Backfill of pre-Console legacy historical data into Console** — Legacy keeps its history
- **Console multi-site deployment** — single-site (SPP India) for v1
- **Console multi-tenant** — not in program
- **PLC / sensor integration** — separate future epic
- **Mobile-app version of Console** — Dash on tablets is sufficient
- **Localisation** — English-only

### Out of scope — modules

These ERPNext modules run on Legacy and are NOT touched by this program:

| Module | Stays on |
|---|---|
| Accounting (GL, AP, AR) | Legacy |
| Procurement / Purchasing | Legacy |
| Sales / Customer Management | Legacy |
| HR (employee records, attendance, payroll) | Legacy |
| Project Management | Legacy |
| CRM | Legacy |
| Quality Management (outside the manufacturing chain) | Legacy |

The porting program touches ONLY the manufacturing chain (Stages 1-12). Anything else stays as-is.

### Out of scope — operations

- **Legacy ERPNext upgrade** to a newer version
- **Database migration** from MariaDB to another DB
- **Frappe Cloud → self-hosted** migration
- **CI/CD overhaul** beyond what `build-dash.yml` already does
- **Production monitoring tooling** (Grafana, Datadog, etc.) — separate ops backlog
- **Audit / SOC compliance work** — separate compliance epic

### Out of scope — downstream stages

The chain continues beyond MPE (Stage 12) for these stages:

- Deflashing
- Receive Deflashing
- Sub Lot Creation
- Lot Resource Tagging
- Packing
- Dispatch

These remain on Legacy Desk. May be addressed in a **separate, future** porting program. NOT part of this charter.

## Decision authority

| Decision type | Who decides |
|---|---|
| Promote a stage from staging cutover to hard cutover | Production overseer + Shop Floor Supervisor sign-off |
| Modify this charter | Production overseer (with reasoning logged in change log below) |
| Add a stage to program scope | Production overseer + Engineering Lead (must trace to Goal 1-5) |
| Remove a stage from program scope | Production overseer (rare; would require strong justification) |
| Approve a new dedicated Ops handler (Principle 2 exception) | Production overseer + Engineering Lead, with documented justification |
| Approve a Bridge mapping value-map change | Engineering Lead — must include test before push |
| Approve a Console doctype field rename | Production overseer — coordinated change across all layers |

## When a stage's port can ship

For each stage, the gate to mark "✅ Shipped" is:

- [ ] Spec exists in `02-specifications/<process>/` (11 files)
- [ ] Spec is technically accurate against current code (verified by independent reviewer)
- [ ] Motion-level requirement exists in `01-requirements/<motion>/` (9 files)
- [ ] All shipped unit tests pass
- [ ] Recommended unit test additions (concurrency, value-map, etc.) implemented
- [ ] Integration test (per-process scenario) passing across 3 sites
- [ ] Operator UAT (the AC-XXX-NNN scripts) executed and signed off
- [ ] Staging cutover deployed; minimum 2-week monitoring period
- [ ] Legacy Desk submission disabled for the stage (hard cutover)
- [ ] Drift findings in `08-traceability.md` reviewed and dispositioned (kept, fixed, or accepted)

## Change log for this charter

| Date | Change | Reason | Author |
|---|---|---|---|
| 2026-05-11 | Initial charter created | Establish program-level vision after motion-level requirements pilot revealed the missing top layer | Production overseer + Claude session |
| | | | |

When future changes happen, add entries here with date, description, reason, author. Casual rewording is not acceptable — charter changes are deliberate decisions.

## Final word

This charter exists so that, three years from now, an engineer joining SPP can read 6 files and understand:

- WHY the dual-ERP architecture exists
- WHY Console is the system of record
- WHY Ops uses only native ERPNext doctypes
- WHY parallel sync over 2PC
- WHAT defines the program's manufacturing scope
- WHAT defines the program's "done"

Everything else in the cockpit serves this baseline understanding. If something in the specs or requirements contradicts the charter, the charter wins and the contradicting artifact gets revised.

This is the durable layer.
