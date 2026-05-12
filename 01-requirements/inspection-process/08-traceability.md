# 08 — Traceability

Maps each functional/non-functional/business requirement to the specification section(s) that implement or enforce it.

## FR ↔ Spec mapping

| Requirement | Implementing spec section(s) | Implementation status |
|---|---|---|
| **FR-INS-001** Single-actor submission | [CD 02-frontend-dash.md](../../02-specifications/compound-deviation/02-frontend-dash.md) | ✅ Implemented |
| **FR-INS-002** Phase 3 unified routing | [CD 03-console-backend.md](../../02-specifications/compound-deviation/03-console-backend.md) §Dispatch | ✅ Implemented |
| **FR-INS-003** Parallel multi-system sync | [CD 04-bridge-layer.md](../../02-specifications/compound-deviation/04-bridge-layer.md), [CD 06-ops-erpnext.md](../../02-specifications/compound-deviation/06-ops-erpnext.md) | ✅ Implemented |
| **FR-INS-004** Audit trail invariant | [CD 03-console-backend.md](../../02-specifications/compound-deviation/03-console-backend.md) §`_safe_local_create` (inherited from MB pattern) | ✅ Implemented |
| **FR-INS-005** Identity round-trip via mix_barcode | [CD 04-bridge-layer.md](../../02-specifications/compound-deviation/04-bridge-layer.md), [CD 05-legacy-erpnext.md](../../02-specifications/compound-deviation/05-legacy-erpnext.md) §6-strategy chain | ✅ Implemented |
| **FR-INS-010** [CI-only] Reading capture against BOM spec | Console Inspection unification spec (TBD) | ⚠️ Spec pending |
| **FR-INS-011** [CI-only] Auto-derived status | Console Inspection unification spec (TBD) | ⚠️ Spec pending |
| **FR-INS-012** [CI-only] Factory-requirement skip on Rejected | [CD 04-bridge-layer.md](../../02-specifications/compound-deviation/04-bridge-layer.md) §Status-conditional target selection | ✅ Implemented |
| **FR-INS-013** [CI-only] Material Transfer SE on Accepted | [CD 06-ops-erpnext.md](../../02-specifications/compound-deviation/06-ops-erpnext.md) §Status-driven Ops behavior | ✅ Implemented |
| **FR-INS-014** [CI-only] Source SE linkage | [CD 05-legacy-erpnext.md](../../02-specifications/compound-deviation/05-legacy-erpnext.md) §`_apply_compound_identity_to_doc` | ✅ Implemented |
| **FR-INS-020** [CD-only] Source CI prerequisite | [CD 02-frontend-dash.md](../../02-specifications/compound-deviation/02-frontend-dash.md) §Flow summary | ✅ Implemented |
| **FR-INS-021** [CD-only] Status-conditional Ops behavior | [CD 06-ops-erpnext.md](../../02-specifications/compound-deviation/06-ops-erpnext.md) | ✅ Implemented |
| **FR-INS-022** [CD-only] Deviation reason capture | [CD 03-console-backend.md](../../02-specifications/compound-deviation/03-console-backend.md) §Validate hook | ✅ Implemented |
| **FR-INS-023** [CD-only] QM signoff capture | [CD 05-legacy-erpnext.md](../../02-specifications/compound-deviation/05-legacy-erpnext.md) §`_apply_deviation_extras` | ✅ Implemented |
| **FR-INS-024** [CD-only] Both legs fire | [CD 04-bridge-layer.md](../../02-specifications/compound-deviation/04-bridge-layer.md) §Status-conditional skip (CD doesn't skip) | ✅ Implemented |
| **FR-INS-030** Reference ID round-trip | [CD 03-console-backend.md](../../02-specifications/compound-deviation/03-console-backend.md) §Reference ID | ✅ Implemented |
| **FR-INS-031** cavity_no fallback | [CD 05-legacy-erpnext.md](../../02-specifications/compound-deviation/05-legacy-erpnext.md) §The `cavity_no` active TODO | ⚠️ Fallback implemented; proper wiring NOT IMPLEMENTED (active TODO) |
| **FR-INS-032** Idempotent submission | [CD 03-console-backend.md](../../02-specifications/compound-deviation/03-console-backend.md) §Reference ID unique, [CD 04-bridge-layer.md](../../02-specifications/compound-deviation/04-bridge-layer.md) §Idempotency | ✅ Implemented |
| **FR-INS-033** Idempotent leg retry | [CD 03-console-backend.md](../../02-specifications/compound-deviation/03-console-backend.md) §RETRY FLOW FIX | ✅ Implemented |
| **FR-INS-034** Concurrent callback safety | [CD 03-console-backend.md](../../02-specifications/compound-deviation/03-console-backend.md) §5-step `apply_bridge_result`, [CD 09-rollout-and-history.md](../../02-specifications/compound-deviation/09-rollout-and-history.md) §The Saga | ✅ Implemented — saga-validated |
| **FR-INS-040** Role-based screen access | [CD 02-frontend-dash.md](../../02-specifications/compound-deviation/02-frontend-dash.md) §Status-driven validation | ✅ Implemented |
| **FR-INS-041** Source-CI fetch on CD entry | [CD 02-frontend-dash.md](../../02-specifications/compound-deviation/02-frontend-dash.md) §Backend calls | ✅ Implemented |
| **FR-INS-042** Live Feedback per-target status | Console Inspection unification spec (TBD) + inherited MB pattern | ✅ Implemented |
| **FR-INS-043** Backdating restrictions | Inherited from MB pattern; Dash component handles via `isSystemManager` / `isAdministrator` checks | ✅ Implemented |
| **FR-INS-050** Per-leg transaction log | Standard Console pattern | ✅ Implemented |
| **FR-INS-051** Error visibility to operator | Standard Console pattern | ✅ Implemented |
| **FR-INS-052** Saga regression test coverage | [CD 08-test-plan.md](../../02-specifications/compound-deviation/08-test-plan.md) §`test_apply_bridge_result_concurrent_callbacks_deviation` | ⚠️ Test recommended but not yet implemented |

## NFR ↔ Spec mapping

| Requirement | Implementing spec section(s) | Implementation status |
|---|---|---|
| **NFR-INS-001** End-to-end latency | [CD 07-end-to-end-flow.md](../../02-specifications/compound-deviation/07-end-to-end-flow.md) | ✅ Empirically measured |
| **NFR-INS-002** Concurrent QI throughput | Inherited from MB 5-step pattern | ✅ Implemented; large-scale not formally tested |
| **NFR-INS-003** Source-CI fetch latency | Console Inspection unification spec (TBD) | ✅ Implemented |
| **NFR-INS-010** Single-leg failure tolerance | [CD 07-end-to-end-flow.md](../../02-specifications/compound-deviation/07-end-to-end-flow.md) | ✅ Implemented |
| **NFR-INS-011** Saga regression protection | [CD 03-console-backend.md](../../02-specifications/compound-deviation/03-console-backend.md) §5-step pattern (byte-identical across doctypes) | ✅ Implemented |
| **NFR-INS-012** cavity_no fallback resilience | [CD 05-legacy-erpnext.md](../../02-specifications/compound-deviation/05-legacy-erpnext.md) §The `cavity_no` active TODO | ✅ Fallback implemented |
| **NFR-INS-013** 6-strategy SE lookup integrity | [CD 04-bridge-layer.md](../../02-specifications/compound-deviation/04-bridge-layer.md) §Downstream Bridge functions | ✅ Implemented; deletion requires zero-hit proof |
| **NFR-INS-020** Cross-system referential integrity | [CD 07-end-to-end-flow.md](../../02-specifications/compound-deviation/07-end-to-end-flow.md) §Final state | ✅ Implemented |
| **NFR-INS-021** Identity consistency | [CD 04-bridge-layer.md](../../02-specifications/compound-deviation/04-bridge-layer.md), [CD 06-ops-erpnext.md](../../02-specifications/compound-deviation/06-ops-erpnext.md) | ✅ Implemented |
| **NFR-INS-022** Stock ledger reconciliation | Operational concern; not directly implemented | ⚠️ Manual reconciliation only |
| **NFR-INS-023** Idempotency under retry | FR-INS-032 + FR-INS-033 | ✅ Implemented |
| **NFR-INS-030** Audit trail completeness | [CD 03-console-backend.md](../../02-specifications/compound-deviation/03-console-backend.md), [CD 04-bridge-layer.md](../../02-specifications/compound-deviation/04-bridge-layer.md), [CD 06-ops-erpnext.md](../../02-specifications/compound-deviation/06-ops-erpnext.md) | ✅ Implemented |
| **NFR-INS-031** Saga incident reconstruction | Cross-log queryable by `reference_id` | ✅ Implemented (manual query; no dashboard) |
| **NFR-INS-032** QM accountability | [CD 05-legacy-erpnext.md](../../02-specifications/compound-deviation/05-legacy-erpnext.md) §`_apply_deviation_extras` | ✅ Implemented |
| **NFR-INS-040** Role enforcement | [CD 02-frontend-dash.md](../../02-specifications/compound-deviation/02-frontend-dash.md), Frappe permissions | ✅ Implemented |
| **NFR-INS-041** Cross-site authentication | Standard Console pattern | ✅ Implemented |
| **NFR-INS-050** Scan-driven workflow | [CD 02-frontend-dash.md](../../02-specifications/compound-deviation/02-frontend-dash.md) §Flow summary | ✅ Implemented |
| **NFR-INS-051** Error UX | [CD 02-frontend-dash.md](../../02-specifications/compound-deviation/02-frontend-dash.md) §Error states (inherited) | ⚠️ Most errors plain English; some leak Frappe internals |
| **NFR-INS-052** Status routing visibility | Dash UX | ⚠️ Partially implemented; status dropdown shows status but downstream consequence not surfaced |
| **NFR-INS-060** Spec-and-test alignment | This cockpit | ✅ Implemented |
| **NFR-INS-061** Saga story preservation | [CD 09-rollout-and-history.md](../../02-specifications/compound-deviation/09-rollout-and-history.md) | ✅ Implemented |
| **NFR-INS-062** Test gate compliance | Cross-project rule | ✅ Implemented |

## BR ↔ Spec mapping

| Rule | Implementing spec section(s) |
|---|---|
| **BR-INS-001** CI + CD share legacy doctype | [CD 04-bridge-layer.md](../../02-specifications/compound-deviation/04-bridge-layer.md) §What the Bridge does |
| **BR-INS-002** Factory-requirement skip on Rejected CIs | [CD 04-bridge-layer.md](../../02-specifications/compound-deviation/04-bridge-layer.md) §Status-conditional target selection |
| **BR-INS-003** Empty-mapping pattern | [CD 04-bridge-layer.md](../../02-specifications/compound-deviation/04-bridge-layer.md) §Empty `field_mappings` pattern |
| **BR-INS-004** Two-block CD payload | [CD 02-frontend-dash.md](../../02-specifications/compound-deviation/02-frontend-dash.md) §Payload shape |
| **BR-INS-005** Status-conditional Ops behavior | [CD 06-ops-erpnext.md](../../02-specifications/compound-deviation/06-ops-erpnext.md) §Status-driven Ops behavior |
| **BR-INS-006** cavity_no fallback | [CD 05-legacy-erpnext.md](../../02-specifications/compound-deviation/05-legacy-erpnext.md) §The `cavity_no` active TODO |
| **BR-INS-007** Race-safe callback aggregation (saga invariant) | [CD 03-console-backend.md](../../02-specifications/compound-deviation/03-console-backend.md) §5-step pattern, [CD 09-rollout-and-history.md](../../02-specifications/compound-deviation/09-rollout-and-history.md) |
| **BR-INS-008** QM role required for CD | [CD 02-frontend-dash.md](../../02-specifications/compound-deviation/02-frontend-dash.md), Frappe permissions |
| **BR-INS-009** Deviation reason minimum 5 chars | [CD 03-console-backend.md](../../02-specifications/compound-deviation/03-console-backend.md) §Controller validate |
| **BR-INS-010** One deviation per source CI | Dash gating only; backend constraint not enforced |
| **BR-INS-011** 6-strategy SE lookup priority | [CD 04-bridge-layer.md](../../02-specifications/compound-deviation/04-bridge-layer.md) §`_lookup_legacy_stock_entry` |
| **BR-INS-012** Shared identity helpers | [CD 05-legacy-erpnext.md](../../02-specifications/compound-deviation/05-legacy-erpnext.md) §Shared helpers |

## Drift findings

| Item | Type | Status |
|---|---|---|
| **FR-INS-031** cavity_no proper wiring | Requirement partially implemented (fallback works; proper wiring TODO) | ❌ Active TODO — recommended fix |
| **FR-INS-052** Saga concurrency test for all 3 inspection doctypes | Test recommended in spec, not yet implemented | ⚠️ Recommended unit test |
| **NFR-INS-022** Automated stock reconciliation between Legacy and Ops | Requirement exists; manual reconciliation only | ❌ Future epic |
| **NFR-INS-051** Some Frappe internals leak to operator | Partial UX gap | ⚠️ Recommended polish |
| **NFR-INS-052** Status downstream consequence visibility in Dash | Partial UX gap | ⚠️ Recommended polish |
| **BR-INS-010** Backend uniqueness constraint on source_compound_inspection | Dash-only gate; no backend constraint | ⚠️ Recommended low-priority enhancement |
| Console Inspection unification spec | Spec folder not yet written; this motion's CI requirements depend on it | ❌ Spec dependency |

## Change log

| Date | Change | By |
|---|---|---|
| 2026-05-12 | Initial requirements document created (Claude — motion-grouped, supersedes Codex's process-scoped inspection-process/) | Production overseer + Claude |
| | | |
