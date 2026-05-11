# 08 — Test plan

## Unit tests — shipped

**File:** `apps/shree_polymer_console/.../doctype/console_compound_deviation/test_console_compound_deviation.py`

Same three-test pattern as MB Mixing:

| Test | What it proves |
|---|---|
| `test_create_and_submit_lifecycle` | Full payload through api → record with deviation fields + Transaction Log |
| `test_partial_payload_still_lands_via_audit_path` | `from_local_cache` bypass leaves diagnostic record |
| `test_desk_path_validates_strictly` | Direct insert without `deviation_reason` throws |

**Plus** Deviation-specific unit tests:

| Test | What it proves |
|---|---|
| `test_deviation_reason_min_length` | Reason < 5 chars throws ValidationError |
| `test_status_default_pending` | If payload omits status, defaults to "Pending" |

**Run:**
```bash
bench --site sppconsole-dev.local run-tests \
  --module shree_polymer_console.shree_polymer_console.doctype.console_compound_deviation.test_console_compound_deviation
```

## Unit tests — gaps (saga-driven priority)

These are **higher priority than for MB** because Compound Deviation is
the process that drove the test-gate rule:

### `test_apply_bridge_result_concurrent_callbacks_deviation`

```python
def test_apply_bridge_result_concurrent_callbacks_deviation(self):
    """The saga's primary regression test. Two threads call apply_bridge_result
    near-simultaneously, one Ops one Legacy. Final state must be Success."""
    import threading
    doc_name = self._create_test_deviation()

    barrier = threading.Barrier(2)
    def call(target):
        barrier.wait()
        d = frappe.get_doc("Console Compound Deviation", doc_name)
        d.apply_bridge_result(target, "Success", f"REMOTE-{target}-001")

    t1 = threading.Thread(target=call, args=("Ops",))
    t2 = threading.Thread(target=call, args=("Legacy",))
    t1.start(); t2.start(); t1.join(); t2.join()

    final = frappe.get_doc("Console Compound Deviation", doc_name)
    self.assertEqual(final.ops_sync_status, "Synced")
    self.assertEqual(final.legacy_sync_status, "Synced")
    self.assertEqual(final.sync_status, "Success")
    self.assertEqual(final.docstatus, 1)
```

**This test is the canonical regression for the saga.** If the 5-step
pattern is ever simplified, this test must fail before being removed.

### `test_apply_bridge_result_self_heal_partial_to_success`

```python
def test_apply_bridge_result_self_heal_partial_to_success(self):
    """Simulate the race that motivated step 4. Manually create the bad state
    (both legs Synced but sync_status=Partial) and verify step 4 corrects."""
    doc_name = self._create_test_deviation()
    frappe.db.set_value("Console Compound Deviation", doc_name, {
        "ops_sync_status":    "Synced",
        "legacy_sync_status": "Synced",
        "sync_status":        "Partial",   # ← the regressed state
    }, update_modified=False)
    frappe.db.commit()

    # Trigger any apply_bridge_result — step 4 should self-heal
    doc = frappe.get_doc("Console Compound Deviation", doc_name)
    doc.apply_bridge_result("Ops", "Success", "OPS-002")

    final = frappe.get_doc("Console Compound Deviation", doc_name)
    self.assertEqual(final.sync_status, "Success")
    self.assertEqual(final.docstatus, 1)
```

### `test_identity_resolution_via_ci_block_priority`

```python
def test_identity_resolution_via_ci_block_priority(self):
    """Verify _pick prioritises compound_inspection_data over compound_deviation_data."""
    payload = {"context": {
        "compound_inspection_data": {"mix_barcode": "FROM_CI_BLOCK"},
        "compound_deviation_data":  {"mix_barcode": "FROM_DEV_BLOCK"},
    }}
    doc_name = create_local_compound_deviation(payload, self.reference_id)
    doc = frappe.get_doc("Console Compound Deviation", doc_name)
    self.assertEqual(doc.mix_barcode, "FROM_CI_BLOCK")
```

### `test_status_validation`

```python
def test_status_validation(self):
    """Status must be one of Accepted/Rejected/Rework/Pending."""
    for valid in ["Accepted", "Rejected", "Rework", "Pending"]:
        payload = {"context": {
            "compound_inspection_data": {"item_code": "X", "transfer_qty": 10},
            "compound_deviation_data":  {"status": valid, "deviation_reason": "valid reason here"},
        }}
        doc_name = create_local_compound_deviation(payload, f"TEST-STATUS-{valid}")
        doc = frappe.get_doc("Console Compound Deviation", doc_name)
        self.assertEqual(doc.status, valid)
```

## Bridge-side tests

The shared identity helpers (`_resolve_compound_identity`, `_lookup_legacy_stock_entry`) have unit tests in the Bridge app at `apps/shree_polymer_legacy_bridge/.../test_compound_helpers.py` (or similar — verify location during cockpit setup).

Critical tests:
- `test_six_strategy_chain_priority` — verifies strategies fire in priority order
- `test_strategy_six_last_ditch_batch_no` — verifies last fallback works
- `test_idempotent_apply_identity` — re-running doesn't overwrite

If these don't exist, they should be added before any Bridge refactor.

## Integration tests — parked (shared harness with MB)

`scenario_compound_deviation.py` precondition: a Compound Inspection with
`status=Rejected` must exist on Console + Ops (Legacy skipped by factory
requirement). The MB Mixing scenario creates an MB, FB scenario creates
a Compound, and a CI scenario creates the rejected CI — Deviation
scenario chains off all of these.

**Confirmed test data:**

| Item | Value |
|---|---|
| Source Compound | `FB_TEST_6123` (from FB scenario) |
| QM employee | `HR-EMP-00201` (role: Quality Manager) |
| Test deviation_reason | `"E2E test deviation — auto-generated"` |
| Test status | Parameterised over `Accepted` / `Rejected` / `Rework` |

**Scenario assertions per status:**

| Status | Legacy CI state | Legacy SE | Ops MES result |
|---|---|---|---|
| Accepted | status=Accepted | Material Transfer SE submitted | impacted_balances has the compound moving from inspection-WIP to ready warehouse |
| Rejected | status=Rejected | Material Issue / write-off SE submitted | impacted_balances empty (action skipped) |
| Rework | status=Rework | No SE | impacted_balances empty (action skipped) |

## E2E tests (Playwright)

| Test | What it covers |
|---|---|
| Happy path — Accepted Deviation | QM scans barcode → fetches CI → enters reason → Accepted → submits → success modal |
| Happy path — Rejected Deviation | Same flow with Rejected status → verify no Ops SE created |
| Happy path — Rework Deviation | Same with Rework → verify no SE on either side |
| Wrong role | Non-QM user opens screen → submit button disabled |
| Reason too short | Enter 3-char reason → validation message → submit blocked |
| Source CI not Rejected | Try to deviate from an Accepted CI → Dash blocks |
| Concurrent submission | Two QMs open the same CI at the same time → second submission either succeeds (per-Console-Inspection-record idempotency) or fails cleanly |

## Smoke tests

```bash
bench --site sppconsole-dev.local console <<EOF
import frappe
assert frappe.db.exists("DocType", "Console Compound Deviation")
mapping = frappe.db.get_value("Legacy Sync Mapping",
    {"console_process_code": "COMPOUND_DEVIATION"}, "legacy_doctype")
assert mapping == "Compound Inspection"
# Confirm empty field_mappings (the architectural fact)
m = frappe.get_doc("Legacy Sync Mapping", "COMPOUND_DEVIATION")
assert len(m.field_mappings) == 0, f"COMPOUND_DEVIATION should have empty mappings, has {len(m.field_mappings)}"
template = frappe.db.get_value("Console Process Template", "COMPOUND_DEVIATION", "is_active")
assert template == 1
recent = frappe.db.get_all("Console Compound Deviation",
    filters={"sync_status": "Success", "docstatus": 1},
    order_by="creation desc", limit=1)
print(f"Compound Deviation smoke OK. Most recent: {recent[0].name if recent else 'NONE'}")
EOF
```

## User acceptance — manual

Most critical UAT step for Compound Deviation:

1. QM submits one Rejected Deviation on production-staging
2. **Verify the legacy `Compound Inspection` record's `cavity_no` field
   shows the structured-log entry** — confirms the fallback fired
   correctly without breaking submission
3. QM submits one Accepted Deviation
4. Verify the Material Transfer SE on Ops moved the compound to the
   ready warehouse
5. Verify Stock Ledger reconciles between Ops + Legacy
6. **Production overseer (you):** verify the saga's invariant — both
   legs reach Success and Console auto-submits the deviation record

**Acceptance threshold:** 1 Rejected + 1 Accepted submission successful
within a single shift, with `cavity_no` fallback log entries visible in
the Bridge's Error Log.
