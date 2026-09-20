# Feature Specification: Inventory Management System

**Feature Branch**: `001-inventory-management-system`  
**Created**: 2026-09-06  
**Status**: Draft  
**Input**: User description: "i want to build inventory managemnt system guide me accordingly"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manage Stock Items (Priority: P1)

Staff and managers can add, edit, search for, and disable stock items. Each item is identified by a unique stock keeping unit (SKU) and described with a name, category, unit of measure, and a reorder level that signals when to replenish. Keeping the item catalogue accurate and up to date is the foundation of every other inventory operation.

**Why this priority**: Without a trustworthy catalogue of items, no counting, movement, or reporting is possible. This story delivers immediate value on its own: users can begin recording what they hold.

**Independent Test**: Can be fully tested by creating, editing, searching, and disabling items in the catalogue, then confirming those items appear with the entered details and a valid unique SKU. This alone delivers an MVP that tracks what items exist.

**Acceptance Scenarios**:

1. **Given** I have permission to manage items, **When** I add a new item with a SKU, name, category, unit, and reorder level, **Then** the item is saved and visible in the catalogue.
2. **Given** a SKU already exists in the catalogue, **When** I try to add another item with the same SKU, **Then** the system rejects the duplicate and shows a clear message.
3. **Given** an existing item, **When** I edit its name, category, unit, or reorder level, **Then** the changes are saved and shown in the catalogue.
4. **Given** the catalogue contains many items, **When** I search or filter by name, SKU, or category, **Then** matching items appear instantly.
5. **Given** an item that should no longer be used, **When** I disable it, **Then** it can no longer be selected for new stock movements, but its past history remains intact.
6. **Given** a required field (e.g., SKU or name) is left empty, **When** I submit the form, **Then** the system blocks the save and tells me which field is missing.

---

### User Story 2 - Record Stock Movements In and Out (Priority: P2)

Users can record stock coming in (e.g., a purchase receipt) and stock going out (e.g., a sales issue or manual adjustment), at a specific location. Each movement is timestamped with the user who recorded it, the location, the quantity, and a reason. The system updates the on-hand quantity for that item and location automatically, and keeps a full history of every movement.

**Why this priority**: This is the core value of an inventory system — knowing how much is actually available and how it changed over time.

**Independent Test**: Can be fully tested by recording several receipts and issues for one item at one location and confirming the on-hand quantity and movement history are correct after each transaction.

**Acceptance Scenarios**:

1. **Given** an item with a known quantity at a location, **When** I record a receipt of 10 units, **Then** the on-hand quantity increases by 10 and the movement is visible in history.
2. **Given** an item with a known quantity at a location, **When** I record an issue of 5 units, **Then** the on-hand quantity decreases by 5 and the movement is visible in history.
3. **Given** an issue quantity greater than the available on-hand stock at that location, **When** I submit the issue, **Then** the system blocks the transaction (or requires an explicit override) and warns me the quantity is insufficient.
4. **Given** a unit quantity that is not a valid positive number, **When** I submit a movement, **Then** the system rejects it and shows a clear error.
5. **Given** the same user records multiple movements at the same time, **When** the system processes them, **Then** each one is stored individually with an accurate running quantity.
6. **Given** an item moved between locations, **When** I review either location's stock, **Then** the quantities reflect the transfer without double counting.

---

### User Story 3 - Receive Low-Stock and Out-of-Stock Alerts (Priority: P3)

When an item's on-hand quantity at a location falls to or below its reorder level, the system flags it as low stock; when it reaches zero, it flags it as out of stock. Alerts are visible on a dashboard so users know what needs replenishment without manually checking every item.

**Why this priority**: Timely alerts prevent stock-outs that stop operations and lose sales. This story sits on top of accurate movement data but delivers standalone value by turning data into action.

**Independent Test**: Can be fully tested by setting a reorder level, recording movements that cross the threshold, and confirming the item is always flagged correctly.

**Acceptance Scenarios**:

1. **Given** an item at a location, **When** its on-hand quantity at that location drops to exactly the reorder level, **Then** the item is flagged as low stock for that location.
2. **Given** an item flagged as low stock, **When** I add stock so it rises above the reorder level, **Then** the low-stock flag is cleared automatically.
3. **Given** an item whose quantity reaches zero, **When** I view the dashboard, **Then** it is flagged as out of stock and appears in the out-of-stock list.
4. **Given** an item stored at two locations, **When** one location is low but the other is not, **Then** the alert is reported per location, not for the item as a whole.

---

### User Story 4 - Reports and Role-Based Access (Priority: P4)

Authorized users can view reports such as stock valuation, recent movement history, and low-stock lists. Access to functions is controlled by role: admins manage users and global settings, managers view reports and approve sensitive operations, and staff perform day-to-day item and movement entry. Users only see the functions their role permits.

**Why this priority**: Reporting turns recorded data into business insight, and role-based control protects data integrity and accountability. It depends on the earlier stories but can be layered on incrementally.

**Independent Test**: Can be fully tested by assigning three roles to test accounts and verifying each can only reach its permitted screens, while reports render correct figures from recorded data.

**Acceptance Scenarios**:

1. **Given** a user with the admin role, **When** they access the system, **Then** they can manage users, acceptances, and global settings.
2. **Given** a user with the manager role, **When** they access the system, **Then** they can view reports and approve operations that require manager consent, but cannot create or disable user accounts.
3. **Given** a user with the staff role, **When** they access the system, **Then** they can record item and movement data but cannot view confidential reports or manage users.
4. **Given** sufficient movement history, **When** a manager opens the stock valuation report, **Then** the report shows current quantity and valuation per item and location.
5. **Given** a product with on-hand 10 units at unit_cost 10.00 across locations, and a receipt of 10 units at 14.00 recorded afterward, **When** the manager opens the stock valuation report, **Then** the product's stored unit_cost equals exactly 12.00 (the weighted average `(10*10.00 + 10*14.00) / 20`) and the valuation row equals on_hand * 12.00, both at 2 decimal places.
6. **Given** a movement with a quantity of 0.123 (3dp) and a receipt unit_cost of 2.123 declared through the API, **When** the decimal values are processed, **Then** the system accepts the quantity at 3dp but rejects the unit_cost as invalid (more than 2dp) with a field-level error (FR-019).
7. **Given** a manager opens the recent movements report, **Then** they can filter by item, location, date range, and type, and the report lists who recorded each movement and when.
8. **Given** a user attempts an action their role does not permit, **When** they submit it, **Then** the system blocks the action and explains that permission is required.

---

### Edge Cases

- What happens when two users record movements for the same item at the same time? The system must apply each transaction exactly once and never lose or double-count a movement.
- How does the system handle a request to issue more stock than is available? It must block the normal path and, if an override is allowed, record the override clearly for audit.
- What happens when an item is disabled but still has stock? The item must remain visible for reporting and cannot be selected for new movements.
- How does the system behave when a quantity is entered as a non-integer for items that are tracked in whole units? It must either allow partial units by unit type or reject with a clear message.
- How does the system handle blank or invalid locations, SKUs, or categories? It must refuse the save and identify the field to correct.
- What happens when the on-hand quantity and the sum of recorded movements disagree (e.g., a legacy import)? The system must support a documented adjustment movement so records can be reconciled.
- What happens when a role has no access to a screen? The screen must not be shown and direct attempts must be blocked.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow authorized users to create, edit, search, and disable stock items identified by a mandatory, unique SKU.
- **FR-002**: Each stock item MUST carry a name, a category, a unit of measure, and a reorder level.
- **FR-003**: The system MUST support multiple locations, and MUST track on-hand stock quantity per item per location.
- **FR-004**: The system MUST allow recording stock movements in (receipts), out (issues), and adjustments, each with a mandatory quantity, location, reason, user, and timestamp.
- **FR-005**: The system MUST reject any movement with an invalid or non-positive quantity, or a missing location, and clearly identify the problem to the user.
- **FR-006**: The system MUST refuse to issue more stock than available at the chosen location unless an explicit, audited override is recorded.
- **FR-007**: The system MUST maintain a permanent, immutable history of every stock movement, including who recorded it and when.
- **FR-008**: The system MUST automatically flag an item at a location as low stock when its quantity reaches the reorder level, and as out of stock when it reaches zero.
- **FR-009**: The system MUST clear a low-stock flag automatically when the item's quantity at that location rises above the reorder level.
- **FR-010**: The system MUST provide role-based access with at least three roles — admin, manager, and staff — each with the permissions described in User Story 4.
- **FR-011**: The system MUST block any action the user's role does not permit and explain that permission is required.
- **FR-012**: The system MUST provide search and filtering across items, movements, and reports by name, SKU, category, location, type, and date range, as applicable.
- **FR-013**: The system MUST provide stock valuation, recent movement history, and low-stock reports to users with the required permission.
- **FR-014**: The system MUST preserve all historical data when an item is disabled or a location is deactivated.
- **FR-015**: The system MUST apply concurrent stock movements without losing or double-counting any transaction.

### Valuation & Rounding Rules *(explicit, measurable)*

These rules are normative. They make FR-013 (stock valuation) and FR-016 (weighted-average unit_cost) independently reproducible and unambiguous.

- **FR-016**: The system MUST compute **unit_cost** as a **weighted average** maintained across all locations for the product (product-global). On each receipt with quantity `q` and receipt `unit_cost` `c`, the new value is:
  `unit_cost' = ( (old_on_hand_total * unit_cost) + (q * c) ) / (old_on_hand_total + q)`
  computed over the product's total on-hand quantity across ALL locations at the moment of the receipt, then stored as `numeric(12,2)`.
- **FR-017**: The weighted-average computation MUST be performed in full decimal precision and rounded **exactly once**, at the point of storage, to 2 decimal places using **ROUND_HALF_UP** (half-up, away from zero on a tie at the 2nd decimal). No rounding may occur on intermediate values of the formula.
- **FR-018**: The system MUST store and display `unit_cost` and every monetary valuation figure to exactly 2 decimal places (`numeric(12,2)` / 2dp), and MUST store and display stock `quantity` to at most 3 decimal places (`numeric(12,3)`).
- **FR-019**: `unit_cost` MUST be validated at every entry point (item create/edit, movement API, movement form): it MUST be `>= 0`, MUST NOT exceed 9,999,999,999.99, and MUST be rejected with a clear field-level error if it is negative or has more than 2 decimal places.
- **FR-020**: The system MUST determine a product's valuation as `on_hand_quantity * unit_cost` per (item, location), each row quantized to 2 decimal places with **ROUND_HALF_UP**, and the valuation report total MUST equal the sum of those per-row values with no re-rounding that changes the penny total.

### Valuation & Rounding Rules *(explicit, measurable)*

These rules are normative. They make FR-013 (stock valuation) and FR-016 (weighted-average unit_cost) independently reproducible and unambiguous.

- **FR-016**: The system MUST compute **unit_cost** as a **weighted average** maintained across all locations for the product (product-global). On each receipt with quantity `q` and receipt `unit_cost` `c`, the new value is:
  `unit_cost' = ( (old_on_hand_total * unit_cost) + (q * c) ) / (old_on_hand_total + q)`
  computed over the product's total on-hand quantity across ALL locations at the moment of the receipt, then stored as `numeric(12,2)`.
- **FR-017**: The weighted-average computation MUST be performed in full decimal precision and rounded **exactly once**, at the point of storage, to 2 decimal places using **ROUND_HALF_UP** (half-up, away from zero on a tie at the 2nd decimal). No rounding may occur on intermediate values of the formula.
- **FR-018**: The system MUST store and display `unit_cost` and every monetary valuation figure to exactly 2 decimal places (`numeric(12,2)` / 2dp), and MUST store and display stock `quantity` to at most 3 decimal places (`numeric(12,3)`).
- **FR-019**: `unit_cost` MUST be validated at every entry point (item create/edit, movement API, movement form): it MUST be `>= 0`, MUST NOT exceed 9,999,999,999.99, and MUST be rejected with a clear field-level error if it is negative or has more than 2 decimal places.
- **FR-020**: The system MUST determine a product's valuation as `on_hand_quantity * unit_cost` per (item, location), each row quantized to 2 decimal places with **ROUND_HALF_UP**, and the valuation report total MUST equal the sum of those per-row values with no re-rounding that changes the penny total.

### Key Entities *(include if feature involves data)*

- **User**: A person with an account and exactly one role (admin, manager, or staff) that determines which functions they can use.
- **Role**: The permission level controlling access to item management, movements, reports, and user administration.
- **Product (Stock Item)**: An item in the catalogue with a unique SKU, name, category, unit of measure, and reorder level; may be active or disabled.
- **Category**: A grouping used to classify and filter stock items.
- **Location**: A warehouse or depot where stock is held; stock quantities are tracked per item per location.
- **StockLevel**: The current on-hand quantity of a product at a specific location, plus its low-stock / out-of-stock status.
- **StockMovement**: A single auditable transaction — receipt, issue, or adjustment — with quantity, location, reason, user, and timestamp.

## Assumptions *(included for context)*

The following decisions were agreed with the user during specification:

- **Scope (Q1 → B)**: The system covers item management, purchase receipts, sales issues, and adjustments. It does not include full supplier, customer, or order management in this phase; those can be addressed by a later feature.
- **User roles (Q2 → C)**: Exactly three roles exist in this phase — admin, manager, and staff — with granular permissions on item management, movements, reports, and user administration.
- **Locations (Q3 → B)**: The system supports multiple locations/warehouses and tracks stock per item per location.
- **Access channel**: The system is accessed through a standard web browser by desktop users.
- **Authentication**: Users sign in with a username and password handled securely; forgotten-password recovery is out of scope for this phase.
- **Reconciliation**: When recorded movements disagree with the physical count, users reconcile using a documented adjustment movement rather than editing history.
- **Data volume**: The system is sized for up to 10,000 active stock items and multiple concurrent users in acceptance testing.
- **Data retention**: Historical movements are retained indefinitely for auditing; no automatic deletion is performed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can record a stock movement (receipt or issue) in under 30 seconds, and the updated on-hand quantity is visible immediately after saving.
- **SC-002**: 100% of recorded stock movements are traceable to the user who recorded them and the time of recording.
- **SC-003**: Concurrent updates from multiple users never lose, duplicate, or corrupt a recorded movement in acceptance tests.
- **SC-004**: Low-stock and out-of-stock alerts appear on the dashboard no later than the next screen refresh after a movement crosses the threshold.
- **SC-005**: 95% of catalogue searches and report filters return results within 2 seconds on a catalogue of at least 10,000 items.
- **SC-006**: Users with only the staff role cannot access reports or user management, verified by end-to-end permission checks that pass 100% of the time.
- **SC-007**: A user performing a typical daily task — record a receipt, record an issue, and check the dashboard for alerts — completes all three steps without assistance on the first attempt at least 90% of the time.