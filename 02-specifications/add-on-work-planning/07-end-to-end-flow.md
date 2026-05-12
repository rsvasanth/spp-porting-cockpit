# 07 — End-to-end flow (planned)

## Narrative — happy path single-row

**Setup:** Production Supervisor Karthik plans the Morning shift's compound batch. Item: COMPOUND-A, workstation: Two Roll Mixing Mill, target: 100 kg.

**T+0:00** — Karthik opens AOWP Dash, scans badge.

**T+0:10** — Selects posting_date=today, shift_type=Morning. Adds row: item=COMPOUND-A, workstation=Two Roll Mixing Mill, target_qty=100. BOM auto-fetches.

**T+0:30** — Work Plan Item Target for (COMPOUND-A × Morning) = 100. No drift warning.

**T+0:45** — Mixing Operation override check returns no override (workstation as-selected).

**T+1:00** — Clicks Submit.

**T+1:01** — Console `initialize_submission`:
1. `build_transaction_payload` runs
2. Routes to `create_local_add_on_work_planning`
3. **`_generate_lot_number(today)` returns `LOT-20260512-003`** (assuming 2 prior submissions today)
4. `_safe_local_create` inserts `Console Add On Work Planning CADWRKP-2026-00078` with Lot # and item child rows
5. Both Legacy + Ops targets queued

**T+1:02** — Dash fires Promise.all.

### Legacy leg (T+1:02 → T+1:10)

1. Bridge `sync_process_transaction(process_type="ADD_ON_WORK_PLANNING")`
2. Inserts `Add On Work Planning` legacy doc with `lot_number="LOT-20260512-003"` (Console-authored, honored by legacy controller)
3. Bridge then calls `create_planning_with_jobcards(payload)` whitelisted method:
   - Creates Work Order `MFG-WO-2026-00112` (production_item=COMPOUND-A, qty=100, bom_no=<auto-fetched>, status=submitted)
   - Creates Job Card `MFG-JC-2026-00125` (workstation=Two Roll Mixing Mill, operation=Mixing, lot_number=LOT-20260512-003)
   - Updates Add On Work Plan Item's `job_card` field to `MFG-JC-2026-00125`
4. Bridge returns `{status: Success, reference_name: "AOWP-2026-...", work_order: "MFG-WO-2026-00112", job_cards: ["MFG-JC-2026-00125"]}`
5. Console `apply_bridge_result("Legacy", ...)`: 5-step dance; aggregate Partial

### Ops leg (T+1:02 → T+1:07)

1. Ops `process_transaction` → generic `TransactionEngine`
2. Action 1: create Work Order with `lot_number="LOT-20260512-003"` custom field
3. Action 2 (for_each items): create Job Card per row, each with `lot_number`
4. Engine returns `{status: success, log_name: "MES-LOG-...", results: {work_order_name: "MFG-WO-OPS-...", job_cards: [...]}}`
5. Console `apply_bridge_result("Ops", ...)`: 5-step dance; aggregate Success when Legacy already done OR self-heal corrects when Legacy lands after

### Final state

| System | Document | State |
|---|---|---|
| Console | `Console Add On Work Planning CADWRKP-2026-00078` | `sync_status=Success`, `docstatus=1`, `lot_number="LOT-20260512-003"` |
| Legacy | `Add On Work Planning` | submitted; `lot_number` Console-authored |
| Legacy | `Work Order MFG-WO-2026-00112` | submitted; production_item=COMPOUND-A, qty=100 |
| Legacy | `Job Card MFG-JC-2026-00125` | submitted; workstation, lot_number set |
| Ops | `Shree Polymer MES Log` | Success |
| Ops | `Work Order MFG-WO-OPS-...` | submitted; `lot_number` custom field set |
| Ops | `Job Card` (Ops mirror) | submitted; `lot_number` set |
| Cross-motion | Downstream BBI can now scan `LOT-20260512-003` and resolve full Job Card context | ✓ |

## Recovery procedures

### Atomic Work Order + Job Card rollback on Legacy

If `create_planning_with_jobcards` fails (e.g. Job Card 2 of 3 fails because of a BOM issue):
- Frappe rolls back all 3 (Work Order, Job Card 1, Job Card 2 partial state)
- Bridge returns Failed
- Console records Legacy Failed; Lot # is NOT consumed by counter (depends on implementation — sequence increment happens on Console doc insert, but legacy retry may need same Lot #)

### Idempotent retry — same Lot #

If Legacy fails and operator retries:
- Console doc still exists with the original Lot #
- Bridge `find_existing_record` finds no matching legacy AOWP (legacy was rolled back)
- Retry creates the legacy chain fresh with the SAME Lot # (Console-authored, preserved across retries)
- Idempotency at legacy: `create_planning_with_jobcards` checks if Work Order with this `lot_number` already exists; if yes, returns existing

### Concurrent Lot # generation safety

Two supervisors submit AOWP simultaneously:
- Both compute `_generate_lot_number(today)`
- If DB-level unique constraint exists on `lot_number`: second insert collides; second submission retries (computes seq+1)
- If no unique constraint: second submission may get the same seq and collide later when legacy auto-detects duplicate

**Recommend:** DB-level unique constraint at implementation time.

## Race resolution

Same 5-step pattern. Whichever leg lands second auto-submits.
