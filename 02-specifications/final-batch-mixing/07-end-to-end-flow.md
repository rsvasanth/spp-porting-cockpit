# 07 — End-to-end flow

> Refer to [`../master-batch-mixing/07-end-to-end-flow.md`](../master-batch-mixing/07-end-to-end-flow.md)
> for the full sequence diagram + race-condition narrative. The FB flow
> differs in only two ways:
>
> 1. **Pre-requisite step:** before FB submission, an MB lot must already
>    exist on both Ops + Legacy with matching `mix_barcode`. Operators
>    scan this MB lot first.
> 2. **Legacy DCR.on_submit path:** for FB, `validate_final_batches`
>    returns True → `create_wo` is invoked → `create_wo_final_batch_mixing`
>    creates the Work Order + Job Card + Manufacturing Stock Entry inline.
>    For MB, this path is skipped.

## What differs in the trace

### Pre-condition

Before the FB submission narrative begins, the operator must:

1. Have a Master Batch lot in stock (created via a previous MB Mixing
   submission, with `sync_status=Success` on both Ops + Legacy)
2. Have the MB's `mix_barcode` printed on a label scannable from the
   Compound mixing area
3. Have additional raw materials from the BOM in stock

### Dash flow delta

After operator scans badge and selects produced Compound item:

```
... select Produced Compound ...
   │
   ▼
Scan Master Batch (FB-only step)
   ├─► handleMasterBatchScan(barcode)
   ├─► validate_rm_barcode({barcode, expected_item_group: "Master Batch"})
   ├─► batch_info appended as scannedItems[0]
   │    + setScannedMasterBatch(batch_info)
   ▼
Scan each raw material (same as MB Mixing)
   ▼
Enter Produced Qty + Submit
```

### Legacy `on_submit` delta

For FB DCR (`inward_material_type="Compound"`):

```
Bridge: legacy_doc.submit()
   ▼
DCR.on_submit fires
   ├─► validate_final_batches(self)
   │   ├─► is_compound = True
   │   ├─► dc_items has is_batch_item=1? (yes for batched FB)
   │   ├─► [batched path]
   │   │   ├─► create_master_batch_stock(self, mb_grouped_item)
   │   │   │   ├─► Creates SE for MB input consumption
   │   │   │   └─► Returns Success
   │   │   └─► create_compound_stock(self, compound_grouped_item)
   │   │       ├─► Creates SE + WO for Compound production
   │   │       └─► Returns Success
   │   └─► returns False (handled inline)
   │   OR
   │   ├─► [non-batched path]
   │   │   ├─► multi-BOM validation passes
   │   │   └─► returns True
   ├─► if returns True: create_wo(self) runs
   │   └─► iterates dc_items, calls create_wo_final_batch_mixing for each
   │       ├─► validate_bom_items_c verifies BOM matches dc_items
   │       ├─► Multi-BOM rejection (defensive)
   │       ├─► Resolves workstation from Mixing Operation master data
   │       ├─► Creates Work Order (docstatus=1)
   │       ├─► update_job_cards (auto-creates JCs via Frappe lifecycle)
   │       └─► make_stock_entry_final_batch
   │           ├─► Builds SE.items with consumed rows + FG row
   │           ├─► FG row has mix_barcode = mt_doc.bridge_mix_barcode (Console's)
   │           ├─► SE.docstatus = 1 (auto-submit)
   │           └─► update_stock_ref appends SE.name to DCR.stock_entry_reference
   ├─► update_over_all_dn_status(self, "Not Hold")
   └─► self.reload()
```

### Failure recovery delta

If `create_wo_final_batch_mixing` returns Failed mid-flight:

```
└─► rollback_wo_se_jc(self, message)
    ├─► Walks hld_items and dc_items
    ├─► For each linked work_order_ref: deletes SE, JCs, WO
    ├─► Resets is_received=0 on linked DN Items
    ├─► Sets DCR docstatus = 0 (back to Draft)
    └─► frappe.msgprint(msg) — surfaces error
```

The Bridge sees Failed; Console's `apply_bridge_result` records Legacy
leg as Failed. Operator can retry from Dash — the second call to
`sync_process_transaction` re-reads the (now-Draft) DCR via idempotency
check and either re-runs the chain or rolls forward.

## Final state for one successful FB submission

In addition to the documents from MB's final state, the FB flow produces:

| System | Document | State |
|---|---|---|
| Console | `Console Final Batch Mixing FBM-2026-...` | `docstatus=1`, `sync_status=Success`, both legs Synced |
| Console | `Console Master Batch Mixing` (the input MB) | Untouched — was already submitted from previous submission |
| Legacy | `Delivery Challan Receipt` (FB, `inward_material_type=Compound`) | `docstatus=1`, `stock_entry_reference` populated |
| Legacy | `Work Order` (production_item=Compound) | `docstatus=1`, `qty=actual_weight` |
| Legacy | `Job Card(s)` | Created and updated with `actual_weight` |
| Legacy | `Stock Entry` (Manufacture, FG=Compound) | `docstatus=1`, FG row has `mix_barcode` from Console |
| Legacy | Original MB SE | Unchanged (the MB is consumed via Stock Ledger only, not via the FB SE) |
| Ops | `Shree Polymer MES Log` | `status=Success` |
| Ops | `Work Order`, `Job Card`, `Stock Entry` | Same set as MB but for the Compound |

## Race window narrative

Same as MB — Ops + Legacy run in parallel via `Promise.all`. The 5-step
atomic dance in `Console Final Batch Mixing.apply_bridge_result` is
**byte-identical** to MB's. Whichever leg finishes second triggers the
auto-submit on the Console doc.

The only material difference: the Legacy leg for FB is **slower** than
for MB (because `create_wo_final_batch_mixing` creates 3-4 documents
inline). Empirically the Legacy leg takes 5-12 seconds vs MB's 2-5
seconds. The Promise.all timeout (120s) is far above this so it's not a
concern, but the race window is **larger** for FB — more likely that Ops
finishes first and writes `Partial` before Legacy promotes to `Success`.
