# Actors and Roles

## Primary Actor

| Actor | Responsibility |
| --- | --- |
| Sheeting Operator | Scans approved compound, enters output rows, submits Sheeting Process |

## Secondary Actors

| Actor | Need from Sheeting |
| --- | --- |
| Blanker | Clip identities must resolve when release or blanking scans happen |
| Mixing Operator | Cut-bit outputs must preserve the recycling identity convention |
| Shop Floor Supervisor | Needs traceability from compound input to output rows |
| Production Overseer | Reviews requirement/spec/code alignment |

## System Actors

| System | Responsibility |
| --- | --- |
| Console Dash | Scanner-driven input, output row entry, soft mass-balance feedback |
| Console Backend | Local audit record and inline clip mapping creation |
| Legacy Bridge | Maps Sheeting payload into `Material Transfer` |
| Legacy ERPNext | Validates and submits `Material Transfer` |
| Ops ERPNext | Creates the Ops stock movement |

## Decision Rights

| Decision | Owner |
| --- | --- |
| Output split between clip and cut-bit rows | Sheeting Operator |
| Whether a source compound is eligible | QA result from upstream inspection/deviation |
| Prefix/barcode convention changes | Production Overseer only |
| Inline clip mapping behavior | Load-bearing; must not be removed during refactor |
