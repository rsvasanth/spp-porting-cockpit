# 06 — Ops ERPNext (v15) — planned

## Likely architectural choice: dedicated Ops handler

BBIE's branching (Asset Movement vs Stock Entry Repack) and Asset state machine handling are NOT cleanly expressible via the generic `TransactionEngine`. The likely design:

**Dedicated Ops handler:** `submit_blank_bin_inward_entry(context)`

```python
# In shree_polymer_ops/api.py
def process_transaction(payload=None):
    # ... existing routing ...
    elif process_code == "BLANK_BIN_INWARD":
        return submit_blank_bin_inward_entry(context)
    # ... rest of routing ...

def submit_blank_bin_inward_entry(payload, run_legacy_sync=False):
    """Dedicated handler for BBIE — handles bin/repack branching + Asset Movement."""
    move_to_cut_bit = bool(payload.get("move_to_cut_bit_warehouse"))
    if move_to_cut_bit:
        # Create Stock Entry (Repack) into Cut Bit warehouse
        se = _create_repack_to_cut_bit(payload)
        return {"status": "success", "reference_name": se.name, ...}
    else:
        # Create Asset Movement (Receive Bin) on Ops
        am = _create_receive_bin_asset_movement(payload)
        return {"status": "success", "reference_name": am.name, ...}
```

`run_legacy_sync=False` is critical — Console architecture calls the Legacy Bridge in parallel; Ops MUST NOT make a duplicate Legacy call. Same pattern as CBT.

## Documents created on Ops

| Variant | Document |
|---|---|
| Bin path | `Asset Movement` (Receipt purpose) moving the bin Asset to Moulding Unit warehouse |
| Cut-bit path | `Stock Entry` (Repack purpose) with `Cutbit_<item>` batch — same as Cut Bit Transfer convention |

## Idempotency

Standard `Shree Polymer MES Log` lookup by `reference_id`.

## Why dedicated and not generic engine

Per Charter Principle 2, dedicated Ops handlers are exceptions. BBIE qualifies because:
- Asset Movement is not a standard "create_doc" action the engine handles cleanly (bin Asset state transitions are coupled)
- Branching on `move_to_cut_bit_warehouse` flag with completely different document types isn't expressible in declarative Process Template actions
- Same justification as CBT and BDE

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add Ops-side validation | Low — additive |
| Change Asset state transition timing | Medium — affects downstream BBI visibility |
| Switch to generic engine | High — would require expressing Asset Movement in sequence actions |
| Remove `run_legacy_sync=False` invariant | **Highest** — duplicate Legacy submissions |
