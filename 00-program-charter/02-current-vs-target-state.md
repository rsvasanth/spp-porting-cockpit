# 02 — Current vs target state

This file shows the SPP manufacturing workflow **before** and **after** the porting program, side by side. Use it to brief stakeholders on what changes for the shop floor.

## High-level transformation

### Before (legacy-only)

```
Shop floor operator
       │
       ▼ (uses Desk UI on tablet)
┌────────────────────────────────────┐
│   Legacy ERPNext (sppmaster)        │
│   - 100+ custom doctypes            │
│   - Desk-based submission           │
│   - Reports run here                │
│   - Single point of failure         │
└────────────────────────────────────┘
```

### After (Console + parallel ERPs)

```
Shop floor operator
       │
       ▼ (uses React Dash on tablet — scanner-driven)
┌────────────────────────────────────┐
│   Console (console.m)               │
│   - System of record                │
│   - Identity owner (reference_id,   │
│     mix_barcode, Lot #)             │
│   - Audit trail                     │
└──────┬─────────────────────┬────────┘
       │ parallel             │
       ▼                      ▼
┌──────────────┐      ┌────────────────┐
│ Legacy ERP   │      │  Ops ERP        │
│ (sppmaster)  │      │  (newspp)       │
│              │      │                 │
│ Custom       │      │ NATIVE ERPNext  │
│ doctypes     │      │ only            │
│ preserved    │      │ (Stock Entry,   │
│              │      │  Work Order,    │
│ Historical   │      │  Job Card,      │
│ reports keep │      │  Batch)         │
│ working      │      │                 │
└──────────────┘      └────────────────┘
       │                      │
       └──── eventually consistent ────┘
```

## Per-stage comparison

For each stage in the manufacturing chain, here's what changed:

### Master Batch Mixing

| Aspect | Before | After |
|---|---|---|
| Operator UI | Legacy Desk form (DCR with `inward_material_type=Master Batch`) | Console Dash `MasterBatchMixingEntry.tsx` |
| Where submission lands | Legacy DCR | Console `Console Master Batch Mixing` → Bridge → Legacy DCR + Ops Stock Entry (parallel) |
| Mix barcode authority | Legacy auto-generated | Console-generated (`C_YYMMDDXn`); Legacy honors via `bridge_mix_barcode` |
| Audit trail | DCR record only | Console doc + Console Transaction Log + Legacy Bridge Log + Ops MES Log |
| Failure recovery | Manual re-entry on Desk | Operator retry via Dash with same `reference_id` |
| Ops representation | None (Legacy-only world) | Native ERPNext Stock Entry (Manufacture) |

### Final Batch Mixing

| Aspect | Before | After |
|---|---|---|
| Operator UI | Legacy Desk DCR (`inward_material_type=Compound`) | Console Dash `FinalBatchMixingEntry.tsx` |
| Where submission lands | Legacy DCR + auto-generated Work Order + Stock Entry | Console doc → Bridge → same Legacy chain + Ops native Stock Entry |
| MB lot scan | Manual barcode entry on Desk | Scanner-driven on Dash; `is_batch_item=1` flag automated |
| Ops representation | None | Native ERPNext Stock Entry (Manufacture) consuming MB + raw materials |

### Compound Inspection

| Aspect | Before | After |
|---|---|---|
| Operator UI | Legacy Desk Compound Inspection form | Console Dash `CompoundInspectionEntry.tsx` (Phase 3 unified) |
| Where submission lands | Legacy Compound Inspection (one of 3 per-type doctypes) | Console `Console Inspection` (unified) → Bridge → Legacy Compound Inspection + Ops Material Transfer SE (status-conditional) |
| Identity resolution | Manual lookup of `stock_id` | Bridge's 6-strategy SE lookup with shared helpers |
| Rejected lot routing | Operator re-files manually | Factory requirement skip: rejected CIs route Ops-only; Compound Deviation later closes the Legacy gap |

### Compound Deviation

| Aspect | Before | After |
|---|---|---|
| Operator UI | Legacy Desk Compound Inspection (manual status override by QM) | Console Dash `CompoundDeviationEntry.tsx` with explicit QM signoff flow |
| Where submission lands | Legacy Compound Inspection (same doctype as regular CI) | Console doc (separate `Console Compound Deviation`) → Bridge populate function → Legacy Compound Inspection with QM fields |
| QM signoff capture | Manual notes | Explicit `quality_approver_id` + `deviation_reason` + status (Accepted/Rejected/Rework) |
| Ops representation | None | Conditional Stock Entry (only if status=Accepted) |

### Sheeting Process

| Aspect | Before | After |
|---|---|---|
| Operator UI | Legacy Desk Material Transfer form | Console Dash `SheetingProcessEntry.tsx` |
| Where submission lands | Legacy Material Transfer + auto-generated Stock Entry | Console doc + Item Clip Mapping rows → Bridge → Legacy Material Transfer + Ops native Stock Entry |
| Clip mapping creation | Manual or Legacy-on-submit | Console inline at create time (BCR-1 fix) |
| Cut-bit vs clip distinction | `is_cut_bit_item` flag on legacy | Same flag, populated by Dash, reconciled by Bridge via `Cutbit_` prefix |
| Ops representation | None | Native Stock Entry (Material Transfer purpose) |

### Cut Bit Transfer

| Aspect | Before | After |
|---|---|---|
| Operator UI | Legacy Desk Cut Bit Transfer form (with clip/bin scan UX) | Console Dash `CutBitTransferEntry.tsx` |
| Where submission lands | Legacy Cut Bit Transfer + on-submit Stock Entry | Console doc + bin mapping retirement → Bridge (Legacy CBT + SE) + Ops dedicated handler (Repack SE) |
| Ops representation | None | Native Stock Entry (Repack) with `use_serial_batch_fields=1` |
| Idempotency | Manual operator awareness | Bridge: `scan_clip__bin` + 10-min window (weaker than reference_id); Ops: `Shree Polymer MES Log` by reference_id |

### Bulk Clip Release

| Aspect | Before | After |
|---|---|---|
| Operator UI | Legacy Desk Bulk Clip Release | Console Dash `BulkClipReleaseEntry.tsx` |
| Where submission lands | Legacy BCR record | Console doc → Bridge → Legacy BCR + Ops dedicated handler |
| Clip state management | Manual via Desk | Console-coordinated state machine; Ops `bulk_release_clips(barcodes=...)` updates clip status |

### Blanking DC Entry

| Aspect | Before | After |
|---|---|---|
| Operator UI | Legacy Desk Blanking DC Entry | Console Dash `BlankingDCEntry.tsx` |
| Where submission lands | Legacy Blanking DC Entry + Asset Movement (Receive Bin) | Console doc → Bridge → Legacy chain + Ops dedicated handler creating Stock Entry + Asset Movement |
| Mass-balance check (net = gross − tare) | Manual on Desk | Enforced at Dash submit-time |
| Move-to-cut-bit toggle | Implicit in form fields | Explicit `move_to_cut_bit_warehouse` flag with branching (bin vs repack path) |

### Blank Bin Inward Entry

*(Not yet shipped — Wave 2 target state)*

| Aspect | Before | After |
|---|---|---|
| Operator UI | Legacy Desk Blank Bin Inward Entry | Console Dash (planned) |
| Where submission lands | Legacy + auto Asset Movement | Console doc → Bridge → Legacy + Ops Asset Movement |
| Cut-bit warehouse repack mode | Implicit on Desk | Explicit toggle on Dash |

### Add On Work Planning

*(Not yet shipped — Wave 3 target state)*

| Aspect | Before | After |
|---|---|---|
| Operator UI | Legacy Desk Add On Work Planning | Console Dash (planned) |
| Lot # generation | Legacy auto-generates | Console-first (Pattern A from plan) — Console generates Lot #, pushes to both ERPs |
| Job Card creation | Legacy generates one per item | Bridge calls `create_planning_with_jobcards` on Legacy; Ops generates equivalent via TransactionEngine |

### Blank Bin Issue

*(Not yet shipped — Wave 3 target state)*

| Aspect | Before | After |
|---|---|---|
| Operator UI | Legacy Desk Blank Bin Issue | Console Dash (planned) |
| BOM validation | Legacy on-submit check | Enforced at Dash submit-time + Bridge mapping |

### Inspection Entry (Line / Patrol / Lot)

*(Not yet shipped — Wave 4 target state)*

| Aspect | Before | After |
|---|---|---|
| Operator UI | Legacy Desk Inspection Entry (one of 3 sub-types) | Single Console Dash screen handling all 3 via dropdown |
| Where submission lands | Legacy Inspection Entry | Console doc → Bridge → Legacy + Ops |
| Uniqueness enforcement | Manual operator discipline | Console + Legacy + Ops all enforce one-of-each-type per Lot |
| Rejection SE timing | Created at inspection-submit | Deferred until MPE submits and batch_no materialises |

### Moulding Production Entry

*(Not yet shipped — Wave 5 target state, the terminal stage)*

| Aspect | Before | After |
|---|---|---|
| Operator UI | Legacy Desk MPE form (complex) | Console Dash with mass-balance display, bin scan UX, inspection-status indicator |
| Mass balance | Loose check on Desk | Enforced 1% tolerance at Dash + Console submit |
| Batch # generation | Legacy auto | Console generates `T-LOT-YYYYMMDD-NNN-NNN` and propagates to both ERPs + Inspection Entries |
| Partial bin handling | Manual on Desk | Explicit Balance Bin child table on Dash with weight reconciliation |
| Cascade SE for rejection inspections | Manual after MPE submit | Automatic — MPE's Bridge sequence calls `submit_inspection_stock_entries_from_moulding` |

## Cross-cutting changes (apply to every stage)

| Concern | Before | After |
|---|---|---|
| Cross-system identity | Each ERP has its own naming series; cross-references manual | `reference_id` (13-digit ms timestamp from Console) is the single key across all systems |
| Mix barcode | Each ERP generates its own | Console-authored `C_YYMMDDXn`; both ERPs honor it |
| Audit trail | Doctype rows only | Console doc + 2 Transaction Logs + Legacy Bridge Log + Ops MES Log per submission |
| Retry semantics | Manual operator awareness | Idempotent at all four layers (Console, Bridge, Ops, downstream) |
| Failure visibility | Hidden until next-shift report | Live Feedback per-target during submit; `Console Transaction Log` queryable in real-time |
| Stock validation | Legacy-side only | Multi-system: Dash pre-validates, Ops enforces at SE submit |
| Operator role enforcement | Frappe permissions only | Three layers: Frappe perms + Dash UI gating + server-side filter on operator list |

## What does NOT change

- Shop-floor physical workstations (mixing mills, sheeting line, blanking presses, moulding machines)
- Item codes, BOMs, batch numbering conventions (Master Batch / Compound / Cutbit_ prefixes preserved)
- Quality Manager signoff authority (still QM role)
- Stock Ledger semantics (Frappe-native; both ERPs use it the same way)
- Reports running on Legacy (preserved untouched; this is why Legacy stays alive)
- Accounting, HR, Procurement modules (entirely out of program scope; remain on Legacy)
