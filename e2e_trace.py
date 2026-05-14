#!/usr/bin/env python3
"""E2E chain trace queries for spp15.local"""
import frappe

def run_queries():
    print("=== E2E Chain Trace: spp15.local ===\n")
    
    # 1. Check CI schema
    print("--- Compound Inspection columns ---")
    ci_fields = frappe.db.sql("DESCRIBE `tabCompound Inspection`", as_dict=True)
    for f in ci_fields:
        print(f['Field'], '|', f['Type'])
    print()
    
    # 2. Count records in each table (7 day window)
    print("--- Record counts (7 day window) ---")
    
    ci_count = frappe.db.sql("""
        SELECT COUNT(*) as cnt FROM `tabCompound Inspection` 
        WHERE docstatus = 1 AND creation >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    """)
    print(f"Compound Inspections (all statuses): {ci_count[0][0]}")
    
    # 3. Recent Material Transfers with clips + cutbits
    print("\n--- Sheeting (Material Transfer with clips + cutbits) ---")
    sheeting = frappe.db.sql("""
        SELECT name, docstatus, posting_date, total_clips, total_cutbit_qty,
               scan_mix_barcode, creation
        FROM `tabMaterial Transfer`
        WHERE docstatus = 1 
          AND total_clips > 0 
          AND total_cutbit_qty > 0
          AND creation >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        ORDER BY creation DESC
        LIMIT 5
    """, as_dict=True)
    for s in sheeting:
        print(f"  {s['name']} | {s['posting_date']} | clips:{s['total_clips']} cutbit:{s['total_cutbit_qty']} | {s['creation']}")
    
    # 4. Recent Cut Bit Transfer records
    print("\n--- Cut Bit Transfer ---")
    cbt = frappe.db.sql("""
        SELECT name, docstatus, posting_date, scan_clip__bin, 
               total_qty, target_batch, mix_barcode, creation
        FROM `tabCut Bit Transfer`
        WHERE docstatus = 1
          AND creation >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        ORDER BY creation DESC
        LIMIT 5
    """, as_dict=True)
    for c in cbt:
        print(f"  {c['name']} | {c['posting_date']} | qty:{c['total_qty']} | target:{c['target_batch']} | mix:{c['mix_barcode']}")
    
    # 5. Item Clip Mapping
    print("\n--- Item Clip Mapping (recent) ---")
    icm = frappe.db.sql("""
        SELECT name, sheeting_clip, barcode, item_code, qty, 
               is_released, creation
        FROM `tabItem Clip Mapping`
        WHERE creation >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        ORDER BY creation DESC
        LIMIT 5
    """, as_dict=True)
    for i in icm:
        print(f"  {i['name']} | clip:{i['sheeting_clip']} | barcode:{i['barcode']} | released:{i['is_released']}")
    
    # 6. Item Bin Mapping for cutbit items
    print("\n--- Item Bin Mapping (Cutbit items) ---")
    ibm = frappe.db.sql("""
        SELECT name, bin, batch_no, item_code, qty, 
               is_retired, creation
        FROM `tabItem Bin Mapping`
        WHERE item_code LIKE 'Cutbit%%'
          AND creation >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        ORDER BY creation DESC
        LIMIT 5
    """, as_dict=True)
    for b in ibm:
        print(f"  {b['name']} | bin:{b['bin']} | batch:{b['batch_no']} | item:{b['item_code']} | retired:{b['is_retired']}")

if __name__ == "__main__":
    run_queries()