---
id: 003
title: Inventory system architecture ADRs
stage: misc
date: 2026-09-15
surface: agent
model: opencode/big-pickle
feature: 001-inventory-management-system
branch: 001-inventory-management-system
user: architext
command: /sp.adr
labels: ["inventory", "adr", "architecture", "decisions", "django"]
links:
  spec: specs/001-inventory-management-system/spec.md
  ticket: null
  adr: history/adr/ADR-001-backend-stack-architecture.md
  pr: null
files:
 - history/adr/ADR-001-backend-stack-architecture.md
 - history/adr/ADR-002-concurrency-safe-movement-ledger.md
 - history/adr/ADR-003-role-based-access-control.md
tests:
 - none (documentation stage; no tests run)
---

## Prompt

```text
# COMMAND: Analyze planning artifacts and document architecturally significant decisions as ADRs

## CONTEXT

The user has completed feature planning and needs to:

- Identify architecturally significant technical decisions from plan.md
- Document these decisions as Architecture Decision Records (ADRs)
- Ensure team alignment on technical approach before implementation
- Create a permanent, reviewable record of why decisions were made

Architecture Decision Records capture decisions that:

- Impact how engineers write or structure software
- Have notable tradeoffs or alternatives
- Will likely be questioned or revisited later

**User's additional input:**

Django-PostgreSQL monolith with row-locking stock movements
```

## Response snapshot

Analyzed the planning artifacts (`plan.md`, `research.md`, `data-model.md`, `contracts/`) and documented the architecturally significant decisions as three clustered ADRs in `history/adr/` (started with the user's "Django-PostgreSQL monolith with row-locking stock movements" suggestion):

- **ADR-001 — Backend Stack & Application Architecture**: Python 3.12 + Django 5.2 LTS + DRF 3.17 + drf-spectacular + psycopg 3 + PostgreSQL 16 (`pg_trgm`); monolith in `backend/` with server-rendered Bootstrap 5 pages + JSON API at `/api/v1`; no separate frontend project; Django migrations as schema source of truth. Alternatives: MERN, FastAPI+React, Laravel+MySQL.
- **ADR-002 — Concurrency-Safe Stock Movement Ledger**: single transaction per movement with `SELECT ... FOR UPDATE` on `StockLevel(product, location)`, append-only immutable `StockMovement` rows, manager-consented audited over-issue, derived (never stored) alert flags. Alternatives: optimistic locking, recompute-from-ledger, triggers.
- **ADR-003 — Role-Based Access Control Model**: custom `User` with single `role` field (admin/manager/staff), shared capability map enforced by page decorators + DRF permission classes under default-deny; deactivation not deletion. Alternatives: Django Groups/Permissions, separate Role table + M2M.

Status set to **Proposed** on all three (awaiting team review before implementation). No conflicts: `history/adr/` had no existing ADRs. Script gap: no `create-adr.sh`/`create-adr.ps1` exists in this repo, so ADRs were produced agent-natively from `.specify/templates/adr-template.md` with allocated IDs (reported in the completion summary).

## Outcome

- ✅ Impact: Permanent, reviewable ADR record locking in the three decisions that shape how engineers write code (stack/architecture, ledger concurrency, RBAC) — each clustered, with alternatives, pros/cons, and references back to the planning docs.
- 🧪 Tests: None run (documentation stage).
- 📁 Files: `history/adr/ADR-001-backend-stack-architecture.md`, `history/adr/ADR-002-concurrency-safe-movement-ledger.md`, `history/adr/ADR-003-role-based-access-control.md`.
- 🔁 Next prompts: `/sp.tasks` to produce the test-first task list; team review/ratification of the three ADRs (Proposed → Accepted) and of the still-unratified constitution before implementation.
- 🧠 Reflection: The `/sp.adr` workflow presumes a `create-adr.sh` that does not exist in this Windows repo (only `scripts/powershell`). Documented the gap and used the agent-native template fallback rather than skipping all ADRs per the strict skip rule — matches the PHR fallback precedent. The user's single named decision was correctly split into two clusters (stack/arch and ledger concurrency) plus RBAC from the plan, respecting the "cluster, don't over-granularize" rule.

## Evaluation notes (flywheel)

- Failure modes observed: no conflict — `history/adr/` was empty. Tooling gap: `create-adr.sh` absent (entire `scripts/bash` missing from this repo).
- Graders run and results (PASS/FAIL): significance checklist PASS for all three clusters (impact + alternatives + cross-cutting scope); template placeholder audit PASS (all {{*}} resolved).
- Prompt variant (if applicable): null.
- Next experiment (smallest change to try): add a `create-adr.ps1` to `.specify/scripts/powershell/` (mirroring `create-phr.sh` semantics and the `adr-template.md`) so future `/sp.adr` runs use the canonical script path.