# 03 — Console backend

> **Identical to MB Mixing.** Read [`../master-batch-mixing/03-console-backend.md`](../master-batch-mixing/03-console-backend.md)
> end-to-end.

## Proof of identity

### `create_local_final_batch_mixing` is a literal copy of `create_local_master_batch_mixing`

`api.py:2134` vs `api.py:2095` — same `_safe_local_create` call, same
`_pick` paths, same `_MIXING_ITEM_KEYMAP` for child rows, same docstring
("Mirror the MB Mixing payload locally — same shape as MB."). The only
differences:

| Line | MB | FB |
|---|---|---|
| doctype name | `"Console Master Batch Mixing"` | `"Console Final Batch Mixing"` |
| process_code | `"MASTER_BATCH_MIXING"` | `"FINAL_BATCH_MIXING"` |
| log_label | `"create_local_master_batch_mixing"` | `"create_local_final_batch_mixing"` |

### `console_final_batch_mixing.py` controller is a literal copy of `console_master_batch_mixing.py`

132 lines, byte-for-byte same logic. `validate` has the same
`from_local_cache` bypass. `before_insert` sets `process_code` to the FB
value. `on_submit` upserts the Transaction Log. `apply_bridge_result`
runs the **same 5-step atomic dance**.

### `console_final_batch_mixing.json` is identical schema

Same 28 fields, same order, same options. Only `autoname` differs (`FBM-`
vs `MBM-`) and the doctype `name`.

## Dispatch

`initialize_submission` routes by `process_code`:

```python
elif process_code == "FINAL_BATCH_MIXING":
    create_local_final_batch_mixing(prelim_payload, reference_id)
```

`apply_bridge_result` module-level dispatcher (`api.py:1980`) includes
`"Console Final Batch Mixing"` in `parent_doctypes`:

```python
parent_doctypes = [
    "Console Inspection",
    "Console Master Batch Mixing",
    "Console Final Batch Mixing",   # ← here
    ...
]
```

`update_local_domain_record` includes FB in the lookup table:

```python
legacy_doctype_map = {
    "MASTER_BATCH_MIXING": "Console Master Batch Mixing",
    "FINAL_BATCH_MIXING":  "Console Final Batch Mixing",   # ← here
    ...
}
```

## Implication for maintenance

**If MB's `apply_bridge_result` is touched, FB's must be touched in lockstep
— or vice versa.** They are not just similar, they are **literally
duplicated.** Any divergence introduces a hidden inconsistency in the
race-safety pattern across the two processes.

**Recommendation flagged for `10-risks-and-decisions.md`:** consolidate
into a shared mixin or base class so the 5-step pattern lives in one
place. This is a refactor candidate, not a Wave 2 blocker.
