# 02 — Frontend (Dash) — `MouldingProductionEntry.tsx` (planned)

**File:** `apps/shree_polymer_console/dash/src/components/processes/MouldingProductionEntry.tsx`
**Status:** PLANNED — not yet implemented. This section documents the expected
design based on legacy behavior and FR-MPE requirements. Subject to change
during implementation.

For the authoritative React/Dash implementation pattern, see
[`../master-batch-mixing/02-frontend-dash.md`](../master-batch-mixing/02-frontend-dash.md).

## Layout — what the operator sees

MPE is a **two-phase form** (not the three-phase scan flow of MB Mixing):

| Phase | State value | What's visible |
|---|---|---|
| Lot Scan | `'lot_scan'` | Lot barcode input → `validate_lot_number` → pre-fill form |
| Production Entry | `'production'` | Pre-filled Job Card + compound data, weight input, balance bin scan, submit |

## State model

```tsx
// Form Data
const [scanLotNumber, setScanLotNumber] = useState<string>('')
const [jobCard, setJobCard] = useState<string>('')
const [mouldReference, setMouldReference] = useState<string>('')
const [compound, setCompound] = useState<string>('')
const [weight, setWeight] = useState<string>('')
const [numberOfLifts, setNumberOfLifts] = useState<number>(0)
const [noOfRunningCavities, setNoOfRunningCavities] = useState<number>(0)
const [curingTime, setCuringTime] = useState<number>(0)

// Balance Bin State
const [noBalanceBin, setNoBalanceBin] = useState<boolean>(false)
const [balanceBins, setBalanceBins] = useState<BalanceBin[]>([])
const [weightOfBalanceBin, setWeightOfBalanceBin] = useState<string>('')
const [binCode, setBinCode] = useState<string>('')

// Injection variant
const [isInjectionMoulding, setIsInjectionMoulding] = useState<boolean>(false)
const [purgedCompound, setPurgedCompound] = useState<string>('')
const [compoundLeakage, setCompoundLeakage] = useState<string>('')

// Operator / Supervisor
const [operator, setOperator] = useState<string>('')
const [operatorName, setOperatorName] = useState<string>('')
const [supervisor, setSupervisor] = useState<string>('')

// Pre-filled data (from validate_lot_number response)
const [batchDetails, setBatchDetails] = useState<any[]>([])
const [mouldingDate, setMouldingDate] = useState<string>(format(new Date(), 'yyyy-MM-dd'))

// Submission State
const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
const [showSuccessModal, setShowSuccessModal] = useState<boolean>(false)
const [submissionResult, setSubmissionResult] = useState<SubmissionResult | null>(null)
```

## Backend calls the component makes

| Call | Purpose | When |
|---|---|---|
| `validate_operator` | Validates operator badge + optional supervisor | On scan |
| `validate_lot_number` | Validates lot barcode against JC, IE, BBI chain | On lot scan |
| `validate_bin` | Validates balance bin barcode | On balance bin scan |
| `validate_bin_weight` | Validates gross weight against tare | On weight entry |
| `get_bom_for_moulding_item` | Fetches BOM rows for compound validation | After lot scan |
| `initialize_submission` | Step 1 of two-step submit | On "Submit to ERP" |
| `execute_submission_step` | Step 2 — Legacy + Ops in parallel | After initialize |

## Lot scan flow

```
Operator scans lot barcode
   │
   ▼
handleLotScan(barcode)
   ├─► validate_lot_number({ batch_no: barcode })
   │     ├─► Checks: open JC, Line+Patrol IE, open BBI rows
   │     ├─► Returns: { status, message: bin_objects[] }
   │     └─► On success: pre-fills job_card, compound, mould_reference
   │
   ▼
Operator sees pre-filled form
   ├─► Confirms/updates number_of_lifts, no_of_running_cavities, curing_time
   ├─► Enters weight
   ├─► (if no_balance_bin = false): scans balance bins
   └─► Operator scans supervisor (if required)
```

## Balance bin scan flow

```
Operator scans balance bin barcode
   ├─► validate_bin({ batch_no: barcode, job_card })
   │     └─► Returns: { status, bin_weight, blanking_bin, asset_name }
   ├─► Operator enters gross weight
   ├─► validate_bin_weight({ weight, bin, bin_Weight, prod_weight })
   │     └─► Returns: { status, message }
   └─► On success: bin added to balanceBins[]
```

## Submit flow — `handleSubmit()`

Same two-step pattern as MB Mixing (`initialize_submission` → `execute_submission_step`
in parallel). See [`../master-batch-mixing/02-frontend-dash.md`](../master-batch-mixing/02-frontend-dash.md)
for the implementation pattern.

## Error and empty states

| State | Trigger | UI |
|---|---|---|
| Lot validation fails | `validate_lot_number` returns error | Red alert with specific missing prerequisite (Line IE, Patrol IE, BBI) |
| Balance bin not issued | `validate_bin` returns "bin not issued" | Inline error, operator must use a different bin |
| Bin already released | `validate_bin` returns "already released" | Inline error |
| Weight tolerance exceeded | `validate()` issues msgprint | Yellow warning banner (soft block, operator can still submit) |
| Submit failure (any target) | `finalStatus = 'Failed'` or `'Partial Success'` | Status modal shows per-target failure; "Retry" button per row |

## What this component does NOT do

- It does **not** repeat the inspection prerequisite check — `validate_lot_number`
  already enforces Line + Patrol existence before the form is shown
- It does **not** create the Stock Entry itself — this happens in the legacy
  `on_submit` controller and Ops TransactionEngine
- It does **not** manage bin state — BBI/IBM updates happen in `update_bins()`
  after SE submit
- It does **not** handle the injection detection itself — `is_injection_moulding`
  is derived from workstation name in the legacy `validate()` call

## Key UX constraints from legacy behavior

1. **Balance bin required if `no_balance_bin = 0`**: The form must enforce at least
   one balance bin row before submit
2. **Injection fields mandatory only when `is_injection_moulding = 1`**: Show
   `purged_compound` + `compound_leakage` fields only for injection presses
3. **Soft tolerance warning**: The tolerance check issues a `frappe.msgprint()`
   but does not block submission — the Dash must not convert this to a hard
   block
4. **Operator + supervisor scan**: Both are separate barcode scans; supervisor
   scan is optional depending on SPP Settings designation mapping
5. **Moulding date cannot be future**: `validate()` blocks `moulding_date > today`