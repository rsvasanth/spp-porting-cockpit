# 05 — Legacy ERPNext (v15) — `Delivery Challan Receipt`

**App:** `apps/shree_polymer_custom_app` (legacy custom app on ERPNext v15)
**Doctype path:** `shree_polymer_custom_app/.../doctype/delivery_challan_receipt/`
**Bench:** `spp15.local` ↔ `sppmaster.frappe.cloud`
**Controller size:** 1506 lines (`delivery_challan_receipt.py`)

## What DCR is in this system

`Delivery Challan Receipt` is a **polymorphic** legacy doctype that handles
multiple inbound material flows distinguished by `inward_material_type`:

| `inward_material_type` | Used for |
|---|---|
| `Master Batch` | MB Mixing (this spec) |
| `Compound` | Final Batch Mixing |
| ...others | Sheeting / Cut Bit / Blanking flows (in legacy these reuse DCR for similar receipts) |

The Bridge writes `inward_material_type = "Master Batch"` for MB Mixing via
the `value_map` in `04-bridge-layer.md`. The legacy controller branches on
this field to decide what Work Orders / Stock Entries to materialise.

## Controller — `delivery_challan_receipt.py`

```python
class DeliveryChallanReceipt(Document):
    def validate(self):
        if self.dc_receipt_date and getdate(self.dc_receipt_date) > getdate():
            frappe.throw("The <b>Mixing Date</b> can't be greater than <b>Today Date</b>..!")

    def on_submit(self):
        fb_mix = validate_final_batches(self)        # only True when inward_material_type=="Compound"
        if fb_mix:
            wo, message = create_wo(self)            # FB Mixing path
            if wo:
                update_over_all_dn_status(self, "Not Hold")
            else:
                frappe.throw(message or "Work Order creation failed..!")
        self.reload()

    def on_cancel(self):
        self.reload()
        # Resets is_received flags on linked Delivery Note Items
        if self.dc_items:
            for dc_items in self.dc_items:
                if dc_items.dc_no:
                    m_item = frappe.db.get_all("Delivery Note Item", filters={
                        "parent": dc_items.dc_no, "parenttype": "Delivery Note",
                        "scan_barcode": dc_items.scan_barcode, "item_code": dc_items.item_code})
                    if m_item:
                        for x in m_item:
                            frappe.db.set_value("Delivery Note Item", x.name, "is_received", 0)
                            frappe.db.set_value("Delivery Note Item", x.name, "dc_receipt_no", "")
```

**Validation:** Only a forward-date check — no business-rule validation in
`validate`. The strict checks (item presence, qty > 0) are implicit because
the Bridge builds the doc from the Console payload that already validated
those.

**Submission:** Branches on `validate_final_batches` — which inspects
`inward_material_type`:

```python
def validate_final_batches(self):
    if self.inward_material_type == "Compound":
        # FB Mixing path: walk dc_items, find batch items, validate each
        ...
        return True   # signals on_submit to create FB Work Order
    return False
```

**For MB Mixing (`inward_material_type == "Master Batch"`)**:
- `validate_final_batches` returns `False`
- `on_submit` does NOT call `create_wo` directly here
- Instead, the MB-specific Work Order + Stock Entry creation happens
  through a different code path triggered earlier — see "How the SE
  actually gets created for MB" below

## How the SE actually gets created for MB

This is the **non-obvious part** of the legacy flow. The DCR submission
itself doesn't materialise the Manufacturing Stock Entry for MB. Instead,
the flow is:

```
Bridge: legacy_doc.insert()              ← DCR created (Draft, no SE yet)
   │
   ▼
Bridge: legacy_doc.submit()              ← DCR submitted
   │
   ▼
DCR.on_submit fires
   ├─► validate_final_batches → False (it's a Master Batch, not Compound)
   ├─► on_submit returns without doing anything special
   │
   ▼
But: an earlier hook (likely DC Item-level / before_insert on dc_items
or a custom client script) creates the manufacturing Stock Entry as part
of the DCR insert. The full chain is in functions:
   • create_master_batch_stock(self, x)   — line 1087
   • create_mb_wo(dc_rec, w_item)         — line 1097
   • make_mb_stock_entry(...)             — line 1153
   • update_master_batch_details(...)     — line 1248
```

**Tracing point for Hermes:** the exact trigger that calls
`create_master_batch_stock` for an MB Mixing DCR submission is **not fully
captured in this spec**. To verify, run a staging MB submission and:

```bash
bench --site spp15.local console <<EOF
import frappe
# Find a recent MB DCR and trace its Stock Entry chain
recent = frappe.db.get_all("Delivery Challan Receipt",
    filters={"inward_material_type": "Master Batch", "docstatus": 1},
    order_by="creation desc", limit=1)
if recent:
    dcr = frappe.get_doc("Delivery Challan Receipt", recent[0].name)
    print("DCR:", dcr.name)
    print("stock_entry_reference:", dcr.stock_entry_reference)
    se_ids = (dcr.stock_entry_reference or "").split(",")
    for se_id in se_ids:
        if se_id:
            se = frappe.get_doc("Stock Entry", se_id)
            print(f"  SE: {se.name}, purpose={se.purpose}, docstatus={se.docstatus}")
            for item in se.items:
                print(f"    {item.item_code}: qty={item.qty}, batch_no={item.batch_no}, "
                      f"mix_barcode={item.mix_barcode}, is_finished_item={item.is_finished_item}")
EOF
```

This is the **first investigation a Hermes worker should run** if they need
to modify the MB → SE materialisation logic.

## Fields the Bridge writes to DCR for MB Mixing

The full set written by the mapping engine (see `04-bridge-layer.md`):

| Legacy field | Value source from Console payload |
|---|---|
| `reference_id` | Console-generated `reference_id` (13-digit ms timestamp) |
| `dc_no` | Same as `reference_id` (DCR's natural-key column) |
| `dc_receipt_date` | `stock_entry_data.posting_date` (Dash's `endDate`) |
| `operation` | `config.operation` = `"Master Batch Mixing"` |
| `inward_material_type` | Derived → `"Master Batch"` (via value_map on `operation`) |
| `item_to_manufacture` | `metadata.produced_item` (the MB FG item code) |
| `bridge_mix_barcode` | `mix_barcode` (Console-generated `C_YYMMDDXn`) |
| `source_warehouse` | `config.legacy_source_warehouse` |
| `target_warehouse` | `config.legacy_target_warehouse` |
| `wip_warehouse` | `config.legacy_wip_warehouse` |
| `dc_items` (child rows) | Each row from `stock_entry_data.consumption_items` |

The legacy `dc_items` rows get:
- `item_code`, `qty`, `batch_no`, `spp_batch_no`, `scan_barcode` (= mix_barcode)
- `dc_no` = reference_id (broadcast from header)
- `operation` = "Master Batch Mixing" (broadcast)
- `item_to_manufacture` = the MB FG item (broadcast)

## The `bridge_mix_barcode` honor pattern

When `reference_id` is set on a DCR, the legacy controller honors the
`bridge_mix_barcode` value sent by the Bridge **instead of** running its
own barcode generator (`generate_barcode(compound)` at line 1060).

This is the **single-barcode-authority** invariant. Console generates
the mix barcode; Legacy stores it; downstream Compound Inspection looks
it up. If anyone changed this so legacy generates a different barcode,
the 6-strategy SE lookup in the Bridge would fail catastrophically.

The exact code path:

1. Console payload includes `mix_barcode: "C_YYMMDDXn"`
2. Bridge mapping writes it to `legacy_doc.bridge_mix_barcode`
3. Legacy DCR's controller (or one of its helpers) checks
   `if self.bridge_mix_barcode: use that else self.bridge_mix_barcode = generate_barcode(self.compound)`
4. The barcode then propagates into the manufacturing SE's
   `mix_barcode` field on the FG row

## Downstream legacy consumers of MB Mixing's output

The Stock Entry created by MB Mixing's DCR submission gets consumed by:

### Compound Inspection (next process in the chain)

When QA opens a Compound Inspection on Legacy, the Bridge's
`populate_compound_inspection_fields` is called. Inside it,
`_lookup_legacy_stock_entry` runs the 6-strategy chain to find the MB's
manufacturing SE so it can set `self.stock_id` (a required field on
legacy Compound Inspection).

```python
def _apply_compound_identity_to_doc(doc, identity, se_lookup):
    """Write resolved compound identity onto the legacy Compound Inspection doc.
    SINGLE place that sets stock_id, stock_entry_reference, dc_receipt_id,
    batch_no, mix_barcode, spp_batch_no, scan_compound, compound_ref, item_code.
    Idempotent: only sets a field if currently empty."""
    legacy_barcode = identity["spp_batch_no"] or identity["mix_barcode"]
    if not doc.get("scan_compound"):  doc.scan_compound  = legacy_barcode
    if not doc.get("mix_barcode"):    doc.mix_barcode    = legacy_barcode
    if not doc.get("spp_batch_no"):   doc.spp_batch_no   = legacy_barcode
    if not doc.get("batch_no"):       doc.batch_no       = se_lookup["batch_no"]
    if not doc.get("stock_id"):       doc.stock_id       = se_lookup["stock_id"]
    if not doc.get("stock_entry_reference"): doc.stock_entry_reference = se_lookup["stock_id"]
    if not doc.get("dc_receipt_id"):  doc.dc_receipt_id  = se_lookup["dc_receipt_id"]
    if not doc.get("item_code"):      doc.item_code      = identity["item_code"]
```

**If MB Mixing writes `mix_barcode` correctly, this is the data flow:**

```
MB Mixing DCR  →  Manufacturing SE  →  Compound Inspection.stock_id
       │              (mix_barcode set)        (resolved via _lookup_legacy_stock_entry)
       │
       └─► dc_receipt_id ↘
                          → Compound Inspection.dc_receipt_id
       └─► batch_no    ↗
```

### Final Batch Mixing (also via DCR)

FB Mixing creates another DCR with `inward_material_type == "Compound"`,
whose `dc_items` reference the MB's batch number as a consumed raw
material. This is where `validate_final_batches → True → create_wo` runs.

## Legacy controller — full function inventory relevant to MB

From `grep "^def "` on `delivery_challan_receipt.py`:

| Function | Line | Used for |
|---|---|---|
| `validate` (class method) | 10 | Forward-date check only |
| `on_submit` (class method) | 14 | Branches into FB path; for MB returns |
| `on_cancel` (class method) | 24 | Resets is_received on linked DN Items |
| `update_over_all_dn_status` | 35 | Updates parent Delivery Note received status |
| `update_stock_ref` | 61 | Appends a Stock Entry name to `stock_entry_reference` (comma-separated) |
| `update_workorder_ref` | 71 | Sets `work_order_ref` on child rows |
| `rollback_wo_se_jc` | 74 | Cleans up WO + SE + Job Card if DCR submit fails |
| `validate_final_batches` | 146 | Returns True iff inward_material_type is Compound |
| `get_batch_items` | 194 | Lists Console-side batch items for a compound |
| `validate_barcode` | 232 | Validates a scanned raw material barcode |
| `update_job_cards` | 314 | Updates Job Card actual_weight on submit |
| `create_wo` | 413 | FB Mixing Work Order creation (not MB) |
| `make_stock_entry` | 507 | Generic SE creation helper |
| `create_wo_final_batch_mixing` | 626 | FB-specific Work Order |
| `rollback_transaction` | 694 | Frappe rollback shortcut |
| `validate_bom_items` | 697 | Verifies BOM rows present |
| `make_stock_entry_final_batch` | 722 | FB SE creation |
| `update_receive_status` | 851 | Toggles is_received on DN items |
| **`create_master_batch_stock`** | **1087** | **MB-specific stock entry creation** ← MB path |
| **`create_mb_wo`** | **1097** | **MB Work Order creation** ← MB path |
| **`make_mb_stock_entry`** | **1153** | **MB Stock Entry creation** ← MB path |
| **`update_master_batch_details`** | **1248** | **Writes MB details back to DCR + SE** ← MB path |
| `create_compound_stock` | 1273 | Compound-side stock entry |
| `validate_bom_items_c` | 1288 | Compound BOM validation |

The **MB-specific path** (the four functions bolded) is what materialises
the manufacturing SE that downstream Compound Inspection depends on. Their
exact trigger sequence is part of the legacy app's historical wiring and
should be traced empirically (see "How the SE actually gets created for MB"
above) before any Hermes worker modifies it.

## Things that can go wrong on the legacy side

| Failure | Symptom | Fix |
|---|---|---|
| Mapping payload missing `bridge_mix_barcode` | Legacy auto-generates a different barcode; Compound Inspection later fails to find the SE | Verify `Legacy Sync Mapping` row for MB has `mix_barcode → bridge_mix_barcode` |
| `inward_material_type` ends up as wrong value | DCR submits but `validate_final_batches` makes wrong branch | Check `Legacy Sync Mapping`'s `value_map` for `operation`; default of `"Compound"` may be silently swallowing a real bug |
| `source_warehouse` / `target_warehouse` missing | DCR insert fails with link validation | Verify `Console Process Template`'s warehouse rows have `legacy_warehouse` populated |
| Mass balance drift between consumption_items and FG qty | SE creates with imbalance — caught at Stock Ledger reconciliation time | No fix needed at this layer; Console intentionally does not enforce. See `10-risks-and-decisions.md`. |
| `dc_items` rows have empty `item_code` | Legacy controller throws in validate | Likely audit-trail payload made it to legacy somehow; should not happen because Bridge is fed canonical payload |

## What Hermes workers can safely change here

The legacy custom app is **read-only reference** for the cockpit. Hermes
workers should **NOT** modify the legacy DCR controller — its behavior is
load-bearing for ALL inbound material flows, not just MB.

If a change to legacy behavior is genuinely required:
1. Surface it explicitly in `10-risks-and-decisions.md`
2. Coordinate with you (the production overseer)
3. Get explicit go-ahead before touching `shree_polymer_custom_app`
4. The change should be made on the legacy bench, not via the Bridge

The Bridge mapping (in Console's `console_mapping_seeder.py`) is the right
layer for adjusting **how** Console payloads land on legacy. Touch the
mapping, not the legacy code.
