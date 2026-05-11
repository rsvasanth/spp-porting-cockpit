# 05 — Legacy ERPNext (v15) — the FB-specific code path

**This is the most important file in this spec.** Unlike MB Mixing, where
the SE-creation chain on legacy isn't fully traced, FB Mixing's legacy
path **is** fully traced and runs on every FB submission. This file is
authoritative for what happens on `sppmaster.frappe.cloud` when the
Bridge submits an FB DCR.

## Entry point

`DeliveryChallanReceipt.on_submit` (`delivery_challan_receipt.py:14`):

```python
def on_submit(self):
    fb_mix = validate_final_batches(self)
    if fb_mix:
        wo, message = create_wo(self)
        if wo:
            update_over_all_dn_status(self, "Not Hold")
        else:
            frappe.throw(message or "Work Order creation failed..!")
    self.reload()
```

For an FB DCR (`inward_material_type == "Compound"`):
- `validate_final_batches(self)` returns **True** (most cases) or **False** (when batched FB) — see branching below
- If True → `create_wo(self)` is called, which dispatches to FB-specific helpers
- If False → fully handled inside `validate_final_batches` (it directly calls `create_master_batch_stock` + `create_compound_stock` for the batched variant)

## `validate_final_batches(self)` — the branching logic

`delivery_challan_receipt.py:146`:

```python
def validate_final_batches(self):
    if self.inward_material_type == "Compound":
        batch_item_found = False
        for k in self.dc_items:
            if k.is_batch_item:
                batch_item_found = True
        if batch_item_found:
            # ── BATCHED FB PATH ──────────────────────────────────────
            # When dc_items contains a row with is_batch_item=1, this means
            # the FB is consuming a pre-made MB. Need to create TWO stock
            # entries: one for the MB input (master batch stock) and one
            # for the Compound output.
            grouped_items = frappe.db.sql(""" SELECT * FROM `tabDC Item`
                WHERE parent = %(rc_id)s
                GROUP BY item_to_manufacture, operation """,
                {"rc_id": self.name}, as_dict=1)
            if len(grouped_items) == 2:
                # Process MB side
                for x in grouped_items:
                    if x.operation != "Batching":
                        if x.is_batch_item:
                            wo, message = create_master_batch_stock(self, x)
                            if not wo:
                                rollback_wo_se_jc(self, message)
                                return False
                            break
                # Process Compound side
                for x in grouped_items:
                    if x.operation != "Batching":
                        if not x.is_batch_item:
                            wo, message = create_compound_stock(self, x)
                            if not wo:
                                rollback_wo_se_jc(self, message)
                                return False
                            break
            else:
                rollback_wo_se_jc(self, "You can receive only one Batch & Final Batch Mixing at a time.")
            return False    # batched path handles everything inline; signals on_submit to skip create_wo
        else:
            # ── NON-BATCHED FB PATH ──────────────────────────────────
            # Standard FB Mixing without a pre-made MB input.
            grouped_items = frappe.db.sql(""" SELECT * FROM `tabDC Item`
                WHERE parent = %(rc_id)s
                GROUP BY item_to_manufacture, operation """,
                {"rc_id": self.name}, as_dict=1)
            if len(grouped_items) == 1:
                for x in grouped_items:
                    # Multi-BOM validation: legacy rejects items with >1 active BOM
                    bom_items = frappe.db.sql(""" SELECT BI.item_code FROM `tabBOM Item` BI
                        INNER JOIN `tabBOM` B ON BI.parent = B.name
                        WHERE B.item = %(item_code)s AND B.is_default=1 AND B.is_active=1 """,
                        {"item_code": x.item_to_manufacture}, as_dict=1)
                    if len(bom_items) > 1:
                        # BOM has multiple input items → DCR must also have multiple matching rows
                        manf_items = frappe.db.sql(""" SELECT item_to_manufacture, operation FROM `tabDC Item`
                            WHERE parent = %(rc_id)s AND item_to_manufacture = %(item_to_manufacture)s """,
                            {"rc_id": self.name, "item_to_manufacture": x.item_to_manufacture}, as_dict=1)
                        if not len(manf_items) == len(bom_items):
                            rollback_wo_se_jc(self, "You can receive only one Master Batch & Final Batch Mixing at a time.")
                            return False
                return True   # signals on_submit to call create_wo
            else:
                rollback_wo_se_jc(self, "You can receive only one Master Batch & Final Batch Mixing at a time.")
                return False
    else:
        # Not a Compound DCR (e.g. Master Batch DCR) — skip the FB logic entirely
        return True
```

**Three FB sub-branches summary:**

| Branch | Trigger | What runs | Returns |
|---|---|---|---|
| Batched FB (with MB input) | `inward_material_type=="Compound"` AND `dc_items` has `is_batch_item=1` row | `create_master_batch_stock` then `create_compound_stock` inline | `False` (on_submit doesn't call create_wo) |
| Non-batched FB | `inward_material_type=="Compound"` AND no `is_batch_item=1` | Multi-BOM validation only | `True` (on_submit calls `create_wo`) |
| Not FB (e.g. MB DCR) | `inward_material_type != "Compound"` | Nothing | `True` (on_submit calls `create_wo` — but this is the wrong branch for MB; relies on the MB DCR not having a single grouped_item that matches the FB shape) |

## `create_wo_final_batch_mixing(child_name, mt_doc, item_code, operation)`

`delivery_challan_receipt.py:626`. Called by `create_wo` (line 413) when
processing each DC Item for the non-batched FB path. Builds a Work Order
+ Stock Entry.

```python
def create_wo_final_batch_mixing(child_name, mt_doc, item_code, operation):
    try:
        bom_resp, fn_resp, msg = validate_bom_items(mt_doc, item_code)
        if not fn_resp:
            if bom_resp:
                spp_settings = frappe.get_single("SPP Settings")
                dc_items = frappe.db.sql(...filtered by item_to_manufacture..., as_dict=1)
                bom = frappe.db.sql(""" SELECT B.name, B.item FROM `tabBOM Item` BI
                    INNER JOIN `tabBOM` B ON BI.parent = B.name
                    WHERE B.item = %(item_code)s AND B.is_active=1 """,
                    {"item_code": item_code}, as_dict=1)
                if bom:
                    # Multi-BOM rejection (defensive)
                    bom__ = frappe.db.sql(""" SELECT B.name FROM `tabBOM` B
                        WHERE B.item = %(bom_item)s AND B.is_Active=1 """,
                        {"bom_item": bom[0].item}, as_dict=1)
                    if len(bom__) > 1:
                        return {"status": "Failed",
                                "message": f"Multiple BOM's found for Item to Produce - {bom[0].item}."}

                    # Compute total qty (sum of consumed items)
                    actual_weight = sum(flt(e_item.qty) for e_item in dc_items)

                    # Resolve workstation from Mixing Operation master data
                    work_station = "Two Roll Mixing Mill"   # default
                    w_stations = frappe.db.get_all("Mixing Operation",
                        filters={"warehouse": mt_doc.source_warehouse},
                        fields=['operation', 'workstation'])
                    if w_stations:
                        work_station = w_stations[0].workstation
                        operation    = w_stations[0].operation

                    # Build Work Order
                    import time
                    wo = frappe.new_doc("Work Order")
                    wo.naming_series   = "MFG-WO-.YYYY.-"
                    wo.company         = "SPP"
                    wo.fg_warehouse    = spp_settings.target_warehouse
                    wo.source_warehouse = mt_doc.source_warehouse
                    wo.wip_warehouse   = spp_settings.wip_warehouse
                    wo.bom_no          = bom[0].name
                    wo.use_multi_level_bom = 0
                    wo.skip_transfer   = 1
                    wo.transfer_material_against = "Work Order"
                    wo.append("operations", {
                        "operation":   operation,
                        "bom":         bom[0].name,
                        "workstation": work_station,
                        "time_in_mins": 20,
                    })
                    wo.referenceid     = round(time.time() * 1000)
                    wo.production_item = bom[0].item
                    wo.qty             = actual_weight
                    wo.planned_start_date = getdate()
                    wo.docstatus       = 1   # auto-submit the WO
                    wo.save(ignore_permissions=True)

                    # Update DCR child + create Job Cards + Stock Entry
                    update_workorder_ref(wo.name, "DC Item", child_name)
                    update_job_cards(wo.name, actual_weight, spp_settings.employee, spp_settings)
                    se = make_stock_entry_final_batch(mt_doc, item_code, spp_settings, wo.name, "Manufacture")
                    return se
            else:
                return {"status": "Failed", "message": "BOM is not matched with items"}
    except Exception:
        frappe.log_error(...)
        return {"status": "Failed", "message": "Work Order or Job Card update failed..!"}
```

**Key behaviors:**

| Behavior | Detail |
|---|---|
| Auto-submits WO on `wo.docstatus = 1` before save | Standard ERPNext pattern; bypasses normal lifecycle |
| Workstation auto-resolved from `Mixing Operation` master data | Console payload's `workstation` is ignored if `Mixing Operation` has a row for this `source_warehouse` |
| `time_in_mins: 20` hardcoded | Every FB Work Order is planned at 20 minutes regardless of actual mixing time |
| `wo.referenceid = round(time.time() * 1000)` | Uses Python's time, NOT the Console-provided `reference_id`. This is a **divergence point** — the Console-side reference_id is lost on the Work Order |
| `update_job_cards(wo.name, actual_weight, ...)` | Auto-creates Job Cards via Frappe's WO lifecycle, then updates them with `actual_weight` |
| `make_stock_entry_final_batch(...)` | Creates the Manufacturing Stock Entry — see below |
| Multi-BOM rejection | If `>1` active BOMs exist for the produced item, refuses to proceed |
| `validate_bom_items` checks every BOM input is in `dc_items` | Stricter than MB's path |

## `make_stock_entry_final_batch(mt_doc, item_code, spp_settings, work_order_id, purpose)`

`delivery_challan_receipt.py:722` (full body not shown; ~130 lines). Creates the Manufacturing Stock Entry:

```python
def make_stock_entry_final_batch(mt_doc, item_code, spp_settings, work_order_id, purpose):
    try:
        st_items = frappe.db.sql("""
            SELECT * FROM `tabDC Item`
            WHERE parent=%(parent_doc)s AND item_to_manufacture=%(item_code)s """,
            {"parent_doc": mt_doc.name, "item_code": item_code}, as_dict=1)

        # Build Stock Entry doc
        se = frappe.new_doc("Stock Entry")
        se.purpose         = purpose                # "Manufacture"
        se.work_order      = work_order_id
        se.from_bom        = 1
        se.fg_completed_qty = sum(flt(i.qty) for i in st_items)
        se.bom_no          = ...    # from WO

        # Append raw material rows (consumed items)
        for x in st_items:
            se.append("items", {
                "item_code": x.item_code, "qty": x.qty,
                "batch_no": x.batch_no, "mix_barcode": x.scan_barcode,
                "spp_batch_number": x.spp_batch_no,
                "s_warehouse": mt_doc.source_warehouse,
                "is_finished_item": 0,
                "allow_zero_valuation_rate": 1,
            })

        # Append finished good row
        se.append("items", {
            "item_code": item_code, "qty": se.fg_completed_qty,
            "t_warehouse": spp_settings.target_warehouse,
            "is_finished_item": 1,
            "mix_barcode": mt_doc.bridge_mix_barcode,    # ← Console-generated barcode honored here
            "spp_batch_number": mt_doc.bridge_mix_barcode,
            "allow_zero_valuation_rate": 1,
        })

        se.docstatus = 1
        se.save(ignore_permissions=True)
        update_stock_ref(mt_doc.name, se.name)   # appends SE.name to DCR.stock_entry_reference
        return {"status": "Success", "se_name": se.name}
    except Exception:
        frappe.log_error(...)
        return {"status": "Failed", "message": str(e)}
```

**Critical: `mt_doc.bridge_mix_barcode` (Console-generated) is honored on
the FG row.** This is where the round-trip identity holds:

```
Console mix_barcode → Bridge → legacy DCR.bridge_mix_barcode
   → legacy SE.items[FG].mix_barcode
   → downstream Compound Inspection looks it up via the 6-strategy chain
```

If FB's `bridge_mix_barcode` is empty (Console payload missed it), legacy
falls back to `generate_barcode(compound)` at line 1060 — producing a
**different** barcode than Console expected. The downstream Compound
Inspection 6-strategy lookup will likely still find the SE via the
strategies that don't require Console's barcode, but the round-trip
identity is broken.

## Documents created on legacy for one FB submission

| Document | Created by | When |
|---|---|---|
| `Delivery Challan Receipt` (FB, `inward_material_type=Compound`) | Bridge `sync_process_transaction` | First step |
| `Work Order` (production_item = Compound) | `create_wo_final_batch_mixing` line 652 | Inside DCR.on_submit |
| `Job Card` (against the WO) | `update_job_cards` (calls Frappe's WO lifecycle) | Inside DCR.on_submit |
| `Stock Entry` (purpose = Manufacture, has FG row with mix_barcode) | `make_stock_entry_final_batch` | Inside DCR.on_submit |
| `Stock Ledger Entry` × N | Auto by Frappe on SE submit | Same transaction |
| `Batch` (for FG) | Auto by Frappe if FG has `has_batch_no=1` | Same |

## Documents NOT created for non-batched FB

- No `Master Batch Stock Entry` — only created in the **batched** FB
  branch via `create_master_batch_stock`. If the operator scans an MB
  input but `is_batch_item=0` was not set on the row, the non-batched
  path runs and the MB input is just treated as a regular consumed item.

## Failure recovery — `rollback_wo_se_jc(info, msg)`

`delivery_challan_receipt.py:74`. If `validate_final_batches` or
`create_wo_final_batch_mixing` fails, this function:

1. Looks up `work_order_ref` on `hld_items` + `dc_items`
2. For each, deletes the SE, the Job Cards, then the Work Order
3. Resets `is_received=0` on linked Delivery Note Items
4. Sets the DCR's `docstatus = 0` (back to draft)
5. Calls `frappe.msgprint(msg)` to surface the error

**This is destructive cleanup.** If the Bridge sees a Failed response from
an FB DCR submission, the DCR + WO + JC + SE may already be partially
created and then rolled back via this function. Idempotent retry from
Bridge works because:
- The DCR was reset to Draft (or never submitted — Bridge would have
  caught the exception before commit)
- Or the DCR was rolled back fully and re-running `sync_process_transaction`
  treats the reference_id as new

## Stock-side semantics

After FB submit:
- **Source warehouse** (DCR.source_warehouse): debited the consumed raw
  materials + MB input (in batched case)
- **WIP warehouse** (SPP Settings.wip_warehouse): briefly used during
  transfer; cleared by SE submit
- **Target warehouse** (SPP Settings.target_warehouse): credited the FG
  Compound qty
- Stock Ledger Entry rows: one per item per warehouse change
- `Item Batch Stock Balance` row: created/updated for FG's new batch

## What Hermes workers must NOT touch on legacy

- `validate_final_batches` branching — affects every Compound DCR
- `create_wo_final_batch_mixing` — production code, complex error handling
- `make_stock_entry_final_batch` — also called by other flows
- `rollback_wo_se_jc` — used by both FB and other DCR rollbacks
- `Mixing Operation` master data — drives workstation auto-resolution
- `SPP Settings` Single — global config used by SE creation

If a change to FB legacy behavior is needed, the right escalation path is:
1. Surface in `10-risks-and-decisions.md`
2. Propose the change on the legacy bench (`spp15.local`), not via Bridge
3. Get explicit go-ahead from production overseer
4. Coordinate with Final Batch shop-floor team — operational impact is high
