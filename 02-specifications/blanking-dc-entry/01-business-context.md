# 01 - Business context

## Process position

Blanking DC Entry records the moment material from a released sheeting clip is weighed into a physical blanking bin.

```text
Sheeting Process
  -> Item Clip Mapping active
  -> Bulk Clip Release
  -> Blanking DC Entry
     - scan clip
     - scan empty bin
     - capture gross weight
     - create bin mapping
  -> downstream blanking / moulding flows consume bin material
```

## Shop-floor meaning

| Term | Meaning |
|---|---|
| Sheeting clip | Source holder carrying compound from sheeting |
| Blanking bin | Destination physical Asset/bin |
| Gross weight | Bin + material weight |
| Bin weight / tare | Empty bin weight from `Console Blanking Bin` / Legacy `Asset` |
| Net weight | Material transferred into bin |
| Item to produce | Mat/preform item selected before scanning |

## Business rule

The operator must prove three things before the row can be added:

| Proof | Validation |
|---|---|
| Clip exists and has material | Active `Console Item Clip Mapping` with qty > 0 |
| Bin is available | Active bin master, no active `Console Item Bin Mapping` |
| Weight is valid | `gross_weight > bin_weight` and `net_weight <= clip qty` |

## Main side effects

| System | Effect |
|---|---|
| Console | Local audit row + `Console Item Bin Mapping` + clip qty deduction |
| Legacy | `Blanking DC Entry` submit creates `Item Bin Mapping` and `Asset Movement` |
| Ops | Dedicated handler creates Material Transfer Stock Entry |

The split matters: Legacy treats BDE primarily as asset/bin mapping work; Ops currently treats it as stock movement from Cutbit warehouse into PreForming.

## Actors

| Actor | Responsibility |
|---|---|
| Blanker | Scans clip, scans bin, enters gross weight |
| Console Dash | Enforces scan order and gross/net checks |
| Console backend | Mirrors audit row and updates local process masters |
| Legacy Bridge | Rebuilds legacy rows and lets legacy controller create Asset Movement |
| Ops app | Creates Stock Entry transfer |

## Current story

Blanking DC Entry is the strongest example so far of **semantic drift between targets**. The Console/Dash and Legacy paths are clip-to-bin mapping flows. The Ops handler assumes material already exists as Cut Bit stock under `CB_<compound>_<spp_batch>`. That may be intended for a post-Cut-Bit route, but it is not the same story the Dash tells today.
