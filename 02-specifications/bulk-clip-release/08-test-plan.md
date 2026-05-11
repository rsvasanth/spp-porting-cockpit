# 08 - Test plan

## Console schema tests

Existing test module:

```bash
bench --site sppconsole-dev.local run-tests --module shree_polymer_console.shree_polymer_console.doctype.console_bulk_clip_release.test_console_bulk_clip_release
```

Required assertions:

| Test | Expected |
|---|---|
| Insert with valid rows | `process_code=BULK_CLIP_RELEASE`, `submitted_by` stamped |
| Empty `released_clips` | Validation error |
| Duplicate barcode | Validation error |
| Retired mapping | Validation error |
| Wrong `total_qty` | Recomputed from child rows |
| `validate_clip_barcode` valid clip | Returns `ok=True`, mapping name, qty |
| `validate_clip_barcode` draft duplicate | Returns `ok=False` |

## Routing tests

| Test | Expected |
|---|---|
| Dash-shaped payload with `process_type` only | Should currently fail with missing `process_code`; document until fixed |
| Payload with `metadata.process_code=BULK_CLIP_RELEASE` | `initialize_submission` should create target logs |
| Same payload | Local `Console Bulk Clip Release` row should exist; currently expected to fail |
| Success callback for BCR | `update_local_domain_record` should find BCR doctype; currently expected to fail |

These tests are the highest priority because they prove whether the doctype/controller is wired to the live cockpit path.

## Bridge tests

| Test | Expected |
|---|---|
| Mapping seeder child fields | Match Legacy `Clip Release Item` JSON |
| Bridge direct helper with barcode text != clip doc name | Still retires mapping; currently suspect |
| Bridge direct helper with clip doc name | Retires mapping |
| `sync_process_transaction` document path | Creates valid `Bulk Clip Release` or fails loudly |

## Ops tests

| Test | Expected |
|---|---|
| `validate_clip_for_release` valid barcode | Returns active mapping |
| `validate_clip_for_release` retired clip | Failed |
| `bulk_release_clips` JSON string list | Parses and retires mappings |
| `bulk_release_clips` Python list | Retires mappings |
| Barcode text differs from clip name | Still resolves via `barcode_text` |

## End-to-end smoke

| Step | Expected |
|---|---|
| Create active clip mapping on Console, Ops, Legacy | All validators see active clip |
| Scan in Dash | Clip appears in table |
| Submit BCR | Both target logs execute |
| Verify Console | local mapping retired |
| Verify Ops | Ops mapping retired |
| Verify Legacy | Legacy mapping retired |
| Verify downstream | Material Transfer no longer rejects clip as unreleased |

## UAT checklist

| Check | Pass condition |
|---|---|
| Operator selection | Barcode input enabled |
| Duplicate scan | Clear error, no duplicate row |
| Already released clip | Clear error |
| Success modal | Shows both target systems |
| Start next release | Clears queue |

## Non-code cockpit rule

Do not patch these issues inside the cockpit-writing task. Create separate code/test tasks for the routing and mapping drift.
