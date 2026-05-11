# 08 — Test plan

## Unit tests — shipped

**File:** `apps/shree_polymer_console/.../doctype/console_final_batch_mixing/test_console_final_batch_mixing.py`

Same three tests as MB Mixing, with the doctype name and process_code
swapped:

| Test | What it proves |
|---|---|
| `test_create_and_submit_lifecycle` | Full FB payload through api → record with child rows + Transaction Log |
| `test_partial_payload_still_lands_via_audit_path` | `from_local_cache` bypass leaves diagnostic record |
| `test_desk_path_validates_strictly` | Direct insert with qty=0 + empty children throws |

**Run:**
```bash
bench --site sppconsole-dev.local run-tests \
  --module shree_polymer_console.shree_polymer_console.doctype.console_final_batch_mixing.test_console_final_batch_mixing
```

## Unit tests — gaps (FB-specific)

Beyond the MB recommendations (concurrency, partial recovery, uniqueness,
backdating, value-map), FB needs these:

### `test_is_batch_item_flag_triggers_batched_path`

Asserts that a payload with `consumption_items[0].is_batch_item=1` results
in a DCR `dc_items` row with `is_batch_item=1`, which would route
`validate_final_batches` into the batched FB path.

This test runs on Console side (mock Bridge); the legacy-side branching
is exercised via integration tests.

### `test_value_map_inward_material_type_compound`

Same shape as MB's recommended `test_value_map_inward_material_type`, but
asserts FB direction:

```python
def test_value_map_fb_inward_material_type(self):
    mapping = frappe.get_doc("Legacy Sync Mapping", "FINAL_BATCH_MIXING")
    inward_row = next((r for r in mapping.field_mappings
                       if r.legacy_field == "inward_material_type"), None)
    vm = json.loads(inward_row.value_map)
    self.assertEqual(vm.get("Final Batch Mixing"), "Compound")
    self.assertEqual(inward_row.default_value, "Compound")  # both FB and default land here
```

### `test_multi_bom_rejection_on_legacy`

This requires a legacy-side test or an integration test. If the produced
item has more than one active BOM, the FB submission should fail with the
"Multiple BOM's found" error. Asserts the Console Transaction Log Legacy
row ends in `Failed` with the expected error message.

### `test_mb_consumption_row_first`

```python
def test_mb_consumption_row_is_first(self):
    """FB payload's consumption_items[0] must be the MB input (is_batch_item=1)."""
    payload = {"context": {
        "metadata": {"produced_item": "COMPOUND-001", "process_code": "FINAL_BATCH_MIXING",
                     "item_group": "Compound"},
        "stock_entry_data": {
            "fg_qty": 100,
            "consumption_items": [
                {"item_code": "MB-001", "qty": 10, "is_batch_item": 1,
                 "mix_barcode": "C_26C03X0"},   # MB input
                {"item_code": "RM-002", "qty": 90, "is_batch_item": 0},
            ]}}}
    doc_name = create_local_final_batch_mixing(payload, self.reference_id)
    doc = frappe.get_doc("Console Final Batch Mixing", doc_name)
    self.assertEqual(doc.consumption_items[0].item_code, "MB-001")
    self.assertEqual(doc.consumption_items[0].mix_barcode, "C_26C03X0")
```

## Integration tests — parked (shared harness with MB)

The parked harness in `06_INTEGRATION_TESTS_TODO.md` covers both MB and FB
because they share the bench-test framework. FB scenario file:

**`scenario_final_batch_mixing.py` — preconditions:**

1. MB lot exists on Console + Ops + Legacy with `sync_status=Success`
2. MB lot's `mix_barcode` is scannable (i.e. `Item Batch Stock Balance`
   row exists on legacy with non-empty `mix_barcode`)
3. FB FG item has exactly one active BOM
4. The BOM lists the MB item + the additional raw materials

**Scenario assertions (delta from MB scenario):**

1. Same as MB scenario assertions, AND
2. Legacy DCR has `dc_items[0].is_batch_item = 1` for the MB row
3. Legacy DCR's `validate_final_batches` ran the **batched** path
4. Two legacy Stock Entries created (MB consumption + Compound production)
5. The MB input's batch was correctly consumed on the Stock Ledger
6. The Compound's FG row on the Ops SE has `mix_barcode` matching the
   Console-generated FB barcode

**Confirmed FB test data:**

| Item | Value |
|---|---|
| Produced (FG) | `FB_TEST_6123` (Compound) |
| MB input | `MB_TEST_6122` (the same FG from MB scenario) |
| Additional raw | `B_TEST_6124` |
| BOM | `BOM-FB_TEST_6123-001` |

## E2E tests (Playwright)

Same as MB plus:

| Test | What it covers |
|---|---|
| Happy path — batched FB | Operator scans MB lot, scans raw materials, submits, sees success modal with Compound barcode |
| MB input out of stock | Try to submit with an MB lot whose stock is 0 — should fail with stock validation error at Ops side |
| MB barcode invalid | Scan a barcode that doesn't exist → Dash shows error, doesn't add to scannedItems |
| Multi-BOM rejection | Use an FG item with two active BOMs → Bridge call fails, operator sees Failed row |

## Smoke tests

```bash
bench --site sppconsole-dev.local console <<EOF
import frappe
assert frappe.db.exists("DocType", "Console Final Batch Mixing")
assert frappe.db.exists("DocType", "Console Final Batch Item")
mapping = frappe.db.get_value("Legacy Sync Mapping",
    {"console_process_code": "FINAL_BATCH_MIXING"}, "legacy_doctype")
assert mapping == "Delivery Challan Receipt"
template = frappe.db.get_value("Console Process Template", "FINAL_BATCH_MIXING", "is_active")
assert template == 1
recent = frappe.db.get_all("Console Final Batch Mixing",
    filters={"sync_status": "Success", "docstatus": 1},
    order_by="creation desc", limit=1)
print(f"FB Mixing smoke OK. Most recent: {recent[0].name if recent else 'NONE'}")
EOF
```

## User acceptance — manual

Same 5-step UAT as MB Mixing, plus:

6. **Quality Inspector** confirms the produced Compound's batch matches
   the MB input in the next-stage Compound Inspection screen (i.e. FB
   round-trip identity holds through to Compound Inspection)

**Acceptance threshold:** 1 successful end-to-end batched FB submission
with all 6 checks green within a single shift.
