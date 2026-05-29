# Legacy Completion Contracts

**Owner:** `shree_polymer_legacy_bridge` (transitional app)
**Status:** Design landed 2026-05-29; doctypes + seeder shipped on bridge branch `feat/legacy-completion-contract`.
**Companion:** [`alignment_report_blanking_dc_entry.md`](../../03-alignment-reports/alignment_report_blanking_dc_entry.md) Bug 2 background.

## Why

Today's Bridge verifier uses a hardcoded contract — "WO + JC + SE submitted" — that's correct for MBM/FBM/Sheeting/Cut Bit but wrong for BDE, BBI, BBIE, MPE. Result: legitimate completions return Failed, blocking Console auto-submit.

A declarative per-process contract fixes this. Each process tells the Bridge what "legacy complete" means by enumerating expected linked records. The verifier walks the contract after dispatch and returns Success / Partial / Failed.

## Architectural choice — lives in Bridge, not Console

Console Process Template describes Ops actions only. The Bridge owns legacy concerns. When `shree_polymer_legacy_bridge` is uninstalled at end of porting, the contracts + verifier code + doctypes go with it. No Console coupling, no leftover schema to clean up.

## Doctypes

```
Legacy Completion Contract  (parent, autoname=field:process_code)
├── process_code              # matches Console Process Template.code
├── is_active
├── description
└── rules → Table: Legacy Completion Rule

Legacy Completion Rule  (child)
├── rule_id
├── linked_doctype     # legacy DocType to check
├── linkage_field      # field on linked doctype that points to parent
├── linkage_source     # dot-path on incoming payload context
├── filters            # JSON dict of WHERE filters
├── condition          # safe_eval gate (empty = always applies)
├── min_count
├── max_count
├── on_missing         # Failed | Partial | Warning
└── description
```

Both module-owned by `shree_polymer_legacy_bridge.bridge`.

## Per-process contracts

Seeded by `shree_polymer_legacy_bridge/completion_contract_seeder.py`. Re-runs idempotently via the migration patch `seed_legacy_completion_contracts`.

### MASTER_BATCH_MIXING

| rule_id | linked_doctype | linkage_field | linkage_source | filters | on_missing |
|---|---|---|---|---|---|
| wo_submitted | Work Order | mix_reference | metadata.reference_name | docstatus=1, status NOT IN (Cancelled, Stopped) | Failed |
| se_manufactured | Stock Entry | work_order | metadata.reference_name | docstatus=1, stock_entry_type=Manufacture | Failed |

### FINAL_BATCH_MIXING

Same shape as MBM.

### SHEETING_PROCESS

| rule_id | linked_doctype | linkage_field | linkage_source | filters | on_missing |
|---|---|---|---|---|---|
| se_repack_submitted | Stock Entry | name | metadata.reference_name | docstatus=1, stock_entry_type=Repack | Failed |

### CUT_BIT_TRANSFER

| rule_id | linked_doctype | linkage_field | linkage_source | filters | on_missing |
|---|---|---|---|---|---|
| se_transfer_submitted | Stock Entry | name | metadata.reference_name | docstatus=1, stock_entry_type=Material Transfer | Failed |

### BULK_CLIP_RELEASE

| rule_id | linked_doctype | linkage_field | linkage_source | filters | on_missing |
|---|---|---|---|---|---|
| clip_mapping_retired | Item Clip Mapping | sheeting_clip | release_data.clips | is_retired=1 | Failed |

### BLANKING_DC_ENTRY

| rule_id | linked_doctype | linkage_field | linkage_source | filters | condition | on_missing |
|---|---|---|---|---|---|---|
| parent_submitted | Blanking DC Entry | stock_entry_reference | metadata.reference_id | docstatus=1 | — | Failed |
| bin_mapping_per_row | Item Bin Mapping | blanking__bin | items.bin_code | is_retired=0 | `context.get('from_blank_bin_inward') in (None, '', '0', 0, False)` | Failed |
| asset_moved | Asset Movement Item | asset | items.bin_code | docstatus=1 | — | Partial (legacy may skip when src==target) |

### BLANK_BIN_INWARD

| rule_id | linked_doctype | linkage_field | linkage_source | filters | condition | on_missing |
|---|---|---|---|---|---|---|
| parent_submitted | Blank Bin Inward Entry | name | metadata.reference_name | docstatus=1 | — | Failed |
| asset_moved_when_movement | Asset Movement Item | asset | items.bin_code | docstatus=1 | `context.get('purpose') == 'Asset Movement'` | Partial |
| se_repack_when_repack | Stock Entry | source_document_name | metadata.reference_name | docstatus=1, stock_entry_type=Repack | `context.get('purpose') == 'Repack'` | Failed |

### BLANK_BIN_ISSUE

| rule_id | linked_doctype | linkage_field | linkage_source | filters | on_missing |
|---|---|---|---|---|---|
| parent_submitted | Blank Bin Issue | name | metadata.reference_name | docstatus=1 | Failed |

(Single rule — BBI has no downstream legacy side effects.)

### WORK_PLANNING

| rule_id | linked_doctype | linkage_field | linkage_source | filters | on_missing |
|---|---|---|---|---|---|
| parent_submitted | Work Planning | name | metadata.reference_name | docstatus=1 | Failed |
| wo_per_item | Work Order | work_planning_ref | metadata.reference_name | docstatus=1, status NOT IN (Cancelled, Stopped) | Failed |

### MOULDING_PRODUCTION_ENTRY

| rule_id | linked_doctype | linkage_field | linkage_source | filters | on_missing |
|---|---|---|---|---|---|
| parent_submitted | Moulding Production Entry | name | metadata.reference_name | docstatus=1 | Failed |
| se_manufactured | Stock Entry | mpe_ref | metadata.reference_name | docstatus=1, stock_entry_type=Manufacture | Failed |
| bin_retired | Item Bin Mapping | blanking__bin | items.bin_code | is_retired=1 | Partial |

### COMPOUND_INSPECTION

| rule_id | linked_doctype | linkage_field | linkage_source | filters | on_missing |
|---|---|---|---|---|---|
| parent_submitted | Compound Inspection | name | metadata.reference_name | docstatus=1 | Failed |

(Rejected CIs don't reach the bridge — verifier never runs for them.)

### COMPOUND_DEVIATION

| rule_id | linked_doctype | linkage_field | linkage_source | filters | condition | on_missing |
|---|---|---|---|---|---|---|
| parent_submitted | Compound Deviation | name | metadata.reference_name | docstatus=1 | — | Failed |
| se_material_transfer_when_accepted | Stock Entry | deviation_ref | metadata.reference_name | docstatus=1, stock_entry_type=Material Transfer | `context.get('status') == 'Accepted'` | Failed |

## Three-state response

| Status | Console reaction |
|---|---|
| Success | `legacy_sync_status = Synced` → contributes to auto-submit |
| Partial | `legacy_sync_status = Synced` with `legacy_warnings` populated → auto-submit proceeds; UI surfaces warnings |
| Failed | `legacy_sync_status = Failed` → blocks auto-submit |

Critically, **Partial maps to Synced for Console's purposes** — the chain progressed enough that the parent record can be considered complete, even if a downstream side effect is still in flight (or never expected for that branch).

## Verifier algorithm — sketch

```python
def run_legacy_completion_verifier(process_code, context, parent_name) -> CompletionResult:
    contract = frappe.db.get_value(
        "Legacy Completion Contract",
        {"process_code": process_code, "is_active": 1},
        "name",
    )
    if not contract:
        return CompletionResult(status="Success")  # no contract = legacy unconstrained

    contract_doc = frappe.get_doc("Legacy Completion Contract", contract)
    failures, warnings = [], []

    for rule in contract_doc.rules:
        if not rule.is_active:
            continue
        if rule.condition and not safe_eval(rule.condition, {"context": context}):
            continue

        candidates = resolve_linkage_source(context, rule.linkage_source, parent_name)
        # candidates is always a list

        for value in candidates:
            filters = {**(json.loads(rule.filters) if rule.filters else {}),
                       rule.linkage_field: value}
            count = frappe.db.count(rule.linked_doctype, filters)

            if count < (rule.min_count or 1):
                msg = (f"Rule {rule.rule_id}: expected >={rule.min_count} "
                       f"{rule.linked_doctype} for {rule.linkage_source}={value}, "
                       f"found {count}")
                if rule.on_missing == "Failed":
                    failures.append(msg)
                else:
                    warnings.append({rule.on_missing: msg})

            if rule.max_count and count > rule.max_count:
                failures.append(f"Rule {rule.rule_id}: too many "
                                f"{rule.linked_doctype}: got {count} (max {rule.max_count})")

    if failures:
        return CompletionResult(status="Failed", reasons=failures, warnings=warnings)
    if warnings:
        return CompletionResult(status="Partial", warnings=warnings)
    return CompletionResult(status="Success")
```

## Retirement story

When legacy goes away end-of-porting:

```bash
bench --site <site> uninstall-app shree_polymer_legacy_bridge
```

This removes the Bridge app, both doctypes, both seeders, the verifier code, and every `Legacy Completion Contract` row. Console doesn't notice — there's no schema reference on Console. Ops doesn't notice. The legacy-completion concept disappears with legacy.

## Phase ordering

| Phase | Scope | Status |
|---|---|---|
| 0 | Cockpit doc | ✓ This file |
| 1 | Doctypes (Legacy Completion Contract + Rule) | ✓ Shipped on `feat/legacy-completion-contract` |
| 2 | Seeder + migration patch | ✓ Shipped on same branch |
| 3 | Implement `completion_verifier.py` | Pending |
| 4 | Wire behind feature flag `Console Device Settings.use_declarative_legacy_verifier` | Pending |
| 5 | Flip flag for BDE only (already broken; safest first try) | Pending |
| 6 | Roll out to BBI, BBIE, Cut Bit, Sheeting one-by-one | Pending |
| 7 | Roll out to MBM, FBM, MPE, WP | Pending |
| 8 | Delete hardcoded verifier | Pending |
