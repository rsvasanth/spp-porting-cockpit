# 09 — Rollout and history

## Milestones

| Milestone | Deliverables | Target System(s) | Exit Criteria |
|---|---|---|---|
| **M1: Master Schema & Sync** | `Console SPP QC Parameter`, `Console SPP QC Template` (+ child) doctypes created. Sync worker pulls hourly + on-demand from Ops. Manual sync trigger wired in admin UI. | Ops → Console | Templates created on Ops appear on Console within 1 hour (scheduled) or 5 seconds (on-demand). |
| **M2: Transactional Core** | `SPP Quality Control` parent + child doctypes created. Controller `validate()` + `on_submit()` + `on_cancel()` implemented. Permission matrix configured. Unit tests cover all `AC-QC-*` from `06-acceptance-criteria.md`. | Console | Unit suite ≥85% line coverage, all tests green. |
| **M3: Bridge Orchestration** | 5 Process Templates registered (`SPP_QC_LINE`/`PATROL`/`LOT`/`INCOMING`/`FINAL_VISUAL`). Dispatch arms added to `initialize_submission`. Ops handler `create_stock_entry_from_qc` + `cancel_stock_entry_from_qc` implemented with idempotency. Draft-SE close batch job implemented. | Console + Ops | Integration suite green; Stock Entry round-trip verified per type matrix. |
| **M4: Legacy Mirror** | `shree_polymer_legacy_bridge/handlers/spp_quality_control.py` implemented. Field mapping per `05-legacy-erpnext.md`. Cancel-cascade order Ops→Legacy→local verified. | Console + Legacy | Submitting QC on Console creates mirror `Inspection Entry` on `spp15.local`. Cancelling cascades correctly. |
| **M5: Shop-floor UI** | `SPPQualityControlEntry.tsx` built per `02-frontend-dash.md`. Scanner focus management verified end-to-end on a real tablet. Template-missing block + on-demand sync modal wired. | Console frontend | E2E suite green on staging tablet. |
| **M6: End-to-End QA** | Full E2E suite (see `08-test-plan.md`) green on `console.m.frappe.cloud` (staging) with `newspp.m.frappe.cloud` + `sppmaster.frappe.cloud` as Ops/Legacy. | All environments | Production readiness review signed off. |

Dependencies: M1 blocks M2; M2 blocks M3; M3+M4 can run in parallel; M5 depends on M2; M6 is integration of all.

## Wave reconciliation

The earlier porting plan (`spp_process_docs/console_porting/04_WAVE4.md`) targeted "port Production Inspection Entry into Console Inspection". With QC moving to a separate doctype, Wave 4 is **superseded by QC milestones M3 + M4**. The cockpit and porting plan MUST be updated to reflect this.

Tasks for the porting plan cleanup (separate effort, out of scope here):

1. Mark Wave 4 obsolete in `spp_process_docs/console_porting/04_WAVE4.md`.
2. Replace references to "Console Inspection / Production family" in Waves 5–6 with "SPP Quality Control".
3. Add a note in `console_porting/00_PORTING_PLAN.md` linking to this spec.

## History

| Date | Event |
|---|---|
| 2026-05-01 | Console Inspection (Phase 3 unified doctype) shipped, originally scoped for Compound + Production + future Other families. |
| 2026-05 | Production-line and incoming/final-visual QC determined to not fit the Console Inspection mould (different lifecycle, identity, actor split). |
| 2026-05-19 | Decision recorded: Console Inspection scope narrowed to **Compound family only**. QC delivered as separate `SPP Quality Control` doctype. This spec authored. |
| (future) | M1–M6 rollout per milestones above. |

## Sign-off gate

Each milestone requires:

- All unit + integration tests green (per `08-test-plan.md`).
- Code review checklist signed (per program charter conventions).
- Cockpit doc updated to reflect any deviation from spec.
- `03-alignment-reports/alignment_report_spp_quality_control.md` re-validated against any new deviation.

No milestone advances without sign-off on the prior milestone's exit criteria.
