# ADR-003: Role-Based Access Control Model

> **Scope**: Document decision clusters, not individual technology choices. Group related decisions that work together (e.g., "Frontend Stack" not separate ADRs for framework, styling, deployment).

- **Status:** Proposed
- **Date:** 2026-09-15
- **Feature:** 001-inventory-management-system
- **Context:** The spec mandates exactly three roles — admin, manager, staff — with one role per user (FR-010), blocked actions must explain that permission is required (FR-011), staff must never reach reports or user management (SC-006), and users are deactivated rather than deleted so accountability history survives (FR-014). Both the server-rendered pages and the `/api/v1` JSON API must enforce the same rules, and SC-006 demands a 100%-passing role × endpoint matrix in tests.

## Decision

- **AuthN:** Django session authentication with PBKDF2 password hashing (framework default), CSRF on all mutating requests, HTTPS + secure cookies in production, secrets via `.env`.
- **AuthZ — model:** custom `User` (subclass `AbstractUser`) with a single non-null `role` column: `admin | manager | staff`. Exactly one role per user is a schema-level fact.
- **AuthZ — enforcement:** a single capability map (shared source of truth) consumed by page-level view decorators/mixins and DRF permission classes; **default-deny** — a new endpoint stays closed until a role is explicitly granted.
- **Admin controls:** create users, change roles, and deactivate accounts (`is_active=False`); accounts are never hard-deleted.

## Consequences

### Positive

- Exactly matches the fixed three-role spec with zero many-to-many machinery; the permission matrix is small, explicit, and fully unit-testable (SC-006).
- One enforcement definition keeps pages and API from drifting apart, so staff can't slip through via an unguarded endpoint.
- Default-deny means a forgotten decorator fails closed (safe) rather than open.
- Deactivation (not deletion) preserves who recorded what (FR-014, FR-007).

### Negative

- A `role` field is rigid: adding a fourth role or per-object permissions (e.g., "manager of WH-A only") requires a migration to a richer model — an unlikely-but-real future constraint.
- Non-negotiated standards: session/CSP hardening beyond defaults (session expiry, password policy) is not specified in the plan and would need separate configuration.
- The framework's built-in `Permissions`/`Groups` remain unused, so future delegation scenarios would require rework.

## Alternatives Considered

- **Django `Groups` + `Permissions` framework:** many-to-many grants add machinery with no benefit for a fixed three-role spec and make the SC-006 matrix harder to enumerate. Rejected.
- **Separate `Role` table (+ M2M to User):** supports future user-defined roles but adds joins and moves the "exactly one role" invariant from schema to application code today. Rejected for this phase; documented as the migration path if roles become dynamic.

## References

- Feature Spec: `specs/001-inventory-management-system/spec.md`
- Implementation Plan: `specs/001-inventory-management-system/plan.md`
- Research (RBAC rationale): `specs/001-inventory-management-system/research.md` (§3)
- Data Model (role matrix, User entity): `specs/001-inventory-management-system/data-model.md` (§1)
- Related ADRs: ADR-001 (Backend Stack & Application Architecture)
- Evaluator Evidence: `history/prompts/001-inventory-management-system/002-inventory-mgmt-implementation-plan.plan.prompt.md`