# Actors and Roles

| Actor | Responsibility |
| --- | --- |
| Blanker / material handler | Scans source assets and submits transfer quantities |
| Mixing Operator | Later consumes cut-bit stock in Final Batch Mixing |
| Shop Floor Supervisor | Reviews recycling and bin consumption |
| Production Overseer | Approves changes to identity and warehouse rules |

## System Actors

| System | Responsibility |
| --- | --- |
| Console Dash | Scan validation, duplicate prevention, quantity entry |
| Console Backend | Local create, native batch relay, bin mapping reduction |
| Legacy Bridge | Maps payload to Legacy `Cut Bit Transfer` and resolves warehouse routing |
| Legacy ERPNext | Creates repack `Stock Entry` and updates bin mappings |
| Ops ERPNext | Dedicated `submit_cut_bit_transfer` handler |

## Decision Rights

| Decision | Owner |
| --- | --- |
| Transfer qty from a source asset | Operator, within available qty |
| Source warehouse routing rule | Production Overseer and Engineering Lead |
| Whether clip mappings retire during CBT | Production Overseer; current rule says no |
| Batch/mix barcode convention changes | Forbidden unless full downstream redesign is approved |
