# 03 — Console backend — `api.py` orchestration

**File:** `apps/shree_polymer_console/shree_polymer_console/shree_polymer_console/api.py`
**Size:** 4438 lines (whole file; this spec covers the ~12 functions that participate in MB Mixing)
**Controller:** `apps/shree_polymer_console/shree_polymer_console/shree_polymer_console/doctype/console_master_batch_mixing/console_master_batch_mixing.py` (132 lines)

The Console backend is the **orchestrator**. Its job:

1. Accept the canonical payload from Dash
2. Resolve warehouses + sequence steps from `Console Process Template`
3. Write a local audit record (`Console Master Batch Mixing`)
4. Create per-target `Console Transaction Log` rows
5. Let the Dash fire each target in parallel
6. Receive callbacks and update aggregate sync_status atomically
7. Auto-submit the Console record once both legs are `Synced`

## Function map (call order for one submission)

```
Dash: initializeSubmission({ payload })
   ▼
api.initialize_submission(payload)
   ├─► build_transaction_payload(payload)              ← canonicalisation
   │     └─► resolves warehouses via Console Process Template
   ├─► dispatch by process_code:
   │     create_local_master_batch_mixing(payload, reference_id)
   │       └─► _safe_local_create("Console Master Batch Mixing", ...)
   │             ├─► doc.flags.from_local_cache = True (skip strict validate)
   │             ├─► insert with child rows
   │             └─► upsert Console Transaction Log "Pending"
   ├─► resolve targets from template.sync_strategy
   ├─► create Console Transaction Log per target (Legacy + Ops)
   └─► return { reference_id, target_logs, transaction_payload }
   ▼
Dash: executeSubmissionStep({ log_name, target_info }) × N (parallel)
   ▼
api.execute_submission_step(log_name, target_info)
   ├─► POST { bridge_url or ops_url }/api/method/...
   ├─► capture response
   ├─► db.set_value Console Transaction Log {status, remote_log_name, ...}
   ├─► update_local_domain_record(process_code, reference_id, status, target, ...)
   │     └─► doc.apply_bridge_result(target, status, remote_name, error)
   │           [the 5-step atomic dance — see below]
   └─► return { status, result, log_name }
```

## `initialize_submission(payload)` — entry point

Defined at `api.py:958`. Returns target_logs the Dash will iterate over.

```python
@frappe.whitelist()
def initialize_submission(payload: dict) -> dict:
    """
    1. Builds the full transaction payload.
    2. Identifies targets based on template sync strategy.
    3. Creates 'Pending' log entries for each target to ensure visibility.
    4. Returns payload and target list for frontend to iterate.
    """
    try:
        # 1. Prelim payload to get metadata and reference_id
        prelim_payload = build_transaction_payload(payload)
        context = prelim_payload.get("context", {})
        reference_id = context.get("reference_id") or context.get("metadata", {}).get("reference_id")
        process_code = context.get("metadata", {}).get("process_code")

        # ERP identity (used by Frappe Cloud for cross-site auth)
        from shree_polymer_console.shree_polymer_console.oauth_client import get_user_erp_token
        erp_token = get_user_erp_token()
        erp_user_identity = erp_token["erp_user"] if erp_token else frappe.session.user
        payload["submitted_by"] = erp_user_identity
        payload["run_as"] = erp_user_identity

        # Phase 3 cutover: route inspection types to unified create_local_inspection
        is_inspection = bool(frappe.db.get_value(
            "Console Process Template", process_code, "is_inspection_type"
        ))
        if is_inspection:
            create_local_inspection(prelim_payload, reference_id)
        elif process_code == "MASTER_BATCH_MIXING":
            create_local_master_batch_mixing(prelim_payload, reference_id)
        elif process_code == "FINAL_BATCH_MIXING":
            create_local_final_batch_mixing(prelim_payload, reference_id)
        elif process_code == "SHEETING_PROCESS":
            create_local_sheeting_process(prelim_payload, reference_id)
        elif process_code == "CUT_BIT_TRANSFER":
            create_local_cut_bit_transfer(prelim_payload, reference_id)
        elif process_code == "BLANKING_DC_ENTRY":
            create_local_blanking_dc_entry(prelim_payload, reference_id)

        # Resolve target endpoints
        settings = frappe.get_single("Console Device Settings")
        sync_strategy = frappe.db.get_value("Console Process Template", process_code, "sync_strategy") \
                        or "Legacy Bridge Only"
        ops_site_url = settings.ops_site_url or frappe.get_site_config().get("ops_site_url")
        bridge_url   = settings.legacy_bridge_url

        targets = []
        # FACTORY REQUIREMENT: Do not route rejected inspections to Legacy.
        is_rejected_inspection = (process_code == "COMPOUND_INSPECTION" and context.get("status") == "Rejected")

        if sync_strategy in ["Legacy Bridge Only", "Both (Parallel)"]:
            if not bridge_url: frappe.throw("Legacy Bridge URL not configured")
            if not is_rejected_inspection:
                targets.append({"url": bridge_url, "type": "Legacy",
                                "method": "shree_polymer_legacy_bridge.sync_api.sync_process_transaction"})
        if sync_strategy in ["New ERP Only", "Both (Parallel)"]:
            if ops_site_url:
                targets.append({"url": ops_site_url, "type": "Ops",
                                "method": "shree_polymer_ops.api.process_transaction"})
            else:
                frappe.throw("Ops Site URL not configured")

        # ── Persist actual sync intent on the parent record ──────────────────
        # apply_bridge_result will compute aggregate sync_status based on this.
        target_types = {t["type"] for t in targets}
        actual_intent = ("Both" if target_types == {"Ops", "Legacy"} else
                         "Ops" if target_types == {"Ops"} else
                         "Legacy" if target_types == {"Legacy"} else None)
        # (inspection-doctype intent propagation snipped for brevity)

        # Build per-target headers + log rows
        target_logs = []
        for target in targets:
            transaction_payload = build_transaction_payload(payload, target_system=target['type'])
            req_params = {"payload": json.dumps(transaction_payload, default=str)}
            if target['type'] == "Legacy":
                req_params.update({"process_type": process_code, "reference_id": reference_id})

            log_name = log_transaction(
                process_type=process_code, reference_id=reference_id,
                target_system=target['type'], status="Pending",
                site_url=target['url'], remote_method=target['method'],
                request_payload=req_params if target['type'] == "Legacy" else transaction_payload,
                submission_mode="Direct",
                auth_method=legacy_auth_method if target['type'] == "Legacy" else ops_auth_method
            )
            if log_name:
                target_logs.append({"target": target['type'], "log_name": log_name,
                                    "url": target['url'], "method": target['method'],
                                    "req_params": req_params})

        if not target_logs:
            return {"status": "Error", "message": "Failed to initialize any system for submission."}

        return {
            "status": "Success",
            "transaction_payload": transaction_payload,
            "reference_id": reference_id,
            "process_code": process_code,
            "target_logs": target_logs
        }
    except Exception as e:
        frappe.log_error(title="Initialize Submission Error", message=frappe.get_traceback())
        return {"status": "Error", "message": str(e)}
```

**Key invariants:**

1. `process_code = "MASTER_BATCH_MIXING"` routes to `create_local_master_batch_mixing` — the dispatch chain is explicit, no template-driven dynamic dispatch
2. `sync_strategy` is configured per process on `Console Process Template`; MB Mixing uses `"Both (Parallel)"` so both Ops + Legacy fire
3. The per-target payload is built **separately** with `target_system=target['type']` — this matters because `build_transaction_payload` evaluates conditions in the template against `target_system`, so a step that's Legacy-only vs Ops-only can be gated
4. Failure here returns `{status: "Error"}` — the Dash treats this as a hard fail and does **not** proceed to execute_submission_step

## `build_transaction_payload(payload, target_system=None)` — canonicalisation

Defined at `api.py:681`. Reads the `Console Process Template` for the
process_code and produces the canonical shape that mapping engines read.

```python
def build_transaction_payload(payload: dict, target_system: str = None) -> dict:
    """Helper to build the full sequence-based payload from raw context."""
    metadata = payload.get("metadata", {})
    if not metadata.get("process_name"):
        metadata["process_name"] = metadata.get("process_type")

    # Auto-set reference doctype from work_order_data or job_card_data
    if not metadata.get("reference_doctype"):
        if payload.get("work_order_data", {}).get("name"):
            metadata["reference_doctype"] = "Work Order"
            metadata["reference_name"] = payload["work_order_data"]["name"]
        elif payload.get("job_card_data", {}).get("name"):
            metadata["reference_doctype"] = "Job Card"
            metadata["reference_name"] = payload["job_card_data"]["name"]

    process_code = metadata.get("process_code")
    reference_id = payload.get("reference_id")
    if not process_code:
        raise ValueError("Missing process_code in metadata")

    # Item normalisation: clear FG batch_no (legacy auto-generates), ensure raw materials have batch
    if payload.get("stock_entry_data") and "items" in payload["stock_entry_data"]:
        for item in payload["stock_entry_data"]["items"]:
            item["allow_zero_valuation_rate"] = 1
            if item.get("is_finished_item"):
                if "batch_no" in item: item["batch_no"] = None  # legacy generates it
            else:
                if not item.get("batch_no"):
                    if item.get("mix_barcode"):    item["batch_no"] = item.get("mix_barcode")
                    elif item.get("spp_batch_number"): item["batch_no"] = item.get("spp_batch_number")

    # 1. Fetch Template
    template = frappe.get_doc("Console Process Template", process_code)
    if not template.is_active:
        raise ValueError(f"Process template {process_code} is inactive")

    # 2. Resolve warehouses (Source / Target / WIP) from template's warehouse table
    #    using safe_eval against payload context for dynamic conditions
    is_compound      = (metadata.get("item_group") == "Compound")
    is_master_batch  = (operation == "Master Batch Mixing" or metadata.get("item_group") == "Master Batch")
    source_wh_row = resolve_warehouse_config("Source", template, wh_context)
    target_wh_row = resolve_warehouse_config("Target", template, wh_context)
    wip_wh_row    = resolve_warehouse_config("WIP",    template, wh_context)

    config = {
        "legacy_source_warehouse": ..., "legacy_target_warehouse": ..., "legacy_wip_warehouse": ...,
        "ops_source_warehouse":    ..., "ops_target_warehouse":    ..., "ops_wip_warehouse":    ...,
        "operation": operation, "workstation": workstation, "company": template.company,
        "naming_series_prefix": template.naming_series_prefix
    }

    # 3. Build sequence from template.actions (with condition evaluation via safe_eval)
    sequence = []
    for action in template.actions:
        if action.condition:
            if not safe_eval(action.condition, None, eval_context):
                continue  # skip step
        sequence.append(...)

    return {"reference_id": ..., "context": {...}, "sequence": [...], "metadata": metadata}
```

**Why this layer exists:** The Console Process Template stores the
**sequence of steps** declaratively (one row per action: create Work Order,
create Job Card, create Stock Entry, etc.) with optional condition strings
evaluated via Frappe's `safe_eval`. This lets non-developers reconfigure
the per-process step list without changing code. For MB Mixing, the
template has actions for Work Order + Job Card + Stock Entry creation that
the Ops MES Transaction Engine consumes.

## `create_local_master_batch_mixing(payload, reference_id)` — local audit

Defined at `api.py:2095`. Writes the `Console Master Batch Mixing` row.

```python
def create_local_master_batch_mixing(payload, reference_id):
    """Mirror the MB Mixing payload locally for audit. Identity = mix_barcode."""
    ctx = payload.get("context", {})
    posting_date, posting_time = _backdate_fields(ctx)
    consumption_items = ctx.get("stock_entry_data", {}).get("consumption_items") or []
    return _safe_local_create(
        "Console Master Batch Mixing",
        {
            "item_code": _pick(ctx, "metadata.produced_item", "stock_entry_data.fg_item",
                                    "work_order_data.item_to_manufacture", "item_code"),
            "batch_no": _pick(ctx, "batch_no", "stock_entry_data.batch_no"),
            "spp_batch_no": _pick(ctx, "spp_batch_no", "spp_batch_number", "mix_barcode"),
            "mix_barcode": _pick(ctx, "mix_barcode", "config.scan_barcode"),
            "qty": flt(_pick(ctx, "stock_entry_data.fg_qty", "work_order_data.qty_to_manufacture", "qty")),
            "warehouse": _pick(ctx, "config.ops_target_warehouse", "config.target_warehouse", "target_warehouse"),
            "workstation": _pick(ctx, "work_order_data.workstation", "job_card_data.workstation", "workstation"),
            "operator_name": _pick(ctx, "job_card_data.employee_code", "operator_name", "metadata.entry_role"),
            "posting_date": posting_date, "posting_time": posting_time,
            "process_code": "MASTER_BATCH_MIXING",
            "payload_snapshot": json.dumps(payload, indent=1),
        },
        reference_id,
        "create_local_master_batch_mixing",
        child_rows={"consumption_items": _normalize_items(consumption_items, _MIXING_ITEM_KEYMAP)},
    )
```

The `_pick(ctx, "a.b", "c.d", ...)` helper tries each dot-path in order and
returns the first non-empty value (`None`/`""` are treated as missing).
This makes the local mirror **forgiving of payload shape drift** — if Dash
moves a field, we have multiple fallbacks.

## `_safe_local_create(doctype, fields, reference_id, log_label, child_rows=None)` — audit-trail invariant

Defined at `api.py:1879`. **This is the most important helper in the
Console backend.** Every shipped Wave 1 doctype goes through it.

```python
def _safe_local_create(doctype, fields, reference_id, log_label, child_rows=None):
    """Insert a Console * record with graceful failure — never block the orchestration."""
    try:
        fields.setdefault("posting_date", frappe.utils.today())
        fields.setdefault("posting_time", frappe.utils.nowtime())
        fields.setdefault("status", "Pending")
        fields["doctype"] = doctype
        fields["reference_id"] = reference_id
        fields["submitted_by"] = frappe.session.user
        # Drop None/empty values so doctype defaults / non-mandatory fields stay clean
        cleaned = {k: v for k, v in fields.items() if v not in (None, "")}
        doc = frappe.get_doc(cleaned)

        # Append child rows BEFORE insert so they're persisted atomically
        if child_rows:
            for table_field, rows in child_rows.items():
                if not rows: continue
                for row in rows:
                    clean_row = {k: v for k, v in (row or {}).items() if v not in (None, "")}
                    if clean_row: doc.append(table_field, clean_row)

        # ── INVARIANT — must not change without architecture review ────────
        # Skip strict validate() on the audit-trail write path. The Desk UI
        # path still runs validate normally; we only bypass it here so a
        # partial Dash payload (e.g. CutBit with no top-level item_code) can
        # still leave a record for diagnostics.
        doc.flags.from_local_cache = True
        doc.flags.ignore_validate = True
        doc.insert(ignore_permissions=True, ignore_links=True)

        # Ensure a Transaction Log exists (upsert keyed on reference_id)
        log_name = frappe.db.get_value("Console Transaction Log", {"reference_id": reference_id}, "name")
        if log_name:
            log = frappe.get_doc("Console Transaction Log", log_name)
            log.process_code = doc.process_code
            log.status = "Pending"
            log.save(ignore_permissions=True)
        else:
            frappe.get_doc({"doctype": "Console Transaction Log",
                            "reference_id": reference_id,
                            "process_code": doc.process_code,
                            "status": "Pending",
                            "target_system": doc.target_system or "Both"}).insert(ignore_permissions=True)

        return doc.name
    except Exception:
        frappe.log_error(f"{log_label} error", frappe.get_traceback())
        return None    # ← graceful failure: Bridge sync continues even if mirror failed
```

**Why this design:**

| Decision | Reason |
|---|---|
| `flags.from_local_cache = True` | Controllers can soften their checks. The MB controller's `validate` returns early when this flag is set. |
| `ignore_validate = True` | Belt-and-braces; even if a controller doesn't honour `from_local_cache`, validate is skipped. |
| `ignore_permissions=True` + `ignore_links=True` | This is system-initiated; user permissions don't apply, and we don't want Link validation against possibly-missing master data. |
| Returns `None` on failure (catches all exceptions) | The Bridge sync is the source of truth for "did the transaction succeed." The local audit record failing should never block the actual transaction. |
| Child rows appended **before** insert | Atomicity — parent + children persist together. |
| Upsert pattern on Transaction Log | Idempotent — re-running `_safe_local_create` for the same reference_id doesn't double-log. |

## Console controller — `console_master_batch_mixing.py`

```python
class ConsoleMasterBatchMixing(Document):
    def validate(self):
        # Strict checks BYPASSED on audit-trail path
        if self.flags.get("from_local_cache"):
            return
        if not self.item_code:
            frappe.throw("Item Code is mandatory")
        if flt(self.qty) <= 0:
            frappe.throw("Produced Quantity must be greater than zero")
        if not self.get("consumption_items"):
            frappe.throw("Consumption Items are mandatory for mixing")

    def before_insert(self):
        self.process_code = "MASTER_BATCH_MIXING"
        if not self.submitted_by:
            self.submitted_by = frappe.session.user

    def on_submit(self):
        """Emits a Console Transaction Log Pending entry for Bridge tracking."""
        if not self.reference_id: return
        log_name = frappe.db.get_value("Console Transaction Log", {"reference_id": self.reference_id}, "name")
        if log_name:
            log = frappe.get_doc("Console Transaction Log", log_name)
            log.process_code = self.process_code
            log.status = "Pending"
            log.save(ignore_permissions=True)
        else:
            frappe.get_doc({"doctype": "Console Transaction Log",
                            "reference_id": self.reference_id,
                            "process_code": self.process_code,
                            "status": "Pending",
                            "target_system": self.target_system or "Both"}).insert(ignore_permissions=True)
```

The `on_submit` log-write is redundant with what `_safe_local_create` does
during insert. It exists because the auto-submit path (triggered by
`apply_bridge_result` step 5) needs to ensure the log exists for downstream
consumers — even when the original insert path failed to write it.

## `apply_bridge_result(target, status, remote_name, error)` — the 5-step atomic dance

Defined on the doctype controller at `console_master_batch_mixing.py:56`.
**This is the load-bearing race-safety pattern.** It must not be simplified.

```python
@frappe.whitelist()
def apply_bridge_result(self, target, status, remote_name=None, error=None):
    """Atomic per-leg update via frappe.db.set_value to avoid race when Ops + Legacy
    callbacks land near-simultaneously."""
    field_prefix = 'ops' if target == 'Ops' else 'legacy'
    leg_status = 'Synced' if status == 'Success' else 'Failed'

    # ── Step 1: Atomic per-field write for THIS leg only ──────────────────
    frappe.db.set_value(self.doctype, self.name, {
        f'{field_prefix}_sync_status': leg_status,
        f'{field_prefix}_reference': remote_name,
        f'{field_prefix}_error_message': error,
    }, update_modified=False)

    # ── Step 2: Re-read BOTH legs from DB (atomic snapshot, no memory) ────
    row = frappe.db.get_value(self.doctype, self.name,
                              ['ops_sync_status', 'legacy_sync_status'], as_dict=True) or {}
    ops_st    = row.get('ops_sync_status')
    legacy_st = row.get('legacy_sync_status')

    # ── Step 3: Aggregate sync_status ─────────────────────────────────────
    if ops_st == 'Synced' and legacy_st == 'Synced':
        new_sync = 'Success'
    elif ops_st == 'Failed' or legacy_st == 'Failed':
        new_sync = 'Failed'
    elif ops_st == 'Synced' or legacy_st == 'Synced':
        new_sync = 'Partial'
    else:
        new_sync = 'Pending'

    set_payload = {'sync_status': new_sync}
    if error:
        set_payload['error_log_summary'] = str(error).split('\n')[0][:140]
    frappe.db.set_value(self.doctype, self.name, set_payload, update_modified=False)

    # ── Step 4: Self-heal — close residual race in step 3-4 ───────────────
    # If a concurrent callback wrote 'Partial' AFTER another caller wrote
    # 'Success', correct it by re-reading final state.
    final = frappe.db.get_value(self.doctype, self.name,
                                ['ops_sync_status', 'legacy_sync_status', 'sync_status', 'docstatus'],
                                as_dict=True) or {}
    if (final.get('ops_sync_status') == 'Synced'
            and final.get('legacy_sync_status') == 'Synced'
            and final.get('sync_status') != 'Success'):
        frappe.db.set_value(self.doctype, self.name, 'sync_status', 'Success', update_modified=False)
        final['sync_status'] = 'Success'

    # ── Step 5: Auto-submit on full success — fetch FRESH doc ─────────────
    # Never use self (which has stale in-memory state from before the leg writes).
    if final.get('sync_status') == 'Success' and final.get('docstatus') == 0:
        fresh = frappe.get_doc(self.doctype, self.name)
        if fresh.docstatus == 0:
            try:
                fresh.submit()
            except Exception as e:
                frappe.log_error(f'Auto-submit failed for {fresh.name}: {e}',
                                 f'apply_bridge_result.{self.doctype}')

    frappe.db.commit()
```

**Why each step exists:**

| Step | The race it closes |
|---|---|
| 1: atomic per-field write | Two callbacks running at the same instant don't clobber each other's leg state — each writes only its own fields. |
| 2: re-read both legs | `self` is stale by the time step 1 returns. Reading from DB gives an atomic snapshot of both legs. |
| 3: aggregate | Computes `sync_status` from current DB state, not stale memory. |
| 4: self-heal | Without this, if Ops callback runs `1→2→3` while Legacy callback also runs `1→2→3`, the slower one's step-3 might overwrite the faster one's `Success` with `Partial`. Re-reading and correcting fixes this. |
| 5: fresh-doc submit | If we called `self.submit()` with the controller's in-memory state, `self.docstatus` might be stale. `frappe.get_doc(...)` reads current DB state. |

**Origin:** the "Compound Deviation saga" (2026-04-29 → 2026-05-01). Multiple
sequential fixes shipped without test coverage, each introducing a new race
under parallel Ops + Legacy callbacks. The 5-step pattern is production-
validated and **must not be simplified**.

## `apply_bridge_result` — global entry point (api.py)

There's also a module-level `apply_bridge_result` at `api.py:1946` that
routes Bridge callbacks to the right doctype. The Bridge POSTs its callback
to this whitelisted function, and it dispatches to the controller method:

```python
@frappe.whitelist()
def apply_bridge_result(reference_id, target, status, remote_name=None, error=None, **kwargs):
    """Global entry point for Bridge callbacks."""
    # 1. Update Transaction Log
    log_filters = {"reference_id": reference_id}
    if target and target != "Both":
        log_filters["target_system"] = target
    logs = frappe.get_all("Console Transaction Log", filters=log_filters, fields=["name"])
    if not logs and "target_system" in log_filters:
        del log_filters["target_system"]
        logs = frappe.get_all("Console Transaction Log", filters=log_filters, fields=["name"])
    for entry in logs:
        log = frappe.get_doc("Console Transaction Log", entry.name)
        log.status = status
        if target and target != "Both": log.target_system = target
        log.remote_reference_name = remote_name
        log.error_message = error
        log.save(ignore_permissions=True)

    # 2. Update parent record — scan known parent doctypes
    parent_doctypes = [
        "Console Inspection", "Console Master Batch Mixing", "Console Final Batch Mixing",
        "Console Sheeting Process", "Console Cut Bit Transfer",
        "Console Compound Deviation", "Console Compound Inspection",
        "Console Blanking DC Entry",
    ]
    for dt in parent_doctypes:
        parent_name = frappe.db.get_value(dt, {"reference_id": reference_id}, "name")
        if parent_name:
            doc = frappe.get_doc(dt, parent_name)
            if hasattr(doc, 'apply_bridge_result'):
                doc.apply_bridge_result(target, status, remote_name, error, **kwargs)
            break
```

The order of `parent_doctypes` matters: `Console Inspection` is first
(Phase 3 unification puts inspection records there), then per-process
doctypes. The function exits after the first match (`break`).

## `execute_submission_step(log_name, target_info)` — per-target dispatch

Defined at `api.py:1107`. Called once per target by the Dash. Makes the
actual HTTP POST to either the Legacy Bridge or the Ops site.

```python
@frappe.whitelist()
def execute_submission_step(log_name: str, target_info: dict) -> dict:
    """Executes a single submission step for a specific target log."""
    if not frappe.db.exists("Console Transaction Log", log_name):
        return {"status": "Failed", "message": f"Log entry {log_name} not found."}

    log = frappe.get_doc("Console Transaction Log", log_name)
    if log.status == "Success":
        return {"status": "Success", "message": "Already synced", "log_name": log_name}

    # Headers (OAuth tokens / API keys per target)
    ops_headers, ops_auth_method = build_erp_headers_for_user()
    legacy_headers, legacy_auth_method = build_legacy_bridge_headers()

    url = f"{target_info['url']}/api/method/{target_info['method']}"
    is_legacy = target_info['target'] == "Legacy"
    headers = legacy_headers if is_legacy else ops_headers
    req_params = target_info.get('req_params') or {}

    # ── RETRY FLOW FIX ────────────────────────────────────────────────────
    # req_params may be empty when retrying from the log UI.
    # Rebuild it from the stored log request_payload.
    if not req_params.get('payload'):
        stored_payload = json.loads(log.request_payload) if log.request_payload else {}
        if is_legacy:
            req_params = {"payload": json.dumps(stored_payload, default=str),
                          "process_type": log.process_type or "",
                          "reference_id": log.reference_id or ""}
        else:
            req_params = {"payload": json.dumps(stored_payload, default=str)}

    # POST (form-encoded — Frappe @whitelist reads frappe.form_dict)
    send_headers = {k: v for k, v in headers.items() if k.lower() != 'content-type'}
    response = requests.post(url, headers=send_headers, data=req_params, timeout=120)

    # Parse response (graceful — non-200 with `status: "success"` body is still success)
    res, err = {}, None
    if response.status_code != 200:
        try:
            error_data = response.json()
            if isinstance(error_data, dict) and error_data.get("message", {}).get("status") == "success":
                res, status = error_data, "Success"
            else:
                err = error_data.get("_server_messages") or error_data.get("exception") or response.text
                res = {"message": {"status": "Failed", "message": f"{target_info['target']} Error: {err}"}}
        except:
            err = response.text
    else:
        res = response.json()
        status = (res.get("message", {}).get("status") or "Success").title()

    # Extract mix_barcode / FG batch info from response for label rendering
    captured_msg = res.get("message", {})
    # ... barcode_image generation, mix_barcode extraction snipped for brevity ...

    # Update Console Transaction Log atomically (db.set_value avoids TimestampMismatch)
    frappe.db.set_value("Console Transaction Log", log_name, {
        "status": status,
        "response_payload": json.dumps(res, default=str),
        "remote_log_name": captured_msg.get("log_name"),
        "remote_reference_doctype": captured_msg.get("reference_doctype") or
            ("Shree Polymer MES Log" if target_info.get("target") == "Ops" else "Legacy Transaction Log"),
        "remote_reference_name": captured_msg.get("reference_name") or captured_msg.get("log_name"),
        "mix_barcode": mix_barcode,
        "fg_item_batch_no": fg_item_batch_no,
        "barcode_image": barcode_image,
        "detailed_error": detailed_err_val,
        "error_message": error_msg_val
    })

    # Fire callback into the parent doctype
    update_local_domain_record(log.process_code, log.reference_id, status, target_info['target'],
                                captured_msg, detailed_err_val)
    frappe.db.commit()

    # Apply targeted stock updates from impacted_balances (Ops response only)
    if status == "Success":
        if captured_msg.get("impacted_balances"):
            from shree_polymer_console.shree_polymer_console.stock_sync import update_cache_from_balances
            update_cache_from_balances(captured_msg.get("impacted_balances"),
                                        trigger_type="Real-time",
                                        bundles=captured_msg.get("impacted_bundles"))
        # impacted_clips, impacted_bins, impacted_qi follow the same pattern

    return {"status": status, "result": res, "log_name": log_name}
```

**Notes for Hermes workers:**

- `timeout=120` is the per-leg HTTP timeout (2 minutes). Long-running Ops
  steps (e.g. Stock Entry submit with many items) approach this.
- `form_dict` payload (not JSON body) — Frappe whitelisted methods read
  from `frappe.form_dict` more reliably than from JSON body.
- The Content-Type header is **deliberately stripped** so `requests` can
  set the correct multipart/form-data boundary.
- On success, `impacted_balances` / `impacted_clips` / `impacted_bins` /
  `impacted_qi` from the response are fed into local cache sync helpers —
  this keeps Console's `Console Stock Cache` warm without a second roundtrip.

## `update_local_domain_record(process_type, reference_id, status, target, captured_msg, err)`

Defined at `api.py:~2920` (called from `execute_submission_step`). Routes
the callback to the right Console doctype.

For MB Mixing, the relevant lookup table is:

```python
legacy_doctype_map = {
    "MASTER_BATCH_MIXING": "Console Master Batch Mixing",
    "FINAL_BATCH_MIXING":  "Console Final Batch Mixing",
    "SHEETING_PROCESS":    "Console Sheeting Process",
    "CUT_BIT_TRANSFER":    "Console Cut Bit Transfer",
}
doctype = "Console Inspection" if is_inspection else legacy_doctype_map.get(process_type)
```

It then looks up the local record by `reference_id` (with fallback to
`ops_reference` / `legacy_reference` for pre-Phase-3 records) and calls
`doc.apply_bridge_result(...)`, which runs the 5-step dance above.

## Helpers — `_pick`, `_backdate_fields`, `_normalize_items`, `_MIXING_ITEM_KEYMAP`

### `_pick(payload, *paths, default=None)` — `api.py:1859`

```python
def _pick(payload, *paths, default=None):
    """Walk a dict by trying each dot-path in order; return first non-empty value."""
    for path in paths:
        node = payload
        for part in path.split("."):
            if not isinstance(node, dict):
                node = None; break
            node = node.get(part)
            if node is None: break
        if node not in (None, ""):
            return node
    return default
```

Used pervasively in `create_local_*` functions. The order of paths matters:
the **most specific** path should be first, falling back to broader paths.
This is how the local-mirror layer survives Dash payload shape drift.

### `_backdate_fields(ctx)` — `api.py:2009`

```python
def _backdate_fields(ctx):
    """Pull posting_date / posting_time from the payload context if present.
    Supports backdating for System Manager / Administrator users."""
    posting_date = (
        _pick(ctx, "metadata.inspection_date", "posting_date",
                   "compound_inspection_data.posting_date", "stock_entry_data.posting_date")
        or frappe.utils.today()
    )
    posting_time = (
        _pick(ctx, "metadata.inspection_time", "posting_time",
                   "compound_inspection_data.posting_time", "stock_entry_data.posting_time")
        or frappe.utils.nowtime()
    )
    return posting_date, posting_time
```

For MB Mixing, the Dash sends `endDate` / `endTime` as
`stock_entry_data.posting_date` / `stock_entry_data.posting_time`, so the
last fallback wins. Inspection-specific paths exist because this helper is
shared with `create_local_inspection`.

### `_normalize_items(items, key_map)` + `_MIXING_ITEM_KEYMAP` — `api.py:2030`

```python
def _normalize_items(items, key_map):
    """Normalize raw payload item dicts into Console child-table rows.
    `key_map` is {payload_key: child_field_name} pairs. Unmapped fields are dropped."""
    out = []
    for raw in items or []:
        row = {}
        for src, dst in key_map.items():
            v = raw.get(src)
            if v not in (None, ""):
                row[dst] = v
        if row:
            out.append(row)
    return out

_MIXING_ITEM_KEYMAP = {
    "item_code":                 "item_code",
    "batch_no":                  "batch_no",
    "spp_batch_number":          "spp_batch_no",   # rename
    "spp_batch_no":              "spp_batch_no",   # also accept canonical
    "mix_barcode":               "mix_barcode",
    "qty":                       "qty",
    "s_warehouse":               "s_warehouse",
    "is_finished_item":          "is_finished_item",
    "allow_zero_valuation_rate": "allow_zero_valuation_rate",
}
```

Two entries map to `spp_batch_no` — this is a deliberate accept-both pattern
to survive the renaming during the unification work (legacy schema used
`spp_batch_number`, Console standardised on `spp_batch_no`).

## What Hermes workers can safely change here

| Change | Risk |
|---|---|
| Add a new `_pick` fallback path | Low — only adds tolerance |
| Add a new field to `_MIXING_ITEM_KEYMAP` | Low — unmapped fields are dropped, new ones are picked up |
| Add a new `create_local_*` function for a new process | Low — pattern is well-established |
| Modify the order of paths in `_pick` calls | Medium — changes which fallback "wins" when multiple are set |
| Touch `_safe_local_create` | **High** — every Wave 1 doctype depends on this exact behavior; needs architecture review |
| Touch the 5-step `apply_bridge_result` | **Highest** — production race-safety; needs architecture review + race-condition tests |
| Change `legacy_doctype_map` in `update_local_domain_record` | Medium — must coordinate with each affected controller |
