# 05 — Business rules

Business rules explain the durable why behind the requirements.

## BR-INS-001 — Inspection is a gate, not production

Inspection does not create material. It changes the allowed disposition of material that already exists.

**Why:** Mixing owns compound creation. Inspection protects downstream processes from consuming material that has not passed QA.

## BR-INS-002 — Failed readings produce Rejected CI

If any required reading is out of spec, the Compound Inspection must be Rejected.

**Why:** The inspector records lab truth. The override decision belongs to a Quality Manager, not the original inspection.

## BR-INS-003 — Rejected CIs skip Legacy until Deviation

Rejected Compound Inspections must not route to Legacy immediately.

**Why:** Legacy represents final QA disposition with stock side effects. Sending both the initial rejection and the later Deviation can duplicate or confuse legacy stock behavior.

## BR-INS-004 — Deviation is the formal QM disposition

A rejected compound can move again only after a Quality Manager records a Deviation decision.

**Why:** This preserves accountability and prevents informal shop-floor bypasses.

## BR-INS-005 — Only three Deviation statuses are valid

Accepted, Rejected, and Rework are the supported business outcomes.

| Status | Why it exists |
|---|---|
| Accepted | Allows controlled override |
| Rejected | Removes bad material |
| Rework | Keeps material pending correction |

## BR-INS-006 — Deviation lands as legacy Compound Inspection

Legacy receives Deviation as `Compound Inspection`.

**Why:** Legacy reports and controller stock behavior already understand that doctype. A new legacy doctype would split the historical quality record.

## BR-INS-007 — Empty mapping for Deviation is intentional

Deviation field population should stay in Bridge Python helpers, not declarative mapping rows.

**Why:** The Bridge must resolve identity, Stock Entry, readings, and Deviation extras in a coordinated way. The mapping engine cannot express that safely.

## BR-INS-008 — Shared identity lookup must not fork

Compound Inspection and Deviation must use the same identity and Stock Entry lookup pipeline.

**Why:** The 2026-04-30 bug came from duplicated lookup logic drifting after payload shape changed.

## BR-INS-009 — The 5-step callback pattern is business-critical

The business rule is: target responses must not falsely leave a fully synced record as Partial.

**Why:** Operators and supervisors make retry/escalation decisions based on this status. The Compound Deviation saga proved this was not theoretical.

## BR-INS-010 — Deviation reason minimum

Deviation reason must be at least 5 characters.

**Why:** Short entries like "ok" do not create an audit trail. The reason is the business justification for overriding or disposing material.

## BR-INS-011 — One active Deviation per rejected CI

The same rejected CI cannot have two active Deviation decisions.

**Why:** Two dispositions for one material lot create stock and audit contradiction.

## BR-INS-012 — `cavity_no` matters

`cavity_no` should be captured end-to-end when available.

**Why:** Multi-cavity runs are rare but real. Defaulting to 1 preserves operation but loses data quality.

## BR-INS-013 — Status-skipped Ops actions can still be success

If Ops skips an action because the status condition is false, that can still be a successful target leg.

**Why:** Not every quality decision creates a Stock Entry. A skipped action is not automatically a failed sync.

## BR-INS-014 — Original readings are not rewritten by Deviation

Deviation can carry readings forward, but it must not change the source CI's lab facts.

**Why:** QA results and QM disposition are separate audit facts.

## BR-INS-015 — Unified inspection is the target model

New inspection-type work should use `Console Inspection` and Process Template configuration.

**Why:** It gives one reporting surface and avoids another round of per-type doctype drift.

