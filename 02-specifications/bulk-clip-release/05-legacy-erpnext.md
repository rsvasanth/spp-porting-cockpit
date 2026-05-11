# 05 - Legacy ERPNext

## Legacy doctype

| Doctype | Path |
|---|---|
| `Bulk Clip Release` | `/Users/alphaworkz/frappe-bench/apps/shree_polymer_custom_app/shree_polymer_custom_app/shree_polymer_custom_app/doctype/bulk_clip_release/` |
| Child | `Clip Release Item` |

Parent fields:

| Field | Meaning |
|---|---|
| `clip` | Desk scan field |
| `clip_release_item` | Child table of clips to release |

Child fields:

| Field | Meaning |
|---|---|
| `clip_name` | Link to `Sheeting Clip` |
| `compound` | Mapped compound item |
| `clip_barcode` | Physical barcode text |
| `spp_batch_number` | Batch trace |
| `item_clip_mapping_id` | Hidden mapping row id |

## Controller behavior

`validate` rejects an empty child table. `on_submit` concatenates `item_clip_mapping_id` values and runs:

```sql
UPDATE `tabItem Clip Mapping`
SET is_retired = 1
WHERE name IN (...)
```

This is the canonical legacy audit-document path. It retires by mapping id, not by barcode.

## Legacy scan helper

`validate_clip(clip)` resolves a physical barcode to an active mapping:

| Step | Behavior |
|---|---|
| 1 | Find `Sheeting Clip` where `barcode_text = clip` |
| 2 | Join `Item Clip Mapping` where `sheeting_clip = SC.name` and `is_retired = 0` |
| 3 | Return mapping fields for child row construction |

This is more robust than the Bridge direct helper because it explicitly resolves barcode text to clip document name.

## Downstream consumers

`Material Transfer.validate_sheeting_clips` checks whether sheeting clips have been released:

```python
check_retired = frappe.db.get_all(
    "Item Clip Mapping",
    filters={"sheeting_clip": clip.sheeting_clip, "is_retired": 0}
)
if check_retired:
    return {"status": False, "message": "The sheeting clip ... is not yet released."}
```

So BCR is a gate for material movement. If mapping retirement misses, downstream Material Transfer can reject the clip as "not yet released."

## Diagnostic

On Legacy:

```python
barcode = "..."
clip = frappe.db.get_value("Sheeting Clip", {"barcode_text": barcode}, "name")
active = frappe.db.get_all(
    "Item Clip Mapping",
    filters={"sheeting_clip": clip, "is_retired": 0},
    fields=["name", "compound", "spp_batch_number", "qty"]
)
print(clip, active)
```

After release, `active` should be empty.

## What Hermes workers can change

| Change | Risk |
|---|---|
| Add reference fields to legacy BCR | Low/medium; helps idempotency |
| Change retirement to barcode text | Medium; must resolve doc name correctly |
| Remove legacy audit document and use direct helper only | Medium; loses CLIPR audit trail |
| Change Material Transfer release check | High; affects Blanking readiness |
