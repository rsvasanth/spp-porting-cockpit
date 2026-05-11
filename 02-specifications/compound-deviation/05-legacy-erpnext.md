# 05 — Legacy ERPNext (v15) — `populate_compound_deviation_fields`

**File:** `apps/shree_polymer_legacy_bridge/shree_polymer_legacy_bridge/sync_api.py:1319`

This is the **most important file in the Compound Deviation spec.** The
Bridge's empty-mapping pattern (see `04-bridge-layer.md`) delegates all
field population to this Python function, which in turn delegates most
work to **shared helpers** that were extracted in the 2026-04-30 refactor.

## The thin-wrapper architecture

```python
def populate_compound_deviation_fields(doc, data=None):
    """Populate a legacy Compound Inspection from a Console Deviation payload.

    Architectural note: from Legacy's perspective, a Compound Deviation IS a
    Compound Inspection — both create the same legacy doctype. This function
    delegates ALL identity/SE/readings logic to the same helpers as
    populate_compound_inspection_fields, then layers on the deviation-specific
    extras (QM signoff, status override, deviation reason).

    The previous implementation had ~200 lines of duplicated SE lookup logic
    that drifted out of sync with the Console payload shape (resulting in the
    "Stock Entry reference not found" bug when identity moved from
    compound_deviation_data into compound_inspection_data). This thin wrapper
    eliminates the drift surface."""
    if not data: return

    # ── Step 1: SAME identity + SE + readings pipeline as Compound Inspection ──
    identity  = _resolve_compound_identity(data)
    se_lookup = _lookup_legacy_stock_entry(identity)
    _apply_compound_identity_to_doc(doc, identity, se_lookup)
    _apply_compound_header_to_doc(doc, data)
    _apply_compound_readings_to_doc(doc, data)

    # ── Step 2: Source warehouse mapping (Compound Inspection WH → U3 Store) ──
    dev_data = data.get("compound_deviation_data") or {}
    if not doc.get("source_warehouse"):
        doc.source_warehouse = WAREHOUSE_MAP.get(
            dev_data.get("source_warehouse", ""),
            "U3-Store - SPP INDIA"   # ← fallback
        )

    # ── Step 3: Quantity fields (Deviation-specific shape: dev_data.qty) ──────
    if dev_data.get("qty") is not None:
        if not doc.get("batch_qty"):    doc.batch_qty    = dev_data["qty"]
        if not doc.get("transfer_qty"): doc.transfer_qty = dev_data["qty"]

    if dev_data.get("operator_id") and not doc.get("operator_id"):
        doc.operator_id = dev_data["operator_id"]
    if dev_data.get("operator_name") and not doc.get("operator_name"):
        doc.operator_name = dev_data["operator_name"]

    # ── Step 4: Apply Deviation-specific extras ──
    _apply_deviation_extras(doc, data)
```

**Each `if not doc.get(field):` pattern is intentional idempotency** — if
the mapping engine (or a prior helper) already populated a field, this
function doesn't overwrite. This makes re-runs safe.

## Shared helpers (also used by Compound Inspection)

### `_resolve_compound_identity(payload_data)` — `sync_api.py:668`

Extracts canonical identity from the payload. For Deviation, reads
`compound_inspection_data` block (same shape as Accepted CI):

```python
def _resolve_compound_identity(payload_data):
    """Extract canonical compound identity from payload."""
    ci = payload_data.get("compound_inspection_data") or {}
    def _pick(*keys):
        for k in keys:
            v = ci.get(k) or payload_data.get(k)
            if v: return v
        return None
    return {
        "mix_barcode":   _pick("mix_barcode"),
        "spp_batch_no":  _pick("spp_batch_no"),
        "item_code":     _pick("item_code"),
        "batch_no":      _pick("batch_no"),
        "compound_ref":  _pick("compound_ref"),
        "dc_receipt_id": _pick("dc_receipt_id"),
    }
```

### `_lookup_legacy_stock_entry(identity)` — `sync_api.py:702`

The **6-strategy SE lookup chain** that drove the Bridge refactor. Tries:

1. `mix_barcode == spp_batch_no` (most common path)
2. `spp_batch_number == stripped spp_batch_no` (strips `C_` prefix)
3. `spp_batch_number == spp_batch_no` (direct match)
4. `mix_barcode == payload mix_barcode` (when different)
5. `mix_barcode == "{item_code}_{spp_batch_no}"` (legacy compound format)
6. `batch_no == payload mix_barcode` (last-ditch)

Each strategy survives because it covers a real production case. **Do NOT
delete strategies** without proof of zero hits.

On miss, emits a structured `frappe.log_error` with all attempted
strategies + recent draft SEs. This was the bug surface during the saga.

### `_apply_compound_identity_to_doc(doc, identity, se_lookup)` — `sync_api.py:807`

Writes the resolved identity fields onto the legacy doc. **Idempotent** —
only writes if field is currently empty:

```python
def _apply_compound_identity_to_doc(doc, identity, se_lookup):
    """SINGLE place that sets stock_id, stock_entry_reference, dc_receipt_id,
    batch_no, mix_barcode, spp_batch_no, scan_compound, compound_ref, item_code.
    Idempotent: only sets a field if currently empty."""
    legacy_barcode = identity["spp_batch_no"] or identity["mix_barcode"]

    if not doc.get("scan_compound"):  doc.scan_compound  = legacy_barcode
    if not doc.get("mix_barcode"):    doc.mix_barcode    = legacy_barcode
    if not doc.get("spp_batch_no"):   doc.spp_batch_no   = legacy_barcode
    if not doc.get("batch_no"):       doc.batch_no       = se_lookup["batch_no"]
    if not doc.get("stock_id"):       doc.stock_id       = se_lookup["stock_id"]
    if not doc.get("stock_entry_reference"):
        doc.stock_entry_reference = se_lookup["stock_id"]
    if not doc.get("dc_receipt_id"):  doc.dc_receipt_id  = se_lookup["dc_receipt_id"]
    if not doc.get("item_code"):      doc.item_code      = identity["item_code"]
    if not doc.get("compound_ref"):   doc.compound_ref   = identity["compound_ref"]
```

### `_apply_compound_header_to_doc(doc, data)`

Sets posting_date, inspection_date, batch_qty, transfer_qty, item_to_manufacture from the `compound_inspection_data` block.

### `_apply_compound_readings_to_doc(doc, data)`

Walks `compound_inspection_data.readings` (the QC test rows) and creates
matching child rows on the legacy Compound Inspection's reading child
table. Same readings used for both Accepted CI and Deviation.

## Deviation-specific helper — `_apply_deviation_extras`

`sync_api.py:971`:

```python
def _apply_deviation_extras(doc, payload_data):
    """Apply Compound Deviation-specific extras on top of a populated CI doc.

    Called AFTER the shared identity/SE/readings helpers have populated
    the CI body. Adds the things that distinguish a Deviation from a
    regular Compound Inspection:
      • status              (QM's decision: Accepted / Rejected / Rework)
      • scan_quality_approver + quality_approver_id + quality_approver_name
      • remarks             (deviation_reason)
      • posting_date / posting_time  (deviation event time)
      • cavity_no fallback  (see comment below)"""
    dev_data = payload_data.get("compound_deviation_data") or {}

    if dev_data.get("status"):
        doc.status = dev_data["status"]

    if dev_data.get("approver_id"):
        doc.scan_quality_approver = dev_data["approver_id"]
        doc.quality_approver_id   = dev_data["approver_id"]
        doc.quality_approver_name = dev_data.get("approver_name") or ""

    if dev_data.get("deviation_reason"):
        doc.remarks = dev_data["deviation_reason"]

    if dev_data.get("posting_date"):    doc.posting_date = dev_data["posting_date"]
    if dev_data.get("inspection_time"): doc.posting_time = dev_data["inspection_time"]

    # ── cavity_no fallback (TEMPORARY — track follow-up task) ──
    # cavity_no was declared in the Console Process Template + Bridge mapping
    # but never wired through end-to-end on Console: no field on the Console
    # Inspection doctype, no input on the Dash UI. So the Compound Deviation
    # payload never carries cavity_no, and Legacy Compound Inspection.validate()
    # rejects with MandatoryError.
    #
    # Until cavity_no is wired through Console, default to 1 here so Deviations
    # can submit. Most compounds run on a single cavity, so 1 is the right
    # statistical default — but log every fallback so ops can spot any
    # production runs that genuinely had multi-cavity moulds.
    #
    # Bug ref: Reference ID 1777721078171 (staging, 2026-05-02).
    if not doc.get("cavity_no"):
        try:
            frappe.log_error(
                title="Bridge: Deviation cavity_no defaulted to 1",
                message=(
                    "compound_inspection_data.cavity_no missing from Compound "
                    "Deviation payload — defaulted to 1 on the Legacy Compound "
                    "Inspection. Track Console wiring (doctype field + Dash UI "
                    "input + payload include) as a follow-up task.\n\n"
                    f"scan_compound: {doc.get('scan_compound')!r}\n"
                    f"batch_no:      {doc.get('batch_no')!r}\n"
                    f"reference_id:  {payload_data.get('reference_id')!r}\n"
                ),
            )
        except Exception:
            pass   # never block sync on logging failure
        doc.cavity_no = 1
```

## The `cavity_no` active TODO

**This is the highest-impact active bug in the Compound Deviation flow.**

| Aspect | Detail |
|---|---|
| Bug ref | Reference ID `1777721078171` (staging, 2026-05-02) |
| Symptom | Legacy `Compound Inspection.validate()` throws `MandatoryError: cavity_no` |
| Cause | Field declared in Console Process Template + Bridge mapping rows, but never wired through Console (no doctype field, no Dash input, payload doesn't carry it) |
| Mitigation | Hardcoded fallback to `cavity_no = 1` + structured log every time |
| Risk | Multi-cavity moulds (rare) get incorrectly recorded as single-cavity; production data quality suffers |
| Resolution path | Add `cavity_no` to `Console Inspection` doctype + add Dash input on CompoundDeviationEntry.tsx + include in `compound_inspection_data.cavity_no` payload + remove the fallback |

**Tracking item flagged in `10-risks-and-decisions.md`** — needs decision
on whether to wire `cavity_no` properly now or accept the default-to-1
behavior long-term.

## `WAREHOUSE_MAP` — Compound Inspection → U3 Store fallback

The `WAREHOUSE_MAP` constant (defined elsewhere in `sync_api.py`) maps
Console-side warehouse names to Legacy ones. For Deviation, if the
payload's `compound_deviation_data.source_warehouse` doesn't match the
map, falls back to `U3-Store - SPP INDIA`.

This is **silent** — no warning if the lookup misses. A Hermes worker who
adds a new warehouse without updating `WAREHOUSE_MAP` will see Deviations
land in `U3-Store` regardless of what the operator selected. Same risk
shape as the `inward_material_type` defensive default flagged in MB's
risks.

## What lands on Legacy for one Compound Deviation submission

| Document | Created by | Notes |
|---|---|---|
| `Compound Inspection` (status set by QM) | `legacy_doc.insert()` + `submit()` in Bridge | Same doctype as a regular CI, distinguished by `status="Accepted"/"Rejected"/"Rework"` + `quality_approver_*` fields populated + `remarks` carries the reason |
| Stock Entry (status-conditional) | CI controller's `on_submit` | If `status="Accepted"`: Material Transfer SE (overrides original rejection). If `Rejected`: scrap/write-off SE. If `Rework`: no SE. |
| `Legacy Bridge Log` | `sync_process_transaction` | `status=Success`, `reference_name` = CI name |

## What Hermes workers MUST NOT touch

- `_resolve_compound_identity`, `_lookup_legacy_stock_entry`,
  `_apply_compound_identity_to_doc`, `_apply_compound_readings_to_doc`,
  `_apply_compound_header_to_doc` — **shared with Compound Inspection.**
  Changes affect both flows.
- The 6-strategy SE lookup — each strategy survives because it covers a
  real case. Removing requires proof of zero hits in production logs.
- The `WAREHOUSE_MAP` fallback — used by multiple flows; touch only with
  full audit of consumers.
