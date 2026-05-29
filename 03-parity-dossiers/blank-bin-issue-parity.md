# Blank Bin Issue Porting Parity Dossier: Linking Bins to Job Cards

**Status:** Draft parity dossier  
**Scope:** Blank Bin Issue process mapping  
**Systems:** Console, Legacy Bridge, legacy ERPNext, Ops ERPNext  
**Runtime impact:** Documentation only. No schema, code, or process behavior changes in this phase.

---

## Purpose and Scope

This dossier outlines how the legacy `Blank Bin Issue` business case is ported into the Console-First architecture.

The Blank Bin Issue step is an intermediate staging process that links a portioned Blanking Bin to a specific Job Card/Lot Number prior to Moulding Production.

---

## Business Parity Summary

In legacy ERPNext, `Blank Bin Issue` was a staging mechanism. It did **not** natively move stock or consume it; it simply recorded which Bins were assigned to which Job Card. Stock consumption was deferred to the Moulding Production Entry (MPE) step.

| Concern | Legacy Behavior | Console-Era Behavior |
| :--- | :--- | :--- |
| **Operator UX** | Desk form for `Blank Bin Issue` | React Dash process screen (`BlankBinIssueEntry`) |
| **Process Rules** | Custom JS and `blank_bin_issue.py` python controller | Console process template plus local payload validation |
| **Legacy Output** | Submitted `Blank Bin Issue` (staging doc only, no Stock Entry) | Same `Blank Bin Issue` created by Legacy Bridge |
| **Ops Output** | Not applicable to legacy-only flow | **Local staging doc only** (No immediate `Stock Entry (Material Issue)`) |
| **Stock Consumption** | Deferred to `Moulding Production Entry` | Deferred to `Moulding Production Entry` |
| **Validation** | Verifies Job Card is "Work In Progress" and Compound matches BOM | Handled locally via Console `validate_blank_issue_barcode` |

---

## Legacy Blank Bin Issue Business Behavior

The legacy controller is located at `apps/shree_polymer_custom_app/shree_polymer_custom_app/shree_polymer_custom_app/doctype/blank_bin_issue/blank_bin_issue.py`.

Key behaviors include:
1. **Barcode Validation (`validate_blank_issue_barcode`):**
   - Validates that the scanned `Lot Number` belongs to an active `Job Card` with `status == "Work In Progress"`.
   - Validates that the scanned `Bin` has an active `Item Bin Mapping` (`is_retired == 0`) and has a non-zero `bin_weight`.
2. **Compound/BOM Validation (`validate_compound`):**
   - Fetches the active `BOM` for the `production_item` requested by the Job Card.
   - Ensures the compound inside the Bin matches the compound required by the BOM.
3. **No Stock Entry Generation:**
   - The document simply appends the staging data to a child table (`items`).
   - `on_submit` performs no stock movement. It only throws an error if no items are added.
   - **Conclusion:** It is a staging/linking document, not an inventory consumption document.

---

## Console Rewrite Behavior

The React Dash component `BlankBinIssueEntry.tsx` provides the operator UI.

1. **Local Scans and Resolution:**
   - The React UI invokes `validate_blank_issue_barcode` in Console's `api.py`.
   - The payload gathers the Job Card details and Bin details.
2. **Standard Payload Dispatch:**
   - On commit, it uses `process_code: 'BLANK_BIN_ISSUE'` to construct the TransactionEngine payload.
   - The engine parallel-syncs this payload to Ops and Legacy Bridge.

---

## Detailed Refactor Design: Ops and Legacy Bridge Alignment

To achieve parity, we will establish the following payload handlers:

### 1. Ops TransactionEngine Alignment
In strict adherence to the Console-First architecture, Ops does **not** create any ERPNext records (no `Stock Entry` and no staging doctype) during this step. 
Because no stock physically moves or is consumed until the Moulding Production Entry (MPE) step, creating a record in Ops would be redundant and semantically incorrect.

**Implementation Strategy:**
- The Console `TransactionEngine` handles the payload with `sync_strategy: "Both (Parallel)"`.
- The `Console Payload Action` configuration for `BLANK_BIN_ISSUE` specifies **zero actions** for `target_system == 'Ops'`.
- Ops receives the payload, logs it successfully in the `MES Transaction Log` for auditability, and completes the transaction without creating any ERPNext documents.
- Stock remains in the `PreForming / Blanking` warehouse until the subsequent MPE transaction natively consumes it.

### 2. Legacy Bridge Routing (`BLANK_BIN_ISSUE`)
The Legacy Bridge needs a new sync leg to handle `BLANK_BIN_ISSUE` payloads.

**Implementation Strategy:**
- Update `shree_polymer_legacy_bridge/sync_api.py` to route `process_type == "BLANK_BIN_ISSUE"`.
- Implement `populate_blank_bin_issue_fields(legacy_doc, payload)` to map the payload context to the legacy `Blank Bin Issue` child table (`items`).
- **Idempotency:** Map `reference_id` to `blanking_dc_no` (or a similar reference field if available) to ensure the staging document isn't duplicated.

---

## Success/Error Handling

### Positive Scenario
- Operator scans Job Card `26E20Z01` and Bin `BLB-00330` in Console.
- Console writes local log and dispatches `BLANK_BIN_ISSUE`.
- Ops creates a `Blank Bin Issue` staging record. No Stock Entry is generated.
- Legacy Bridge creates a `Blank Bin Issue` staging record on the legacy site.
- All sync logs marked `Success`.

### Negative Scenario
- Job Card status is `Completed`. Console blocks scan locally.
- Bin compound does not match BOM. Console blocks scan locally.
