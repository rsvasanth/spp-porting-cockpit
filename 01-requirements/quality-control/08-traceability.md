# 08 — Traceability

## Where things live

| Concern | Document |
|---|---|
| Business motion / purpose | [`01-purpose.md`](01-purpose.md) |
| Actors and permissions | [`02-actors-and-roles.md`](02-actors-and-roles.md) |
| Functional requirements | [`03-functional-requirements.md`](03-functional-requirements.md) |
| Non-functional requirements | [`04-non-functional-requirements.md`](04-non-functional-requirements.md) |
| Business rules / invariants | [`05-business-rules.md`](05-business-rules.md) |
| Acceptance criteria | [`06-acceptance-criteria.md`](06-acceptance-criteria.md) |
| Out-of-scope boundary | [`07-out-of-scope.md`](07-out-of-scope.md) |

## Implementation spec

The "how it actually works" spec is at [`../../02-specifications/spp-quality-control/`](../../02-specifications/spp-quality-control/).

| Section | Spec file |
|---|---|
| Architectural strategy | `01-business-context.md` |
| UI / dash | `02-frontend-dash.md` |
| Console doctype + controller | `03-console-backend.md` |
| Bridge orchestration | `04-bridge-layer.md` |
| Legacy mirror | `05-legacy-erpnext.md` |
| Ops master + Stock Entry | `06-ops-erpnext.md` |
| End-to-end flow | `07-end-to-end-flow.md` |
| Test plan | `08-test-plan.md` |
| Rollout + history | `09-rollout-and-history.md` |
| Risks + decisions | `10-risks-and-decisions.md` |

## Related cockpit documents

- [`../inspection-process/`](../inspection-process/) — Compound Inspection / Deviation requirements (separate motion).
- [`../../02-specifications/console-inspection-unification/`](../../02-specifications/console-inspection-unification/) — Compound family unified doctype. **Scope-narrowed: Compound only.**
- [`../../00-program-charter/`](../../00-program-charter/) — System-of-record decisions; Console is system of record for QC.

## Cross-app references

| App | Where QC touches it |
|---|---|
| `shree_polymer_console` | New `SPP Quality Control` doctype, new `Console SPP QC Parameter` + `Console SPP QC Template` cached read-only doctypes |
| `shree_polymer_ops` | Existing `SPP QC Parameter` + `SPP QC Template` (masters), Stock Entry creation/cancellation via Bridge |
| `shree_polymer_legacy_bridge` | Inspection Entry mirror on `spp15.local` (Wave 4 work — to be re-scoped to target SPP Quality Control instead of Console Inspection) |
| `shree_polymer_custom_app` | Legacy `Inspection Entry` doctype (the mirror target) |

## Test traceability

Each `AC-QC-<n>` from `06-acceptance-criteria.md` MUST correspond to one or more tests listed in the spec's `08-test-plan.md`. The test plan MUST reference the AC by ID.

## Wave/milestone traceability

QC is delivered in 6 milestones (M1–M6) per the spec's `09-rollout-and-history.md`. The cockpit porting plan ([`/Users/alphaworkz/frappe-bench/spp_process_docs/console_porting/`](../../../spp_process_docs/console_porting/)) MUST be updated to reflect that Wave 4 (originally "port Inspection Entry into Console Inspection") is superseded by QC milestones M3 + M5.
