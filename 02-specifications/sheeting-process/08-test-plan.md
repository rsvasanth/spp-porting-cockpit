# 08 — Test plan

## Unit tests — shipped

**File:** `apps/shree_polymer_console/.../doctype/console_sheeting_process/test_console_sheeting_process.py`

Same shape as MB Mixing's 3 tests, adapted for Sheeting:
- `test_create_and_submit_lifecycle`
- `test_partial_payload_still_lands_via_audit_path`
- `test_desk_path_validates_strictly` (with `items` empty triggers throw)

**Run:**
```bash
bench --site sppconsole-dev.local run-tests \
  --module shree_polymer_console.shree_polymer_console.doctype.console_sheeting_process.test_console_sheeting_process
```

## Unit tests — recommended additions

### `test_clip_mapping_written_at_create_time`

```python
def test_clip_mapping_written_at_create_time(self):
    """BCR-1 invariant: clip mappings must exist on Console BEFORE Bridge calls."""
    payload = {"context": {
        "metadata": {"produced_item": "COMPOUND-A", "process_code": "SHEETING_PROCESS"},
        "stock_entry_data": {"item_code": "COMPOUND-A", "qty": 100,
                              "spp_batch_number": "C_26C03X0"},
        "mix_barcode": "C_26C03X0",
        "items": [
            {"item_code": "COMPOUND-A", "batch_no": "C_26C03X0-1", "qty": 30,
             "spp_batch_number": "C_26C03X0-1", "is_cut_bit_item": 0},
            {"item_code": "COMPOUND-A", "batch_no": "C_26C03X0-2", "qty": 30,
             "spp_batch_number": "C_26C03X0-2", "is_cut_bit_item": 0},
            {"item_code": "COMPOUND-A", "batch_no": "Cutbit_C_26C03X0-1", "qty": 10,
             "spp_batch_number": "Cutbit_C_26C03X0-1", "is_cut_bit_item": 1},
        ],
    }}
    doc_name = create_local_sheeting_process(payload, self.reference_id)
    self.assertTrue(doc_name)
    # 2 clips → 2 Item Clip Mapping rows. Cut-bit doesn't get a mapping.
    mappings = frappe.get_all("Console Item Clip Mapping",
        filters={"reference_id": self.reference_id})
    self.assertEqual(len(mappings), 2,
                     "Expected 2 clip mappings (cut-bit excluded)")
```

### `test_cut_bit_flag_detection_by_prefix`

```python
def test_cut_bit_flag_detection_by_prefix(self):
    """populate_sheeting_fields should backfill is_cut_bit_item from batch_no prefix."""
    # This is a Bridge-side test, runs in legacy_bridge app.
    from shree_polymer_legacy_bridge.shree_polymer_legacy_bridge.sync_api import populate_sheeting_fields
    doc = frappe.new_doc("Material Transfer")
    doc.append("batches", {"item_code": "X", "batch_no": "C_TEST-1", "qty": 30})
    doc.append("batches", {"item_code": "X", "batch_no": "Cutbit_C_TEST-1", "qty": 10})
    populate_sheeting_fields(doc, {})
    self.assertEqual(doc.batches[0].is_cut_bit_item, 0)
    self.assertEqual(doc.batches[1].is_cut_bit_item, 1)
    self.assertEqual(doc.cutbit_qty, 10)
```

### `test_apply_bridge_result_with_legacy_spp_batch_no`

```python
def test_apply_bridge_result_with_legacy_spp_batch_no(self):
    """Sheeting captures legacy_spp_batch_no kwarg onto Console doc."""
    doc_name = self._create_test_sheeting()
    doc = frappe.get_doc("Console Sheeting Process", doc_name)
    doc.apply_bridge_result("Legacy", "Success", "MT-2026-001",
                            legacy_spp_batch_no="LEGACY-BATCH-001")
    final = frappe.get_doc("Console Sheeting Process", doc_name)
    self.assertEqual(final.legacy_spp_batch_no, "LEGACY-BATCH-001")
```

### `test_apply_bridge_result_with_impacted_clips_backfill`

```python
def test_apply_bridge_result_backfills_clip_ops_refs(self):
    """When Ops succeeds with impacted_clips, the Item Clip Mappings get Ops batch refs."""
    doc_name = self._create_test_sheeting_with_clip_mappings()
    doc = frappe.get_doc("Console Sheeting Process", doc_name)
    impacted = [{"barcode": "C_TEST-1", "batch_no": "OPS-BATCH-1", ...}]
    doc.apply_bridge_result("Ops", "Success", "MES-LOG-001",
                            impacted_clips=impacted)
    mapping = frappe.get_doc("Console Item Clip Mapping",
                              {"clip_barcode": "C_TEST-1"})
    self.assertEqual(mapping.ops_batch_no, "OPS-BATCH-1")
```

### `test_concurrent_callbacks` (saga-style)

Same as MB's recommended test. Critical because Sheeting has the
additional kwargs path — concurrency tests must verify that
`legacy_spp_batch_no` capture and `impacted_clips` backfill don't
collide.

## Integration tests — parked

Same harness as MB. `scenario_sheeting_process.py` precondition: a
submitted MB → CI → FB chain producing a compound lot.

**Test data:**
- Source compound: `FB_TEST_6123` from FB scenario
- Output count: 3 clips + 1 cut-bit
- Expected sum: 3×30 + 10 = 100 kg

**Scenario assertions:**

1. Console state: Sheeting Process row + 4 Sheeting Item children + 3 Item Clip Mapping rows
2. Legacy state: Material Transfer + 4 batch rows + 3 sheeting_clip rows + cutbit_qty=10 + auto-created SE
3. Ops state: MES Log + Stock Entry with 4 item rows
4. Stock Ledger: compound debited 100, clips + cut-bit credited correctly
5. Downstream readiness: clip barcodes are now scannable for Cut Bit Transfer and Bulk Clip Release

## E2E tests (Playwright)

| Test | What it covers |
|---|---|
| Happy path | Operator scans compound → enters 3 clip + 1 cut-bit outputs → submits → both legs Success |
| Mass balance violation | Outputs total >5% off from source → Dash blocks submit |
| Clip-only submission | No cut-bit rows → submits successfully, no cutbit_qty on legacy |
| Cut-bit-only submission | Only cut-bit rows (rare but valid) → submits successfully, cutbit_qty = total |
| Retry after Ops failure | Kill Ops mid-flight → operator retries → second submission idempotent |

## Smoke tests

```bash
bench --site sppconsole-dev.local console <<EOF
import frappe
assert frappe.db.exists("DocType", "Console Sheeting Process")
assert frappe.db.exists("DocType", "Console Sheeting Item")
assert frappe.db.exists("DocType", "Console Sheeting Clip")
mapping = frappe.db.get_value("Legacy Sync Mapping",
    {"console_process_code": "SHEETING_PROCESS"}, "legacy_doctype")
assert mapping == "Material Transfer", f"mapping={mapping}"
# Verify the literal mapping for material_transfer_type
m = frappe.get_doc("Legacy Sync Mapping", "SHEETING_PROCESS")
mtt_row = next((r for r in m.field_mappings if r.legacy_field == "material_transfer_type"), None)
assert mtt_row, "material_transfer_type mapping missing"
print("Sheeting Process smoke OK")
EOF
```

## User acceptance — manual

1. Operator runs one full sheeting submission with 3 clips + 1 cut-bit
2. Verify each clip's barcode is scannable in Bulk Clip Release screen
3. Verify cut-bit batch is scannable as Final Batch Mixing raw input
4. Verify legacy Material Transfer shows correct material_transfer_type, cutbit_qty, and Stock Entry reference
5. Verify Ops Stock Entry stock ledger reconciles
6. Production overseer (you) confirms `sync_status=Success` + `legacy_spp_batch_no` populated within 30 seconds
