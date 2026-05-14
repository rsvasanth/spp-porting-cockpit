# SPEC-DRIVEN METHODOLOGY

> **Audience:** Hermes workers, Claude/Codex agents, and reviewers tasked with writing or updating specifications in `02-specifications/` for the SPP Porting Cockpit.
>
> **Purpose:** Codify the methodology that produced the four reference specs (Master Batch Mixing, Final Batch Mixing, Compound Inspection, Compound Deviation) so every future spec is written at the same depth and rigor.
>
> **Companion docs:**
> - [`AGENT-SPEC-DRIVEN-GUIDE.md`](AGENT-SPEC-DRIVEN-GUIDE.md) — 1-page overview
> - [`ARCHITECTURE-DECISIONS.md`](ARCHITECTURE-DECISIONS.md) — 5 load-bearing ADRs
> - [`SYSTEM-ARCHITECTURE.md`](SYSTEM-ARCHITECTURE.md) — system-level diagrams
> - [`CONTINUATION-PROMPT.md`](CONTINUATION-PROMPT.md) — spec writing prompt for fresh sessions

---

## 1. Core principle

**The Legacy code is the ground truth. The Specification is the source of truth for the port.**

| Source | Authority |
|---|---|
| Legacy controller `.py` + `.json` | Ground truth — describes what the business actually does |
| Existing Console implementation (where shipped) | Reference for the port pattern |
| Plan docs (`spp_process_docs/console_porting/0*_WAVE*.md`) | Aspirational — useful for scope; NOT authoritative for behaviour |
| Cockpit spec | Source of truth for the port — what the agent team will build against |

**No spec written purely from plan docs.** Plan docs may motivate the port; only the legacy code can ground it.

---

## 2. The reference examples

Four shipped specs demonstrate this methodology at full depth. Read them before writing any new spec:

| Reference spec | What it demonstrates |
|---|---|
| [`02-specifications/master-batch-mixing/`](02-specifications/master-batch-mixing/) | **Full template** — every section at maximum depth. Wave 1 head-of-chain process. |
| [`02-specifications/final-batch-mixing/`](02-specifications/final-batch-mixing/) | **Delta-style** — points back to MB for shared layers; documents only what diverges. |
| [`02-specifications/compound-deviation/`](02-specifications/compound-deviation/) | **Saga narrative** — origin of the 5-step `apply_bridge_result` race-safety pattern. Empty-mapping pattern. |
| [`02-specifications/console-inspection-unification/`](02-specifications/console-inspection-unification/) | **Polymorphic doctype** — single Console doctype with family discriminator; validation dispatch. |

**Do not modify these four reference specs except to correct factual drift against current code.** They are the methodological reference.

---

## 3. The 8 phases

Every new spec — and every revision to an existing spec — follows these phases in order.

### Phase 1 — Legacy Deep-Dive

**Output:** Complete inventory of the legacy implementation.

| Step | What to do | Output artifact |
|---|---|---|
| 1.1 | Locate the legacy doctype Python file at `apps/shree_polymer_custom_app/.../doctype/<process>/<process>.py` | File path + line count |
| 1.2 | Read the controller end-to-end (`validate`, `before_insert`, `on_submit`, `on_cancel`, all helpers) | Function inventory table — name, line number, purpose |
| 1.3 | Read the JSON schema file | Field-list table with types, options, mandatory flags |
| 1.4 | Identify every `frappe.db.*` call (SQL, get_value, set_value, exists, delete) | Each call documented with what it reads/writes |
| 1.5 | Identify every `@frappe.whitelist()` method | List with signatures + purpose |
| 1.6 | Enumerate `SPP Settings` field dependencies (every `frappe.get_single("SPP Settings")` field access) | Field list with what each is used for |
| 1.7 | Map every child doctype + linked doctype dependency | Cross-doctype graph (e.g. Work Planning ↔ Mould Specification ↔ Press Mould Specification ↔ Moulding Serial No ↔ Work Plan Item Target) |
| 1.8 | Document cancellation cascade | Step-by-step deletion sequence with pre-guards |
| 1.9 | Document any custom (non-Frappe-hook) submission methods | E.g. `submit_workplan` whitelisted method that calls `run_method("on_submit_value")` |

**Worked example:** MB Mixing's `05-legacy-erpnext.md` documents:
- The `Delivery Challan Receipt` controller line-by-line
- Every helper called downstream (`populate_compound_inspection_fields`, `_lookup_legacy_stock_entry`, etc.)
- Every `frappe.db.*` call in `_lookup_legacy_stock_entry`'s 6-strategy chain
- Downstream consumers (Compound Inspection's `stock_id` requirement)

**Anti-pattern (Work Planning gap):** Codex's spec listed validation NAMES (`validate_shift_mould`, `validate_bom`) but did NOT capture:
- The cancellation cascade's downstream guards (blocks if `Blank Bin Issue.scan_production_lot` or `Moulding Production Entry.scan_lot_number` matches)
- The `Moulding Serial No` doctype lifecycle (created on submit, deleted on cancel)
- The `Mould Specification` + `Press Mould Specification` lookups that populate Job Card cavity/temperature fields
- The 7+ `SPP Settings` field dependencies

### Phase 2 — Identity & Cross-System Mapping

**Output:** Exact identity algorithms + cross-system propagation rules.

| Step | What to do | Output artifact |
|---|---|---|
| 2.1 | Identify the cross-system identity key | Format spec with example (e.g. `bridge_mix_barcode = "C_26C03X1"`) |
| 2.2 | Decode the identity algorithm BYTE-BY-BYTE | Code excerpt + worked example with concrete date/inputs |
| 2.3 | Decide barcode/Lot # authority (Console-first vs Legacy-first) | Decision recorded as ADR-style entry |
| 2.4 | Trace identity round-trip Console → Bridge → Legacy → Ops | Sequence diagram |
| 2.5 | Document field-name drift across layers | Drift table (Dash payload / Console doctype / Bridge mapping / Legacy field / Ops field) |

**Worked example — MB Mixing:**
- Identity: `mix_barcode` format `C_YYMMDDXn` (decoded: `C_` prefix + 2-digit year + month-letter + 2-digit day + `X` separator + sequence)
- Authority: Console-first (ADR-003); Legacy honors via `bridge_mix_barcode`
- Round-trip: Console `mix_barcode` → Bridge `bridge_mix_barcode` → Legacy DCR `bridge_mix_barcode` → Legacy SE FG row `mix_barcode` → downstream CI's 6-strategy lookup

**Worked example — Work Planning (must be in spec, currently missing):**
- Identity: Lot # / Job Card `batch_code`
- Format: `{YY}{MonthLetter}{DD}{ShiftSeries}{Serial:02d}` — e.g. 2026-05-12, shift series=1, serial=3 → `"26E12103"`
- Algorithm:
  - YY = last 2 digits of year (`getdate(date).year[-2:]`)
  - MonthLetter = `getmonth("MM")` → 01→A, 02→B, …, 12→L
  - DD = day-of-month string
  - ShiftSeries = `doc.shift_series`
  - Serial = `validate_get_serial_no(doc, "Generate")` → finds next unused serial for (posted_date, shift_series) from `Moulding Serial No` rows
- Authority: Console-first (Pattern A per plan doc Wave 3)
- Round-trip: Console Lot # → Legacy `Job Card.batch_code` → downstream `Blank Bin Issue.scan_production_lot` + `Moulding Production Entry.scan_lot_number`

**Anti-pattern:** "Lot # is generated daily" — too vague to implement.
**Correct:** Quote `get_spp_batch_date()` and `getmonth()` from `work_planning.py:248-280`, show the worked example.

### Phase 3 — Bridge Translation

**Output:** Field-by-field mapping from Console payload to each target system.

| Step | What to do | Output artifact |
|---|---|---|
| 3.1 | Map Console payload paths → Legacy doctype fields | `Legacy Sync Mapping` field_mappings table |
| 3.2 | Map Console payload paths → Ops payload shape | Mapping table (often different shape from Legacy) |
| 3.3 | Identify dialect translations (Shift A → "8 Hours - 1") | Translation table |
| 3.4 | Document `populate_*_fields` function (Bridge-side Python enrichment) | Code skeleton |
| 3.5 | Decide empty-mappings vs populated mappings pattern | Decision with rationale (see Compound Deviation reference) |
| 3.6 | Define idempotency key per target | E.g. `dc_no` on Legacy DCR, `Shree Polymer MES Log.reference_id` on Ops |
| 3.7 | Document Bridge cross-step references (if multi-step) | E.g. MPE's 3-step sequence with `{{ work_order_name }}` placeholders |

**Worked example — Mixing:**
- Console `metadata.produced_item` → Legacy `item_to_manufacture`
- Console `config.operation` → Legacy `inward_material_type` via value-map (`"Master Batch Mixing" → "Master Batch"`)
- Console `mix_barcode` → Legacy `bridge_mix_barcode`
- `seed_mixing_process_mapping` has the canonical mapping; FB and MB share it (the same mapping seeded twice for two process_codes)

**Worked example — Compound Deviation:**
- `field_mappings = []` (empty) — all population done in Python via `populate_compound_deviation_fields`
- Bridge knows only `legacy_doctype = "Compound Inspection"` (same as CI)
- All field-setting logic in shared helpers (`_resolve_compound_identity`, `_lookup_legacy_stock_entry`, `_apply_compound_identity_to_doc`, `_apply_compound_header_to_doc`, `_apply_compound_readings_to_doc`)
- Plus deviation-specific `_apply_deviation_extras`

**Anti-pattern:** "Bridge maps the payload to legacy" — descriptive only.
**Correct:** List every `field_mappings` row OR explain why the mapping is empty and what the populate function does.

### Phase 4 — Console Doctype Design

**Output:** Complete Console doctype JSON shape + child tables.

| Step | What to do | Output artifact |
|---|---|---|
| 4.1 | Mirror legacy doctype fields | Field-by-field comparison table (legacy vs Console) |
| 4.2 | Add Console tracking fields | Standard 14-field tracking block: `reference_id`, `sync_status`, `target_system`, `submitted_by`, `ops_sync_status`, `ops_reference`, `ops_error_message`, `legacy_sync_status`, `legacy_reference`, `legacy_error_message`, `error_log_summary`, `payload_snapshot`, `process_code`, `status` |
| 4.3 | Identify child tables + their fields | Per-child-table schema |
| 4.4 | Document naming series convention | `{PREFIX}-.YYYY.-.#####` |
| 4.5 | Document permissions | Role matrix (System Manager, Administrator, process-specific operator role, etc.) |
| 4.6 | Flag denormalised vs Link fields | E.g. MB uses `item_code` Data (not Link to Console Item) — decoupling Console doctype from master data freshness |
| 4.7 | Document `is_submittable=1` + `track_changes=1` defaults | Standard for all Wave 1+ doctypes |

**Worked example:** MB Mixing's `02-target.md` lists all 28 fields (13 process + 14 tracking + 1 status) with type, mandatory flag, and rationale for each Data-vs-Link choice.

### Phase 5 — Console Backend (`api.py`) Function Design

**Output:** Function skeletons for `create_local_*`, `_safe_local_create` usage, and controller methods.

| Step | What to do | Output artifact |
|---|---|---|
| 5.1 | Define `create_local_{process}(payload, reference_id)` with `_pick` paths per field | Function code with full `_pick` fallback paths |
| 5.2 | Define `_*_ITEM_KEYMAP` for child rows | Keymap dict |
| 5.3 | Reference `_safe_local_create` invocation | Standard pattern with `flags.from_local_cache=True` |
| 5.4 | Define controller class with `validate`, `before_insert`, `on_submit`, `apply_bridge_result` | Skeleton |
| 5.5 | Specify `apply_bridge_result` is BYTE-IDENTICAL to MB | Reference to MB §03; do NOT re-document the 5-step pattern in prose |
| 5.6 | Document validation dispatch (for inspection-family) | Process Template `validation_dispatch_method` Python function pointer |
| 5.7 | Document any process-specific extras (e.g. Sheeting's `legacy_spp_batch_no` capture + `impacted_clips` backfill) | Code excerpt of the extras inside step 1 |
| 5.8 | Document module-level `apply_bridge_result` dispatcher routing for this doctype | Add to `parent_doctypes` list in `api.py:1980` |

**Critical invariant:** **The 5-step `apply_bridge_result` pattern is byte-identical across all Wave 1+ doctypes (MB, FB, Sheeting, Cut Bit, CD, Compound Inspection, Console Inspection, Blanking DC).** Any change to one requires the same change to all in the same PR. See ADR-002.

**Anti-pattern:** Re-describing the 5-step pattern in prose for each new spec.
**Correct:** Reference [`02-specifications/master-batch-mixing/03-console-backend.md`](02-specifications/master-batch-mixing/03-console-backend.md) §5-step pattern; state "byte-identical implementation."

### Phase 6 — Dash UX

**Output:** Operator flow + payload builder + Live Feedback handling.

| Step | What to do | Output artifact |
|---|---|---|
| 6.1 | Document operator scan flow step-by-step | Narrative (badge scan → barcode scan → form entry → submit) |
| 6.2 | List backend calls the Dash makes | Table — call name, when, purpose |
| 6.3 | Document `generatePayload()` shape verbatim | Code excerpt with all field paths |
| 6.4 | Document `handleSubmit()` Live Feedback flow | Promise.all per-target + per-row status |
| 6.5 | Document retry behavior | Same `reference_id`; rebuilds `req_params` from `Console Transaction Log.request_payload` |
| 6.6 | Document error/loading/empty states | Per-state behavior |
| 6.7 | Document backdating UX (System Manager / Administrator only) | Clamp logic |
| 6.8 | Identify per-target visibility / transparency banners | E.g. workstation override pre-submit banner for Work Planning |

**Worked example:** MB Mixing's `02-frontend-dash.md` shows the full state model, the verbatim `generatePayload()` function, and the Live Feedback `Promise.all` orchestration.

### Phase 7 — Testing (Per Test Gate Rule)

**Output:** Required tests + recommended additions.

| Test type | Coverage | Reference |
|---|---|---|
| **Unit (shipped 3-test pattern)** | (1) lifecycle, (2) audit-trail bypass, (3) strict validate via Desk path | `test_console_master_batch_mixing.py` |
| **Concurrency test** | The saga regression — `threading.Barrier` test ensuring 5-step pattern converges to `sync_status="Success"`, `docstatus=1` | Mandatory for any change to `apply_bridge_result` |
| **Value-map test** | If Bridge uses value-maps, assert correct resolution | Mixing's `inward_material_type` value-map |
| **Idempotency test** | Re-submit same `reference_id` → cleanly rejected | All processes |
| **Cancellation cascade test** | (For processes with cancel) — pre-guards block; allowed cancel deletes downstream | Work Planning's BBI + MPE guards |
| **Integration scenario** | Per-process file in `06_INTEGRATION_TESTS_TODO.md` parked harness | Cross-system reconciliation |
| **E2E happy path (Playwright)** | Dash → submit → both legs Success → success modal | Per-process |
| **Smoke test** | Post-deploy 30-second sanity script (doctype exists, mapping seeded, template active, recent success record) | Per-process |
| **UAT script** | Plain-language operator UAT with sign-off criteria | Per-process |

**Test gate rule (from `~/.claude/projects/.../feedback_test_gate.md`):** No code goes out without all tests passing. Syntax + JSON checks are NOT a substitute. If the worktree has no bench attached, do NOT push — prepare the test command and wait for user go-ahead.

### Phase 8 — Spec Writing (the 11-file structure)

Every spec folder gets EXACTLY 11 files. Line targets per file are guidance; the methodology requires the SECTIONS, not the line counts.

| File | Required sections | Authority |
|---|---|---|
| `README.md` | Status + naming + legacy/Ops targets + deltas-at-a-glance table + file index | MB README |
| `01-business-context.md` | Shop-floor meaning + position in chain + actors/roles + operational constraints | MB §01 |
| `02-frontend-dash.md` | Operator flow + state model + `generatePayload()` verbatim + `handleSubmit()` verbatim + backend calls + retry behavior + error/empty states | MB §02 |
| `03-console-backend.md` | `create_local_*` with full `_pick` paths + `_safe_local_create` invocation + controller `validate` / `before_insert` / `on_submit` + `apply_bridge_result` reference (byte-identical) + module-level dispatcher routing | MB §03 |
| `04-bridge-layer.md` | `sync_process_transaction` reference + mapping seeder rows OR empty-mapping rationale + `populate_*_fields` function + idempotency key | MB §04 |
| `05-legacy-erpnext.md` | **Function inventory table + every `frappe.db.*` call + cancellation cascade with pre-guards + downstream consumers + cross-doctype dependencies (Mould Spec, Press Mould Spec, etc.) + SPP Settings field list** | MB §05 |
| `06-ops-erpnext.md` | Generic engine path OR dedicated handler with Charter-Principle-2 justification + Ops document creation chain + `run_legacy_sync=False` invariant (where applicable) | MB §06 |
| `07-end-to-end-flow.md` | Sequence narrative T+0:00 → T+success + race resolution + recovery procedures + final state table per system | MB §07 |
| `08-test-plan.md` | Shipped tests + recommended additions + integration scenarios + E2E + smoke + UAT | MB §08 |
| `09-rollout-and-history.md` | Deploy timeline + what Hermes can/cannot touch (3 tiers) + drift vs plan + Reviewer checklist | MB §09 |
| `10-risks-and-decisions.md` | Plan-vs-reality deltas + cross-doctype invariants + operational risks + deferred decisions + questions waiting on production overseer | MB §10 |

---

## 4. Quality gates per phase

Each phase has a checklist. A spec is NOT ready for review until every box is checked.

### Phase 1 checklist — Legacy Deep-Dive
- [ ] Legacy `.py` file path + line count documented
- [ ] Every controller method enumerated with line number
- [ ] Every `frappe.db.*` call inventoried
- [ ] Every `@frappe.whitelist()` method listed with signature
- [ ] Every `SPP Settings` field dependency captured
- [ ] Every cross-doctype lookup documented (child + linked)
- [ ] Cancellation cascade documented (if applicable)
- [ ] Any custom (non-standard) submission methods identified

### Phase 2 checklist — Identity
- [ ] Identity field name + format spec documented
- [ ] Algorithm decoded byte-by-byte with worked example
- [ ] Authority decision recorded (Console-first vs Legacy-first)
- [ ] Round-trip diagram present
- [ ] Field-name drift table present (if drift exists)

### Phase 3 checklist — Bridge
- [ ] Console → Legacy mapping table complete
- [ ] Console → Ops mapping table complete
- [ ] Dialect translations documented (if any)
- [ ] Populate function skeleton documented (if any)
- [ ] Idempotency key documented per target

### Phase 4 checklist — Console Doctype
- [ ] Legacy-mirror field table present
- [ ] 14-field tracking block confirmed present
- [ ] Child tables documented
- [ ] Naming series convention chosen
- [ ] Permissions matrix documented
- [ ] Denormalised vs Link choices justified

### Phase 5 checklist — Console Backend
- [ ] `create_local_*` function code documented with `_pick` paths
- [ ] `_*_ITEM_KEYMAP` documented (if child rows)
- [ ] `_safe_local_create` invocation referenced
- [ ] Controller method skeletons present
- [ ] `apply_bridge_result` REFERENCED to MB (not re-described)
- [ ] Validation dispatch documented (if inspection-family)
- [ ] Module-level dispatcher routing documented

### Phase 6 checklist — Dash UX
- [ ] Operator flow step-by-step
- [ ] Backend calls listed
- [ ] `generatePayload()` shape verbatim
- [ ] `handleSubmit()` flow documented
- [ ] Retry behavior documented
- [ ] Error / loading / empty states documented
- [ ] Backdating UX documented
- [ ] Any pre-submit transparency banners documented (e.g. workstation override)

### Phase 7 checklist — Testing
- [ ] 3-test unit pattern documented
- [ ] Concurrency test added if `apply_bridge_result` touched
- [ ] Value-map test added if Bridge uses value-maps
- [ ] Idempotency test added
- [ ] Cancellation cascade test added (if cancel exists)
- [ ] Integration scenario documented (TBD if parked)
- [ ] E2E happy path documented
- [ ] Smoke test script documented
- [ ] UAT script documented

### Phase 8 checklist — Spec Writing
- [ ] 11 files present
- [ ] Each file has its required sections
- [ ] Cross-links to MB / FB / CD / Console Inspection where appropriate
- [ ] No re-description of 5-step pattern (references MB instead)
- [ ] No re-description of `_safe_local_create` (references MB instead)
- [ ] All ADR-relevant content cross-linked to `ARCHITECTURE-DECISIONS.md`

---

## 5. Anti-patterns to avoid

These are patterns the methodology REJECTS. Code review should block any spec that contains them.

### Anti-pattern 1 — "Plan-doc-style spec"

**Symptom:** Spec describes WHAT FIELDS EXIST and WHAT VALIDATIONS RUN, without describing WHY or HOW.

**Example (rejected):**
> "The system validates `shift_series` is present. The system validates `shift_time` is present. The system validates target qty exists."

**Correct:**
> "Legacy `validate()` enforces (per `work_planning.py:14-41`):
> 1. `shift_series` mandatory — throws "Shift Series is not found..!"
> 2. `shift_time` mandatory — throws "Shift Time is not found..!"
> 3. Target qty per (item × shift_time) exists in `Work Plan Item Target` — queries `WHERE item IN (...) AND shift_type = "{shift_time}" AND target_qty != 0`
> The target qty values are cached into `qty_wt_item` instance variable for use by `create_work_order()` later."

### Anti-pattern 2 — "Vague identity algorithm"

**Symptom:** Identity format described in prose without enough detail to implement.

**Example (rejected):**
> "Lot # is generated from date and shift series."

**Correct:**
> "Lot # algorithm (`get_spp_batch_date` line 248–253):
> ```
> {YY}{MonthLetter}{DD}{ShiftSeries}{Serial:02d}
> ```
> Where:
> - `YY` = last 2 digits of `doc.date.year`
> - `MonthLetter` from `getmonth("MM")`: 01→A, 02→B, …, 12→L
> - `DD` = day-of-month string
> - `ShiftSeries` = `doc.shift_series`
> - `Serial` = `validate_get_serial_no("Generate")` → next unused serial for `(posted_date, shift_series)` from `Moulding Serial No` table
>
> Example: date=2026-05-12, shift_series='1', serial=3 → `"26E12103"`"

### Anti-pattern 3 — "Re-describing the 5-step pattern"

**Symptom:** Spec re-narrates the 5-step `apply_bridge_result` race-safety pattern in prose, risking drift.

**Example (rejected):**
> "The controller's `apply_bridge_result` updates the leg status, reads both legs from the database, computes the aggregate, self-heals if needed, and submits the document if both legs synced."

**Correct:**
> "`apply_bridge_result` implements the canonical 5-step race-safe pattern byte-identical to the reference at [`02-specifications/master-batch-mixing/03-console-backend.md`](02-specifications/master-batch-mixing/03-console-backend.md) §5-step pattern. ADR-002 documents the rationale.
>
> Process-specific extras (if any) execute within step 1 (atomic per-field write), NOT in later steps."

### Anti-pattern 4 — "Skip cancellation"

**Symptom:** Spec ignores `on_cancel` because "cancellation is rare."

**Why it's bad:** Cancellation has downstream guards (e.g. WP blocks cancellation if BBI or MPE exists). Missing this means the port either over-allows cancellation (data corruption) or under-allows it (operational deadlock).

**Correct:** Phase 1 step 1.8 mandates documenting the full cancellation cascade with pre-guards.

### Anti-pattern 5 — "Ignore SPP Settings dependencies"

**Symptom:** Spec lists Console fields but not the `SPP Settings` Singleton fields the legacy controller reads.

**Why it's bad:** Without enumerating SPP Settings deps, the Console port will fail at runtime when those fields aren't configured on the target site.

**Correct:** Phase 1 step 1.6 mandates an SPP Settings field list.

### Anti-pattern 6 — "Cross-doctype lookups hidden"

**Symptom:** Spec mentions Job Card creation but not the `Mould Specification` / `Press Mould Specification` lookups that populate cavity counts and temperatures.

**Why it's bad:** Downstream MPE depends on these JC fields being correct. Missing this in the spec means the port creates Job Cards with NULL fields and MPE rejects.

**Correct:** Phase 1 step 1.7 mandates a cross-doctype dependency graph.

---

## 6. Reference patterns by need

When you reach a specific situation, look at the reference example:

| Situation | Reference |
|---|---|
| First-time spec writing the methodology | MB Mixing — full template |
| Process is similar to MB | FB Mixing — delta-style; cross-link to MB |
| Process has race-condition history | Compound Deviation — saga narrative |
| Process is polymorphic (one Console doctype, multiple types) | Console Inspection unification |
| Process has dedicated Ops handler | Cut Bit Transfer — Charter Principle 2 exception |
| Process has multi-output + inline write race | Sheeting Process — BCR-1 invariant |
| Process has multi-step Bridge sequence with cross-step references | Moulding Production Entry (when shipped) — for now use plan doc |
| Process has Asset Movement on Legacy | Blanking DC Entry (shipped) |

---

## 7. Case study — Work Planning (where the methodology was NOT followed)

Current state: [`02-specifications/work-planning/`](02-specifications/work-planning/) (527 lines, Codex-written 2026-05-12).

The legacy `work_planning.py` is 390 lines. The current spec captures field names and validation names but missed:

| Phase | Gap |
|---|---|
| Phase 1 (Legacy Deep-Dive) | Did not enumerate `Moulding Serial No`, `Mould Specification`, `Press Mould Specification`, `Work Plan Item Target` cross-doctype dependencies. Did not document 7+ SPP Settings field dependencies. Did not document the cancellation cascade's downstream guards (BBI + MPE checks). Did not document the custom `on_submit_value` method invoked via `submit_workplan` whitelisted method (NOT a standard Frappe hook). |
| Phase 2 (Identity) | Lot # algorithm captured as "Date + month code + day + shift series + serial" — high-level only. Did not decode the exact format (`{YY}{MonthLetter}{DD}{ShiftSeries}{Serial:02d}`) or the `getmonth()` letter mapping (01→A, …, 12→L). |
| Phase 3 (Bridge) | Bridge mapping rows not enumerated. `create_planning_with_jobcards` whitelisted method design not provided. |
| Phase 5 (Console Backend) | `create_local_work_planning` skeleton not provided. Multi-BOM operator picker (`get_validate_bom`) flow not captured. |
| Phase 6 (Dash UX) | `generatePayload()` shape not provided verbatim. Workstation override pre-submit transparency banner not documented. |
| Phase 7 (Testing) | Concurrency test not specified. Cancellation cascade test not specified. Lot # collision test not specified. |

**Remediation path:** Rewrite the spec following the 8 phases. Specifically:
1. Re-read `work_planning.py` end-to-end with Phase 1 checklist in hand
2. Decode the Lot # algorithm with a worked example (Phase 2)
3. Enumerate every cross-doctype dependency (Phase 1 step 1.7)
4. Provide `create_local_work_planning` skeleton (Phase 5)
5. Provide `generatePayload()` shape (Phase 6)
6. Add concurrency + cancellation tests to test plan (Phase 7)
7. Rewrite all 11 files at MB Mixing depth (Phase 8)

This case study is the canonical example of "what NOT to ship as a spec."

---

## 8. Process for adopting this methodology

| Step | Owner | Trigger |
|---|---|---|
| 1. New spec needed | Agent (Hermes / Claude / Codex) | New process to port OR existing spec needs depth |
| 2. Phase 1 — Legacy Deep-Dive | Agent | Before writing any spec content |
| 3. Phase 2-7 — Working artefacts | Agent | Internal — these inform Phase 8 |
| 4. Phase 8 — Spec drafting | Agent | 11 files following the structure |
| 5. Quality-gate review | Reviewer | Each phase checklist run |
| 6. Production overseer sign-off | Production overseer | Final approval before merge |
| 7. Alignment report (level 4) | Reviewer or independent agent | Cross-validates `01-requirements/` ↔ `02-specifications/` ↔ actual code |

---

## 9. When this methodology fails — escalation

If an agent applying this methodology hits a situation not covered:

1. **Spec the legacy completely first** — even if you can't proceed to the Console port, the legacy Deep-Dive is always doable
2. **Surface the gap in `10-risks-and-decisions.md`** — name the missing pattern + recommended next step
3. **Ask the production overseer** — one focused question with options
4. **Update this methodology document** — if a new pattern is discovered (like the BCR-1 inline-write race), add it as a reference pattern in §6

The methodology evolves. The reference examples are stable. The cockpit is the contract.

---

## 10. Change log

| Date | Change | Author |
|---|---|---|
| 2026-05-14 | Initial draft following Work Planning case study clarification | Production overseer + Claude |

When future changes happen, add entries here with date, description, and author.
