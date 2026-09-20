# ADR-002: Concurrency-Safe Stock Movement Ledger

> **Scope**: Document decision clusters, not individual technology choices. Group related decisions that work together (e.g., "Frontend Stack" not separate ADRs for framework, styling, deployment).

- **Status:** Proposed
- **Date:** 2026-09-15
- **Feature:** 001-inventory-management-system
- **Context:** The spec's hardest requirement is data integrity: concurrent stock movements must never be lost, duplicated, or corrupted (FR-015/SC-003), on-hand quantities are authoritative per (item, location) (FR-003), over-issue must be blocked unless explicitly consented and audited (FR-006), and every movement becomes part of a permanent immutable history (FR-007). Separately, low/out-of-stock flags must stay perfectly in sync with reality (FR-008/FR-009) and past data must survive item/location deactivation (FR-014).

## Decision

- **Write protocol (row locking):** every movement runs in a single DB transaction: `SELECT ... FOR UPDATE` the `StockLevel(product, location)` row → validate (positive magnitude per unit rule, enabled item, active location) → append `StockMovement` row (with recorder + timestamp, set once) → update `StockLevel.quantity` (receipt +, issue/adjustment −) → commit.
- **First-movement race:** when no `StockLevel` row exists for a (product, location) pair, `SELECT ... FOR UPDATE` locks nothing, so two concurrent first movements can both attempt an insert. The `UNIQUE(product, location)` constraint is the seatbelt — the losing transaction aborts with `IntegrityError`, and the caller **retries the entire movement transaction** (re-entering the lock path) rather than swallowing or working around the error.
- **Scope guardrail:** the protocol assumes one movement touches exactly one (product, location). Multi-item batch movements would change lock-acquisition ordering and introduce deadlock risk, so they are out of scope for the ledger service.
- **Immutability:** `StockMovement` exposes insert-only behavior (no update/destroy); corrections and reconciliation happen via documented `ADJUSTMENT` movements, never edits.
- **Override path:** an issue that would go below zero aborts with 409 and the shortfall message unless a manager-consented override is recorded — the consent, approver, and timestamp persist on the movement row for audit.
- **Derived alert flags:** no stored low/out-of-stock columns; status is computed on read (`qty == 0` → out of stock; `0 < qty <= reorder_level` → low stock), so flags cannot drift.
- **Writers serialize** at the per-(item, location) row lock; no optimistic retries at the application layer.

## Consequences

### Positive

- FR-015/SC-003 made structurally simple: the lock serializes writers, so the second writer always sees the authoritative quantity before deciding an over-issue — no lost or double-counted movements.
- Immutable append-only ledger satisfies FR-007 trivially and makes reconciliation auditable by design; history survives deactivation (FR-014).
- Derived flags mean FR-008/FR-009 are correct by construction — nothing to update that can go stale.

### Negative

- Correctness depends on every future code path honoring the single-transaction rule; a `.save()` outside the service could bypass locking and re-introduce race bugs (mitigated by keeping quantity writes exclusively in `MovementService` and covering it with stress tests).
- The first-movement race adds an explicit `IntegrityError → retry` branch to `MovementService`; it must be covered by a dedicated test (two parallel first movements for the same pair resolve to exactly one row).
- The single-(product, location) guardrail means batch movements must be composed as separate movements, each with its own transaction — a deliberate constraint so lock ordering stays simple and deadlock-free.
- Per-(item, location) serialization caps write throughput on one hot item — irrelevant at this scale (tens of users, 10k items) but worth noting for growth.
- Two statuses with a reorder_level of zero need a documented precedence rule (out-of-stock wins), a spec ambiguity the plan codified.

## Alternatives Considered

- **Optimistic locking (version column + retries):** viable but pushes retry logic into every caller and complicates the over-issue consent branch. Rejected.
- **Recompute quantity from the ledger on read:** elegant but O(movements) per read and no natural guard for the running balance during reporting. Rejected.
- **PostgreSQL triggers/stored procedures:** strongest enforcement but non-portable, hard to unit-test via the Django ORM, and duplicates service logic. Rejected.

## References

- Feature Spec: `specs/001-inventory-management-system/spec.md`
- Implementation Plan: `specs/001-inventory-management-system/plan.md`
- Research (concurrency rationale): `specs/001-inventory-management-system/research.md` (§2, §4)
- Data Model (entities/constraints): `specs/001-inventory-management-system/data-model.md` (§6, §7)
- Related ADRs: ADR-001 (Backend Stack & Application Architecture)
- Evaluator Evidence: `history/prompts/001-inventory-management-system/002-inventory-mgmt-implementation-plan.plan.prompt.md`