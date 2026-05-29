# 06 — Acceptance criteria

Each criterion is a testable assertion. Format: `AC-QC-<n>`.

## Template gate

**AC-QC-01** — Given an Item with no active `SPP QC Template`, when a QI scans a lot for that Item, then the UI displays the strict-block message and submission is impossible.

**AC-QC-02** — Given a template-missing block, when the QI clicks "Sync templates now", then the Console pulls fresh templates from Ops within 5s and re-checks.

**AC-QC-03** — Given a template exists, when the QI scans the lot, then the parameter grid renders with `nominal_value`, `min_value`, `max_value` populated from the cached template.

## Reading validation

**AC-QC-04** — Given a reading entered within `[min_value, max_value]`, when the QI tabs out of the field, then the cell turns green.

**AC-QC-05** — Given a reading outside the bounds, when the QI tabs out, then the cell turns red.

**AC-QC-06** — Given any combination of frontend colors, when the QI submits, then the backend recomputes `reading_status` for each parameter independently of frontend signals.

## Calculations

**AC-QC-07** — Given a Moulding inspection with 5 rejected pieces and `one_no_qty_equal_kgs = 0.050`, when the QC is submitted, then `total_rejected_qty_kg = 0.250` and the Stock Entry detail row records `qty = 0.250 Kg`.

**AC-QC-08** — Given an Incoming inspection with 5 rejected pieces, when submitted, then the Stock Entry detail row records `qty = 5 Nos` (no conversion).

## Stock Entry creation

**AC-QC-09** — Given a Line / Patrol / Lot / Incoming inspection, when submitted, then the Stock Entry on Ops is created at `docstatus = 0` (Draft).

**AC-QC-10** — Given a Final Visual / PDIR inspection, when submitted, then the Stock Entry on Ops is created at `docstatus = 1` (Submitted) and moves stock from Source to Target/PDIR warehouse.

**AC-QC-11** — Given a Bridge timeout after Ops created the SE but before response, when the Console retries with the same `reference_id`, then Ops does NOT create a duplicate SE.

## Cancellation

**AC-QC-12** — Given a submitted QC whose Stock Entry has been consumed downstream, when the Supervisor cancels, then the Ops cancel fails, the cascade halts, and the local QC remains at `docstatus = 1`.

**AC-QC-13** — Given a submitted QC whose Stock Entry is still free, when the Supervisor cancels, then in order: Ops cancels the SE, Legacy cancels the Inspection Entry, and Console marks `docstatus = 2`.

**AC-QC-14** — Given any cancellation outcome, the result MUST be visible in `Console Transaction Log` with full request/response payloads.

## Identity

**AC-QC-15** — Given an Inspector badge identical to the Operator badge, when both are scanned, then submission is blocked with a same-person error.

**AC-QC-16** — Given a Lot barcode that does not resolve in `Console Work Plan Item`, when scanned, then the UI displays an unresolved-lot error and submission is impossible.

## Permissions

**AC-QC-17** — A user without the QI role cannot create `SPP Quality Control`.

**AC-QC-18** — A user without the Supervisor role cannot cancel `SPP Quality Control`.
