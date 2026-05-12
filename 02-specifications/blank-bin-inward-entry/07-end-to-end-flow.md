# 07 — End-to-end flow (planned)

> Read [`../master-batch-mixing/07-end-to-end-flow.md`](../master-batch-mixing/07-end-to-end-flow.md) for the sequence-diagram template. BBIE follows the same pattern with two-path branching.

## Narrative — Bin path (default)

**Setup:** Material Handler Aravind has a filled bin (Asset `BIN-042`) at the blanking warehouse. It contains 25 kg of compound from a recent BDE submission.

**T+0:00** — Aravind opens BBIE Dash, scans badge.

**T+0:15** — Scans `BIN-042`. `validate_blank_bin_inward` returns:
- Item: COMPOUND-A
- Batch: B-2026-...
- Net weight: 25 kg (from BDE)
- Source: blanking warehouse
- Compound: COMPOUND-A
- Asset status: Filled at blanking warehouse ✓

**T+0:30** — Toggle off (default bin path). Dash shows: "This bin will arrive at Moulding Unit warehouse."

**T+0:45** — Confirms net weight 25 kg (no drift). Clicks Submit.

**T+0:46** — `initialize_submission` routes to `create_local_blank_bin_inward_entry`. Console doc created (`CBBIE-2026-00012`).

**T+0:47** — Promise.all fires Legacy + Ops in parallel.

### Legacy leg (T+0:47 → T+0:52)

- Bridge `sync_process_transaction(process_type="BLANK_BIN_INWARD")`
- Maps + populates: `move_to_cut_bit_warehouse=0`
- `legacy_doc.insert() + submit()`
- Legacy `on_submit`: creates `Asset Movement (Receipt)` moving BIN-042 from blanking → Moulding Unit
- Bin Asset status flips to "Inward at Moulding Unit"
- Bridge returns `{status: Success, reference_name: "AM-2026-..."}`
- Console `apply_bridge_result`: 5-step dance; aggregate Partial (Ops pending)

### Ops leg (T+0:47 → T+0:51)

- Ops `process_transaction` → dispatches to dedicated `submit_blank_bin_inward_entry(context, run_legacy_sync=False)`
- Creates Ops `Asset Movement (Receipt)` mirroring the Legacy AM
- Returns `{status: success, log_name: "MES-LOG-...", reference_name: "AM-..."}`
- Console `apply_bridge_result`: 5-step dance; aggregate Success; auto-submit fires

### Final state (bin path)

| System | Document | State |
|---|---|---|
| Console | `Console Blank Bin Inward Entry CBBIE-2026-00012` | `docstatus=1`, `sync_status=Success`, `move_to_cut_bit_warehouse=0` |
| Legacy | `Blank Bin Inward Entry` | submitted; `stock_entry_reference` = AM name |
| Legacy | `Asset Movement AM-2026-...` (Receipt) | submitted; BIN-042 now at Moulding Unit |
| Legacy | BIN-042 Asset status | "Inward at Moulding Unit" |
| Ops | `Shree Polymer MES Log` | Success |
| Ops | `Asset Movement` (Ops mirror) | submitted; bin Asset state updated on Ops |
| Stock Ledger | No SE; AM only | (correctly: no inventory qty change, just location) |

## Narrative — Cut-bit repack path

**Setup:** Bin BIN-099 at blanking warehouse contains 18 kg of leftover compound from a partial run. Material Handler decides to repack.

**T+0:00** — Same scan flow.

**T+0:30** — Toggle ON. Dash shows: "This bin will be REPACKED. Compound moves to cut-bit warehouse with `Cutbit_COMPOUND-A` batch. Bin will return to Available status." Cut-bit batch field auto-populates: `Cutbit_COMPOUND-A`.

**T+0:45** — Submit.

### Legacy leg (cut-bit path)

- Bridge populate function detects `move_to_cut_bit_warehouse=1`
- `legacy_doc.submit()`
- Legacy `on_submit`: calls `make_repack_to_cut_bit(self)`
  - Creates Stock Entry (Repack):
    - Source row: BIN-099's contents debited from source warehouse
    - Target row: 18 kg credited to `Cut-Bit Warehouse - SPP INDIA` with `Cutbit_COMPOUND-A` batch
  - Sets bin Asset status to "Available"
- Bridge returns `{status: Success, reference_name: "MAT-STE-..."}`

### Ops leg (cut-bit path)

- Dedicated handler detects `move_to_cut_bit_warehouse=1`
- Creates Ops Stock Entry (Repack) mirroring the Legacy SE
- Uses `Cutbit_<item>` batch convention + auto-creates Batch if missing
- Uses `use_serial_batch_fields=1` (same as Cut Bit Transfer SABB handling)
- Returns Success

### Final state (cut-bit path)

| System | Document | State |
|---|---|---|
| Console | `Console Blank Bin Inward Entry` | `docstatus=1`, `move_to_cut_bit_warehouse=1`, `cut_bit_batch="Cutbit_COMPOUND-A"` |
| Legacy | `Blank Bin Inward Entry` | submitted |
| Legacy | `Stock Entry (Repack)` | submitted; compound moves to cut-bit warehouse |
| Legacy | BIN-099 Asset status | "Available" (back to empty) |
| Legacy | `Cutbit_COMPOUND-A` batch | qty incremented by 18 kg |
| Ops | `Stock Entry (Repack)` | submitted; mirror of Legacy SE |
| Stock Ledger | Compound moves on both ERPs | Stock Ledger Entries reflect |

## Race resolution

Same 5-step pattern as MB. Whichever leg lands second triggers auto-submit.

## Recovery procedures

| Failure | Recovery |
|---|---|
| Bridge timeout mid-flight | Console Partial state; operator retries from Transaction Log |
| Ops AM creation fails | Console reports Ops Failed; retry |
| Bin already Inward (state machine violation) | Bridge rejects; clear error; operator investigates |
| Cut-bit batch creation race (two operators repacking simultaneously) | Frappe Batch creation is idempotent; second insert finds existing |
