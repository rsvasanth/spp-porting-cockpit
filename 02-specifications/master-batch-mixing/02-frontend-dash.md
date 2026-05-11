# 02 — Frontend (Dash) — `MasterBatchMixingEntry.tsx`

**File:** `apps/shree_polymer_console/dash/src/components/processes/MasterBatchMixingEntry.tsx`
**Size:** 1068 lines
**Stack:** React 18 + TypeScript + Vite, using `frappe-react-sdk` for backend calls and Tailwind + shadcn/ui for the UI.

The component is registered in `dash/src/components/processes/processRegistry.tsx`
under the key `MASTER_BATCH_MIXING` and is mounted by the parent
`ProcessRouter` when an operator picks Master Batch Mixing from the
Dashboard.

## Layout — what the operator sees

The screen has **three phases** controlled by the `currentStep` state:

| Phase | State value | What's visible |
|---|---|---|
| Initial | `'initial'` | Operator + Produced Item selectors, Start Date/Time |
| Scanning | `'scanning'` | BOM panel with raw-material rows + barcode scan inputs |
| Complete | `'complete'` | Produced qty input + "Submit to ERP" button |

Within each phase, a top `ProcessHeader` bar shows process metadata,
warehouse config from the `Console Process Template`, and the End-Mix date
picker.

## State model — every field captured

```tsx
// Form Data
const [startDate, setStartDate] = useState<string>(format(new Date(), 'yyyy-MM-dd'))
const [startTime, setStartTime] = useState<string>(format(new Date(), 'HH:mm'))
const [endDate, setEndDate] = useState<string>('')
const [endTime, setEndTime] = useState<string>('')
const [operator, setOperator] = useState<string>('')                 // employee_id
const [operatorName, setOperatorName] = useState<string>('')
const [producedItem, setProducedItem] = useState<string>('')         // Console Item name
const [producedQty, setProducedQty] = useState<string>('')           // Kg, parseFloat'd on submit

// Process State
const [bomInfo, setBomInfo] = useState<BOMInfo | null>(null)
const [scannedItems, setScannedItems] = useState<any[]>([])          // raw materials scanned
const [workstation, setWorkstation] = useState<string>('')           // resolved from template
const [operation, setOperation] = useState<string>('')               // "Master Batch Mixing"
const [mixBarcode, setMixBarcode] = useState<string>('')             // Console-generated C_YYMMDDXn
const [barcodeImageUrl, setBarcodeImageUrl] = useState<string>('')   // PNG data URL for print

// Submission State
const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
const [showSuccessModal, setShowSuccessModal] = useState<boolean>(false)
const [submissionResult, setSubmissionResult] = useState<SubmissionResult | null>(null)
const [currentReferenceID, setCurrentReferenceID] = useState<string>('')
```

The `currentReferenceID` is generated **lazily** on first submit by
`Date.now().toString()` (13-digit ms timestamp). It becomes the
cross-system idempotency key passed through every downstream layer.

## Backend calls the component makes

| Call | Purpose | When |
|---|---|---|
| `get_available_employees` | Lists employees with the required role (default `Mixing Operator`) | Component mount |
| `get_available_items` | Lists Console Items in allowed item groups (default `['Master Batch']`) | Component mount |
| `get_bom_for_produced_item` | Fetches BOM rows for the selected MB item | On Produced Item selection |
| `validate_rm_barcode` | Validates a scanned raw-material barcode against the BOM | On each scan |
| `generate_compound_mix_barcode` | Server-generates the C_YYMMDDXn barcode | Just before submit |
| `get_final_payload` | (Preview only) returns the canonicalised payload Console will send | On "Preview Payload" click |
| `initialize_submission` | Step 1 of two-step submit — see `03-console-backend.md` | On "Submit to ERP" |
| `execute_submission_step` | Step 2 — called once per target (Legacy, Ops) **in parallel** | After initialize |
| `save_mixing_label` | Persists the printed-label record | After successful submit |

## Operator scan flow

```
Operator scans badge
   │
   ▼
handleOperatorSelect(employee_id)
   ├─► validates against availableEmployees list (must have Mixing Operator role)
   ├─► auto-focuses Produced Item dropdown
   ▼
Operator picks Produced Item
   ├─► handleProducedItemSelect(item_code)
   ├─► calls fetchBOM({ produced_item }) → returns BOMInfo
   ├─► sets workstation + operation from BOM
   ├─► renders BOMPanel with one row per raw material expected
   ▼
For each raw material:
   ├─► Operator scans barcode
   ├─► validateBarcode({ barcode, expected_item_code, expected_qty }) → server check
   ├─► server returns { item_code, batch_no, spp_batch_no, qty, warehouse }
   ├─► row added to scannedItems[]
   ▼
When all BOM rows scanned:
   ├─► currentStep = 'complete'
   ▼
Operator enters Produced Qty (Kg)
   ├─► Operator clicks "Submit to ERP"
   ▼
handleSubmit()
```

### Backdating UX

The component allows backdating only for System Manager / Administrator
roles (the `isSystemManager`, `isAdministrator` flags come from
`useUserInfo`). For regular operators, the Start Date is clamped to
"today or yesterday" by the `handleCompleteMixing` logic:

```tsx
if (start < minDate && !isSystemManager && !isAdministrator) {
    setError('Date can be -1 day or today only')
    return
}
const isBackDated = start < new Date(now.getTime() - 1000 * 60 * 60)
if (isBackDated && (isSystemManager || isAdministrator)) {
    // Respect the manually selected start date/time as the posting time too
    setEndDate(startDate); setEndTime(startTime); setDuration(30)
} else {
    // Normal flow: End time is "now"
    setEndDate(format(now, 'yyyy-MM-dd')); setEndTime(format(now, 'HH:mm'))
}
```

The end date/time becomes `stock_entry_data.posting_date` /
`posting_time` in the payload, which the backend reads via `_backdate_fields`.

## The payload builder — `generatePayload(overrideMixBarcode?)`

This is the most important function in the file. It produces the shape that
the entire backend stack reads. **The Bridge mapping (`04-bridge-layer.md`),
Console backend (`03-console-backend.md`), and Ops engine
(`06-ops-erpnext.md`) all assume this shape.** Changes here ripple
everywhere.

Verbatim from `MasterBatchMixingEntry.tsx:409`:

```tsx
const generatePayload = (overrideMixBarcode?: string) => {
    if (!bomInfo || !operator || !producedItem || !producedQty) return null
    const activeMixBarcode = overrideMixBarcode ?? mixBarcode
    const referenceID = currentReferenceID || Date.now().toString()

    const primaryStep = template?.steps?.find(s => s.is_primary_input);
    let primaryItem = scannedItems[0];  // primary input is the first scanned item

    const itemsList = Array.isArray(availableItems) ? availableItems : (availableItems as any)?.message
    const selectedItemData = Array.isArray(itemsList) ? itemsList.find((i: any) => i.name === producedItem) : null
    const itemGroup = selectedItemData?.item_group || ''

    return {
        reference_id: referenceID,
        metadata: {
            process_type: template?.template_name || "Master Batch Mixing",
            process_code: processCode,
            entry_role: getStepValidations('Operator')?.required_role || "Mixing Operator",
            produced_item: producedItem,
            item_group: itemGroup,
        },
        config: {
            source_warehouse:        opsSourceWarehouse,
            target_warehouse:        opsTargetWarehouse,
            wip_warehouse:           opsWipWarehouse,
            legacy_source_warehouse: legacySourceWarehouse,
            legacy_target_warehouse: legacyTargetWarehouse,
            legacy_wip_warehouse:    legacyWipWarehouse,
            operation: operation,
            scan_barcode: primaryItem?.mix_barcode || referenceID,
        },
        work_order_data: {
            item_to_manufacture: producedItem,
            qty_to_manufacture: parseFloat(producedQty),
            bom_no: bomInfo.bom.name,
            planned_start_date: `${startDate} ${startTime}`,
            reference_id: referenceID,
            referenceid: referenceID,    // legacy alt spelling kept for compat
            duration: duration,
            workstation: workstation,
            operation: operation,
        },
        job_card_data: {
            employee_code: operator,
            completed_qty: parseFloat(producedQty),
            start_time: `${startDate} ${startTime}`,
            end_time: `${endDate} ${endTime}`,
            workstation: workstation,
            operation: operation,
        },
        stock_entry_data: {
            posting_date: endDate,
            posting_time: endTime,
            fg_item: producedItem,
            fg_qty: parseFloat(producedQty),
            consumption_items: scannedItems.map(item => ({
                item_code: item.item_code,
                qty: item.qty,
                batch_no: item.batch_no,
                spp_batch_number: item.spp_batch_no,
                mix_barcode: item.mix_barcode || item.barcode,
                s_warehouse: item.warehouse,
                is_finished_item: 0
            })),
            items: [
                // raw materials (consumption rows)
                ...scannedItems.map(item => ({ /* same shape + allow_zero_valuation_rate: 1 */ })),
                // finished good
                {
                    item_code: producedItem,
                    qty: parseFloat(producedQty),
                    t_warehouse: opsTargetWarehouse,
                    is_finished_item: 1,
                    spp_batch_number: activeMixBarcode,
                    mix_barcode: activeMixBarcode,
                    barcode_attach: activeMixBarcode,
                    barcode_text: activeMixBarcode,
                    allow_zero_valuation_rate: 1
                }
            ]
        },
        mix_barcode: activeMixBarcode,
    }
}
```

**Key points about this shape:**

| Property | Why it's there |
|---|---|
| `reference_id` at top level + in `metadata` + in `work_order_data` | Backward compat — different consumers read it from different paths |
| Duplicate `referenceid` (no underscore) in `work_order_data` | Legacy alt spelling preserved for old Bridge mapping rows |
| `config.scan_barcode` falls back to `referenceID` when primary item has no barcode | Defensive — used downstream by legacy DCR's `scan_barcode` field |
| `stock_entry_data.items` includes BOTH consumption AND FG | Generic mapping path; `consumption_items` is the strict subset |
| `stock_entry_data.consumption_items` is the dedicated raw-material list | Used by `_normalize_items(_, _MIXING_ITEM_KEYMAP)` in Console backend |
| FG row has `barcode_attach` + `barcode_text` + `mix_barcode` + `spp_batch_number` all set to the same value | Different downstream consumers read different fields; all populated for safety |
| `t_warehouse` is in **Ops** namespace (`opsTargetWarehouse`) | Ops engine reads this; Legacy gets warehouses via the `config.legacy_*` block |

## Submit flow — `handleSubmit()`

Verbatim from `MasterBatchMixingEntry.tsx:633`:

```tsx
const handleSubmit = async () => {
    setIsSubmitting(true)
    setError('')
    try {
        // Resolve mix barcode (may already be set; if not, derive from primary scan)
        let generatedBarcode = mixBarcode
        if (!generatedBarcode && scannedItems.length > 0) {
            const primary = scannedItems[0]
            generatedBarcode = primary.mix_barcode || primary.barcode || primary.spp_batch_no || ""
            setMixBarcode(generatedBarcode)
        }

        const payload = generatePayload(generatedBarcode)
        if (!payload) throw new Error('Failed to build payload')

        // Step 1: tell backend to lock down reference_id + create per-target logs
        const initApiResult = await initializeSubmission({ payload })
        const initResult = initApiResult?.message || initApiResult
        if (initResult?.status !== 'Success') throw new Error(initResult?.message || 'Failed to initialize submission')

        const { target_logs, reference_id } = initResult
        setSubmissionResult({
            status: 'Processing',
            reference_id,
            results: target_logs.map((tl: any) => ({ target: tl.target, status: 'Pending' }))
        })
        setShowSuccessModal(true)

        // Step 2: fire all targets IN PARALLEL via Promise.all
        const submissionPromises = target_logs.map(async (logInfo: any) => {
            try {
                setSubmissionResult(prev => ({
                    ...prev,
                    results: prev.results.map(r =>
                        r.target === logInfo.target ? { ...r, status: 'Processing' } : r
                    )
                }))
                const stepApiResult = await executeSubmissionStep({
                    log_name: logInfo.log_name, target_info: logInfo
                })
                const stepResult = stepApiResult?.message || stepApiResult
                const individualResult = { target: logInfo.target, status: stepResult.status, result: stepResult.result }
                setSubmissionResult(prev => ({
                    ...prev,
                    results: prev.results.map(r => r.target === logInfo.target ? individualResult : r)
                }))
                return individualResult
            } catch (stepErr) {
                return { target: logInfo.target, status: 'Failed',
                         result: { message: { status: 'Failed', message: stepErr.message || String(stepErr) } } }
            }
        })

        const finalResults = await Promise.all(submissionPromises)
        const finalStatus = finalResults.every(r => r.status === 'Success') ? 'Success' :
                            finalResults.some(r => r.status === 'Success')  ? 'Partial Success' : 'Failed'

        setSubmissionResult(prev => ({ ...prev, status: finalStatus, results: finalResults,
            impacted_balances: finalResults.find(r => r.target === 'Ops' || r.target === 'Legacy')
                ?.result?.impacted_balances || [] }))
    } catch (err) {
        setError(err.message || String(err))
        setShowSuccessModal(false)
    } finally {
        setIsSubmitting(false)
    }
}
```

**This is the Live Feedback pattern.** The operator sees each target's
status flip individually (`Pending → Processing → Success/Failed`) — not
a single spinner that resolves "everything done." Critical for trust
in shop-floor UX.

## Retry behavior

If one target fails, the `submissionResult.status` becomes `Partial Success`.
The success modal stays open showing per-target status. The component **does
not auto-retry** failed targets — the operator clicks "Retry Failed" which
calls `executeSubmissionStep` again with the same `log_name`. The backend's
`execute_submission_step` has a "RETRY FLOW FIX" that rebuilds `req_params`
from the stored `Console Transaction Log.request_payload`, so retries are
idempotent (see `03-console-backend.md`).

## Error and empty states

| State | Trigger | UI |
|---|---|---|
| Template loading | `isLoading === true` from `useProcessTemplate` | Centered spinner, "Loading production template..." |
| Template not found | `!template` after load | Red alert + "Back to Dashboard" button |
| BOM fetch failed | `bomInfo === null` after select | Red alert, scanning blocked |
| Barcode rejected | `validate_rm_barcode` returns error | Inline error row in BOMPanel; operator must rescan |
| Submit failure (any target) | `finalStatus === 'Failed'` or `'Partial Success'` | Status modal shows per-target failure; "Retry" button per row |
| Network drop during execute | catch block in submissionPromise | Target row shows red "Failed" with error string |

## What this component does NOT do

- It does **not** generate the mix barcode itself — it asks the backend
  via `generate_compound_mix_barcode`. (The backend has the date/sequence
  state; client-side generation would risk collisions across operators.)
- It does **not** call legacy or ops directly — it only talks to Console's
  `api.py` and lets `execute_submission_step` proxy out to each target.
- It does **not** persist any state locally (no IndexedDB / localStorage).
  An accidental browser refresh mid-submit loses the in-memory state, but
  the `reference_id` is already locked into `Console Transaction Log` so
  the operator can resume by finding the log entry.

## Where to extend it safely

If a Hermes worker needs to add a field:
1. Add to component state + Form UI
2. Include in `generatePayload` return shape
3. Add corresponding `_pick` path in `api.py::create_local_master_batch_mixing`
4. Update Console doctype JSON if it should be stored on `Console Master Batch Mixing`
5. Update `console_mapping_seeder.py` if it should flow to Legacy DCR
6. Run all unit tests + one end-to-end staging submission before merging
