# 01 — Purpose

## What this motion does

Quality Control covers every shop-floor inspection event other than the Compound family. A single Console-native doctype (`SPP Quality Control`) captures five inspection types:

| Inspection Type | When it runs | Actor | Outcome |
|---|---|---|---|
| **Line** | Mid-run during moulding | QI | Accept / Reject / Rework, mid-run rejection moves stock to rejection warehouse |
| **Patrol** | Periodic patrol sampling during moulding | QI | Same as Line |
| **Lot** | End-of-lot summary | QI | Same as Line |
| **Incoming** | Receipt of raw / bought-out materials | QI | Accept / Reject of incoming batch |
| **Final Visual / PDIR** | Packing-stage pre-dispatch | QI | Accept / Reject; on accept stock moves to PDIR / Target warehouse |

All five inspections share:
- The same scan-driven shop-floor UI
- The same `SPP QC Template` configured on Ops per Item
- The same Bridge-driven Stock Entry orchestration on Ops
- The same Legacy `Inspection Entry` mirror on `spp15.local`

## Position in the chain

```
Master Batch Mixing → Final Batch Mixing → Compound Inspection
                                                  │
                                                  ▼
                                          Sheeting → Blanking → Moulding
                                                                    │
                                                            ┌───────┼───────┐
                                                            │       │       │
                                                            ▼       ▼       ▼
                                                          Line   Patrol    Lot   ◀── SPP Quality Control
                                                                    │
                                                                    ▼
                                                              Final Visual / PDIR ◀── SPP Quality Control
                                                                    │
                                                                    ▼
                                                                Dispatch

       Incoming (Raw / BOI) ─── SPP Quality Control ─── Stores
```

## Why a new doctype (not Console Inspection)

Console Inspection was originally scoped to absorb Production-family inspections as well. That direction was reversed: the operational shape of Compound (chemistry, deviation override) is too different from production-line scan/reject flows. QC owns its own state machine, its own UI, its own permissions surface.

See [`07-out-of-scope.md`](07-out-of-scope.md) for the Compound boundary.
