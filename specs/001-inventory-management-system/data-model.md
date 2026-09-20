# Data Model: Inventory Management System

Phase 1 output for `/sp.plan`. Defines the authoritative schema (as Django models → PostgreSQL 16 migrations), including constraints, indexes, and state transitions.

**Date**: 2026-09-15 | **Branch**: `001-inventory-management-system` | **Spec**: [`spec.md`](./spec.md)

## Entities & Relationships (ERD)

```text
User ──┬─ 1 ── role (admin | manager | staff)
       │
       └── records ── StockMovement ──✂── product > Product (PROTECT)
                          │                │
                          └── location  >─ Project
                                            Location (PROTECT)
StockLevel (product, location) ── unique pair
Product      >── Category  (PROTECT)
Product      >── UnitOfMeasure (PROTECT)
Location     │
Category     ┘                          (catalog + warehouses, no SKU on Category)
```

Reads as: each `StockMovement` has exactly one `product`, one `location`, and one `user`; each `StockLevel` row is the on-hand quantity of one product at one location.

## 1. User & Role

| Column | Type | Constraints |
|--------|------|-------------|
| id | PK | auto |
| username | varchar(150) | unique, not null (Django `AbstractUser`) |
| password_hash | varchar(128) | not null (PBKDF2-HMAC-SHA256, Django default) |
| **role** | varchar(16) | choices `admin` \| `manager` \| `staff`, not null |
| email | varchar(254) | nullable |
| is_active | bool | default true (admin can deactivate — not delete) |
| date_joined | datetime | auto |

- Custom model: `class User(AbstractUser)` with `role` added. **Introduced in Phase 0 before any migration**, per plan Risks.
- Exactly one role per user (a fixed single value, per FR-010 / US4).
- User accounts are never hard-deleted; `is_active=False` preserves accountability (FR-014).
- Capabilities by role (single source of truth, shared by page decorators and DRF permission classes):

| Capability | staff | manager | admin |
|------------|:-----:|:-------:|:-----:|
| Manage items (CRUD, disable) | ✔ | ✔ | ✔ |
| Records movements (incl. adjustments) | ✔ | ✔ | ✔ |
| Over-issue / sensitive-override **consent** | ✘ | ✔ | ✔ |
| View reports (valuation, movements, low-stock) | ✘ | ✔ | ✔ |
| Manage users / roles | ✘ | ✘ | ✔ |
| Global settings | ✘ | ✘ | ✔ |

## 2. Category

| Column | Type | Constraints |
|--------|------|-------------|
| id | PK | auto |
| name | varchar(100) | unique, not null |
| description | text | nullable |
| is_active | bool | default true |
| created_at | datetime | auto |

- Used for classification and filtering (FR-002, FR-012). Deactivated categories keep existing products (PROTECT).

## 3. UnitOfMeasure

| Column | Type | Constraints |
|--------|------|-------------|
| id | PK | auto |
| name | varchar(50) | unique, not null (e.g. "Kilogram", "Piece") |
| symbol | varchar(10) | not null (e.g. "kg", "pc") |
| allow_fractional | bool | default false — permits decimal movement quantities |

- Source of the fractional-unit rule (spec Edge Case; research §6).

## 4. Location

| Column | Type | Constraints |
|--------|------|-------------|
| id | PK | auto |
| name | varchar(100) | not null |
| code | varchar(20) | unique, not null |
| is_active | bool | default true |
| created_at | datetime | auto |

- A warehouse/depot (Assumptions: multi-location). Deactivating keeps history and stock rows intact and stops new movements to/from it (FR-014).

## 5. Product (Stock Item)

| Column | Type | Constraints |
|--------|------|-------------|
| id | PK | auto |
| **sku** | varchar(50) | **unique, not null** (FR-001) |
| name | varchar(200) | not null (FR-002) |
| category | FK → Category | not null, `on_delete=PROTECT` |
| unit | FK → UnitOfMeasure | not null, `on_delete=PROTECT` |
| reorder_level | numeric(12,3) | not null, `>= 0` (FR-002) |
| unit_cost | numeric(12,2) | default 0 — **valuation basis (CONFIRMED, see plan Risks §2 / spec FR-016–FR-019)** |
| is_active | bool | default true ("disabled") |
| created_at / updated_at | datetime | auto |

- Disabling (`is_active=False`) removes the item from new-movement selection while every past StockLevel/StockMovement row remains (US1, FR-014).
- `sku` is immutable after creation.

## 6. StockLevel (the concurrency-critical row)

| Column | Type | Constraints |
|--------|------|-------------|
| id | PK | auto |
| product | FK → Product | `on_delete=PROTECT` |
| location | FK → Location | `on_delete=PROTECT` |
| quantity | numeric(12,3) | not null, `>= 0` (blocked path) |
| UNIQUE | (product, location) | **not null** |

- A row exists for each (item, location) pair that has ever held stock.
- **Concurrency protocol**: a movement transaction executes `SELECT ... FOR UPDATE` on this row, appends the `StockMovement`, updates `quantity`, then commits — serializing writers per (item, location) (FR-015 / SC-003; research §2).
- Status flags are **derived**, never stored: `quantity == 0` ⇒ out of stock; `0 < quantity <= product.reorder_level` ⇒ low stock (FR-008/FR-009; research §4).

## 7. StockMovement (append-only ledger)

| Column | Type | Constraints |
|--------|------|-------------|
| id | PK | auto |
| flow | varchar(16) | choices `receipt` \| `issue` \| `adjustment`, not null |
| product | FK → Product | not null, PROTECT |
| location | FK → Location | not null, PROTECT |
| quantity | numeric(12,3) | not null, `> 0` (magnitude) (FR-005) |
| direction | derived | receipt = +, issue = −, adjustment = ± (via signed field or sign rule) |
| reason | varchar(500) | not null (FR-004) |
| recorded_by | FK → User | not null, PROTECT ("who") (FR-004, FR-007) |
| recorded_at | datetime | auto, indexed ("when") |
| requires_override | bool | false unless issue below zero |
| override_by | FK → User | nullable (manager who consented) |
| override_at | datetime | nullable |
| reconciliation_ref | varchar(100) | nullable — documentation of the source of an adjustment (Edge Case) |

- **Immutability (FR-007)**: no update/destroy operations are exposed by serializers or services; corrections are new `adjustment` movements. `recorded_by` and `recorded_at` are set once by the transaction.
- Over-issue path (FR-006): without a manager-consented override the service aborts with 409 and the shortfall; with consent the row carries `requires_override=True`, `override_by`, `override_at`, preserving an audit trail.
- Movement history filters: item, location, type, recorded_by, date range (FR-012).

## Constraints & Indexes Summary

| Object | Type | Purpose |
|--------|------|---------|
| `users.role` | check | only admin/manager/staff |
| `products.sku` | unique | FR-001 duplicate rejection |
| `categories.name` | unique | clean catalogue |
| `locations.code` | unique | clean locations |
| `stock_levels(product_id, location_id)` | unique | per-item-per-location accounting (FR-003) |
| `stock_levels.quantity >= 0` | check | recorded quantities can't go negative on the positive path |
| `stock_movements.quantity > 0` | check | FR-005 (magnitude; sign derived from flow) |
| `products.name` | GIN (`pg_trgm`) | search/filter latency (SC-005) |
| `products.sku` btree (already unique) | index | exact SKU lookup |
| `products.category_id` btree | index | category filter |
| `stock_levels.location_id` btree | index | per-location reporting |
| `stock_movements(product_id, location_id, recorded_at)` btree | composite | movement-history filters |
| `stock_movements(flow, recorded_at)` btree | composite | type + date-range report |

## State Transitions

```text
Product:    [active] ──disable──> [disabled]
            [active] <──enable──  [disabled]          (re-activation allowed)

StockLevel: derived status on read:
            quantity == 0                 -> OUT_OF_STOCK
            0 < quantity <= reorder_level -> LOW_STOCK
            quantity > reorder_level      -> OK

Movement (write path, single transaction):
    validate (qty>0, unit rule, enabled item/location, reason)
    └─ issue below zero?
        ├─ no  -> commit (receipt +, issue/adjustment −)
        └─ yes -> need manager consent
                   ├─ consent absent -> abort 409 (shortfall in message)
                   └─ consent given  -> record override audit + commit
```

## Reconciliation

Per the spec Assumptions, when physical count disagrees with recorded on-hand, users record a documented `adjustment` (`reconciliation_ref` explains the source). History is never edited; the ledger and StockLevel converge in the same atomic transaction.