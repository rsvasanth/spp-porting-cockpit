# 08 — Test plan

Tests are organized by acceptance criterion (`AC-QC-<n>` from `01-requirements/quality-control/06-acceptance-criteria.md`).

## Unit tests (Console controller)

### Template gate
- `test_submit_blocks_when_no_active_template` — AC-QC-01
- `test_submit_blocks_when_template_inactive` — AC-QC-01
- `test_validate_template_for_item_endpoint_returns_missing` — AC-QC-01

### Reading validation
- `test_reading_status_pass_at_min_bound` (inclusive) — AC-QC-04
- `test_reading_status_pass_at_max_bound` (inclusive) — AC-QC-04
- `test_reading_status_fail_below_min` — AC-QC-05
- `test_reading_status_fail_above_max` — AC-QC-05
- `test_validate_recomputes_status_overriding_frontend` — AC-QC-06

### Calculations
- `test_moulding_rejected_kg_computed_from_pieces` — AC-QC-07
- `test_incoming_qty_in_nos_no_conversion` — AC-QC-08
- `test_one_no_qty_equal_kgs_snapshotted_at_validate` — BR-QC-08

### Identity
- `test_same_employee_inspector_operator_blocked` — AC-QC-15
- `test_unresolved_lot_blocks_submit` — AC-QC-16
- `test_employee_barcode_resolution` — FR-QC-02

### Reference & idempotency
- `test_reference_id_generated_on_first_submit` — BR-QC-10
- `test_duplicate_reference_id_reuses_existing_log` — AC-QC-11

### Permissions
- `test_quality_inspector_can_create_and_submit` — AC-QC-17
- `test_operator_cannot_create_qc` — AC-QC-17
- `test_supervisor_can_cancel_qc` — AC-QC-18
- `test_inspector_cannot_cancel_submitted_qc` — AC-QC-18

## Integration tests (Console + Ops)

### Stock Entry creation
- `test_line_inspection_creates_draft_se_on_ops` — AC-QC-09
- `test_patrol_inspection_creates_draft_se` — AC-QC-09
- `test_lot_inspection_creates_draft_se` — AC-QC-09
- `test_incoming_creates_draft_se_in_nos` — AC-QC-09
- `test_final_visual_creates_submitted_se` — AC-QC-10
- `test_final_visual_moves_stock_to_pdir_warehouse` — AC-QC-10

### Warehouse routing
- `test_warehouses_resolved_from_process_template` — BR-QC-07
- `test_changing_template_warehouse_affects_next_submission` — BR-QC-07

### Idempotency
- `test_retry_with_same_reference_id_no_duplicate_se` — AC-QC-11

### Cancellation
- `test_cancel_blocked_when_stock_consumed` — AC-QC-12
- `test_cancel_cascades_when_stock_free` — AC-QC-13
- `test_cancel_logs_in_transaction_log` — AC-QC-14
- `test_cancel_halts_on_legacy_failure_keeps_local_submitted` — FR-QC-18 failure path

## Integration tests (Console + Legacy)

### Mirror
- `test_legacy_inspection_entry_created_on_qc_submit` — FR-QC-16
- `test_legacy_cancelled_on_qc_cancel` — AC-QC-13
- `test_legacy_failure_leaves_console_submitted_for_retry` — NFR-QC-04

### Field mapping
- `test_field_mapping_inspector_to_inspected_by_id` — see `05-legacy-erpnext.md`
- `test_field_mapping_mould_reference_to_mould_no` — see `05-legacy-erpnext.md`
- `test_reading_rows_mirrored` — child table parity

## Sync tests

- `test_template_sync_pulls_new_template` — FR-QC-04
- `test_template_sync_updates_existing_template` — incremental update
- `test_template_sync_tombstones_inactive_template` — `is_active=0` handling
- `test_on_demand_sync_completes_within_5s` — NFR-QC-07
- `test_hourly_sync_scheduled` — NFR-QC-08

## E2E tests (Playwright / Cypress)

- `e2e_full_line_inspection_happy_path` — scan → grid → submit → SE on Ops
- `e2e_template_missing_block_then_sync_then_submit` — recovery flow
- `e2e_supervisor_cancel_with_consumed_stock_blocks` — AC-QC-12
- `e2e_supervisor_cancel_full_cascade_succeeds` — AC-QC-13
- `e2e_scanner_keyboard_focus_progression` — FR-QC-01 (no mouse)

## Coverage targets

- Console controller (`spp_quality_control.py`): ≥85% line coverage.
- Bridge handlers (`spp_quality_control` modules in api.py + legacy_bridge): ≥80%.
- Ops handler (`shree_polymer_ops.api.spp_quality_control`): ≥80%.
- Frontend component (`SPPQualityControlEntry.tsx`): smoke + integration only; E2E covers user flows.

## Negative-path priorities

The legacy QC implementation drifted via untested error paths. The QC test suite MUST prioritize negative-path coverage:

1. Template-missing-then-stale-sync.
2. Bridge timeout after Ops SE creation.
3. Legacy failure after Ops success.
4. Concurrent submission attempts with the same reference_id.
5. Cancellation with consumed stock.
6. Cancellation with offline Legacy.
7. Inspector badge scan that resolves to inactive Employee.
8. Lot scan resolving to multiple Job Cards (ambiguous lot).
9. Reading value submitted as string / NaN / negative / scientific notation.
10. Template modified on Ops between scan-resolve and submit (sync_hash mismatch).

Each negative path MUST have a dedicated test asserting the documented system behavior (not just that "something errors").
