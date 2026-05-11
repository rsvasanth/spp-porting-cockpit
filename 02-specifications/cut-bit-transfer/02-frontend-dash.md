# 02 - Frontend Dash

> Shared submit orchestration is documented in [`../master-batch-mixing/02-frontend-dash.md`](../master-batch-mixing/02-frontend-dash.md). Cut Bit's Dash delta is the scan-list payload built by `CutBitTransferEntry.tsx`.

## Component

| File | Role |
|---|---|
| `/Users/alphaworkz/frappe-bench/apps/shree_polymer_console/dash/src/components/processes/CutBitTransferEntry.tsx` | Operator UI for scanning Clip/Bin assets and submitting CBT |

## State model

| State | Meaning |
|---|---|
| `scannedAssets` | Current Clip/Bin rows staged for one transfer |
| `barcodeInput` | Scanner input field |
| `operator` | Console Employee selected from Blanker list |
| `isValidating` | Scan validation in flight |
| `isSubmitting` | Orchestration submit in flight |
| `completedAssetCount` | Success-modal metric captured before clearing rows |

`ScannedAsset` carries the fields downstream systems need:

| Field | Source |
|---|---|
| `asset_id` | Validation response; usually physical barcode or resolved asset name |
| `asset_type` | `Clip` or `Bin` |
| `mapping_name` | Active mapping row |
| `item_code` / `item_name` | Mapped compound item |
| `spp_batch_number` | Console/legacy trace key |
| `native_batch_no` | Ops-native ERPNext batch when known |
| `available_qty` | Max operator can transfer |
| `source_warehouse` | Warehouse resolved by validation layer |

## Employee selection

The component calls:

```ts
get_available_employees({ required_role: 'Blanker', fallback_to_active: 1 })
```

The `fallback_to_active=1` comment is load-bearing. It keeps the screen usable when role data drifts, while leaving a server-side warning so missing `Console Employee.user_id` or missing `Console User.roles` can still be diagnosed.

## Scan flow

| Step | Frontend behavior | Backend called |
|---|---|---|
| 1 | Require operator before scan | n/a |
| 2 | Reject duplicate `asset_id` already in list | n/a |
| 3 | POST barcode for validation | `validate_cut_bit_asset` |
| 4 | On success, prepend row to `scannedAssets` | n/a |
| 5 | Let operator adjust transfer qty per row | n/a |

Validation failure remains local to the screen. No submission row is created until `handleSubmit`.

## Quantity guard

Before submit, Dash rejects any row where:

```ts
a.qty <= 0 || a.qty > a.available_qty
```

This is a frontend guard only. The Console local doctype validates total `qty > 0` for Desk inserts, but `_safe_local_create` bypasses strict validation for audit writes. Ops and Legacy remain the real stock-ledger guards.

## Submit payload

The submitted payload is intentionally compact:

```ts
const payload = {
  metadata: {
    reference_id: `CBT-${Date.now()}`,
    run_as: operator
  },
  items: scannedAssets.map(a => ({
    item_code: a.item_code,
    batch_no: a.native_batch_no,
    native_batch_no: a.native_batch_no,
    spp_batch_number: a.spp_batch_number,
    qty: a.qty,
    asset_id: a.asset_id,
    asset_type: a.asset_type,
    mapping_name: a.mapping_name,
    source_warehouse: a.source_warehouse,
    clip_name: a.asset_id,
  }))
}
```

`clip_name` is deliberately set to the scanned asset id. The Bridge later uses it to populate `scan_barcode` and `sheeting_clip` when flattening `CUT_BIT_TRANSFER` payloads.

## Reference ID shape

| Process | Reference ID |
|---|---|
| Cut Bit Transfer | `CBT-${Date.now()}` |
| Standard MB/FB paths | usually raw `Date.now()` |

Console `initialize_submission` handles this because it reads `reference_id` from top-level context or `metadata.reference_id`. The `submit_cut_bit_transfer` wrapper also hoists it to top-level before calling `submit_process`.

## Submission result UI

The success modal renders `submissionResult.results[]`, one row per target system. This matches the shared Console orchestrator shape: Legacy and Ops can independently succeed/fail while the local audit row aggregates through `apply_bridge_result`.

## Frontend risks

| Risk | Existing guard |
|---|---|
| Duplicate scan in one batch | `scannedAssets.find(a => a.asset_id === barcode)` |
| Operator submits no rows | `scannedAssets.length === 0` check |
| Over-transfer from asset | `qty <= available_qty` check |
| Native batch empty for Console-local clip | Backend wrapper relays to Ops validation at submit time |
| Operator list empty due role drift | `fallback_to_active=1` plus visible warning |

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add row-level display fields | Low |
| Change `reference_id` prefix | Medium; audit/search conventions depend on `CBT-` |
| Remove `clip_name: a.asset_id` | High; Legacy scan resolution uses it |
| Remove native batch relay assumptions | High; Ops handler rejects incomplete item rows |
