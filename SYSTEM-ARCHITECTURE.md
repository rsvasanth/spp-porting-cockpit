# SPP Console MES — System Architecture Diagram

> This document provides a system-level view of the Console MES porting architecture.
> It covers the parallel sync backbone, the cascade chain, and the identity
> propagation paths. For per-process details, see the 12 specification folders.

---

## Parallel Sync Backbone

```mermaid
sequenceDiagram
    participant Dash
    participant Console as Console API
    participant TL as Transaction Log
    participant Legacy as Legacy ERPNext
    participant Ops as Ops ERPNext

    Dash->>Console: POST initialize_submission(payload)
    Note over Console: Creates local audit record<br/>Creates Transaction Log rows<br/>Generates reference_id (Date.now())
    Console->>Dash: acknowledgment + reference_id

    par Parallel execution
        Dash->>Console: POST execute_submission_step(reference_id, "Legacy")
        Note over Console: execute_submission_step fires
        Console->>Legacy: sync_process_transaction()
        Legacy-->>Console: callback: apply_bridge_result(intent, "Legacy", status)
    and Parallel execution
        Dash->>Console: POST execute_submission_step(reference_id, "Ops")
        Note over Console: execute_submission_step fires
        Console->>Ops: process_transaction()
        Ops-->>Console: callback: apply_bridge_result(intent, "Ops", status)
    end

    Note over Console: 5-step apply_bridge_result atomic dance<br/>Race-safe callback aggregation
    alt Both legs Synced
        Console->>Console: Auto-submit local audit record
        Note over Console: DocStatus 0 → 1
    else One leg Failed
        Console->>Dash: Partial failure — operator retry
    else Both legs Failed
        Console->>Dash: Total failure — operator review
    end
```

### Key invariants

| Invariant | How enforced |
|---|---|
| Single barcode authority | Console generates `bridge_mix_barcode`; both legs honor it |
| Idempotency | `reference_id` (13-digit Date.now()) is unique on all 3 systems |
| Audit trail | Partial payloads land via `_safe_local_create` with `flags.from_local_cache` |
| Race-safe aggregation | 5-step `apply_bridge_result` closes concurrent callback races |
| Eventually consistent | No 2PC; one leg can lag independently |

---

## Production Chain — Cascade Flow

```mermaid
flowchart LR
    subgraph Planning
        WP["Work Planning<br/>WRKP-.#####"]
        AWP["Add On Work Planning<br/>AOWP-.#####"]
    end

    subgraph Blank_Preparation
        SH["Sheeting Process<br/>SHEET-.#####"]
        BCR["Bulk Clip Release"]
        CBT["Cut Bit Transfer<br/>CBT-.#####"]
        BDE["Blanking DC Entry<br/>BLNK-.#####"]
    end

    subgraph Issue_Allocation
        BBIE["Blank Bin Inward<br/>BBIE-.#####"]
        BBI["Blank Bin Issue<br/>BBI-.#####"]
    end

    subgraph Inspection
        CI["Compound Inspection<br/>INSP-.YYYY.-.#####"]
        CD["Compound Deviation<br/>CD-.#####"]
        IE["Inspection Entry<br/>INSP-.YYYY.-.#####"]
    end

    subgraph Terminal
        MPE["Moulding Production Entry<br/>MLDPE-.#####"]
    end

    WP --> |"Job Card batch_code"| BBI
    AWP --> |"Job Card batch_code"| BBI
    WP --> |"Work Order"| MPE

    SH --> |"sheeting_clip"| BCR
    SH --> |"cutbit_qty"| CBT
    CBT --> |"Cutbit_/CB_ batch"| MPE
    BCR --> |"clip release"| BDE

    BDE --> |"Item Bin Mapping"| BBIE
    BBIE --> |"bin issue"| BBI
    BBI --> |"open BBI rows"| MPE

    CI --> |"Accepted → SE"| CD
    CI --> |"Rejected → deviation"| CD
    CD --> |"QM signoff"| CI

    IE --> |"Line + Patrol prerequisite"| MPE
    MPE --> |"batch cascade"| IE
    MPE --> |"Inspection rejection SE"| IE
```

### Cascade chain table

| From | To | What cascades | Mechanism |
|---|---|---|---|
| Work Planning | Job Card | `batch_code` = Lot # | Legacy WO/JC creation |
| BBI | MPE | Open bin rows | `is_completed = 0` gate in MPE `validate_lot_number` |
| MPE | Inspection Entry | Produced `batch_no` | `submit_inspection_stock_entries_from_moulding` |
| Inspection Entry | MPE | Line + Patrol prerequisite | MPE blocks without both submitted |
| Sheeting | BCR | Clip release state | `Item Clip Mapping.is_released` |
| Sheeting | CBT | Cutbit batch | `Cutbit_` / `CB_` naming convention |

---

## Clip/Bin Mapping Identity Propagation

```mermaid
flowchart TD
    SH_S["Sheeting Process<br/>Clip row"]
    SH_CB["Sheeting Process<br/>Cut-bit row"]

    BCR["Bulk Clip Release<br/>Clip Mapping"]
    CBT["Cut Bit Transfer<br/>Bin Mapping"]

    BDE["Blanking DC Entry<br/>Item Bin Mapping"]
    BBIE["Blank Bin Inward Entry<br/>Asset Movement"]
    BBI["Blank Bin Issue<br/>Blank Bin Issue Item"]
    IBM["Item Bin Mapping"]

    MPE["Moulding Production Entry<br/>Consumed Batches"]

    SH_S --> |"inline write BCR-1"| BCR
    BCR --> |"retires clip mapping"| BDE
    SH_CB --> |"CBT bin source"| CBT
    CBT --> |"retire/reduce bin"| BDE

    BDE --> |"creates bin|asset"| BBIE
    BBIE --> |"normal inward"| BBI
    BBIE --> |"repack to cutbit"| CBT
    BBI --> |"open BBI rows"| MPE

    IBM --> |"consumed"| MPE
    MPE --> |"retire/update IBM"| IBM
```

### Mapping identity conventions

| Pattern | Prefix | Used by | Purpose |
|---|---|---|---|
| Clip mapping | `sheeting_clip` | Sheeting, BCR, BDE | Track which clip is in which bin |
| Cutbit batch | `Cutbit_` | CBT, MPE | Repurposed material batch identity |
| Mix barcode | `CB_` | CBT, MPE | Cutbit mix for Final Batch Mixing |
| Bin mapping | `Item Bin Mapping` | BDE, BBIE, BBI, MPE | Physical bin content identity |

---

## Architecture Risk Map

```mermaid
flowchart LR
    subgraph Critical_Risk
        C1["IE/MPE Cascade Overlap<br/>Two functions, overlapping scope"]
        C2["cavity_no wiring<br/>TODO since Compound Deviation"]
    end

    subgraph High_Risk
        H1["BDE Ops ≠ Legacy semantics<br/>Asset Movement vs Stock Entry"]
        H2["Batch identity drift<br/>spp_batch_no vs spp_batch_number"]
        H3["BCR wiring incomplete<br/>Callback routing gap"]
    end

    subgraph Medium_Risk
        M1["BBI not ported<br/>68k records on Legacy only"]
        M2["Network awareness missing<br/>NFR-MIX-052 not implemented"]
        M3["Bridge uptime not monitored<br/>NFR-MIX-011 gap"]
    end

    subgraph Low_Risk
        L1["Mass-balance soft signal only<br/>FR-MIX-031 deferred"]
        L2["Production-staging isolation<br/>Operational discipline only"]
    end
```

### Risk severity guide

| Severity | Meaning |
|---|---|
| **Critical** | Blocks refactor of cascade chain or identity propagation |
| **High** | Data quality or sync correctness at risk; needs code/test fix |
| **Medium** | Operational gap; needs monitoring or ops procedure |
| **Low** | Known deferred decision; revisit in cleanup wave |

---

## Document index

| File | What it covers |
|---|---|
| `ARCHITECTURE-DECISIONS.md` | 5 load-bearing ADRs |
| `SYSTEM-ARCHITECTURE.md` | This file — system-level diagrams |
| `01-requirements/*/08-traceability.md` | Per-motion requirements traceability |
| `02-specifications/*/10-risks-and-decisions.md` | Per-motion spec risks |
| `CONTINUATION-PROMPT.md` | Spec writing methodology |
| `CONTINUATION-PROMPT-REQUIREMENTS.md` | Requirements writing methodology |
