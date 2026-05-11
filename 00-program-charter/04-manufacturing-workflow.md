# 04 — Manufacturing workflow

This file is the **program's table of contents** for the manufacturing scope. It maps each stage of SPP's production chain to its legacy doctype, Console doctype, and Ops native doctype.

Read this when you need to understand "which processes are in this program" or "what's the mapping from legacy custom to Ops native for stage X."

## The 13-stage manufacturing chain

```
Stage  1.  Master Batch Mixing
Stage  2.  Final Batch Mixing
Stage  3.  Compound Inspection      [↘ Compound Deviation if Rejected]
Stage  3a. Compound Deviation (overlay)
Stage  4.  Sheeting Process
Stage  5.  Cut Bit Transfer         [recycling: cut-bits → back to Stage 2]
Stage  6.  Bulk Clip Release
Stage  7.  Blanking DC Entry
Stage  8.  Blank Bin Inward Entry
Stage  9.  Add On Work Planning     [generates Lot # + Job Cards]
Stage 10.  Blank Bin Issue          [assigns bins to Job Cards]
Stage 11.  Inspection Entry         [Line + Patrol + Lot variants per Job Card]
Stage 12.  Moulding Production Entry [TERMINAL — consumes everything above]
```

## Stage-by-stage mapping table

| # | Stage | Legacy doctype | Console doctype | Ops native doctype(s) | Ops handler |
|---|---|---|---|---|---|
| 1 | Master Batch Mixing | `Delivery Challan Receipt` (`inward_material_type="Master Batch"`) | `Console Master Batch Mixing` (`MBM-`) | `Stock Entry` (Manufacture) + `Work Order` + `Job Card` + `Batch` | Generic TransactionEngine |
| 2 | Final Batch Mixing | `Delivery Challan Receipt` (`inward_material_type="Compound"`) | `Console Final Batch Mixing` (`FBM-`) | Same as MB Mixing | Generic TransactionEngine |
| 3 | Compound Inspection | `Compound Inspection` | `Console Inspection` (Phase 3 unified) | `Stock Entry` (Material Transfer — only if Accepted) | Generic TransactionEngine |
| 3a | Compound Deviation | `Compound Inspection` (overlay, same doctype) | `Console Compound Deviation` (legacy) / `Console Inspection` (Phase 3) | `Stock Entry` (status-conditional: Material Transfer if Accepted; Material Issue if Rejected; none if Rework) | Generic TransactionEngine |
| 4 | Sheeting Process | `Material Transfer` (custom legacy doctype) + auto-created Stock Entry | `Console Sheeting Process` (`CSHT-`) + Item Clip Mapping rows | `Stock Entry` (Material Transfer) | Generic TransactionEngine |
| 5 | Cut Bit Transfer | `Cut Bit Transfer` (custom legacy) + auto Stock Entry | `Console Cut Bit Transfer` (`CBT-`) + Bin Mapping updates | `Stock Entry` (Repack) with `use_serial_batch_fields=1` | **Dedicated** `submit_cut_bit_transfer(context, run_legacy_sync=False)` |
| 6 | Bulk Clip Release | `Bulk Clip Release` (custom legacy) | `Console Bulk Clip Release` (`CBCR-`) | (none direct — clip state update) | **Dedicated** `bulk_release_clips(barcodes=[...])` |
| 7 | Blanking DC Entry | `Blanking DC Entry` (custom legacy) | `Console Blanking DC Entry` (`CBDE-`) | `Stock Entry` + `Asset Movement` (Receive Bin) | **Dedicated** `submit_blanking_dc_entry(context)` |
| 8 | Blank Bin Inward Entry | `Blank Bin Inward Entry` (custom legacy) | `Console Blank Bin Inward Entry` (not yet shipped) | `Asset Movement` (Receive Bin at Moulding Unit) — OR — `Stock Entry` (Repack to Cut Bit warehouse) | Likely dedicated handler |
| 9 | Add On Work Planning | `Add On Work Planning` (custom legacy) | `Console Add On Work Planning` (not yet shipped) | `Work Order` + `Job Card` (multiple) | Generic TransactionEngine via `create_planning_with_jobcards` whitelisted method |
| 10 | Blank Bin Issue | `Blank Bin Issue` (custom legacy) | `Console Blank Bin Issue` (not yet shipped) | Link bins to Job Card (no direct Stock Entry — bin assignment) | Generic TransactionEngine |
| 11 | Inspection Entry | `Inspection Entry` (custom legacy, polymorphic with `inspection_type`) | `Console Inspection Entry` (not yet shipped) OR folded into `Console Inspection` | (no direct SE at inspection time; rejection SEs deferred until MPE) | Generic TransactionEngine |
| 12 | Moulding Production Entry | `Moulding Production Entry` (custom legacy) | `Console Moulding Production Entry` (`CMPE-`, not yet shipped) | `Stock Entry` (Manufacture) + `Job Card` update + cascade rejection SEs | Generic TransactionEngine with `submit_inspection_stock_entries_from_moulding` whitelisted method |

## Cross-stage references

### Recycling loop

```
Stage 4 (Sheeting) → produces cut-bit batches with Cutbit_<item_code> prefix
                          ↓
                   Stage 5 (Cut Bit Transfer) consolidates them into Cutbit warehouse
                          ↓
                   Stage 2 (Final Batch Mixing) consumes them as raw input
```

### Inspection prerequisite chain

```
Stage 9  (Work Planning) → generates Lot #
                                ↓
Stage 11 (Inspection Entry — Line / Patrol / Lot) → references Lot #
                                ↓
Stage 12 (MPE) → BLOCKS if Line + Patrol inspections missing for the Lot
```

### Batch number cascade

```
Stage 12 (MPE) → generates final batch_no (T-LOT-YYYYMMDD-NNN-NNN)
                       ↓
                Propagated back to all Inspection Entries for the lot
                       ↓
                Cascading rejection SEs become eligible to submit on legacy + ops
```

## Process status against the porting program

| # | Stage | Wave | Implementation status (as of cockpit init) |
|---|---|---|---|
| 1 | MB Mixing | Wave 1 | ✅ Shipped to staging (2026-05-01) |
| 2 | FB Mixing | Wave 1 | ✅ Shipped to staging |
| 3 | Compound Inspection | Phase 1-4 | ✅ Shipped to staging (Phase 3 unified) |
| 3a | Compound Deviation | Phase 1-4 | ✅ Shipped; saga-resolved 2026-05-01 |
| 4 | Sheeting | Wave 1 | ✅ Shipped to staging |
| 5 | Cut Bit Transfer | Wave 1 + Wave 1.5 hardening | ✅ Shipped + dedicated Ops handler |
| 6 | Bulk Clip Release | Wave 2 | ⏳ In progress |
| 7 | Blanking DC Entry | Wave 2 | ⏳ In progress |
| 8 | Blank Bin Inward Entry | Wave 2 | ❌ Not yet shipped |
| 9 | Add On Work Planning | Wave 3 | ❌ Not yet shipped |
| 10 | Blank Bin Issue | Wave 3 | ❌ Not yet shipped |
| 11 | Inspection Entry | Wave 4 | ❌ Not yet shipped (may fold into Phase 3 Console Inspection) |
| 12 | Moulding Production Entry | Wave 5 | ❌ Not yet shipped (terminal stage) |

Program completion = all 13 stages at ✅ Shipped.

## Cross-stage identity conventions

| Concept | Format | Origin | Used by stages |
|---|---|---|---|
| Console transaction reference | `reference_id` = 13-digit `Date.now()` ms | Console Dash | All 13 stages |
| Mix barcode (raw compound) | `C_YYMMDDXn` (Console-authored) | Mixing (Stages 1–2) | Stages 1–4 (consumed downstream) |
| Sheeting auto-numbered output | `C_YYMMDDXn-N` for clips; `Cutbit_C_YYMMDDXn-N` for cut-bits | Sheeting (Stage 4) | Stages 4–7 |
| Cut Bit consolidated batch | `Cutbit_<item_code>` (Stage 5 output) | Cut Bit Transfer (Stage 5) | Stage 2 (recycling input) |
| Cut Bit mix barcode | `CB_<item_code>` | Cut Bit Transfer | Stage 5 SE FG row |
| Lot # | `LOT-YYYYMMDD-NNN` (planned, Console-authored Pattern A) | Work Planning (Stage 9) | Stages 9–12 |
| Job Card identifier | Legacy auto-generated `MFG-JC-YYYY-NNNNN` | Work Planning's `create_planning_with_jobcards` | Stages 9–12 |
| Production batch (FG from MPE) | `T-<lot_no>-<seq>` (e.g. `T-LOT-20260315-001-001`) | MPE (Stage 12) | Stages 11–12; downstream Deflashing/Packing (out of program) |

## Downstream out-of-program stages

The porting program ends at MPE (Stage 12). The following stages exist on Legacy and may be ported in a future program:

- Deflashing
- Receive Deflashing
- Sub Lot Creation
- Lot Resource Tagging
- Packing
- Dispatch

These remain on Legacy Desk for now. The MPE handoff to Deflashing happens via batch_no + FG warehouse state; no Console intervention needed.

## How to use this file

- **Onboarding a new engineer:** show them this file; they understand the program scope in one read
- **Planning a new wave:** identify which stages are still ❌ and prioritise
- **Reviewing a PR:** check if the change crosses stage boundaries (a Stage 4 change that touches Stage 1's batch convention is a red flag)
- **Designing a new feature:** verify it doesn't introduce a stage not in this table — that would be scope creep
