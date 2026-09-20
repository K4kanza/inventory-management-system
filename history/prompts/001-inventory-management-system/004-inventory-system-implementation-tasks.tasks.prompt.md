---
id: 004
title: Inventory system implementation tasks
stage: tasks
date: 2026-09-15
surface: agent
model: opencode/big-pickle
feature: 001-inventory-management-system
branch: 001-inventory-management-system
user: architext
command: /sp.tasks
labels: ["inventory", "tasks", "implementation", "checklist"]
links:
  spec: specs/001-inventory-management-system/spec.md
  ticket: null
  adr: history/adr/ADR-001-backend-stack-architecture.md
  pr: null
files:
 - specs/001-inventory-management-system/tasks.md
tests:
 - none (task-generation stage; tasks.md format-validated — 62 tasks, IDs sequential, 0 format violations)
---

## Prompt

```text
/sp.tasks

# COMMAND OUTLINE (user input was empty)

1. Setup: check-prerequisites.ps1 -Json → FEATURE_DIR + AVAILABLE_DOCS
2. Load design documents: plan.md, spec.md (required); data-model.md, contracts/, research.md, quickstart.md (optional)
3. Execute task generation workflow:
   - Extract tech stack/libraries/structure from plan.md
   - Extract user stories with priorities (P1-P4) from spec.md
   - Map data-model entities and contract endpoints to user stories
   - Generate tasks organized by user story; dependency graph; parallel examples; validation
4. Generate tasks.md from .specify/templates/tasks-template.md:
   - Phase 1 Setup, Phase 2 Foundational, Phase 3+ one phase per story (priority order), final Polish phase
   - Strict checklist format: "- [ ] T00X [P?] [US?] Description with file path"
   - Dependencies section, parallel execution examples, implementation strategy (MVP first)
5. Report: tasks.md path, total counts, per-story counts, parallel opportunities, independent test criteria, MVP scope
6. Create PHR
```

## Response snapshot

Generated `specs/001-inventory-management-system/tasks.md` (62 tasks, T001–T062) organized as:

- **Phase 1 Setup (6)**: backend/ skeleton, pyproject.toml (Django 5.2 LTS/DRF 3.17/drf-spectacular/psycopg3), ruff+pytest config, settings split (base/dev/prod), .env.example, manage.py/urls/wsgi/asgi.
- **Phase 2 Foundational (8)**: custom `User` with `role` BEFORE any migration (ADR-003), capability map + default-deny permission helpers, DRF/dr-spectacular wiring, auth pages, logging/exception handler, pg_trgm extension migration, pytest role-aware fixtures.
- **Phase 3 US1 Manage Stock Items (14, MVP)**: contract+integration tests first, then Category/UnitOfMeasure/Location/Product models, serializers+forms with duplicate-SKU validation, list/search/create/edit/disable views+API, catalogue templates, seed script.
- **Phase 4 US2 Record Movements (12)**: StockLevel/StockMovement models+indexes, MovementService.record() with SELECT FOR UPDATE + first-movement IntegrityError retry (ADR-002), over-issue manager consent, movements API+pages, fractional/positive/disabled guards.
- **Phase 5 US3 Alerts (6)**: status derivation helper (out-of-stock precedence), dashboard view, /dashboard/alerts API, dashboard template.
- **Phase 6 US4 Reports & RBAC (9)**: valuation (weighted-average unit_cost — gated on user confirmation), report services/API/templates, user management, global settings, default-deny RBAC sweep.
- **Phase 7 Polish (7)**: concurrency stress (SC-003), reconciliation, search perf (SC-005), security hardening, audit-readiness (immutability), quickstart validation, full green suite.

Format validated: 62/62 IDs sequential (T001–T062), no missing/duplicates, 100% match `- [ ] T<ID> [P?] [US?] description with path`, 28 [P] parallel tasks. US labels: US1=14, US2=12, US3=6, US4=9. Story dependencies: US2→US1, US3→US2, US4→US1-3; MVP = US1.

## Outcome

- ✅ Impact: Immediately executable, checklist-compliant task list carrying the plan's ADR decisions (monolith, row-locking ledger + first-movement retry, single role + default-deny) into implementation, with every story independently testable and an explicit MVP cut line at US1.
- 🧪 Tests: none run (planning/tasks stage). tasks.md format validated programmatically (62 tasks, sequential IDs, no format violations).
- 📁 Files: `specs/001-inventory-management-system/tasks.md`.
- 🔁 Next prompts: `/sp.green` (or `/sp.red`) to begin Phase 1 setup + T015/T016 test-first cycle for US1; `my_story` etc.; confirm the `unit_cost` valuation decision before T049.
- 🧠 Reflection: The task-generation rules tightly gate test tasks ("only if spec requests TDD") — the spec's mandatory "User Scenarios & Testing" section plus plan.md's testing strategy (SC-003/005/006) justified including them, and the plan's advisory test-first gate was surfaced again in tasks.md. PowerShell split-based format check initially mis-parsed `[P]` markers; switched to regex validation for the recorded 62/62 result.

## Evaluation notes (flywheel)

- Failure modes observed: naive `-split ' '` ID extraction tripped on `[P]`/`[USx]` markers (non-fatal; re-validated with regex). No design gaps in task mapping.
- Graders run and results (PASS/FAIL): format validator PASS (0 bad lines), sequence validator PASS (T001–T062 complete, no dups), story-coverage validator PASS (US1/2/3/4 all present).
- Prompt variant (if applicable): null.
- Next experiment (smallest change to try): none for tasks; next is TDD execution starting with US1 contract/integration tests to confirm they fail before implementation.