# 05 — Legacy ERPNext (v15) — `Inspection Entry`

**App:** `apps/shree_polymer_custom_app` (legacy custom app on ERPNext v15)
**Doctype path:** `shree_polymer_custom_app/.../doctype/inspection_entry/`
**Bench:** `spp15.local` ↔ `sppmaster.frappe.cloud`
**Controller size:** 1534 lines (`inspection_entry.py`)
**JSON size:** 437 lines (`inspection_entry.json`)

## What Inspection Entry is on legacy

`Inspection Entry` is a **polymorphic** quality record with 6 distinct
inspection type branches. It is a submittable DocType (`is_submittable: 1`)
with `INSP-.#####` autoname. It creates Stock Entries for rejected material
and participates in the MPE batch cascade.

## Controller — `inspection_entry.py`

### `validate()` — type-aware validation

```python
def validate(self):
    # Future posting date blocked
    if getdate(self.posting_date) > getdate():
        frappe.throw("The <b>Posting Date</b> can't be greater than <b>Today Date</b>..!")
    
    # Lot required
    if not self.lot_no:
        frappe.throw("Could not find the <b>Lot No</b>, Please scan the lot.")
    
    # Inspector required
    if not self.inspector_code:
        frappe.throw("Could not find the <b>Inspector Id</b>, Please scan the Inspector.")
    
    # Items child table required
    if not self.items:
        frappe.throw("Please add some items before save..!")
    
    # Duplicate prevention (all except Final Visual)
    if self.lot_no and not self.inspection_type == "Final Visual Inspection":
        check_exist = frappe.db.get_all("Inspection Entry",
            filters={"name": ("!=", self.name), "docstatus": 1,
                     "lot_no": self.lot_no, "inspection_type": self.inspection_type})
        if check_exist:
            frappe.throw(f"Inspection Entry for lot <b>{self.lot_no}</b> already exists..!")
    
    # Type-specific qty validation
    if self.inspection_type in ("Lot Inspection", "Line Inspection", "Patrol Inspection"):
        if not int(self.inspected_qty_nos):
            frappe.throw("Total inspected Qty not found..!")
    
    if self.inspection_type in ("Incoming Inspection", "Final Inspection"):
        if not int(self.total_inspected_qty_nos):
            frappe.throw("Total inspected Qty not found..!")
    
    # Final Visual — compute qty after rejection
    if self.inspection_type in ("Final Visual Inspection", "PDIR"):
        if self.inspection_type == "Final Visual Inspection":
            if self.vs_pdir_qty:
                self.vs_pdir_qty_after_rejection = self.total_inspected_qty_nos - (self.total_rejected_qty or 0)
```

**Validation rules by type:**

| Type | Required fields | Duplicate check |
|---|---|---|
| Line / Patrol / Lot | `inspected_qty_nos` | Yes (lot + type) |
| Incoming / Final | `total_inspected_qty_nos` | Yes (lot + type) |
| Final Visual | `total_inspected_qty_nos` | No (BR-IE-001 exempt) |
| Visual | — | — |

### `on_submit()` — 3-branch submission

```python
def on_submit(self):
    if self.inspection_type in ("Lot Inspection", "Line Inspection", "Patrol Inspection"):
        # Branch A: moulding rejection SE
        if self.total_rejected_qty:
            resp_m = make_stock_entry(self)
            if resp_m and resp_m.get('status') == 'failed':
                rollback_entries(self, resp_m.get('message'))
        
        # CRITICAL DRIFT: comment says Patrol included, SQL checks Line + Lot
        exe_insp = frappe.db.sql(f"""
            SELECT name FROM `tabInspection Entry` 
            WHERE (inspection_type = 'Line Inspection' OR inspection_type = 'Lot Inspection') 
            AND docstatus = 1 AND lot_no = '{self.lot_no}'""", as_dict=1)
        
        if exe_insp and len(exe_insp) >= 2:
            submit_inspection_stock_entry_immediately(self)
    
    elif self.inspection_type in ("Incoming Inspection", "Final Inspection"):
        # Branch B: incoming/final rejection SE + deflashing trigger
        if self.total_rejected_qty:
            resp_inc = make_inc_stock_entry(self)
            if resp_inc and resp_inc.get('status') == 'failed':
                rollback_entries(self, resp_inc.get('message'))
        
        if self.inspection_type == "Incoming Inspection":
            submit_deflash_receipt_entry(self)
    
    elif self.inspection_type in ("Final Visual Inspection", "PDIR"):
        # Branch C: VS/PDIR path
        if self.inspection_type == "Final Visual Inspection":
            if self.total_rejected_qty:
                self.submit__vs_pdir()
            else:
                self.submit__vs_pdir_no_rejection()
    
    self.reload()
```

## Branch A — Line / Patrol / Lot

### `make_stock_entry(self)` — rejection Material Transfer

```python
def make_stock_entry(self):
    if flt(self.total_rejected_qty_kg, 3) > 0:
        spp_settings = frappe.get_single("SPP Settings")
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.purpose = "Material Transfer"
        stock_entry.company = "SPP"
        stock_entry.naming_series = "MAT-STE-.YYYY.-"
        naming_status, naming_series = get_stock_entry_naming_series(spp_settings, self.inspection_type)
        if naming_status:
            stock_entry.naming_series = naming_series
        stock_entry.stock_entry_type = "Material Transfer"
        stock_entry.from_warehouse = spp_settings.unit_2_warehouse
        stock_entry.to_warehouse = spp_settings.rejection_warehouse
        stock_entry.append("items", {
            "item_code": self.product_ref_no,
            "s_warehouse": spp_settings.unit_2_warehouse,
            "t_warehouse": spp_settings.rejection_warehouse,
            "stock_uom": "Kg", "uom": "Kg",
            "use_serial_batch_fields": 1,
            "allow_zero_valuation_rate": 1,
            "transfer_qty": flt(self.total_rejected_qty_kg, 3),
            "qty": flt(self.total_rejected_qty_kg, 3),
            "inspection_ref": self.name,
            "source_ref_document": self.doctype,
            "source_ref_id": self.name,
        })
        stock_entry.insert(ignore_permissions=True)
        frappe.db.set_value(self.doctype, self.name, "stock_entry_reference", stock_entry.name)
        return {"status": "success"}
    return {"status": "success"}  # no-op if rejected kg = 0
```

Key fields: `stock_uom = "Kg"`, `transfer_qty = total_rejected_qty_kg`, stores
`stock_entry_reference` on IE. Stock Entry created as Draft (not submitted here).

### `submit_inspection_stock_entry_immediately(self)` — MPE batch cascade

> **This is the most complex function in the file (lines 185–323).**
> It fires when BOTH Line + Lot Inspections are submitted for a lot.
> It receives the MPE produced batch and cascades it to ALL inspection
> Stock Entries (Line + Lot + Patrol) for that lot.

```python
def submit_inspection_stock_entry_immediately(self):
    """Cascade MPE batch to all inspection rejection SEs for this lot."""
    # Step 1: Get Moulding Production Entry for this lot
    mould_prod = frappe.db.get_value("Moulding Production Entry",
        {"scan_lot_number": self.lot_no, "docstatus": 1},
        ["name", "stock_entry_reference"], as_dict=1)
    
    # Step 2: Get batch from MPE's Stock Entry
    target_batch = frappe.db.get_value("Stock Entry Detail", {
        "parent": mould_prod.stock_entry_reference,
        "is_finished_item": 1,
        "t_warehouse": ["is", "set"]
    }, "batch_no")
    
    # Step 3: Find ALL inspection entries for this lot (Line + Lot + Patrol)
    exe_insp = frappe.db.sql(f"""
        SELECT name, stock_entry_reference, inspection_type 
        FROM `tabInspection Entry` 
        WHERE (inspection_type = 'Line Inspection' 
               OR inspection_type = 'Lot Inspection' 
               OR inspection_type = 'Patrol Inspection') 
        AND docstatus = 1 AND lot_no = '{self.lot_no}'""", as_dict=1)
    
    # Step 4: Update batch in Stock Entry Detail AND Inspection Entry for each
    # Step 5: Submit each draft Stock Entry
    for ins in exe_insp:
        if ins.stock_entry_reference:
            # Update batch in SE Detail
            frappe.db.sql(f"""UPDATE `tabStock Entry Detail` SET batch_no = '{target_batch}' 
                             WHERE source_ref_document = 'Inspection Entry' 
                             AND source_ref_id = '{ins.name}'""")
            # Update batch in IE
            frappe.db.sql(f"""UPDATE `tabInspection Entry` 
                             SET batch_no = '{target_batch}', spp_batch_number = '{self.lot_no}' 
                             WHERE name = '{ins.name}'""")
            # Submit the Stock Entry
            ins_stock_entry = frappe.get_doc("Stock Entry", ins.stock_entry_reference)
            for item in ins_stock_entry.items:
                item.use_serial_batch_fields = 1
                if not item.batch_no:
                    item.batch_no = target_batch
            ins_stock_entry.docstatus = 1
            ins_stock_entry.save(ignore_permissions=True)
            submitted_count += 1
```

**Key invariants:**
- Only fires when MPE exists (MPE is the batch source)
- `target_batch` comes from MPE's submitted Stock Entry's finished item row
- Cascades to **Line + Lot + Patrol** (see Drift Finding #1 in `10-risks-and-decisions.md`)
- Updates `batch_no` on both `Stock Entry Detail` and `Inspection Entry` itself
- Stock Entry Detail has `source_ref_document = 'Inspection Entry'` AND `source_ref_id = ins.name`

## Branch B — Incoming / Final

### `make_inc_stock_entry(self)` — incoming rejection Material Transfer

```python
def make_inc_stock_entry(self):
    spp_settings = frappe.get_single("SPP Settings")
    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.purpose = "Material Transfer"
    stock_entry.company = "SPP"
    stock_entry.naming_series = "MAT-STE-.YYYY.-"
    naming_status, naming_series = get_stock_entry_naming_series(spp_settings, self.inspection_type)
    if naming_status:
        stock_entry.naming_series = naming_series
    stock_entry.stock_entry_type = "Material Transfer"
    stock_entry.from_warehouse = spp_settings.unit_2_warehouse
    stock_entry.to_warehouse = spp_settings.rejection_warehouse
    stock_entry.append("items", {
        "item_code": self.product_ref_no,
        "s_warehouse": spp_settings.unit_2_warehouse,
        "t_warehouse": spp_settings.rejection_warehouse,
        "stock_uom": "Nos", "uom": "Nos",
        "use_serial_batch_fields": 1,
        "allow_zero_valuation_rate": 1,
        "spp_batch_number": self.spp_batch_number,
        "transfer_qty": self.total_rejected_qty,
        "qty": self.total_rejected_qty,
        "inspection_ref": self.name,
        "source_ref_document": self.doctype,
        "source_ref_id": self.name,
    })
    stock_entry.insert(ignore_permissions=True)
    frappe.db.set_value(self.doctype, self.name, "stock_entry_reference", stock_entry.name)
    return {"status": "success"}
```

Key differences from Branch A: `stock_uom = "Nos"` (not Kg), `qty = total_rejected_qty`
(nos, not kg), `spp_batch_number` carried (not `batch_no`).

### `submit_deflash_receipt_entry(self)` — trigger Deflashing Receipt

```python
def submit_deflash_receipt_entry(self):
    rept_entry = frappe.db.get_all("Deflashing Receipt Entry",
        {"scan_lot_number": self.lot_no, "docstatus": 1}, ["name"])
    if rept_entry:
        mould__prod = frappe.get_doc("Deflashing Receipt Entry", rept_entry[0].name)
        mould__prod.run_method("manual_on_submit")
    else:
        frappe.throw("There is no <b>Deflashing Receipt Entry</b> found..!")
```

This is the **cross-Doctype trigger** for Incoming Inspection: IE submits
→ looks up the Deflashing Receipt Entry for the same lot → calls its
`manual_on_submit` → which submits the linked Stock Entry.

## Branch C — Final Visual / PDIR

### `submit__vs_pdir()` — rejection path

```python
def submit__vs_pdir(self):
    """Final Visual with rejection: create VS/PDIR SE, Work Order, Job Card, update LRT."""
    psdir = make_vs_pdir_stock_entry(self)   # creates rejection Material Transfer
    if psdir and psdir.get('status') == "success":
        exe_lrt = frappe.db.sql(f"""SELECT name, warehouse, batch_no FROM `tabLot Resource Tagging` 
                                    WHERE scan_lot_no='{self.lot_no}' AND docstatus = 1 LIMIT 1""",
                                as_dict=1)
        if exe_lrt:
            lrt = frappe.get_doc("Lot Resource Tagging", exe_lrt[0].name)
            lrt__resp = lrt.run_method('make_wo_stock_entry')
            if lrt__resp:
                if lrt__resp.get('status') == "success":
                    stock_id = frappe.db.sql(f"""SELECT parent FROM `tabStock Entry Detail` 
                                                 WHERE source_ref_document = 'Inspection Entry' 
                                                 AND source_ref_id = '{self.name}'""", as_dict=1)
                    if stock_id:
                        frappe.db.sql(f"""UPDATE `tabStock Entry` 
                                         SET posting_date = '{self.posting_date}' 
                                         WHERE name = '{stock_id[0].parent}'""")
                        lrt.reload()
                    else:
                        frappe.throw('Stock Entry Reference not found...')
                else:
                    rollback_vs_pdir(self, lrt)
            else:
                frappe.throw('Something went wrong, not able to submit <b>Stock Entry</b>..!')
        else:
            submit_vs_entry__only(self)
    else:
        frappe.throw(psdir.get('message'))
```

### `submit__vs_pdir_no_rejection()` — no-rejection path

```python
def submit__vs_pdir_no_rejection(self):
    """Final Visual without rejection: check stock, update LRT qty, create WO + SE."""
    exe_lrt = frappe.db.sql(f"""SELECT name, warehouse, batch_no FROM `tabLot Resource Tagging` 
                                WHERE scan_lot_no='{self.lot_no}' AND docstatus = 1 LIMIT 1""",
                            as_dict=1)
    if exe_lrt:
        bom = frappe.db.sql("""SELECT B.name, BI.item_code FROM `tabBOM Item` BI 
                               INNER JOIN `tabBOM` B ON BI.parent = B.name 
                               INNER JOIN `tabItem` I ON I.name = BI.item_code 
                               WHERE B.item=%(item_code)s AND B.is_active=1 
                               AND B.is_default=1 AND I.item_group = 'Products'""",
                            {"item_code": self.product_ref_no}, as_dict=1)
        if bom:
            stock_status = check_available_stock(exe_lrt[0].get("warehouse"),
                                                 bom[0].item_code,
                                                 exe_lrt[0].get("batch_no", ""))
            if stock_status.get('status') == "Success":
                update_qty = self.total_inspected_qty_nos
                frappe.db.sql(f"""UPDATE `tabLot Resource Tagging` 
                                 SET qty_after_rejection_nos = {update_qty} 
                                 WHERE scan_lot_no='{self.lot_no}' AND docstatus = 1""")
                lrt = frappe.get_doc("Lot Resource Tagging", exe_lrt[0].name)
                lrt__resp = lrt.run_method('make_wo_stock_entry')
                # ... WO + SE creation with all FG qty (no rejection)
            else:
                frappe.throw(stock_status.get('message'))
        else:
            frappe.throw(f"<b>Active and Default Bom</b> not found for the item...")
    else:
        submit_vs_entry__only(self)
```

### `make_vs_pdir_stock_entry(self)` — VS/PDIR rejection SE

```python
def make_vs_pdir_stock_entry(self):
    """Creates Final Visual/PDIR rejection Material Transfer to pdir_visual_t__warehouse."""
    bom = frappe.db.sql("""SELECT B.name, BI.item_code FROM `tabBOM Item` BI 
                           INNER JOIN `tabBOM` B ON BI.parent = B.name 
                           INNER JOIN `tabItem` I ON I.name = BI.item_code 
                           WHERE B.item=%(item_code)s AND B.is_active=1 
                           AND B.is_default=1 AND I.item_group = 'Products'""",
                        {"item_code": self.product_ref_no}, as_dict=1)
    if bom:
        spp_settings = frappe.get_single("SPP Settings")
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.purpose = "Material Transfer"
        stock_entry.company = "SPP"
        stock_entry.stock_entry_type = "Material Transfer"
        stock_entry.from_warehouse = self.source_warehouse or spp_settings.unit_2_warehouse
        stock_entry.to_warehouse = spp_settings.pdir_visual_t__warehouse
        stock_entry.append("items", {
            "item_code": bom[0].item_code,
            "s_warehouse": self.source_warehouse or spp_settings.unit_2_warehouse,
            "t_warehouse": spp_settings.pdir_visual_t__warehouse,
            "stock_uom": "Nos", "uom": "Nos",
            "use_serial_batch_fields": 1,
            "spp_batch_number": self.spp_batch_number,
            "batch_no": self.batch_no,
            "transfer_qty": self.total_rejected_qty,
            "qty": self.total_rejected_qty,
            "source_ref_document": self.doctype,
            "source_ref_id": self.name,
        })
        stock_entry.insert(ignore_permissions=True)
        frappe.db.set_value(self.doctype, self.name, "stock_entry_reference", stock_entry.name)
        sub_entry = frappe.get_doc("Stock Entry", stock_entry.name)
        sub_entry.docstatus = 1
        sub_entry.save(ignore_permissions=True)
        return {"status": "success"}
```

## `validate_lot_number(batch_no, docname, inspection_type)` — lot scan validation

This is the **primary lot scan validation function** (lines 748–1049). It
resolves Job Card context, MPE status, Mould Specification piece weight, and
stock availability differently per inspection type.

**For Line / Patrol:**
```python
# Check no duplicate IE exists for same lot + type
check_exist = frappe.db.get_value("Inspection Entry",
    {"name": ("!=", docname), "docstatus": 1, "lot_no": batch_no,
     "inspection_type": inspection_type}, "name")
# Resolve Job Card by batch_code
check_lot_issue = frappe.db.sql("""SELECT JB.mould_reference, JB.total_completed_qty, 
                                    JB.workstation, JB.work_order, JB.name as job_card,
                                    JB.production_item, JB.batch_code, E.employee_name as employee
                                    FROM `tabJob Card` JB 
                                    LEFT JOIN `tabJob Card Time Log` LG ON LG.parent = JB.name
                                    LEFT JOIN `tabEmployee` E ON LG.employee = E.name
                                    WHERE JB.batch_code=%(lot_no)s LIMIT 1""", ...)
# Check MPE exists (optional — not required for submission)
# Derive one_no_qty_equal_kgs from Mould Specification (mould_ref + production_item)
# Resolve batch_no from Item Bin Mapping via Blank Bin Issue
```

**For Lot Inspection:**
- Same Job Card lookup
- MPE **must exist** — throws if no `stock_entry_reference` found for the lot:
  ```python
  if not rept_entry:
      return {"status":"Failed","message":f"There is no <b>Moulding Production Entry</b> found..."}
  ```
- Same Mould Specification lookup for piece weight

**For Incoming / Final:**
- Checks for Deflashing Receipt Entry (not MPE)
- Resolves product details from Deflashing Receipt's Stock Entry
- No Mould Specification lookup (not a moulding type)

**For Final Visual / PDIR:**
- Checks Lot Resource Tagging (LRT) with `scan_lot_no = batch_no`, `docstatus = 1`
- Validates BOM operations sequence (PDIR requires Final Visual to be done first)
- Checks stock availability via `check_available_stock`

## Rollback functions

### `rollback_entries(self, msg)` — rollback Branch A/B

```python
def rollback_entries(self, msg):
    self.reload()
    if self.stock_entry_reference:
        delete_stock_entry_safely(self.stock_entry_reference)
    bl_dc = frappe.get_doc(self.doctype, self.name)
    bl_dc.db_set("docstatus", 0)
    bl_dc.db_set("stock_entry_reference", "")
    frappe.throw(msg)
```

### `rollback_vs_pdir(self, lrt)` — rollback Branch C

```python
def rollback_vs_pdir(self, lrt=None):
    self.reload()
    if self.stock_entry_reference:
        delete_stock_entry_safely(self.stock_entry_reference)
    exe_info = frappe.get_doc(self.doctype, self.name)
    exe_info.db_set('docstatus', 0)
    exe_info.db_set('stock_entry_reference', '')
    if lrt:
        lrt.run_method('rollback_____')
```

### `rollback__vs_entry__only(self, msg)` — rollback Branch C (no LRT)

```python
def rollback__vs_entry__only(self, msg):
    self.reload()
    if self.vs_pdir_work_order_ref:
        stock__id = frappe.db.get_value("Stock Entry",
            {"work_order": self.vs_pdir_work_order_ref}, "name")
        if stock__id:
            delete_stock_entry_safely(stock__id)
        if frappe.db.exists("Work Order", self.vs_pdir_work_order_ref):
            frappe.delete_doc("Work Order", self.vs_pdir_work_order_ref, force=1)
    lot__r = frappe.get_doc(self.doctype, self.name)
    lot__r.db_set("docstatus", 0)
    lot__r.db_set("vs_pdir_stock_entry_ref", '')
    del__resp, batch__no = delete_batches([self.lot_no])
    if not del__resp:
        frappe.msgprint(batch__no)
    if msg:
        frappe.throw(msg)
```

## Legacy controller full function inventory

| Function | Line | Used for |
|---|---|---|
| `validate` (class) | 15 | Forward-date, lot/inspector/items required, duplicate check, type qty |
| `on_submit` (class) | 41 | 3-branch submission (A: Line/Patrol/Lot, B: Incoming/Final, C: Final Visual) |
| `submit__vs_pdir` (class) | 78 | Final Visual with rejection |
| `submit__vs_pdir_no_rejection` (class) | 111 | Final Visual without rejection |
| `make__vs__pdir` (class) | 156 | Utility method |
| `rollback_vs_pdir` (module) | 160 | Rollback Final Visual with LRT |
| `submit_moulding_entry` (module) | 172 | **DEPRECATED** — kept for backward compat |
| `submit_inspection_stock_entry_immediately` (module) | 185 | MPE batch cascade |
| `submit_deflash_receipt_entry` (module) | 325 | Trigger Deflashing Receipt |
| `rollback_entries` (module) | 337 | Rollback Branch A/B |
| `rollback__vs_entry__only` (module) | 355 | Rollback Branch C no LRT |
| `submit_vs_entry__only` (module) | 382 | Submit Final Visual no LRT case |
| `make_stock_entry_vs_entry__only` (module) | 399 | Make VS-only SE |
| `generate_barcode` (module) | 479 | Barcode image generation |
| `create_work_order_vs_entry__only` (module) | 500 | Create Work Order for Final Visual |
| `update_job_cards_vs_entry__only` (module) | 557 | Update Job Cards time logs |
| `make_vs_pdir_stock_entry` (module) | 577 | Final Visual rejection SE |
| `make_stock_entry` (module) | 641 | Branch A rejection SE (Line/Patrol/Lot kg) |
| `make_inc_stock_entry` (module) | 686 | Branch B rejection SE (Incoming/Final nos) |
| `check_available_stock` (module) | 731 | Stock balance check |
| `validate_lot_number` (module, whitelisted) | 748 | Lot scan validation per type |
| `check_multi_bom_vls` (module) | 1051 | BOM check for Final Visual |
| `check_return_workstation` (module) | 1066 | Workstation lookup by operation |
| `lrt_check_available_stock` (module) | 1078 | LRT stock check |
| `lrt_check_uom_bom` (module) | 1096 | LRT BOM/UOM check |
| `lrt_check__u1_warehouse` (module) | 1112 | U1 warehouse path for LRT |
| `lrt_check__material_recp` (module) | 1146 | Material receipt path for LRT |
| `lrt_material_respt_return_response` (module) | 1164 | LRT material response |
| `lrt_check__u1_sublot` (module) | 1181 | U1 sublot check |
| `lrt_return_response` (module) | 1188 | LRT response builder |
| `lrt_check_sublot` (module) | 1209 | Sublot check for LRT |
| `lrt_validate_dre_ins_jc` (module) | 1246 | DRE + Incoming Inspection check |
| `lrt_validate_lot_number` (module) | 1264 | LRT lot number validation |
| `check_vs_only_exists` (module) | 1308 | Check if lot has VS entry |
| `check_uom_bom` (module) | 1433 | BOM/UOM check |
| `check_sublot` (module) | 1453 | Sublot check |
| `validate_ins_receipt_return` (module) | 1484 | Incoming inspection receipt validation |
| `validate_inspector_barcode` (module, whitelisted) | 1509 | Inspector barcode validation |

## What Hermes workers can safely change here

| Change | Risk |
|---|---|
| Add a new inspection type value | Low — add to JSON options + add to `on_submit` branching |
| Add a new defect type to the Select | Low — cosmetic |
| Modify `validate_lot_number` for a new type | Medium — must preserve Job Card resolution for existing types |
| Touch `submit_inspection_stock_entry_immediately` | **Highest** — cascade is load-bearing for MPE; see `10-risks-and-decisions.md` |
| Touch the `on_submit` trigger query for Line+Lot vs Line+Lot+Patrol | **Highest** — affects batch cascade trigger; see Drift Finding #1 |
| Touch Branch C (Final Visual) | **High** — Work Order + LRT update chain; coordination with LRT spec needed |
| Touch the duplicate prevention logic | **High** — Final Visual exemption is a business rule |