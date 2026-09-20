# Implementation Plan: Inventory Management System

**Branch**: `001-inventory-management-system` | **Date**: 2026-09-15 | **Spec**: [`spec.md`](./spec.md)
**Input**: Feature specification from `/specs/001-inventory-management-system/spec.md`

## Summary

Primary requirement: a multi-role, multi-location web inventory management system in which users maintain a stock-item catalogue, record audited stock movements (receipts, issues, adjustments), are alerted to low/out-of-stock items, and view reports. The defining technical challenges are concurrency-safe stock quantities (FR-015 / SC-003) and an immutable movement audit trail (FR-007).

Technical approach: a monolith **Django 5.2 LTS** application served to desktop browsers, backed by **PostgreSQL 16**. Server-rendered pages (Bootstrap 5) cover all workflows; a small JSON API under `/api/v1` powers the dashboard, instant search, and report filtering. Stock levels are maintained per (item, location) and updated atomically inside database transactions using `SELECT ... FOR UPDATE` row locking, so concurrent movements can never be lost or double-counted. RBAC uses exactly three roles (admin, manager, staff) enforced server-side at both the API and page level.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Django 5.2 LTS, Django REST Framework 3.17, drf-spectacular (OpenAPI), psycopg[binary] 3, Bootstrap 5 (CDN, no build step)
**Storage**: PostgreSQL 16 (+ `pg_trgm` extension)
**Testing**: pytest + pytest-django, Django TestCase, ruff (lint + format)
**Target Platform**: Desktop web browsers (server-rendered; vanilla JS only)
**Project Type**: web
**Performance Goals**: <2s p95 for catalogue search and report filters on 10,000 items (SC-005); alerts visible on next page refresh (SC-004)
**Constraints**: ACID integrity of stock quantities under concurrency (FR-015/SC-003); movements append-only and retained indefinitely (FR-007/FR-014); no lost or duplicated transactions
**Scale/Scope**: ≤10,000 active stock items, tens of concurrent users, unbounded movement history

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Gate result — PASS on both checks (before Phase 0 research and again post-Phase 1 design).**

`.specify/memory/constitution.md` is still the **unratified** SpecKit template: every principle and section is a `[...]` placeholder. No binding constitution gates exist yet, so there is nothing to violate — but the plan also cannot claim genuine constitution compliance.

**Governance gap (flagged, not papered over):** a constitution must be ratified before `/sp.tasks` execution so gates are enforceable. Until then this plan commits to these advisory gates (recommended for ratification):
1. **Test-first**: every feature ships with tests; Red–Green–Refactor enforced during implementation.
2. **Smallest viable diff**: no features beyond FR-001..FR-015; no speculative modules.
3. **No secrets in code**: all configuration via environment variables.
4. **Immutable audit data**: movements are append-only; corrections happen via `ADJUSTMENT` movements, never edits.

## Project Structure

### Documentation (this feature)

```text
specs/001-inventory-management-system/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output — decisions & rationale
├── data-model.md        # Phase 1 output — entities, relationships, constraints
├── quickstart.md        # Phase 1 output — local setup & run
├── contracts/
│   └── openapi.yaml     # Phase 1 output — JSON API contract (OpenAPI 3.0)
└── tasks.md             # Phase 2 output (/sp.tasks command — NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── manage.py
├── config/                      # Django project package
│   ├── settings/
│   │   ├── base.py              # shared settings
│   │   ├── development.py       # DEBUG, local DB, console email
│   │   └── production.py        # HTTPS, security defaults, env-driven
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/                # Custom User (role), auth views, user admin API
│   │   ├── models.py  admin.py  views.py  serializers.py  permissions.py  tests/
│   ├── catalog/                 # UnitOfMeasure, Category, Product + CRUD/search
│   │   ├── models.py  views.py  serializers.py  forms.py  tests/
│   ├── warehouses/              # Location, StockLevel
│   │   ├── models.py  views.py  serializers.py  tests/
│   ├── movements/               # StockMovement, MovementService, override consent
│   │   ├── models.py  services.py  views.py  serializers.py  forms.py  tests/
│   ├── reports/                 # valuation / movements / low-stock reports
│   │   ├── services.py  views.py  serializers.py  tests/
│   └── dashboard/               # dashboard page: stock alerts + quick actions
│       ├── views.py  urls.py  tests/
├── templates/                   # page templates (base.html, auth, catalog, ...)
├── static/                      # CSS/JS for Bootstrap layering and API calls
├── tests/
│   ├── conftest.py              # fixtures: user roles, categories, items, locations
│   ├── integration/
│   │   ├── test_concurrency.py  # SC-003: parallel movements never lost
│   │   ├── test_permissions.py  # SC-006: role × endpoint matrix
│   │   └── test_reconciliation.py
│   └── performance/
│       └── test_search_latency.py  # SC-005 against 10k seeded rows
├── data/seed.py                 # idempotent seed: roles, sample categories/units
└── pyproject.toml               # deps, pytest config, ruff config
```

**Structure Decision**: Web-application monolith (template Option 2, adapted). All source lives under `backend/`. The Django server both renders HTML templates and exposes the JSON API, so there is **no separate frontend project**; interactive search/alerts/reports use small amounts of vanilla JS against `/api/v1`, while CRUD flows are classic form POSTs. Django migrations are the single source of truth for the schema. Tests are app-scoped (unit) plus a `backend/tests/integration/` package for concurrency, permission-matrix, and reconciliation scenarios, and a `backend/tests/performance/` package for search latency.

## Implementation Phases

Dependency order: schema/auth first, catalogue before movements, movements before alerts/reports, RBAC hardened after each layer exists.

| Phase | Deliverable | Primary requirements |
|-------|-------------|----------------------|
| **0. Bootstrap & schema** | Project skeleton, env-based settings, **custom User model with `role` before any migration**, catalog/location/movement models + first migration, pytest/ruff wired | FR-002, FR-010, FR-013* |
| **1. Item catalogue** | Category/Location/UnitOfMeasure/Product CRUD pages + `/api/v1/items`, duplicate-SKU rejection, search & filter (pg_trgm), soft-disable | FR-001, FR-002, FR-012 |
| **2. Stock levels & movements** | `StockLevel` row management, `MovementService.record()` with locking transaction; receipts/issues/adjustments; over-issue block + manager consent override; fractional-unit validation; `/api/v1/movements` + history list | FR-003..FR-007, FR-009 |
| **3. Alerts & dashboard** | Dashboard page; low-stock and out-of-stock lists computed per location; `/api/v1/dashboard/alerts` | FR-008, FR-009 |
| **4. Reports** | Valuation, recent movements, low-stock reports + filters; `/api/v1/reports/*` | FR-012, FR-013 |
| **5. RBAC hardening** | Sweep every view/endpoint with role enforcement; admin user management + settings; seed roles; permission-matrix integration tests | FR-010, FR-011, FR-014 |
| **6. Non-functional hardening** | Concurrency stress tests, performance test on 10k rows, security pass (CSRF/auth/HTTPS), audit-readiness review, final green run | SC-001..SC-007 |

Each phase ends green: the test suite passes and the acceptance scenarios it covers are automated.

## Modules, Components & Data Flow

| Module (Django app) | Responsibility |
|---------------------|----------------|
| `accounts` | Custom `User` with single `role` (admin/manager/staff), login/logout, user management API (admin-only), role permission helpers |
| `catalog` | `UnitOfMeasure`, `Category`, `Product`; CRUD, search/filter, disable workflow |
| `warehouses` | `Location`, `StockLevel`; per-(item, location) quantity authority |
| `movements` | Append-only `StockMovement` ledger + `MovementService` (transactional core), over-issue consent, filters |
| `reports` | Read-only report queries (valuation, movements, low-stock) |
| `dashboard` | Alert lists and quick actions page |

**Data flow (write path — the concurrency-critical one):**

```
Browser form/API → authn (session) + authz (role) → MovementService.record()
  → BEGIN;  SELECT ... FOR UPDATE StockLevel(product, location)
  → validate: quantity>0, unit rule, item enabled, location active
      → if ISSUE would go negative and override requested → branch: requires manager consent; write audit of approver
  → INSERT StockMovement(user, product, location, type, qty, reason, timestamp)
  → UPDATE StockLevel.quantity (receipt +, issue/adjust-−)
  → COMMIT (single atomic unit)
```

**Read path:** item lists, dashboards and reports read `StockLevel.quantity` joined to `Product` and derive low/out-of-stock flags on the fly (`qty <= reorder_level` etc.); movement history reads the immutable ledger with filters. Because bounds are decided in the same transaction that locks the row, concurrent writers serialize per (item, location) and FR-015 holds.

## API Endpoints

Base path `/api/v1`. JSON API is session-authenticated with CSRF for same-origin calls; pages and API share the same permission rules (DRY via reusable permission classes).

| Method & path | Purpose | Role |
|---------------|---------|------|
| `POST /auth/login` · `POST /auth/logout` · `GET /auth/me` | Session auth | all (authenticated for `me`) |
| `GET /categories` · `POST /categories` | List/create categories | staff+ |
| `GET /locations` · `POST /locations` | List/create locations | staff+ / manager+ |
| `GET /items?search=&category=&location=&page=` | Search/filter catalogue | staff+ |
| `POST /items` | Create item (unique SKU) | staff+ |
| `GET/PATCH /items/{sku}` | Detail / edit item | staff+ |
| `POST /items/{sku}/disable` | Soft-disable item | manager+ |
| `GET /stock-levels?item=&location=` | Current quantities | staff+ |
| `POST /movements` (`type=receipt\|issue\|adjustment`) | Record movement; over-issue requires consent | staff+ |
| `GET /movements?item=&location=&type=&from=&to=` | Movement history (immutable) | staff+ |
| `POST /movements/{id}/consent` | Manager consent for over-issue / sensitive adjustment | manager+ |
| `GET /dashboard/alerts` | Low-stock + out-of-stock per location | staff+ |
| `GET /reports/valuation` | Quantity × unit-cost valuation per item/location | manager+ |
| `GET /reports/movements` | Filtered movement report with recorder & timestamps | manager+ |
| `GET /reports/low-stock` | Low/out-of-stock list | manager+ |
| `GET /users` · `POST /users` · `PATCH /users/{id}/role` | User + role management | admin |
| `GET/PATCH /settings` | Global settings | admin |

Error taxonomy: `400` field validation (FR-005), `403` role not permitted (FR-011), `409` duplicate SKU (FR-001) / insufficient stock without consent (FR-006), `404` unknown resource, `500` logged server error. All errors return a stable JSON shape `{"detail": ..., "fields": {...}}`.

## Database Schema Considerations

See [`data-model.md`](./data-model.md) for the full entity definitions; key points:

- **Fixed identity**: custom `User` (subclass `AbstractUser`) with `role`; **must be created before the catalog tables** to reuse auth tables correctly. No migration history exists yet (greenfield), so this is the moment to decide.
- **Referential integrity**: all inventory FKs use `on_delete=PROTECT`; a disabled item or deactivated location keeps rows intact (FR-014).
- **Uniqueness**: `Product.sku` unique; `StockLevel(UNIQUE product, location)` — the seatbelt for per-location accounting; `Category.name` and `Location.code` unique.
- **Immutable ledger**: `StockMovement` exposes insert-only behaviour at the serializer/service layer (no update, no destroy); recorded `user_id` + `created_at` never change. Reconciliation is a documented `adjustment`.
- **Indexes**:
  - `Product.sku` (already unique), btree on `Product.category_id`;
  - GIN trgm index on `Product.name` (added via `pg_trgm`) for 2s search at 10k rows (SC-005);
  - btree on `StockLevel(location_id)` for per-location reporting;
  - composite btree on `StockMovement(product_id, location_id, created_at)` for history filters; btree on `(type, created_at)`.
- **Concurrency**: `SELECT ... FOR UPDATE` on the `StockLevel` row inside the movement transaction serializes writers per (item, location) — this is what makes FR-015 hold without relying on app-level retries.
- **Status flags** are derived on read (`qty == 0` → out of stock; `0 < qty <= reorder_level` → low), so flags can never drift from reality; no stored flag columns for alerts.
- **Valuation basis**: `unit_cost` on `Product`, updated as weighted average from receipts — **CONFIRMED 2026-09-16 (spec FR-016..FR-020, data-model.md:96)**.

## Dependencies & External Integrations

| Dependency | Version | Purpose | External? |
|------------|---------|---------|-----------|
| Python | 3.12 | Runtime | no |
| Django | 5.2 LTS | App framework, auth, ORM, forms, admin | no |
| Django REST Framework | 3.17 | JSON API under `/api/v1` | no |
| drf-spectacular | latest | Generates OpenAPI contract -> `contracts/openapi.yaml` | no |
| psycopg | 3 (binary) | PostgreSQL driver | no |
| PostgreSQL | 16 | Primary store; `pg_trgm` extension for search | yes (server process) |
| Bootstrap | 5 (CDN) | UI styling | yes (CDN) |
| pytest + pytest-django | latest | Unit/integration tests | no |
| ruff | latest | Lint + format | no |

**External integrations: none beyond PostgreSQL and the Bootstrap CDN.** No suppliers, customers, e-commerce, or third-party reporting.

## Security, Validation & Error Handling

- **Authentication**: Django session auth; PBKDF2-HMAC-SHA256 password hashing (default); `login_required` middleware defaults; CSRF protection on every POST; HTTPS-only + secure cookies in production; no secrets in code (`.env`).
- **Authorization**: single source of truth = `role` field + reusable permission mixins/decorators applied to every page view **and** DRF permission classes applied to every API view; default-deny (a new endpoint is closed until a role is explicitly granted).
- **Validation**: forms (pages) and DRF serializers (API) express the same rules — mandatory SKU/name (FR-001), positive quantity + required location (FR-005), fractional units only where the unit allows it (Edge Case), require a reason, block disabled items / inactive locations on movements.
- **Movement invariants**: receipts and issues/adjustments change stock by the correct sign exactly once per insert; an issue below zero is rejected with the missing-quantity message unless an explicit, manager-consented, audited override is recorded (FR-006).
- **Auditability**: every movement immutable with recorder + timestamp (FR-007); over-issue overrides persist approver + timestamp; adjustments reference their reconciliation reason.

## Testing Strategy

| Layer | Coverage |
|-------|----------|
| Unit (per app) | Model validation, `MovementService` sign/quantity logic, permission classes |
| Contract | `drf-spectacular` schema rendered to `contracts/openapi.yaml`; schema snapshot CI check |
| Integration | SC-003 concurrent movements (threads against a real Postgres); SC-006 full role×endpoint matrix; ledger→level reconciliation; over-issue consent audit trail |
| Performance | Seeded 10,000-item catalogue; assert search/filter < 2s (SC-005) |
| E2E page paths | Record receipt → issue → dashboard alert visible after save (SC-001, SC-004, SC-007) |

**Commands**: `cd backend; python -m pytest; ruff check .; ruff format --check .`

## Risks & Ambiguities

1. **[Governance — GAP]** Constitution is unratified (template placeholders only), so no binding project gates exist. Mitigation: ratify the advisory gates in the Constitution Check before running `/sp.tasks`.
2. **[Resolved — CONFIRMED 2026-09-16]** Weighted-average `unit_cost` (product-global across all locations), ROUND_HALF_UP to 2dp exactly once at storage; valuation = `on_hand × unit_cost` per (item, location), 2dp. See spec FR-016..FR-020, SC-008; checklist CHK013/CHK045.
3. **[Ambiguous — resolved by rule]** When `reorder_level == 0` and `quantity == 0`, an item is both "at reorder" and "out of stock". Rule: out-of-stock takes precedence; low-stock means `0 < qty <= reorder_level`.
4. **[Risk]** Concurrency correctness depends on the row-locking pattern; it must be proven by integration stress tests against real PostgreSQL, not just unit tests.
5. **[Risk]** The custom User model is a one-way-early decision on a greenfield repo — introduce it in Phase 0 before any data; changing it later requires a costly data migration.

## Complexity Tracking

> Filled only when Constitution Check violations require justification.

No constitution violations were found (constitution unratified — see Constitution Check). No complexity trade-offs to justify beyond the documented monolith-with-API structure, which is the *smallest* structure satisfying "frontend + backend" requirements.

**Next step**: run `/sp.tasks` to produce the test-first task list and begin Phase 0.