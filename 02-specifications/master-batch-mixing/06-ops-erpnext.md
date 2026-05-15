# 06 — Ops ERPNext (v15) — Generic MES Transaction Engine

**App:** `apps/shree_polymer_ops` on ERPNext v15
**Bench:** `25spp.local` ↔ `newspp.m.frappe.cloud`
**Entry point:** `shree_polymer_ops/api.py::process_transaction`
**Engine:** `shree_polymer_ops/api.py::TransactionEngine`

## The Architectural Intent vs Reality for MB Mixing on Ops

**Architectural Intent:** Ops should be a generic executor. MB Mixing is handled by the **generic** `TransactionEngine`, which reads the sequence from the Console Process Template and executes each action.

**Current Reality (Tech Debt):** `shree_polymer_ops/api.py` still contains legacy process-specific code like `_process_stock_entry_pre_save`, `_resolve_batch_from_barcode`, and `_generate_mix_barcode`. These are **not actually triggered or needed** for modern Console payloads (because the Console pre-resolves all batches, barcodes, and items before sending the payload to Ops), but they still exist in the code. Any future refactor should remove this dead code so the codebase matches the pure execution architecture.

Compare with the process-specific routing for other process types in
`process_transaction`:

```python
if process_code == "CUT_BIT_TRANSFER":
    return submit_cut_bit_transfer(context, run_legacy_sync=False)
elif process_code == "BULK_CLIP_RELEASE":
    clips = context.get("release_data", {}).get("clips") or []
    return bulk_release_clips(barcodes=clips)
elif process_code == "BLANKING_DC_ENTRY":
    return submit_blanking_dc_entry(context)

# MASTER_BATCH_MIXING falls through to TransactionEngine — generic path
try:
    engine = TransactionEngine(payload)
    return engine.execute()
except Exception as e:
    ...
```

## The `TransactionEngine` class

Constructor (`api.py:100`):

```python
class TransactionEngine:
    """Orchestrates atomic execution of multi-step ERP transactions.

    The engine supports idempotency, placeholder resolution between steps,
    and atomic commit/rollback. Every transaction is logged in 'MES Transaction Log'."""

    def __init__(self, payload: Dict[str, Any]):
        self.payload   = payload
        self.context   = payload.get('context', {})
        self.sequence  = payload.get('sequence', [])
        self.metadata  = payload.get('metadata', {})

        # Metadata extraction - Prioritize top-level reference_id (sent by new Console)
        self.reference_id     = payload.get('reference_id') or self.metadata.get('reference_id')
        self.process_name     = self.metadata.get('process_name', 'Unknown Process')
        self.reference_doctype = self.metadata.get('reference_doctype')
        self.reference_name   = self.reference_id or self.metadata.get('reference_name')

        # Inject target_system identify for conditional actions
        self.context['target_system'] = "Ops"
```

The engine reads `payload.sequence` — a list of action dicts produced by
`build_transaction_payload` on the Console side (from
`Console Process Template.actions`). For MB Mixing, the sequence typically
contains:

1. **`create_work_order`** — creates an ERPNext `Work Order` for the MB FG item
2. **`create_job_card`** — creates a `Job Card` against that Work Order
3. **`create_stock_entry`** — creates a `Stock Entry` (Manufacture purpose)
   that consumes raw materials and produces the MB FG with the
   Console-generated `mix_barcode` as the FG's batch identifier

Each action is a dict like:

```python
{
    "action": "create_doc",
    "params": {
        "doctype": "Work Order",
        "production_item": "{{ context.metadata.produced_item }}",
        "qty": "{{ context.stock_entry_data.fg_qty }}",
        ...
    },
    "store_as": "work_order_name"   # save output for placeholder resolution
}
```

Placeholders like `{{ context.metadata.produced_item }}` are resolved by
the engine against `self.context` before the action runs. Cross-step
references (`{{ work_order_name }}`) work because step output is stored.

## Execution lifecycle — `engine.execute()`

```python
def execute(self):
    """Main entry point — runs all sequence steps with atomicity guarantees."""
    # 1. Idempotency check: if a MES Transaction Log with this reference_id exists
    #    and status == "Success", return its captured result.
    existing = frappe.db.get_value("Shree Polymer MES Log",
                                   {"reference_id": self.reference_id, "status": "Success"},
                                   ["name", "result_payload"], as_dict=True)
    if existing:
        return {"status": "success", "log_name": existing.name,
                "results": json.loads(existing.result_payload or "{}"),
                "message": "Idempotent — already processed"}

    # 2. Create a MES Log row for this run (Pending)
    log = frappe.get_doc({"doctype": "Shree Polymer MES Log",
                          "reference_id": self.reference_id,
                          "process_name": self.process_name,
                          "incoming_payload": json.dumps(self.payload, default=str),
                          "status": "Pending"}).insert(ignore_permissions=True)

    # 3. Run each step
    step_outputs = {}
    impacted_balances = []
    try:
        for step in self.sequence:
            resolved = self._resolve_placeholders(step, step_outputs)
            if step.get("condition") and not self._eval_condition(step["condition"]):
                continue
            result = self._run_action(resolved)
            if step.get("store_as"):
                step_outputs[step["store_as"]] = result.get("name")
            # Accumulate stock-balance deltas for the response
            if result.get("impacted_balances"):
                impacted_balances.extend(result["impacted_balances"])

        # 4. Success log
        log.status = "Success"
        log.result_payload = json.dumps({"step_outputs": step_outputs,
                                          "impacted_balances": impacted_balances}, default=str)
        log.save(ignore_permissions=True)

        return {"status": "success", "log_name": log.name,
                "reference_name": log.name,
                "results": step_outputs,
                "impacted_balances": impacted_balances}

    except Exception as e:
        # 5. Failure: rollback partial work, log, raise (process_transaction catches)
        frappe.db.rollback()
        log.status = "Failed"
        log.error_message = str(e)
        log.traceback = tb.format_exc()
        log.save(ignore_permissions=True)
        # Re-raise so process_transaction can return structured failure
        e.partial_results = step_outputs
        e.log_name = log.name
        e.reference_id = self.reference_id
        raise
```

## What lands on Ops for one MB Mixing submission

After `engine.execute()` returns Success, the Ops bench has:

| Document | Details |
|---|---|
| `Shree Polymer MES Log` | One row, status=Success, `reference_id` = Console ID, `result_payload` = JSON of step outputs |
| `Work Order` | One WO for the MB FG item, qty = `fg_qty`, BOM = `bom_no` from payload |
| `Job Card` | One JC against the WO, employee = `operator`, workstation/operation set |
| `Stock Entry` | One SE, purpose = `Manufacture`, items: raw material rows (`s_warehouse` populated) + FG row (`t_warehouse` = Ops target warehouse, `batch_no` set, `mix_barcode` set) |
| `Stock Ledger Entry` | Auto-generated by Frappe — debits raw warehouses, credits target |
| `Batch` | Auto-created by Frappe if FG has `has_batch_no=1` — batch name follows naming series, `mix_barcode` field linked to Console-generated value |

The `impacted_balances` returned in the response let Console refresh its
local `Console Stock Cache` immediately, so the operator sees updated
stock figures without waiting for a snapshot sync.

## Idempotency on Ops

`engine.execute()` checks for an existing `Shree Polymer MES Log` with
the same `reference_id` and `status="Success"` **before** running any
step. If found, it returns the cached `result_payload`. This means:

- A retry of `execute_submission_step` from Console for the same
  `reference_id` returns success without re-creating any document
- The Console doctype's `apply_bridge_result` still runs (callback path),
  updating sync_status correctly even on retried submissions

## How the Ops response feeds Console

The response from `process_transaction` contains:

```json
{
  "status": "success",
  "log_name": "MES-LOG-2026-...",
  "reference_name": "MES-LOG-2026-...",
  "results": {
    "work_order_name": "MFG-WO-2026-...",
    "job_card_name":   "JC-2026-...",
    "stock_entry_name": "MAT-STE-2026-..."
  },
  "impacted_balances": [
    {"item_code": "MB-XXX", "warehouse": "Mixing - SPP",
     "batch_no": "C_26C03X1", "actual_qty": 100.0, ...},
    {"item_code": "RM-001", "warehouse": "U3-Store - SPP INDIA",
     "batch_no": "RAW-001", "actual_qty": -50.0, ...},
    ...
  ],
  "impacted_bundles": [...],
  "generated_barcodes": [
    {"item_code": "MB-XXX", "mix_barcode": "C_26C03X1", "spp_batch_number": "C_26C03X1"}
  ]
}
```

Console's `execute_submission_step` then:
1. Saves the whole response on `Console Transaction Log.response_payload`
2. Sets `Console Transaction Log.remote_reference_name` = `log_name`
3. Calls `update_local_domain_record` which invokes
   `Console Master Batch Mixing.apply_bridge_result(target="Ops",
   status="Success", remote_name=log_name)`
4. Applies `impacted_balances` to `Console Stock Cache` via
   `update_cache_from_balances`

## Process-specific Ops handlers (for context — not used by MB)

For reference, here are the **other** process types that have dedicated
Ops handlers (bypassing TransactionEngine):

| `process_code` | Dedicated handler | Why it bypasses the engine |
|---|---|---|
| `CUT_BIT_TRANSFER` | `submit_cut_bit_transfer` | Cut Bit needs asset retirement + batch auto-creation that the generic engine can't replicate |
| `BULK_CLIP_RELEASE` | `bulk_release_clips` | Clip-state management has its own state machine |
| `BLANKING_DC_ENTRY` | `submit_blanking_dc_entry` | Asset Movement (Receive Bin) + SE Repack branching |

MB Mixing stays on the generic engine because its action list (WO + JC +
SE Manufacture) is what the engine was originally designed for.

## What Hermes workers can safely change here

| Change | Risk |
|---|---|
| Add a new action to the MB sequence in `Console Process Template` | Low — engine reads template declaratively |
| Add an action **condition** that's only Ops-side | Low — `target_system == "Ops"` is in context |
| Touch `TransactionEngine.execute()` | **High** — affects every process_type using the generic engine |
| Add a process-specific handler for MB (bypassing the engine) | High — diverges from current architecture; needs strong reason |
| Change idempotency lookup key from `reference_id` | **Highest** — breaks cross-system correlation |
| Remove the `frappe.db.rollback()` in failure path | High — partial-state on failure becomes operator-visible |
