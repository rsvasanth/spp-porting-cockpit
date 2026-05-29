# 01 — Business context

## Architectural strategy

QC is partitioned across the three-site ecosystem to preserve master data integrity while keeping shop-floor execution fast, resilient, and auditable.

```
┌────────────────────────────┐    ┌──────────────────────────────┐    ┌────────────────────────────┐
│       Ops Site             │    │       Console MES App         │    │       Legacy Site          │
│       (25spp.local)        │    │                               │    │       (spp15.local)        │
├────────────────────────────┤    ├──────────────────────────────┤    ├────────────────────────────┤
│ SPP QC Parameter           │───▶│ Console SPP QC Parameter      │    │ Inspection Entry           │
│ SPP QC Template            │───▶│ Console SPP QC Template       │    │ (legacy mirror)            │
│   (master, item-bound)     │    │ (read-only cache)             │    │                            │
│                            │    │                               │    │                            │
│ Stock Entry                │◀───│ SPP Quality Control           │───▶│                            │
│ (draft / submitted)        │    │ (unified transaction)         │    │                            │
│                            │    │ Console Mould Specification   │    │                            │
│                            │    │ (piece-weight cache)          │    │                            │
└────────────────────────────┘    └──────────────────────────────┘    └────────────────────────────┘
```

## Decoupling invariants

1. **Master of truth**: Ops owns `SPP QC Parameter` and `SPP QC Template`. Console caches are read-only.
2. **Item-specific binding**: Each `SPP QC Template` links to exactly one Item.
3. **Strict gate**: No active template for an Item → no inspection submission. No generic fallbacks.
4. **Single Console doctype**: All 5 inspection types live in `SPP Quality Control` with `inspection_type` as the discriminator.

## Why one doctype for 5 types (and not five)

| What's shared | What differs |
|---|---|
| Scan-driven shop-floor UI | UoM for rejection (Nos vs Nos→Kg) |
| Template gate logic | SE submission gate (Draft vs Submitted) |
| Calculation pipeline | Warehouse routing (Rejection vs Target/PDIR) |
| Bridge orchestration | Parent context (Job Card vs Purchase Receipt) |
| Legacy `Inspection Entry` mirror | — |
| `Console Transaction Log` audit | — |

The 5 types share 80% of their lifecycle. The 20% differences are config-driven via `Console Process Template` parameters per type — not hardcoded branches in the controller.

## Why a separate doctype from Console Inspection

See [`README.md`](README.md) for the headline. The detail:

- Compound has a 2-actor workflow (QI initial decision → QM deviation override). QC is single-actor (QI submits, Supervisor cancels).
- Compound identity resolves through `mix_barcode` via a 6-strategy lookup chain. QC identity resolves through `lot_no` via a single Work Plan Item lookup.
- Compound runs once per batch. QC runs many times per shift (Line/Patrol especially).
- Compound mirrors to Legacy `Compound Inspection`. QC mirrors to Legacy `Inspection Entry`.

The two motions are conceptually similar but operationally distinct. Trying to force them into one doctype produced more branches than it removed.

## Position in the SPP ecosystem

- Console Inspection — Compound family only (per `console-inspection-unification` spec, now narrowed).
- **SPP Quality Control — production-line + incoming + final-visual QC. This spec.**
- Future inspection forms (first-piece approval, supplier audits) — separate motions, not in this spec.
