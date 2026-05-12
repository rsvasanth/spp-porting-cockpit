# 06 — Ops ERPNext — `shree_polymer_ops::process_transaction`

**Pattern:** Same as `Master Batch Mixing` — see
[`../master-batch-mixing/06-ops-erpnext.md`](../master-batch-mixing/06-ops-erpnext.md)
for the authoritative reference. This file documents MPE-specific behavior only.

## MPE in Ops — `TransactionEngine`

MPE payload routes to `TransactionEngine` for `process_code = "MOULDING_PRODUCTION_ENTRY"`.

The Ops MPE flow follows the same pattern as other manufacturing doctypes:
1. Idempotency check (MES Log)
2. For each step in the sequence (configured in `Console Process Template`):
   - Creates Work Order → Job Card → Stock Entry (Manufacture, submit)
3. Returns `{status, log_name, results, impacted_balances}`

**Key difference:** MPE's sequence includes the inspection prerequisite check
**before** the manufacturing steps. The inspection entries are preconditions
not created by MPE — they must already exist from [Inspection Entry](../inspection-entry/)
which ships before MPE in Wave 2.

## MPE-specific sequence (from `Console Process Template`)

```
Step 1: Validate — check Job Card is open, check Line+Patrol inspections submitted
Step 2: Create Work Order (if not exists — idempotent by reference_id)
Step 3: Create Job Card (if not exists — idempotent by reference_id)
Step 4: Create Stock Entry (Manufacture, submit)
Step 5: Return impacted_balances + batch_no
```

The actual validation (Job Card open, inspections present) happens in the
legacy `validate_lot_number()` — which the Dash calls **before** allowing
the operator to proceed to the MPE form. The Ops engine relies on this
pre-validation and does not repeat it.

## What Hermes workers can safely change here

| Change | Risk |
|---|---|
| Add new step to MPE sequence | Medium — changes submission flow; coordinate with legacy side |
| Change stock entry creation logic | **High** — affects manufactured batch quality |
| Touch idempotency check | **High** — risk of duplicate Work Order / Job Card |