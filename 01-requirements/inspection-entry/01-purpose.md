# 01 — Purpose

Inspection Entry records quality inspection outcomes for production lots and related stock flows. It captures inspected quantity, defect types, rejected quantity, rejected weight, inspector identity, and the stock movement needed to isolate rejected material.

## Process position

```text
Lot / Batch / Incoming / Final Visual context
  -> Inspection Entry
  -> Rejection Stock Entry or deferred stock action
  -> MPE batch cascade or downstream receipt/visual flow
```

## Inspection types in live legacy

| Type | Live total | Submitted | Main purpose |
|---|---:|---:|---|
| Lot Inspection | 29,615 | 28,474 | Lot-level moulding quality inspection. |
| Line Inspection | 29,487 | 29,201 | Line-side moulding inspection; MPE prerequisite. |
| Incoming Inspection | 27,891 | 27,718 | Incoming/deflashing-related inspection flow. |
| Final Visual Inspection | 27,378 | 25,597 | Final visual/PDIR-style rejection or FG flow. |
| Patrol Inspection | 9,820 | 9,667 | Patrol sampling; MPE prerequisite. |
| Visual Inspection | 6 | 6 | Historical/small-volume type. |

## Why this is a separate requirement identity

The old grouped moulding pack treated Inspection Entry mainly as three MPE-adjacent variants. Legacy and site data show a wider unified DocType. For refactor analysis, Inspection Entry needs its own folder so the business can compare the current polymorphic legacy flow against Console implementation and decide whether Console should mirror all types or intentionally scope a subset.

