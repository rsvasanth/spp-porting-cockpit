# 10 — Risks and decisions

## Critical drift findings — decisions required before shipping

These are **not** minor gaps. They are contradictions between documented
behavior and executable behavior that must be resolved before any refactor
touches the IE `on_submit` or MPE cascade chains.

---

### Critical Drift Finding #1 — `on_submit` trigger query excludes Patrol

**The mismatch:**

The `on_submit` comment at line 48-49 says:
```python
# 🆕 NEW FLOW: Submit stock entries when Line + Lot inspections are complete
# ✅ UPDATED: Now includes Patrol Inspection in the query
```

But the executable SQL at lines 50-56 checks **only** `Line Inspection` OR
`Lot Inspection` — Patrol is **NOT** included:

```python
exe_insp = frappe.db.sql(
    f"""SELECT name FROM `tabInspection Entry` 
    WHERE (inspection_type = 'Line Inspection' OR inspection_type = 'Lot Inspection') 
    AND docstatus = 1 AND lot_no = '{self.lot_no}'""",
    as_dict=1
)
```

**Impact:**

The cascade trigger fires when **Line + Lot** are both submitted (count >= 2).
Patrol IE, even when submitted, does not participate in the trigger.

However, `submit_inspection_stock_entry_immediately` (called when the trigger
fires) **does** include Patrol in its cascade query (line 239):
```python
WHERE (inspection_type = 'Line Inspection' 
       OR inspection_type = 'Lot Inspection' 
       OR inspection_type = 'Patrol Inspection')
```

So the inconsistency is:
- The **trigger** excludes Patrol
- The **cascade** includes Patrol

**Operational effect:** If an operator submits Line IE (draft SE created) and
then submits Patrol IE (draft SE created), the trigger never fires because
it only watches Line + Lot. The cascade only fires when **Line + Lot** are both
submitted. Patrol's draft SE will only get its batch and be submitted when
`submit_inspection_stock_entry_immediately` is called by a **Line or Lot** submit
after MPE exists.

**Decision required:**

| Option | Description | Recommendation |
|---|---|---|
| A — Confirm trigger is Line + Lot only (ignore comment) | The comment is wrong; actual behavior is Line + Lot. Patrol is excluded intentionally. | Clarify with QA Lead if this is intentional |
| B — Add Patrol to trigger query | Change SQL to `OR inspection_type = 'Patrol Inspection'` | Makes trigger consistent with cascade |
| C — Make trigger fire on any IE submit when MPE exists | Refactor to check MPE + any IE, not count-based | More robust but bigger change |

**My recommendation:** Option B — add Patrol to the trigger query. The comment
explicitly says "includes Patrol" and the cascade already handles Patrol.
The current state is a bug where the trigger and cascade are inconsistent.

---

### Critical Drift Finding #2 — Two overlapping MPE batch cascade paths

**The mismatch:**

There are **two** distinct functions that perform the same physical operation
(updating IE rejection Stock Entries with MPE's produced batch):

| Function | Location | Cascade scope |
|---|---|---|
| `submit_inspection_stock_entries_from_moulding` | MPE controller (`../moulding-production-entry/`) | Line + Patrol IE (via `_submit_line_and_patrol_inspections`) |
| `submit_inspection_stock_entry_immediately` | IE controller (this spec, line 185) | Line + Lot + Patrol IE (via `exe_insp` query) |

**How the two paths work:**

**Path 1 — MPE side (MPE `on_submit`):**
```
MPE submitted
  → MPE.on_submit calls submit_inspection_stock_entries_from_moulding
      → _submit_line_and_patrol_inspections(lot_no)
          → query: Line OR Patrol IE for lot (NOT Lot)
          → for each: update batch_no + submit SE
```

**Path 2 — IE side (IE `on_submit`):**
```
IE submitted (Line or Lot)
  → IE.on_submit trigger query (Line + Lot count >= 2)
  → submit_inspection_stock_entry_immediately
      → get MPE batch
      → query: Line OR Lot OR Patrol IE for lot (includes Patrol but NOT MPE stock_entry check)
      → for each: update batch_no + submit SE
```

**Why this is a problem:**

1. **Double-cascade risk:** If both MPE's `on_submit` and IE's `on_submit`
   fire for the same lot, the same SE could be updated twice. However, the
   second update is idempotent (same batch_no), so data is not corrupted,
   but performance is wasted.

2. **Scope mismatch:** MPE side cascades to Line + Patrol (not Lot).
   IE side cascades to Line + Lot + Patrol (includes Lot, excludes nothing).
   If Lot IE's `on_submit` fires the IE cascade, it will update Line + Lot
   + Patrol SEs — which overlaps with what MPE would do if MPE is also
   submitted.

3. **MPE existence check:** MPE's helper only fires when MPE stock_entry
   reference exists (MPE submitted). IE's helper also gets MPE from the same
   condition. Both require MPE to exist.

**Decision required:**

| Option | Description | Recommendation |
|---|---|---|
| A — Consolidate to single cascade function | Keep one cascade function (MPE side or IE side), delete the other. Update both MPE and IE specs. | Best — removes double-cascade risk |
| B — Coordinate trigger scopes | MPE cascades Line + Patrol, IE cascades Line + Lot. Non-overlapping. | Achievable but requires careful ownership boundary |
| C — Add MPE existence guard to IE cascade | IE cascade only fires if MPE exists and has stock_entry_reference. Prevents duplicate when MPE cascade already fired. | Safe fallback but doesn't reduce redundancy |
| D — Document as intentional two-stage cascade | MPE fires first (Line+Patrol), then IE fires on Line+Lot (Line already handled, adds Lot+Patrol). No conflict because MPE and IE are submitted in different orders. | Works but fragile if order changes |

**My recommendation:** Option A — consolidate to a single cascade function.
The cascade is the same operation regardless of which side triggers it.
Having two trigger paths is a maintenance hazard and creates confusion about
which function owns the batch update invariant.

**Coordination required with:** MPE spec (`../moulding-production-entry/10-risks-and-decisions.md`) — both drift findings must be resolved together.

---

## Cross-doctype invariants Hermes must NOT break

These invariants are load-bearing for the IE → MPE → rejection SE chain.
Breaking one layer doesn't immediately fail but compounds downstream.

| # | Invariant | Where enforced | Breaks if… |
|---|---|---|---|
| 1 | `stock_entry_reference` on IE links to the draft Material Transfer rejection SE | `make_stock_entry` line 675 | IE re-submitted without `stock_entry_reference` cleared |
| 2 | `source_ref_document = 'Inspection Entry'` AND `source_ref_id = ie.name` on SE Detail | `make_stock_entry` line 669-671 | IE cascade `WHERE` clause fails to find the SE Detail |
| 3 | Batch update cascade reads from MPE's Stock Entry finished item row | `submit_inspection_stock_entry_immediately` line 219-227 | MPE changes its SE structure or finished item row format |
| 4 | Patrol is excluded from trigger query but included in cascade | `on_submit` line 50-56 vs line 239 | See Critical Drift Finding #1 |
| 5 | `vs_pdir_qty_after_rejection` precomputed in `validate()` before `on_submit` | `validate()` line 36-39 | Field recomputed differently or reset before Branch C fires |
| 6 | Incoming IE triggers `Deflashing Receipt Entry.manual_on_submit` | `submit_deflash_receipt_entry` line 328-330 | DRE's `manual_on_submit` signature changes |
| 7 | Final Visual exemption from duplicate prevention | `validate()` line 25 | Duplicate rule extended to Final Visual, blocking re-inspection |
| 8 | `reference_id` is cross-system correlation key for IE | Console Transaction Log + Bridge idempotency | `reference_id` generation changes or is not set on IE |

---

## Other decisions deferred

### Lot Inspection requires MPE to exist

`validate_lot_number` for Lot Inspection throws if no MPE `stock_entry_reference`
is found. Line and Patrol do not have this requirement. This is a deliberate
business rule (Lot is the final moulding gate; MPE must have been produced).

**Revisit when:** MPE and IE are deployed — confirm QA agrees Lot IE should
require MPE before Line/Patrol.

### Visual Inspection (6 records)

Only 6 records exist with `inspection_type = "Visual Inspection"`. This is
likely a pre-unification artifact. The JSON schema does not list "Visual
Inspection" as an option (only Patrol, Line, Lot, Incoming, Final Visual).
Recommend treating it as deprecated and **not** adding it as a supported type
unless production use resurfaces.

### Defect type field hidden in JSON but used in child table

The JSON has `"hidden": 1` for `type_of_defect` and `rejected_qty` fields
(lines 175, 182). But the child table `Inspection Entry Item` is shown and
the legacy controller logic depends on these fields. The hidden flag likely
applies to the header-level display, not the child table. Console Dash should
expose these fields in the child table regardless of the JSON's hidden flag.

### `submit_moulding_entry` deprecated

The `submit_moulding_entry` function (line 172-183) is marked deprecated and
logs an error if called. This was the old flow where IE would trigger MPE's
SE submission. The new flow has MPE's `on_submit` calling `submit_inspection_stock_entries_from_moulding`
instead. This deprecated function is kept for backward compatibility and
should be removed in a future cleanup wave.

### No Ops leg for Inspection Entry

Currently `sync_strategy` for `INSPECTION_ENTRY` is `"Legacy Bridge Only"`.
The rejection Stock Entry lives on Legacy. This was a deliberate choice since
the rejection warehouse (Unit-2 → Rejection warehouse) is on the Legacy side.
If a future wave adds Ops participation, the entire rejection SE creation
pattern would need re-architecting.

**Do not add an Ops leg for IE without a formal architecture review** — it
changes the fundamental data flow for a production-critical quality gate.

---

## What I want you (production overseer) to decide before IE ships

| Question | Why it matters | My recommendation |
|---|---|---|
| Drift #1: Patrol in trigger query? | Cascade may miss Patrol IE in some submission orders | **Add Patrol to trigger query** — comment says it should be included |
| Drift #2: Consolidate cascade functions? | Double-cascade risk, maintenance hazard | **Consolidate to one function** — either MPE side or IE side, not both |
| Lot Inspection MPE requirement confirmed? | Blocking validation for Lot IE | **Confirm** — if MPE must be submitted before Lot IE, this is intentional |
| Visual Inspection (6 records) — treat as deprecated? | Avoids adding a 6-record edge case to Console | **Yes, mark deprecated** — do not add as supported type |
| Add an Ops leg for inspection in a future wave? | Would re-architect rejection SE creation | **No for now** — Legacy-only is simpler; revisit when ops scale demands it |
| Remove deprecated `submit_moulding_entry` in cleanup wave? | Dead code | **Yes** — remove in Wave N cleanup, after MPE cascade is confirmed stable |

---

## When in doubt — pause and ask

This spec documents **empirical behavior** from live production code. The two
critical drift findings show that even the comments in the code are not
authoritative — the executable SQL is. Before any Hermes worker modifies
the IE `on_submit`, the MPE cascade, or the `validate_lot_number` branching,
these drift findings must be resolved with explicit approval from the
production overseer.

The cost of asking is one turn; the cost of a cascade change that breaks
rejection stock entries for 124k+ production records is days of recovery.