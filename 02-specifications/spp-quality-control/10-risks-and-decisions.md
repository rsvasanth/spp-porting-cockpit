# 10 — Risks and decisions

## Architectural decisions

### ADR-QC-01 — Separate doctype from Console Inspection
**Decision (2026-05-19):** QC lives in `SPP Quality Control`, NOT in `Console Inspection`.
**Reason:** Compound family (Console Inspection) and production-line QC differ in lifecycle (1× per batch vs many× per shift), identity resolution (6-strategy lookup vs single Work Plan lookup), actor split (QI + QM vs QI + Operator + Supervisor), and downstream mirror target (Legacy Compound Inspection vs Legacy Inspection Entry).
**Trade-off accepted:** Two doctypes instead of one polymorphic doctype. Mitigated by sharing the Bridge primitives (`build_transaction_payload`, `initialize_submission`, `execute_submission_step`, `apply_bridge_result`).

### ADR-QC-02 — One doctype for 5 inspection types
**Decision:** Line, Patrol, Lot, Incoming, Final Visual all share `SPP Quality Control`, discriminated by `inspection_type`.
**Reason:** The 5 share 80% of lifecycle (scan flow, template gate, calculation, audit). The 20% differences (UoM, SE submission gate, warehouse routing) are config-driven via `Console Process Template`, not hardcoded.
**Risk:** Type-specific branches could creep into the controller. Mitigation: controller must NOT contain `if inspection_type == "..."` branches for warehouse / UoM / SE behavior; all variability flows through Process Template parameters.

### ADR-QC-03 — Strict template gate (no fallback)
**Decision:** No inspection without an active template. No generic / default tolerances.
**Reason:** Quality data is meaningless without explicit tolerance bands; permissive defaults erode trust in the system.
**Risk:** Inspector blocked on shop floor by missing template = production line stops. Mitigation: on-demand sync button + hourly scheduled sync + clear escalation message naming the supervisor action required.

### ADR-QC-04 — Ops is system of record for masters; Console for transactions
**Decision:** `SPP QC Parameter` + `SPP QC Template` masters live on Ops only. `SPP Quality Control` transactions live on Console only.
**Reason:** Master data needs a single authoritative editor (Template Administrator on Ops). Transaction velocity needs Console-local writes (shop-floor latency).
**Trade-off:** Sync lag is acceptable for master data; not for transactions.

### ADR-QC-05 — Snapshot `one_no_qty_equal_kgs` at validate
**Decision:** Piece weight is snapshotted onto the QC record at `validate()` time; later Mould Spec changes do NOT propagate.
**Reason:** Reversal arithmetic must use the same conversion factor as the original posting; otherwise the reversal won't unwind the original Stock Entry quantity.
**Trade-off:** A change in Mould Spec after submission creates an arithmetic discontinuity between historical and current records. Acceptable; documented.

### ADR-QC-06 — Cancellation is leg-async, cascade-ordered
**Decision:** Each cancel leg (Ops, Legacy, local) is an independent Bridge call. The cascade is strictly ordered: Ops first, Legacy second, local last. Failure at any leg halts the cascade.
**Reason:** Synchronous all-or-nothing cross-site cancellation would hang the UI thread on intermittent shop-floor connectivity. Strict ordering prevents silent half-cancel state.
**Trade-off:** Partial-cancel states are observable in `Console Transaction Log` and require supervisor retry. Acceptable; explicit.

### ADR-QC-07 — Permissions are RBAC by default; `ignore_permissions=True` is documented exception
**Decision:** QC controller MUST NOT use `ignore_permissions=True` without inline written justification.
**Reason:** The legacy api.py has 31 `ignore_permissions=True` calls — at that density, permissions effectively don't exist for that surface. QC starts clean.

## Open risks

### Risk-QC-01 — Draft SE accumulation
Line/Patrol/Lot/Incoming create Draft Stock Entries that depend on the end-of-shift batch closer. If the closer fails or is delayed, Drafts accumulate and create reconciliation overhead.
**Mitigation:** the closer is itself a monitored scheduled job; failures must alert; recovery is `bench execute` of the same job. Operationally observable via Process Template's `draft_close_strategy` parameter.

### Risk-QC-02 — Bridge dispatch arm count
Adding 5 process codes to the existing 14-arm elif chain in `initialize_submission` pushes the chain to 19 arms. This is the same problem the planned Bridge registry refactor is meant to solve.
**Mitigation:** ship QC against the elif now; refactor to registry in a separate PR.

### Risk-QC-03 — Same scanner used by Inspector and Operator
If both badges scan into the same input field (operator forgets to advance focus), inspector identity could be miscaptured.
**Mitigation:** form-level focus management + visible state of "Step 1 of 3 — Inspector" / "Step 2 of 3 — Operator" / "Step 3 of 3 — Lot".

### Risk-QC-04 — Variant Items
Templates link to Items; ERPNext Item variants share a template-Item. Spec assumption: scanned variant resolves to template-Item's template. Needs Ops confirmation.
**Mitigation:** test coverage in `08-test-plan.md` includes a variant-Item resolution test. If business says variants need their own templates, add a per-template `include_variants` flag.

### Risk-QC-05 — Template version drift between scan and submit
If a Template Administrator edits a template between the QI's lot scan and submit, the QC could be submitted against a stale template.
**Mitigation:** `template_sync_hash` is stamped on the QC record at validate. The Bridge payload includes it for audit. Future enhancement: re-fetch template at submit and compare hashes — fail submission on mismatch with "template changed; re-confirm" UX.

### Risk-QC-06 — Legacy Inspection Entry field rename
Legacy `Inspection Entry` is on ERPNext v14 in `shree_polymer_custom_app`. A field rename on the Legacy side silently breaks the mirror.
**Mitigation:** Bridge handler raises (not warns) on missing target fields. Schema-coupling test in legacy_bridge CI.

### Risk-QC-07 — Process Template misconfiguration
Admin configures wrong warehouses on a Process Template → stock movements wrong but submission succeeds.
**Mitigation:** Process Template warehouse fields are mandatory; pre-launch checklist in `09-rollout-and-history.md` requires reviewing each of the 5 Process Templates per environment.

## Decisions deferred (not blockers for M1)

- **Calibration tracking** for testing instruments — out of scope (`07-out-of-scope.md`).
- **Mobile offline mode** — out of scope.
- **Auto-Job-Card-cancel on Rejected** — out of scope.
- **Multi-shift batch closer alternatives** (e.g., submit-on-cancel) — implementable but explicit M3+ decision.
