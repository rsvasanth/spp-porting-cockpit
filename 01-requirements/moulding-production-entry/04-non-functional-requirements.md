# 04 — Non-functional requirements

## NFR-MPE-001 — Scan response time
Lot and bin scan validation should return within shop-floor usable latency. Target: under 2 seconds for normal records.

## NFR-MPE-002 — Submit reliability
MPE submit is a multi-record transaction. It must not create an orphan Stock Entry, orphan batch, or completed Job Card when later steps fail.

## NFR-MPE-003 — Concurrency safety
Two users must not submit production for the same open Job Card/bin set concurrently. The bin completion and Job Card completion checks must be repeat-safe.

## NFR-MPE-004 — Quantity precision
All kg quantities must preserve legacy precision behavior, normally three decimal places for production and consumed weights.

## NFR-MPE-005 — Audit completeness
Audit must reconstruct lot, Job Card, Work Order, operator, supervisor, bins consumed, balance bins, source batches, produced batch, Stock Entry, and cascaded Inspection Entries.

## NFR-MPE-006 — Target parity
Console must preserve legacy validation outcomes unless a drift is explicitly accepted by the process owner.

## NFR-MPE-007 — Recoverability
Failed MPE submissions must expose the failing step and target record name, if any, so an overseer can reconcile without database guessing.

## NFR-MPE-008 — No hidden mass-balance policy change
Any change from legacy tolerance message behavior to hard blocking must be configurable and signed off; requirements must not encode an unverified 1% hard throw as current reality.

