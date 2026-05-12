# 10 — Risks and decisions

## Key decision

Work Planning and Add On Work Planning must remain separate process identities in the cockpit.

## Drift findings

| ID | Drift | Impact | Recommendation |
| --- | --- | --- | --- |
| WP-DRIFT-001 | Previous Add On spec collapsed Work Planning and Add On. | Lost one-per-shift base-plan rule. | Keep separate specs and requirements. |
| WP-DRIFT-002 | No Work Planning spec existed. | Refactor workers lacked source for base planning. | Use this folder as authority. |
| WP-DRIFT-003 | Add On does not call shift uniqueness validation. | Cannot inherit Work Planning duplicate rule. | Treat as supplemental process. |
| WP-DRIFT-004 | Legacy cancel uses direct DB deletion. | Risky technical behavior. | Preserve business guard; improve technical implementation if porting. |
| WP-DRIFT-005 | Ops target fields unknown. | Lot #/mould/shift identity may be lost. | Verify Ops Work Order / Job Card custom fields. |

## Load-bearing invariants

| Invariant | Why |
| --- | --- |
| One Work Planning per date + shift series | Defines official shift plan |
| Multiple rows per Work Planning | One shift can produce multiple products |
| Target qty from Work Plan Item Target | Quantities are master-data driven |
| Job Card Lot # is downstream identity | BBI/MPE depend on it |
| Downstream BBI/MPE block cancel | Prevents deleting executed plan |

## Open questions

| Question | Recommended answer |
| --- | --- |
| Should Console create separate `Console Work Planning`? | Yes |
| Should Work Planning use Console-authored Lot # format or Legacy Job Card batch code? | Decide during port; preserve downstream scan compatibility |
| Should cancellation still delete WO/JC? | Prefer controlled cancellation, not direct deletion |
| Should Add On require a link to base Work Planning? | Useful, but not present in Legacy; treat as future enhancement |
