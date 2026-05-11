# 02 — Frontend (Dash) — `FinalBatchMixingEntry.tsx`

**File:** `apps/shree_polymer_console/dash/src/components/processes/FinalBatchMixingEntry.tsx`

> Refer to [`../master-batch-mixing/02-frontend-dash.md`](../master-batch-mixing/02-frontend-dash.md)
> for the full pattern. FB's component mirrors MB's structure: same three
> phases (`initial` → `scanning` → `complete`), same `useProcessTemplate` /
> `useUserInfo` hooks, same Live Feedback submit flow with parallel
> `Promise.all([executeSubmissionStep(legacy), executeSubmissionStep(ops)])`.

## Deltas from MB Dash

### 1. Different default item group

```tsx
// MB:
const allowedItemGroups = getStepValidations('Produced Item')?.item_groups || ['Master Batch']
// FB:
const allowedItemGroups = getStepValidations('Produced Item')?.item_groups || ['Compound']
```

The Console Process Template for `FINAL_BATCH_MIXING` has a step validation
row that explicitly sets `item_groups: ["Compound"]`. The component falls
back to that default if the template is missing the row.

### 2. Extra MB scan step

The FB component has an additional scan input **before** the regular raw
material scan loop:

```tsx
// FB-specific state
const [scannedMasterBatch, setScannedMasterBatch] = useState<{
    mix_barcode: string
    spp_batch_no: string
    item_code: string  // the MB item code
    batch_no: string
    qty: number
    warehouse: string
} | null>(null)

const handleMasterBatchScan = async (barcode: string) => {
    // calls validate_rm_barcode with expected_item_group="Master Batch"
    const result = await validateBarcode({ barcode, expected_item_group: "Master Batch" })
    if (result.message?.status === "failed") {
        setError(result.message.message)
        return
    }
    setScannedMasterBatch(result.message.batch_info)
    // MB consumption is auto-appended to scannedItems as the first row
    setScannedItems([result.message.batch_info, ...scannedItems])
}
```

This means the operator's flow is:
1. Scan operator badge
2. Select produced Compound item
3. **Scan MB lot barcode** ← new step
4. Scan each additional raw material from the BOM
5. Enter produced qty + submit

### 3. Payload shape — MB row in `consumption_items`

The FB `generatePayload` produces the same canonical shape as MB, but the
first row of `consumption_items` is the **MB lot being consumed**:

```tsx
stock_entry_data: {
    consumption_items: [
        // First row: the scanned MB
        {
            item_code: scannedMasterBatch.item_code,    // the MB FG item
            qty: scannedMasterBatch.qty,
            batch_no: scannedMasterBatch.batch_no,
            spp_batch_number: scannedMasterBatch.spp_batch_no,
            mix_barcode: scannedMasterBatch.mix_barcode,
            s_warehouse: scannedMasterBatch.warehouse,
            is_finished_item: 0,
            // Critical: tells legacy this is the MB input, not a raw material
            is_batch_item: 1,   // ← FB-only field
        },
        // Subsequent rows: regular raw materials (same shape as MB Mixing)
        ...scannedItems.slice(1).map(...)
    ],
    ...
}
```

**The `is_batch_item: 1` flag** drives legacy's `validate_final_batches`
branching. When the DCR's `dc_items` has at least one row with
`is_batch_item == 1`, the legacy controller takes the "batched FB
mixing" path (`create_master_batch_stock` + `create_compound_stock`)
instead of the simpler "non-batched FB" path
(`create_wo_final_batch_mixing`).

### 4. Different `metadata.item_group`

```tsx
metadata: {
    process_type: template?.template_name || "Final Batch Mixing",
    process_code: processCode,   // "FINAL_BATCH_MIXING"
    entry_role: getStepValidations('Operator')?.required_role || "Mixing Operator",
    produced_item: producedItem,
    item_group: "Compound",   // not "Master Batch"
}
```

`build_transaction_payload` reads this and sets `is_compound = (item_group == "Compound")`
which drives different warehouse resolution logic in the template.

## Same as MB Mixing — refer to MB spec

- Operator scan validation against role
- BOM fetch + render
- Per-raw-material scan validation via `validate_rm_barcode`
- Live Feedback Promise.all submission flow
- Retry button rebuilds `req_params` from log
- Error/loading/empty states
- Backdating UX (only System Manager / Administrator)
- Barcode label rendering + print dialog

## Where to extend safely

Same advice as MB: add field → state → `generatePayload` → backend `_pick`
path → Console doctype JSON → mapping seeder → run all tests.

The one extra consideration for FB: any change that touches the MB-input
row (`is_batch_item`, `mix_barcode`) ripples through to legacy's
`validate_final_batches` branching. Test on staging with both paths
(batched + non-batched) before pushing.
