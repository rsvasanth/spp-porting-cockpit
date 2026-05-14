-- ============================================================
-- SPP E2E Chain Trace: Compound Inspection → Final Batch → Sheeting → Cut Bit Transfer
-- Target site: spp15.local (Legacy ERPNext v15)
-- Purpose: Find a real compound lot and trace it through the full chain
-- ============================================================

-- STEP 1: Find recent Compound Inspections that were Accepted
-- This is the QA gate between MB Mixing and FB Mixing
SELECT 
    ci.name AS ci_name,
    ci.docstatus,
    ci.inspection_type,
    ci.lot_no AS source_lot,
    ci.status,
    ci.inspected_qty_nos,
    ci.inspected_qty_kgs,
    ci.total_rejected_qty,
    ci.posting_date,
    ci.creation
FROM `tabCompound Inspection` ci
WHERE ci.docstatus = 1 
  AND ci.status = 'Accepted'
  AND ci.inspection_type = 'Compound Inspection'
ORDER BY ci.creation DESC
LIMIT 10;

-- STEP 2: Find Final Batch Mixing records that consumed the CI lot
-- FB Mixing takes MB lot + raw materials → Compound output
-- Look for DCRs with inward_material_type = 'Compound' that reference the same lot
-- The FB output becomes the input to Sheeting
SELECT 
    fb.name AS fb_name,
    fb.docstatus,
    fb.inward_material_type,
    fb.scan_lot_number AS fb_lot,
    fb.scan_mix_barcode,
    fb.bridge_mix_barcode,
    fb.total_rm_qty,
    fb.total_output_qty,
    fb.mix_ratio,
    fb.posting_date,
    fb.creation
FROM `tabDelivery Challan Receipt` fb
WHERE fb.inward_material_type = 'Compound'
  AND fb.docstatus = 1
ORDER BY fb.creation DESC
LIMIT 10;

-- STEP 3: Find Sheeting records that consumed the FB output
-- Sheeting Material Transfer has both clip rows and cutbit rows
-- Find recent Material Transfers with sheeting_clip child rows and cutbit output
SELECT 
    sh.name AS sheeting_name,
    sh.docstatus,
    sh.posting_date,
    sh.creation,
    sh.total_clips,
    sh.total_cutbit_qty,
    sh.scan_mix_barcode AS source_barcode
FROM `tabMaterial Transfer` sh
WHERE sh.docstatus = 1
  AND sh.total_clips > 0
  AND sh.total_cutbit_qty > 0
ORDER BY sh.creation DESC
LIMIT 10;

-- STEP 4: Find Cut Bit Transfer records that consumed sheeting cutbit output
-- CBT repacks cutbit into Cutbit_<item> batch + CB_<item> mix barcode
-- Look for recent CBT records
SELECT 
    cbt.name AS cbt_name,
    cbt.docstatus,
    cbt.posting_date,
    cbt.scan_clip__bin,
    cbt.total_qty,
    cbt.target_batch,
    cbt.mix_barcode,
    cbt.creation
FROM `tabCut Bit Transfer` cbt
WHERE cbt.docstatus = 1
ORDER BY cbt.creation DESC
LIMIT 10;

-- STEP 5: Cross-reference — find the CI→FB→Sheeting→CBT chain for a specific compound
-- This query chains them via barcode/linkage fields
-- Use this once you have candidate lots from steps 1-4
SELECT 
    'Compound Inspection' AS stage,
    ci.name AS record_name,
    ci.lot_no AS linking_lot,
    ci.status,
    ci.creation
FROM `tabCompound Inspection` ci
WHERE ci.docstatus = 1 AND ci.status = 'Accepted'
UNION ALL
SELECT 
    'Final Batch Mixing' AS stage,
    fb.name AS record_name,
    fb.scan_lot_number AS linking_lot,
    'Submitted' AS status,
    fb.creation
FROM `tabDelivery Challan Receipt` fb
WHERE fb.docstatus = 1 AND fb.inward_material_type = 'Compound'
UNION ALL
SELECT 
    'Sheeting' AS stage,
    sh.name AS record_name,
    sh.scan_mix_barcode AS linking_lot,
    'Submitted' AS status,
    sh.creation
FROM `tabMaterial Transfer` sh
WHERE sh.docstatus = 1
UNION ALL
SELECT 
    'Cut Bit Transfer' AS stage,
    cbt.name AS record_name,
    cbt.scan_clip__bin AS linking_lot,
    'Submitted' AS status,
    cbt.creation
FROM `tabCut Bit Transfer` cbt
WHERE cbt.docstatus = 1
ORDER BY creation DESC
LIMIT 50;

-- STEP 6: Item Clip Mapping state after Sheeting + BCR
-- Trace clip lifecycle: Sheeting creates mapping → BCR releases it
-- Find clips that were created during sheeting and released during BCR
SELECT 
    icm.name AS mapping_name,
    icm.sheeting_clip,
    icm.barcode,
    icm.item_code,
    icm.qty AS mapping_qty,
    icm.is_released,
    icm.creation
FROM `tabItem Clip Mapping` icm
WHERE icm.creation >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY icm.creation DESC
LIMIT 20;

-- STEP 7: Item Bin Mapping for cutbit bins used in CBT
-- This shows the bin state that CBT reads and retires
SELECT 
    ibm.name AS bin_mapping_name,
    ibm.bin,
    ibm.batch_no,
    ibm.item_code,
    ibm.qty,
    ibm.is_retired,
    ibm.creation
FROM `tabItem Bin Mapping` ibm
WHERE ibm.creation >= DATE_SUB(NOW(), INTERVAL 7 DAY)
  AND ibm.item_code LIKE 'Cutbit%'
ORDER BY ibm.creation DESC
LIMIT 20;

-- STEP 8: Summary counts for the E2E chain
SELECT 
    'Compound Inspections (Accepted)' AS metric,
    COUNT(*) AS count
FROM `tabCompound Inspection` ci
WHERE ci.docstatus = 1 AND ci.status = 'Accepted'
    AND ci.creation >= DATE_SUB(NOW(), INTERVAL 30 DAY)
UNION ALL
SELECT 
    'Final Batch Mixing Records' AS metric,
    COUNT(*) AS count
FROM `tabDelivery Challan Receipt` fb
WHERE fb.docstatus = 1 AND fb.inward_material_type = 'Compound'
    AND fb.creation >= DATE_SUB(NOW(), INTERVAL 30 DAY)
UNION ALL
SELECT 
    'Sheeting Records (with clips+cutbits)' AS metric,
    COUNT(*) AS count
FROM `tabMaterial Transfer` sh
WHERE sh.docstatus = 1
    AND sh.total_clips > 0 AND sh.total_cutbit_qty > 0
    AND sh.creation >= DATE_SUB(NOW(), INTERVAL 30 DAY)
UNION ALL
SELECT 
    'Cut Bit Transfer Records' AS metric,
    COUNT(*) AS count
FROM `tabCut Bit Transfer` cbt
WHERE cbt.docstatus = 1
    AND cbt.creation >= DATE_SUB(NOW(), INTERVAL 30 DAY);