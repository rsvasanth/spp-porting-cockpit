# 08 — Traceability

This file maps each functional and business requirement to the specification section(s) that implement or enforce it. Use it when:

- Reviewing a spec change to verify which requirements it affects
- Hunting drift between requirements and shipped reality
- Onboarding a new Hermes worker — start from a requirement, walk to the spec

## FR ↔ Spec mapping

| Requirement | Implementing spec section(s) | Implementation status |
|---|---|---|
| **FR-MIX-001** Single-operator submission | [MB 02-frontend-dash.md](../../02-specifications/master-batch-mixing/02-frontend-dash.md), [FB 02-frontend-dash.md](../../02-specifications/final-batch-mixing/02-frontend-dash.md) | ✅ Implemented |
| **FR-MIX-002** Parallel multi-system sync | [MB 03-console-backend.md](../../02-specifications/master-batch-mixing/03-console-backend.md) §`initialize_submission`, [MB 04-bridge-layer.md](../../02-specifications/master-batch-mixing/04-bridge-layer.md) | ✅ Implemented |
| **FR-MIX-003** Partial sync recovery | [MB 03-console-backend.md](../../02-specifications/master-batch-mixing/03-console-backend.md) §`apply_bridge_result`, [MB 02-frontend-dash.md](../../02-specifications/master-batch-mixing/02-frontend-dash.md) §Retry | ✅ Implemented |
| **FR-MIX-004** Audit trail invariant | [MB 03-console-backend.md](../../02-specifications/master-batch-mixing/03-console-backend.md) §`_safe_local_create` | ✅ Implemented via `flags.from_local_cache` |
| **FR-MIX-005** Console-authoritative barcode | [MB 04-bridge-layer.md](../../02-specifications/master-batch-mixing/04-bridge-layer.md) §`bridge_mix_barcode`, [MB 05-legacy-erpnext.md](../../02-specifications/master-batch-mixing/05-legacy-erpnext.md) §Honor pattern | ✅ Implemented |
| **FR-MIX-006** Reference ID round-trip | [MB 03-console-backend.md](../../02-specifications/master-batch-mixing/03-console-backend.md), [MB 04-bridge-layer.md](../../02-specifications/master-batch-mixing/04-bridge-layer.md) §Idempotency | ✅ Implemented |
| **FR-MIX-010** Role-based item filtering | [MB 02-frontend-dash.md](../../02-specifications/master-batch-mixing/02-frontend-dash.md), [FB 02-frontend-dash.md](../../02-specifications/final-batch-mixing/02-frontend-dash.md) §`allowedItemGroups` | ✅ Implemented |
| **FR-MIX-011** Role-based operator filtering | [MB 02-frontend-dash.md](../../02-specifications/master-batch-mixing/02-frontend-dash.md) §`get_available_employees` | ✅ Implemented |
| **FR-MIX-012** Backdating restrictions | [MB 02-frontend-dash.md](../../02-specifications/master-batch-mixing/02-frontend-dash.md) §`handleCompleteMixing` | ✅ Implemented |
| **FR-MIX-013** Real-time barcode validation | [MB 02-frontend-dash.md](../../02-specifications/master-batch-mixing/02-frontend-dash.md) §`validate_rm_barcode` | ✅ Implemented |
| **FR-MIX-014** Live Feedback per-target status | [MB 02-frontend-dash.md](../../02-specifications/master-batch-mixing/02-frontend-dash.md) §`handleSubmit`, [MB 03-console-backend.md](../../02-specifications/master-batch-mixing/03-console-backend.md) §`execute_submission_step` | ✅ Implemented |
| **FR-MIX-015** Printable barcode label | [MB 02-frontend-dash.md](../../02-specifications/master-batch-mixing/02-frontend-dash.md) §`triggerActualPrint` | ✅ Implemented |
| **FR-MIX-020** [MBM] Raw materials only | [MB 01-business-context.md](../../02-specifications/master-batch-mixing/01-business-context.md) | ⚠️ Enforced at Dash UI / template only; backend doesn't strict-check |
| **FR-MIX-021** [FBM] Master Batch consumption | [FB 02-frontend-dash.md](../../02-specifications/final-batch-mixing/02-frontend-dash.md) §MB scan, [FB 04-bridge-layer.md](../../02-specifications/final-batch-mixing/04-bridge-layer.md) §`is_batch_item` | ✅ Implemented |
| **FR-MIX-022** [FBM] MB lot stock availability | [FB 06-ops-erpnext.md](../../02-specifications/final-batch-mixing/06-ops-erpnext.md) | ✅ Enforced at Ops Stock Entry submit time |
| **FR-MIX-023** [FBM] Cut-bit recycling input | [FB 01-business-context.md](../../02-specifications/final-batch-mixing/01-business-context.md), [Sheeting 04-bridge-layer.md](../../02-specifications/sheeting-process/04-bridge-layer.md) §Cutbit prefix | ✅ Implemented |
| **FR-MIX-030** Mandatory fields on strict path | [MB 03-console-backend.md](../../02-specifications/master-batch-mixing/03-console-backend.md) §`validate` | ✅ Implemented |
| **FR-MIX-031** Soft mass-balance signal | [MB 10-risks-and-decisions.md](../../02-specifications/master-batch-mixing/10-risks-and-decisions.md) §Decision #1 | ❌ NOT IMPLEMENTED — recommended deferred decision |
| **FR-MIX-032** Cross-system identity consistency | [MB 07-end-to-end-flow.md](../../02-specifications/master-batch-mixing/07-end-to-end-flow.md) §Final state, [FB 07-end-to-end-flow.md](../../02-specifications/final-batch-mixing/07-end-to-end-flow.md) | ✅ Implemented |
| **FR-MIX-040** Idempotent submission | [MB 03-console-backend.md](../../02-specifications/master-batch-mixing/03-console-backend.md) §`reference_id` unique constraint | ✅ Implemented |
| **FR-MIX-041** Idempotent leg retry | [MB 03-console-backend.md](../../02-specifications/master-batch-mixing/03-console-backend.md) §`execute_submission_step` RETRY FLOW FIX, [MB 04-bridge-layer.md](../../02-specifications/master-batch-mixing/04-bridge-layer.md) §`find_existing_record` | ✅ Implemented |
| **FR-MIX-042** Concurrent callback safety | [MB 03-console-backend.md](../../02-specifications/master-batch-mixing/03-console-backend.md) §5-step `apply_bridge_result` | ✅ Implemented — saga-validated |
| **FR-MIX-050** Per-leg transaction log | [MB 03-console-backend.md](../../02-specifications/master-batch-mixing/03-console-backend.md) §`log_transaction` | ✅ Implemented |
| **FR-MIX-051** Error visibility to operator | [MB 02-frontend-dash.md](../../02-specifications/master-batch-mixing/02-frontend-dash.md) §Error states | ✅ Implemented |
| **FR-MIX-052** Error visibility to overseer | `Console Transaction Log` listview | ✅ Implemented via standard Frappe listview |

## NFR ↔ Spec mapping

| Requirement | Implementing spec section(s) | Implementation status |
|---|---|---|
| **NFR-MIX-001** End-to-end latency | [MB 07-end-to-end-flow.md](../../02-specifications/master-batch-mixing/07-end-to-end-flow.md) §Narrative trace timings | ✅ Empirically measured; ~5–10s under normal load |
| **NFR-MIX-002** Concurrent operator throughput | [MB 03-console-backend.md](../../02-specifications/master-batch-mixing/03-console-backend.md) §5-step dance | ✅ Tested up to 3 concurrent (AC-MIX-007); 10-operator load not formally tested |
| **NFR-MIX-003** Scan-to-validation latency | [MB 02-frontend-dash.md](../../02-specifications/master-batch-mixing/02-frontend-dash.md) §Operator scan flow | ✅ Implemented |
| **NFR-MIX-010** Single-leg failure tolerance | [MB 07-end-to-end-flow.md](../../02-specifications/master-batch-mixing/07-end-to-end-flow.md) §Recovery procedures | ✅ Implemented |
| **NFR-MIX-011** Bridge availability | Operational concern; not directly implemented | ⚠️ No active uptime monitoring |
| **NFR-MIX-012** Stale state recovery | [MB 02-frontend-dash.md](../../02-specifications/master-batch-mixing/02-frontend-dash.md) §Retry, [MB 03-console-backend.md](../../02-specifications/master-batch-mixing/03-console-backend.md) §RETRY FLOW FIX | ✅ Implemented |
| **NFR-MIX-013** Bridge-side rollback | [FB 05-legacy-erpnext.md](../../02-specifications/final-batch-mixing/05-legacy-erpnext.md) §`rollback_wo_se_jc` | ✅ Implemented for FB path |
| **NFR-MIX-020** Cross-system referential integrity | [MB 07-end-to-end-flow.md](../../02-specifications/master-batch-mixing/07-end-to-end-flow.md) §Final state table | ✅ Implemented via the 5-step dance + idempotency |
| **NFR-MIX-021** Stock ledger reconciliation | Manual operational check | ⚠️ Manual reconciliation only; no automated check |
| **NFR-MIX-022** Idempotency under retry | FR-MIX-040 + FR-MIX-041 | ✅ Implemented |
| **NFR-MIX-030** Audit trail completeness | [MB 03-console-backend.md](../../02-specifications/master-batch-mixing/03-console-backend.md) §`payload_snapshot`, [MB 04-bridge-layer.md](../../02-specifications/master-batch-mixing/04-bridge-layer.md) §`Legacy Bridge Log`, [MB 06-ops-erpnext.md](../../02-specifications/master-batch-mixing/06-ops-erpnext.md) §`Shree Polymer MES Log` | ✅ Implemented |
| **NFR-MIX-031** Identity traceability | [MB 05-legacy-erpnext.md](../../02-specifications/master-batch-mixing/05-legacy-erpnext.md) §Downstream consumers, [MB 04-bridge-layer.md](../../02-specifications/master-batch-mixing/04-bridge-layer.md) §6-strategy lookup | ✅ Implemented |
| **NFR-MIX-032** Operator accountability | [MB 02-target.md](../../02-specifications/master-batch-mixing/02-target.md) §`submitted_by` field | ✅ Implemented |
| **NFR-MIX-040** Role enforcement | [MB 02-target.md](../../02-specifications/master-batch-mixing/02-target.md) §Permissions | ✅ Implemented |
| **NFR-MIX-041** Cross-site authentication | [MB 03-console-backend.md](../../02-specifications/master-batch-mixing/03-console-backend.md) §`build_erp_headers_for_user`, `build_legacy_bridge_headers` | ✅ Implemented |
| **NFR-MIX-042** Production-staging isolation | `Console Device Settings` per-site config | ⚠️ Operational discipline; no system-level safeguard |
| **NFR-MIX-050** Single-pass scan workflow | [MB 02-frontend-dash.md](../../02-specifications/master-batch-mixing/02-frontend-dash.md) §Operator scan flow | ✅ Implemented |
| **NFR-MIX-051** Error UX (plain English) | [MB 02-frontend-dash.md](../../02-specifications/master-batch-mixing/02-frontend-dash.md) §Error states | ⚠️ Most errors plain; some still leak Frappe internals |
| **NFR-MIX-052** Network awareness | Not implemented | ❌ NOT IMPLEMENTED — feature request |
| **NFR-MIX-060** Spec-and-test alignment | This cockpit | ✅ Implemented via this folder |
| **NFR-MIX-061** Reversibility of customisations | All spec files | ✅ Implemented |
| **NFR-MIX-062** Test gate compliance | Cross-project rule in `~/.claude/projects/.../feedback_test_gate.md` | ✅ Implemented as operational rule |

## BR ↔ Spec mapping

| Rule | Implementing spec section(s) |
|---|---|
| **BR-MIX-001** Operation-to-material-type derivation | [MB 04-bridge-layer.md](../../02-specifications/master-batch-mixing/04-bridge-layer.md) §`inward_material_map` value-map |
| **BR-MIX-002** Mass balance NOT enforced | [MB 10-risks-and-decisions.md](../../02-specifications/master-batch-mixing/10-risks-and-decisions.md) §Decision #1 |
| **BR-MIX-003** DCR is the legacy target | [MB 01-business-context.md](../../02-specifications/master-batch-mixing/01-business-context.md), [MB 05-legacy-erpnext.md](../../02-specifications/master-batch-mixing/05-legacy-erpnext.md) §Why DCR |
| **BR-MIX-004** Parallel sync, not 2PC | [MB 03-bridge-sequence.md](../../02-specifications/master-batch-mixing/03-bridge-sequence.md) §Eventual consistency |
| **BR-MIX-005** Console as single barcode authority | [MB 04-bridge-layer.md](../../02-specifications/master-batch-mixing/04-bridge-layer.md) §`bridge_mix_barcode` |
| **BR-MIX-006** Reference ID as idempotency key | [MB 03-console-backend.md](../../02-specifications/master-batch-mixing/03-console-backend.md) §Reference ID, [MB 04-bridge-layer.md](../../02-specifications/master-batch-mixing/04-bridge-layer.md) §Idempotency |
| **BR-MIX-007** [FBM] `is_batch_item` distinguishes MB consumption | [FB 04-bridge-layer.md](../../02-specifications/final-batch-mixing/04-bridge-layer.md), [FB 05-legacy-erpnext.md](../../02-specifications/final-batch-mixing/05-legacy-erpnext.md) §`validate_final_batches` branching |
| **BR-MIX-008** Operator must hold Mixing Operator role | [MB 02-target.md](../../02-specifications/master-batch-mixing/02-target.md) §Permissions |
| **BR-MIX-009** Backdating admin-only | [MB 02-frontend-dash.md](../../02-specifications/master-batch-mixing/02-frontend-dash.md) §`handleCompleteMixing` |
| **BR-MIX-010** [FBM] Cut-bit recycling | [Sheeting 05-legacy-erpnext.md](../../02-specifications/sheeting-process/05-legacy-erpnext.md) §Cutbit prefix, [Cut Bit 05-legacy-erpnext.md](../../02-specifications/cut-bit-transfer/05-legacy-erpnext.md) |
| **BR-MIX-011** Audit-trail bypass for partial payloads | [MB 03-console-backend.md](../../02-specifications/master-batch-mixing/03-console-backend.md) §`_safe_local_create` |
| **BR-MIX-012** Auto-submit only on full success | [MB 03-console-backend.md](../../02-specifications/master-batch-mixing/03-console-backend.md) §5-step pattern, Step 5 |
| **BR-MIX-013** Bridge SE lookup 6 strategies | [MB 04-bridge-layer.md](../../02-specifications/master-batch-mixing/04-bridge-layer.md) §`_lookup_legacy_stock_entry` |
| **BR-MIX-014** Race-safe callback aggregation | [MB 03-console-backend.md](../../02-specifications/master-batch-mixing/03-console-backend.md) §5-step pattern; [Compound Deviation 09-rollout-history.md](../../02-specifications/compound-deviation/09-rollout-and-history.md) §The Saga |

## Drift findings

When a spec section is found that does NOT trace to any requirement, OR when a requirement has no spec implementation, log here.

### Current drift findings

| Item | Type | Status |
|---|---|---|
| **FR-MIX-031** Soft mass-balance | Requirement without implementation | Deferred decision per business choice |
| **NFR-MIX-052** Network awareness | Requirement without implementation | Future feature |
| **NFR-MIX-021** Automated stock reconciliation | Requirement without implementation | Future epic |
| **NFR-MIX-011** Bridge uptime monitoring | Requirement without implementation | Operational backlog |
| **NFR-MIX-042** Production-staging isolation safeguards | Requirement without implementation | Operational backlog |

## Change log

| Date | Change | By |
|---|---|---|
| 2026-05-11 | Initial requirements document created | Production overseer + Claude session |
| | | |

When future changes happen, add entries here with date, description, and author.

## How to use this file when reviewing changes

**Before approving a spec change:**
1. Identify which requirements the change affects (search this file for the spec section's reference)
2. For each affected requirement, verify the spec section still satisfies the requirement
3. If a change creates new behaviour not yet in any requirement, EITHER:
   - Add a new requirement entry (preferred for permanent changes)
   - Add a drift finding (acceptable for known-temporary changes)

**Before approving a requirement change:**
1. Identify which spec sections currently implement the requirement
2. If the requirement change invalidates the implementation, flag the affected specs as "needs update"
3. Add a change log entry with date and reason

**Drift hunting heuristic:**
- A spec section with no requirement → "Why does this code exist?" → either add a requirement or flag as a candidate for removal
- A requirement with no spec → "Is this implemented?" → either find the implementation or flag as a feature gap
