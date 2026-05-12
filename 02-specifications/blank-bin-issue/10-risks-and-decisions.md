# 10 — Risks and decisions

## Plan-vs-reality deltas

| ID | Delta | Reality | Recommendation |
|---|---|---|---|
| BBI-DRIFT-001 | Spec folder was empty. | Legacy/site process is high volume. | Use this folder as the source-grounded spec. |
| BBI-DRIFT-002 | Console `develop` has no BBI path. | No local doctype/API/Dash route found. | Treat BBI as not ported. |
| BBI-DRIFT-003 | Stale Console branch evidence looked promising. | Live `iyyanarr/shree_polymer_console` showed no BBI branch on 2026-05-12; stale evidence has UI and dummy helpers only. | Do not treat as implementation-complete or current branch work. |
| BBI-DRIFT-004 | Prototype scans `Console Job Card` and `Console Blanking DC Entry`. | Legacy scans lot barcode and physical bin Asset barcode. | Rework scan identities during implementation. |
| BBI-DRIFT-005 | Prototype adds `actual_qty`. | Legacy BBI uses Item Bin Mapping `qty`; no manual actual qty field. | Confirm with production before adding manual qty. |
| BBI-DRIFT-006 | Duplicate prevention is tempting. | Legacy duplicate checks are commented; live duplicate lot/bin pairs exist. | Do not add uniqueness without signoff. |

## Load-bearing invariants

| Invariant | Why |
|---|---|
| BBI is not a stock movement. | Prevents false stock ledger changes. |
| `is_completed = 0` means available for MPE. | MPE lot validation depends on it. |
| MPE, not BBI, completes issue rows. | Completion means consumed, not merely issued. |
| Bin scan validates location and BOM compound. | Prevents wrong material reaching MPE. |
| Planning cancellation blocks after BBI exists. | BBI is a downstream commitment. |

## Decisions waiting on implementation

| Decision | Recommendation |
|---|---|
| Should Ops mirror BBI as a custom DocType? | Yes, unless Ops MPE gets a stronger reservation model. |
| Should Console add manual `actual_qty`? | No by default; preserve legacy `qty` from Item Bin Mapping. |
| Should duplicate open bin/job issues be blocked? | Investigate live duplicates first; do not hard-block blindly. |
| Should Bridge use populate helper? | Yes, because barcode and BOM validation are not simple field copies. |

## Opinion

BBI should be ported before MPE. MPE's lot validation reads open BBI rows as a hard prerequisite, so implementing MPE first would either bypass a real legacy gate or force temporary logic that later gets replaced.
