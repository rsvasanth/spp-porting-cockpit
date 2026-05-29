# Alignment Report: Blanking DC Entry

**Status update:** 2026-05-29. The three "Gaps and Discrepancies" listed in the prior version of this report (callback routing omission, method signature drift, severe semantic drift on Ops) are now all **closed**. This file replaces the prior version which described pre-fix state.

## 1. Executive Summary

The Blanking DC Entry (BDE) process now exhibits **Full Alignment** with the requirements after fixes shipped on `shree_polymer_console` `develop` (commit `d3e45f7`) and the `feat/sync-asset-master` PR on `shree_polymer_ops`. Console owns all business logic; Ops executes a single declarative Asset Movement action via the generic TransactionEngine; Legacy mirror is written by the Bridge populate function.

## 2. Functional Requirements Alignment

| Requirement | Description | Status |
|---|---|---|
| FR-BDE-004 to 006 | Clip Source Validation | ✅ Aligned |
| FR-BDE-005 | Compound-to-item BOM check | ⚠ Left-shifted to Console clip-scan validator; the in-spec Python example in [parity dossier](../03-parity-dossiers/blanking-dc-entry-parity.md) is documentary, the live validator should be tested |
| FR-BDE-007 to 009 | Bin Target Validation (occupied / tare / location) | ✅ Aligned; Asset master sync now provides bin_weight + location locally |
| FR-BDE-010, 011 | Net Weight Calculation | ✅ Aligned (`net_weight = gross_weight − bin_weight` in controller validate) |
| FR-BDE-015, 016 | Mapping Lifecycle | ✅ Aligned; partial clip retire via `_consume_clips_for_blanking_dc` |
| FR-BDE-017, 018 | Legacy execution | ✅ Aligned; Bridge `populate_blanking_dc_fields` writes BDE + Item Bin Mapping + Asset Movement on legacy |
| FR-BDE-019 | Parallel Target Sync | ✅ Aligned; callback routing fixed, 5-step `apply_bridge_result` complete |

## 3. Closed Gaps

1. **Callback Routing (was Delta #1):** `update_local_domain_record.legacy_doctype_map` now includes `"BLANKING_DC_ENTRY": "Console Blanking DC Entry"` ([`api.py:4646`](../../apps/shree_polymer_console/shree_polymer_console/shree_polymer_console/api.py:4646)). Bridge + Ops callbacks reach the parent record.
2. **Method Signature (was Delta #2):** `Console Blanking DC Entry.apply_bridge_result` was already using the canonical `(self, target, status, remote_name=None, error=None)` signature. Steps 4 (self-heal race) and 5 (auto-submit on full Success) were added 2026-05-29 to match the MBM canonical pattern.
3. **Ops Semantic Drift (was Delta #3 / ADR-005):** Resolved. Ops creates `Asset Movement` only, no Stock Entry. `submit_blanking_dc_entry` deleted from `shree_polymer_ops/api.py`. See updated [ADR-005](../ARCHITECTURE-DECISIONS.md#adr-005--blanking-dc-entry-target-semantics-ops--legacy).
4. **Console Asset stubs (was Drift #5):** Lazy-stub insert at `api.py:5798` removed. Ops `get_assets` now syncs full Asset payload (location, bin_weight, asset_category) for `asset_category in ("Blanking Bin", "Mould")`. `Console Asset` schema extended with the matching fields.

## 4. Live Verification Checklist

| Layer | Check | Method |
|---|---|---|
| Console Asset sync | `with_tare`, `with_location`, `with_category` close to `total` | SQL on `tabConsole Asset` after `sync_master_data(force=True)` |
| Callback routing | Console Transaction Log rows transition Pending → Success for both legs | Watch logs during a real submit |
| 5-step dance | Parent record reaches `docstatus=1` after both legs land | Confirm on the Console Blanking DC Entry list view |
| Downstream | A subsequent BBI on the same bin finds the new mapping by `blanking__bin` | Scan in Dash → BBI page |

## 5. Remaining Documentary Cleanup

| File | What still mentions stale code |
|---|---|
| [`03-parity-dossiers/blanking-dc-entry-parity.md`](../03-parity-dossiers/blanking-dc-entry-parity.md) | Sections "Detailed Refactor Design" and "Refactored Ops Field Mappings" still describe the to-do, not the as-is. The 2026-05-29 changes make those sections historical. |
| [`02-specifications/blanking-dc-entry/06-ops-erpnext.md`](../02-specifications/blanking-dc-entry/06-ops-erpnext.md) | ✅ Updated 2026-05-29 |
| [`02-specifications/blanking-dc-entry/03-console-backend.md`](../02-specifications/blanking-dc-entry/03-console-backend.md) | Notes "callback routing currently incomplete" — outdated; now wired |
| [`02-specifications/blanking-dc-entry/10-risks-and-decisions.md`](../02-specifications/blanking-dc-entry/10-risks-and-decisions.md) | Plan-vs-reality deltas 1, 2, 3 now closed |

These are followups for the next cockpit refresh pass — no code work implied.
