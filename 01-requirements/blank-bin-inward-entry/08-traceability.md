# Traceability

## Source Map

| Area | Source |
| --- | --- |
| Requirement source | Legacy `blank_bin_inward_entry.py`, BBIE spec, `spp15.local` records |
| Spec | `02-specifications/blank-bin-inward-entry/` |
| Legacy DocType | `shree_polymer_custom_app/.../doctype/blank_bin_inward_entry/` |
| Console process | `BLANK_BIN_INWARD` |

## FR Mapping

| Requirement IDs | Evidence |
| --- | --- |
| FR-BIE-001 to FR-BIE-008 | Legacy schema and `validate` |
| FR-BIE-009 to FR-BIE-016 | Legacy `on_submit`, `asset_movement`, `make_stock_entry` |
| FR-BIE-017 | BBIE Ops spec recommendation |
| FR-BIE-018 | Process split correction |

## NFR / BR Mapping

| Requirement IDs | Evidence |
| --- | --- |
| NFR-BIE-001 to NFR-BIE-011 | BBIE spec and legacy rollback logic |
| BR-BIE-001 to BR-BIE-011 | Legacy branch logic and site-record counts |

## Drift Findings

| ID | Drift | Impact | Required correction |
| --- | --- | --- | --- |
| DRIFT-BIE-001 | Old requirement pack grouped BBIE under `blanking`. | Branch semantics were buried. | Use `blank-bin-inward-entry` pack. |
| DRIFT-BIE-002 | Earlier docs framed normal inward as default. | Site records show repack path dominates. | Treat cut-bit path as primary tested path. |
| DRIFT-BIE-003 | Spec labels several BBIE pieces as planned, but legacy has active production records. | Requirements must not mark BBIE as theoretical. | Use legacy/site as authority. |
| DRIFT-BIE-004 | Ops handler is planned, not verified shipped. | Console/Ops alignment unknown. | Mark implementation review needed. |
| DRIFT-BIE-005 | Stock refs can be comma-separated across rows. | Refactor may assume single ref. | Preserve or normalize deliberately. |

## Change Log

| Date | Change | By |
| --- | --- | --- |
| 2026-05-12 | Split BBIE from grouped `blanking` requirement pack and checked `spp15.local` records. | Codex |
