# 02 - Frontend Dash

> Shared `initialize_submission` / `execute_submission_step` orchestration is documented in [`../master-batch-mixing/02-frontend-dash.md`](../master-batch-mixing/02-frontend-dash.md). Bulk Clip Release uses the same frontend orchestration shape, but its payload is much smaller.

## Component

| File | Role |
|---|---|
| `/Users/alphaworkz/frappe-bench/apps/shree_polymer_console/dash/src/components/processes/BulkClipReleaseEntry.tsx` | Scan and release many clips in one batch |

## State model

| State | Meaning |
|---|---|
| `scannedClips` | Draft list of clips queued for release |
| `barcodeInput` | Scanner input |
| `operator` | Selected Mill Operator |
| `isvalidating` | Per-scan validation in flight |
| `isSubmitting` | Target execution in flight |
| `submissionResult` | Modal status for Legacy/Ops legs |

`ScannedClip` is intentionally small:

| Field | Source |
|---|---|
| `clip_name` | Scanned barcode text |
| `compound` | Console mapping `compound` |
| `spp_batch_number` | Console mapping `spp_batch_number` |
| `qty` | Active mapping qty |

## Scan flow

| Step | Behavior |
|---|---|
| 1 | Require operator before enabling input |
| 2 | Block duplicate `clip_name` already in `scannedClips` |
| 3 | Call `validate_clip_barcode` with current draft barcodes |
| 4 | On `ok`, append clip to draft list |
| 5 | Display compound, batch, qty |

The validator call:

```ts
validateClip({
  barcode,
  draft_barcodes: JSON.stringify(scannedClips.map(c => c.clip_name))
})
```

This is a good pattern: duplicate rejection happens both in Dash and in the backend helper.

## Payload shape

Current Dash submit payload:

```ts
const payload = {
  metadata: {
    process_type: 'BULK_CLIP_RELEASE',
    reference_id: `BCR-${Date.now()}`,
    run_as: operator
  },
  release_data: {
    clips: scannedClips.map(c => c.clip_name)
  }
}
```

## Critical drift: `process_type` vs `process_code`

`build_transaction_payload` requires:

```python
process_code = metadata.get("process_code")
if not process_code:
    raise ValueError("Missing process_code in metadata")
```

Dash currently sends `metadata.process_type`, not `metadata.process_code`. The Wave 2 plan explicitly said to verify BCR submits with `process_code: "BULK_CLIP_RELEASE"`. This is a likely live wiring bug unless another wrapper mutates the payload before it reaches `initialize_submission`.

## Critical drift: payload vs Console doctype fields

| Console doctype wants | Dash sends |
|---|---|
| `release_date` | not sent |
| `released_from_warehouse` | not sent |
| `released_to_warehouse` | not sent |
| `operator_id` | `metadata.run_as` |
| `released_clips[]` with row detail | `release_data.clips[]` barcode strings |

This is acceptable only if the orchestration path never tries to create `Console Bulk Clip Release` from the raw Dash payload. But the existence of the Console doctype/controller implies the intended cockpit path should create it. That local-create bridge is currently missing.

## UI drift

There is a duplicate `className` attribute on the "Reset Entire Queue" button in the TSX. That is frontend cleanup, not cockpit work, but it should be flagged as test/lint drift.

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add `process_code` next to `process_type` | Low/high-value; needs test |
| Switch to `submit_bulk_release_clips` wrapper | Medium; bypasses live feedback modal shape |
| Expand payload to match `Console Bulk Clip Release` fields | Medium; requires backend local-create path |
| Remove `draft_barcodes` validation | Medium; duplicate safety weakens |
