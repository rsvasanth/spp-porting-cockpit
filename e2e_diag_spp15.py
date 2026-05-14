# E2E Chain Diagnostic - Find Sheeted Batches on spp15.local
import frappe

print('=' * 60)
print('SPP15.LOCAL - E2E CHAIN DIAGNOSTIC')
print('Finding batches that have been SHEETED (have Item Clip Mapping)')
print('=' * 60)

# Find CI batches that HAVE Item Clip Mapping records
icm_batches = frappe.db.sql('''
    SELECT DISTINCT spp_batch_number, COUNT(*) as records, MAX(creation) as last_sheeted
    FROM `tabItem Clip Mapping`
    WHERE is_retired = 0
    GROUP BY spp_batch_number
    ORDER BY last_sheeted DESC
    LIMIT 10
''', as_dict=1)

print('\n[STEP 0] CI Batches with Item Clip Mapping (sheeted):')
if not icm_batches:
    print('  NONE FOUND - no batches have been sheeted yet')
else:
    for r in icm_batches:
        print(f'  Batch: {r["spp_batch_number"]} | ICM Records: {r["records"]} | Last Sheeted: {r["last_sheeted"]}')

# Also check Item Bin Mapping
ibm_batches = frappe.db.sql('''
    SELECT DISTINCT spp_batch_number, COUNT(*) as records, MAX(creation) as last_issued
    FROM `tabItem Bin Mapping`
    WHERE is_retired = 0
    GROUP BY spp_batch_number
    ORDER BY last_issued DESC
    LIMIT 10
''', as_dict=1)

print('\n[STEP 0b] CI Batches with Item Bin Mapping (blank-issued):')
if not ibm_batches:
    print('  NONE FOUND')
else:
    for r in ibm_batches:
        print(f'  Batch: {r["spp_batch_number"]} | IBM Records: {r["records"]} | Last Issued: {r["last_issued"]}')

# Pick the most recent batch that has ICM records
if icm_batches:
    target_batch = icm_batches[0]['spp_batch_number']
    print(f'\n=== USING TARGET BATCH: {target_batch} ===\n')

    # Step 1: Find the Compound Inspection record
    print('[STEP 1] Compound Inspection for this batch:')
    ci = frappe.db.sql('''
        SELECT name, batch_no, inspection_type, qty, pass_qty, fail_qty,
               operator, supervisor, creation, docstatus
        FROM `tabCompound Inspection`
        WHERE batch_no = %s AND docstatus = 1
        ORDER BY creation DESC LIMIT 5
    ''', (target_batch,), as_dict=1)
    if ci:
        for r in ci:
            print(f'  CI: {r["name"]} | Type: {r["inspection_type"]} | Qty: {r["qty"]} | Pass: {r["pass_qty"]} | Fail: {r["fail_qty"]} | Op: {r["operator"]} | {r["creation"]}')
    else:
        print('  NO CI RECORDS FOUND for this batch')

    # Step 2: Item Clip Mapping (Sheeting)
    print('\n[STEP 2] Item Clip Mapping (Sheeting records):')
    icm = frappe.db.sql('''
        SELECT name, compound, sheeting_clip, spp_batch_number, qty, is_retired, creation
        FROM `tabItem Clip Mapping`
        WHERE spp_batch_number = %s
        ORDER BY creation DESC LIMIT 10
    ''', (target_batch,), as_dict=1)
    if icm:
        for r in icm:
            status = 'RETIRED' if r['is_retired'] else 'ACTIVE'
            print(f'  ICM: {r["name"]} | Clip: {r["sheeting_clip"]} | Qty: {r["qty"]} | Status: {status} | {r["creation"]}')
    else:
        print('  NO ICM RECORDS FOUND')

    # Step 3: Stock Entries for this batch (via Stock Entry Detail)
    print('\n[STEP 3] Stock Entries for this batch (via Stock Entry Detail):')
    se = frappe.db.sql('''
        SELECT se.name, se.stock_entry_type, se.docstatus, se.creation,
               sed.spp_batch_number, sed.item_code, sed.qty, sed.t_warehouse
        FROM `tabStock Entry` se
        JOIN `tabStock Entry Detail` sed ON se.name = sed.parent
        WHERE sed.spp_batch_number = %s
        ORDER BY se.creation DESC LIMIT 10
    ''', (target_batch,), as_dict=1)
    if se:
        for r in se:
            docstatus_map = {0: 'DRAFT', 1: 'SUBMITTED', 2: 'CANCELLED'}
            status = docstatus_map.get(r['docstatus'], str(r['docstatus']))
            print(f'  SE: {r["name"]} | Type: {r["stock_entry_type"]} | Status: {status} | Item: {r["item_code"]} | Qty: {r["qty"]} | Warehouse: {r["t_warehouse"]} | {r["creation"]}')
    else:
        print('  NO STOCK ENTRIES FOUND for this batch')

    # Step 4: Look for DCR / Material Transfer records for this batch
    print('\n[STEP 4] Material Transfer / DCR records for this batch:')
    mt = frappe.db.sql('''
        SELECT name, creation, docstatus
        FROM `tabMaterial Transfer`
        WHERE batch_no = %s
        ORDER BY creation DESC LIMIT 10
    ''', (target_batch,), as_dict=1)
    if mt:
        for r in mt:
            docstatus_map = {0: 'DRAFT', 1: 'SUBMITTED', 2: 'CANCELLED'}
            status = docstatus_map.get(r['docstatus'], str(r['docstatus']))
            print(f'  MT: {r["name"]} | Status: {status} | {r["creation"]}')
    else:
        print('  NO Material Transfer records found')

    # Step 5: Cut Bit Transfer records
    print('\n[STEP 5] Cut Bit Transfer records for this batch:')
    cbt = frappe.db.sql('''
        SELECT name, creation, docstatus
        FROM `tabCut Bit Transfer`
        WHERE batch_no = %s
        ORDER BY creation DESC LIMIT 10
    ''', (target_batch,), as_dict=1)
    if cbt:
        for r in cbt:
            docstatus_map = {0: 'DRAFT', 1: 'SUBMITTED', 2: 'CANCELLED'}
            status = docstatus_map.get(r['docstatus'], str(r['docstatus']))
            print(f'  CBT: {r["name"]} | Status: {status} | {r["creation"]}')
    else:
        print('  NO Cut Bit Transfer records found')

    # Step 6: MES Transaction Log for this batch
    print('\n[STEP 6] MES Transaction Log for this batch:')
    mtl = frappe.db.sql('''
        SELECT name, action, docstatus, creation
        FROM `tabMES Transaction Log`
        WHERE reference_doctype = 'Compound Inspection'
        AND reference_docname LIKE %s
        ORDER BY creation DESC LIMIT 10
    ''', (f'%{target_batch}%',), as_dict=1)
    if mtl:
        for r in mtl:
            docstatus_map = {0: 'DRAFT', 1: 'SUBMITTED', 2: 'CANCELLED'}
            status = docstatus_map.get(r['docstatus'], str(r['docstatus']))
            print(f'  MTL: {r["name"]} | Action: {r["action"]} | Status: {status} | {r["creation"]}')
    else:
        print('  NO MES Transaction Log records found for this batch')

else:
    print('\nNo sheeted batches found. Cannot proceed with E2E trace.')
    print('Showing recent Compound Inspection records instead:')
    recent_ci = frappe.db.sql('''
        SELECT name, batch_no, inspection_type, qty, pass_qty, docstatus, creation
        FROM `tabCompound Inspection`
        WHERE docstatus = 1
        ORDER BY creation DESC LIMIT 10
    ''', as_dict=1)
    for r in recent_ci:
        print(f'  CI: {r["name"]} | Batch: {r["batch_no"]} | Type: {r["inspection_type"]} | Qty: {r["qty"]} | Pass: {r["pass_qty"]} | {r["creation"]}')

print('\n' + '=' * 60)
print('DIAGNOSTIC COMPLETE')
print('=' * 60)