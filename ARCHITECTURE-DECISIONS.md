# SPP Porting Cockpit — Architecture Decision Records

> **Purpose:** Capture the load-bearing architectural decisions that govern the
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

**Date:** 2026-05-12 documented · **Resolved 2026-05-29 — Option A (unify on Legacy semantics).**
**Status:** Resolved. Ops creates Asset Movement only; no Stock Entry path. `Item Bin Mapping` is Console-state + Bridge-mirrored to legacy. Achieved declaratively via the `BLANKING_DC_ENTRY` Console Process Template + the engine's `_normalise_asset_movement_locations` helper. See [`02-specifications/blanking-dc-entry/06-ops-erpnext.md`](02-specifications/blanking-dc-entry/06-ops-erpnext.md).
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

## ADR-006 — Zero Logic in Ops (Console-as-Brain)

**Date:** 2026-05-15
**Status:** Accepted — load-bearing invariant
**Motion(s):** All Console processes

### Context

During the initial porting phases, process-specific business logic (e.g., barcode generation, batch resolution, and sheeting validation) was embedded directly into the Ops execution layer (`shree_polymer_ops/api.py`). This led to an architectural contradiction: the Console was designed to be the central "brain", but Ops was still making execution-time decisions. This confused both developers and AI agents, causing them to mistakenly assume new processes required writing custom Python logic in Ops.

### Decision

**Ops must be a "Zero Logic" thin execution layer. The Console is the exclusive brain.**

All business rules, variable resolution, batch mapping, and conditional logic must be executed by the `shree_polymer_console` BEFORE a transaction payload is dispatched. The payload sent to Ops must be a fully resolved, declarative sequence of standard actions (`create_doc`, `submit_doc`, etc.).

```python
# BR-ARCH-006 — Zero Logic in Ops
# Ops TransactionEngine is forbidden from containing process-specific methods.
# Example: NO `_handle_sheeting_pre_save()`. 
# If a process requires special logic, the Console template or Console API must resolve it.
```

### Consequences

| | |
|---|---|
| **Enforced** | Ops remains purely generic and highly resilient. New processes can be launched via Console JSON templates without deploying any new Python code to Ops. |
| **Not enforced** | Ops becomes a tangled web of legacy hooks, causing divergence between what the Console thinks happened and what Ops actually executed. |

### Migration Note
All legacy process hooks (`_handle_sheeting_pre_save`, `_process_stock_entry_pre_save`, etc.) have been surgically stripped from `shree_polymer_ops/api.py` as of May 2026. Future contributors must not reintroduce them.

---

## ADR-007 — Rack Locations Are Child Warehouses, Not an Inventory Dimension

**Date:** 2026-09-19
**Status:** Accepted — load-bearing (supersedes the 2026-09-04 "rack as Ops Inventory Dimension" decision)
**Motion(s):** FIFO Rack Locations for the Unit-3 storage area: master batch in `Mixing - SPP`, accepted compound in `Compound - SPP`. Planning map: iyyanarr/shree_polymer_console#265.

### Context

The "FIFO screen – MB storage area" requirement puts master batch and accepted compound onto barcoded rack slots (`8C` …), with standalone FIFO **Check-In** and **Check-Out** screens. FIFO order follows the mixing moment, and a supervisor approves exceptions. The racks stand physically inside the stores. Downstream processes (Final Batch Mixing, Sheeting) must not be FIFO-gated.

The first design (2026-09-04) made the rack an **ERPNext Inventory Dimension** on the ledger *inside* the existing store warehouse, the same pattern Ops uses for the Deflashing Vendor. Rolled-back proofs on local Ops (tickets #267 and #268 on the map) showed it works mechanically, but it breaks down at the edges:

- Downstream scans find stock by warehouse and post rows with **no** rack. ERPNext's per-dimension negative-stock check skips empty values and counts per *item + rack*, not per batch. So a racked batch used downstream without a Check-Out leaves **phantom stock** on its rack.
- Clearing a phantom can't be done with a move: that's refused with `BatchNegativeStockError`. It needs a no-location Material Receipt followed by a Material Issue. That nets to zero value but books gross *Inventory ↔ Stock Adjustment* postings for every clear.
- The design therefore needed a Blocked state, a manager clear, adjustment postings, a separate Console rack table, and a new Ops `get_rack_balances` endpoint. That endpoint would have been custom Ops logic, against ADR-006.

### Decision

**Each rack slot is a leaf warehouse under a per-store group warehouse.** (Slot warehouse names below are illustrative; slot ids are still open on the map.)

```
MB Racks - SPP        (group)  →  MB 8C - SPP, MB 8A - SPP, …        (leaves)
Compound Racks - SPP  (group)  →  C 8C - SPP,  C 8A - SPP,  …        (leaves)
Mixing - SPP, Compound - SPP   →  unchanged leaves (the stores)
```

- **Check-In** = Material Transfer store → slot. **Check-Out** = Material Transfer slot → store. Console resolves both and dispatches them as plain, declarative stock entries (ADR-006).
- **Downstream sees only the stores.** Sheeting's compound scan is already limited to `Compound - SPP`. The Master Batch Mixing and Final Batch Mixing scans pass their source warehouse, `Mixing - SPP`, to `validate_rm_barcode`, which already supports it. This is the **only** downstream change, and it would have refused none of the real past consumptions (all came from `Mixing - SPP`).
- At Check-Out, a supervisor's badge and a reason may approve an **out-of-turn** batch and/or **immature** compound. Each approval is logged separately.
- FIFO order (Mix Moment, then the serial in the mix barcode) is computed in Console. ERPNext's native batch FIFO orders by `Batch.creation` per warehouse and is not used.

### Options considered

| Option | Why not / why |
|---|---|
| **A — Inventory Dimension inside the store warehouse** (2026-09-04) | Phantom stock whenever downstream uses a racked batch, so it needs a Blocked state, a manager clear with Stock Adjustment postings, a separate rack table, and an Ops endpoint. |
| **B — Dimension pointing at ERPNext's `Location` tree** | Same phantom problem. `Location` is also the asset master on Ops (876 assets, 1,578 asset movements), is GIS-oriented, and commits mid-transaction when a child location is edited. |
| **C — Child leaf warehouse per slot** ✅ | The ledger itself keeps racked stock out of downstream reach, so phantom stock can't exist. It uses only native stock entries and reports. |

### Consequences

| | |
|---|---|
| **Enforced** | Racked stock can only leave through FIFO Check-Out. No phantom stock, Blocked state, manager clear or adjustment postings. Racked stock is ordinary Console Stock Cache rows under the slot warehouses, so no separate rack table and no new Ops endpoint. |
| **Cost** | One warehouse per slot, to be created at go-live and added to the stock sync. |
| **Permanent** | `Mixing - SPP` and `Compound - SPP` stay leaves. ERPNext refuses to turn a warehouse with stock history into a group, and group warehouses can't transact, so stock never moves between a parent and its child. |
| **Not a precedent against dimensions** | The Deflashing Vendor stays a dimension. The only process that takes stock out of `Deflashing Vendors - SPP` is deflash receiving, which names the vendor, so no untagged row can strand vendor stock. |

**Do not reintroduce a rack dimension, or give downstream scans access to rack warehouses, without revisiting this ADR.**

---

## Change Log

| Date | ADR | Change | Author |
|---|---|---|---|
| 2026-05-12 | All | Initial ADR log drafted from cockpit traceability cross-validation | Architect mode session |
| 2026-05-15 | ADR-006 | Added Zero Logic in Ops mandate | Architect mode session |
| 2026-09-19 | ADR-007 | Rack Locations are child warehouses, not an inventory dimension (supersedes the 2026-09-04 decision) | Wayfinder session, map shree_polymer_console#265 |
