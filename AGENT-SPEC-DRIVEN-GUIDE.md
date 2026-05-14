# Agent Guide: Spec-Driven Development Approach

## 1. The Core Philosophy
For the Shree Polymer Porting project, **the Specification is the source of truth, but the Legacy Code is the ground truth.** 

An agent should never implement a feature based *only* on the Markdown spec. You must cross-reference the spec with the Legacy logic to identify "Implicit Requirements."

## 2. The Spec-Driven Workflow for Agents

### Step 1: Spec Review
- Read the `.md` files in `02-specifications`.
- Identify the **Target Process Code** and the **Sync Targets** (Legacy, Ops, or Both).

### Step 2: Semantic Validation (The "Legacy Deep-Dive")
- **CRITICAL**: Before writing sync code, go to the Legacy Bridge or Custom App and find the `.py` file for that process.
- Search for `validate()` and `before_insert()` methods.
- **Identify mandatory fields that aren't in the spec**. (e.g., in Work Planning, `scan_supervisor` was required by Legacy but missing in the initial Console payload).

### Step 3: Local-First Implementation
- Always implement the local save first in `api.py`.
- **Orchestration**: Immediately after `doc.insert()`, call an orchestration function.
- **Transaction Logs**: The orchestration function *must* create `Console Transaction Log` entries. This is non-negotiable for system resilience.

### Step 4: Payload Translation
- Different targets speak different "dialects."
- **Ops**: Usually takes a clean JSON representation of the DocType.
- **Legacy**: Often requires mapping IDs (like `Shift A`) to Legacy strings (like `8 Hours - 1`).
- Never send the same raw payload to both systems unless explicitly verified.

### Step 5: Automated E2E Testing
- Do not rely only on browser tests.
- Create a `test_{process}_sync.py` file.
- The test must verify that `Success` is received from **both** remote sites.

## 3. How to Review Existing Specs
When reviewing an existing process:
1.  Check the `03-alignment-reports` for that process.
2.  If no report exists, run the `e2e_trace.py` or similar utility to see where synchronization is breaking.
3.  Compare the current `api.py` orchestration logic against the `Required Orchestration` section in the spec.

---

## 4. The long-form methodology

For the complete spec-driven methodology — the 8 phases, quality gates per phase, anti-patterns, and reference examples — see [`SPEC-DRIVEN-METHODOLOGY.md`](SPEC-DRIVEN-METHODOLOGY.md).

This guide is the 1-page summary. The methodology document is the long-form playbook.

---
*This guide was established after the successful stabilization of the Work Planning module.*
