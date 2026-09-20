# Tasks: Inventory Management System

**Input**: Design documents from `/specs/001-inventory-management-system/`
**Prerequisites**: plan.md (required), spec.md (required for user stories + priorities), research.md, data-model.md, contracts/ (all present)
**Branch**: `001-inventory-management-system`

**Tests**: The spec's "User Scenarios & Testing (mandatory)" section and plan.md "Testing Strategy" require per-story independent tests (SC-003, SC-005, SC-006). Test tasks are therefore included and MUST be written and failing before implementation (advisory test-first gate from plan.md).

**Organization**: Tasks are grouped by user story so each story is independently implemented and tested, delivered as an MVP increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 = Manage Stock Items, US2 = Record Stock Movements, US3 = Low/Out-of-Stock Alerts, US4 = Reports & Role-Based Access)
- All paths are under `backend/` per plan.md structure

## Path Conventions

- Django project: `backend/config/` (settings split: `base.py`, `development.py`, `production.py`)
- Apps: `backend/apps/{accounts,catalog,warehouses,movements,reports,dashboard}/`
- Tests: `backend/tests/{contract,integration,performance}/` + app-level `tests/` packages
- Commands: `cd backend; python -m pytest; ruff check .; ruff format --check .`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create `backend/` skeleton: `config/` package, `apps/` package (accounts, catalog, warehouses, movements, reports, dashboard), `templates/`, `static/`, `tests/{contract,integration,performance}/`
- [X] T002 Create `backend/pyproject.toml` with pinned deps: Django 5.2 LTS, djangorestframework 3.17, drf-spectacular, psycopg[binary] 3, Django >= 4.2 + `[dev]` extras (pytest, pytest-django, ruff)
- [X] T003 [P] Configure ruff (lint + format) and pytest in `backend/pyproject.toml` (DJANGO_SETTINGS_MODULE=config.settings.development, python_files=test_*.py)
- [X] T004 Create settings split `backend/config/settings/base.py`, `development.py`, `production.py` (env-driven `SECRET_KEY`, `DATABASE_URL`, DB engine, static/secret-key handling)
- [X] T005 [P] Create `backend/.env.example` and `backend/.gitignore` entry for `backend/.env` and `backend/.venv`
- [X] T006 Create `backend/manage.py`, `backend/config/urls.py`, `backend/config/wsgi.py`, `backend/config/asgi.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Create custom `User` model (subclass `AbstractUser`) with non-null `role` field (choices admin/manager/staff) in `backend/apps/accounts/models.py` — MUST be set BEFORE any migration history (ADR-003)
- [X] T008 [P] Create role → capability map + reusable permission mixins/decorators (default-deny) in `backend/apps/accounts/permissions.py` (ADR-003)
- [X] T009 Wire `AUTH_USER_MODEL`, INSTALLED_APPS, REST_FRAMEWORK + SPECTACULAR_SETTINGS in `backend/config/settings/base.py`
- [X] T010 Create initial migration for custom `User` and `python manage.py migrate` (verify clean creation)
- [X] T011 [P] Configure Django session auth + login/logout views/urls and base templates in `backend/templates/{base.html,registration/*.html}` (auth pages)
- [X] T012 [P] Configure structured logging + DRF default exception handler in `backend/config/settings/base.py`
- [X] T013 Create PostgreSQL `pg_trgm` extension migration (apps/catalog/migrations/0001_pg_trgm.py via `RunSQL`)
- [X] T014 Create pytest fixtures in `backend/tests/conftest.py`: role-aware user factories (staff/manager/admin), authenticated client helper, category/location factories

**Checkpoint**: Foundation ready — django-admin works, custom user migrates, auth pages load, pytest runs green — user story implementation can now begin.

---

## Phase 3: User Story 1 - Manage Stock Items (Priority: P1) 🎯 MVP

**Goal**: Staff/managers add, edit, search, and disable stock items (unique SKU, name, category, unit, reorder level), with instant filter by name/SKU/category and duplicate-SKU rejection.

**Independent Test**: Create, edit, search, and disable items in the catalogue, then confirm items appear with entered details and a valid unique SKU; duplicate SKUs rejected with a clear field error.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T015 [P] [US1] Contract test for `/api/v1/items` endpoints against `contracts/openapi.yaml` in `backend/tests/contract/test_items.py`
- [X] T016 [P] [US1] Integration test for item CRUD + duplicate-SKU + disable journeys in `backend/tests/integration/test_items.py`

### Implementation for User Story 1

- [X] T017 [P] [US1] Create `Category` model in `backend/apps/catalog/models.py`
- [X] T018 [P] [US1] Create `UnitOfMeasure` model (`allow_fractional` flag) in `backend/apps/catalog/models.py`
- [X] T019 [P] [US1] Create `Location` model (unique `code`, `is_active`) in `backend/apps/warehouses/models.py`
- [X] T020 [US1] Create `Product` model (unique `sku`, FK category + unit with PROTECT, `reorder_level >= 0`, `unit_cost`, `is_active`) in `backend/apps/catalog/models.py` (depends on T017, T018)
- [X] T021 [US1] Run catalog + warehouses migrations; add btree index on `sku`/`category_id` and GIN trgm index task carried by T013 extension
- [X] T022 [P] [US1] Create catalog serializers (`Category`, `Unit`, `Item`, `ItemWrite`) in `backend/apps/catalog/serializers.py` including duplicate-SKU + required-field validation
- [X] T023 [P] [US1] Create catalog model forms mirroring the same validation in `backend/apps/catalog/forms.py`
- [X] T024 [US1] Implement item list/search/create/edit/disable views (page + API) in `backend/apps/catalog/views.py` and `backend/apps/catalog/urls.py` (staff+)
- [X] T025 [US1] Implement `/api/v1/items` endpoints (list/create/detail/patch/disable) wired into `backend/config/urls.py`
- [X] T026 [US1] Create catalogue templates: item list with search/filter form and item create/edit form in `backend/templates/catalog/`
- [X] T027 [US1] Implement disable workflow (protected by manager+; disabled items excluded from new-movement selection, history preserved) in `backend/apps/catalog/views.py`
- [X] T028 [US1] Create idempotent `backend/data/seed.py`: categories, units (kg fractional, pc whole), locations (WH-A, WH-B), sample items with reorder levels

**Checkpoint**: At this point, User Story 1 is fully functional and testable independently (MVP).

---

## Phase 4: User Story 2 - Record Stock Movements In and Out (Priority: P2)

**Goal**: Users record receipts, issues, and adjustments per location; on-hand quantity updates atomically; over-issue is blocked or manager-consented with audit; full immutable movement history retained.

**Independent Test**: Record receipts and issues for one item at one location; confirm on-hand quantity and movement history are correct after each transaction; over-issue rejected or recorded with explicit consented override.

### Tests for User Story 2 ⚠️

- [X] T029 [P] [US2] Contract test for `/api/v1/movements` endpoints in `backend/tests/contract/test_movements.py`
- [X] T030 [P] [US2] Integration test for movement journeys (receipt/issue/adjustment, over-issue consent, fractional reject) in `backend/tests/integration/test_movements.py`

### Implementation for User Story 2

- [X] T031 [P] [US2] Create `StockLevel` model (unique `product`+`location`, `quantity >= 0`) in `backend/apps/warehouses/models.py`
- [X] T032 [P] [US2] Create `StockMovement` model (flow receipt/issue/adjustment, `quantity > 0`, `reason`, `recorded_by`, `recorded_at`, override audit fields, `reconciliation_ref`) in `backend/apps/movements/models.py`
- [X] T033 [US2] Run migrations for stock models; composite index `(product_id, location_id, recorded_at)` (depends on T031, T032)
- [X] T034 [US2] Implement `MovementService.record()` in `backend/apps/movements/services.py`: single transaction, `SELECT ... FOR UPDATE` on StockLevel, first-movement `IntegrityError → retry` on `UNIQUE(product, location)` (ADR-002)
- [X] T035 [US2] Implement quantity validation in `backend/apps/movements/services.py`: positive magnitude, fractional only if unit allows, enabled item + active location required, reason mandatory
- [X] T036 [US2] Implement over-issue block + manager consent flow (abort 409 with shortfall; consent records `override_by`/`override_at`) in `backend/apps/movements/services.py` (ADR-002)
- [X] T037 [P] [US2] Create movement serializers (`MovementWrite`, `Movement`) in `backend/apps/movements/serializers.py`
- [X] T038 [US2] Implement `/api/v1/movements` POST + GET and `/api/v1/movements/{id}/consent` endpoints in `backend/apps/movements/views.py` + `urls.py`
- [X] T039 [US2] Create movement record page + history list (with filters) templates in `backend/templates/movements/`
- [X] T040 [US2] Wire movement pages/API into dashboard quick actions (record receipt/issue) in `backend/apps/dashboard/`

**Checkpoint**: At this point, User Stories 1 AND 2 both work independently; movements are immutable and auditable.

---

## Phase 5: User Story 3 - Receive Low-Stock and Out-of-Stock Alerts (Priority: P3)

**Goal**: Dashboard flags items low-stock (qty <= reorder level) or out-of-stock (qty == 0) per location, with flags clearing automatically when stock rises above reorder level (derived on read, per ADR-002).

**Independent Test**: Set a reorder level, record movements crossing the threshold, and confirm the item is flagged low-stock / out-of-stock per location on the dashboard and that the flag clears when stock rises.

### Tests for User Story 3 ⚠️

- [X] T041 [P] [US3] Contract test for `/api/v1/dashboard/alerts` in `backend/tests/contract/test_dashboard.py`
- [X] T042 [P] [US3] Integration test for alert threshold crossings (low, out, clear; per-location independence) in `backend/tests/integration/test_alerts.py`

### Implementation for User Story 3

- [X] T043 [US3] Implement shared status derivation helper (`ok | low_stock | out_of_stock`, out-of-stock precedence) in `backend/apps/warehouses/services.py`
- [X] T044 [US3] Implement dashboard view with per-location low/out-of-stock queries in `backend/apps/dashboard/views.py`
- [X] T045 [P] [US3] Implement `/api/v1/dashboard/alerts` endpoint + `AlertSummary` serializer in `backend/apps/dashboard/serializers.py`
- [X] T046 [US3] Create dashboard template with alert lists and quick actions in `backend/templates/dashboard/dashboard.html`

**Checkpoint**: User Story 3 independently functional — alerts appear on next refresh (SC-004).

---

## Phase 6: User Story 4 - Reports and Role-Based Access (Priority: P4)

**Goal**: Managers view reports (stock valuation, recent movements, low-stock lists) with filters; admins manage users and global settings; every page/endpoint enforces roles (staff cannot reach reports or user management).

**Independent Test**: Assign three roles to test accounts and verify each reaches only its permitted screens while reports render correct figures from recorded data; blocked actions explain permission required.

### Tests for User Story 4 ⚠️

- [X] T047 [P] [US4] Permission matrix integration test (full role × endpoint/page matrix, SC-006) in `backend/tests/integration/test_permissions.py`
- [X] T048 [P] [US4] Integration test for valuation + movement report correctness in `backend/tests/integration/test_reports.py`

### Implementation for User Story 4

- [X] T049 [US4] Implement weighted-average `unit_cost` update on receipts in `backend/apps/movements/services.py` (valuation basis, plan Risk #2 — confirm unit_cost decision with user before building)
- [X] T050 [P] [US4] Implement report services (valuation, recent movements, low-stock) in `backend/apps/reports/services.py`
- [X] T051 [P] [US4] Implement `/api/v1/reports/*` endpoints + serializers in `backend/apps/reports/serializers.py`, `views.py`, `urls.py` (manager+)
- [X] T052 [US4] Create report page templates with item/location/date-range/type filters in `backend/templates/reports/`
- [X] T053 [US4] Implement admin user management (create user, change role, deactivate) in `backend/apps/accounts/views.py` + `backend/templates/accounts/` (admin)
- [X] T054 [US4] Implement global settings (key-value) model + admin page in `backend/apps/accounts/settings.py` + templates
- [X] T055 [US4] RBAC hardening sweep: apply `permissions.py` mixins/decorators + DRF permission classes to EVERY view/endpoint (default-deny) per ADR-003

**Checkpoint**: All four user stories independently functional end-to-end.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements affecting multiple user stories

- [X] T056 [P] Concurrency stress test: parallel movements for the same (item, location) never lost/duplicated (SC-003) in `backend/tests/integration/test_concurrency.py`
- [X] T057 [P] Reconciliation test: `adjustment` movement restores ledger/level parity in `backend/tests/integration/test_reconciliation.py`
- [X] T058 [P] Performance test: 10k-item catalogue search/filter p95 < 2s (SC-005) in `backend/tests/performance/test_search_latency.py` (marked slow)
- [X] T059 Security hardening pass: HTTPS/secure-cookie defaults in `backend/config/settings/production.py`, CSRF coverage, no secrets in code
- [X] T060 [P] Audit-readiness: verify no update/delete paths exist for `StockMovement` (immutable, FR-007) and history survives item/location deactivation
- [X] T061 Run quickstart.md validation end-to-end on a fresh DB (migrate, seed, runserver smoke, pytest, ruff)
- [X] T062 Final full-suite run: `python -m pytest` (incl. slow), `ruff check .`, `ruff format --check .` all green

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS all user stories** (custom `User` before any migration)
- **User Stories (Phase 3+)**: All depend on Foundational completion (ADR-001 monolith, ADR-003 authZ)
  - US2 depends on US1 completing the catalogue (movements reference items; also `unit_cost` seeds from US1)
  - US3 depends on US2 (movement data drives alerts)
  - US4 depends on US1–US3 (reports/RBAC sit on top); RBAC sweep also hardens US1–US3 endpoints
  - Stories proceed sequentially in priority order; US1 is the MVP
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: After Foundational — no dependencies on other stories (MVP)
- **US2 (P2)**: After Foundational **and US1** — independently testable with seeded items
- **US3 (P3)**: After US2 — independently testable with its own thresholds
- **US4 (P4)**: After US1–US3 — full permission matrix verified last

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Migrations and models before services (per app)
- Services before endpoints; endpoints before templates
- Story complete (all checkboxes) before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (Phase 2)
- Within a story: tests [P] in parallel; independent models [P] in parallel; serializers/forms [P] in parallel
- Different stories are sequential in this plan (single implementer), but US1 endpoints and US1 templates are parallelizable [P]
- Polish [P] tasks (concurrency/reconciliation/perf/audit) can run in parallel once stories are green

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests together (write first, expect FAIL):
Task: "Contract test for /api/v1/items endpoints in backend/tests/contract/test_items.py"
Task: "Integration test for item CRUD + duplicate-SKU + disable journeys in backend/tests/integration/test_items.py"

# Launch all US1 models together:
Task: "Create Category model in backend/apps/catalog/models.py"
Task: "Create UnitOfMeasure model in backend/apps/catalog/models.py"
Task: "Create Location model in backend/apps/warehouses/models.py"

# Launch serializers and forms together (after models):
Task: "Create catalog serializers in backend/apps/catalog/serializers.py"
Task: "Create catalog model forms in backend/apps/catalog/forms.py"
```

> **Note**: Commands are `python -m pytest`, `python manage.py runserver` etc. run from `backend/` (Windows PowerShell). Run project commands directly in a fresh shell — the parallel "launch" lines are coordination hints, not literal executable shell syntax.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Write US1 tests (fail), implement US1 models → services → endpoints → templates
4. **STOP and VALIDATE**: run US1 contract + integration tests independently; demo the catalogue
5. Deploy/demo if ready (SC-001 catalogue path)

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. Add US1 → test independently → Demo (MVP: track which items exist)
3. Add US2 → test independently → Demo (core value: real stock movements)
4. Add US3 → test independently → Demo (alerts on dashboard)
5. Add US4 → test independently → Demo (reports + hardened RBAC)
6. Polish: concurrency/perf/security/audit gates → full green suite (SC-001..SC-007)

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done, US1 proceeds (bottleneck — everything depends on the catalogue)
3. After US1, US2 and US3 can proceed in parallel (US2 core, US3 alerts)
4. US4 lands last (reports + RBAC sweep over all existing endpoints)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to user story for traceability (US1..US4)
- Each user story is independently testable via its Independent Test section
- Verify tests fail before implementing (test-first advisory gate from plan.md)
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
- ADR decisions to honor: ADR-001 (monolith, no separate frontend), ADR-002 (row-locking ledger, first-movement retry, single-(item,location) guardrail), ADR-003 (single role field, default-deny)
- Confirmation gate (passed 2026-09-16): `unit_cost` weighted-average valuation basis CONFIRMED — see plan Risks §2 resolution / spec FR-016..FR-020.