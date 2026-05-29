# 03 — Functional requirements

Numbered for traceability. Format: `FR-QC-<n>`.

## Scan flow

**FR-QC-01** — The Console QC dashboard MUST accept three sequential barcode scans in order: (1) Inspector Employee badge, (2) Operator Employee badge, (3) Lot Number.

**FR-QC-02** — Each scan MUST auto-resolve and display the human-readable identity (Inspector name, Operator name, Item code + Job Card from Lot).

**FR-QC-03** — Lot scan MUST resolve via `Console Work Plan Item` cache and populate: `item_code`, `workstation`, `mould_reference`, `one_no_qty_equal_kgs` (from `Console Mould Specification`).

## Template gate

**FR-QC-04** — On Lot scan, the Console MUST query `Console SPP QC Template` for the resolved `item_code`.

**FR-QC-05** — If no active template exists for the Item, the Console MUST block the inspection and display: *"No active Quality Template configured for Item [Item Code]. Action halted. Please configure the template on the Ops site first."*

**FR-QC-06** — If a template exists, the Console MUST render a dynamic parameter grid showing each `parameter`, `nominal_value`, `min_value`, `max_value`, and an empty `reading_value` input.

**FR-QC-07** — On template-missing (FR-QC-05), the UI MUST offer a "Sync templates now" button that triggers an on-demand sync from Ops and re-checks before final block.

## Reading entry

**FR-QC-08** — Each `reading_value` MUST be color-coded in real time: green if `min_value <= reading_value <= max_value`, red otherwise.

**FR-QC-09** — Reading status (`Pass` / `Fail`) MUST be computed authoritatively on the backend at submit time. Frontend color is presentational only.

## Quantities and submission

**FR-QC-10** — `total_inspected_qty`, `total_accepted_qty`, `total_rejected_qty` MUST be captured in `Nos`.

**FR-QC-11** — For Moulding inspection types (`Line`, `Patrol`, `Lot`), `total_rejected_qty_kg` MUST equal `total_rejected_qty * one_no_qty_equal_kgs`.

**FR-QC-12** — Submission MUST be idempotent: a duplicate `reference_id` from a retry MUST NOT create a second Stock Entry on Ops.

## Stock Entry cascade

**FR-QC-13** — On submit, the Console MUST trigger Bridge orchestration to create the appropriate Stock Entry on Ops per the type matrix in `05-business-rules.md`.

**FR-QC-14** — Target warehouses MUST be resolved from `Console Process Template` parameters (NOT hardcoded, NOT global settings).

**FR-QC-15** — On Bridge success, the Console MUST store the returned Stock Entry name in `stock_entry_reference`.

## Legacy mirror

**FR-QC-16** — On Bridge success, the Console MUST also write a mirror `Inspection Entry` record on Legacy (`spp15.local`) via the Legacy Bridge.

## Cancellation

**FR-QC-17** — Cancel MUST first ask Ops to cancel the linked Stock Entry. If Ops refuses (stock consumed / locked), the Console MUST refuse cancellation and surface the Ops error message.

**FR-QC-18** — If Ops cancels successfully, the Console MUST cascade cancel to Legacy `Inspection Entry`, then mark local `SPP Quality Control` as `docstatus=2`.

## Audit

**FR-QC-19** — Every submit, cancel, and template-missing-block event MUST land in `Console Transaction Log` with full request/response payloads.
