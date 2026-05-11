# 05 — Legacy ERPNext (v15) — `Material Transfer`

**App:** `apps/shree_polymer_custom_app`
**Doctype:** `Material Transfer` (a custom legacy doctype, **NOT** ERPNext's Stock Entry)
**Bench:** `spp15.local` ↔ `sppmaster.frappe.cloud`

## What `Material Transfer` is on this legacy bench

Unlike Stock Entry (ERPNext native), `Material Transfer` is a custom
doctype defined by `shree_polymer_custom_app`. It's used for material
movements that need richer metadata than standard SE:
- `material_transfer_type` (Select) — discriminates between flows
- `batches` child table (Material Transfer Item) — output line rows
- `sheeting_clip` child table — clip-specific metadata
- `cutbit_qty` aggregate
- `stock_entry_ref` field — links to a Stock Entry that gets created on submit

The legacy app's `Material Transfer` controller's `on_submit` typically
creates a Stock Entry (purpose = Material Transfer or Repack) as a side
effect, generating the actual stock ledger movement.

## Why a separate doctype (not a Stock Entry directly)

| Reason | Detail |
|---|---|
| Multi-row outputs with metadata | Stock Entry's items table can't carry sheeting-clip-specific metadata |
| Material transfer type discrimination | Different types need different downstream behavior; SE's `stock_entry_type` isn't granular enough |
| Aggregate fields like `cutbit_qty` | Not present on native SE |
| Stock Entry generated as a side effect | Material Transfer.on_submit triggers SE creation with the right type and batches |

## Material Transfer fields the Bridge writes

| Legacy field | Source from Console payload |
|---|---|
| `stock_entry_ref` | Console `reference_id` (idempotency key) |
| `transfer_date` | `posting_date` |
| `employee` | `employee_code` |
| `item` | `source_item` (the input compound item) |
| `scan_spp_batch_number` | `source_batch` |
| `qty` | `target_qty` (the source compound's qty being transferred) |
| `source_warehouse` | `config.legacy_source_warehouse` |
| `target_warehouse` | `config.legacy_target_warehouse` |
| `material_transfer_type` | `"Transfer Compound to Sheeting Warehouse"` (literal) |
| `batches` (child) | One row per output line — see below |
| `sheeting_clip` (child) | Clip-specific rows — see below |

## `batches` child rows (Material Transfer Item)

Each output line from the Sheeting submission becomes one `batches` row:

| Legacy field | Source |
|---|---|
| `item_code` | `items[i].item_code` |
| `batch_no` | `items[i].batch_no` |
| `scan_barcode` | `items[i].batch_no` (same value as batch_no — dual-mapped) |
| `qty` | `items[i].qty` |
| `is_cut_bit_item` | Backfilled by `populate_sheeting_fields` (1 if `"Cutbit_"` prefix on batch_no, else 0) |
| `mix_barcode` | Synthesized by Bridge as `{item_code}_{original_batch}` |

## `sheeting_clip` child rows (Sheeting Clip)

Each clip row from `payload.sheeting_clip` becomes one legacy
`sheeting_clip` row. The mapping is a wholesale list-replication
(`console_field: "sheeting_clips"` → `legacy_field: "sheeting_clip"`),
so the Console payload's clip array goes verbatim to legacy.

## Material Transfer's on_submit (legacy controller behavior)

(The controller code lives in
`apps/shree_polymer_custom_app/.../doctype/material_transfer/material_transfer.py`
— not read in this spec's research pass, but the behaviour is known
from the Bridge response handling.)

When the Bridge calls `legacy_doc.submit()` on the Material Transfer:

1. The controller validates the batches + sheeting_clip rows
2. Creates a Stock Entry (purpose configured by `material_transfer_type`)
   - For `"Transfer Compound to Sheeting Warehouse"`: SE purpose = Material Transfer
   - Each `batches` row → one SE Detail row with `is_cut_bit_item` honored
   - `mix_barcode` from the synthesized format propagates to SE Detail
3. Submits the SE
4. Updates `stock_entry_ref` on the Material Transfer header (loop back)
5. Stock Ledger Entries created by Frappe automatically

The Bridge then reads back `stock_entry_ref` and extracts
`spp_batch_number` from the SE's FG row to return as `legacy_spp_batch_no`
in the response.

## Documents created on legacy for one Sheeting submission

| Document | Created by | Notes |
|---|---|---|
| `Material Transfer` (with `material_transfer_type="Transfer Compound to Sheeting Warehouse"`) | `legacy_doc.insert() + submit()` in Bridge | Has both `batches` and `sheeting_clip` child rows |
| `Stock Entry` (purpose: Material Transfer) | Material Transfer's on_submit | Items table mirrors `batches`; FG rows have `mix_barcode` set |
| `Stock Ledger Entry` × N | Auto by Frappe on SE submit | One per item per warehouse change |
| `Sheeting Clip` records | Side effect of Material Transfer.on_submit | One per clip in `sheeting_clip` table; linked to the source compound |
| `Batch` (for each FG output) | Auto by Frappe if items have `has_batch_no=1` | Each clip and cut-bit may get its own batch |

## Downstream legacy consumers

### Cut Bit Transfer → reads cut-bit batches from this Sheeting submission

Cut-bit output rows (with `is_cut_bit_item=1`) are eligible inputs for
Cut Bit Transfer. The legacy `Cut Bit Transfer` controller looks up
these rows via the cut-bit batch number prefix `Cutbit_`.

### Blanking → reads clip barcodes from this Sheeting submission

Clip output rows (with `is_cut_bit_item=0`) get registered in legacy
`Sheeting Clip` doctype. Downstream Blanking scans the clip barcode
which resolves back to:
- Source compound's batch (via clip mapping)
- Original mix_barcode (via the synthesized `{item_code}_{original_batch}`)
- Stock Entry that this Sheeting submission produced

This is why `_lookup_legacy_stock_entry` in the Bridge has the strategy
`mix_barcode == "{item_code}_{spp_batch_no}"` — that's the Sheeting
synthesis format. **Removing this strategy breaks Compound Inspection
on sheeted compounds.**

## `WAREHOUSE_MAP` fallbacks (same risk as MB)

```python
# populate_sheeting_fields
if not doc.source_warehouse:
    doc.source_warehouse = "U3-Store - SPP INDIA"
if not doc.target_warehouse:
    doc.target_warehouse = "Sheeting Warehouse - SPP INDIA"
```

Hardcoded defaults. If the Console Process Template's warehouse rows are
misconfigured, the Bridge silently uses these defaults. Same monitoring
risk as MB's value-map default.

## What Hermes workers must NOT touch on legacy

Same advice as MB:
- `Material Transfer` controller logic (creates SE, manages clip records)
- `Sheeting Clip` doctype schema or validation
- The `material_transfer_type` Select options
- Cross-doctype lookups by `mix_barcode` synthesis format

If a legacy-side change is required:
1. Surface in `10-risks-and-decisions.md`
2. Propose change on legacy bench, not via Bridge
3. Test on staging with both clip + cut-bit paths
