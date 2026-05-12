# Alignment Report: Sheeting Process

## 1. Executive Summary

This report evaluates the alignment between the target requirements (`01-requirements/sheeting-process`) and the documented architectural reality (`02-specifications/sheeting-process`).

Overall, the Sheeting process architecture is **Highly Aligned** with the requirements. It effectively builds upon the Console-First architecture established in the Mixing processes while correctly introducing specific Sheeting capabilities: managing multiple output items (Clips and Cut-bits) from a single source Compound, handling inline clip mapping to avoid downstream race conditions, and driving legacy `Material Transfer` documents. 

## 2. Functional Requirements Alignment

| Requirement | Description | Status | Implementation Notes |
|---|---|---|---|
| **FR-SHT-004 to 007** | Multiple outputs (Clips & Cut-bits) | ✅ Aligned | Handled correctly via Dash generating an output array containing both normal clips and cut-bits with `is_cut_bit_item = 1`. |
| **FR-SHT-009** | Preserve `Cutbit_` naming | ✅ Aligned | Enforced in Dash and used by the Bridge's `populate_sheeting_fields` to automatically detect and flag recycling output. |
| **FR-SHT-010 to 011** | Soft mass-balance visibility | ⚠️ Misaligned | A 5% tolerance check exists purely on the Dash side. The backend does not enforce this tolerance, meaning payloads bypassing the Dash check will be accepted. |
| **FR-SHT-013** | Inline clip mappings | ✅ Aligned | Critical alignment: `_write_clip_mappings_for_sheeting` executes inline during local `_safe_local_create` BEFORE remote sync, closing the BCR-1 downstream scan race. |
| **FR-SHT-014 to 016** | Legacy Material Transfer | ✅ Aligned | The Bridge successfully drives the creation of a Legacy `Material Transfer` document populated with `batches` and `sheeting_clip` child rows. |
| **FR-SHT-017** | Synthesize missing `mix_barcode` | ✅ Aligned | Handled cleanly in `sync_api.py`. Missing rows are synthesized via the documented format `{item_code}_{original_batch}` to ensure downstream fallback logic works. |
| **FR-SHT-019** | Per-target status and retry | ✅ Aligned | The 5-step `apply_bridge_result` atomic pattern is mirrored from Mixing, with two extra prep steps to capture Legacy + Ops unique batch numbers. |

## 3. Business Rules Verification

The architectural specifications rigorously honor the core business rules:

- **BR-SHT-003 & 004 (Identity Separation):** Clips and cut-bits are correctly distinguished both in Console outputs and on Legacy via the `is_cut_bit_item` flag.
- **BR-SHT-005 (Cutbit Prefix):** The legacy controller searches for the `Cutbit_` prefix in the batch number to correctly calculate the `cutbit_qty` and flag the item.
- **BR-SHT-006 (Inline Mapping):** Successfully adhered to by generating `Console Item Clip Mapping` rows before issuing network calls.

## 4. Gaps, Discrepancies, and Drift

1. **Mass-Balance Check (BR-SHT-009)**: Same as the mixing process, the 5% mass-balance check is purely UI-driven (Dash). Backend APIs don't enforce this check. Stock ledger reconciliation is the only fallback if drift occurs.
2. **Ops Reference Backfill Race**: When the Ops leg completes, it returns `impacted_clips` to backfill the `Console Item Clip Mapping`. If this DB update fails (e.g., due to a lock), there's currently no automatic retry, which could leave a mapping missing its Ops reference.
3. **WAREHOUSE_MAP Hardcoded Fallback**: The Legacy bridge uses a hardcoded WAREHOUSE_MAP fallback. If the shop floor configuration changes and the master data doesn't match, this will silently route items to the wrong legacy warehouses.
4. **Undocumented Recycling Loop**: Cut-bits generated here feed directly back into Final Batch (FB) Mixing. This relationship is physically understood on the shop floor but isn't explicitly documented in the cockpit's context models.

## 5. Recommendations

To maintain robustness and full requirement parity, the following actions are recommended for the production overseer:

1. **Document the Cut-Bit Recycling Loop**: Add a dedicated section in the `03-context/` documentation outlining how cut-bit batches (`Cutbit_C_*`) created during Sheeting are consumed as raw materials in FB Mixing.
2. **Monitor Ops Backfill Failures**: Implement explicit structured logging/monitoring around `_backfill_ops_reference_for_sheeting`. Since it happens in a callback, a failure here should alert developers for a manual retry.
3. **Monitor WAREHOUSE_MAP Fallbacks**: Add alerts whenever the WAREHOUSE_MAP fallback is triggered on the Legacy side, preventing silent misconfigurations from corrupting inventory locations.
4. **Accept Backend Mass-Balance Gap**: Acknowledge that mass-balance is only enforced in the UI. Keep this as a known architectural characteristic to maintain operational flow speed.
