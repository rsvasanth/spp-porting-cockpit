# 09 - Rollout and history

## What shipped

| Area | Status |
|---|---|
| Console doctype | Exists |
| Console child doctype | Exists |
| Dash component | Exists and sends `process_code` |
| Console validators | Exist |
| Console local create | Exists |
| Console side effects | Bin mapping write + clip qty deduction |
| Bridge populate function | Exists |
| Legacy doctype | Exists with active Asset Movement path |
| Ops handler | Exists as dedicated Stock Entry handler |

## What is not cockpit-clean

| Gap | Why |
|---|---|
| Callback map omits `BLANKING_DC_ENTRY` | local sync fields do not update |
| Controller callback signature is non-standard | naive map fix will mis-call method |
| Ops and Legacy model different effects | Stock Entry vs Asset Movement/bin mapping |
| Console mapping seeder disagrees with Bridge seeder | field mappings vs populate-only |
| Plan mentions cut-bit branch controls not in Dash | stale planning text |

## Hermes boundaries

| Area | This spec task |
|---|---|
| Write cockpit docs | Yes |
| Patch BDE code | No |
| Run bench tests | No, unless asked |
| Provide exact test plan | Yes |

## Recommended future code workstream

| Step | Goal |
|---|---|
| 1 | Decide whether Ops BDE should remain Cutbit Stock Entry or align to bin mapping |
| 2 | Fix callback routing + method signature together |
| 3 | Add tests for local create side effects |
| 4 | Reconcile Console vs Bridge mapping seeders |
| 5 | Add BOM validation to Console scan if required |

## Current recommendation

Do not treat BDE as fully port-clean until target semantics are decided. The local/Dash/Legacy story is coherent; the Ops story is the question mark.
