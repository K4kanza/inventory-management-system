# ADR-001: Backend Stack & Application Architecture

> **Scope**: Document decision clusters, not individual technology choices. Group related decisions that work together (e.g., "Frontend Stack" not separate ADRs for framework, styling, deployment).

- **Status:** Proposed
- **Date:** 2026-09-15
- **Feature:** 001-inventory-management-system
- **Context:** The feature spec is technology-agnostic but demands a transactional, auditable inventory ledger served to desktop web browsers: ACID stock updates under concurrency (FR-015/SC-003), immutable movement history (FR-007), username/password auth (Assumptions), and web access for a small team (≤10,000 active items, tens of concurrent users). The architect needed one integrated stack that minimizes moving parts while keeping the audit ledger safe and keeping search fast at the spec's scale; the user confirmed the Django + PostgreSQL direction during planning.

## Decision

- **Runtime language:** Python 3.12
- **Framework:** Django 5.2 LTS (security support to April 2028; chosen over the newer 6.x feature line for LTS stability)
- **API layer:** Django REST Framework 3.17 + drf-spectacular (generates `contracts/openapi.yaml`)
- **Database driver:** psycopg[binary] 3
- **Database:** PostgreSQL 16 (with `pg_trgm` for search)
- **Application shape:** single monolith under `backend/` (Django project `config/`, app package `apps/`, templates, static); server-rendered Bootstrap 5 pages for CRUD plus a JSON API at `/api/v1` for dashboard, instant search, and reports; **no separate frontend project** (vanilla JS only)
- **Schema management:** Django migrations as the single source of truth (custom `User` model introduced before any migration history exists)

## Consequences

### Positive

- One deployable, one test surface, one language — smallest viable structure satisfying "frontend + backend".
- LTS framework with built-in auth, forms, admin, ORM: drastically less glue code for a CRUD-heavy app.
- PostgreSQL gives row-level locking, unique constraints, and `pg_trgm` needed for SC-005 search at 10k rows.
- OpenAPI contract is generated (drf-spectacular), keeping the signed contract and implementation truthful.

### Negative

- Monolith couples page views and API in one process: if a future feature (reports BI, mobile app) demands an independent backend, a split will be required (reversible but not free).
- Bootstrap via CDN means no offline styling and a runtime dependency; acceptable for this access channel.
- Django 5.2 pinning forfeits 6.x features until the next LTS; deliberate for a phase-scoped system.

## Alternatives Considered

- **MERN (React + Express + MongoDB):** MongoDB's document model weakens strict ledger ACID and cross-document locking that FR-015 requires; more glue code. Rejected.
- **FastAPI + React + PostgreSQL:** two deployment surfaces, no built-in admin/forms for CRUD-heavy flows, heavier integration testing. Rejected for this scale.
- **Laravel + MySQL:** viable PHP option, declined by user in favour of Python; MySQL's trigram search and advanced locking are weaker. Rejected.

## References

- Feature Spec: `specs/001-inventory-management-system/spec.md`
- Implementation Plan: `specs/001-inventory-management-system/plan.md`
- Research (versions & rationale): `specs/001-inventory-management-system/research.md` (§1)
- Related ADRs: ADR-002 (Concurrency-Safe Stock Movement Ledger), ADR-003 (Role-Based Access Control Model)
- Evaluator Evidence: `history/prompts/001-inventory-management-system/002-inventory-mgmt-implementation-plan.plan.prompt.md`