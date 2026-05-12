# 07 — End-to-end flow

## Happy path

1. Supervisor opens Work Planning for a date and shift.
2. System validates supervisor scan.
3. Supervisor adds multiple item / press / mould rows.
4. System validates target quantities against `Work Plan Item Target`.
5. System validates BOM availability.
6. System checks no submitted Work Planning already exists for the same date + shift series.
7. Work Planning is submitted.
8. Supervisor triggers Work Order / Job Card creation.
9. Legacy creates Work Orders and native Job Cards.
10. Job Cards receive Lot #, barcode, shift, supervisor, mould, and press settings.
11. Work Plan Item rows receive Job Card and Lot #.
12. Downstream BBI / Inspection / MPE scan or reference the Lot #.

## Duplicate shift path

1. A submitted Work Planning already exists for date + shift series.
2. Supervisor tries to submit another Work Planning for the same key.
3. Legacy blocks with the existing plan reference.
4. If extra work is required, supervisor should use Add On Work Planning.

## Cancellation path

1. User cancels Work Planning.
2. System checks child Job Card Lot # against submitted Blank Bin Issue.
3. System checks child Job Card Lot # against submitted Moulding Production Entry.
4. If either exists, cancellation is blocked.
5. If neither exists, linked Job Cards, Work Orders, and Moulding Serial No rows are cleaned.

## Console port target

Console should retain the same business checkpoints but can improve technical safety:

| Legacy behavior | Console target |
| --- | --- |
| Manual helper after submit | Orchestrated process leg |
| Direct DB cleanup on cancel | Controlled cancellation workflow |
| Shift duplicate validation | Same invariant |
| Job Card Lot # | Same downstream identity |
