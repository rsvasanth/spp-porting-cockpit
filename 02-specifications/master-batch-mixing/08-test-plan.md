# 08 — Test plan

## Unit tests — shipped

**File:** `apps/shree_polymer_console/.../doctype/console_master_batch_mixing/test_console_master_batch_mixing.py`

```python
class TestConsoleMasterBatchMixing(FrappeTestCase):
    """Wave 1 + Wave 1.5 hardening tests for Console Master Batch Mixing.

    Two paths exercised:
        1. api._safe_local_create (audit-trail) — flags.from_local_cache bypass
        2. Desk UI direct insert — validate runs strictly
    """

    def setUp(self):
        self.reference_id = "TEST-MBM-DOD-001"
        self.partial_ref = "TEST-MBM-PARTIAL-001"
        # Idempotent cleanup
        for ref in (self.reference_id, self.partial_ref, "INVALID-REF"):
            frappe.db.delete("Console Master Batch Mixing", {"reference_id": ref})
            frappe.db.delete("Console Transaction Log", {"reference_id": ref})
        frappe.db.commit()

    def test_create_and_submit_lifecycle(self):
        """Full payload through api → record persists with child rows + transaction log."""
        payload = {
            "context": {
                "metadata": {"produced_item": "MB-ITEM-001", "process_code": "MASTER_BATCH_MIXING"},
                "mix_barcode": "MIX001",
                "config": {"ops_target_warehouse": "U3-Store"},
                "stock_entry_data": {
                    "fg_item": "MB-ITEM-001", "fg_qty": 100,
                    "consumption_items": [{"item_code": "RM-001", "qty": 50,
                                            "s_warehouse": "U3-Store", "batch_no": "RAW-001"}]}}}
        doc_name = create_local_master_batch_mixing(payload, self.reference_id)
        self.assertTrue(doc_name, "create_local_master_batch_mixing should return a doc name")
        doc = frappe.get_doc("Console Master Batch Mixing", doc_name)
        self.assertEqual(doc.process_code, "MASTER_BATCH_MIXING")
        self.assertEqual(doc.mix_barcode, "MIX001")
        self.assertEqual(len(doc.consumption_items), 1)
        self.assertEqual(doc.consumption_items[0].item_code, "RM-001")
        self.assertEqual(doc.consumption_items[0].qty, 50)
        self.assertTrue(frappe.db.exists("Console Transaction Log",
                                          {"reference_id": self.reference_id}))

    def test_partial_payload_still_lands_via_audit_path(self):
        """The api path uses flags.from_local_cache to bypass validate.
        Partial payloads (no item_code, no items) MUST still leave a diagnostic record."""
        payload = {"context": {"mix_barcode": "PARTIAL-MIX"}}  # no produced_item, no items, no qty
        doc_name = create_local_master_batch_mixing(payload, self.partial_ref)
        self.assertTrue(doc_name, "Partial payload must still land for diagnostics")
        doc = frappe.get_doc("Console Master Batch Mixing", doc_name)
        self.assertEqual(doc.mix_barcode, "PARTIAL-MIX")
        self.assertEqual(doc.process_code, "MASTER_BATCH_MIXING")
        self.assertTrue(doc.payload_snapshot, "payload_snapshot should be persisted for replay")

    def test_desk_path_validates_strictly(self):
        """Direct insert (Desk UI path) without from_local_cache flag → validate throws."""
        with self.assertRaises(frappe.ValidationError):
            doc = frappe.get_doc({"doctype": "Console Master Batch Mixing",
                                  "reference_id": "TEST-MBM-STRICT",
                                  "qty": 0, "consumption_items": []})
            doc.insert(ignore_permissions=True)
```

**Run command:**
```bash
bench --site sppconsole-dev.local run-tests \
  --module shree_polymer_console.shree_polymer_console.doctype.console_master_batch_mixing.test_console_master_batch_mixing
```

## Unit tests — gaps (recommended additions)

Hermes Test Engineer should write these before any change to the 5-step
race pattern or the `_safe_local_create` flag pattern:

### `test_apply_bridge_result_concurrent_callbacks`

Simulate the race: two threads call `apply_bridge_result` near-simultaneously,
one with `target="Ops"` and one with `target="Legacy"`. Assert final state:

```python
def test_apply_bridge_result_concurrent_callbacks(self):
    """Both legs callback concurrently — final state must be Success + auto-submitted."""
    import threading
    doc_name = self._create_test_mbm()
    doc = frappe.get_doc("Console Master Batch Mixing", doc_name)

    barrier = threading.Barrier(2)
    def call(target):
        barrier.wait()  # ensure both call apply_bridge_result simultaneously
        # Use a fresh doc instance per thread (mirrors real callback flow)
        d = frappe.get_doc("Console Master Batch Mixing", doc_name)
        d.apply_bridge_result(target, "Success", f"REMOTE-{target}-001")

    t1 = threading.Thread(target=call, args=("Ops",))
    t2 = threading.Thread(target=call, args=("Legacy",))
    t1.start(); t2.start(); t1.join(); t2.join()

    final = frappe.get_doc("Console Master Batch Mixing", doc_name)
    self.assertEqual(final.ops_sync_status, "Synced")
    self.assertEqual(final.legacy_sync_status, "Synced")
    self.assertEqual(final.sync_status, "Success")
    self.assertEqual(final.docstatus, 1)
```

### `test_apply_bridge_result_partial_then_recover`

```python
def test_apply_bridge_result_partial_then_recover(self):
    """Legacy fails, then retry succeeds → sync_status promotes correctly."""
    doc_name = self._create_test_mbm()
    doc = frappe.get_doc("Console Master Batch Mixing", doc_name)

    # Ops succeeds first
    doc.apply_bridge_result("Ops", "Success", "OPS-001")
    doc.reload()
    self.assertEqual(doc.sync_status, "Partial")

    # Legacy fails
    doc.apply_bridge_result("Legacy", "Failed", None, error="Test error")
    doc.reload()
    self.assertEqual(doc.sync_status, "Failed")

    # Retry Legacy — succeeds
    doc.apply_bridge_result("Legacy", "Success", "LEGACY-001")
    doc.reload()
    self.assertEqual(doc.sync_status, "Success")
    self.assertEqual(doc.docstatus, 1)  # auto-submitted via step 5
```

### `test_reference_id_uniqueness`

```python
def test_reference_id_uniqueness(self):
    """Second insert with same reference_id must raise DuplicateEntryError."""
    payload = {"context": {"metadata": {"produced_item": "X", "process_code": "MASTER_BATCH_MIXING"},
                            "stock_entry_data": {"fg_qty": 1, "consumption_items": [{"item_code": "Y", "qty": 1}]}}}
    doc_name = create_local_master_batch_mixing(payload, self.reference_id)
    self.assertTrue(doc_name)
    # Second call with same ref — should fail at the unique constraint, return None
    doc_name_2 = create_local_master_batch_mixing(payload, self.reference_id)
    self.assertIsNone(doc_name_2, "Second create with same reference_id should fail gracefully")
```

### `test_backdated_posting_date_survives`

```python
def test_backdated_posting_date_survives(self):
    """Backdated posting_date in payload flows through to Console doc."""
    payload = {"context": {
        "metadata": {"produced_item": "X", "process_code": "MASTER_BATCH_MIXING"},
        "stock_entry_data": {"posting_date": "2026-04-01", "posting_time": "08:00",
                              "fg_qty": 1, "consumption_items": [{"item_code": "Y", "qty": 1}]}}}
    doc_name = create_local_master_batch_mixing(payload, self.reference_id)
    doc = frappe.get_doc("Console Master Batch Mixing", doc_name)
    self.assertEqual(str(doc.posting_date), "2026-04-01")
```

### `test_value_map_inward_material_type`

```python
def test_value_map_inward_material_type(self):
    """Bridge mapping must resolve Master Batch Mixing → 'Master Batch'."""
    mapping = frappe.get_doc("Legacy Sync Mapping", "MASTER_BATCH_MIXING")
    inward_row = next((r for r in mapping.field_mappings
                       if r.legacy_field == "inward_material_type"), None)
    self.assertIsNotNone(inward_row)
    vm = json.loads(inward_row.value_map)
    self.assertEqual(vm.get("Master Batch Mixing"), "Master Batch")
    self.assertEqual(inward_row.default_value, "Compound")  # defensive default
```

## Integration tests — parked

Per `06_INTEGRATION_TESTS_TODO.md`, per-process real-data tests across
all 3 sites. The harness is **not built yet** but the design is fixed:

**Files to create in `apps/shree_polymer_console/.../integration_tests/`:**

```
├── __init__.py
├── README.md                              # runbook for ops
├── runner.py                              # generic harness (per-process scenarios)
├── preflight_master_batch_mixing.py       # asserts test items, BOMs, warehouses exist
├── scenario_master_batch_mixing.py        # the actual test sequence
├── fixtures/
│   └── seed_master_batch_mixing.py        # creates / re-receives test stock
├── checks/
│   ├── console_checks.py                  # asserts on Console state
│   ├── ops_checks.py                      # asserts on Ops state
│   └── legacy_checks.py                   # asserts on Legacy state
└── reports/                               # gitignored runtime output
```

**Confirmed test data:**

| Item | Value |
|---|---|
| Produced (FG) | `MB_TEST_6122` |
| Raw (consumed) | `B_TEST_6122` |
| BOM | `BOM-MB_TEST_6122-001` |
| Workstation | `Two Roll Mixing Mill` |
| Operation | `Master Batch Mixing` |
| Operator | `HR-EMP-00101` (role: Mixing Operator) |
| Ops Warehouse | `Mixing - SPP` |
| Legacy Warehouse | `U3-Store - SPP INDIA` |
| Test mix_barcode | `TEST_MIX_<unix_ms>` (unique per run) |

**Scenario assertions (the canonical MB integration test):**

1. Console submission via `initialize_submission` + `execute_submission_step`:
   - Returns `{status: Success, reference_id, target_logs: [Legacy, Ops]}`
   - Both legs ultimately return `Success`
2. `Console Master Batch Mixing` post-conditions:
   - `sync_status == "Success"`, `docstatus == 1`
   - `legacy_reference` populated, `ops_reference` populated
   - Child `consumption_items` rows match input
3. `Console Transaction Log` post-conditions:
   - Two rows for the reference_id, both `Status=Success`
   - `remote_reference_name` populated on both
4. Legacy DCR post-conditions:
   - One row with `dc_no = reference_id`
   - `inward_material_type = "Master Batch"`
   - `bridge_mix_barcode = test_mix_barcode`
   - `stock_entry_reference` populated (SE created)
   - Manufacturing Stock Entry has FG row with `mix_barcode = test_mix_barcode`
5. Ops state post-conditions:
   - One `Shree Polymer MES Log` row, `status="Success"`
   - One `Work Order` for the produced item
   - One `Stock Entry` (Manufacture), FG row has `batch_no` set
6. Stock Ledger reconciliation:
   - Raw material qty reduced on both Ops + Legacy
   - FG qty increased on both Ops + Legacy
   - Net positions match (within rounding)

**Estimated effort to build:** 3.5 hours first time (incl. framework), 45
min per subsequent process scenario. Wave 1 total: ~5.5 hours.

## End-to-end tests (Playwright via Dash)

To be written. Critical flows:

| Test | What it covers |
|---|---|
| Happy path submit | Operator scan → BOM → raw scan → produced qty → submit → success modal |
| Network failure mid-submit | Kill bridge connectivity after `initialize_submission`; verify Dash shows `Partial` and retry button works |
| Backdating | System Manager user submits with posting_date = yesterday; verify legacy DCR `dc_receipt_date` = yesterday |
| Invalid operator role | Try to submit as a user without `Mixing Operator` role; verify rejection |
| Mass imbalance (informational) | Submit with consumed=50, produced=100; verify it succeeds (no enforcement) and shows warning |

## Smoke tests — post-deploy

30-second sanity script (after every Console deploy):

```bash
bench --site sppconsole-dev.local console <<EOF
import frappe
# Doctype existence
assert frappe.db.exists("DocType", "Console Master Batch Mixing")
assert frappe.db.exists("DocType", "Console Master Batch Item")
# Mapping seeded
mapping = frappe.db.get_value("Legacy Sync Mapping",
    {"console_process_code": "MASTER_BATCH_MIXING"}, "legacy_doctype")
assert mapping == "Delivery Challan Receipt", f"mapping={mapping}"
# Template active
template = frappe.db.get_value("Console Process Template", "MASTER_BATCH_MIXING", "is_active")
assert template == 1, "MASTER_BATCH_MIXING template inactive!"
# Recent success
recent = frappe.db.get_all("Console Master Batch Mixing",
    filters={"sync_status": "Success", "docstatus": 1},
    order_by="creation desc", limit=1)
print(f"MB Mixing smoke OK. Most recent successful submit: {recent[0].name if recent else 'NONE'}")
EOF
```

## User acceptance tests — manual

The shop-floor user-acceptance gate before declaring "shipped" for any
MB Mixing change:

1. **Operator submits one MB Mixing record from production Dash**
   on `console.m.frappe.cloud` using a real raw-material barcode
2. **Confirms the resulting MB barcode** (printed label) is scannable in
   the next-stage Compound Inspection screen — i.e., the round-trip
   identity holds
3. **Quality Inspector** opens the resulting MB record on
   `sppmaster.frappe.cloud` (legacy DCR), confirms it's linked to a
   submitted Stock Entry
4. **Ops** confirms the FG qty in the target warehouse
   (`Mixing - SPP`) on `newspp.m.frappe.cloud` matches what was submitted
5. **Production overseer** (you) confirms `sync_status = Success` within
   30 seconds of submission

**Acceptance threshold:** 1 successful end-to-end submission with all 5
checks green within a single shift before declaring "done."

## Test gate enforcement

Per project rule `feedback_test_gate.md`: **no code goes out without
all tests passing first.** For any change to MB Mixing layers:

- The 3 shipped unit tests must pass
- If the change touches `apply_bridge_result`, the recommended concurrency
  test must be added first
- If the change touches the Bridge mapping, the value-map test must be added
- Smoke test must pass on staging before declaring the change shipped
- If the change touches the Dash component, an E2E happy-path test should
  be added

Hermes Test Engineer worker enforces these gates as part of the Kanban
"Tests Passing" column transition.
