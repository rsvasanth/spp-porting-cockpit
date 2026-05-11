# 08 — Traceability

This file maps inspection requirements to current specification coverage.

## FR ↔ Spec mapping

| Requirement | Spec section(s) | Status |
|---|---|---|
| FR-INS-001 Scan compound identity | [Compound Deviation 07](../../02-specifications/compound-deviation/07-end-to-end-flow.md), source `CompoundInspectionEntry.tsx` | Partially specified; CI spec pending |
| FR-INS-002 Capture readings | [Compound Deviation 05](../../02-specifications/compound-deviation/05-legacy-erpnext.md) shared readings helpers | Partially specified; CI spec pending |
| FR-INS-003 Derive status | Source `CompoundInspectionEntry.tsx`; [Compound Deviation 04](../../02-specifications/compound-deviation/04-bridge-layer.md) | Partially specified |
| FR-INS-004 Accepted CI syncs to both | Console Inspection unification spec pending | Gap |
| FR-INS-005 Rejected CI skips Legacy | [Compound Deviation 04](../../02-specifications/compound-deviation/04-bridge-layer.md) factory requirement skip | Implemented |
| FR-INS-006 Rejected CI discoverable | [Compound Deviation 09](../../02-specifications/compound-deviation/09-rollout-and-history.md) 2026-05-09 fix | Implemented |
| FR-INS-010 Source must be rejected CI | [Compound Deviation 03](../../02-specifications/compound-deviation/03-console-backend.md); current `validate_compound_deviation_business_rules` | Implemented |
| FR-INS-011 QM signoff | [Compound Deviation 02](../../02-specifications/compound-deviation/02-frontend-dash.md), [05](../../02-specifications/compound-deviation/05-legacy-erpnext.md) | Implemented |
| FR-INS-012 Reason required | [Compound Deviation 03](../../02-specifications/compound-deviation/03-console-backend.md) | Implemented |
| FR-INS-013 Supported dispositions | [Compound Deviation 01](../../02-specifications/compound-deviation/01-business-context.md) | Implemented |
| FR-INS-014 One active Deviation | Current source validation; [Compound Deviation 10](../../02-specifications/compound-deviation/10-risks-and-decisions.md) still says deferred | Implemented in source; spec stale |
| FR-INS-015 Identity continuity | Current source validation; [Compound Deviation 05](../../02-specifications/compound-deviation/05-legacy-erpnext.md) | Implemented |
| FR-INS-016 Read-only source context | [Compound Deviation 02](../../02-specifications/compound-deviation/02-frontend-dash.md) | Implemented |
| FR-INS-020 Status-driven stock behavior | [Compound Deviation 06](../../02-specifications/compound-deviation/06-ops-erpnext.md), [07](../../02-specifications/compound-deviation/07-end-to-end-flow.md) | Implemented |
| FR-INS-021 Legacy Deviation representation | [Compound Deviation 04](../../02-specifications/compound-deviation/04-bridge-layer.md), [05](../../02-specifications/compound-deviation/05-legacy-erpnext.md) | Implemented |
| FR-INS-022 Ops status conditions | [Compound Deviation 06](../../02-specifications/compound-deviation/06-ops-erpnext.md) | Implemented |
| FR-INS-023 Identity round-trip | [Compound Deviation 05](../../02-specifications/compound-deviation/05-legacy-erpnext.md) | Implemented |
| FR-INS-024 Retry without duplication | [Compound Deviation 03](../../02-specifications/compound-deviation/03-console-backend.md), MB shared spec | Implemented |
| FR-INS-025 Partial visibility | [Compound Deviation 07](../../02-specifications/compound-deviation/07-end-to-end-flow.md) | Implemented |
| FR-INS-030 Full payload audit | [Compound Deviation 03](../../02-specifications/compound-deviation/03-console-backend.md) | Implemented |
| FR-INS-031 Per-leg logs | MB shared spec; [Compound Deviation 07](../../02-specifications/compound-deviation/07-end-to-end-flow.md) | Implemented |
| FR-INS-032 Saga-safe callbacks | [Compound Deviation 09](../../02-specifications/compound-deviation/09-rollout-and-history.md) | Implemented |
| FR-INS-033 Source lookup diagnostics | [Compound Deviation 05](../../02-specifications/compound-deviation/05-legacy-erpnext.md) | Implemented |
| FR-INS-034 Cavity number capture | [Compound Deviation 10](../../02-specifications/compound-deviation/10-risks-and-decisions.md) | Incomplete / fallback |

## NFR ↔ Spec mapping

| Requirement | Spec section(s) | Status |
|---|---|---|
| NFR-INS-001 Scan lookup latency | Source only; CI spec pending | Needs explicit spec |
| NFR-INS-010 Single-leg tolerance | [Compound Deviation 07](../../02-specifications/compound-deviation/07-end-to-end-flow.md) | Implemented |
| NFR-INS-011 Rejected-CI target clarity | [Compound Deviation 04](../../02-specifications/compound-deviation/04-bridge-layer.md) | Implemented |
| NFR-INS-013 Callback safety | [Compound Deviation 09](../../02-specifications/compound-deviation/09-rollout-and-history.md) | Implemented |
| NFR-INS-020 Reading completeness | Current source validation | Implemented; CI spec pending |
| NFR-INS-023 Duplicate disposition | Current source validation | Implemented; spec stale |
| NFR-INS-024 Cavity data quality | [Compound Deviation 10](../../02-specifications/compound-deviation/10-risks-and-decisions.md) | Incomplete |
| NFR-INS-030 QM accountability | [Compound Deviation 02](../../02-specifications/compound-deviation/02-frontend-dash.md) | Implemented |
| NFR-INS-050 Unified extensibility | Current `Console Inspection` source; unification spec pending | Needs spec |
| NFR-INS-052 Test gate | [Compound Deviation 09](../../02-specifications/compound-deviation/09-rollout-and-history.md) | Operational rule |

## BR ↔ Spec mapping

| Rule | Spec section(s) |
|---|---|
| BR-INS-001 Inspection is a gate | [Compound Deviation 01](../../02-specifications/compound-deviation/01-business-context.md) |
| BR-INS-002 Failed readings reject CI | Source `CompoundInspectionEntry.tsx`; CI spec pending |
| BR-INS-003 Rejected CIs skip Legacy | [Compound Deviation 04](../../02-specifications/compound-deviation/04-bridge-layer.md) |
| BR-INS-004 Deviation is formal QM disposition | [Compound Deviation 01](../../02-specifications/compound-deviation/01-business-context.md) |
| BR-INS-005 Statuses | [Compound Deviation 01](../../02-specifications/compound-deviation/01-business-context.md) |
| BR-INS-006 Legacy CI target | [Compound Deviation 04](../../02-specifications/compound-deviation/04-bridge-layer.md) |
| BR-INS-007 Empty mapping | [Compound Deviation 04](../../02-specifications/compound-deviation/04-bridge-layer.md) |
| BR-INS-008 Shared lookup | [Compound Deviation 05](../../02-specifications/compound-deviation/05-legacy-erpnext.md) |
| BR-INS-009 Callback reliability | [Compound Deviation 09](../../02-specifications/compound-deviation/09-rollout-and-history.md) |
| BR-INS-010 Reason minimum | [Compound Deviation 03](../../02-specifications/compound-deviation/03-console-backend.md) |
| BR-INS-011 One active Deviation | Current source; spec risk section stale |
| BR-INS-012 `cavity_no` matters | [Compound Deviation 10](../../02-specifications/compound-deviation/10-risks-and-decisions.md) |
| BR-INS-013 Status-skipped Ops success | [Compound Deviation 06](../../02-specifications/compound-deviation/06-ops-erpnext.md) |
| BR-INS-014 Original readings immutable | [Compound Deviation 02](../../02-specifications/compound-deviation/02-frontend-dash.md) |
| BR-INS-015 Unified inspection target | Current source; unification spec pending |

## Drift findings

| Item | Type | Status |
|---|---|---|
| Console Inspection unification spec missing | Requirement has source evidence but no completed spec folder | Needs `02-specifications/console-inspection-unification/` |
| Duplicate Deviation backend gate | Spec says deferred; current source implements it in unified validation | Spec stale; update when unification spec is written |
| `cavity_no` fallback | Requirement exists but end-to-end capture incomplete | Known data-quality gap |
| Rejected CI target status | Rejected CI intentionally skips Legacy, but operators may read it as Partial/failure | Needs UI wording / UAT emphasis |
| Old per-type doctypes | Source supports old `Console Compound Inspection` and `Console Compound Deviation`; requirements prefer unified model | Migration/backfill decision deferred |

## Reviewer notes

When reviewing the future Console Inspection unification spec, check these items first:

| Check | Why |
|---|---|
| Does the spec document `create_local_inspection`? | Several requirements depend on the unified audit write path, but the current spec set only documents Deviation directly. |
| Does the spec document intent-aware callback aggregation? | Rejected CIs may be Ops-only by design; the aggregate status must not treat the skipped Legacy leg as an accidental failure. |
| Does the spec update the duplicate-Deviation story? | The Compound Deviation spec lists backend uniqueness as deferred, but current source has a backend gate in unified validation. |
| Does the spec cover readings specs? | Requirements depend on reading completeness and status derivation, not only on target sync. |
| Does the spec state what happens to old per-type doctypes? | Requirements accept read support, but prefer unified records for new submissions. |

## Change log

| Date | Change | By |
|---|---|---|
| 2026-05-11 | Initial inspection-process requirements pack created | Codex |
| | | |
