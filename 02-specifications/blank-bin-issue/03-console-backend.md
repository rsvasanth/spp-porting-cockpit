# 03 — Console backend

> Read [`../master-batch-mixing/03-console-backend.md`](../master-batch-mixing/03-console-backend.md) for `initialize_submission`, target logs, `_safe_local_create`, and callback aggregation. BBI currently has no verified local doctype on `develop`.

## Current `develop` gap

| Console backend artifact | Status |
|---|---|
| `Console Blank Bin Issue` DocType | Not found on current `develop`. |
| `Console Blank Bin Issue Item` child DocType | Not found on current `develop`. |
| `create_local_blank_bin_issue` | Not found on current `develop`. |
| `BLANK_BIN_ISSUE` branch in `initialize_submission` | Not found on current `develop`. |
| `update_local_domain_record` mapping | No BBI mapping found. |
| `apply_bridge_result` parent-doctype list | No BBI parent found. |

## Stale branch evidence gap

A stale local Console remote-tracking ref/commit added whitelisted scan helpers but still did not add a local BBI audit DocType or target mapping. Its commit message says "blank bin issue ui and dummy functions in api.py", which matches the code. The live `iyyanarr/shree_polymer_console` remote branch list should be treated as authoritative; on 2026-05-12 it showed no live BBI branch.

## Required local record contract

A real Console port needs a local record because BBI is downstream-blocking and MPE-critical:

| Field group | Required values |
|---|---|
| Audit | `reference_id`, `sync_status`, target references, submission metadata. |
| Scan identity | `scan_production_lot`, `scan_bin`, `job_card`, `bin`. |
| Production context | `production_item`, `qty_to_manufacture`, `press`, `mould`. |
| Bin context | `asset_name`, `bin_weight`, `compound`, `spp_batch_number`, `qty`. |
| Child row | Same fields plus `is_completed`, default `0`. |

## Local create behavior

Legacy has a load-bearing copy behavior: `validate()` rebuilds the child table from parent fields. Console can implement this more cleanly, but the target result must be the same:

| Input | Local persisted result |
|---|---|
| One lot + one bin scan | One parent BBI row and one child item row. |
| `is_completed` omitted | Child row defaults to incomplete / open for MPE. |
| Missing lot or bin | Local create should fail before target sync. |
| Retried reference_id | Must be idempotent like other Console processes. |

## Callback implication

Until a local doctype exists, standard callback wiring cannot update BBI domain state. If BBI is ported through the shared live-feedback flow, it needs the same mapping coverage as other local audit doctypes:

```python
legacy_doctype_map["BLANK_BIN_ISSUE"] = "Console Blank Bin Issue"
```

and the doctype's `apply_bridge_result` must accept the same caller shape as the shared callback path.
