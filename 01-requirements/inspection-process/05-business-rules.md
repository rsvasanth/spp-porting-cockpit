# 05 — Business rules

These are the constraints, invariants, and "why" decisions that drive the specifications. Each rule explains the **business reasoning** behind an implementation choice.

## BR-INS-001 — CI and CD produce the same legacy doctype

**Rule:** Both Compound Inspection and Compound Deviation submissions create rows in legacy `Compound Inspection`. Status field discriminates: Accepted/Rejected from QI; Accepted/Rejected/Rework from QM with `quality_approver_*` fields populated.

**Why:** Legacy's design treats "the QA decision about this compound batch" as one event with optional QM override. Maintaining two legacy doctypes would have required additional reporting changes and confusing user training. Reusing one doctype with discriminating status keeps legacy reports working and operator mental model simple.

**Implication:** Any change to legacy `Compound Inspection` schema affects both CI and CD; coordinate together.

## BR-INS-002 — Factory-requirement skip on Rejected CIs

**Rule:** A Rejected CI submission must NOT POST to the Legacy Bridge. Only the Ops leg fires. The Console record stays in `sync_status="Partial"` until a later CD closes the Legacy gap.

**Why:** Operations chose this pattern because:
1. A Rejected CI without QM signoff is **inconclusive** from the Legacy reporting perspective — the compound's fate is unknown
2. Creating a Legacy CI record with `status="Rejected"` would prematurely commit to a write-off in Legacy reports
3. Allowing the QM to make the real decision (via CD) ensures the Legacy record reflects the final disposition, not an intermediate state

**Implementation:** `initialize_submission` in api.py:1009 explicitly skips the Legacy leg when `process_code == "COMPOUND_INSPECTION"` AND `context.status == "Rejected"`.

**Decision authority:** Operations / QA leadership — this is a fixed business rule, not a per-submission choice.

## BR-INS-003 — Empty-mapping pattern for Compound Deviation

**Rule:** `Legacy Sync Mapping` for `COMPOUND_DEVIATION` has an empty `field_mappings` list. All field population is done in Python by `populate_compound_deviation_fields` in the Bridge.

**Why:** Compound Deviation needs:
1. Multi-step identity resolution (`_resolve_compound_identity` → `_lookup_legacy_stock_entry` → 6-strategy chain) that the declarative mapping engine cannot express
2. Conditional field setting (only set if currently empty — idempotent re-runs)
3. Shared helpers with Compound Inspection — both use the same identity pipeline

The empty-mapping pattern delegates all logic to Python while keeping the mapping doctype as a routing shell. The mapping engine knows "for `COMPOUND_DEVIATION`, create a `Compound Inspection` legacy doc"; everything else happens in `populate_compound_deviation_fields`.

**Origin:** Established during the saga's 2026-04-30 helper-refactor commit (`1df2de8` or similar). The previous implementation had ~200 lines of duplicated SE lookup logic that drifted out of sync with the Console payload shape.

**Implication for Hermes workers:** Adding `field_mappings` rows to `COMPOUND_DEVIATION` would duplicate Python logic and create drift. Don't.

## BR-INS-004 — Two-block CD payload (compound_inspection_data + compound_deviation_data)

**Rule:** A CD payload must include:
1. `compound_inspection_data` — same shape as an Accepted CI payload (identity + readings)
2. `compound_deviation_data` — QM-specific fields (status, approver, reason)

**Why:** The CD payload was historically structured as a single block with deviation-specific fields. During the saga, Console refactored to emit identity in `compound_inspection_data` (matching the CI shape exactly) and deviation specifics in a thin separate block. This let the Bridge run the **same** identity pipeline for both Accepted CIs and Deviations.

**Origin:** Saga's 2026-04-30 Console payload refactor (commit `458eb5c`).

**Cross-implication:** Any change to the CI payload shape must also be reflected in CD's `compound_inspection_data` block. Drift here breaks the shared identity pipeline.

## BR-INS-005 — Status-conditional Ops behavior

**Rule:** The Ops side's Stock Entry creation is conditional on inspection status:

| Status | Ops SE created? | SE Purpose |
|---|---|---|
| `Accepted` (CI or CD) | Yes | Material Transfer (compound → ready warehouse) |
| `Rejected` (CD only — CI Rejected doesn't reach Ops at submit time per BR-INS-002 + factory-requirement skip) | Yes | Material Issue / write-off (compound → scrap warehouse) |
| `Rework` (CD only) | No | Compound stays in inspection-WIP; operator returns it to mixing |

**Why:** Each status has a different inventory consequence. Accepted means the compound is good for production; Rejected means write off the inventory loss; Rework means physical relocation only, no ledger movement.

**Implementation:** Driven by the Ops `Console Process Template` action row's `condition` field (`status == 'Accepted'` etc.). The generic TransactionEngine skips actions whose conditions evaluate to False.

## BR-INS-006 — cavity_no fallback to 1 (active TODO)

**Rule:** When the Console payload does not include `cavity_no`, the Bridge's `_apply_deviation_extras` defaults to `cavity_no = 1` on the legacy Compound Inspection. Every fallback fire emits a structured log entry.

**Why:** Legacy `Compound Inspection.validate()` makes `cavity_no` mandatory. The Console architecture intended to wire this field through (it appears in Process Template + Bridge mapping) but the wiring is incomplete: no field on `Console Inspection` doctype, no Dash input, payload doesn't carry it. Default-to-1 is a pragmatic patch that keeps submissions flowing while the wiring is tracked.

**Risk:** Multi-cavity moulds (rare but non-zero) are incorrectly recorded as single-cavity. Production data quality suffers for those runs.

**Bug ref:** Reference ID `1777721078171` (staging, 2026-05-02).

**Resolution path:** Add `cavity_no` to `Console Inspection` doctype + Dash input + payload include → remove the Bridge fallback. Estimated effort: 1 hour.

**Decision needed:** Whether to prioritise this wiring now or accept the default-to-1 long-term. Recommended: wire properly (high data-quality benefit, low effort).

## BR-INS-007 — Race-safe callback aggregation (the saga invariant)

**Rule:** When Ops and Legacy callbacks land near-simultaneously on Console doctype's `apply_bridge_result`, the final `sync_status` must reflect actual DB state — not stale in-memory state.

**Why (saga history):**
- The Compound Deviation saga of 2026-04-29 → 2026-05-01 demonstrated that two callbacks running concurrently both read `self` (stale), both compute aggregate from their stale view, and the slower callback regresses an earlier `Success` to `Partial`
- The 5-step pattern enforces:
  1. Atomic per-leg `db.set_value`
  2. Re-read both legs from DB
  3. Aggregate from DB state
  4. **Self-heal** — if both legs Synced but `sync_status != Success`, correct it
  5. **Fresh-doc submit** — `frappe.get_doc(name)` to avoid stale in-memory state

**Status:** Implemented byte-identically across all three inspection doctypes (Console Inspection, Console Compound Inspection, Console Compound Deviation) and 4 other Wave 1 doctypes.

**Critical:** Any future change to callback handling MUST preserve this contract. A concurrency test is the canonical regression check.

## BR-INS-008 — QM role required for CD

**Rule:** Submitting a CD requires the Console User to have `Quality Manager` role (or higher: System Manager / Administrator). Quality Inspectors cannot submit CD.

**Why:**
- QM signoff is the audit-critical decision — only QMs are trained to authorise deviation decisions
- Separating CI (QI) from CD (QM) enforces decision rights at the UI layer
- Audit-trail accountability: every CD record has a QM signature

**Implementation:** Enforced at three layers: Frappe doctype permissions, Dash UI button gating, server-side `get_available_employees` filter on operator dropdown.

## BR-INS-009 — Deviation reason minimum 5 characters

**Rule:** `deviation_reason` field on CD must be at least 5 characters when submitted through the Desk UI / strict path. The audit-trail bypass path (`_safe_local_create`) does not enforce this.

**Why:** During the saga, some operators submitted "ok" or "yes" as the reason. The 5-char minimum forces a real explanation. The audit-trail bypass is exempt because a record with even a bad reason is better than a missing record for diagnostics.

**Where enforced:** Controller `validate()` in `console_compound_deviation.py` and `console_inspection.py` (when `inspection_type="Compound Deviation"`).

## BR-INS-010 — One deviation per source CI

**Rule:** Each Rejected CI should have at most one CD overlay (in non-cancelled state). Multiple CDs on the same CI would create ambiguous final disposition.

**Why:** A CD is the authoritative final decision. Multiple CDs would imply the QM changed their mind — which is operationally rare and should require explicit cancellation of the prior CD.

**Implementation status:** Enforced at the Dash layer (CD submit button hidden if existing non-cancelled CD found for the source CI). NOT enforced at the backend with a unique constraint — recommended future addition.

## BR-INS-011 — 6-strategy SE lookup priority

**Rule:** The Bridge's `_lookup_legacy_stock_entry(identity)` tries six resolution strategies in priority order. Each strategy covers a real production case; deletion requires zero-hit proof.

**Why:**
1. `mix_barcode == spp_batch_no` — most common (Console-generated barcode)
2. `spp_batch_number` stripped of `C_` prefix — legacy without prefix
3. Direct `spp_batch_number` match
4. `mix_barcode` vs payload — when they differ
5. Compound format `{item_code}_{spp_batch_no}` — Sheeting synthesis
6. `batch_no` fallback — last-ditch

This chain is the result of years of legacy data variations. The 6 strategies cover every real shape of compound identity in the legacy install.

**New strategies should be appended at the end**, never inserted at higher priority. Removing a strategy requires `Legacy Bridge Log` review showing zero hits via that path for at least 90 days.

## BR-INS-012 — Shared identity helpers with Compound Inspection

**Rule:** `populate_compound_deviation_fields` calls the same helpers as `populate_compound_inspection_fields`:
- `_resolve_compound_identity(data)`
- `_lookup_legacy_stock_entry(identity)`
- `_apply_compound_identity_to_doc(doc, identity, se_lookup)`
- `_apply_compound_header_to_doc(doc, data)`
- `_apply_compound_readings_to_doc(doc, data)`

CD then adds `_apply_deviation_extras(doc, data)` on top.

**Why:** Single source of truth for identity resolution. Pre-saga, CI and CD had separate ~200-line identity pipelines that drifted apart. Consolidation in 2026-04-30 refactor eliminated drift surface.

**Implication:** Changes to identity logic affect BOTH CI and CD. Coordinate tests.
