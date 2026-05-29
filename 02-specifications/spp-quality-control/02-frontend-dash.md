# 02 — Frontend (Dash) specification

## Surface

Path: `dash/src/components/processes/SPPQualityControlEntry.tsx`
Registered in `dash/src/lib/processRegistry.tsx` under the appropriate `inspection_type` keys.

## Layout

```
+--------------------------------------------------------------------------------+
|  SPP Quality Control                                                           |
+--------------------------------------------------------------------------------+
|  Inspector Scan: [=== Employee Badge Barcode ===]   (Inspector Name)           |
|  Operator Scan:  [=== Employee Badge Barcode ===]   (Operator Name)            |
|  Scan Lot:       [=== Lot Number Barcode ===]       (Item / Job Card)          |
+--------------------------------------------------------------------------------+
|  Inspection Type: [ Line v ]                                                   |
+--------------------------------------------------------------------------------+
|  Dynamic Testing Specifications — Template: <template_name>                    |
|  Last Synced: <timestamp>                                                      |
|                                                                                |
|  Parameter       | Nom        | Min        | Max        | Measured             |
|  ----------------|------------|------------|------------|--------------------- |
|  Hardness        | 70         | 65         | 75         | [ 68.0 ]   (green)   |
|  Specific Grav.  | 1.15       | 1.12       | 1.18       | [ 1.19 ]   (red)     |
|  TS2             | 1.80       | 1.50       | 2.10       | [ 1.75 ]   (green)   |
+--------------------------------------------------------------------------------+
|  Inspected (Nos): [ 100 ]   Rejected (Nos): [ 5 ]                              |
|  Piece Wt (Kg):   [ 0.050 ] Rejected (Kg):  [ 0.250 ]                          |
+--------------------------------------------------------------------------------+
|                                    [ SUBMIT INSPECTION ]                       |
+--------------------------------------------------------------------------------+
```

## Scan focus management

- Page mount: focus on Inspector Scan input.
- On Inspector scan complete (Tab or Enter): focus moves to Operator Scan input.
- On Operator scan complete: focus moves to Lot Scan input.
- On Lot scan resolved successfully: focus moves to the first `reading_value` input in the parameter grid.
- On final reading entered: focus moves to the Submit button.

The entire flow must be completable with a keyboard-wedge scanner (no mouse).

## Color rules

- `reading_value` within `[min_value, max_value]` (inclusive) → green border + green icon.
- Outside the range → red border + red icon.
- Empty / non-numeric → neutral.
- Color is presentational ONLY. Backend recomputes `reading_status` at submit.

## Template-missing block

When the Lot scan resolves to an Item without an active template, render a modal:

```
+------------------------------------------------------+
|  No active Quality Template configured for Item      |
|  [Item Code].                                        |
|                                                      |
|  Action halted. Please configure the template on     |
|  the Ops site first.                                 |
|                                                      |
|  Cached templates last synced: <timestamp>           |
|                                                      |
|  [ Sync templates now ]    [ Dismiss ]               |
+------------------------------------------------------+
```

"Sync templates now" calls the on-demand sync endpoint, refreshes the cache, and re-checks. If still missing, the modal redisplays with updated `last_synced` timestamp.

## State machine (client-side)

```
idle → scanning_inspector → scanning_operator → scanning_lot → resolving
                                                              ├─→ template_missing (block modal)
                                                              └─→ ready (parameter grid)
                                                                       │
                                                              entering_readings
                                                                       │
                                                                  submitting
                                                                       ├─→ success (toast + reset)
                                                                       └─→ failed (error banner + retry)
```

## Data layer

Use `useFrappePostCall` from `frappe-react-sdk` for submission, `useFrappeGetDocList` for template lookups. Match the pattern in `MouldingProductionEntry.tsx`. Do NOT use the legacy `frappe.db` lib.

## Accessibility

- All inputs have visible labels (not placeholder-only).
- Color is supplemented by an icon (✓ / ✗) for color-blind users.
- Touch targets ≥48px.
