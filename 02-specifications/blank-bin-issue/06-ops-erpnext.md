# 06 — Ops ERPNext

## Current Ops status

No dedicated BBI submit handler was found in the Ops app. The only BBI references found in Ops are cancellation guards in Work Planning and Add On Work Planning.

| Ops artifact | Status |
|---|---|
| `submit_blank_bin_issue(context)` | Not found. |
| `Blank Bin Issue` custom DocType in Ops | Not verified in source search. |
| Generic engine Process Template for BBI | Not verified. |
| Work Planning cancellation guard | Exists; checks `Blank Bin Issue` by lot. |

## What Ops must represent

Because BBI is not a stock movement, Ops does not need a Stock Entry for this process. It needs one of these:

| Option | Meaning |
|---|---|
| Custom `Blank Bin Issue` DocType | Mirrors Legacy reservation and lets Ops MPE consume open rows. |
| Generic planning/material reservation log | Records bin-to-Job-Card assignment without ledger impact. |

The current generic Transaction Engine can create stock documents, but BBI's native action is not a Stock Entry. Treating BBI as a stock transfer would be a semantic bug.

## Required downstream contract

Ops-side MPE, when implemented, must be able to answer:

| Query | Why |
|---|---|
| Which bins are issued to this lot and still open? | MPE lot validation. |
| Which compound/SPP batch/qty does each bin carry? | MPE source consumption. |
| Which BBI child row should be marked complete? | Prevents double consumption. |
| Which bin remains active as a balance bin? | Supports partial consumption. |

## Drift risk

If Ops skips BBI and lets MPE scan bins directly, the planning cancellation guard and legacy audit model no longer match. That may be a valid redesign later, but it is not current legacy behavior.

