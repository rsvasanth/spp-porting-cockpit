# 02 — Frontend Dash — `InspectionEntry.tsx`

**File:** `apps/shree_polymer_console/shree_polymer_console/public/inspection/InspectionEntry.tsx`
**Size:** Estimated ~800 lines (inspector scan + lot scan + type-aware defect rows).
**Framework:** React + Frappe React SDK (`frappe-io/frappe-react-sdk`).

> This spec is written from the legacy controller + JSON schema. The React
> component design is inferred from the field visibility rules and the
> type-specific UX flows. Actual component implementation should match
> these patterns.

## What the Dash does

The Inspection Entry Dash is a **type-aware form** with 6 inspection type
variants. The inspector:

1. Selects inspection type
2. Scans inspector badge → `inspector_code` + `inspector_name` populated
3. Scans production lot → `lot_no` resolved, system fetches Job Card context,
   MPE status, and mould specification piece weight
4. Enters inspected quantities and defect rows (dynamic per type)
5. Submits → Console `initialize_submission` → Bridge → Legacy IE submitted

## Type selection

The `inspection_type` field is a Select with 6 options. It is the **primary
discriminator** that controls all downstream field visibility, required-field
rules, and submit behavior.

```typescript
const INSPECTION_TYPES = [
  "Patrol Inspection",
  "Line Inspection",
  "Lot Inspection",
  "Incoming Inspection",
  "Final Visual Inspection",
] as const;
// Note: "Visual Inspection" (6 records) may be a pre-unification artifact
// — treat as deprecated or included as-is
```

Changing `inspection_type` after entering data should reset child rows and
totals (confirm with product owner if partial data preservation is desired).

## Inspector scan

- `scan_inspector` field: Barcode input, calls `validate_inspector_barcode`
- On valid scan: `inspector_code` (Link → Employee) + `inspector_name` (Data) populated
- On invalid: error message shown
- Designation mapping from SPP Settings filters which employees are valid
  inspectors for the selected type (line 1516: `f"{inspection_type.split(' ')[0]} Inspector"`)

## Lot / production scan

- `scan_production_lot` field: Barcode input, calls `validate_lot_number(batch_no, docname, inspection_type)`
- On valid scan: `lot_no`, `product_ref_no`, `operator_name`, `machine_no`,
  `batch_no`, `spp_batch_number`, and type-specific context populated
- For moulding types (Line/Patrol/Lot): `one_no_qty_equal_kgs` resolved from
  Mould Specification using mould_reference + production_item

## Field visibility per type

Derived from `inspection_entry.json` `depends_on` conditions:

| Field | Line/Patrol/Lot | Incoming/Final | Final Visual | Notes |
|---|---|---|---|---|
| `inspected_qty_nos` | Shown (read_only, mandatory) | Hidden | Hidden | FR-IE-006 |
| `total_inspected_qty_nos` | Hidden | Shown (mandatory) | Shown (mandatory) | FR-IE-007 |
| `total_inspected_qty_kgs` | Hidden | Shown (conditional on UOM=Kg) | Shown (conditional on UOM=Kg) | |
| `uom` | Hidden | Hidden | Shown (Nos/Kgs select) | Default "Nos" |
| `total_rejected_qty_kg` | Shown | Hidden | Hidden | Rejection in kg |
| `is_manual_rejected_weight` | Shown (Patrol only) | Hidden | Hidden | Check, read_only |
| `vs_pdir_qty` | Hidden | Hidden | Shown (read_only) | |
| `vs_pdir_qty_after_rejection` | Hidden | Hidden | Shown (hidden field, computed in validate) | |
| `type_of_defect` | Hidden (child row field) | Hidden (child row field) | Hidden (child row field) | |
| `rejected_qty` | Hidden (child row field) | Hidden (child row field) | Hidden (child row field) | |
| `items` (child table) | Shown | Shown | Shown | `Inspection Entry Item` |
| `machine_no` | Shown (read_only) | Hidden | Hidden | From Job Card workstation |
| `product_ref_no` | Shown (read_only) | Shown (read_only) | Shown (read_only) | |

## Child table — `Inspection Entry Item`

The child table stores defect rows with:
- `type_of_defect` — Select: FLOW-(FL), BUBBLE-(BU)/BLISTER-(BL), CUTMARK-(CU),
  DEFLASH-(DF), RIB, FOREIGN PARTICLE-(FP), UNDER FILL-(UF), DIPRESSION-(DP),
  UNDER CURE-(UC), SURFACE DEFECT-(SD), OVER CURE-(OC)/FAST CURE, BURST/TEAR,
  BLACK MARK
- `rejected_qty` — Int (nos)
- `rejected_qty_kg` — Float (kg, hidden in JSON but present in legacy logic)

The "Add" button (hidden in JSON) calls a server-side method to append rows.
In the Console Dash this should be replaced with inline row addition.

## Totals computation

On every child row change:

```typescript
const totalRejectedNos = items.reduce((sum, row) => sum + (row.rejected_qty || 0), 0);
const totalRejectedKg  = items.reduce((sum, row) => sum + (row.rejected_qty_kg || 0), 0);
const rejectionPct     = inspectedQty > 0 ? (totalRejectedNos / inspectedQty) * 100 : 0;
```

For Line/Patrol/Lot: `total_rejected_qty_kg` = sum of child `rejected_qty_kg` OR
derived from `total_rejected_qty * one_no_qty_equal_kgs` if not manually entered.

For Incoming/Final/Final Visual: `total_rejected_qty` is sum of child `rejected_qty` (nos).

## Validation feedback

The Dash should call `validate_lot_number` on lot scan to get early feedback
before the user fills in defect rows. The response includes:

- For Line/Patrol: Job Card context, MPE completion status, one_no_qty_equal_kgs
- For Lot: same + MPE stock_entry_reference check (Lot requires MPE to exist)
- For Incoming: Deflashing Receipt Entry check
- For Final Visual: LRT check + BOM operations sequence validation

## Submit flow

1. `handleSubmit` builds payload with all header fields + child rows
2. `initialize_submission({ payload })` — creates Console Inspection record
3. `execute_submission_step` fires Legacy Bridge leg
4. Dash shows real-time status panel
5. On success: IE submitted, draft rejection SE created (Line/Patrol/Lot/Incoming)
6. On failure: error modal with rollback state visible

## What Hermes workers can safely change here

| Change | Risk |
|---|---|
| Add a new inspection type option | Low — add to Select + add corresponding `depends_on` rules |
| Add a new defect type option | Low — add to Select in child row |
| Change child row field labels | Low — cosmetic only |
| Modify type-specific visibility conditions | Medium — must match legacy JSON `depends_on` logic |
| Change totals computation formula | Medium — affects rejection kg accuracy |
| Touch the submit flow (initialize_submission → execute_submission_step) | **High** — shared pattern with all Console doctypes; needs architecture review |