# Alignment Report: Mixing Process

## 1. Executive Summary

This report evaluates the alignment between the target requirements (`01-requirements/mixing-process`) and the documented architectural reality (`02-specifications/master-batch-mixing` & `02-specifications/final-batch-mixing`). 

Overall, the architectural specifications are **Highly Aligned** with the requirements. The Console-First architecture, "Double-Hop Mirroring", and parallel sync mechanism satisfy the performance, idempotency, and audit requirements. A few specific deviations (e.g., mass-balance checking) are intentional business decisions actively tracked in the specification's Risk logs.

## 2. Functional Requirements Alignment

| Requirement | Description | Status | Implementation Notes |
|---|---|---|---|
| **FR-MIX-001** | Single-operator submission (< 30s) | ✅ Aligned | Dash orchestrates parallel sync (`Promise.all`), typically completing well under the 30s limit (MB: 2-5s, FB: 5-12s). |
| **FR-MIX-002** | Parallel multi-system sync | ✅ Aligned | Handled via `initialize_submission` creating local audit records, then branching to Legacy and Ops targets. |
| **FR-MIX-003** | Partial sync recovery | ✅ Aligned | Enabled by the robust 5-step `apply_bridge_result` aggregation pattern, which correctly infers `Partial` state if only one leg succeeds. |
| **FR-MIX-004** | Audit trail invariant | ✅ Aligned | Strict validation is explicitly bypassed via `flags.from_local_cache = True`, guaranteeing an audit row for all attempts. |
| **FR-MIX-005** | Console-authoritative barcode | ✅ Aligned | Console-generated `C_YYMMDDXn` is successfully mapped as `bridge_mix_barcode` on Legacy and FG batch on Ops. |
| **FR-MIX-006** | Reference ID round-trip | ✅ Aligned | 13-digit timestamp serves as the cross-system idempotency key across Console, Legacy, and Ops. |
| **FR-MIX-021** | FBM Master Batch consumption | ✅ Aligned | `is_batch_item=1` flag controls branching in Legacy `validate_final_batches` to properly execute the batched-FB path. |
| **FR-MIX-031** | Soft mass-balance signal | ⚠️ Misaligned | Planned as a soft warning, but currently **not implemented**. Tracked as an intentional deviation. |

## 3. Business Rules Verification

The architectural specifications rigorously honor the core business rules:

- **BR-MIX-001 (Operation-to-material-type):** The value map correctly routes "Master Batch Mixing" → "Master Batch" and defaults everything else to "Compound". 
- **BR-MIX-004 (Parallel sync):** There is no two-phase commit, avoiding sequential bottlenecking.
- **BR-MIX-006 (Reference ID Idempotency):** The `reference_id` acts as a hard boundary, ensuring that duplicate submissions fail fast at the local layer or bounce harmlessly off the target layers.
- **BR-MIX-014 (Race-safe callback aggregation):** The 5-step atomic dance inside `apply_bridge_result` successfully mitigates concurrent DB update race conditions observed in earlier production phases.

## 4. Gaps, Discrepancies, and Drift

While generally aligned, the following discrepancies and "plan-vs-reality" drifts were identified:

1. **Mass Balance Check (BR-MIX-002)**: The original requirement suggests a soft 5% mass-balance check, but the reality is no check at all. The business accepts this since deviation is tracked downstream.
2. **Workstation Override (FBM)**: In Final Batch Mixing, Legacy auto-resolves the workstation from `Mixing Operation` master data, completely ignoring the Console's submitted value. If master data is missing, it silently defaults to "Two Roll Mixing Mill".
3. **Multi-BOM Validation**: Validation for multiple active BOMs happens on the Legacy side during `create_wo_final_batch_mixing`, not defensively on the Console side. This can cause the legacy leg to fail unexpectedly if BOM data is dirty.
4. **Denormalized Master Data**: `item_code` and `operator_name` in Console Mixing are Data fields, not Link fields. This defers strict referential integrity in favor of decoupled audit speed.

## 5. Recommendations

To fully close the gap between requirements and current architecture, the following actions are recommended for the production overseer:

1. **Reinstate the Soft Mass-Balance Warning**: Implement Dash-side logic to log and display a warning if total consumption deviates > 5% from produced quantity (without blocking submission).
2. **Dash-Side Workstation Verification**: Add a UI check in the FBM component that warns the operator if their selected workstation differs from the Legacy `Mixing Operation` master data mapping.
3. **Unmatched Operation Monitoring**: Add an alert on the `Console Transaction Log` for unmatched operations that fall back to the default `"Compound"` `inward_material_type`, ensuring no new processes are silently misrouted.
4. **Barcode Image Persistence**: Persist the `barcode_image` field URL onto the `Console Master Batch Mixing` / `Console Final Batch Mixing` documents to allow easy reprints, as the field already exists in the transaction log.
