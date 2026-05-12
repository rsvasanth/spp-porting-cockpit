# 10 — Risks and decisions

## Plan-vs-reality deltas

| # | Delta | Plan said | Reality (planned) | Recommendation |
|---|---|---|---|---|
| 1 | Path discriminator | `move_to_cut_bit_warehouse` Check | Same | **Keep** |
| 2 | Dedicated Ops handler vs generic engine | Plan implied generic engine | Dedicated handler recommended for Asset Movement + branching | **Use dedicated** — per BBIE 06-ops-erpnext.md |
| 3 | Weight re-verification at BBIE | Not explicit | Soft warning if drift > 5% from BDE | **Add at Dash** |
| 4 | Multi-bin batch BBIE | Not explicit | One bin per BBIE submission | **Single-bin** keeps audit clear |

## Cross-doctype invariants Hermes must NOT break

| # | Invariant | Where enforced | Breaks if… |
|---|---|---|---|
| 1 | Bin Asset state transitions atomic | Legacy on_submit + Ops handler | Either side fails to update Asset status |
| 2 | Cut-bit path produces `Cutbit_<item>` batch | Bridge populate + Ops handler | Convention drifts; FB Mixing recycling breaks |
| 3 | `run_legacy_sync=False` from Console path | Ops `process_transaction` dispatch | Removed; duplicate Legacy calls |
| 4 | Asset Movement on both ERPs is created (bin path) | Legacy on_submit + Ops handler | Either side fails; Asset state out of sync |
| 5 | `use_serial_batch_fields=1` for cut-bit path SE | Ops handler | ERPNext v15 SABB conflict |
| 6 | 5-step race-safety pattern | Controller | Saga regression |

## Operational risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Bin in wrong state at scan | Medium | Low — clear rejection | Bridge validates Asset status |
| Cut-bit batch creation collision (concurrent submissions) | Low | Low | Frappe Batch insert is idempotent on batch_id |
| Asset Movement on one ERP fails | Low | Medium — Asset state out of sync | Partial state; operator retries |
| `run_legacy_sync=True` from Console (bug) | Low — covered by code review | High | Bridge idempotency catches duplicate |
| Operator confused by toggle UX | Medium | Low — operational training | Transparency banner pre-submit |

## Decisions deferred

### Multi-bin batch BBIE

Could BBIE accept multiple bins per submission?

**Currently:** One bin per BBIE.

**Pros of multi-bin:**
- Faster shift handoffs (move 5 bins at once)
- Less HTTP round-trips

**Cons:**
- Audit clarity: each bin is its own physical event
- Single-failure complication (which bin failed?)
- Reconciliation gets harder

**Recommend:** Defer indefinitely. Operational practice handles single-bin BBIE well.

### Weight re-verification threshold

5% drift soft warning — same as Sheeting motion mass-balance. Operationally proven.

**Recommend:** Keep at 5%. Adjust if operations data shows tighter is achievable.

### Third path (scrap)

If a bin's contents are genuinely waste (not even cut-bit-worthy), should there be a third path option?

**Currently:** No. Operator scraps manually via a Stock Entry adjustment in Legacy (out of Console).

**Recommend:** Defer. Cut-bit path covers most cases; outright scrap is rare and outside normal shop-floor BBIE workflow.

## Questions waiting on Production Overseer

| Question | Recommendation |
|---|---|
| Implement as dedicated Ops handler? | **Yes** — Charter Principle 2 exception, justified by Asset Movement complexity |
| Soft warning threshold at 5%? | **Yes** for now; revisit after one shift of production data |
| Add a third path option for scrap? | **No** for v1 |
| Add bin-history view in Dash? | **No** for v1; defer to future analytics |
