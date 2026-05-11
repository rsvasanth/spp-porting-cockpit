# 09 - Rollout and history

## What shipped

| Area | Status |
|---|---|
| Console doctype | Exists with meaningful validation and callback logic |
| Console child doctype | Exists as `Console Clip Release Item` |
| Dash component | Exists and is wired to live-feedback orchestration |
| Console scan validator | Exists and is tested |
| Ops handler | Exists as dedicated barcode-list function |
| Legacy doctype | Exists and retires mappings by mapping id |
| Bridge helper | Exists as direct barcode-list retire function |

## What is not cleanly wired

| Gap | Why it matters |
|---|---|
| Dash sends `process_type`, not `process_code` | `build_transaction_payload` can fail before target logs |
| No `create_local_bulk_clip_release` | Console audit row may never be created from Dash flow |
| No `BULK_CLIP_RELEASE` callback map | BCR controller callback may never run |
| Mapping seeder child fields drift from Legacy JSON | Legacy document path may not create usable child rows |

## Hermes boundaries

| Area | This spec task |
|---|---|
| Write cockpit docs | Yes |
| Change Dash/API/Bridge/Ops code | No |
| Execute bench migrations | No |
| Run full tests | No, unless user explicitly asks |
| Provide exact test commands | Yes |

## Recommended next code workstream

When the user asks for implementation, do it as a dedicated BCR wiring task:

| Step | Goal |
|---|---|
| 1 | Fix Dash payload to include `metadata.process_code` |
| 2 | Add `create_local_bulk_clip_release` or route through existing direct helper deliberately |
| 3 | Add `BULK_CLIP_RELEASE` to `update_local_domain_record` |
| 4 | Fix Bridge mapping or add populate resolver |
| 5 | Add tests for barcode/doc-name drift |

## Current recommendation

Treat Bulk Clip Release as **not cockpit-clean yet**. The source has the right pieces, but not enough proof that the live Dash path exercises the rich Console doctype and callback safely.
