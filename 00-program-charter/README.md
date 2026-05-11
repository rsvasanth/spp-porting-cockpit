# SPP Porting Program — Charter

**This is the day-one document for anyone joining the SPP Console porting program.** It captures the program's vision, architectural principles, and success criteria — not how individual processes work (that's `02-specifications/`) or what each business motion needs (that's `01-requirements/`).

If you read only one file in this cockpit, read [01-vision-and-goals.md](01-vision-and-goals.md) first.

## The program in one paragraph

Shree Polymer Industries is migrating its shop-floor MES (Manufacturing Execution System) from a single-ERP-on-legacy-Desk-only setup to a **Console-primary, parallel-ERP architecture**. Console (a custom Frappe app with a React Dash UI) becomes the system of record. Submissions fan out via a sync Bridge to two ERPs in parallel: the existing legacy ERPNext v15 install (preserved as-is for historical continuity) and a new Ops ERPNext v15 install (built clean, using only **native ERPNext doctypes** — Stock Entry, Work Order, Job Card, Batch — with no custom per-process doctypes). The migration covers the **entire manufacturing chain** from Master Batch Mixing through Moulding Production Entry. Eventual consistency between the two ERPs is an accepted trade-off; reliability and shop-floor speed take precedence over transactional rollback.

## The three pillars

| Pillar | What it means | Why it matters |
|---|---|---|
| **Console as system of record** | Identity (reference_id, mix_barcode, Lot #), audit trail, and operator workflow live on Console. Both ERPs are downstream consumers. | Decouples shop-floor velocity from ERP-side complexity; survives any single-ERP outage |
| **Native ERPNext on Ops** | Ops uses only standard ERPNext doctypes (Stock Entry, Work Order, Job Card, Batch). No custom per-process doctypes. Generic `TransactionEngine` reads sequence templates. | Aligns with ERPNext community patterns; simplifies upgrades; preserves the future option of running on Ops alone |
| **End-to-end manufacturing scope** | All ~13 stages from MB Mixing through MPE in scope. Not a partial rollout. | Half-ported flows don't deliver value; the chain must work end-to-end before any stage's port is "done" |

The full implications of each pillar are documented in [03-architectural-principles.md](03-architectural-principles.md).

## Files in this charter

| File | What it answers | Audience |
|---|---|---|
| [01-vision-and-goals.md](01-vision-and-goals.md) | Why are we porting at all? What's the strategic intent? | Anyone joining the program |
| [02-current-vs-target-state.md](02-current-vs-target-state.md) | How does SPP run today vs after the port? Side-by-side per stage. | Engineers, ops staff, stakeholders comparing before/after |
| [03-architectural-principles.md](03-architectural-principles.md) | The three pillars expanded with trade-offs and what they rule in/out | Engineers making implementation decisions; reviewers questioning changes |
| [04-manufacturing-workflow.md](04-manufacturing-workflow.md) | The 13-stage chain at program level — legacy doctype → Console doctype → Ops native doctype mapping | Everyone — this is the program's "table of contents" for the manufacturing scope |
| [05-system-of-record-decisions.md](05-system-of-record-decisions.md) | Who owns what truth at each moment? When does legacy go read-only? | Architects, data owners, future migration leads |
| [06-cutover-and-success-criteria.md](06-cutover-and-success-criteria.md) | How do we declare the porting program "done"? What's NOT in this program's scope? | Production overseer, program sponsor |

## How this charter relates to the rest of the cockpit

```
00-program-charter/          ← Level 0: program vision (this folder)
   │
   ▼ informs
   │
01-requirements/             ← Level 1: business intent per motion
   ├── mixing-process/         (MB + FB)
   ├── inspection-process/     (CI + Compound Deviation)
   ├── sheeting-and-cutting/   (Sheeting + Cut Bit + BCR)
   ├── blanking/               (Blanking DC + Bin Inward + Bin Issue)
   ├── production-planning/    (Add On Work Planning)
   └── moulding/               (MPE + Inspection Entry)
   │
   ▼ implements
   │
02-specifications/           ← Level 2: technical reality per Console process
   └── (one folder per Console process)
```

When a contradiction is found between layers:
- **Charter > Requirements > Specifications** in authority
- A spec describing behaviour that contradicts the charter is a bug in the code, not in the charter
- A requirement contradicting the charter is a misframed requirement that should be revised

## Drift watch for this charter

This charter is **the most stable layer**. It should not change frequently. When it does change:
- Each change gets a dated entry in [06-cutover-and-success-criteria.md §Change log](06-cutover-and-success-criteria.md)
- The triggering decision (production overseer's call, stakeholder workshop output, retrospective insight) is named
- Affected motion-level requirements and process specs get follow-up flags

Casual rewording is not acceptable — the charter codifies decisions that took the team time to reach.
