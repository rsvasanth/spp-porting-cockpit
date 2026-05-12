# Alignment Report: Blanking DC Entry

## 1. Executive Summary

This report evaluates the alignment between the target requirements (`01-requirements/blanking-dc-entry`) and the documented architectural specifications (`02-specifications/blanking-dc-entry`).

The Blanking DC Entry (BDE) process exhibits **Moderate Alignment** with the requirements. While the core UI interactions, clip consumption, and legacy target submissions perform as expected, significant architectural drifts exist around sync callback routing, method signatures, and diverging business semantics between Ops and Legacy systems.

## 2. Functional Requirements Alignment

| Requirement | Description | Status | Implementation Notes |
|---|---|---|---|
| **FR-BDE-004 to 006** | Clip Source Validation | ✅ Aligned | Scan correctly resolves active `Item Clip Mapping` and validates against sheeting warehouse stock. |
| **FR-BDE-007 to 009** | Bin Target Validation | ✅ Aligned | Scan rejects occupied bins and correctly fetches the physical bin's tare weight. |
| **FR-BDE-010, 011** | Net Weight Calculation | ✅ Aligned | Calculates `net_weight = gross_weight - bin_weight` and enforces limits before submit. |
| **FR-BDE-015, 016** | Mapping Lifecycle | ✅ Aligned | Successfully reduces/retires source clip quantity while creating active bin mappings for downstream scans. |
| **FR-BDE-017, 018** | Legacy execution | ✅ Aligned | Drives native Legacy `Asset Movement` and `Item Bin Mapping` to update physical bin locations. |
| **FR-BDE-019** | Parallel Target Sync | ⚠️ Misaligned | Sync correctly executes to targets, but the **local callback routing is broken** (see Gaps below). |

## 3. Business Rules Verification

- **BR-BDE-001 (Fill, don't issue):** Aligned. Strictly fills bins, acting as the transition point into the Blanking phase.
- **BR-BDE-006 (Weight logic):** Aligned. Gross minus tare enforced accurately.
- **BR-BDE-009 (Asset Movement over Work Order):** Aligned. The older Work Order path is bypassed in favor of accurate Asset Movement tracking.

## 4. Gaps, Discrepancies, and Drift

1. **Callback Routing Omission (Delta #1)**: The central `update_local_domain_record` function completely omits `BLANKING_DC_ENTRY`. As a result, when Bridge or Ops callbacks return Success/Failed, the local Console record's sync status remains stuck in `Pending`.
2. **Method Signature Drift (Delta #2)**: The BDE controller's `apply_bridge_result` defines a signature of `(intent, target, status, payload)`, which deviates from the standard pattern established in Mixing `(target, status, remote, error)`. If routing is fixed naively without fixing the signature, callbacks will crash.
3. **Severe Semantic Drift in Ops (Delta #3)**: Legacy models BDE as a `clip -> bin` mapping shift producing an `Asset Movement`. Ops, however, interprets BDE as creating a `Cutbit -> PreForming Stock Entry`. Allowing Ops to quietly consume `CB_` batches while the operator actually scanned a sheeting clip is a major physical-to-digital mismatch.
4. **Console-Side BOM Validation**: The requirements imply scanning should validate compound-to-item BOM compatibility. Currently, this relies heavily on Legacy validation failing post-submission.

## 5. Recommendations

To repair the process and align it fully with requirements, the following sequential actions are recommended:

1. **Fix Callback Signature**: Refactor the `apply_bridge_result` method in the BDE controller to match the standard 4-argument signature used by Mixing and Sheeting.
2. **Restore Callback Routing**: Add `BLANKING_DC_ENTRY` to `update_local_domain_record` so local Console records correctly update to `Success` upon target completion.
3. **Resolve Ops Semantics**: The production overseer must make an architectural decision on whether Ops should model BDE as a Stock Entry or align it with Legacy's bin mapping model. Do not proceed with refactoring Ops BDE until this is answered.
4. **Shift BOM Validation Left**: Implement Console-side BOM validation at scan time, provided the Console's cached BOM data is trustworthy enough to prevent false rejections on the shop floor.
