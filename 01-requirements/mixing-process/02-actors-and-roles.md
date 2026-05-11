# 02 — Actors and roles

## Primary actors

### Mixing Operator (Sheet/Master Batch/Final Batch)

The operator who runs the mixing mill and submits the record.

| Aspect | Detail |
|---|---|
| Console role name | `Mixing Operator` |
| Where active | Two Roll Mixing Mill, Avon Kneader, and similar workstations |
| Console access | Dash UI only (no Desk access) |
| Console permissions | Create + Submit on `Console Master Batch Mixing` and `Console Final Batch Mixing` |
| Decision rights | Selects produced item from allowed item groups; selects raw materials by scanning barcodes; enters produced qty |
| Constraint | Cannot backdate posting time beyond "yesterday" |

**What the Mixing Operator needs from the system:**

- A scan-driven UI that requires no typing for the common case
- Real-time feedback on whether the submission succeeded on each ERP (the Live Feedback pattern)
- A printable barcode label for the produced batch immediately on success
- A clear retry path if one of the legs fails
- Tolerance for partial Dash payloads (e.g. operator forgets a field) — the system should still capture an audit record rather than silently dropping the event

### Quality Inspector

Inspects the mixed compound for QA conformance (next stage after Mixing).

| Aspect | Detail |
|---|---|
| Console role name | `Quality Inspector` |
| Console access | Dash + limited Desk |
| Permissions on Mixing records | Read-only (does NOT submit Mixing records) |
| Why they need read access | To verify the lot exists before opening a Compound Inspection |

### Quality Manager

Approves deviations on rejected compound lots (handled by separate Compound Deviation requirement; in scope here only for permission visibility).

| Aspect | Detail |
|---|---|
| Console role name | `Quality Manager` |
| Permissions on Mixing records | Read + create + submit (for backdating/correction cases) |

### System Manager / Administrator

Production overseer + Frappe admin role.

| Aspect | Detail |
|---|---|
| Console role | `System Manager` / `Administrator` |
| Permissions | Full CRUD on Mixing records |
| Special capability | Can backdate `posting_date` / `posting_time` arbitrarily (regular operators are clamped) |
| Usage pattern | Late entry corrections, audit reconstruction, training/test submissions |

## Secondary actors

### Shop Floor Supervisor

Reviews mixing throughput and deviations at shift-end. Not a direct system user; consumes reports.

**What they need from the system:**

- Per-shift summary of submitted mixings (count, qty, by workstation, by operator)
- Visibility into `sync_status` distribution (mostly Success; Partial / Failed surface incidents)
- Drill-down from a Partial record to see which leg failed and why

### Compound QA Lead

Sets the spec rules that Compound Inspection runs against. Indirect actor here — the QA Lead's spec rules drive whether the next-stage CI accepts or rejects the lot.

**What they need from this process:**

- Every Mixing record's identity (mix_barcode + spp_batch_no) must be traceable to the source Compound Inspection (via downstream lookups)
- Cut-bit batches (from Sheeting recycling) must trace back to the original Mixing record's batch

### Inventory / Stock Controller

Reconciles Stock Ledger Entries between Legacy and Ops at shift-end.

**What they need from this process:**

- For each successful Mixing, equivalent Stock Ledger Entries exist on both Legacy and Ops with matching qty
- Partial sync records are visible (currently via `Console Transaction Log`; long-term: a reconciliation dashboard)

## Non-human actors (system roles)

### Console Dash (React app)

| Responsibility | What it must guarantee |
|---|---|
| Operator-facing UI | Sub-second scan-to-validation feedback |
| Payload construction | Canonical shape that Console backend accepts |
| Live Feedback orchestration | `Promise.all([executeStep(Legacy), executeStep(Ops)])` — both legs in flight in parallel |
| Retry UX | Rebuilds request from `Console Transaction Log` so retry is idempotent |

### Console Backend (Frappe / Python)

| Responsibility | What it must guarantee |
|---|---|
| Local audit record | Every submission lands a `Console *` record, even if Dash payload is partial |
| Cross-system idempotency | `reference_id` (13-digit ms timestamp) unique across Console; respected by Bridge + Ops |
| Race-safe callback handling | The 5-step `apply_bridge_result` pattern aggregates leg state correctly under concurrent callbacks |
| Auto-submit on full success | Console doc moves Draft → Submitted only when BOTH legs report Synced |

### Legacy Bridge (Frappe app on Legacy bench)

| Responsibility | What it must guarantee |
|---|---|
| Mapping resolution | Reads `Legacy Sync Mapping` rows + applies value-maps to build the legacy DCR |
| Process-specific enrichment | Defaults that the mapping engine can't express (`bridge_mix_barcode` honor, etc.) |
| Idempotency on legacy side | Re-runs for same `reference_id` return cached result, don't duplicate DCR |
| Submit-and-return | Submits the DCR (triggers legacy SE creation chain) and returns the document name |

### Ops MES Transaction Engine

| Responsibility | What it must guarantee |
|---|---|
| Generic action execution | Reads sequence from `Console Process Template`, runs each action with placeholder resolution |
| Stock Entry creation | Builds Manufacture-purpose SE with the right warehouses, items, and FG barcode |
| Idempotency | `Shree Polymer MES Log` lookup by `reference_id` returns cached result on retry |
| Impact reporting | Returns `impacted_balances` so Console can refresh its stock cache without a separate roundtrip |

## Decision rights matrix

| Decision | Who decides |
|---|---|
| When to submit a Mixing record | Mixing Operator (operational autonomy) |
| Which produced item is allowed | QA Lead (sets `Console Process Template.allowed_item_groups`) |
| Whether mass balance is enforced | Production Overseer (currently NO — see business rules) |
| Whether a Partial sync is acceptable | Mixing Operator (retries) → escalates to Shop Floor Supervisor if persistent |
| When to add a new value-map entry (e.g. new operation type) | Engineering Lead + QA Lead — requires Bridge mapping change |
| When to deprecate a Mixing variant | Production Overseer + Shop Floor Supervisor — requires Console Process Template change |
