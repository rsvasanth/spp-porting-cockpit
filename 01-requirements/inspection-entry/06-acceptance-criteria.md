# 06 — Acceptance criteria

## AC-IE-001 — Line Inspection happy path
Given a lot with a valid moulding Job Card and active Mould Specification, when the inspector submits Line Inspection with defect rows, then IE is submitted, totals are stored, and a rejection Stock Entry is created if rejected kg is positive.

## AC-IE-002 — Patrol duplicate blocked
Given a submitted Patrol Inspection exists for the lot, when another Patrol Inspection is submitted for the same lot, then the system blocks it.

## AC-IE-003 — Final Visual duplicate allowed by legacy rule
Given a submitted Final Visual Inspection exists for the lot, when another Final Visual Inspection is created, then duplicate prevention must not block solely on lot/type.

## AC-IE-004 — Missing inspector blocked
Given lot is scanned but inspector code is missing, when the user saves/submits, then the system rejects the entry.

## AC-IE-005 — Missing child rows blocked
Given required header fields are present but no inspection items exist, when the user saves/submits, then the system rejects the entry.

## AC-IE-006 — MPE cascade updates batch
Given Line/Patrol rejection Stock Entries exist in draft and MPE is submitted for the lot, then IE batch_no and Stock Entry Detail batch_no are updated to the produced batch and draft rejection entries are submitted.

## AC-IE-007 — Final Visual rejection path
Given Final Visual Inspection has rejected quantity, when submitted, then the configured Final Visual/PDIR rejection Stock Entry path executes and updates quantity-after-rejection.

## AC-IE-008 — Future date blocked
Given posting date is in the future, when user saves/submits, then validation blocks the entry.

