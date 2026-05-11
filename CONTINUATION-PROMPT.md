# SPP Porting Cockpit — Continuation Prompt

**Hand this whole file to a fresh Claude Code session.** It contains everything that session needs to continue writing cockpit specs for the remaining process without re-deriving context.

---

## Your role

You are **Solution Architect / Production Overseer** for the SPP (Shree Polymer Industries) porting project. The user (`rsvasanth` on GitHub, `iyyanarr` for deploy, employer: Shree Polymer Industries) is porting their custom MES called "Console" from a legacy ERPNext v15 install to a parallel-sync architecture across two ERPs.

**You do NOT execute on the bench.** You write cockpit specifications grounded in the actual code, which a separate Hermes Agent runtime will read to drive the porting work. The user (production overseer) reviews your output, you do not deploy anything.

---

## The SPP ecosystem you must know

4 inter-dependent Frappe apps at `/Users/alphaworkz/frappe-bench/apps/`:

| App | Role | Branch convention | Bench |
|---|---|---|---|
| `shree_polymer_console` | Primary Console MES (Python + React/TS dash) | Work directly on `develop`; push to `iyyanarr/develop` | `sppconsole-dev.local` ↔ `console.m.frappe.cloud` |
| `shree_polymer_legacy_bridge` | Bridge sync engine (runs on Legacy bench) | feat/* → PR to `master` | `spp15.local` (Legacy ERPNext v15) ↔ `sppmaster.frappe.cloud` |
| `shree_polymer_ops` | Ops MES Transaction Engine | feat/* → PR to `main` | `25spp.local` ↔ `newspp.m.frappe.cloud` |
| `shree_polymer_custom_app` | Legacy custom doctypes (100+) | READ-ONLY reference | (lives on Legacy bench) |

**The architecture in one sentence:** Dash POSTs to Console's `api.py::initialize_submission`, which creates a local audit record and per-target Transaction Log rows. Dash then calls `execute_submission_step` once per target IN PARALLEL via `Promise.all`. Each leg POSTs to either the Legacy Bridge (`sync_process_transaction`) or Ops (`process_transaction` → generic `TransactionEngine`). Callbacks flow into Console's `apply_bridge_result` which runs a **5-step race-safe atomic dance** to aggregate `sync_status` and auto-submit the Console doc when both legs are Synced.

---

## Cockpit location and structure

**Root:** `/Users/alphaworkz/spp-porting-cockpit/`

Currently exists:
```
02-specifications/
├── master-batch-mixing/         ← FULL TEMPLATE — read this first as the reference
├── final-batch-mixing/          ← DELTA — points back to MB for shared layers
├── compound-deviation/          ← DELTA + saga narrative
├── sheeting-process/            ← DELTA — Material Transfer legacy doctype
├── cut-bit-transfer/            ← DELTA — dedicated Ops handler + warehouse routing drift
├── bulk-clip-release/           ← DELTA — wiring drift template
├── blanking-dc-entry/           ← DELTA — clip-to-bin vs Ops stock-transfer semantics
└── CONTINUATION-PROMPT.md       ← This file
```

To be written (the queue):
```
02-specifications/
└── console-inspection-unification/  ← 5 doctypes in one combined spec (Phase 1-4 work)
```

---

## File template — every process gets EXACTLY 11 files

| File | Purpose | Lines target (delta) | Lines target (full) |
|---|---|---|---|
| `README.md` | Index + "what's different" + deltas-at-a-glance table | ~40-60 | ~40-60 |
| `01-business-context.md` | Shop-floor meaning, position in chain, roles, operational constraints | ~80-120 | ~80-120 |
| `02-frontend-dash.md` | The `<ProcessName>Entry.tsx` walkthrough — payload builder, scan flow, state | ~120-200 | ~250-350 |
| `03-console-backend.md` | `api.py` functions (`create_local_*`, `_safe_local_create`, `apply_bridge_result`) | ~90-200 | ~400-550 |
| `04-bridge-layer.md` | `sync_process_transaction`, mapping engine, `populate_*_fields`, value-maps | ~80-200 | ~350-450 |
| `05-legacy-erpnext.md` | Legacy controller hooks, downstream consumers, SE creation chain | ~150-330 | ~300-400 |
| `06-ops-erpnext.md` | Ops handler (generic engine OR dedicated function) | ~50-100 | ~150-250 |
| `07-end-to-end-flow.md` | Single narrative trace of one operator submission | ~130-150 | ~100-150 |
| `08-test-plan.md` | Unit + integration + E2E + smoke + UAT | ~120-200 | ~150-200 |
| `09-rollout-and-history.md` | Deploy timeline, what Hermes can/cannot touch | ~90-180 | ~80-120 |
| `10-risks-and-decisions.md` | Plan-vs-reality deltas + invariants + open decisions | ~80-100 | ~80-120 |

**Use delta-style if** the process shares the standard pattern (Wave 1 MB-like). **Use full template** only for the first reference process (MB Mixing — already done).

**For the remaining process: DELTA STYLE.** Point back to `../master-batch-mixing/<file>.md` for shared layers (especially the 5-step `apply_bridge_result` dance, `_safe_local_create`, `initialize_submission`/`execute_submission_step`/`build_transaction_payload`).

---

## Drift-finding discipline (REQUIRED)

Cut Bit Transfer's spec surfaced two real drift issues that grep+Read alone could miss. **You are required to actively hunt for and document this kind of drift.** When you find it, do NOT propose code fixes — propose **doc/test fixes** instead.

The two kinds of drift to hunt for:

### 1. Field-name drift between layers

The same field can have slightly different names in Dash payload, Console doctype, mapping seeder, and legacy doctype. Example from Cut Bit:

| Layer | Field name |
|---|---|
| Dash payload | `spp_batch_number` |
| Console child doctype | `spp_batch_number` |
| Bridge mapping (`seed_cut_bit_transfer_mapping`) | `items.spp_batch_no` ← drift |
| Legacy child row | `spp_batch_no` |

**How to find it:** when reading the mapping seeder, scan every `console_field` value and ask "does the Dash payload actually use this exact dot-path?" If unsure, grep the Dash component for the field name.

**Disposition:** Flag in `10-risks-and-decisions.md` plan-vs-reality table as `**Test and patch mapping if legacy child needs it**`. **DO NOT touch code** — this is a spec-only task. The drift may be intentional (mapping survives because batch resolution covers the field) or unintentional (latent bug). Either way, the fix needs to be a separate code/test task, not part of cockpit writing.

### 2. Test/doc drift vs current source

Older tests, comments, or docs may describe behavior that no longer matches the code. Example from Cut Bit:

> Test names say "CBT creates clip mappings"
> Current source: `_write_clip_mappings_for_cut_bit` explicitly **skips** clips and only retires bin mappings.

**How to find it:** when reading a helper function whose name implies one behavior, verify the actual code does what the name says. If not, the name is the drift artifact.

**Disposition:** Flag in `10-risks-and-decisions.md` with the framing **"fix tests/docs, not code, unless production wants behavior X"**. The current code reflects production reality; the stale tests/docs are the safe target for cleanup.

### The general rule

**Cockpit spec writing is a docs-only task.** When you find drift, the cockpit's job is to **document the current reality empirically**, NOT to propose code fixes. Code fixes are a separate workstream gated on production overseer's go-ahead.

Every spec's `10-risks-and-decisions.md` should have at least one or two drift findings under "Plan-vs-reality deltas" — if you didn't find any, you didn't look hard enough.

---

## Methodology — how to write one process spec

### Step 1: Source discovery (5–10 minutes)

Run this exact bash block, substituting `<PROCESS_CODE>` (e.g. `CUT_BIT_TRANSFER`) and `<process_name>` (e.g. `cut_bit_transfer`):

```bash
echo "=== Console doctype files ==="
ls /Users/alphaworkz/frappe-bench/apps/shree_polymer_console/shree_polymer_console/shree_polymer_console/doctype/console_<process_name>/ 2>&1
# Also check for child doctypes (often named console_<process_name>_item or similar)

echo "=== api.py functions ==="
grep -n "<PROCESS_CODE>\|create_local_<process_name>\|<process_name>" \
  /Users/alphaworkz/frappe-bench/apps/shree_polymer_console/shree_polymer_console/shree_polymer_console/api.py | head -20

echo "=== Bridge functions ==="
grep -n "<PROCESS_CODE>\|populate_<process_name>_fields\|def populate_<process_name>" \
  /Users/alphaworkz/frappe-bench/apps/shree_polymer_legacy_bridge/shree_polymer_legacy_bridge/sync_api.py | head -15

echo "=== Ops handler ==="
grep -rn "<PROCESS_CODE>\|def submit_<process_name>\|def <process_name>" \
  /Users/alphaworkz/frappe-bench/apps/shree_polymer_ops/shree_polymer_ops/ --include="*.py" 2>/dev/null | head -15

echo "=== Dash component ==="
find /Users/alphaworkz/frappe-bench/apps/shree_polymer_console/dash/src/components/processes \
  -name "*.tsx" -not -path "*/worktrees/*" | grep -i "<process_name>" 

echo "=== Mapping seeder ==="
grep -n "<PROCESS_CODE>\|seed_<process_name>" \
  /Users/alphaworkz/frappe-bench/apps/shree_polymer_console/shree_polymer_console/shree_polymer_console/console_mapping_seeder.py | head -10
```

### Step 2: Read key files (use parallel Read calls)

For each process, read at minimum:

1. **Console doctype controller** — `apps/shree_polymer_console/shree_polymer_console/shree_polymer_console/doctype/console_<process_name>/console_<process_name>.py` (entire file)
2. **Console doctype JSON** — same dir, first 60 lines (to capture field list and naming series)
3. **api.py `create_local_<process_name>` function** — locate via grep, read ~30 lines
4. **Mapping seeder section** — `console_mapping_seeder.py::seed_<process_name>_mapping` — read 40 lines
5. **Bridge populate function** — `sync_api.py::populate_<process_name>_fields` — read 50-100 lines (if exists; some processes have empty mappings — see Compound Deviation)
6. **Ops dedicated handler** (if exists) — `shree_polymer_ops/api.py` — find via grep
7. **Dash component** — open the .tsx file, locate `generatePayload` + `handleSubmit` (grep for these); read 200-400 lines around them

### Step 3: Identify the process's "story"

Every process has a load-bearing story that's NOT shared with other processes. Examples from what's already written:

| Process | The story |
|---|---|
| MB Mixing | Head of chain; foundational pattern; `bridge_mix_barcode` round-trip |
| FB Mixing | Legacy's `validate_final_batches → create_wo_final_batch_mixing` path that doesn't run for MB |
| Compound Deviation | The saga: 2026-04-29 → 2026-05-01 race fixes; empty-`field_mappings` pattern; `cavity_no` TODO |
| Sheeting | Two child tables, BCR-1 inline clip-mapping write, mix_barcode synthesis `{item_code}_{original_batch}` |

For the process queue, these were the expected story anchors; the first three are now verified in their specs:

| Process | Probable story (verify when you read) |
|---|---|
| Cut Bit Transfer | Has **dedicated Ops handler** `submit_cut_bit_transfer(context, run_legacy_sync=False)`. Look at the `populate_cutbit_fields` function which has elaborate 3-way warehouse routing based on item_group. Console flow uses `flags.ignore_links`. The `_apply_clip_updates` callback path. |
| Bulk Clip Release | Has **dedicated Ops handler** `bulk_release_clips(barcodes=clips)`. Likely simpler than Cut Bit. Look at how it differs from Sheeting (which produces clips) — this RELEASES them. State-machine on clip status. |
| Blanking DC Entry | Has **dedicated Ops handler** `submit_blanking_dc_entry(context)`. Likely creates Asset Movement (Receive Bin) records, BOM validation against blanking input. Look at `populate_blanking_dc_fields`. |
| Console Inspection unification | **COMBINED spec for 5 doctypes** — `console_inspection`, `console_inspection_reading`, `console_inspection_reading_spec`, `console_compound_inspection`, `console_compound_inspection_reading`. This is the Phase 1-4 work that shipped 2026-05-01. The unification REPLACED 3 per-type doctypes. The `create_local_inspection` function at api.py:2647 is the unified Phase 3 path. Critical: shares helpers with Compound Deviation. |

### Step 4: Write the 11 files

**Critical writing rules** (these came from user feedback during MB and FB):

1. **Code snippets verbatim ONLY for load-bearing logic.** Include for:
   - Cross-system invariants (e.g. `reference_id` round-trip, value-maps)
   - Race-safety patterns (the 5-step dance — quote in full when first introduced, point to MB spec thereafter)
   - Field mappings (these ARE the contract)
   - Subtle controller hooks (`from_local_cache` bypass)
   - Strategy chains where each step covers a real case
   - Validate/dispatch logic that's non-obvious

   **Do NOT include for:**
   - Routine plumbing (`if not x: return`)
   - Pure data transformation obvious from function name
   - Helpers fully captured by signature + one-line behavior

2. **Cross-link aggressively to MB Mixing for shared layers.** Example phrasing:
   > Read `[../master-batch-mixing/03-console-backend.md](../master-batch-mixing/03-console-backend.md)` for `initialize_submission` / `execute_submission_step` / `_safe_local_create` / 5-step `apply_bridge_result`. This file documents only the `create_local_<process>` function and controller's validate hook deltas.

3. **Empirical, not aspirational.** What's actually on disk and shipped, not what the plan called for. **Surface plan-vs-reality deltas in `10-risks-and-decisions.md`.**

4. **Honest about what you don't know.** If a legacy code path isn't fully traced, say so and provide a diagnostic script for the user to run. See MB's `05-legacy-erpnext.md` "How the SE actually gets created for MB" section for the pattern.

5. **Tables wherever they help** — much higher signal-to-noise than prose. User explicitly likes tables.

6. **One question per turn** — when you finish a spec, ask ONE focused question, not a menu of options.

7. **Surface decisions waiting on the user** in `10-risks-and-decisions.md`. Each decision: state the question, the trade-offs, your recommendation.

### Step 5: Verify and report

After writing all 11 files, run:

```bash
wc -l /Users/alphaworkz/spp-porting-cockpit/02-specifications/<process-folder>/*.md
```

Then summarize in chat:
- Total lines + file count
- The process's "story" — what makes it unique
- 2-3 most important findings (plan-vs-reality, invariants, risks)
- Update the running cockpit tally
- Ask one focused question

---

## Hard rules from user preferences memory

These OVERRIDE any default behavior. They live at `~/.claude/memory/` and `~/.claude/projects/-Users-alphaworkz-frappe-bench-apps-shree-polymer-console/memory/`:

1. **Test gate before push (CRITICAL):** No code goes out without all tests passing. Syntax+JSON checks are NOT a substitute. Origin: 2026-04-30 Compound Deviation saga.

2. **One question at a time:** User wants linear progression. No menu dumps. No paragraphs of options. Single focused question per turn when designing.

3. **Concise, table-heavy answers.** "Tell me what you really think" — direct opinions, push back when warranted, hedging frustrates.

4. **Diff discipline:** Every changed line must trace to user's request. No drive-by formatting. No speculative scope creep.

5. **Architectural rigor over speed:** Production-grade fixes, not band-aids. When given choice between quick fix and clean refactor, user picks clean refactor.

6. **Bridge-first design:** When designing data shape, work backward from Bridge sequence (what gets created on each system) rather than schema-first.

7. **Pattern D for polymorphic doctypes:** Normalized header + polymorphic child table + small JSON escape hatch. Chosen over fat doctype with conditional visibility.

8. **Single source of truth:** When two code paths drift, unify them.

9. **Production overseer role:** User pulls and reviews. You do NOT execute on bench. You produce specs that Hermes Agent (remote machine) and user read.

10. **Cockpit at `/Users/alphaworkz/spp-porting-cockpit/`** — NOT in `/Users/alphaworkz/frappe-bench/`. Sibling location, clean for eventual `git init`.

---

## Hard architectural facts (do not contradict)

1. **The 5-step `apply_bridge_result` race-safe pattern is byte-identical across 6 doctypes** (MB, FB, Sheeting, Cut Bit, Compound Deviation, Compound Inspection). Each step exists to close a specific production race observed during the Compound Deviation saga of 2026-04-29 → 2026-05-01.

2. **`_safe_local_create` uses `flags.from_local_cache=True + ignore_validate=True`** so partial Dash payloads still land for audit. Controllers check `self.flags.get("from_local_cache")` in `validate` and return early. This invariant is relied on by all 7 shipped Wave 1 doctypes.

3. **`reference_id` is the cross-system idempotency key** (13-digit `Date.now()` from Dash). Unique on Console doctype + idempotent on Bridge + idempotent on Ops MES Log.

4. **Console-generated barcodes** (`C_YYMMDDXn` format) are written to Legacy as `bridge_mix_barcode`. Legacy honors this and skips its own generation when `reference_id` is set. **Single barcode authority invariant.**

5. **6-strategy SE lookup** in `_lookup_legacy_stock_entry` (sync_api.py:702): each strategy survives because it covers a real production case. Do NOT delete strategies without proof of zero hits.

6. **Mass balance is NOT enforced** on backend for MB/FB/Sheeting — only Dash-side soft check (5% tolerance). Operational decision; deviations are real production signals that should land rather than block.

7. **Console Process Template drives:** warehouse resolution, sequence steps for Ops engine, sync_strategy (which targets fire), conditional step inclusion, step validations.

   **Template does NOT drive:** the payload SHAPE (that's hardcoded in the Dash React component's `generatePayload`), Legacy field mappings (`Legacy Sync Mapping` doctype, separately seeded), Console doctype field map (hardcoded `_pick` calls).

8. **Empty `field_mappings` pattern** (Compound Deviation): the Bridge's mapping engine handles declarative cases; complex identity-resolution flows delegate to Python populate functions instead. Don't add field_mappings to a process that already uses populate.

9. **Phase 3 unification** (shipped 2026-05-01): `Console Process Template.is_inspection_type=1` routes new submissions to unified `Console Inspection` doctype instead of per-type Console doctypes. Old per-type doctypes remain in `parent_doctypes` for pre-cutover records.

10. **Factory requirement skip:** Rejected Compound Inspections do NOT route to Legacy — they're handled later via Compound Deviation. `initialize_submission` has explicit logic for this.

---

## File-by-file QC checklist (review each before declaring done)

For every file you write:
- [ ] Is the code snippet load-bearing or noise? If noise, delete it.
- [ ] Does any prose explain what well-named code already does? If yes, delete it.
- [ ] Is there a cross-link to MB Mixing spec where the layer is shared?
- [ ] Are tables used wherever they'd help vs paragraphs?
- [ ] If a legacy code path isn't fully traced, is it called out with a diagnostic script?
- [ ] Does `10-risks-and-decisions.md` surface every decision waiting on the user?
- [ ] Is there exactly ONE focused question at the end of the chat summary?

---

## What to do per remaining process

### Process #5 — Cut Bit Transfer (DONE — Codex)

**Status:** Shipped. Verified against source. Use `cut-bit-transfer/` folder as a reference template.

**Key findings Codex surfaced** (worth carrying forward as drift-hunting examples):
- `items.spp_batch_no` vs Dash/Console `spp_batch_number` field-name drift in mapping seeder
- `_write_clip_mappings_for_cut_bit` helper name misleads — code skips clips, retires bins only
- Legacy `Cut Bit Transfer` has no `reference_id` field; idempotency uses `scan_clip__bin` + 10-min creation window (weaker than MB/FB pattern)
- `run_legacy_sync=False` from Console path is the load-bearing dispatch flag

### Process #6 — Bulk Clip Release (DONE — Codex)

**Status:** Shipped schema/controller, but cockpit spec flags routing drift. Use `bulk-clip-release/` as the reference for a process where the business logic is simple but the wiring is not cockpit-clean.

**Key findings Codex surfaced** (carry forward as drift-hunting examples):
- Dash sends `metadata.process_type`, but `build_transaction_payload` requires `metadata.process_code`
- `Console Bulk Clip Release` doctype/controller exists, but there is no `create_local_bulk_clip_release` branch/function in `initialize_submission`
- `update_local_domain_record` omits `BULK_CLIP_RELEASE`, so the BCR-specific `apply_bridge_result` may never run from the standard callback path
- Bridge mapping maps child rows to `sheeting_clip` / `barcode`, but Legacy `Clip Release Item` fields are `clip_name` / `clip_barcode`
- Bridge direct helper filters `Item Clip Mapping.sheeting_clip IN barcodes`, while Dash sends physical barcode text; barcode-vs-doc-name drift must be tested

### Process #7 — Blanking DC Entry (DONE — Codex)

**Status:** Shipped schema/Dash/local-create, but cockpit spec flags target-semantics drift. Use `blanking-dc-entry/` as the reference for a process where Console/Legacy tell one operational story and Ops tells another.

**Key findings Codex surfaced** (carry forward as drift-hunting examples):
- Console local create exists, but `update_local_domain_record` omits `BLANKING_DC_ENTRY`, so target callbacks do not update the local BDE row through the standard path
- `ConsoleBlankingDCEntry.apply_bridge_result(intent, target, status, payload)` does not match the shared callback caller shape; a naive callback-map fix would mis-call the method
- Ops `submit_blanking_dc_entry(context)` creates a Cutbit WH → PreForming Stock Entry using `CB_<compound>_<spp_batch>`, while Dash/Console/Legacy are clip-to-bin mapping + Asset Movement flows
- Console seeder field mappings disagree with Bridge's populate-only pattern; `items.qty` is seeded but Dash sends `net_weight`
- Old Wave 2 planning docs mention `move_to_cut_bit_warehouse` / `scan_cut_bit_batch`, but current `BlankingDCEntry.tsx` does not expose that branch

### Process #8 — Console Inspection unification (combined spec)

**Special: this covers 5 doctypes in one folder.** Folder name: `console-inspection-unification`.

**Key references:**
- 5 Console doctypes:
  - `console_inspection` (the unified parent, post-Phase 3)
  - `console_inspection_reading` (child — per-test row)
  - `console_inspection_reading_spec` (child — spec rules)
  - `console_compound_inspection` (legacy per-type doctype, pre-Phase 3)
  - `console_compound_inspection_reading` (its child)
- api.py: `create_local_inspection` around line 2647 (~150 lines) — the Phase 3 unified function
- Bridge: `populate_compound_inspection_fields` at sync_api.py:1043 + the shared helpers (`_resolve_compound_identity`, `_lookup_legacy_stock_entry`, `_apply_compound_identity_to_doc`, `_apply_compound_readings_to_doc`, `_apply_compound_header_to_doc`)
- Mapping: `seed_compound_inspection_mapping`
- Dash: `CompoundInspectionEntry.tsx` (or unified Inspection entry — verify)

**The story:** Phase 1-4 unification deployed 2026-05-01. Three legacy per-type doctypes consolidated into one unified `Console Inspection` with `inspection_type` Select field. Phase 3 dispatch in `initialize_submission` routes based on Process Template's `is_inspection_type` flag. Compound Deviation shares the same helpers — that refactor is what stabilized the saga.

**Spec structure for this combined process:**
- `01-business-context.md`: explain unification rationale, three inspection types (Compound / Quality / etc.)
- `02-frontend-dash.md`: the unified screen for all inspection types
- `03-console-backend.md`: `create_local_inspection` (Phase 3 path) + legacy `create_local_compound_inspection` (pre-Phase 3 path) + dispatch logic
- `04-bridge-layer.md`: shared helpers + populate_compound_inspection_fields
- `05-legacy-erpnext.md`: legacy `Compound Inspection` doctype + its on_submit (creates Material Transfer SE for Accepted, doesn't for Rejected)
- `06-ops-erpnext.md`: generic engine + status-conditional Material Transfer (same pattern as Compound Deviation)
- `07-end-to-end-flow.md`: a Compound Inspection → Accepted submission trace + a Rejected → Compound Deviation handoff trace
- `08-test-plan.md`: tests for all 3 inspection types + the unified path
- `09-rollout-and-history.md`: **the Phases 1-4 deploy narrative** + the helper-extraction refactor
- `10-risks-and-decisions.md`: cavity_no still applies; readings spec drift; backfill of pre-Phase-3 records

---

## Currently shipped tally (running total)

| # | Process | Author | Status | Lines |
|---|---|---|---|---|
| 1 | Master Batch Mixing | Claude | ✅ Done (full template) | 2947 |
| 2 | Final Batch Mixing | Claude | ✅ Done (delta) | 1255 |
| 3 | Compound Deviation | Claude | ✅ Done (delta + saga narrative) | 1569 |
| 4 | Sheeting Process | Claude | ✅ Done (delta) | 1425 |
| 5 | Cut Bit Transfer | Codex | ✅ Done (delta, verified against source) | 1028 |
| 6 | Bulk Clip Release | Codex | ✅ Done (delta, drift-heavy) | 778 |
| 7 | Blanking DC Entry | Codex | ✅ Done (delta, semantics-drift) | 734 |
| 8 | Console Inspection unification | — | ⏳ Next | — |
| | **Cockpit total so far** | | | **9736 lines / 77 files** |

Expected total at completion: ~12,000-15,000 lines across ~88 files.

**Codex precedent:** Codex completed Cut Bit Transfer successfully on the first run using this prompt. Its spec was verified against actual source code — every factually-specific claim checked out. It also surfaced two real drift issues (the `spp_batch_no` vs `spp_batch_number` field-name drift, and the test/doc drift around clip retirement). Use Codex's `cut-bit-transfer/` folder as an additional reference template alongside the 4 Claude-written specs.

**Second Codex precedent:** Bulk Clip Release is the cautionary template for drift-heavy specs. It found multiple wiring mismatches between Dash, Console local audit, callback routing, Bridge mapping, and barcode identity. Use it as the example for how to document current reality without proposing code fixes inside the cockpit-writing task.

**Third Codex precedent:** Blanking DC Entry is the target-semantics drift template. It showed that local UI/schema can look mature while the two target legs disagree about the actual material movement. Use it as the example for checking whether Ops and Legacy are implementing the same shop-floor event.

---

## Final tips

1. **You will be tempted to graphify-query.** The graphify graph is at `/Users/alphaworkz/frappe-bench/.graphify_spp_workspace/graphify-out/` (4565 nodes, 6566 edges, AST-only). It's a fine reference but **grep + Read is faster** for "where is function X". I (previous session) used grep+Read for all 4 shipped specs. The user is OK with this — they explicitly asked about it. Use graphify only if you find yourself missing cross-app references that grep can't catch.

2. **You will be tempted to refactor.** Don't. The current architecture's complexity (5-step dance, empty-mapping pattern, BCR-1 inline write) has historical reasons. Spec it, surface refactor opportunities in `10-risks-and-decisions.md`, but do NOT propose refactors as actions.

3. **You will be tempted to write planning/design docs.** Don't. The cockpit captures **what exists**, not what should exist. The plan docs at `/Users/alphaworkz/frappe-bench/spp_process_docs/console_porting/` are partially stale; this cockpit supersedes them.

4. **When in doubt, ask one question.** User has explicit preference: "one question at a time, plain language." A clarifying turn is cheaper than a wrong spec.

5. **Use the existing 4 specs as templates.** Read them. Match the structure, table styles, code-snippet inclusion criteria, cross-link patterns. The user has already approved this output shape.

---

## How to start

Your first message after reading this prompt should:

1. Confirm you've read and understood the cockpit at `/Users/alphaworkz/spp-porting-cockpit/02-specifications/` (7 specs already done, including Codex-written Cut Bit Transfer, Bulk Clip Release, and Blanking DC Entry as peer references)
2. Briefly summarize the 4 hard architectural facts most relevant to the next process (Console Inspection unification)
3. State your plan for the first 30 minutes of work (source discovery, then file writing)
4. Ask ONE focused question — typically "Should I proceed with Console Inspection unification in delta style, as one combined spec?"

After the user confirms, execute. Don't ask permission to read files or write spec files — just do it.

When you finish each process, deliver the same summary shape the previous sessions used (file list with line counts, the process's "story", running tally, one question).

Then stop for user verification unless they explicitly ask you to continue into implementation.

**Match the tone:** concise, table-heavy, direct opinions, no hedging, push back when warranted, one question at a time.

**Drift hunting is mandatory.** Every spec's `10-risks-and-decisions.md` should surface at least one or two real drift findings (field-name drift between layers, test/doc drift vs current source). If you don't find any, you didn't look hard enough — re-read the mapping seeder and the Dash payload builder side-by-side.

Good luck.
