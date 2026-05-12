# 08 — Test plan

## Unit tests — to be implemented

Standard pattern: 3 tests + branching coverage.

```python
class TestConsoleBlankBinInwardEntry(FrappeTestCase):
    def setUp(self):
        # Standard reference_id cleanup
        ...

    def test_create_and_submit_bin_path(self):
        """Default bin path: move_to_cut_bit=0."""
        payload = {"context": {
            "metadata": {"process_code": "BLANK_BIN_INWARD"},
            "bin_code": "BIN-TEST-001",
            "item": "COMPOUND-TEST",
            "net_weight_kgs": 25,
            "gross_weight_kgs": 30,
            "move_to_cut_bit_warehouse": 0,
        }}
        doc_name = create_local_blank_bin_inward_entry(payload, self.reference_id)
        doc = frappe.get_doc("Console Blank Bin Inward Entry", doc_name)
        self.assertEqual(doc.move_to_cut_bit_warehouse, 0)

    def test_create_and_submit_cut_bit_path(self):
        """Cut-bit repack path: move_to_cut_bit=1."""
        payload = {"context": {
            "metadata": {"process_code": "BLANK_BIN_INWARD"},
            "bin_code": "BIN-TEST-002",
            "item": "COMPOUND-TEST",
            "net_weight_kgs": 18,
            "move_to_cut_bit_warehouse": 1,
            "cut_bit_batch": "Cutbit_COMPOUND-TEST",
        }}
        doc_name = create_local_blank_bin_inward_entry(payload, self.reference_id_2)
        doc = frappe.get_doc("Console Blank Bin Inward Entry", doc_name)
        self.assertEqual(doc.move_to_cut_bit_warehouse, 1)
        self.assertEqual(doc.cut_bit_batch, "Cutbit_COMPOUND-TEST")

    def test_cut_bit_path_requires_cut_bit_batch(self):
        """If move_to_cut_bit=1 without cut_bit_batch, validation throws."""
        payload_invalid = {"context": {
            "metadata": {"process_code": "BLANK_BIN_INWARD"},
            "bin_code": "BIN-TEST-003",
            "item": "X",
            "net_weight_kgs": 10,
            "move_to_cut_bit_warehouse": 1,
            # cut_bit_batch missing
        }}
        with self.assertRaises(frappe.ValidationError):
            doc = frappe.get_doc({"doctype": "Console Blank Bin Inward Entry",
                                  "reference_id": "TEST-BBIE-INVALID",
                                  "bin_code": "BIN-TEST-003",
                                  "net_weight_kgs": 10,
                                  "move_to_cut_bit_warehouse": 1})
            doc.insert(ignore_permissions=True)

    def test_concurrent_callbacks_safety(self):
        """5-step apply_bridge_result pattern under concurrent Ops + Legacy callbacks."""
        # Standard saga regression test pattern
        ...
```

## Bridge tests

- Bin path: `populate_blank_bin_inward_fields` sets `target_warehouse` to Moulding Unit warehouse
- Cut-bit path: target_warehouse to cut-bit warehouse + cut_bit_batch validated
- Bin state check: bin in non-Filled state rejects with clear error
- Idempotency: retry with same reference_id returns existing record

## Ops tests

- Bin path: Asset Movement created with correct source/target locations
- Cut-bit path: Stock Entry Repack created with Cutbit_<item> batch + `use_serial_batch_fields=1`
- `run_legacy_sync=False` enforced from Console path
- Idempotency via MES Log

## E2E tests (Playwright)

| Test | What it covers |
|---|---|
| Happy path bin | Scan bin → toggle off → submit → both legs Success → bin Asset state = Inward |
| Happy path cut-bit | Scan bin → toggle on → cut-bit batch shown → submit → both legs Success → bin Asset state = Available |
| Wrong bin state | Scan empty bin → validation rejects |
| Weight drift soft warning | Re-enter weight differing > 5% → warning visible, submit still allowed |

## Smoke tests

```bash
bench --site sppconsole-dev.local console <<EOF
import frappe
assert frappe.db.exists("DocType", "Console Blank Bin Inward Entry"), "BBIE doctype missing"
mapping = frappe.db.get_value("Legacy Sync Mapping",
    {"console_process_code": "BLANK_BIN_INWARD"}, "legacy_doctype")
assert mapping == "Blank Bin Inward Entry"
template = frappe.db.get_value("Console Process Template", "BLANK_BIN_INWARD", "is_active")
assert template == 1
print("BBIE smoke OK")
EOF
```

## User acceptance — manual

1. Material Handler runs one bin-path BBIE submission
2. Verify bin Asset on Legacy shows "Inward at Moulding Unit" state
3. Run one cut-bit-path BBIE submission
4. Verify Cut-Bit warehouse stock incremented; bin returned to Available
5. Verify Ops mirror records match
6. Production overseer confirms `sync_status=Success` within 30 seconds
