# 06 - Ops ERPNext

> Read [`../master-batch-mixing/06-ops-erpnext.md`](../master-batch-mixing/06-ops-erpnext.md) for the generic engine. Blanking DC Entry uses a dedicated handler.

## Dispatch

Ops `process_transaction` routes:

```python
elif process_code == "BLANKING_DC_ENTRY":
    return submit_blanking_dc_entry(context)
```

## Dedicated handler

`submit_blanking_dc_entry(payload)` creates one `Stock Entry` with purpose/type `Material Transfer`.

For each item:

| Row | Warehouse | Batch |
|---|---|---|
| Source | `CUTBIT_WH` | `CB_<compound>_<spp_batch>` |
| Target | `BLANKING_WH` / PreForming | same `CB_<compound>_<spp_batch>` |

The handler expects:

| Field | Source |
|---|---|
| `compound` or `item_code` | Dash item row |
| `spp_batch_number` | Dash item row |
| `net_weight` or `qty` | Dash item row |

## Semantic drift

The handler comment says:

> Cut Bit WH -> PreForming (Blanking) WH. The compound arrives in Cut Bit WH with batch `CB_{compound}_{spp_batch}`.

Current Dash/Console BDE scans a sheeting clip and a blanking bin. It does not require a prior Cut Bit Transfer or send a `CB_` batch id. Ops derives that batch name anyway.

This is the largest target-semantics risk in BDE:

| Path | Meaning |
|---|---|
| Console/Dash | Clip material weighed into bin |
| Legacy | Item Bin Mapping + Asset Movement |
| Ops | Stock Entry from Cutbit warehouse to PreForming |

If the Ops site does not have `CB_<compound>_<spp_batch>` stock in Cutbit warehouse, Ops BDE fails even though Console/Legacy BDE is logically valid.

## Response shape

Ops returns:

| Field | Meaning |
|---|---|
| `status` | Success/Failed |
| `reference_name` | Stock Entry name |
| `reference_doctype` | `Stock Entry` |
| `message` | Human-readable result |

No impacted bin mappings are returned by this handler. Console creates its own `Console Item Bin Mapping` during local create.

## What Hermes workers can change

| Change | Risk |
|---|---|
| Align Ops with Legacy Asset Movement/bin mapping semantics | High-value architecture task |
| Keep Stock Entry semantics but require Cut Bit path | Needs UI/process clarity |
| Return impacted bins | Low/medium; helps local cache updates |
| Change batch convention | High; stock lookup depends on it |
