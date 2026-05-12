# 08 — Test plan

## Unit tests — to be implemented

```python
class TestConsoleAddOnWorkPlanning(FrappeTestCase):
    def test_create_and_submit_single_row(self):
        """Single-row AOWP generates Lot # + Job Card."""
        payload = {"context": {
            "metadata": {"process_code": "ADD_ON_WORK_PLANNING"},
            "shift_type": "Morning",
            "supervisor_id": "HR-EMP-00001",
            "items": [{"item_produced": "COMPOUND-TEST", "work_station": "Two Roll Mixing Mill",
                       "target_qty": 100, "bom": "BOM-TEST-001"}]
        }}
        doc_name = create_local_add_on_work_planning(payload, self.reference_id)
        doc = frappe.get_doc("Console Add On Work Planning", doc_name)
        self.assertTrue(doc.lot_number.startswith("LOT-"))
        self.assertEqual(len(doc.items), 1)
        # Verify lot_number cascaded to child
        self.assertEqual(doc.items[0].lot_number, doc.lot_number)

    def test_lot_number_sequence(self):
        """Two successive submissions get sequential Lot #s."""
        payload1 = {...}
        d1 = create_local_add_on_work_planning(payload1, "TEST-1")
        payload2 = {...}
        d2 = create_local_add_on_work_planning(payload2, "TEST-2")
        ln1 = frappe.db.get_value("Console Add On Work Planning", d1, "lot_number")
        ln2 = frappe.db.get_value("Console Add On Work Planning", d2, "lot_number")
        seq1 = int(ln1.split("-")[-1])
        seq2 = int(ln2.split("-")[-1])
        self.assertEqual(seq2, seq1 + 1)

    def test_lot_number_daily_reset(self):
        """Lot # sequence resets on new posting_date."""
        # ... submit one for today, one for tomorrow ...
        # ... assert tomorrow's seq starts at 001 ...

    def test_concurrent_lot_number_generation(self):
        """5 concurrent submissions get unique Lot #s, no duplicates."""
        import threading
        results = []
        def submit():
            payload = {"context": {...}}
            d = create_local_add_on_work_planning(payload, f"TEST-CONC-{threading.current_thread().name}")
            results.append(frappe.db.get_value("Console Add On Work Planning", d, "lot_number"))

        threads = [threading.Thread(target=submit) for _ in range(5)]
        for t in threads: t.start()
        for t in threads: t.join()

        self.assertEqual(len(set(results)), 5, "All 5 Lot #s must be unique")

    def test_multi_bom_rejection(self):
        """Item with > 1 active BOM rejects."""
        # ... create 2 active BOMs for an item ...
        with self.assertRaises(frappe.ValidationError):
            doc = frappe.get_doc({"doctype": "Console Add On Work Planning",
                                  "reference_id": "TEST-MULTI-BOM",
                                  "shift_type": "Morning",
                                  "items": [{"item_produced": "MULTI-BOM-ITEM",
                                             "target_qty": 100,
                                             "work_station": "Mill"}]})
            doc.insert(ignore_permissions=True)

    def test_apply_bridge_result_concurrent_callbacks(self):
        """5-step race-safety pattern."""
        # Standard saga regression test
        ...
```

## Bridge tests

- `seed_add_on_work_planning_mapping` produces correct field_mappings
- Bridge mapping engine resolves placeholders for AOWP payload
- `create_planning_with_jobcards` atomic rollback when Job Card creation fails mid-flight
- Workstation override applied when Mixing Operation row exists
- Idempotency via reference_id

## Ops tests

- Generic TransactionEngine processes AOWP sequence correctly
- Work Order + Job Cards created with `lot_number` custom field set
- `for_each items` iteration creates correct number of Job Cards
- Cross-step output chaining (work_order_name → Job Card.work_order) works

## E2E tests (Playwright)

| Test | Coverage |
|---|---|
| Happy path single-row | submit → Lot # generated → both ERPs have WO + JC |
| Happy path multi-row (3 items) | one WO + 3 JCs created on each ERP |
| Multi-BOM rejection | error surfaces; submit blocked |
| Target qty drift warning | inline warning visible; can override |
| Workstation override transparency | banner shown pre-submit |
| Concurrent submission by 2 supervisors | both get unique Lot #s |

## Smoke tests

```bash
bench --site sppconsole-dev.local console <<EOF
import frappe
assert frappe.db.exists("DocType", "Console Add On Work Planning")
mapping = frappe.db.get_value("Legacy Sync Mapping",
    {"console_process_code": "ADD_ON_WORK_PLANNING"}, "legacy_doctype")
assert mapping == "Add On Work Planning"
print("AOWP smoke OK")
EOF
```

## User acceptance — manual

1. Production Supervisor runs AOWP with 2 items
2. Verify generated Lot # displayed on success modal
3. Verify Legacy: WO + 2 JCs created with matching Lot #
4. Verify Ops: WO + 2 JCs with `lot_number` custom field
5. Downstream Blank Bin Issue can scan Lot # and find Job Cards
6. Production overseer confirms `sync_status=Success` within 30 seconds
