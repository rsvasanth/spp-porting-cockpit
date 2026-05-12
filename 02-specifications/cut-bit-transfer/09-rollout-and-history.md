# 09 - Rollout and history

## What the source/spec shows

| Wave | Shipped behavior |
|---|---|
| Wave 1 | Real Console local doctype for `Console Cut Bit Transfer` and child `Console Cut Bit Item` |
| Wave 1 | `initialize_submission` creates a local audit record before target execution |
| Wave 1 | `CUT_BIT_TRANSFER` added to local domain callback routing |
| Wave 1.5 / hardening | Dedicated Ops handler routed before generic Transaction Engine |
| Wave 1.5 / hardening | `run_legacy_sync=False` in Console path to avoid duplicate Legacy calls |
| Wave 1.5 / hardening | Console submit wrapper relays native batch numbers before orchestration |
| W1-C3 / BCR-adjacent | Console native mapping side effects for downstream Clip/Bin lifecycle |

## Current repo locations

| App | File |
|---|---|
| Console Dash | `/Users/alphaworkz/frappe-bench/apps/shree_polymer_console/dash/src/components/processes/CutBitTransferEntry.tsx` |
| Console API | `/Users/alphaworkz/frappe-bench/apps/shree_polymer_console/shree_polymer_console/shree_polymer_console/api.py` |
| Console doctype | `/Users/alphaworkz/frappe-bench/apps/shree_polymer_console/shree_polymer_console/shree_polymer_console/doctype/console_cut_bit_transfer/` |
| Bridge | `/Users/alphaworkz/frappe-bench/apps/shree_polymer_legacy_bridge/shree_polymer_legacy_bridge/sync_api.py` |
| Ops | `/Users/alphaworkz/frappe-bench/apps/shree_polymer_ops/shree_polymer_ops/api.py` |
| Legacy | `/Users/alphaworkz/frappe-bench/apps/shree_polymer_custom_app/shree_polymer_custom_app/shree_polymer_custom_app/doctype/cut_bit_transfer/` |

## Why this spec is delta-style

The orchestration backbone is already documented in Master Batch Mixing:

| Shared layer | Reference |
|---|---|
| `initialize_submission` | [`../master-batch-mixing/03-console-backend.md`](../master-batch-mixing/03-console-backend.md) |
| `execute_submission_step` | [`../master-batch-mixing/03-console-backend.md`](../master-batch-mixing/03-console-backend.md) |
| Transaction Logs | [`../master-batch-mixing/03-console-backend.md`](../master-batch-mixing/03-console-backend.md) |
| 5-step `apply_bridge_result` | [`../master-batch-mixing/03-console-backend.md`](../master-batch-mixing/03-console-backend.md) |

Cut Bit's shipped complexity is in process-specific routing and identity repair, not in the base cockpit loop.

## Hermes can touch

| Area | Allowed? | Notes |
|---|---|---|
| Spec text in this cockpit folder | Yes | This is the deliverable |
| Console/Bridge/Ops code | No for this task | User asked for spec only |
| Bench execution | No | Production overseer reviews; Hermes/runtime executes elsewhere |
| Tests | Not run for spec-only work | Include test commands instead |

## Known historical drift

| Drift | Reality |
|---|---|
| Older process docs mention `cb_...` scan behavior | Current Dash scans Clip/Bin assets and submits `items[]` |
| Existing Console test names say CBT creates clip mappings | Current helper skips clips and consumes Bin mappings only |
| Legacy idempotency lacks `reference_id` | Bridge uses first barcode + 10-minute creation window |
| Generic Ops engine docs include CBT in examples | Current Ops routes CBT before generic engine |

## Rollout checklist for future code changes

| Step | Required before push |
|---|---|
| Console change | Run Console doctype tests and relevant API tests |
| Bridge change | Run Legacy Bridge tests or provide exact bench command if local site unavailable |
| Ops change | Run `shree_polymer_ops.tests.test_cut_bit` and E2E smoke if stock logic touched |
| Dash change | Build dash assets and commit generated assets |
| Any production sync change | Verify no duplicate Legacy call from Ops path |

## Current recommendation

Treat the current implementation as production reality. Do not "clean up" the duplicate-looking Legacy and Ops Stock Entry creation without a wider architecture decision: the parallel-sync model intentionally creates equivalent documents on two ERPs.
