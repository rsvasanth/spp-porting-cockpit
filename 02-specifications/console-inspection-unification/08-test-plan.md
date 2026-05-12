# 08 — Test plan

## Unit tests — shipped

**Files:**
- `apps/shree_polymer_console/.../doctype/console_inspection/test_console_inspection.py`
- `apps/shree_polymer_console/.../doctype/console_compound_inspection/test_console_compound_inspection.py`
- `apps/shree_polymer_console/.../doctype/console_compound_deviation/test_console_compound_deviation.py` (covered in CD spec)

Same three-test pattern as MB:
- `test_create_and_submit_lifecycle`
- `test_partial_payload_still_lands_via_audit_path`
- `test_desk_path_validates_strictly`

Plus unification-specific:
- `test_inspection_family_drives_identity` — Compound family → mix_barcode required; Production → lot_no required
- `test_phase_3_dispatch_routes_to_unified` — Submitting any `is_inspection_type=1` process lands in `Console Inspection`, NOT the legacy per-type doctype

**Run:**
```bash
bench --site sppconsole-dev.local run-tests \
  --module shree_polymer_console.shree_polymer_console.doctype.console_inspection.test_console_inspection
```

## Unit tests — recommended additions

### `test_validation_dispatch_runs_registered_function`

```python
def test_validation_dispatch_runs_registered_function(self):
    """Registering a validation_dispatch_method on a Process Template causes it
    to fire during validate()."""
    # Setup: register a custom validation function
    frappe.db.set_value("Console Process Template", "COMPOUND_INSPECTION",
        "validation_dispatch_method", "shree_polymer_console.api.test_validation_hook")

    # Define the hook (in a test-helper module)
    # ... that flips a flag on the doc ...

    payload = {"context": {
        "metadata": {"process_code": "COMPOUND_INSPECTION"},
        "compound_inspection_data": {"mix_barcode": "TEST-001", "readings": [...]},
    }}
    doc_name = create_local_inspection(payload, self.reference_id)
    doc = frappe.get_doc("Console Inspection", doc_name)
    self.assertEqual(doc.test_validation_ran, True)  # confirms dispatch fired
```

### `test_apply_bridge_result_byte_identical_across_doctypes`

```python
def test_apply_bridge_result_pattern_is_consistent(self):
    """The 5-step pattern must be byte-identical across:
    Console Inspection, Console Compound Inspection, Console Compound Deviation."""
    import inspect
    from shree_polymer_console.shree_polymer_console.doctype.console_inspection.console_inspection import ConsoleInspection
    from shree_polymer_console.shree_polymer_console.doctype.console_compound_inspection.console_compound_inspection import ConsoleCompoundInspection
    from shree_polymer_console.shree_polymer_console.doctype.console_compound_deviation.console_compound_deviation import ConsoleCompoundDeviation

    sigs = [
        inspect.getsource(ConsoleInspection.apply_bridge_result),
        inspect.getsource(ConsoleCompoundInspection.apply_bridge_result),
        inspect.getsource(ConsoleCompoundDeviation.apply_bridge_result),
    ]
    self.assertEqual(sigs[0], sigs[1], "ConsoleInspection != ConsoleCompoundInspection apply_bridge_result")
    self.assertEqual(sigs[1], sigs[2], "ConsoleCompoundInspection != ConsoleCompoundDeviation")
```

### `test_apply_bridge_result_concurrent_callbacks_all_three`

Run the canonical concurrency regression test for each of the three doctypes. This is the **saga regression test** — must pass for all three after any race-safety code change.

### `test_factory_requirement_skip_rejected_ci`

```python
def test_rejected_ci_skips_legacy_leg(self):
    """A Compound Inspection with status=Rejected must route Ops-only."""
    payload = {"context": {
        "metadata": {"process_code": "COMPOUND_INSPECTION"},
        "compound_inspection_data": {"mix_barcode": "TEST-002"},
        "status": "Rejected",
    }}
    result = initialize_submission(payload)
    # Verify target_logs has only Ops, not Legacy
    targets = [t["target"] for t in result.get("target_logs", [])]
    self.assertIn("Ops", targets)
    self.assertNotIn("Legacy", targets)
```

### `test_pre_phase_3_doctype_callback_routing`

```python
def test_module_level_apply_bridge_result_finds_pre_phase_3_record(self):
    """If a callback arrives for a pre-Phase-3 record, the module-level
    apply_bridge_result dispatcher finds it via the parent_doctypes list."""
    # Create a Console Compound Deviation record (pre-Phase-3 doctype)
    # Call module-level apply_bridge_result with its reference_id
    # Verify the per-type doctype's apply_bridge_result was invoked
```

## Integration tests — parked

Shared harness with other motions. Inspection scenarios:

| Scenario | Pre-condition | Assertion |
|---|---|---|
| CI Accepted happy path | MB lot exists; readings within spec | Console Inspection submitted; Legacy + Ops have records; Material Transfer SE created |
| CI Rejected (factory-requirement skip) | MB lot; reading out of spec | Console Inspection Partial; Ops has MES Log but no SE; Legacy has no record |
| CD Accept-override | Rejected CI exists | Legacy CI now exists with status=Accepted; QM signoff fields populated; Material Transfer SE created |
| CD Rejected (write-off) | Rejected CI exists | Material Issue SE on both ERPs |
| CD Rework | Rejected CI exists | No SE created on either ERP |

## E2E tests (Playwright)

| Test | Coverage |
|---|---|
| CompoundInspectionEntry happy path (Accepted) | UI → submit → success modal with both legs ✅ |
| CompoundInspectionEntry happy path (Rejected) | UI → submit → success modal with Ops ✅ Legacy skipped |
| CompoundDeviationEntry override (Accept) | UI → scan rejected CI → submit Accepted CD → both legs ✅ |
| Wrong-role access | QI cannot access CD; QM cannot submit CI (read-only) |

## Smoke tests

```bash
bench --site sppconsole-dev.local console <<EOF
import frappe
assert frappe.db.exists("DocType", "Console Inspection")
assert frappe.db.exists("DocType", "Console Inspection Reading")
assert frappe.db.exists("DocType", "Console Inspection Reading Spec")
# Pre-Phase-3 doctypes preserved
assert frappe.db.exists("DocType", "Console Compound Inspection")
assert frappe.db.exists("DocType", "Console Compound Deviation")
# Process Templates with is_inspection_type=1
templates = frappe.db.get_all("Console Process Template",
    filters={"is_inspection_type": 1}, fields=["name", "inspection_family"])
assert len(templates) >= 2, "Expect at least COMPOUND_INSPECTION + COMPOUND_DEVIATION"
print(f"Inspection unification smoke OK. {len(templates)} inspection types registered")
EOF
```

## User acceptance — manual

For each inspection_type, run the standard 5-step UAT (similar to other motions):

1. Operator submits one record via Dash
2. Confirms identity round-trip to both ERPs
3. QA reviews the resulting legacy Compound Inspection record (status, signoff fields)
4. Stock Ledger reconciles for SE creation cases
5. Production overseer confirms `sync_status=Success` within 30 seconds

Across at least one CI Accepted, one CI Rejected → CD Accepted, one CD Rejected, one CD Rework.

## Test gate enforcement

For any change to inspection-related modules:
- 5-step `apply_bridge_result` concurrency test on ALL three doctypes
- Validation dispatch test if `validation_dispatch_method` mechanism is touched
- Family-driven identity test if `create_local_inspection` is modified
- Pre-Phase-3 backward-compat test if `parent_doctypes` list is changed
- Factory-requirement-skip test if `initialize_submission` Legacy-leg routing is touched
