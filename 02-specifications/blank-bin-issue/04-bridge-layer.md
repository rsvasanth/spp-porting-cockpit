# 04 — Bridge layer

## Current Bridge status

No verified `BLANK_BIN_ISSUE` mapping or `populate_blank_bin_issue_fields` function was found in the current Bridge search.

| Bridge artifact | Status |
|---|---|
| `Legacy Sync Mapping` seed for `BLANK_BIN_ISSUE` | Not found. |
| Python populate helper | Not found. |
| Direct whitelisted submit helper | Not found. |
| Idempotency rule | Not defined for BBI. |

## Legacy field contract

Bridge must create Legacy `Blank Bin Issue` with parent fields that match the Desk form:

| Legacy parent field | Source |
|---|---|
| `scan_production_lot` | Scanned lot barcode / Job Card batch code. |
| `scan_bin` | Scanned physical bin barcode. |
| `job_card` | Resolved Job Card name. |
| `bin` | Asset name for the bin. |
| `production_item` | Job Card production item. |
| `qty_to_manufacture` | Job Card for quantity. |
| `press` | Job Card workstation. |
| `mould` | Job Card mould reference. |
| `bin_weight` | Asset bin weight. |
| `compound` | Active Item Bin Mapping compound. |
| `spp_batch_number` | Active Item Bin Mapping SPP batch number. |
| `qty` | Active Item Bin Mapping qty. |
| `asset_name` | Asset display name. |

The child table must receive the same values and preserve `is_completed = 0` unless the record is being re-synced after MPE completion.

## Populate vs declarative mapping

BBI looks simple enough for declarative field mappings, but scan validation is not simple. A safe Bridge path should either:

| Option | Pros | Risk |
|---|---|---|
| Declarative mapping only | Simple and consistent with many processes. | Trusts Console payload too much; may bypass legacy barcode validation semantics. |
| Python populate helper | Can re-resolve Job Card, Asset, Item Bin Mapping, BOM compound. | More code, but better parity. |

Recommendation for spec readers: use a populate helper unless Console backend already proves the payload was resolved through authoritative replicated masters.

## Drift to test

The prototype branch uses `context_data.item`, `batch`, and `actual_qty`; legacy expects `production_item`, `spp_batch_number`, and `qty`. If a future mapping uses branch payload names directly, Legacy child rows will be wrong or incomplete.

