# 07 — Out of scope

This document explicitly states what the Mixing Process requirements do NOT cover. The purpose is to prevent scope creep and clarify boundaries when a Hermes worker is tempted to "fix" something adjacent.

## Out of scope — features

### OOS-MIX-001 — Real-time stock consistency across ERPs

The Mixing Process does NOT guarantee real-time inventory consistency between Legacy and Ops. The eventual-consistency model (BR-MIX-004) is explicit. Any feature request to "make stock always match" belongs to a separate reconciliation epic.

**Why not:** Real-time consistency requires a two-phase commit across ERPs, which has been explicitly rejected as too slow and too fragile.

### OOS-MIX-002 — Transactional rollback on Partial sync

If one leg succeeds and the other fails, the system does NOT automatically roll back the successful leg to maintain consistency. The Partial state persists until an operator retries.

**Why not:** Compensating-transaction logic across two ERPs is high-risk and rarely needed. The Partial state is operationally visible and recoverable.

### OOS-MIX-003 — Mass balance enforcement

The system does NOT enforce a mass-balance check at submit time (BR-MIX-002). Deviations between consumption and production are captured but not blocked.

**Why not:** Operational decision — deviations are a real production signal.

**If reinstated as a future requirement:** must be a soft warning (logged + surfaced in success modal), NOT a hard throw.

### OOS-MIX-004 — Historical back-fill of pre-Console DCR records

The Mixing Process does NOT include any back-fill mechanism to import pre-Console (Bridge-era) legacy DCR records into Console.

**Why not:** Historical legacy records do not carry `reference_id` and cannot be correlated to Console submissions. Querying historical Mixing data requires querying Legacy DCR directly.

**Implication for reports:** any report that needs "all MB mixings ever" must union Console + Legacy DCR — Console is NOT exhaustive for historical data.

### OOS-MIX-005 — Multi-cavity mould tracking

The Mixing Process does NOT track cavity-level production data. (The downstream Moulding Production Entry process does.) The Mixing record is a single-cavity-equivalent record regardless of the downstream moulding setup.

**Why not:** Mixing happens at the mill, before any moulding decision. Cavity tracking would couple Mixing to downstream MPE concerns.

### OOS-MIX-006 — Operator productivity metrics

The Mixing Process records WHO submitted (`submitted_by`) but does NOT include features for measuring operator productivity, shift efficiency, or comparative throughput.

**Why not:** Productivity analytics belong to a separate reporting layer that consumes Console + Legacy + Ops data via reports. Building metrics into the transactional flow couples concerns.

### OOS-MIX-007 — Real-time machine integration (PLCs, sensors)

The Mixing Process does NOT integrate with the mixing mill's PLC or any sensor data. Operator manual entry is the data source.

**Why not:** PLC integration is a separate epic — different protocol stack, different data shape, different failure modes.

**Future consideration:** A "PLC-attested mixing submission" feature could attach sensor readings to the payload. That's a separate requirement.

### OOS-MIX-008 — Bin / asset state machine

The Mixing Process does NOT manage bin or asset states (those are managed by Cut Bit Transfer, Bulk Clip Release, Blanking, etc.). Mixing only produces an FG batch — what happens to it downstream is out of scope.

**Why not:** Each downstream process owns its own state machine. Coupling Mixing to bin lifecycle would violate separation of concerns.

### OOS-MIX-009 — Multi-BOM resolution

The Mixing Process does NOT support multiple active BOMs for the same produced item. If a produced item has more than one active BOM, the legacy controller rejects the submission with "Multiple BOM's found."

**Why not:** Multi-BOM resolution requires additional operator input (which BOM is being used) and complicates the audit trail. The business has chosen one-active-BOM-per-item as a constraint.

**Recovery path:** Legacy BOM cleanup — deactivate duplicate BOMs.

### OOS-MIX-010 — Localisation / non-English UI

The Dash UI for Mixing is English-only. No localised strings, currency conversion, or non-Gregorian date support.

**Why not:** Single-site deployment; English is the working language. Localisation belongs to a separate i18n epic if Console expands to multi-site / multi-region.

## Out of scope — operations

### OOS-MIX-020 — Automatic retry of failed submissions

The Mixing Process does NOT automatically retry failed legs. Operators must explicitly press Retry.

**Why not:** Auto-retry on transient errors can mask underlying issues. Operator-driven retry forces awareness of the failure mode.

### OOS-MIX-021 — Cross-shift handoff reconciliation

There is no system feature for "end-of-shift reconciliation" of partially-synced records. Shift handoffs rely on operators reviewing `Console Transaction Log` filtered by `status != "Success"`.

**Why not:** Reconciliation is an operational practice, not a code feature. A reconciliation dashboard exists as a future epic.

### OOS-MIX-022 — Approval workflow

Mixing submissions do NOT require any approval workflow. An operator submits; the record submits. Approval workflows exist on adjacent processes (Compound Deviation) but not on Mixing itself.

**Why not:** Mixing is high-frequency. Approval would introduce queue lag that breaks shop floor pace.

## Out of scope — integrations

### OOS-MIX-030 — Direct database access from Dash

The Dash UI does NOT make direct database queries to Legacy or Ops. All communication goes via Console's backend API.

**Why not:** Cross-ERP DB access from a browser is a security and topology nightmare.

### OOS-MIX-031 — Webhook from Bridge to Console

The Bridge does NOT POST webhooks back to Console. Console reads the Bridge's HTTP response synchronously.

**Why not:** A webhook from Bridge → Console would require Bridge to know how to reach Console (firewall + auth complexity). The synchronous response-read model is simpler.

### OOS-MIX-032 — Mixing data export to BI / data warehouse

The Mixing Process does NOT include a feature for exporting data to a BI tool or data warehouse. Data lives in the three ERPs and is queryable via Frappe reports / API.

**Why not:** BI integration is a separate downstream epic, not part of the transactional Mixing flow.

## Related but out of scope (link to other requirement folders)

| Related process | Owned by |
|---|---|
| Compound Inspection (QA after Mixing) | `01-requirements/inspection-process/` (TBD) |
| Compound Deviation (QM override on rejected lots) | `01-requirements/inspection-process/` (TBD) |
| Sheeting (consumes Mixing output) | `01-requirements/sheeting-and-cutting/` (TBD) |
| Cut Bit Transfer (recycles cut-bits back to Mixing) | `01-requirements/sheeting-and-cutting/` (TBD) |
| Stock reconciliation | future `01-requirements/reconciliation/` |
| Operator productivity reporting | future `01-requirements/reporting/` |

## When in doubt

If a Hermes worker is unsure whether a change is in scope, the test is:

1. Does the change affect the Mixing operator's submission flow?
2. Does it change what records land on Console / Legacy / Ops for a Mixing submission?
3. Does it change the cross-system invariants (reference_id round-trip, barcode authority, race-safe aggregation)?

If yes to any of these — in scope. If no to all three — likely out of scope, belongs to another requirement folder.
