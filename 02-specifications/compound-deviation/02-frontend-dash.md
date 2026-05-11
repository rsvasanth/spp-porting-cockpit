# 02 — Frontend (Dash) — `CompoundDeviationEntry.tsx`

**File:** `apps/shree_polymer_console/dash/src/components/processes/CompoundDeviationEntry.tsx`

> Read [`../master-batch-mixing/02-frontend-dash.md`](../master-batch-mixing/02-frontend-dash.md)
> for the shared scaffold (state model, Live Feedback flow, retry, error states).
> Deviation's UX differs in **what data the operator provides** but not in
> **how submission orchestrates**.

## Flow summary

```
Open Compound Deviation Entry
   │
   ▼
Scan or search for the rejected Compound (by mix_barcode)
   ├─► Fetches source Compound Inspection: GET get_rejected_compound_inspection(mix_barcode)
   ├─► Display source CI's readings as read-only context
   └─► Block submit if no rejected CI found OR if CI is not Rejected
   ▼
Scan QM badge
   ├─► Validates against get_available_employees(required_role="Quality Manager")
   └─► Sets approver_id + approver_name
   ▼
Select Status from dropdown: Accepted / Rejected / Rework
   ▼
Enter Deviation Reason (textarea, min 5 chars)
   ▼
Optionally edit qty (defaults to source CI's transfer_qty)
   ▼
Submit
   ├─► initializeSubmission({ payload })
   ├─► Promise.all([executeSubmissionStep(...) per target])
   └─► Success modal — same as MB Mixing
```

## State delta from MB

```tsx
// Identity (from source CI)
const [sourceCi, setSourceCi] = useState<RejectedCIBlock | null>(null)
const [mixBarcode, setMixBarcode] = useState<string>('')

// QM signoff
const [approverId, setApproverId] = useState<string>('')
const [approverName, setApproverName] = useState<string>('')

// Decision
const [status, setStatus] = useState<'Accepted' | 'Rejected' | 'Rework'>('Accepted')
const [deviationReason, setDeviationReason] = useState<string>('')
const [qty, setQty] = useState<string>('')   // defaults to source CI's transfer_qty
```

Where `RejectedCIBlock` is the fetched body of the source Compound
Inspection — `item_code`, `batch_no`, `spp_batch_no`, `mix_barcode`,
`scan_compound`, `transfer_qty`, `batch_qty`, `operator_name`, all the
QC reading rows, etc.

## Backend calls

| Call | When | Purpose |
|---|---|---|
| `get_rejected_compound_inspection(mix_barcode)` | On barcode scan | Finds the Console Inspection (or pre-Phase-3 Console Compound Inspection) with `status="Rejected"` and matching `mix_barcode`. Returns the full body for read-only display. |
| `get_available_employees(required_role="Quality Manager")` | Component mount | List of QMs |
| `initialize_submission` | On submit | Standard pattern |
| `execute_submission_step` | Once per target | Standard pattern |

## Payload shape — `generatePayload()`

Different blocks from MB Mixing. No `stock_entry_data`, no
`work_order_data`. Instead:

```tsx
return {
    reference_id: referenceID,
    metadata: {
        process_type: "Compound Deviation",
        process_code: "COMPOUND_DEVIATION",
        entry_role: "Quality Manager",
    },
    config: {
        legacy_source_warehouse: sourceCi.source_warehouse,    // e.g. "Compound Inspection Warehouse - SPP"
        legacy_target_warehouse: legacyTargetWarehouse,        // depends on status
        ops_source_warehouse:    opsSourceWarehouse,
        ops_target_warehouse:    opsTargetWarehouse,
        operation: "Compound Inspection",
        scan_barcode: sourceCi.mix_barcode,
    },
    // The CI identity block (matches the shape of an Accepted CI payload)
    compound_inspection_data: {
        item_code:        sourceCi.item_code,
        batch_no:         sourceCi.batch_no,
        spp_batch_no:     sourceCi.spp_batch_no,
        mix_barcode:      sourceCi.mix_barcode,
        scan_compound:    sourceCi.mix_barcode,
        compound_ref:     sourceCi.compound_ref,
        dc_receipt_id:    sourceCi.dc_receipt_id,
        transfer_qty:     parseFloat(qty) || sourceCi.transfer_qty,
        batch_qty:        sourceCi.batch_qty,
        operator_id:      sourceCi.operator_id,
        operator_name:    sourceCi.operator_name,
        cavity_no:        sourceCi.cavity_no,         // see 10-risks: often missing
        readings:         sourceCi.readings,          // full reading rows
    },
    // The deviation-specific block
    compound_deviation_data: {
        status:           status,                     // QM's decision
        approver_id:      approverId,
        approver_name:    approverName,
        deviation_reason: deviationReason,
        qty:              parseFloat(qty) || sourceCi.transfer_qty,
        source_warehouse: sourceCi.source_warehouse,  // used by WAREHOUSE_MAP fallback
        operator_id:      sourceCi.operator_id,
        operator_name:    sourceCi.operator_name,
        posting_date:     format(new Date(), 'yyyy-MM-dd'),
        inspection_time:  format(new Date(), 'HH:mm'),
    },
    mix_barcode: sourceCi.mix_barcode,
}
```

**The two-block pattern is the architectural pivot from the saga.**
Before 2026-04-30, the payload only had `compound_deviation_data` and
the Bridge had its own ~200 lines of identity resolution that drifted
from the CI shape. The fix: emit `compound_inspection_data` (same shape
as an Accepted CI) + a thin `compound_deviation_data` (only the
QM-specific bits). The Bridge then runs the **same** identity pipeline
for both Accepted CIs and Deviations.

## Status-driven validation

The Submit button is enabled only when:

```tsx
const canSubmit =
    sourceCi != null
    && sourceCi.status === "Rejected"
    && approverId !== ""
    && status !== ""
    && deviationReason.trim().length >= 5
    && (status !== "Rework" || /* any extra checks */)
```

Status `Rework` doesn't change the submit gate beyond the standard
checks; the routing logic in `initialize_submission` handles the
status-conditional target selection (see `04-bridge-layer.md`).

## Same as MB Mixing

- Live Feedback Promise.all submit flow
- Retry from log UI
- Error states + loading spinner
- Backdating for System Manager / Administrator
- Success modal with per-target status indicators

## Where to extend safely

If a Hermes worker needs to add a field:
1. Determine which block it belongs in:
   - Identity (matches an Accepted CI) → `compound_inspection_data`
   - QM signoff / decision → `compound_deviation_data`
2. Add to component state + form UI
3. Include in `generatePayload`
4. Add corresponding `_pick` path in
   `api.py::create_local_compound_deviation`
5. If the field needs to land on legacy: update
   `populate_compound_deviation_fields` in the Bridge — **NOT** the
   `Legacy Sync Mapping` field_mappings (which stays empty for this
   process)
6. Run unit tests + concurrency test + one staging E2E
