# Business Rules

| ID | Rule | Rationale |
| --- | --- | --- |
| BR-SHT-001 | Sheeting may start only from approved compound. | QA release is the gate into production routing. |
| BR-SHT-002 | One Sheeting submission may produce many output rows. | Physical sheeting naturally creates multiple pieces. |
| BR-SHT-003 | Clip and cut-bit outputs are different identities even if produced together. | They have different downstream paths. |
| BR-SHT-004 | `is_cut_bit_item` distinguishes recycling output from clip output. | Legacy and Bridge logic use the flag. |
| BR-SHT-005 | `Cutbit_` prefix must be preserved for cut-bit output identity. | Final Batch Mixing recycling depends on this convention. |
| BR-SHT-006 | Clip mappings must be written inline on Console. | Downstream scans can happen before sync callback returns. |
| BR-SHT-007 | Legacy Sheeting transfer must include `sheeting_clip` rows. | Legacy rejects sheeting transfer without clips. |
| BR-SHT-008 | Child quantities must be positive. | Legacy validation enforces it. |
| BR-SHT-009 | Mass-balance is a warning in Sheeting, not a hard block. | Variance should be visible without forcing false entries. |
| BR-SHT-010 | `reference_id` must be stable across retry. | Cross-system identity must not fork. |
| BR-SHT-011 | Sheeting must not retire clip mappings. | Release and consumption are separate process decisions. |
| BR-SHT-012 | Requirements shall not merge Sheeting with Cut Bit Transfer or Bulk Clip Release. | The user reviews implementation process-by-process. |

## Future Consideration

Automated yield analytics can be added later, but it must not change the submission rules above.
