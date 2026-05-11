# SPP Porting Cockpit — Requirements Layer Continuation Prompt

**Hand this whole file to a fresh Claude Code or Codex session.** It contains everything that session needs to scaffold business requirements for the remaining business motions without re-deriving context.

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
│   └── mixing-process/       ← PILOT — read this first as the reference
│
├── 02-specifications/        ← OTHER layer — empirical, code-grounded
│   ├── master-batch-mixing/  ← Already done by Claude
│   ├── final-batch-mixing/   ← Already done by Claude
│   ├── compound-deviation/   ← Already done by Claude (with the Saga narrative)
│   ├── sheeting-process/     ← Already done by Claude
│   └── cut-bit-transfer/     ← Already done by Codex
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
| **Grouping** | By **business motion** (e.g. "mixing", "blanking") | By **Console process** (e.g. "Master Batch Mixing") |
| **Per process count** | 1 requirement folder covers 1-3 related processes | 1 spec folder per process |

### How they link

Each requirement entry in `01-requirements/<motion>/08-traceability.md` maps to specification section(s) in `02-specifications/<process>/`. A requirement-without-spec is either a feature gap (acceptable but flagged) or a missing implementation (must be addressed). A spec-without-requirement is either a missing requirement entry (preferred fix) OR a candidate for code removal (rare).

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

Example motion prefixes: `MIX` (mixing), `INS` (inspection), `SHC` (sheeting-cutting), `BLK` (blanking), `PLN` (planning), `MLD` (moulding).

---

## Grouping decision — by business motion

Requirements group **multiple Console processes** into one folder when they share:
- The same shop-floor workflow
- The same operator role(s)
- The same legacy doctype OR closely-related legacy doctypes
- The same business stakeholders (QA Lead, Shop Floor Supervisor, etc.)

Locked grouping:

| Folder | Console processes covered |
|---|---|
| `mixing-process/` | Master Batch Mixing + Final Batch Mixing |
| `inspection-process/` | Compound Inspection + Compound Deviation |
| `sheeting-and-cutting/` | Sheeting Process + Cut Bit Transfer + Bulk Clip Release |
| `blanking/` | Blanking DC Entry + Blank Bin Inward Entry + Blank Bin Issue |
| `production-planning/` | Add On Work Planning (+ Work Planning if implemented) |
| `moulding/` | Moulding Production Entry + Inspection Entry (Line/Patrol/Lot) |

**Total:** 6 requirement folders mapping to ~13 spec folders.

Note: `moulding/` groups MPE with the Inspection Entry sub-processes because MPE blocks on inspection completion — the requirements are tightly coupled. Alternative: separate `inspection-entry/` motion. Use your judgment when you scaffold; the pilot mixing-process grouped MB+FB which had clear shared workflow.

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
| **Sheeting-and-Cutting** (to write) | Multi-output process (clips + cut-bits); clip mapping race (BCR-1); recycling loop back to mixing |
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

## What to do per remaining motion

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

### Motion #3 — sheeting-and-cutting (NEXT)

**Covers:** Sheeting Process + Cut Bit Transfer + Bulk Clip Release

**Specs to reference:**
- `02-specifications/sheeting-process/` (already exists)
- `02-specifications/cut-bit-transfer/` (already exists, Codex-written)
- `02-specifications/bulk-clip-release/` (already exists, Codex-written)

**The story:** Sheeting branches material into two streams (clips → blanking; cut-bits → back to mixing). Cut Bit Transfer consolidates reusable material. Bulk Clip Release moves clips from sheeting to blanking floor. The motion is the central recycling and routing logic.

**Key requirement themes:**
- The BCR-1 inline clip-mapping write (preserves downstream lookup invariant)
- The `Cutbit_` prefix convention for recycled material
- The `CB_` prefix convention for cut-bit mix barcodes
- Two child tables on legacy Material Transfer (`batches` + `sheeting_clip`)
- Cut Bit's dedicated Ops handler + the `run_legacy_sync=False` invariant
- Three-way warehouse routing (Compound → sheeting_wh, blanking_ig → unit2_wh, else → blanking_wh)
- Weak Legacy idempotency for CBT (10-minute window vs reference_id)

**Numbering prefix:** `SHC` (e.g. FR-SHC-001).

### Motion #4 — blanking

**Covers:** Blanking DC Entry + (planned) Blank Bin Inward Entry + (planned) Blank Bin Issue

**Specs to reference:**
- `02-specifications/blanking-dc-entry/` (already exists, Codex-written)
- Wave 2 + Wave 3 plan docs at `/Users/alphaworkz/frappe-bench/spp_process_docs/console_porting/02_WAVE2.md` and `03_WAVE3.md`

**The story:** Blanking turns clips into blank pieces in bins. Bins are physical assets (Asset doctype). Mass balance enforced at Net Weight = Gross - Tare. Bins get issued to Job Cards by Blank Bin Issue (Wave 3). Multiple branches (move_to_cut_bit_warehouse toggle).

**Key requirement themes:**
- Asset Movement (Receive Bin) creation
- Bin tare weight + net weight calculation
- BOM validation at Blanking (per produced blank)
- Branching: standard bin path vs cut-bit repack path
- The `move_to_cut_bit_warehouse` flag and its downstream implications
- Bin state machine: Available → Filled (Blanking) → Inward (at Moulding) → Issued (to Job Card) → Consumed (at MPE)

**Numbering prefix:** `BLK` (e.g. FR-BLK-001).

### Motion #5 — production-planning

**Covers:** Add On Work Planning (+ Work Planning if separate)

**Specs to reference:** None shipped yet. Use plan doc `03_WAVE3.md` as primary source.

**The story:** Wave 3 — production planning generates Lot numbers + Job Cards via the Bridge. The Lot # is the cross-system identity that all downstream Inspection + Moulding records reference. Open question: Console-first vs Legacy-first Lot # generation (Pattern A vs Pattern B per plan doc).

**Key requirement themes:**
- Lot # generation authority (recommended: Console-first)
- Job Card creation on Legacy (via whitelisted method `create_planning_with_jobcards`)
- Work Plan Item Target validation (>10% drift from shift target throws)
- Multi-row planning (one supervisor → many items × workstations)
- Cross-system Job Card naming reconciliation (Legacy vs Ops)

**Numbering prefix:** `PLN` (e.g. FR-PLN-001).

### Motion #6 — moulding

**Covers:** Moulding Production Entry + Inspection Entry (Line/Patrol/Lot variants)

**Specs to reference:** None shipped yet. Use plan docs `04_WAVE4.md` and `05_WAVE5.md`.

**The story:** The terminal process and highest-complexity wave. MPE consumes Blank Bins, runs against a Lot/Job Card, validates Line+Patrol inspection prerequisites, and generates the final FG batch number. Inspection Entry is a precondition — three variants (Line/Patrol/Lot) with uniqueness constraints per Lot.

**Key requirement themes:**
- Inspection prerequisite enforcement (MPE blocks without Line+Patrol)
- Mass balance ENFORCED here (1% tolerance) — the one place it's a hard throw
- Real-time stock validation
- Partial bin handling (operator weighs remainder)
- FIFO / specific-batch allocation
- Batch # generation cascade (MPE generates batch_no, propagates back to all Inspection Entries for the lot)
- Injection moulding variant (`purged_compound` + `compound_leakage`)
- Cascading SE submissions (rejection SEs from inspections submit after MPE batch_no materialises)

**Numbering prefix:** `MLD` (e.g. FR-MLD-001).

This is the **largest motion**. Estimated requirements pack size: 1500-2000 lines.

---

## Currently shipped tally (running total)

| Motion | Author | Status | Lines |
|---|---|---|---|
| mixing-process | Claude | ✅ Done (pilot) | 1179 |
| inspection-process | Codex | ✅ Done (intent + drift) | 876 |
| sheeting-and-cutting | — | ⏳ Next | — |
| blanking | — | Queued | — |
| production-planning | — | Queued | — |
| moulding | — | Queued | — |
| **Requirements total so far** | | | **2055 lines / 18 files** |

Expected total at completion: ~7,000-10,000 lines across ~54 files (6 motions × 9 files each).

**Combined with specifications layer:**
- Specs: 9736 lines / 77 files (7 of 8 processes done) → projected ~12-15k lines at completion
- Requirements: 2055 lines / 18 files (2 of 6 motions done) → projected ~7-10k lines at completion
- **Total cockpit at completion:** ~20-25k lines / ~110-120 files

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
   - The relevant specifications for the next motion (sheeting-and-cutting: read `sheeting-process/`, `cut-bit-transfer/`, and `bulk-clip-release/`)
2. Briefly state the motion's "story" in 2-3 sentences
3. List the 5 most important business rules you'll capture
4. State your plan for the first 30 minutes of work (spec reading → file writing in order README → 01 → 02 → ...)
5. Ask ONE focused question — typically "Should I proceed with sheeting-and-cutting requirements using the mixing-process and inspection-process packs as templates?"

After the user confirms, execute. Don't ask permission to read files or write requirement files — just do it.

When you finish each motion, deliver the same summary shape:
- File list with line counts
- The motion's "story" recap
- 3-5 drift findings (NEW requirements surfaced + requirements without implementation)
- Running tally update
- One focused question (typically the next motion)

Then continue: sheeting-and-cutting → blanking → production-planning → moulding.

**Match the tone:** concise, table-heavy, plain language, direct opinions, one question at a time.

**Drift hunting is mandatory.** Every motion's `08-traceability.md §Drift findings` must surface at least 3-5 entries. If you find none, you didn't cross-read the specs hard enough.

**Cockpit work is intent-capture, not code change.** When you find a feature gap, document it. Don't propose to build it as part of requirements work.

Good luck.
