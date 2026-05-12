# 03 — Console backend (planned)

> Shares the orchestration scaffold from MB Mixing. This file documents the **planned** Console-side function.

## Planned dispatch

```python
# api.py:initialize_submission (planned addition)
elif process_code == "BLANK_BIN_INWARD":
    create_local_blank_bin_inward_entry(prelim_payload, reference_id)
```

`update_local_domain_record.legacy_doctype_map` would extend to include:
```python
"BLANK_BIN_INWARD": "Console Blank Bin Inward Entry",
```

Module-level `apply_bridge_result.parent_doctypes` list extends to include `"Console Blank Bin Inward Entry"`.

## Planned `create_local_blank_bin_inward_entry`

```python
def create_local_blank_bin_inward_entry(payload, reference_id):
    """Mirror BBIE payload locally. Identity = bin_code + reference_id."""
    ctx = payload.get("context", {})
    posting_date, posting_time = _backdate_fields(ctx)
    return _safe_local_create(
        "Console Blank Bin Inward Entry",
        {
            "bin_code":                  _pick(ctx, "bin_code"),
            "item":                      _pick(ctx, "item", "metadata.produced_item"),
            "spp_batch_number":          _pick(ctx, "spp_batch_number"),
            "gross_weight_kgs":          flt(_pick(ctx, "gross_weight_kgs")),
            "net_weight_kgs":            flt(_pick(ctx, "net_weight_kgs")),
            "move_to_cut_bit_warehouse": cint(_pick(ctx, "move_to_cut_bit_warehouse")),
            "cut_bit_batch":             _pick(ctx, "cut_bit_batch"),
            "target_warehouse":          _pick(ctx, "config.legacy_target_warehouse"),
            "operator_name":             _pick(ctx, "metadata.run_as", "operator_name"),
            "posting_date":              posting_date,
            "posting_time":              posting_time,
            "process_code":              "BLANK_BIN_INWARD",
            "payload_snapshot":          json.dumps(payload, indent=1),
        },
        reference_id,
        "create_local_blank_bin_inward_entry",
        child_rows=None,  # No child rows for BBIE per current design
    )
```

## Planned controller

`console_blank_bin_inward_entry.py`:

```python
class ConsoleBlankBinInwardEntry(Document):
    def validate(self):
        if self.flags.get("from_local_cache"):
            return
        if not self.bin_code:
            frappe.throw("Bin Code is mandatory")
        if flt(self.net_weight_kgs) <= 0:
            frappe.throw("Net Weight must be greater than zero")
        # If move_to_cut_bit_warehouse=1, cut_bit_batch is required
        if self.move_to_cut_bit_warehouse and not self.cut_bit_batch:
            frappe.throw("Cut-bit batch is required when repacking to cut-bit warehouse")

    def before_insert(self):
        self.process_code = "BLANK_BIN_INWARD"
        if not self.submitted_by:
            self.submitted_by = frappe.session.user

    def on_submit(self):
        # Standard Transaction Log upsert
        ...

    @frappe.whitelist()
    def apply_bridge_result(self, target, status, remote_name=None, error=None):
        # ── BYTE-IDENTICAL 5-step pattern from MB ──
        # Same code as Console Master Batch Mixing
        ...
```

## Validation invariants

| Invariant | Why |
|---|---|
| `bin_code` mandatory | Identity key |
| `net_weight_kgs > 0` | Sanity check |
| `cut_bit_batch` required if `move_to_cut_bit_warehouse=1` | Branching requires target batch |
| `from_local_cache` bypass | Audit-trail invariant preserved |

## Apply_bridge_result — same saga pattern

The 5-step race-safe pattern from MB Mixing's `apply_bridge_result` (and inherited by every Wave 1+ Console doctype) MUST be implemented byte-identically here.

## Helpers needed

- `_pick` — inherited, no change
- `_backdate_fields` — inherited, no change
- No new keymaps (BBIE has no child rows)

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add new field to Console BBIE doctype | Low — additive |
| Touch the 5-step pattern | **Highest** — saga regression |
| Add a new target warehouse option | Medium — coordinate with Process Template config + Bridge populate |
| Change `move_to_cut_bit_warehouse` semantics | High — affects branching across all layers |
