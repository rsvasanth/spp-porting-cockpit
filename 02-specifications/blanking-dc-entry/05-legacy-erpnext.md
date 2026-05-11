# 05 - Legacy ERPNext

## Legacy doctype

| Doctype | Role |
|---|---|
| `Blanking DC Entry` | Parent transaction |
| `Blanking DC Item` | Child rows for clip/bin/weight |
| `Item Bin Mapping` | Tracks material currently in a bin |
| `Asset Movement` | Moves physical bin asset location |

## Active submit path

The current `on_submit` path emphasizes Asset Movement and bin mapping. Work Order / manufacture / Material Transfer paths exist in the file, but are commented or helper-only in the active submit path.

Active submit:

| Step | Behavior |
|---|---|
| 1 | Validate SPP Settings `from_location` and `to_location` |
| 2 | `create___asset_movement(self, spp_settings)` |
| 3 | For each row, create `Item Bin Mapping` unless `from_blank_bin_inward` |
| 4 | Create and submit `Asset Movement` |

## Legacy validation

Legacy `validate_clip_barcode(batch_no, item_produced)` does more than Console validation:

| Check | Legacy behavior |
|---|---|
| Clip active mapping | Joins `Item Clip Mapping` to `Sheeting Clip` by `barcode_text` |
| BOM | `validate_compound(compound, item_produced)` |
| Stock | Looks up `Item Batch Stock Balance` via `mix_barcode`, `sheeting_clip`, warehouse, and `spp_batch_number` |

Console's `validate_blanking_clip_barcode` currently does only the active mapping and qty checks.

## Bin validation

Legacy `validate_asset_barcode` resolves `Asset` by `barcode_text`, checks location, tare weight, and active/released state depending on `from_blank_bin_inward`.

The current Console Dash has no `from_blank_bin_inward` branch.

## Downstream effect

Legacy Item Bin Mapping row contains:

| Field | Source |
|---|---|
| `compound` | child `scanned_item` |
| `qty` | child `net_weight` |
| `blanking__bin` | child `bin_code` |
| `spp_batch_number` | child batch trace |
| `mat` | item to produce |

This row is what downstream bin issue / moulding flows will scan later.

## Diagnostic

After a Legacy BDE submit:

```python
doc = frappe.get_last_doc("Blanking DC Entry")
print(doc.name, doc.stock_entry_reference, doc.posting_date)
for row in doc.items:
    print(row.scanned_item, row.spp_batch_number, row.bin_code, row.net_weight)
    print(frappe.db.get_all("Item Bin Mapping", {
        "blanking__bin": row.bin_code,
        "is_retired": 0
    }, ["name", "compound", "qty", "spp_batch_number"]))
```

Also inspect latest `Asset Movement` for the bin asset.

## What Hermes workers can change

| Change | Risk |
|---|---|
| Change active submit path to stock-entry path | High; changes business semantics |
| Remove Asset Movement | High; physical bin location tracking breaks |
| Remove BOM check from legacy validation | Medium/high |
| Change Item Bin Mapping fields | High; downstream bin scans depend on them |
