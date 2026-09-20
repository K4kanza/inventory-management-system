---
id: 008
title: Remediate spec plan task inconsistencies
stage: spec
date: 2026-09-16
surface: agent
model: opencode/big-pickle
feature: 001-inventory-management-system
branch: 001-inventory-management-system
user: architext
command: /sp.analyze
labels: ["inventory", "spec", "plan", "tasks", "consistency", "remediation", "analysis"]
links:
  spec: specs/001-inventory-management-system/spec.md
  ticket: null
  adr: history/adr/ADR-002-concurrency-safe-movement-ledger.md
  pr: null
files:
  - specs/001-inventory-management-system/spec.md
  - specs/001-inventory-management-system/plan.md
  - specs/001-inventory-management-system/tasks.md
tests: []
---

## Prompt

```text
# COMMAND: Analyze and remediate core artifact consistency

Run /sp.analyze on spec.md, plan.md, tasks.md (read-only analysis, then apply
approved remediation):

1. Detect inconsistencies, duplications, ambiguities, underspecified items
   across the three core artifacts. Constitution (.specify/memory/constitution.md)
   is non-negotiable; conflicts are CRITICAL.
2. Report findings with stable IDs, severity (CRITICAL/HIGH/MEDIUM/LOW), and a
   coverage summary + metrics. Never modify files during analysis.
3. On user approval, apply remediation edits (this exchange -> V1 + D1/D2 only;
   skip C1 and the CHK022/CHK049 re-anchor).
4. Re-read edited files and verify changes are on disk.
5. Re-run /sp.analyze to confirm HIGH findings cleared.
6. Create a PHR (stage: spec) for the exchange.
7. Do not commit anything.
```

## Response snapshot

Ran the analysis; surfaced four findings. Applied the two approved HIGH
remediations: **V1** (plan.md:177 + plan.md:218 + tasks.md:276 — valuation basis
now recorded as CONFIRMED 2026-09-16 instead of "needs user confirmation" /
"ambiguity", matching spec FR-016..FR-020 and data-model.md:96) and **D1+D2**
(spec.md US4 acceptance scenarios — removed one duplicated weighted-average/3dp
scenario pair and renumbered the block 5,6,5,6 -> 5,6,7,8). Left C1 (constitution
ratification) and C2 (missing PHR tooling) flagged-but-open as governance items.
No code, business rules, scope, or ADR changes.

## Outcome

- ✅ Impact: Cross-artifact contradiction cleared — plan/tasks now agree with
  spec/data-model/checklist on the weighted-average unit_cost (ROUND_HALF_UP 2dp
  once, product-global). US4 acceptance scenarios are unique and sequentially
  numbered, restoring traceability. Post-remediation /sp.analyze shows Ambiguity 0,
  Duplication 0, FR coverage 100%.
- 🧪 Tests: none run (requirements-analysis + doc remediation stage; verification
  was direct read-tool + grep reads of each edited region on disk).
- 📁 Files: spec.md, plan.md, tasks.md (each edit verified by re-reading the exact
  line range after the edit).
- 🔁 Next prompts: ratify the constitution (C1) before implementation; optionally
  address C2 (add create-phr tooling) and the low-effort traceability improvement
  (openapi.yaml unit_cost/valuation descriptions + CHK022/CHK049 re-anchor).
- 🧠 Reflection: The /sp.analyze remediation loop (diagnose -> propose -> approve
  -> apply -> re-verify -> re-analyze) is the flywheel that keeps spec/plan/tasks
  from drifting. Duplication surfaced because an earlier valuation-rule edit had
  appended scenarios without renumbering — a good argument for running /sp.analyze
  after any spec edit that adds numbered items.

## Evaluation notes (flywheel)

- Failure modes observed: the paired plan.md/tasks.md reads came back labelled
  oddly in transport, so before editing I re-read each target region and relied on
  the read tool + grep for byte-accurate oldString matching instead of trusting a
  single read. Em-dash and § glyphs must be copied exactly from the read output,
  not reconstructed.
- Next experiment to improve prompt quality: keep the analyze/approve/apply/verify
  loop but add an explicit "rename numbering" check to the analysis checklist so a
  future spec edit that inserts numbered scenarios triggers renumber verification.