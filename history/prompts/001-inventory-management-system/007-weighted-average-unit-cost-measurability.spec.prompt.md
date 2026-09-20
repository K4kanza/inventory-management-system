---
id: 007
title: Weighted-average unit_cost measurability
stage: spec
date: 2026-09-16
surface: agent
model: opencode/big-pickle
feature: 001-inventory-management-system
branch: 001-inventory-management-system
user: architext
command: /sp.analyze
labels: ["inventory", "spec", "measurability", "weighted-average", "valuation", "gap"]
links:
  spec: specs/001-inventory-management-system/spec.md
  ticket: null
  adr: history/adr/ADR-002-concurrency-safe-movement-ledger.md
  pr: null
files:
  - specs/001-inventory-management-system/spec.md
  - specs/001-inventory-management-system/data-model.md
  - specs/001-inventory-management-system/checklists/requirements.md
tests: []
---

## Prompt

```text
# COMMAND: Apply the weighted-average valuation decision

## Context

You are working in the SPEC stage of a feature (001-inventory-management-system).
A prior `/sp.analyze` flagged two measurability gaps in the valuation rules:
CHK049 (weighted-average formula precision) and CHK022 (unit_cost measurability).

The user confirmed the decision:
- Weighted-average unit_cost **product-global (across all locations)**
- ROUND_HALF_UP to 2dp, applied **exactly once** at the point of storage
- unit_cost `numeric(12,2)` non-negative; quantity `numeric(12,3)`

## Task

1. Make the weighted-average formula and rounding rules explicit and measurable in
   spec.md (normative, independently reproducible).
2. Reconcile the unit_cost valuation-basis wording (data-model.md, plan Risks §2,
   checklist items) with the confirmed decision.
3. Add measurable success criteria / acceptance scenario coverage.
4. Do NOT change implementation code — verify it already satisfies the confirmed
   decision; report any mismatch, do not fix unnoticed.
5. Do NOT silently renumber existing requirement IDs; report ID/subject mismatches.
6. Record this exchange as a structured PHR afterward.
```

## Response snapshot

Closed the two requirement-quality gaps without touching implementation. Added to
`spec.md`: **FR-016** (product-global weighted-average formula, `(old_on_hand_total*unit_cost
+ q*c)/(old_on_hand_total + q)`), **FR-017** (ROUND_HALF_UP exactly once at storage, 2dp,
no intermediate rounding), **FR-018** (`numeric(12,2)` money / `numeric(12,3)` quantity),
**FR-019** (unit_cost validation ≥0, ≤9,999,999,999.99, ≤2dp, field-level rejection),
**FR-020** (valuation row = on_hand × unit_cost per (item, location), each quantized
ROUND_HALF_UP 2dp, report total = exact sum). Added **VL-001..VL-004** explicit & Rounding
Rules, **SC-008** (report reproducible to the penny), and two quantified acceptance
scenarios (weighted-average `10@10.00 + 10@14.00 → 12.00`; 3dp quantity accepted /
2dp unit_cost rejected per FR-019). Patched `data-model.md:96` unit_cost row from
`NEEDS CONFIRMATION` to CONFIRMED (weighted-average, ref FR-016–FR-019). Marked
CHK013/CHK045 (the on-disk valuation-subject items) `[x]` with RESOLVED notes; flagged —
did not silently rename — that the cited CHK022/CHK049 IDs map to different subjects
(SC-001 refresh / FR traceability) on disk.

## Outcome

- ✅ Impact: FR-013/FR-016 (stock valuation + weighted-average) are now independently
  reproducible and unambiguous; acceptance criteria quantified (SC-008). No
  implementation change required — `backend/apps/movements/services.py` `_revalue`
  already implements FR-016/FR-017 (ROUND_HALF_UP 2dp, product-global) — verified, not
  assumed.
- 🧪 Tests: none run (spec-stage requirement quality pass; verification was byte-level
  on-disk anchor confirms via runtime-driven reads after a garbled-shell incident).
- 📁 Files: spec.md, data-model.md, checklists/requirements.md (requirements-quality
  checklist only; no plan/tasks edits — plan Risks §2 and tasks T049 already record the
  weighted-average decision as accepted).
- 🔁 Next prompts: `/sp.plan` only if a reviewer wants the valuation derivation committed
  as an ADR; otherwise `/sp.tasks`/implementation can proceed with no plan/tasks changes.
- 🧠 Reflection: The user-cited checklist IDs (CHK049/CHK022) did not match the on-disk
  subjects (weighted-average lives in CHK013, valuation-basis reconciliation in CHK045) —
  anchored the fix on the artifact's real subjects and reported the mismatch rather than
  renumbering. Working through an unreliable bash transport forced read-tool verification
  of every edit; no file-wide rewrite was trusted until confirmed line-by-line.

## Evaluation notes (flywheel)

- Failure modes observed: bash/child-process transport returned garbled or module-load
  errors (`.`-relative `.venv` path, `& ` misrouting, 3-step edit commands jumping steps),
  so on-disk truth was re-verified via the read tool after each edit; PowerShell eval
  output was not byte-faithful.
- Next experiment to improve prompt quality: route all script creation through the read
  tool + agent-native write/Edit with a single verified venv absolute path
  (`E:\PIAIC\6-9-SDD\backend\.venv\Scripts\python.exe`), and capture a full-diff snapshot
  before committing so spec edits are auditable.
