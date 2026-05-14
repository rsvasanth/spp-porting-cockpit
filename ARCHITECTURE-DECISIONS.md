# SPP Porting Cockpit — Architecture Decision Records

> **Purpose:** Capture the 5 load-bearing architectural decisions that govern the
> Console MES porting project. These are the decisions that would require
> significant rework if reversed. Each ADR is a standalone record. Hermes workers
> and reviewers should read this before touching any cross-cutting concern.

---

## ADR-001 — Mass Balance NOT Enforced on Backend

**Date:** 2026-04 (implicit — first production use of MB/FB mixing)
**Status:** Accepted — deferred enforcement
**Motion(s):** Mixing (`mixing-process/`)

### Context

The mixing processes (Master Batch and Final Batch) have a physical mass balance
invariant: compound consumed = compound produced. Deviations from this balance
were initially treated as errors requiring operator correction.

Production reality: deviations are real signals. Operators were falsifying
entries to pass mass-balance checks rather than reporting actual variance.

### Decision

**Do NOT enforce mass balance on the backend.** The Dash may show a soft
warning (5% tolerance), but the Console controller and Bridge MUST NOT block
submission based on mass variance.

```python
# BR-MIX-002 — mass balance NOT enforced
# Rationale: deviations are real production signals that should land
# rather than block. Blocking forces falsification.
```

### Consequences

| | |
|---|---|
| **Enforced** | Deviations land in the system; QA can see real variance |
| **Not enforced** | No automatic detection of weighing errors or material loss |

### Alternatives considered

| Alternative | Rejected because |
|---|---|
| Strict mass balance with tolerance | Tolerance is site-specific and creates false confidence |
| Operator override flag | Adds friction; doesn't solve the falsification incentive |

### Review trigger

If SPP Settings gains a `strict_mass_balance` flag and production overseer
approves, revisit. Until then, treat this as invariant.

---

## ADR-002 — Parallel Sync, Not Two-Phase Commit

**Date:** 2026-04 (implicit — architecture design)
**Status:** Accepted — load-bearing
**Motion(s):** All Console processes

### Context

Console submissions must be recorded on two parallel ERPs (Legacy v15 and Ops v15).
A naive approach would use distributed transactions (2PC) to guarantee atomicity:
both succeed or both fail.

However, Legacy and Ops are independent ERPNext instances with no shared
transaction coordinator. Enforcing 2PC would require either a shared lock
manager or coarser locking that blocks shop-floor operations.

### Decision

**Use eventually consistent parallel sync. Do NOT use two-phase commit.**

```
Console submission
  ├── Legacy Bridge (async, independent)
  │     └── Success or failure recorded per-target
  └── Ops MES Transaction Engine (async, independent)
        └── Success or failure recorded per-target

Console aggregates results via 5-step apply_bridge_result.
Auto-submit only when both legs report Synced.
```

### Consequences

| | |
|---|---|
| **Benefit** | Each leg is independently recoverable; shop floor not blocked by one system's latency |
| **Risk** | Transient split-brain state: one leg synced, one leg pending |
| **Risk** | A failed leg requires manual reconciliation or retry |

### How split-brain is managed

The 5-step `apply_bridge_result` atomic dance (first proven in the Compound
Deviation saga 2026-04-29 → 2026-05-01) closes the race:

```
Step 1: Read both leg statuses from Transaction Log (read-committed)
Step 2: Determine if both are terminal (Synced / Failed)
Step 3: If both terminal — set console docstatus
Step 4: If one pending and one failed — flag for retry
Step 5: If both Synced — submit console doc
```

### Alternatives considered

| Alternative | Rejected because |
|---|---|
| 2PC with shared lock manager | Requires infrastructure not available between independent ERPs |
| Sync in series (Legacy then Ops) | Latency unacceptable for shop-floor scan workflow |

---

## ADR-003 — Console as Single Barcode Authority

**Date:** 2026-04 (implicit — first barcode generation)
**Status:** Accepted — load-bearing invariant
**Motion(s):** Master Batch Mixing, Final Batch Mixing, Sheeting

### Context

Compound batches are identified by barcode throughout the shop floor. Both
Legacy and Ops need to reference the same batch identity. If each system
generates its own batch number, identity diverges — a scan on the shop floor
resolves to different batches on each system.

### Decision

**Console generates all batch barcodes. Legacy and Ops MUST honor the
Console-generated barcode.**

Barcode format: `C_YYMMDDXn` (Console prefix + date + sequence)

```
Console creates local audit record
  └── Writes bridge_mix_barcode to local doc
  └── Passes to both Legacy Bridge and Ops
Legacy Bridge honors bridge_mix_barcode → skips own batch generation
Ops honors the same barcode → consistent identity
```

Single barcode authority invariant:
```python
# BR-MIX-005 — Console as single barcode authority
# bridge_mix_barcode written to Console doc
# Legacy honors and skips generation when reference_id is set
# Ops uses same barcode for Stock Entry
```

### Consequences

| | |
|---|---|
| **Enforced** | Batch identity is consistent across all 3 systems |
| **Not enforced** | Batch divergence → inspection lookup failures, rejection cascade breaks |

### How this extends beyond barcodes

The same pattern applies to all cross-system identity fields:
- `reference_id` — idempotency key (13-digit Date.now(), Console-generated)
- `mix_barcode` — compound identity for inspection lookup
- `spp_batch_number` / `spp_batch_no` — production lot identifier (field name drift exists — see CBT spec)

### Alternatives considered

| Alternative | Rejected because |
|---|---|
| Legacy generates; Console and Ops follow | Legacy is the legacy system; its batch generation doesn't scale |
| Ops generates; others follow | Ops is the newer system; Console is the shop-floor authority |

---

## ADR-004 — Consolidate IE → MPE Batch Cascade Functions

**Date:** 2026-05-12 (documented — unresolved)
**Status:** Proposed — awaiting production overseer decision
**Motion(s):** Inspection Entry + Moulding Production Entry

### Context

There are **two distinct functions** that perform the same physical cascade
operation (updating inspection entry rejection Stock Entries with the MPE
produced batch number):

| Function | Location | Cascade scope |
|---|---|---|
| `submit_inspection_stock_entries_from_moulding` | MPE controller | Line + Patrol IE |
| `submit_inspection_stock_entry_immediately` | IE controller | Line + Lot + Patrol IE |

**Trigger conditions differ:**
- MPE cascade fires when MPE's `on_submit` calls its helper
- IE cascade fires when IE's `on_submit` trigger query finds Line + Lot ≥ 2

**The inconsistency:**
IE `on_submit` comment says Patrol is included in trigger query.
Executable SQL checks only `Line OR Lot` — Patrol excluded.
Cascade function includes Patrol.

### Decision (pending)

| Option | Description | Recommendation |
|---|---|---|
| **A — Consolidate** | One cascade function, owned by one doctype | **Recommended** — removes double-cascade risk |
| **B — Coordinate scopes** | MPE: Line + Patrol. IE: Line + Lot. Non-overlapping. | Achievable but requires explicit ownership boundary |
| **C — Add MPE existence guard** | IE cascade fires only when MPE exists and has stock_entry_reference | Safe fallback but doesn't reduce redundancy |
| **D — Document as intentional** | MPE fires first (Line+Patrol), IE fires on Line+Lot | Works but fragile; cascades can fire in unexpected order |

### Recommended path (Option A)

1. Choose one function as the canonical owner — recommend MPE side (since MPE
   is the batch producer)
2. IE `on_submit` does NOT call its cascade helper
3. MPE cascade adds Lot to its scope (currently Line + Patrol)
4. Result: one function, all three types covered, one trigger (MPE submit)

### Blockers

- Production overseer must confirm Lot IE should be included in cascade
- IE Drift A (Patrol excluded from trigger query) must also be resolved

---

## ADR-005 — Blanking DC Entry Target Semantics: Ops ≠ Legacy

**Date:** 2026-05-12 (documented — unresolved)
**Status:** Known drift — production architecture decision needed
**Motion(s):** Blanking DC Entry

### Context

Blanking DC Entry (BDE) is the process of filling a physical blanking bin from
a released sheeting clip. On Legacy, this creates:
- `Item Bin Mapping` (bin-content identity)
- `Asset Movement` (physical bin movement)

On Ops, BDE creates:
- `Stock Entry` from Cutbit warehouse to PreForming warehouse

These are fundamentally different material movements. The Legacy story is
clip-to-bin mapping + Asset Movement. The Ops story is Stock Entry transfer.

### The drift

```
Legacy path (what Dash/Console model):
  Scan clip → resolve active Item Clip Mapping
  → create Asset Movement (bin receive)
  → create Item Bin Mapping (bin content identity)

Ops path (actual code):
  submit_blanking_dc_entry(context)
  → creates Stock Entry (Cutbit WH → PreForming WH)
  → uses CB_<compound>_<spp_batch> batch naming
```

### Decision required

| Option | Description |
|---|---|
| **A — Unified Legacy semantics** | Ops should also create Asset Movement + Item Bin Mapping. Stock Entry is not the right abstraction for clip-to-bin. |
| **B — Accept divergence** | Document that Ops BDE is a different operational flow (repack path), not a parallel implementation of the same event. |
| **C — Redesign BDE for both targets** | BDE on Console creates two distinct events: (1) clip-to-bin on Legacy, (2) cutbit-to-preforming on Ops. Treat as separate process templates. |

### My recommendation

Option B — Ops BDE and Legacy BDE are serving different operational needs.
Legacy BDE is bin preparation for moulding. Ops BDE is cutbit stock transfer.
Do not force them into the same abstraction. Document the divergence and let
each target implement its own semantics.

**Do not add an Ops leg for BDE without a formal architecture review.**
Adding Ops participation without resolving the semantic gap will create
inconsistency that downstream Blanking Bin Issue, Moulding Production Entry,
and Inspection Entry will have to compensate for.

---

## Change Log

| Date | ADR | Change | Author |
|---|---|---|---|
| 2026-05-12 | All | Initial ADR log drafted from cockpit traceability cross-validation | Architect mode session |
