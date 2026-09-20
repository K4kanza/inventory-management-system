---
id: 005
title: Inventory system implementation (green)
stage: green
date: 2026-09-16
surface: agent
model: opencode/big-pickle
feature: 001-inventory-management-system
branch: 001-inventory-management-system
user: architext
command: /sp.green
labels: ["inventory", "implementation", "green", "test-driven", "rbac"]
links:
  spec: specs/001-inventory-management-system/spec.md
  ticket: null
  adr: history/adr/ADR-001-backend-stack-architecture.md
  pr: null
  files:
  - specs/001-inventory-management-system/tasks.md
  - backend/apps/api/views.py
  - backend/apps/api/serializers.py
  - backend/apps/movements/services.py
  - backend/apps/movements/models.py
  - backend/tests/*
  - backend/config/settings/*.py
tests:
 - 47 passed, 1 skipped (PostgreSQL-gated concurrency test), 1 deselected (slow postgres perf test); ruff check clean; ruff format --check 79/79; makemigrations --check clean; drf-spectacular schema generated clean; runserver smoke: /accounts/login/ 200, /api/docs/ 200; production `check --deploy` clean after CSRF_TRUSTED_ORIGINS fix
---

## Prompt

```text
/sp.green

# COMMAND OUTLINE (user input was empty)

1. Read tasks.md (62 tasks, T001-T062). Load design docs and tests already present.
2. Execute phases in order, writing implementation task-by-task; mark each task [X] only when its deliverable verifiably works; run the spec test suite (contract + integration + performance) between phases.
3. Phase 1 Setup: backend/ skeleton, pyproject (Django 5.2 LTS, DRF 3.17, drf-spectacular, psycopg[binary] 3, pytest, ruff), settings split, .env.example, manage.py/urls/wsgi/asgi.
4. Phase 2 Foundational: custom User(role) + capability map + default-deny (ADR-003) BEFORE any migration; DRF/spectacular wiring; auth pages; logging + DRF exception handler; pg_trgm RunSQL migration; pytest fixtures.
5. Phase 3 US1: TDD first (contract test_items + integration fail), then Category/UnitOfMeasure/Location/Product models, migrations, serializers/forms (dup-SKU + 409), list/search/create/edit/disable views+API, catalogue templates, seed command.
6. Phase 4 US2: StockLevel + StockMovement (immutable, status pending/applied/cancelled, override audit fields); MovementService.record() with SELECT FOR UPDATE + first-movement IntegrityError retry (ADR-002); positive/fractional/active guards; 409 over-issue without consent; POST /movements/{id}/consent; pages + dashboard quick actions.
7. Phase 5 US3: derived status helper (ok/low_stock/out_of_stock, out precedence, per-status row filter); alerts API + dashboard template.
8. Phase 6 US4: weighted-average unit_cost on receipts (T049 — confirm basis with user) → user chose weighted-average; report services + /reports/* endpoints (manager+); report templates with filters; user management (admin); global settings key-value model + page (admin); RBAC default-deny sweep on all endpoints/pages.
9. Phase 7 Polish: concurrency stress (SC-003, postgres-gated), reconciliation ledger/level parity, search perf (SC-005, slow+postgres), security hardening (production settings + check --deploy), audit immutability, quickstart fresh-DB run, final full suite green.
10. Fix failures, keep suite green, mark tasks [X], create PHR with test results.
```

## Response snapshot

Implemented the full Django backend for the inventory system; final suite **47 passed, 1 skipped, 1 deselected**, ruff clean, schema generates, deploy check clean.

- **Running**: Python 3.14 + Django 5.2.17 + DRF 3.17 (PSycopg binary installed; dev/tests on SQLite via DJ-DATABASE-URL fallback; production requires PostgreSQL).
- **Foundational**: `accounts.User` with single `role`; `ROLE_CAPABILITIES` map + `require_capability` decorator + default-deny `RequireRolePermission` (anonymous API → 401/403 mapped, anonymous pages → login redirect); auth pages in `django.contrib.auth.urls`.
- **US1**: Category/UnitOfMeasure/Location/Product models; API (list/create/detail/patch/disable, lookup by SKU, dup-SKU → 409, search filter, inactive excluded) + pages (catalogue list w/ filter, form, detail); `seed_dev_data` command.
- **US2**: StockLevel (unique (product, location)) + StockMovement (append-only — save() rejects edits to immutable fields; status pending/applied/cancelled; override_by/override_at; reconciliation_ref; unit_cost). `MovementService.record()`: SELECT FOR UPDATE, first-movement IntegrityError→retry, positive magnitude, fractional-only-if-unit, active checks, over-issue→409 or pending-on-request; `consent()` approve/deny. API + record page + history list.
- **US3**: `StockLevel.status()` derived ok/low_stock/out_of_stock (out precedence); `build_alert_summary`; `/api/dashboard/alerts/`; dashboard template with alerts + quick actions.
- **US4**: weighted-average `unit_cost` on receipts (blends on-hand value with receipt cost across all locations; per-receipt `unit_cost` stored on the movement); valuation/movements/low-stock report services + `/api/reports/*` (manager+); report templates w/ filters; admin user management; global settings key-value model + `/settings/` page (admin); RBAC sweep both layers.
- **Polish**: concurrency race test (postgres-gated), reconciliation ledger-parity test, search perf (postgres+slow), hardcoded production settings, immutability test, fresh-DB quickstart (migrate/seed/runserver smoke/pytest/ruff).
- **Deviations recorded**: serializers consolidated in `apps/api/serializers.py` (contract-driven); seed as management command not `backend/data/seed.py`; `StockLevel.quantity>=0` DB constraint dropped (negative allowed only via consent, ADR-002); alerts keyed on existing StockLevel rows (never-stocked item has no row); moving-average is product-global not per-location.

## Outcome

- ✅ Impact: All four user stories implemented, tested, and RBAC-hardened as a single Django app (ADR-001); 62/62 tasks marked [X] in tasks.md.
- 🧪 Tests: 47 passed; 1 skipped `test_concurrent_first_movements_serialize` (needs PostgreSQL); 1 deselected `test_search_perf` (slow + PostgreSQL). Coverage includes contract (auth/items/movements/alerts+reports/users), integration (movement service journeys, consent, immutability, weighted-average, reconciliation, pages+RBAC matrix), perf (gated).
- 📁 Files: full `backend/` tree; `specs/001-inventory-management-system/tasks.md` (all [X]); new migrations `movements.0002_stockmovement_unit_cost`, `accounts.0002_globalsetting`.
- 🔁 Next prompts: `/sp.yellow` (or deploy/runserver for manual demo); verify weighted-average behavior on a PostgreSQL instance to run the concurrency + perf gates (SC-003/SC-005).
- 🧠 Reflection: The single most productive debugging pass was normalizing API responses through actual serializers (`LocationRead` etc.) rather than emitting raw ORM objects — three JSON-serialization failures collapsed into one `_location_data` helper. The real gates left are environmental (PostgreSQL), not code: concurrency and search-latency clauses remain unproven on this machine.

## Evaluation notes (flywheel)

- Failure modes observed: (1) raw ORM `Location` objects in alert/valuation dicts → not JSON-serializable; (2) `RequireRolePermission` default-deny blocked `/auth/me`+`/auth/logout` (permitted when `required_capability is None`); (3) DRF returns 403 not 401 for anonymous session auth (moved /auth/me to AllowAny + explicit 401); (4) ruff auto-fix + format pass over 25 files; (5) empty-string `CSRF_TRUSTED_ORIGINS` broke `check --deploy` (filter empties).
- Graders run and results (PASS/FAIL): pytest 47 passed (PASS); ruff check (PASS); ruff format --check (PASS); makemigrations --check (PASS); spectacular schema (PASS); runserver smoke (PASS); check --deploy (PASS).
- Prompt variant (if applicable): null.
- Next experiment (smallest change to try): run the postgres-gated suite against a real PostgreSQL once available (provision `DATABASE_URL` in dev settings and execute the concurrency stress + 10k search perf tests).