# Research: Inventory Management System

Phase 0 output for `/sp.plan`. Resolves the NEEDS CLARIFICATION items in the Technical Context and locks the technology decisions the plan builds on.

**Date**: 2026-09-15 | **Branch**: `001-inventory-management-system`

## 1. Technology stack

### Decision
Python 3.12 + **Django 5.2 LTS** + **Django REST Framework 3.17** + **PostgreSQL 16**, with server-rendered Bootstrap 5 pages and a small JSON API (`/api/v1`). Schema managed by Django migrations.

### Rationale
- Django 5.2 is the current LTS series (latest patch 5.2.17, August 2026) with mainstream/security support to **April 2028** — the longest supported line available today. DRF officially supports Django 5.2.
- The feature is fundamentally a **transactional ledger**: receipts/issues/adjustments must be ACID and never lost or double-counted (FR-015, SC-003). PostgreSQL gives row-level locking, foreign keys, unique constraints, and `pg_trgm` for search.
- Django provides authentication, forms/validation, the admin, ORM migrations, and a permission framework out of the box — sharply reducing build effort for a phase-scoped system (per the spec's assumptions: username/password auth, role-based access).
- Server-rendered pages satisfy the "standard web browser, desktop users" access channel with the fewest moving parts.
- Verified versions (2026-09): Django latest official 6.1.1 with **5.2 LTS** supported to Apr 2028; DRF v3.17.2; Django 5.2 supports PostgreSQL 14+; Python 3.12/3.13 officially supported by DRF.

### Alternatives considered
- **MERN (React + Express + MongoDB)**: MongoDB's document model weakens the strict audit-ledger and cross-document concurrency guarantees this feature demands (per-item, per-location locking); more glue code for only marginal UI benefit.
- **FastAPI + React + PostgreSQL**: viable, but two deployment surfaces, no built-in admin/forms for a CRUD-heavy app, and more integration testing overhead than a single framework.
- **Laravel + MySQL**: PHP is a legitimate option but was declined by the user in favour of Python; MySQL's `pg_trgm`-equivalent search and advanced locking features are weaker.

## 2. Concurrency control for stock movements

### Decision
Append the movement and update the on-hand quantity inside **one transaction that locks the `StockLevel` row with `SELECT ... FOR UPDATE`**, keyed by `(product, location)`. No optimistic retries, no triggers.

### Rationale
- Two users moving stock for the same item/location serialize at the row lock: the second writer re-reads the authoritative quantity inside the transaction and can correctly evaluate an over-issue (FR-006) before committing. This directly satisfies SC-003 (no lost/duplicated movements) and is supported natively by both Django ORM (`SelectForUpdate`) and PostgreSQL.
- Run-to-complete semantics are explicit in tests: concurrent threads each record N movements and the final ledger and level are exactly consistent.

### Alternatives considered
- **Optimistic locking (version column)**: requires client retry loops and complicates the "block over-issue" rule and consent flow.
- **Recompute levels from the ledger on read**: elegant but O(movements) per read and no natural seatbelt for the running quantity at report time.
- **Triggers/stored procedures**: less portable, harder to unit-test with Django's ORM, and reimplements logic Django already owns.

## 3. Role-based access control

### Decision
A custom `User` (subclassing Django `AbstractUser`) with a single `role` column using choices `admin | manager | staff`. Enforcement via reusable view decorators (pages) and DRF permission classes (API) that share one mapping of role → capability. Exactly one role per user is guaranteed by the field.

### Rationale
- The spec is explicit: exactly three roles, each user exactly one role, functions gated by role (FR-010, FR-011, US4). A single nullable=False column *is* the simplest correct model; it also inherits Django's password handling and session auth.
- One role ⇒ no many-to-many complexity; the permission map is small (≈8 capabilities) and fully unit-testable as a matrix (SC-006).

### Alternatives considered
- **Django `Groups` + `Permissions` framework**: powerful but many-to-many machinery with no benefit for a fixed three-role spec; more subtle to test exhaustively.
- **Separate `Role` table**: fine for future user-defined roles, but an unnecessary join today and shifts the "exactly one role" invariant to app code.

## 4. Low/out-of-stock alerts

### Decision
**Derive flags on read** from `StockLevel.quantity` and `Product.reorder_level` — no stored flag columns. Precedence rule: `qty == 0` ⇒ out of stock; `0 < qty <= reorder_level` ⇒ low stock.

### Rationale
- Flags can never drift from reality (no update glitch to fix), which keeps FR-008/FR-009 trivially correct — the flag clears the moment a movement raises the quantity above the reorder level.
- Alerts must appear on the dashboard at "the next screen refresh" (SC-004); a plain indexed query at this scale (10k items, tens of concurrent users) is comfortably sub-100ms.

### Alternatives considered
- **Stored `is_low`/`is_out` booleans updated on movement**: introduces a second source of truth that can drift and needs cascade repair.
- **PostgreSQL triggers to maintain flags**: heavier and not ORM-traceable.

## 5. Search & filtering performance

### Decision
PostgreSQL **`pg_trgm` GIN index on `Product.name`** plus existing btree indexes on `sku` (unique), `category_id`, `location_id`, and composite movement-history indexes. Search/filter queries use the ORM with `icontains`/trigram-matching over name/SKU/category and join to per-location levels for stock filters.

### Rationale
- The spec targets 10,000 items with 95% of searches under 2s (SC-005). Trigram GIN indexes give fuzzy "type-ahead" sub-second name matching at this scale, while SKU/category filters are exact-equality index hits. Measured acceptance is automated in a performance test.
- No full-text engine needed: SKUs and part numbers are not natural-language text, so `FTS` ranking buys little.

### Alternatives considered
- **Elasticsearch/Solr**: gross over-engineering at 10k rows and one query type.
- **Simple `LIKE '%term%'` scans**: at 10k rows it is "fast enough" only until filters join to per-location levels; trgm reliably keeps p95 well under the 2s budget.

## 6. Fractional vs whole-unit quantities

### Decision
Each `UnitOfMeasure` carries `allow_fractional` (e.g. kg = yes, piece = no). Movement quantity is validated against the product's unit: decimals only where `allow_fractional`, else positive integers; non-integer rejection returns a clear field error (Edge Case in spec).

### Rationale
The spec explicitly permits either behaviour ("must either allow partial units by unit type or reject with a clear message"); per-unit-type is the more useful reading and matches real inventory practice.

## 7. Stock valuation cost basis — NEEDS CLARIFICATION (confirmed as assumption)

### Decision
Add **`unit_cost` to `Product`**, maintained as a **weighted-average cost** updated on each receipt (cost × qty added to existing stock value). Valuation = `Σ (StockLevel.quantity × Product.unit_cost)` per item and location.

### Rationale
FR-013/US4 require a "stock valuation" report with "current quantity and valuation per item and location", but the specification defines **no cost field anywhere** — this is an ambiguity in the spec, not derivable from the given entities. Weighted-average is the least surprising for a phase-scoped system with no PO/finance module and is auditable from the ledger.

### Alternatives considered
- **FIFO/LIFO costing**: accurate but adds a per-movement costing engine with no spec backing.
- **Last-receipt cost**: simpler than weighted average but volatile for valuation.
- **Exclude valuation from scope**: contradicts FR-013.

This item is flagged as **requires user confirmation** in `plan.md` Risks before Phase 4 is built.

## 8. Ecosystem fact-check (as of 2026-09-15)

- Django: official latest is 6.1.1; **5.2 LTS** supported to April 2028 (verified via djangoproject.com/download).
- Django REST Framework: **3.17.2**, supports Django 5.2 and Python 3.10–3.14.
- Django 5.2 supports PostgreSQL 14+; PostgreSQL **16** selected (two full release cycles of maturity, widely available in managed services).
- Python **3.12** is a stable Y-released interpreter (3.12.x) and within DRF's supported matrix.

## Decisions not needing research (spec-internal)

- Scope trimmed to inventory only; no supplier/customer/order management (Assumptions).
- Password auth with forgotten-password recovery out of scope (Assumptions).
- Reconciliation only via documented adjustment movements (Assumptions).
- Data retained indefinitely; no automatic deletion (Assumptions).
- Ability to record a movement in under 30s and see the updated quantity immediately (SC-001) is a UX page-flow target, not a server throughput target.