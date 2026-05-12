# 05 — Legacy ERPNext — `Moulding Production Entry` controller

**File:** `apps/shree_polymer_custom_app/shree_polymer_custom_app/shree_polymer_custom_app/doctype/moulding_production_entry/moulding_production_entry.py`
**Size:** 1,429 lines (controller only; `shree_polymer_custom_app.api` helpers are external)
**JSON:** `apps/shree_polymer_custom_app/.../moulding_production_entry.json`

This section documents the full legacy controller behavior. For MPE-specific
orchestration in Console (initialize_submission, create_local_moulding_production_entry,
apply_bridge_result), see [03-console-backend.md](03-console-backend.md). For the
Bridge mapping, see [04-bridge-layer.md](04-bridge-layer.md).

## Doctype metadata

```json
{
  "autoname": "MLDPE-.#####",
  "is_submittable": 1,
  "module": "Shree Polymer Custom App",
  "fields": [ /* 43 fields */ ],
  "permissions": [{ "role": "System Manager", "create": 1, "submit": 1, ... }]
}
```

Key field groups:
- **Identification:** `scan_lot_number` (barcode), `job_card` (Link), `moulding_date`
- **Operator:** `operator` (barcode scan), `employee` (resolved Link), `employee_name`
- **Supervisor:** `scan_supervisor`, `supervisor_id`, `supervisor_name`
- **Production:** `weight`, `number_of_lifts`, `no_of_running_cavities`, `curing_time`
- **Compound:** `compound`, `batch_details` (JSON), `balance_bins` (Table child)
- **Shell:** `s_source_warehouse`, `s_batch`, `shell_qty_kgs`, `shell_qty_nos`, `shell_item`
- **Injection variant:** `is_injection_moulding` (hidden Check), `purged_compound`, `compound_leakage`
- **Output:** `stock_entry_reference`, `batch_no`, `spp_batch_number`, `weight_without_shell`
- **Mould reference:** `mould_reference`, `no_of_cavity_in_mspec` (hidden)

## Document lifecycle — `validate()`

The validate chain runs on every save (draft or submit attempt). Key steps:

### 1. `validate()` — injection detection from workstation name

```python
def validate(self):
    if self.job_card:
        workstation = frappe.db.get_value("Job Card", self.job_card, "workstation")
        if workstation:
            ws_name = frappe.db.get_value("Workstation", workstation, "workstation_name") or ""
            self.is_injection_moulding = 1 if ("INJECTION" in ws_name.upper() or "INJUCTION" in ws_name.upper()) else 0
        else:
            self.is_injection_moulding = 0
    else:
        self.is_injection_moulding = 0
```

**Key behavior:** `is_injection_moulding` is derived from the workstation name
on every `validate()` call (not stored at scan time). The check handles both
the correct spelling `INJECTION` and the historical typo `INJUCTION` found
in production data.

### 2. `validate()` — date and required field checks

```python
if getdate(self.moulding_date) > getdate():
    frappe.throw("The <b>Posting Date</b> can't be greater than <b>Today Date</b>..!")
if not self.curing_time:
    frappe.throw(f"Curing Time can't be Empty or Zero..!")
if not self.no_of_running_cavities:
    frappe.throw(f"No.of running cavities can't be Empty or Zero..!")
if not self.number_of_lifts:
    frappe.throw(f"No.os lifts can't be Empty or Zero..!")
```

### 3. `validate()` — inspection quantity + balance bin gate

```python
ins_resp_ = self.validate_inspection_qty(self.scan_lot_number)
if ins_resp_.get("status") == "success":
    if self.no_balance_bin == 0:
        if not self.balance_bins:
            frappe.throw("Please scan and add atleast one <b>Balance Bin</b>..!")
    tolerance_val = validate_tolerance(self)
    # ... tolerance message or throw
else:
    frappe.throw(ins_resp_.get("message"))
```

> **Note:** `validate_inspection_qty()` currently returns `{"status": "success"}`
> unconditionally — the body is commented out. The active inspection check is
> in `validate_lot_number()` (whitelisted API), which the Dash calls before
> presenting the entry form. The balance bin gate here enforces that at least
> one balance bin row exists if `no_balance_bin = 0`.

### 4. `validate()` — weight and required references

```python
if not self.weight:
    frappe.throw(f"Weight can't be Empty or Zero..!")
if not self.job_card:
    frappe.throw(f"Job Card value is missing..!")
if not self.compound:
    frappe.throw(f"Compound value is missing..!")
if not self.batch_details:
    frappe.throw(f"Source batch details not found..!")
self.cmpr_balbin_get_cmp_qty()  # accumulates compound_available_qty from batch_details
self.weight = flt(self.weight, 3)
```

### 5. `validate()` — output weight calculation

```python
# Calculate total output weight (Produced + Rejection + Purge + Leakage)
total_output_weight = flt(self.weight + self.line_rejection_qty + flt(self.purged_compound) + flt(self.compound_leakage), 3)
self.weight_without_shell = total_output_weight
```

> **Injection variant:** `purged_compound` and `compound_leakage` are only
> mandatory when `is_injection_moulding = 1` (set in the JSON field's
> `mandatory_depends_on`). They contribute to the output weight calculation.

### 6. `validate()` — shell item handling

```python
s_resp = validate_shell(self)
if s_resp.get('status') == 'failed':
    frappe.throw(s_resp.get('message'))
else:
    if s_resp.get('is_shell_item_found'):
        self.s_source_warehouse = s_resp.get('warehouse')
        self.s_batch = s_resp.get('batch_id')
        self.shell_qty_kgs = s_resp.get('total_shell_qty_in_kgs')
        self.shell_qty_nos = s_resp.get('total_shell_qty_in_nos')
        self.shell_item = s_resp.get('shell_item')
        self.weight_without_shell = flt(total_output_weight - s_resp.get('total_shell_qty_in_kgs'), 3)
    else:
        self.weight_without_shell = total_output_weight
```

Shell item presence is BOM-driven (checked via `validate_shell()`). When found,
output weight is reduced by shell kg. Shell is transferred from Unit-2 warehouse
in the Stock Entry.

## `validate_get_line_ins_qty()` — line rejection weight calculation

```python
def validate_get_line_ins_qty(self):
    # Fetch theoretical rejection weight instead of weighed rejection
    ins_info = frappe.db.get_all("Inspection Entry", {
        "lot_no": self.scan_lot_number, "docstatus": 1,
        "inspection_type": ["in", ["Line Inspection", "Patrol Inspection"]]
    }, ["name", "total_rejected_qty"])

    total_rejected_qty_nos = 0
    if ins_info:
        for ins in ins_info:
            total_rejected_qty_nos += flt(ins.total_rejected_qty, 3)

    # Resolve Asset ID to name for consistent Mould Specification lookup
    mould_val = self.mould_reference
    resolved_mould = frappe.db.get_value("Asset", mould_val, "asset_name") or mould_val

    mould_spec = frappe.db.get_value("Mould Specification",
        {"mould_ref": resolved_mould, "compound_code": self.compound, "mould_status": "ACTIVE"},
        "avg_blank_wtproduct_gms")

    if mould_spec:
        avg_blank_weight_kg = flt(mould_spec, 3) / 1000
    else:
        frappe.log_error(title="Mould Spec Missing", message=f"No Active Mould Spec found for {self.mould_reference}")

    self.line_rejection_qty = flt(total_rejected_qty_nos * avg_blank_weight_kg, 3)
```

**Key behavior:**
- `total_rejected_qty` from inspection entries = **piece count** (nos), not weight
- Conversion to kg uses `avg_blank_wtproduct_gms` from active Mould Specification
- Mould reference resolved via Asset name (handles the Asset ID → name resolution)
- `line_rejection_qty` is a float stored on the document for use in manufacturing qty

## `cmpr_balbin_get_cmp_qty()` — compound available from batch details

```python
def cmpr_balbin_get_cmp_qty(self):
    import json
    self.updated_batch_details = json.loads(self.batch_details)
    for is__bc in self.updated_batch_details:
        if is__bc.get('is_balance_bin'):
            self.compound_available_qty += is__bc.get('consumed__qty')
        else:
            self.compound_available_qty += is__bc.get('qty')
```

`compound_available_qty` accumulates from all batch detail rows (both consumed
balance bins and fresh bins). This is the denominator for the tolerance check
and the material consumption calculation.

## `on_submit()` — the core booking logic

The submit chain has five gates, each throwing on failure:

```
validate_cavity → validate_mat_qty → validate_comsumption_details
  → validate_actual_warehouse_stock → make_stock_entry
```

### Gate 1: `validate_cavity()`

```python
def validate_cavity(self):
    if self.no_of_cavity_in_mspec:
        if not float(self.no_of_cavity_in_mspec) >= float(self.no_of_running_cavities):
            return {"message": f"The <b>No.of.Cavitiy - {self.no_of_running_cavities}</b> can't be greater than - <b>{self.no_of_cavity_in_mspec}</b>..! "}
        else:
            return {"status": "success"}
    else:
        return {"message": f"The <b>No.of.Cavities</b> from <b>Job Card</b> not fetched.<br>Please check the Job Card..!"}
```

Running cavities must not exceed the mould specification's cavity count.

### Gate 2: `validate_mat_qty()`

```python
def validate_mat_qty(self):
    total_available_qty = flt(flt(self.compound_available_qty, 3) + flt(self.shell_qty_kgs, 3), 3)
    total_required_qty = flt(self.weight + self.line_rejection_qty + flt(self.purged_compound) + flt(self.compound_leakage), 3)

    spp_settings = frappe.get_single("SPP Settings")
    if not spp_settings.maximum__allowed_qty and spp_settings.maximum__allowed_qty != 0:
        return {"status": "failed", "message": "The '%' of excess Qty allowed for the <b>Production Entry</b> not mapped in <b>SPP Settings</b>..!"}

    if not total_available_qty == total_required_qty:
        if total_required_qty > total_available_qty:
            if spp_settings.maximum__allowed_qty:
                one_percen = flt(total_available_qty / 100, 3)
                actual_percen = flt(total_required_qty / one_percen, 3)
                allowd_percen = flt(100.0 + spp_settings.maximum__allowed_qty, 3)
                if actual_percen > allowd_percen:
                    total_with_extra_qty = flt(spp_settings.maximum__allowed_qty * one_percen, 3)
                    return {"status": "failed", "message": f"The <b>Total Required Qty - {total_required_qty} kgs</b> should be less than or equal to total <b>Available Qty -> ...</b>"}
            elif spp_settings.maximum__allowed_qty == 0:
                return {"status": "failed", "message": "Total Required Qty should be less than or equal to total Available Qty"}
    return {"status": 'success'}
```

**Key behavior:** Uses `maximum__allowed_qty` from SPP Settings (not hardcoded).
When `maximum__allowed_qty == 0`, any over-consumption is rejected. When set
to a positive value, allows that percentage over-consumption before blocking.

### Gate 3: `validate_comsumption_details()`

This is the most complex gate. It:
1. Calculates proportional consumption for each batch detail row
2. Handles balance bins with corrected inventory logic (uses measured net weight)
3. Validates total consumption against compound available quantity
4. Calls `validate_consumption_with_spp_settings()` for the mat-percentage check

```python
def validate_comsumption_details(self):
    # ... proportional share logic for balance bins and fresh bins ...
    
    # Validation: Shortage Block
    if flt(weight, 3) > flt(self.compound_available_qty, 3):
        frappe.throw(f"<b>Insufficient compound stock scanned!</b><br>...")

    vcwspps = validate_consumption_with_spp_settings(self)
    if vcwspps.get('status') == "success":
        self.updated_batch_details = json.dumps(self.updated_batch_details)
        return {"status": 'success'}
    else:
        return vcwspps
```

### Gate 4: `validate_actual_warehouse_stock()`

Added in a later iteration. Validates **actual warehouse stock** for each
consumed batch against the source warehouse from the Work Order. Uses
`erpnext.stock.doctype.batch.batch.get_batch_qty` (READ-ONLY).

```python
def validate_actual_warehouse_stock(self):
    # For each consumed batch, checks get_batch_qty(batch_no, warehouse, item_code)
    # Returns HTML table of shortages if any found
    # Returns {"status": "failed", "message": html_table} on shortage
    # Returns {"status": "success"} if all batches have sufficient stock
```

This is a NEW guard added after the initial production run — the original
consumption validation only checked the scanned bin weights, not the actual
warehouse stock.

### Gate 5: `make_stock_entry()` — SE creation + submission

See [the dedicated `make_stock_entry` section below](#make_stock_entry---se-creation-submission-and-cascade).

## `make_stock_entry()` — SE creation, submission, and cascade

```python
def make_stock_entry(self):
    production__item = frappe.db.get_value("Work Order", frappe.db.get_value(
        "Job Card", self.job_card, "work_order"), "production_item")
    batch__rep, batch__no = generate_batch_no(
        batch_id="T"+self.scan_lot_number, item=production__item,
        qty=flt(flt((self.weight + self.line_rejection_qty), 3), 3))
    if batch__rep:
        # 1. Update Job Card time logs, completed qty, parameters
        jc = frappe.get_doc("Job Card", self.job_card)
        for time_log in jc.time_logs:
            time_log.completed_qty = flt(flt((self.weight + self.line_rejection_qty), 3), 3)
            time_log.time_in_mins = 1
            time_log.employee = self.employee
        jc.total_completed_qty = flt(flt((self.weight + self.line_rejection_qty), 3), 3)
        jc.for_quantity = flt(flt((self.weight + self.line_rejection_qty), 3), 3)
        jc.number_of_lifts = self.number_of_lifts
        jc.no_of_running_cavities = self.no_of_running_cavities
        jc.cure_time = self.curing_time
        if self.special_instructions:
            jc.remarks = self.special_instructions
        jc.save(ignore_permissions=True)

        # 2. Update Work Order operations completed_qty
        work_order_id = frappe.db.get_value("Job Card", self.job_card, "work_order")
        work_order = frappe.get_doc("Work Order", work_order_id)
        if work_order.operations:
            for operation in work_order.operations:
                frappe.db.set_value("Work Order Operation", operation.name,
                    "completed_qty", flt(flt((self.weight + self.line_rejection_qty), 3), 3))
                frappe.db.commit()

        # 3. Build Stock Entry
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.purpose = "Manufacture"
        stock_entry.work_order = work_order_id
        stock_entry.company = work_order.company
        stock_entry.from_bom = 1
        stock_entry.naming_series = "MAT-STE-.YYYY.-"  # overridden by naming_series if available
        naming_status, naming_series = get_stock_entry_naming_series(spp_settings, "Moulding Entry")
        if naming_status:
            stock_entry.naming_series = naming_series
        stock_entry.bom_no = work_order.bom_no
        stock_entry.set_posting_time = 0
        stock_entry.use_multi_level_bom = work_order.use_multi_level_bom
        stock_entry.stock_entry_type = "Manufacture"
        stock_entry.fg_completed_qty = flt(flt(self.weight + self.line_rejection_qty, 3), 3)
        stock_entry.inspection_required = frappe.db.get_value("BOM", work_order.bom_no, "inspection_required")
        stock_entry.from_warehouse = work_order.source_warehouse
        stock_entry.to_warehouse = work_order.fg_warehouse

        # 4. Append source details (consumption rows + FG row + shell row)
        bcode_resp = generate_barcode(self.scan_lot_number)
        resp__s = append_source_details(stock_entry, self, work_order)

        # 5. Append FG item row
        stock_entry.append("items", {
            "item_code": work_order.production_item,
            "s_warehouse": None,
            "t_warehouse": work_order.fg_warehouse,
            "stock_uom": "Kg", "uom": "Kg", "conversion_factor_uom": 1,
            "is_finished_item": 1,
            "allow_zero_valuation_rate": 1,
            "transfer_qty": flt(flt(self.weight, 3), 3),
            "qty": flt(flt(self.weight, 3), 3),
            "use_serial_batch_fields": 1,
            "spp_batch_number": self.scan_lot_number,
            "mix_barcode": bcode_resp.get("barcode_text"),
            "barcode_attach": bcode_resp.get("barcode"),
            "barcode_text": bcode_resp.get("barcode_text"),
            "source_ref_document": self.doctype,
            "source_ref_id": self.name,
            "batch_no": batch__no,
            "docstatus": 0
        })
        stock_entry.blanking_dc_no = self.name
        stock_entry.insert(ignore_permissions=True)

        # 6. Update posting date and stock_entry_reference
        frappe.db.sql(f" UPDATE `tabStock Entry` SET posting_date = '{self.moulding_date}' WHERE name = '{stock_entry.name}' ")
        frappe.db.set_value(self.doctype, self.name, "stock_entry_reference", stock_entry.name)

        # 7. Generate reference batch (for SE batch linkage)
        ref_res, batch__no = generate_batch_no(batch_id=batch__no, reference_doctype="Stock Entry", reference_name=stock_entry.name)

        if ref_res:
            # IMMEDIATE SUBMIT — new flow (not deferred)
            stock_entry_doc = frappe.get_doc("Stock Entry", stock_entry.name)
            for item in stock_entry_doc.items:
                if item.serial_and_batch_bundle:
                    existing_bundle = frappe.db.exists("Serial and Batch Bundle", item.serial_and_batch_bundle)
                    if existing_bundle:
                        item.serial_no = None
                        item.batch_no = None
                item.use_serial_batch_fields = 1
            stock_entry_doc.docstatus = 1
            stock_entry_doc.save(ignore_permissions=True)

            # Cascade: submit Line + Patrol inspection stock entries
            submit_inspection_stock_entries_from_moulding(self, stock_entry_doc)

            # Update bins (close BBI items, retire or update IBM)
            update_bins(self, resp__s, spp_settings)

            # Complete Job Card immediately
            frappe.db.set_value("Job Card", self.job_card, "docstatus", 1)
            frappe.db.set_value("Job Card", self.job_card, "status", 'Completed')

            # Complete Work Order immediately
            frappe.db.set_value("Work Order", work_order_id, "status", "Completed")

            return {"status": "success"}
        else:
            return {"status": "failed", "message": batch__no}
    else:
        return {"status": "failed", "message": batch__no}
```

**Key behaviors:**
- Stock Entry is submitted **immediately** inside `make_stock_entry()` — not deferred
- Job Card and Work Order are completed immediately after SE submit
- Cascade to Line/Patrol inspection stock entries happens as part of the same transaction
- Bin closure (`update_bins`) happens after SE submit
- Batch number uses the `generate_batch_no` contract with prefix `T` + scan_lot_number

## `submit_inspection_stock_entries_from_moulding()` — inspection SE cascade

```python
def submit_inspection_stock_entries_from_moulding(self, moulding_stock_entry):
    """
    Submit Line & Patrol inspection stock entries immediately after Moulding Production.
    Updates batch_no on inspection entries, submits draft SEs.
    """
    # Extract target batch from Moulding SE FG row
    target_batch = None
    for item in moulding_stock_entry.items:
        if item.t_warehouse and item.is_finished_item:
            target_batch = item.batch_no
            break

    # Find submitted Line + Patrol inspection entries for this lot
    exe_insp = frappe.db.sql(f"""SELECT name, stock_entry_reference, inspection_type
    FROM `tabInspection Entry`
    WHERE (inspection_type = 'Line Inspection' OR inspection_type = 'Patrol Inspection')
    AND docstatus = 1 AND lot_no = '{self.scan_lot_number}'""", as_dict=1)

    for ins in exe_insp:
        if ins.stock_entry_reference:
            # Update batch_no in Stock Entry Detail
            frappe.db.sql(f"""UPDATE `tabStock Entry Detail`
            SET batch_no = '{target_batch}'
            WHERE source_ref_document = 'Inspection Entry' AND source_ref_id = '{ins.name}'""")

            # Update batch_no + spp_batch_number in Inspection Entry
            frappe.db.sql(f"""UPDATE `tabInspection Entry`
            SET batch_no = '{target_batch}', spp_batch_number = '{self.scan_lot_number}'
            WHERE name = '{ins.name}'""")

            # Submit draft Stock Entry
            ins_stock_entry = frappe.get_doc("Stock Entry", ins.stock_entry_reference)
            if ins_stock_entry.docstatus == 0:
                for item in ins_stock_entry.items:
                    item.use_serial_batch_fields = 1
                    if not item.batch_no:
                        item.batch_no = target_batch
                ins_stock_entry.docstatus = 1
                ins_stock_entry.save(ignore_permissions=True)
```

**Key behavior:** This function handles the MPE-specific cascade. It updates
inspection entries with the produced batch number and submits any pending
inspection Stock Entries. This is separate from the broader Inspection Entry
cascade (see [Inspection Entry spec](../inspection-entry/) for its own SE
creation and cascade behavior).

## `update_bins()` — BBI item and bin mapping closure

```python
def update_bins(self, resp__s, spp_settings):
    for c__bin in resp__s:
        if c__bin.get('is__consumed') and c__bin.get('is_balance_bin'):
            # Mark BBI item completed, update IBM qty and job_card
            frappe.db.sql(f""" UPDATE `tabBlank Bin Issue Item` set is_completed=1 where name = '{c__bin.get('blank_bin_issue_item_name')}' """)
            frappe.db.sql(""" UPDATE `tabItem Bin Mapping` set qty=(%(qty)s),job_card = %(job_card)s where name=%(name)s """,
                          {"qty": c__bin.get('balance__qty'), 'job_card': c__bin.get('job_card'), "name": c__bin.get('item_bin_mapping_name')})
        elif c__bin.get('is__consumed') and not c__bin.get('is_balance_bin'):
            # Retire IBM, mark BBI item completed, trigger asset movement
            frappe.db.sql(""" UPDATE `tabItem Bin Mapping` set is_retired=1 , job_card = %(job_card)s where name =%(name)s """,
                          {'job_card': c__bin.get('job_card'), "name": c__bin.get('item_bin_mapping_name')})
            frappe.db.sql(f""" UPDATE `tabBlank Bin Issue Item` set is_completed=1 where name = '{c__bin.get('blank_bin_issue_item_name')}' """)
            last_mov = frappe.db.sql(f" SELECT AMI.target_location FROM `tabAsset Movement` AM INNER JOIN `tabAsset Movement Item` AMI ON AM.name = AMI.parent WHERE AMI.asset = '{c__bin.get('bin')}' ORDER BY AMI.creation DESC LIMIT 1 ", as_dict=1)
            if last_mov:
                if not last_mov[0].target_location == spp_settings.from_location:
                    make_asset_movement(spp_settings, c__bin)
            else:
                make_asset_movement(spp_settings, c__bin)
```

**Key behavior:** When a bin is consumed:
- If it's a **balance bin** (partial consumption): BBI item marked completed, IBM qty
  updated to remaining balance, IBM job_card set to this MPE
- If it's a **full bin**: IBM retired, BBI item marked completed, Asset Movement
  created to return bin to `from_location`

The `resp__s` is the return from `append_source_details()`, which processes
`updated_batch_details` JSON and returns a list with `is__consumed`, `is_balance_bin`,
`blank_bin_issue_item_name`, `item_bin_mapping_name`, `bin`, `balance__qty`, `job_card`.

## `append_source_details()` — SE item rows from batch details

This function builds the consumption rows for the Stock Entry:

1. Consolidates consumed batches (multiple bins → single consumption row per batch)
2. Handles purge/leakage deduction from consumption (for injection moulding)
3. Adds a **scrap item row** for purge/leakage (marked `is_scrap_item=1`, uses same
   compound batch as consumed material, transferred to `purge_scrap_warehouse`)
4. Adds shell item row (if shell item present)

```python
def append_source_details(stock_entry, self, work_order):
    import json
    final_batch_details = []
    batch_details = json.loads(self.updated_batch_details)
    for b__ in batch_details:
        if b__.get('is__consumed'):
            # Consolidate by batch_no + spp_batch_number
            match_found = False
            for exe_b in final_batch_details:
                if exe_b.get('batch_no__') == b__.get('batch_no__') and exe_b.get('spp_batch_number') == b__.get('spp_batch_number'):
                    exe_b['consumed__qty'] = flt(exe_b['consumed__qty'] + b__['consumed__qty'], 3)
                    match_found = True
            if not match_found:
                final_batch_details.append(b__)

    # Calculate total purge qty (purged_compound + compound_leakage)
    total_purge_qty = flt(self.purged_compound) + flt(self.compound_leakage)
    remaining_purge_to_deduct = total_purge_qty

    for f__b in final_batch_details:
        full_batch_qty = flt(f__b.get('consumed__qty'), 3)
        normal_consumption_qty = full_batch_qty

        # Deduct purge from consumption rows (top-down)
        if remaining_purge_to_deduct > 0:
            if remaining_purge_to_deduct >= full_batch_qty:
                normal_consumption_qty = 0
                remaining_purge_to_deduct = flt(remaining_purge_to_deduct - full_batch_qty, 3)
            else:
                normal_consumption_qty = flt(full_batch_qty - remaining_purge_to_deduct, 3)
                remaining_purge_to_deduct = 0

        if normal_consumption_qty > 0:
            stock_entry.append("items", {
                "item_code": self.compound,
                "s_warehouse": work_order.source_warehouse,
                "t_warehouse": None,
                "is_finished_item": 0,
                "allow_zero_valuation_rate": 1,
                "use_serial_batch_fields": 1,
                "transfer_qty": flt(normal_consumption_qty, 3),
                "qty": flt(normal_consumption_qty, 3),
                "spp_batch_number": f__b.get('spp_batch_number'),
                "batch_no": f__b.get('batch_no__'),
            })

    # Add scrap row for purge/leakage (injection moulding)
    if total_purge_qty > 0:
        # Uses SAME batch as first consumed compound item
        first_batch_info = final_batch_details[0]
        stock_entry.append("items", {
            "item_code": self.compound,
            "s_warehouse": work_order.source_warehouse,
            "t_warehouse": None,
            "is_finished_item": 0,
            "is_scrap_item": 1,
            "allow_zero_valuation_rate": 1,
            "transfer_qty": flt(total_purge_qty, 3),
            "qty": flt(total_purge_qty, 3),
            "batch_no": first_batch_info.get('batch_no__'),
            "spp_batch_number": first_batch_info.get('spp_batch_number'),
            "docstatus": 0
        })

    # Add shell item row
    if self.shell_qty_nos:
        stock_entry.append("items", {
            "item_code": self.shell_item,
            "s_warehouse": self.s_source_warehouse,
            "t_warehouse": None,
            "stock_uom": "Nos", "uom": "Nos",
            "is_finished_item": 0,
            "allow_zero_valuation_rate": 1,
            "transfer_qty": self.shell_qty_nos,
            "qty": self.shell_qty_nos,
            "batch_no": self.s_batch,
            "docstatus": 0
        })

    return batch_details
```

## `validate_tolerance()` — production tolerance check

```python
def validate_tolerance(self):
    spp_settings = frappe.get_single("SPP Settings")
    total_bins_weight = frappe.db.sql(""" SELECT sum(IB.qty) as total_qty
        FROM `tabItem Bin Mapping` IB
        INNER JOIN `tabBlank Bin Issue Item` BI ON IB.blanking__bin = BI.bin
        INNER JOIN `tabJob Card` JB ON JB.name= BI.job_card
        WHERE IB.is_retired = 0 AND BI.is_completed=0 AND BI.docstatus = 1 AND JB.name=%(job_card)s""",
        {"job_card": self.job_card}, as_dict=1)
    if spp_settings.production_tolerance != 0 and total_bins_weight and total_bins_weight[0].total_qty:
        from_wt = total_bins_weight[0].total_qty - (total_bins_weight[0].total_qty * spp_settings.production_tolerance)/100
        to_wt = total_bins_weight[0].total_qty + (total_bins_weight[0].total_qty * spp_settings.production_tolerance)/100
        if not self.weight >= from_wt and self.weight < to_wt:
            return {"status": True, "message": "Mat bin weight should be between <b>"+str('%.3f' % (from_wt))+"</b> to <b>"+'%.3f' % (to_wt)+"</b>"}
    return {"status": True}
```

**Key behavior:** Tolerance is a **soft warning** — it returns a message rather
than throwing. The `validate()` caller issues a `frappe.msgprint()` for the
message but does not block submission. This is a deliberate design: production
variances are real signals, not errors.

> **Drift from old requirement:** The old requirements document said "hardcoded 1%."
> This is not accurate. Legacy uses `SPP Settings.production_tolerance` which is
> configurable and defaults to whatever the site has set. The 1% figure in the old
> requirements may have been a site-specific default, not a hardcoded constant.

## `validate_shell()` — shell item detection and sourcing

```python
def validate_shell(self):
    spp_settings = frappe.get_single("SPP Settings")
    if not spp_settings.unit_2_warehouse:
        frappe.throw(f'<b>Unit - 2 Warehouse</b> is not mapped in <b>SPP Settings</b>..!')

    bom = frappe.db.get_value("Job Card", self.job_card, "bom_no")
    shell_details = frappe.db.sql(f""" SELECT BI.item_code FROM `tabBOM Item` BI
        INNER JOIN `tabBOM` B ON B.name = BI.parent
        INNER JOIN `tabItem` I ON I.name = BI.item_code
        WHERE I.item_group = 'Shell' AND B.name = '{bom}' """, as_dict=1)

    if shell_details:
        # Resolve shell weight from Mould Specification or UOM conversion
        check_uom = frappe.db.get_all("UOM Conversion Detail", filters={
            "parent": shell_details[0].item_code, "uom": "Kg"}, fields=['conversion_factor'])
        if check_uom:
            shell_item = shell_details[0].item_code
            total_shell_qty_in_nos = self.number_of_lifts * self.no_of_running_cavities

            resolved_mould = frappe.db.get_value("Asset", self.mould_reference, "asset_name") or self.mould_reference
            mould_spec = frappe.db.get_value("Mould Specification",
                {"mould_ref": resolved_mould, "compound_code": self.compound, "mould_status": "ACTIVE"},
                "shell_weight")

            if mould_spec:
                shell_weight_gms = flt(mould_spec, 3)
            else:
                shell_weight_gms = flt(1000 / check_uom[0].conversion_factor, 3)

            total_shell_qty_in_kgs = flt((shell_weight_gms / 1000) * total_shell_qty_in_nos, 3)

            # Find a batch with sufficient stock in Unit-2 warehouse
            query = f""" SELECT B.batch_id,IBSB.qty batch_qty FROM `tabBatch` B
                INNER JOIN `tabItem Batch Stock Balance` IBSB ON IBSB.batch_no = B.batch_id AND IBSB.item_code = B.item
                WHERE B.item = '{shell_details[0].item_code}' AND IBSB.warehouse = '{spp_settings.unit_2_warehouse}'
                AND B.disabled = 0 AND B.expiry_date >= CURDATE() """
            stock_info = frappe.db.sql(query, as_dict=1)
            if stock_info:
                for k in stock_info:
                    if k.batch_qty >= total_shell_qty_in_nos:
                        selected_shell_batch = k.batch_id
                        break
                if not selected_shell_batch:
                    return {'status': 'failed', 'message': f'There is no enough <b>Stock</b> for the shell item - <b>{shell_details[0].item_code}</b>'}
            else:
                return {'status': 'failed', 'message': f'<b>Stock</b> is not found for the shell item - <b>{shell_details[0].item_code}</b>'}

            return {'status': 'success', 'is_shell_item_found': True, 'warehouse': spp_settings.unit_2_warehouse,
                    'batch_id': selected_shell_batch, 'total_shell_qty_in_kgs': total_shell_qty_in_kgs,
                    'total_shell_qty_in_nos': total_shell_qty_in_nos, 'shell_item': shell_item}
        else:
            return {'status': 'failed', 'message': f'<b>UOM</b> conversion factor in <b>Kgs</b> not found for the item - <b>{shell_details[0].item_code}</b>'}

    return {'status': 'success', 'is_shell_item_found': False}
```

## `on_cancel()` — rollback Job Card, Work Order, Stock Entry

```python
def on_cancel(self):
    try:
        se = None
        if self.stock_entry_reference:
            try:
                if frappe.db.get_value("Stock Entry", self.stock_entry_reference, "name"):
                    se = frappe.get_doc("Stock Entry", self.stock_entry_reference)
                    if se.docstatus == 1:
                        se.docstatus = 2
                        se.save(ignore_permissions=True)
            except Exception:
                frappe.db.rollback()
                frappe.throw("Can't cancel/change Stock Entry..!")
            if se:
                try:
                    frappe.db.sql(f"UPDATE `tabWork Order` SET status='Not Started' WHERE name='{se.work_order}'")
                    frappe.db.sql(f"UPDATE `tabWork Order Operation` SET status='Pending' WHERE parent='{se.work_order}' AND parentfield='operations' AND parenttype='Work Order' ")
                    frappe.db.sql(f"UPDATE `tabJob Card` SET status='Work In Progress',docstatus=0 WHERE work_order='{se.work_order}'")
                except Exception:
                    frappe.db.rollback()
                    frappe.throw("Can't cancel/change Work Order,Job card .. !")
        else:
            frappe.throw("Stock Entry reference not found.")
        frappe.db.commit()
    except Exception:
        frappe.db.rollback()
        frappe.log_error(title=f"{self.doctype }- on cancel failed", message=frappe.get_traceback())
        self.reload()
```

**Key behavior:** On cancel, the Stock Entry is cancelled (docstatus = 2), Work
Order reset to `Not Started`, Work Order Operations reset to `Pending`, and
Job Card reset to `Work In Progress` with docstatus = 0. No cascade to rollback
inspection entries or bin states — those remain as-is (intentional design).

## `rollback_entries()` — failure rollback (not on_cancel)

```python
def rollback_entries(self, msg):
    try:
        frappe.log_error(title=f"MPE Rollback Triggered: {self.name}", message=f"Reason: {msg}")
        self.reload()

        # 1. Rollback Main Stock Entry
        stock_name = frappe.db.get_value("Stock Entry", {"blanking_dc_no": self.name}, "name")
        if stock_name:
            delete_stock_entry_safely(stock_name)

        # 2. Reset Job Card
        frappe.db.set_value("Job Card", self.job_card, {"docstatus": 0, "status": "Work In Progress"})

        # 3. Reset Work Order
        work_order = frappe.db.get_value("Job Card", self.job_card, "work_order")
        if work_order:
            frappe.db.set_value("Work Order", work_order, {"status": "In Process", "produced_qty": 0})

        # 4. Reset MPE to draft
        self.db_set("docstatus", 0)
        self.db_set("stock_entry_reference", None)

        # 5. Delete the Batch
        del__resp, batch__no = delete_batches([self.scan_lot_number])

        frappe.db.commit()
        self.reload()

        if not del__resp:
            frappe.msgprint(batch__no)

    except Exception:
        frappe.db.rollback()
        self.reload()
        frappe.log_error(title="rollback_entries", message=frappe.get_traceback())
        frappe.msgprint("Something went wrong..Not able to rollback..!")
    frappe.throw(msg)
```

**When it fires:** Called from `make_stock_entry()` when the SE creation or
submission fails. It performs a controlled rollback of the partial state.

**Note:** Inspection Entry rollback is **DISABLED** in the current code (the
block that would reset Line/Patrol/Lot Inspection Entries to draft is commented
out). The decision not to cascade cancel to inspection entries is deliberate.

## `sort_bins_for_print()` — asset print card ordering

```python
def sort_bins_for_print(self, values):
    # Sorts print cards by numeric suffix (e.g., "Asset 12" → 12)
    # Non-integer suffixes appended after sorted integers
    # Used for print format presentation, not data integrity
```

Not load-bearing for the production workflow; only affects print layout.

## Whitelisted API functions

### `validate_lot_number(batch_no)` — lot scan validation

This is the primary entry-point the Dash calls before presenting the MPE form.
It performs FR-MPE-001 (open Job Card check) and FR-MPE-002 (inspection prerequisite check).

```python
@frappe.whitelist()
def validate_lot_number(batch_no):
    # 1. Check open moulding Job Card
    job_card = frappe.db.get_value("Job Card", {"batch_code": batch_no, "operation": "Moulding"}, 'status')
    if not job_card:
        return {"status": "Failed", "message": "The scanned lot barcode is <b>invalid</b>..!."}
    if job_card == "Completed":
        return {"status": "Failed", "message": "The <b>Moulding Operation</b> for the scanned lot was completed..!"}

    # 2. Check submitted Line + Patrol inspections exist
    check_line_inspe_entry = frappe.db.get_value("Inspection Entry", {
        "lot_no": batch_no, "docstatus": 1, "inspection_type": "Line Inspection"})
    check_patrol_inspe_entry = frappe.db.get_value("Inspection Entry", {
        "lot_no": batch_no, "docstatus": 1, "inspection_type": "Patrol Inspection"})

    missing_inspections = []
    if not check_line_inspe_entry:
        missing_inspections.append("Line Inspection")
    if not check_patrol_inspe_entry:
        missing_inspections.append("Patrol Inspection")

    if missing_inspections:
        return {"status": "Failed", "message": f"The following inspections are missing: {', '.join(missing_inspections)}"}

    # 3. Check open Blank Bin Issue rows exist for this lot
    check_lot_issue = frappe.db.sql(""" SELECT BI.bin,BI.name as blank_bin_issue_item_name,B.name as blanking_bin_issue_name,
        B.job_card,JB.name as job_card,B.scan_bin,JB.mould_reference,JB.no_of_running_cavities
        FROM `tabBlank Bin Issue Item` BI
        INNER JOIN `tabJob Card` JB ON JB.name= BI.job_card
        INNER JOIN `tabBlank Bin Issue` B ON B.name = BI.parent
        WHERE BI.is_completed = 0 AND JB.batch_code=%(lot_no)s AND B.docstatus = 1 ORDER BY B.creation ASC """,
        {"lot_no": batch_no}, as_dict=1)
    if not check_lot_issue:
        return {"status": "Failed", "message": "There is no entry for Blank Bin Issue for the scanned lot number."}

    # 4. Validate mould reference and cavity count present
    # 5. For each bin: check active Item Bin Mapping, resolve batch_no
    # 6. Validate compound is in active BOM
    # Returns {"status": "Success", "message": all_blank__bins} — the batch detail list
```

The returned `all_blank__bins` is the list of bin objects (with IBM data
resolved) that becomes the `batch_details` JSON on the MPE document.

### `validate_bin(batch_no, job_card)` — bin scan validation

```python
@frappe.whitelist()
def validate_bin(batch_no, job_card):
    # Checks scanned bin barcode against Item Bin Mapping
    # Returns bin_weight, blanking_bin (Asset ID), asset_name
```

### `validate_bin_weight(weight, bin, bin_Weight, prod_weight)` — balance bin validation

```python
@frappe.whitelist()
def validate_bin_weight(weight, bin, bin_Weight, prod_weight):
    # Checks balance bin gross weight >= bin tare weight
    # Checks net weight doesn't exceed expected remaining qty
    # Used when scanning a balance bin after partial consumption
```

### `validate_operator(operator, supervisor=None)` — operator badge validation

```python
@frappe.whitelist()
def validate_operator(operator, supervisor=None):
    # If supervisor: validates against SPP Settings designation_mapping for "Moulding Supervisor"
    # If operator only: validates employee barcode exists and is Active
    # Returns employee name + ID on success
```

## What Hermes workers can safely change here

| Change | Risk |
|---|---|
| Add a new validation in `validate()` | Low — additive; ensure cascade chain is respected |
| Change tolerance threshold | Medium — production impact; coordinate with shop floor |
| Add a new whitelisted API | Low — only called from Dash if registered in process template |
| Modify `make_stock_entry` batch prefix | **High** — downstream inspection cascade uses batch number |
| Change inspection cascade logic | **High** — Inspection Entry batch_no must match produced batch |
| Remove `is_injection_moulding` detection | **High** — injection variant handling (purge/leakage, scrap warehouse) depends on it |
| Change bin closure behavior | **High** — BBI + IBM state machine; changes affect upstream BBI |
| Touch `rollback_entries` | **High** — failure recovery; errors here leave inconsistent state |
| Touch `on_cancel` | **High** — ERPNext core behavior; unexpected changes break cancel flow |