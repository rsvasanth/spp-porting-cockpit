# 01 — Business context

## What Moulding Production Entry is (shop floor)

Moulding Production Entry (MPE) is the **terminal production booking** in the
shop-floor chain. An operator at a moulding press:

1. Scans the finished-goods lot barcode (produced by [Inspection Entry](../inspection-entry/)
   Line + Patrol inspections passing the lot)
2. The system resolves the lot to an open `Job Card` with operation `Moulding`
3. The operator enters produced weight, balance bin weights (if any), and
   production parameters (lifts, running cavities, curing time)
4. The system validates the chain — lot inspection prerequisites, open BBI
   bins, active bin mappings, stock availability, and production tolerance
5. On submit, the system creates and submits a Manufacturing Stock Entry,
   completes the Job Card and Work Order, updates inspection entries with
   the produced batch, and closes consumed bin rows

**MPE is the last link in the chain.** Without a successful MPE:
- No finished-goods batch is created
- No compound is booked into finished-goods inventory
- Job Card and Work Order remain open
- Downstream finished-goods flows (dispatch, sale) are blocked

## Why this is the terminal link in the chain

The full shop-floor production chain ending at MPE:

```
Master Batch Mixing → Compound Inspection → Final Batch Mixing
  → Sheeting → Cut Bit Transfer → Bulk Clip Release → Blanking
  → Blank Bin Inward → Work Planning → Blank Bin Issue
  → Inspection Entry (Line/Patrol) → Moulding Production Entry
```

Each upstream record feeds the next. MPE is terminal because:
- It consumes the last physical material (compound in bins issued via BBI)
- It produces the finished-goods batch (the traceability anchor for dispatch)
- It completes the production operations that upstream planning initiated
- It cascades batch information back to inspection rejection entries

## What success looks like for the operator

1. Operator scans lot barcode → lot validated against open Job Card
2. Operator sees mould reference, compound, running cavities from Job Card
3. Operator scans balance bins (if any) and enters produced weight
4. System validates all chains (inspections, bins, tolerance, stock) in real time
5. Operator hits **SUBMIT TO ERP**
6. System creates + submits Manufacture Stock Entry, completes Job Card/Work Order
7. Operator sees the generated batch number (from the `generate_batch_no` contract)
8. Operator sees bin closure updates and inspection cascade confirmation

## What success looks like upstream (Console / ops / legacy)

1. `Console Moulding Production Entry` row exists with `sync_status = "Success"`
   and `docstatus = 1`
2. `Console Transaction Log` has two entries (Legacy + Ops), both `Status = "Success"`
3. Legacy bench has `Moulding Production Entry` submitted with `stock_entry_reference`
   pointing to the manufacturing Stock Entry
4. Ops bench has the corresponding `Stock Entry` (Manufacture) with FG batch and
   consumed compound lines
5. Job Card status = `Completed`, docstatus = 1
6. Work Order status = `Completed`
7. `Blank Bin Issue Item` rows consumed by this MPE have `is_completed = 1`
8. `Item Bin Mapping` rows for consumed bins are retired or updated
9. Line + Patrol `Inspection Entry` rows have `batch_no` and `spp_batch_number`
   updated from the produced batch

## Why MPE is Wave 2, not Wave 1

MPE depends on:
- [Blank Bin Issue](../blank-bin-issue/) — supplies the open bin rows MPE consumes
- [Inspection Entry](../inspection-entry/) — supplies Line + Patrol inspections MPE validates
- Both `blank_bin_issue_item_name` and `item_bin_mapping_name` references in `update_bins`
  require BBI to be already shipped
- The `stock_entry_reference` linking MPE to its manufacturing SE requires the SE
  creation chain to be working on both Legacy and Ops

Shipping MPE first (without BBI and IE) would require mock data that can't be
validated against real shop-floor conditions.

## What makes MPE complex relative to upstream entries

Unlike Mixing (Wave 1) which has a clean two-leg sync with independent stock
entries on each bench, MPE:

1. **Cascades to multiple systems in one submit:** Job Card + Work Order on
   Legacy ERPNext, Stock Entry on both benches, Inspection Entry updates on
   Legacy — all in one `on_submit` call
2. **Has inspection prerequisites:** cannot run without submitted Line + Patrol
   records (cross-doctype dependency, not self-contained)
3. **Has active bin state:** BBI bins must be active (not retired/released) at
   submit time — a runtime state check, not a data shape check
4. **Has a rollback mechanism:** `rollback_entries()` tears back everything on
   failure — Stock Entry cancel, Job Card reset, Work Order reset, batch delete
5. **Has injection vs compression moulding variants:** injection adds
   `purged_compound` + `compound_leakage` to output weight and requires special
   treatment of scrap warehouse
6. **Has shell consumption:** when BOM includes Shell item group, MPE deducts
   shell weight from output and transfers shell from Unit-2 warehouse

## Who interacts with this process

| Role | What they do |
|---|---|
| Moulding Operator | Runs the Dash submission, scans bins, enters weight |
| Quality Inspector | (Indirect) — Inspection Entry must exist before MPE can run |
| Quality Manager | (Indirect) — Reviews rejections that affect line rejection qty |
| System Manager | Backdates posting time; handles recovery on rollback |
| Shop Floor Supervisor | Monitors open Job Cards; resolves bin/blocking issues |

## Live data on `spp15.local`

| Metric | Value |
|---|---|
| Total MPE records | 30,006 |
| Submitted | 28,931 (96.3%) |
| Draft / Cancelled | ~1,075 |
| Injection moulding records | 613 (2.0%) |
| Non-injection (compression) | 29,393 (97.8%) |
| Dominant downtime reason codes | `PLANNING`, `COMPOUND SHORTAGE`, `OPERATOR ISSUE`, `COMPOUND ISSUE`, `MLD CHANGE` |
| Records with no reason code | Majority (normal production without deviation) |