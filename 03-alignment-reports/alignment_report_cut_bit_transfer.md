# Alignment Report: Cut Bit Transfer

## 1. Executive Summary

This report evaluates the alignment between the target requirements (`01-requirements/cut-bit-transfer`) and the documented architectural specifications (`02-specifications/cut-bit-transfer`).

Overall, the Cut Bit Transfer (CBT) process is **Highly Aligned** with the requirements. It effectively implements a repack/recycling flow to standardize identity (`Cutbit_...`) for downstream Final Batch Mixing. A few crucial deviations center around legacy system idempotency and testing drift related to clip vs. bin mapping retirement.

## 2. Functional Requirements Alignment

| Requirement | Description | Status | Implementation Notes |
|---|---|---|---|
| **FR-CBT-003, 004** | Relay validation (Console -> Ops -> Legacy) | ✅ Aligned | Dash validation gracefully checks Console mappings, then relays through Ops API to find native batches if missing. |
| **FR-CBT-011, 012** | Dedicated repack execution | ✅ Aligned | Unlike generic processes, Ops routes CBT to a dedicated `submit_cut_bit_transfer` handler to manage specific `Repack` side effects. |
| **FR-CBT-013** | Console owns parallel sync | ✅ Aligned | Ops receives the `run_legacy_sync=False` flag, preventing a race where Ops and Console both attempt to sync to Legacy. |
| **FR-CBT-014 to 016** | Warehouse routing | ✅ Aligned | Handled securely through legacy rules directing Compound -> Sheeting, Blanking -> Unit 2, and others to Blanking. |
| **FR-CBT-018** | Output identity conventions | ✅ Aligned | Preserves `Cutbit_<item_code>` for batches and `CB_<item_code>` for mix barcodes, matching downstream FB Mixing scan logic. |
| **FR-CBT-019** | Bin qty reduction vs Clip preservation | ✅ Aligned | `_write_clip_mappings_for_cut_bit` accurately reduces Bin quantities but intentionally defers Clip retirement to downstream Blanking processes. |

## 3. Business Rules Verification

The architectural specifications rigorously honor the core business rules:

- **BR-CBT-001 (Repack logic):** Effectively implemented as a repack step (not new production), converting legacy identities to a standard recycling identity.
- **BR-CBT-009 (No double sync):** Verified in the execution trace; the Console effectively governs the 5-step aggregation independently of the Ops-side logic.
- **BR-CBT-010 & 011 (Mapping Lifecycle):** Clip mappings are accurately kept alive, while bin mappings are retired/reduced proportionally. 

## 4. Gaps, Discrepancies, and Drift

1. **Weak Legacy Idempotency (NFR-CBT-006 / Delta #4)**: The Legacy `Cut Bit Transfer` doctype lacks a stable `reference_id` field. The Bridge compensates with a weak check based on the first scanned barcode and a 10-minute creation window. This can cause false negatives on delayed retries.
2. **Testing Documentation Drift (Delta #3)**: Existing Console tests assert that CBT handles clip mapping creation/retirement, directly conflicting with current code/business rules which intentionally leave clips untouched.
3. **Warehouse Validation Mismatch**: The Console's local bin validation expects the source warehouse to be `PreForming - SPP`, which may conflict with the Ops default `Unit-2 - SPP`.
4. **Field Name Drift (`spp_batch_no` vs `spp_batch_number`)**: Dash/Console use `spp_batch_number`, while some legacy child mappings expect `items.spp_batch_no`, risking silent trace data dropping.

## 5. Recommendations

To fully close the gap between requirements and current architecture, the following actions are recommended for the production overseer:

1. **Keep Deferring Clip Retirement**: Do not update the code to retire clips during CBT. Instead, **update the Console test suite** so the tests accurately reflect this business rule, eliminating the documentation drift.
2. **Align Warehouse Validation**: Investigate the discrepancy between `PreForming - SPP` (Console bin validation) and `Unit-2 - SPP` (Ops). Unify these if they describe the same physical flow.
3. **Schema Update (Later Wave)**: Plan a future database schema migration to add `reference_id` to the Legacy `Cut Bit Transfer` doctype for hard idempotency, replacing the 10-minute window hack.
4. **Audit `spp_batch_no` Field**: Add a Bridge test to verify that the Legacy child table accurately receives the `spp_batch_number` payload, preventing silent drops of batch tracing.
