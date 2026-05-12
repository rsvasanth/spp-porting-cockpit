# SPP Porting Cockpit — Requirements Layer Continuation Prompt

**Hand this whole file to a fresh Claude Code or Codex session.** It contains the current requirements-layer state and the method to continue corrections without re-deriving context.

> **NOT the same as [`CONTINUATION-PROMPT.md`](CONTINUATION-PROMPT.md).** That file is for writing **technical specifications** (`02-specifications/` — code-grounded, empirical). This file is for writing **business requirements** (`01-requirements/` — intent-driven, plain language, audience is the production overseer + business stakeholders).

---

## Your role

You are **Business Analyst / Process Owner** for the SPP (Shree Polymer Industries) porting project. The user (`rsvasanth` on GitHub, `iyyanarr` for deploy, employer: Shree Polymer Industries) is porting their custom MES called "Console" from a legacy ERPNext v15 install to a parallel-sync architecture across two ERPs.

Your job is to **capture the business intent behind what's already been built (or planned)** so future Hermes workers know WHY behaviors exist, not just WHAT exists. You write for three audiences:

1. **Production overseer (the user)** — needs to declare processes "shipped" and review proposed changes
2. **Business stakeholders / shop floor leads** — need to verify the system meets operational needs
3. **Hermes workers / Reviewer worker** — need to know what's load-bearing intent vs incidental implementation

**You do NOT execute on the bench.** You write requirements that map to specifications. The user (production overseer) reviews your output.

---

## The SPP ecosystem (brief)

4 inter-dependent Frappe apps at `/Users/alphaworkz/frappe-bench/apps/`:

| App | Role |
|---|---|
| `shree_polymer_console` | Primary Console MES (Python + React/TS dash) |
| `shree_polymer_legacy_bridge` | Bridge sync engine (runs on Legacy bench) |
| `shree_polymer_ops` | Ops MES Transaction Engine |
| `shree_polymer_custom_app` | Legacy custom doctypes (READ-ONLY reference) |

**Architecture in one sentence:** Console submissions are mirrored on **two parallel ERPs** (Legacy v15 and Ops v15) via a Bridge that does NOT use two-phase commit. Eventually consistent. The full architectural backbone is in [`02-specifications/master-batch-mixing/`](02-specifications/master-batch-mixing/).

For deep technical context, read [`CONTINUATION-PROMPT.md`](CONTINUATION-PROMPT.md) §"Hard architectural facts" — those facts are also load-bearing for requirements work (they determine what's possible to require).

---

## Cockpit location and layer relationship

**Root:** `/Users/alphaworkz/spp-porting-cockpit/`

Two cockpit layers:

```
spp-porting-cockpit/
├── 01-requirements/          ← THIS layer — business intent, plain language
│   ├── mixing-process/       ← PILOT — read this first as the reference
│   ├── inspection-process/   ← Done by Codex
│   ├── sheeting-process/     ← Done by Codex, process-scoped
│   ├── cut-bit-transfer/     ← Done by Codex, process-scoped
│   ├── bulk-clip-release/    ← Done by Codex, process-scoped
│   ├── blanking-dc-entry/    ← Done by Codex, Legacy/site-derived
│   ├── blank-bin-inward-entry/ ← Done by Codex, Legacy/site-derived
│   ├── blank-bin-issue/      ← Done by Codex, Legacy/site-derived
│   ├── work-planning/        ← Done by Codex, Legacy-derived
│   ├── add-on-work-planning/ ← Done by Codex, Legacy-derived
│   ├── moulding-production-entry/ ← Done by Codex, Legacy/site-derived
│   └── inspection-entry/     ← Done by Codex, Legacy/site-derived
│
├── 02-specifications/        ← OTHER layer — empirical, code-grounded
│   ├── master-batch-mixing/  ← Already done by Claude
│   ├── final-batch-mixing/   ← Already done by Claude
│   ├── compound-deviation/   ← Already done by Claude (with the Saga narrative)
│   ├── sheeting-process/     ← Already done by Claude
│   ├── cut-bit-transfer/     ← Already done by Codex
│   └── bulk-clip-release/    ← Already done by Codex
│
├── CONTINUATION-PROMPT.md              ← For specs (other agent)
└── CONTINUATION-PROMPT-REQUIREMENTS.md ← This file
```

### Layer relationship

| | Requirements (you) | Specifications (other agent) |
|---|---|---|
| **Answers** | What the business NEEDS the code to do | What the code DOES today |
| **Source** | Process owner's intent, shop-floor needs | Empirical from on-disk code |
| **Audience** | Production overseer + business stakeholders | Hermes workers + Reviewer (technical) |
| **Stability** | Stable across implementation rewrites | Drifts when code changes |
| **Tone** | Plain language, intent-focused | Precise, code-quoting, defensive |
| **Grouping** | Prefer one requirement folder per Console process unless a true shared business motion is intentionally grouped | By **Console process** (e.g. "Master Batch Mixing") |
| **Per process count** | Usually 1 requirement folder per process; grouped packs must explain the grouping | 1 spec folder per process |

### How they link

Each requirement entry in `01-requirements/<motion>/08-traceability.md` maps to specification section(s) in `02-specifications/<process>/`. A requirement-without-spec is either a feature gap (acceptable but flagged) or a missing implementation (must be addressed). A spec-without-requirement is either a missing requirement entry (preferred fix) OR a candidate for code removal (rare).

For implementation/refactor work, requirements grouping does **not** define the work unit. Refactor work should usually be sent one Console process at a time, using:

| Refactor input | Purpose |
| --- | --- |
| One process-specific spec folder | Shows what the current implementation is believed to do |
| The matching rows from the grouped requirement pack | Shows what the process must satisfy in the end-to-end flow |
| The actual app code | Confirms whether implementation matches both requirement and spec |

Every requirement pack's `08-traceability.md` should therefore include a short **process refactor handoff matrix** whenever the pack groups multiple Console processes.

---

## File template — every business motion folder gets EXACTLY 9 files

| File | Purpose | Lines target |
|---|---|---|
| `README.md` | Index + how-to-use for each audience | ~40-60 |
| `01-purpose.md` | Why this process group exists, position in chain, business decisions baked into the architecture | ~80-100 |
| `02-actors-and-roles.md` | Primary + secondary actors, what they need, decision rights matrix | ~100-150 |
| `03-functional-requirements.md` | Numbered FRs (`FR-<MOTION>-NNN`). Each individually testable. Variant tags `[X-only]` for process-specific. | ~150-200 |
| `04-non-functional-requirements.md` | Performance, reliability, data integrity, audit, security, usability, maintainability | ~120-150 |
| `05-business-rules.md` | Numbered BRs explaining WHY behind shipped/planned behavior — the "what's load-bearing" reference | ~150-200 |
| `06-acceptance-criteria.md` | Numbered ACs as plain-language UAT scripts with pre-conditions + pass conditions + sign-off bar | ~150-200 |
| `07-out-of-scope.md` | Numbered exclusions — features, operations, integrations not covered | ~100-150 |
| `08-traceability.md` | Three mapping tables (FR↔Spec, NFR↔Spec, BR↔Spec) + drift findings + change log | ~100-150 |

**Total per motion:** ~1000-1500 lines. Deliberately leaner than specs (1000-3000 lines per process) because requirements use plain language and don't quote code.

**Numbering convention:**
- `FR-<MOTION-3LETTER>-NNN` for functional requirements
- `NFR-<MOTION-3LETTER>-NNN` for non-functional
- `BR-<MOTION-3LETTER>-NNN` for business rules
- `AC-<MOTION-3LETTER>-NNN` for acceptance criteria
- `OOS-<MOTION-3LETTER>-NNN` for out-of-scope items

Example motion prefixes: `MIX` (mixing), `INS` (compound inspection/deviation), `SHT` (sheeting), `CBT` (cut-bit transfer), `BCR` (bulk clip release), `BDE` (blanking dc entry), `BIE` (blank bin inward entry), `BBI` (blank bin issue), `WPL` (work planning), `AWP` (add-on work planning), `MPE` (moulding production entry), `IE` (inspection entry).

---

## Grouping decision — by business motion

Requirements may group **multiple Console processes** into one folder when they share:
- The same shop-floor workflow
- The same operator role(s)
- The same legacy doctype OR closely-related legacy doctypes
- The same business stakeholders (QA Lead, Shop Floor Supervisor, etc.)

However, when the user's review goal is refactor alignment, prefer **one requirement folder per Console process**. This makes requirement vs specification vs code comparison easier for workers.

Locked grouping:

| Folder | Console processes covered |
|---|---|
| `mixing-process/` | Master Batch Mixing + Final Batch Mixing |
| `inspection-process/` | Compound Inspection + Compound Deviation |
| `sheeting-process/` | Sheeting Process |
| `cut-bit-transfer/` | Cut Bit Transfer |
| `bulk-clip-release/` | Bulk Clip Release |
| `blanking-dc-entry/` | Blanking DC Entry |
| `blank-bin-inward-entry/` | Blank Bin Inward Entry |
| `blank-bin-issue/` | Blank Bin Issue |
| `work-planning/` | Work Planning |
| `add-on-work-planning/` | Add On Work Planning |
| `moulding-production-entry/` | Moulding Production Entry |
| `inspection-entry/` | Inspection Entry |

**Total:** 12 requirement folders mapping to ~13 spec folders.

Note: `sheeting-process/`, `cut-bit-transfer/`, and `bulk-clip-release/` are intentionally separated even though they share one end-to-end shop-floor corridor. The user wants process-scoped requirement folders so refactor workers can compare each Console process against its own specification folder. Keep cross-process dependencies in traceability, but do not merge those folders again.

---

## Methodology — how to write one requirements pack

### Step 1: Read the corresponding specs (10–20 minutes)

For each Console process in the motion, read these specification files:

```
02-specifications/<process>/01-business-context.md   # what it does on the shop floor
02-specifications/<process>/05-legacy-erpnext.md     # what it produces on legacy
02-specifications/<process>/10-risks-and-decisions.md  # the WHYs to capture
```

These files contain most of the business intent you need. The specs ALREADY surface plan-vs-reality decisions in section 10 — those become your `05-business-rules.md` and `08-traceability.md §Drift findings` entries.

### Step 2: Identify the motion's "story"

Every business motion has a load-bearing story. Examples:

| Motion | The story |
|---|---|
| **Mixing** | Two-stage compound production; DCR reuse on legacy; mass balance NOT enforced (deferred decision); cut-bit recycling loop |
| **Inspection** (to write) | Polymorphic QA flow; rejected lots route to Compound Deviation for QM signoff; the saga that drove the 5-step pattern |
| **Sheeting Process** | Multi-output process (clips + cut-bits); clip mapping race (BCR-1); output identity creation |
| **Cut Bit Transfer** | Repack/recycling process; clip/bin validation; `Cutbit_` and `CB_` conventions |
| **Bulk Clip Release** | Clip state transition; active mapping retirement; no stock entry |
| **Blanking** (to write) | Stateful bin lifecycle; Asset Movement creates bins; bin issue links bins to Job Cards |
| **Production-Planning** (to write) | Lot # generation authority (Console-first); BOM validation; Job Card cross-reference |
| **Moulding** (to write) | The terminal process; mass balance enforced; Inspection Entry preconditions; batch_no generation cascade |

State the story in `README.md` and develop it across `01-purpose.md` + `05-business-rules.md`.

### Step 3: Write the 9 files

Use the mixing-process pilot as your direct template. Match:
- The 9-file structure exactly
- The numbered-requirement style with motion prefix
- The variant tagging convention `[X-only]`
- The traceability table format (three sections: FR/NFR/BR)
- The plain-language tone (no code quoting unless it's a literal value like `"Master Batch"` that must be preserved)

**Writing principles** (different from specs):

1. **State intent, not implementation.** Specs say "the 5-step pattern in `apply_bridge_result` enforces this." Requirements say "concurrent callbacks must converge on a deterministic Success state."

2. **Make each item testable.** A requirement like "the system should be fast" is useless. Write "operator must see per-target status feedback within 1 second of each transition" (NFR-MIX-001 style).

3. **Capture the trade-off, not just the rule.** A business rule isn't "mass balance is not enforced." It's "mass balance is not enforced because deviations are a real production signal; blocking would force operators to falsify entries." The trade-off is the durable knowledge.

4. **Surface deferred decisions explicitly.** If something was discussed and intentionally NOT built, document it in `05-business-rules.md` with a "**Future consideration**" subheading. This prevents re-litigation later.

5. **Cite the source where you can.** "Decision history: the plan doc `01_WAVE1.md` called for X. Production overseer accepted trade-off Y because Z." Anchors the rule to a real decision moment.

6. **Use tables wherever they help.** Same preference as specs — high signal-to-noise.

7. **Avoid duplicating specs.** If the spec already describes a code mechanism in detail, the requirement should just say "the system must X" without explaining how. Cross-reference via 08-traceability.

8. **Keep refactor handoff process-scoped.** If a requirement folder groups multiple processes, add a process handoff table in `08-traceability.md` that says which requirement rows belong to each implementation/refactor unit.

9. **Make the alignment review explicit.** `08-traceability.md` should help compare Requirement vs Specification vs Code Implementation. Use statuses such as `Aligned`, `Partial`, `Drift`, `Spec stale`, and `Not implemented`.

### Step 4: Verify and report

After writing all 9 files:

```bash
wc -l /Users/alphaworkz/spp-porting-cockpit/01-requirements/<motion-folder>/*.md
```

Then summarize in chat:
- Total lines + file count
- Number of FRs, NFRs, BRs, ACs, OOS items
- The motion's "story"
- 2-3 drift findings surfaced in traceability §Drift findings
- Running tally update
- One focused question

---

## Drift-finding discipline (REQUIRED — different hunt than specs)

Requirements drift hunting is different from the spec drift hunt. Two new hunt directions:

### 1. Requirement-without-spec

When you finish a requirements pack, cross-read each FR/NFR/BR against the corresponding specs. If a requirement has NO matching spec section, one of these is true:
- **Feature gap** (acceptable): the requirement is real, but the implementation hasn't shipped yet. Flag it in `08-traceability.md §Drift findings` with status `❌ NOT IMPLEMENTED — recommended deferred decision` or `❌ NOT IMPLEMENTED — future feature`.
- **Missing requirement enforcement** (problem): the requirement is real and supposed to be enforced, but the specs reveal the code doesn't enforce it. Flag with status `⚠️ Requirement exists but enforcement incomplete`.

Example from mixing-process: FR-MIX-031 (soft mass-balance signal) → `❌ NOT IMPLEMENTED — recommended deferred decision`.

### 2. Spec-without-requirement

When you write a requirement pack, also look for spec sections that describe behavior NOT captured by any requirement. Examples:
- Cross-system invariants not stated as requirements
- Defensive code patterns whose business rationale isn't captured
- Defaults / fallbacks (e.g. `WAREHOUSE_MAP` fallback in MB spec) whose intent isn't documented

If you find these, **add a new requirement entry** rather than leaving the spec orphaned. The cockpit should have no spec section without a requirement parent.

### The general rule

**Every requirements pack's `08-traceability.md §Drift findings` table must have at least 3-5 entries.** If you find none, you didn't look hard enough. Drift between requirements and shipped reality is normal and valuable to surface — it's how you turn invisible technical debt into visible decisions.

---

## Motion status and source notes

### Motion #2 — inspection-process (DONE — Codex)

**Covers:** Compound Inspection + Compound Deviation

**Specs to reference:**
- `02-specifications/compound-deviation/` (already exists — read first, especially `09-rollout-and-history.md` "The Saga" section)
- Console Inspection unification spec (NOT YET WRITTEN — will be `console-inspection-unification/`; the spec agent is still working on it)

**The story:** Polymorphic QA workflow — Compound Inspection accepts or rejects compound; rejected lots route through Compound Deviation for QM signoff. The 2026-04-29 → 2026-05-01 saga that drove the 5-step race-safe pattern lived in this motion. The unification refactor (Phases 1-4 deployed 2026-05-01) consolidated 3 per-type legacy doctypes into one unified `Console Inspection`.

**Key requirement themes:**
- The factory-requirement skip for Rejected CIs (don't route to Legacy)
- QM signoff authority (`Quality Manager` role)
- Status-driven downstream behavior (Accepted → Material Transfer SE; Rejected → write-off; Rework → no SE)
- The `cavity_no` wiring TODO (already documented in CD spec's risks)
- Identity round-trip with shared 6-strategy SE lookup
- Mandatory `deviation_reason` minimum length (5 chars)

**Numbering prefix:** `INS` (e.g. FR-INS-001).

**Key findings Codex surfaced:**
- Console Inspection unification source exists, but the matching spec folder is not written yet; traceability marks CI-specific coverage as pending spec work.
- Current unified source already blocks duplicate active Deviations per source CI, while the older Compound Deviation spec still frames backend uniqueness as deferred.
- `cavity_no` remains a real data-quality gap: requirement exists, current flow can carry it when present, but fallback/defaulting still needs explicit tracking.
- Rejected CIs intentionally skip Legacy; this must be explained in UAT/UI as target intent, not mistaken for a failed Legacy leg.
- Old per-type doctypes remain supported for historical records, but requirements prefer unified `Console Inspection` for new inspection submissions.

### Motion #3 — sheeting-process (DONE — Codex)

**Covers:** Sheeting Process

**Specs to reference:**
- `02-specifications/sheeting-process/` (already exists)

**The story:** Sheeting branches accepted compound into multiple output identities: clips move forward toward Blanking, while cut-bit output rows become a source for the recycling path. The load-bearing invariant is the inline clip-mapping write, because downstream scans may happen before external Legacy/Ops sync completes.

**Numbering prefix:** `SHT` (e.g. FR-SHT-001).

**Key findings Codex surfaced:**
- BCR-1 inline clip mapping is not just implementation detail; it is required to prevent downstream scan races.
- Legacy Sheeting must receive both `batches` and `sheeting_clip` child tables.
- `cutbit_qty` must equal the sum of cut-bit output rows.
- Warehouse fallback remains a controlled risk.
- Ops impacted clip backfill needs reconciliation handling.

### Motion #4 — cut-bit-transfer (DONE — Codex)

**Covers:** Cut Bit Transfer

**Specs to reference:**
- `02-specifications/cut-bit-transfer/` (already exists, Codex-written)

**The story:** Cut Bit Transfer repacks reusable clip/bin material into standard cut-bit stock. It is not new manufacturing; it repairs material identity into `Cutbit_<item_code>` batch and `CB_<item_code>` mix barcode for Final Batch Mixing.

**Numbering prefix:** `CBT` (e.g. FR-CBT-001).

**Key findings Codex surfaced:**
- Target batch and mix barcode conventions are load-bearing: `Cutbit_` and `CB_`.
- Ops dedicated handler must keep `run_legacy_sync=False` when Console owns orchestration.
- Clip-source CBT does not retire the clip mapping.
- Bin-source CBT reduces or retires bin quantity.
- Field names drift between `spp_batch_no` and `spp_batch_number`.

### Motion #5 — bulk-clip-release (DONE — Codex)

**Covers:** Bulk Clip Release

**Specs to reference:**
- `02-specifications/bulk-clip-release/` (already exists, Codex-written)

**The story:** Bulk Clip Release is a clip-state transition, not manufacturing. It retires active clip mappings so downstream Blanking/reuse does not see stale occupied clips, and it must not create Stock Entry records.

**Numbering prefix:** `BCR` (e.g. FR-BCR-001).

**Key findings Codex surfaced:**
- Bulk Clip Release Dash currently sends `process_type`, while the standard orchestrator expects `process_code`; requirements mandate canonical `process_code = BULK_CLIP_RELEASE`.
- Bulk Clip Release has a real doctype/controller intent, but the standard local-create branch and callback routing are incomplete; requirements prefer the audit-first path over direct helper retirement.
- Bulk Clip Release bridge child mapping drifts from Legacy child fields and can confuse barcode text with document name; requirements mandate explicit resolution for both identifiers.
- Direct helper release is fallback, not preferred design.
- Local mirror retirement timing must be explicit.

### Motion #6a — blanking-dc-entry (DONE — Codex correction)

**Covers:** Blanking DC Entry

**Specs to reference:**
- `02-specifications/blanking-dc-entry/` (already exists, Codex-written)
- Legacy code: `shree_polymer_custom_app/.../doctype/blanking_dc_entry/`
- Site records: `spp15.local` has 13260 total BDE records / 13186 submitted.

**The story:** BDE fills a physical blanking bin from a released sheeting clip. It creates the bin-content identity through `Item Bin Mapping` and tracks physical bin movement through native `Asset Movement`.

**Key requirement themes:**
- Clip scan resolves active `Item Clip Mapping`
- BOM compatibility between source compound and target mat/item
- Bin availability and tare weight
- Net weight = gross - bin weight
- Legacy Asset Movement + Item Bin Mapping creation
- Current Ops semantic drift: Ops uses Cutbit-to-PreForming Stock Entry

**Numbering prefix:** `BDE` (e.g. FR-BDE-001).

### Motion #6b — blank-bin-inward-entry (DONE — Codex correction)

**Covers:** Blank Bin Inward Entry

**Specs to reference:**
- `02-specifications/blank-bin-inward-entry/`
- Legacy code: `shree_polymer_custom_app/.../doctype/blank_bin_inward_entry/`
- Site records: `spp15.local` has 1945 total BBIE records / 1919 submitted; `move_to_cut_bit_warehouse=1` dominates (1859 total).

**The story:** BBIE handles a filled bin after BDE. It either creates an Asset Movement for normal inward movement or repacks the contents into cut-bit stock, retiring the source bin mapping.

**Numbering prefix:** `BIE` (e.g. FR-BIE-001).

### Motion #6c — blank-bin-issue (DONE — Codex correction)

**Covers:** Blank Bin Issue

**Specs to reference:**
- `02-specifications/blank-bin-issue/` is currently empty.
- Legacy code: `shree_polymer_custom_app/.../doctype/blank_bin_issue/`
- Site records: `spp15.local` has 68078 total BBI records / 67309 submitted.

**The story:** BBI binds a bin to a Moulding Job Card/Lot. It is a logical issue/reservation, not a Stock Entry or Asset Movement.

**Numbering prefix:** `BBI` (e.g. FR-BBI-001).

### Motion #7 — work-planning (DONE — Codex correction)

**Covers:** Work Planning

**Specs to reference:** Dedicated cockpit spec is missing. Use Legacy code as primary source:
- `shree_polymer_custom_app/.../doctype/work_planning/work_planning.py`
- `shree_polymer_custom_app/.../doctype/work_planning/work_planning.json`
- `shree_polymer_custom_app/.../doctype/work_planning/work_planning.js`

**The story:** Work Planning is the official base production plan for a shift. It may contain multiple products, but Legacy enforces one submitted Work Planning per date + shift series. It creates Work Orders and Job Cards, and the Job Card Lot # becomes the downstream identity for Blank Bin Issue, Inspection, and Moulding.

**Key requirement themes:**
- One submitted Work Planning per date + shift series
- Multiple item rows per shift plan
- Work Plan Item Target validation by item + shift time
- Work Order and Job Card creation
- Cancellation blocked once BBI or MPE references the Job Card Lot #
- Separate process identity from Add On Work Planning

**Numbering prefix:** `WPL` (e.g. FR-WPL-001).

### Motion #8 — add-on-work-planning (DONE — Codex correction)

**Covers:** Add On Work Planning

**Specs to reference:**
- `02-specifications/add-on-work-planning/` exists and is now scoped to supplemental Add On Work Planning only.
- Legacy code remains authority for behavior: `shree_polymer_custom_app/.../doctype/add_on_work_planning/`.

**The story:** Add On Work Planning is supplemental production planning. It uses similar Work Order / Job Card mechanics but does not enforce the one-plan-per-shift rule. It must remain separate from Work Planning in requirements because the shift uniqueness semantics differ.

**Key requirement themes:**
- Supplemental planning beyond the official shift Work Planning
- Multiple add-on records may exist for the same shift unless process owner changes rule
- Uses `Add On Work Plan Item`, not `Work Plan Item`
- Creates additional Work Orders and Job Cards
- Cancellation blocked once downstream BBI or MPE references the Lot #

**Numbering prefix:** `AWP` (e.g. FR-AWP-001).

### Motion #9a — moulding-production-entry (DONE — Codex, split/corrected)

**Covers:** Moulding Production Entry only.

**Specs to reference:** `02-specifications/moulding-production-entry/` exists but is empty. Use legacy code and live `spp15.local` records as primary source.

**The story:** MPE is the terminal production booking. It consumes open Blank Bin Issue rows, validates Line+Patrol Inspection Entry prerequisites, applies legacy production tolerance behavior, creates/submits the Manufacture Stock Entry, completes Job Card/Work Order, and cascades the produced batch to inspection rejection entries.

**Key requirement themes:**
- Inspection prerequisite enforcement (MPE blocks without Line+Patrol)
- Production tolerance parity with `SPP Settings.production_tolerance` (do not hard-code unverified 1% behavior)
- Real-time stock validation
- Partial bin handling (operator weighs remainder)
- FIFO / specific-batch allocation
- Batch generation through legacy `generate_batch_no` contract
- Injection moulding variant (`purged_compound` + `compound_leakage`)
- Cascading Line/Patrol rejection SE submissions after MPE batch_no materialises

**Numbering prefix:** `MPE` (e.g. FR-MPE-001).

Live evidence used: 30,006 MPE records on `spp15.local`, 28,931 submitted; 613 injection records.

### Motion #9b — inspection-entry (DONE — Codex, split/corrected)

**Covers:** Unified Inspection Entry DocType.

**Specs to reference:** `02-specifications/inspection-entry/` exists but is empty. Use legacy code and live `spp15.local` records as primary source.

**The story:** Inspection Entry is a polymorphic quality record, not only the MPE precondition screen. It handles Line, Patrol, Lot, Incoming, Final Visual, and Visual Inspection branches, creates rejection stock entries where applicable, and accepts the MPE-produced batch cascade for moulding rejection entries.

**Key requirement themes:**
- Type-aware validation and duplicate prevention
- Required inspector, lot/context, child rows, and inspected quantity by type
- Defect-row rejected nos/kg capture
- MPE dependency for Line/Patrol batch cascade
- Incoming and Final Visual branches kept visible as real live behavior
- Drift between comments and executable SQL called out for refactor

**Numbering prefix:** `IE` (e.g. FR-IE-001).

Live evidence used: 124,197 Inspection Entry records on `spp15.local`, 120,663 submitted, across six inspection type values.

---

## Currently shipped tally (running total)

| Motion | Author | Status | Lines |
|---|---|---|---|
| mixing-process | Claude | ✅ Done (pilot) | 1179 |
| inspection-process | Codex | ✅ Done (pilot-aligned intent + drift) | 1034 |
| sheeting-process | Codex | ✅ Done (process-scoped correction) | 269 |
| cut-bit-transfer | Codex | ✅ Done (process-scoped correction) | 252 |
| bulk-clip-release | Codex | ✅ Done (process-scoped correction) | 242 |
| blanking-dc-entry | Codex | ✅ Done (Legacy/site-derived correction) | 272 |
| blank-bin-inward-entry | Codex | ✅ Done (Legacy/site-derived correction) | 267 |
| blank-bin-issue | Codex | ✅ Done (Legacy/site-derived correction) | 267 |
| work-planning | Codex | ✅ Done (Legacy-derived correction) | 343 |
| add-on-work-planning | Codex | ✅ Done (Legacy-derived correction) | 277 |
| moulding-production-entry | Codex | ✅ Done (Legacy/site-derived split) | 305 |
| inspection-entry | Codex | ✅ Done (Legacy/site-derived split) | 275 |
| **Requirements total so far** | | | **4983 lines / 108 files** |

Current completed requirements layer: 4983 lines across 108 files.

**Combined with specifications layer:**
- Specs: 13556 lines / 121 files (11 process specs done) → projected ~15-18k lines at completion
- Requirements: 4983 lines / 108 files; Sheeting, Cut Bit Transfer, Bulk Clip Release, BDE, BBIE, BBI, Work Planning, Add On Work Planning, Moulding Production Entry, and Inspection Entry are now separate requirement identities.
- **Current documented cockpit:** 18539 lines / 229 files across requirements + specifications

---

## Final tips

1. **Read the mixing-process pilot before writing.** It's the canonical template. Match its structure exactly. Aim for the same length range per file (~80-180 lines).

2. **Read the corresponding specs first.** The specs surface most of the business intent already — your job is to lift it from implementation-described prose into intent-described requirements. Don't write requirements from scratch; reverse-engineer from shipped reality.

3. **For un-shipped motions** (planning, moulding), use the plan docs at `/Users/alphaworkz/frappe-bench/spp_process_docs/console_porting/` as primary source. Mark every requirement that's NOT yet implemented in `08-traceability.md §Drift findings` with the appropriate status (❌ NOT IMPLEMENTED).

4. **Don't repeat the spec.** If the spec already documents a mechanism, the requirement says "the system must [outcome]" without explaining HOW. The trace is via 08-traceability.

5. **Use tables aggressively.** Same density preference as specs. Bullet lists are fine but tables compress better.

6. **Surface decisions, don't hide them.** Every "we chose X over Y because Z" goes in `05-business-rules.md`. Future Hermes workers re-litigate decisions when the rationale isn't preserved.

7. **Cross-link aggressively.** Each FR in `08-traceability.md` should link to specific spec sections (not just "see the spec folder"). This is the navigation surface for Hermes and reviewers.

8. **You will be tempted to add features.** Don't. Requirements capture intent for what's shipped or planned. New features belong to a separate workstream — flag in `07-out-of-scope.md` if you have ideas.

9. **One question per turn.** Same preference as specs.

10. **When in doubt, ask.** The user prefers a clarifying turn over a wrong document.

---

## How to start

Your first message after reading this prompt should:

1. Confirm you've read and understood:
   - The cockpit at `/Users/alphaworkz/spp-porting-cockpit/`
   - The mixing-process pilot at `01-requirements/mixing-process/` (read all 9 files)
   - The relevant specifications for the next motion (blanking: read `blanking-dc-entry/` and the Wave 2/Wave 3 plan docs for planned bin flows)
2. Briefly state the motion's "story" in 2-3 sentences
3. List the 5 most important business rules you'll capture
4. State your plan for the first 30 minutes of work (spec reading → file writing in order README → 01 → 02 → ...)
5. Ask ONE focused question — typically "Should I proceed with blanking requirements using the completed requirement packs as templates?"

After the user confirms, execute. Don't ask permission to read files or write requirement files — just do it.

When you finish each motion, deliver the same summary shape:
- File list with line counts
- The motion's "story" recap
- 3-5 drift findings (NEW requirements surfaced + requirements without implementation)
- Running tally update
- One focused question (typically the next motion)

Then continue using separate process identity: blanking → work-planning → add-on-work-planning → moulding.

**Match the tone:** concise, table-heavy, plain language, direct opinions, one question at a time.

**Drift hunting is mandatory.** Every motion's `08-traceability.md §Drift findings` must surface at least 3-5 entries. If you find none, you didn't cross-read the specs hard enough.

**Cockpit work is intent-capture, not code change.** When you find a feature gap, document it. Don't propose to build it as part of requirements work.

Good luck.
