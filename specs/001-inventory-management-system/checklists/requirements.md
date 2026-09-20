# Requirements Quality Checklist — Inventory Management System
Validates `specs/001-inventory-management-system/` as a *set of requirements* (unit tests in prose), not the implementation. Each item asks whether the requirement text is well-formed and ready to build against.
**Purpose**: Confirm the spec is complete, unambiguous, consistent, and measurable BEFORE another implementation phase (e.g., US4 RBAC sweep) or a fresh team member starts from it.
**Scope**: Whole spec — US1 (FR-001..FR-002), US2 (FR-003..FR-007), US3 (FR-008, FR-009, SC-004), US4 (FR-010..FR-013), concurrency (FR-015, SC-003), performance (SC-005).
**Date**: 2026-09-16
**Balanced weighting** — no single quality dimension over-represented.
---
## Requirement Completeness
- [ ] CHK001 - Is the exact set of fields required for a new stock item (SKU, name, category, unit, reorder level) fully enumerated with a defined unit_cost policy? [Completeness, Spec §US1, Data-model §Product]
- [ ] CHK002 - Are edit rules specified for EVERY catalogue field — which are immutable after creation (SKU) versus mutable (name, category, unit, reorder level, unit_cost)? [Completeness, Spec §US1]
- [ ] CHK003 - Is the disable workflow's impact on existing movements/history/stock levels fully specified (FR-014: history preserved, item hidden from new selections)? [Completeness, Spec §US1]
- [ ] CHK004 - Are the complete set of movement flows (receipt, issue, adjustment) AND all accepted directions (in/out) enumerated? [Completeness, Spec §US2]
- [ ] CHK005 - Is the full list of movement metadata fields (flow, direction, product, location, quantity, reason, user, timestamp, override_by, unit_cost) specified as mandatory-vs-optional? [Completeness, Spec §US2]
- [ ] CHK006 - Are all three alert states (low-stock, out-of-stock, ok) defined including the precedence rule when multiple apply? [Completeness, Spec §US3]
- [ ] CHK007 - Is 'low stock' defined with the same threshold semantics across the catalogue, dashboard, and reports (reorder level per product or per location)? [Completeness, Consistency, Spec §US1/§US3/§US4]
- [ ] CHK008 - Is the full RBAC permission matrix (admin/manager/staff × item/movement/alerts/reports/user-management) enumerable and complete for every endpoint? [Completeness, Spec §US4]
## Requirement Clarity
- [ ] CHK009 - Is the SKU uniqueness rule unambiguous — global unique, or per-item-case; is it case-insensitive? [Clarity, Spec §US1]
- [ ] CHK010 - Is the 'reorder level' meaning clear — a per-item threshold or a per-(item, location) threshold; which value drives alerts? [Clarity, Spec §US1]
- [ ] CHK011 - Is the movement direction→quantity sign convention (receipt = +, issue = −) explicitly documented or left implicit? [Clarity, Spec §US2]
- [ ] CHK012 - Are "low", "at reorder level", and "below reorder level" boundaries (≤ vs <) quantified for the alert flag? [Clarity, Spec §US3]
- [x] CHK013 - Is the weighted-average unit_cost formula (how receipts blend with on-hand value) precise enough to reproduce the same decimal independently? [Clarity, Measurability, Spec §US2]  **RESOLVED: FR-016/FR-017 (weighted-average formula + ROUND_HALF_UP once at 2dp), FR-019 (unit_cost validation)**
- [ ] CHK014 - Do "manager consent for over-issue" requirements define the exact approval workflow and the record-keeping (who, when) for that consent? [Clarity, Spec §US2]
- [ ] CHK015 - Is "confidential reports" defined — which reports are restricted and to which roles? [Clarity, Spec §US4]
## Requirement Consistency
- [ ] CHK016 - Do the low/out-of-stock alert rules in Spec §US3 match the status derivation used by the dashboard and the valuation report? [Consistency, Spec §US3/§US4]
- [ ] CHK017 - Do the valuation requirements (per item+location) agree with the location-per-item quantity model in the data model? [Consistency, Spec §US4, Data-model]
- [ ] CHK018 - Is over-issue handling consistent between the API rejection (SC-003 concurrency) and the manager-consent override path — one canonical rule or two contradictory ones? [Consistency, Spec §US2]
- [ ] CHK019 - Do all role definitions use the same role names/values (admin, manager, staff) across auth, permissions, and API docs? [Consistency, Spec §US4, contracts]
- [ ] CHK020 - Is the reorder/alert threshold consistent between the data-model field naming (reorder_level vs reorder_level) and spec terminology? [Consistency, Data-model, Spec]
## Acceptance Criteria Quality
- [ ] CHK021 - Can "instantly" in US1 search be verified with a numeric target (e.g., p95 < 2s), or is it a subjective bar? [Measurability, Spec §US1, SC-005]
- [x] CHK022 - Is 'update on-hand quantity reflects immediately' (SC-001) testable without a human contrast (quantified refresh semantics)? [Measurability, Spec §US1]  **RESOLVED: FR-016/FR-017 (weighted-average unit_cost formula + ROUND_HALF_UP once), FR-018 (2dp/3dp precision)**
- [ ] CHK023 - Is the out-of-stock threshold (quantity == 0) an objective, single-value acceptance criterion? [Measurability, Spec §US3]
- [ ] CHK024 - Does each US have at least one acceptance scenario that can be exercised from a fresh database state (independent testability)? [Coverage, Spec §US1-4]
- [ ] CHK025 - Are acceptance scenarios for role-based access grounded in explicit role→capability mappings that a tester can read directly? [Measurability, Spec §US4]
## Scenario Coverage
- [ ] CHK026 - Is a 'never-stocked item' scenario covered (item exists but no StockLevel row — does it alert as out-of-stock or stay silent)? [Coverage, Edge Case, Spec §US3]
- [ ] CHK027 - Are concurrent first-movement scenarios (two users recording the first StockLevel for the same item+location) covered as a requirement to serialize (SC-003)? [Coverage, Spec §US2]
- [ ] CHK028 - Is a reconciliation flow covered as a REQUIRED scenario (adjustments restoring ledger↔level parity) rather than only an implementation detail? [Coverage, Spec §US2]
- [ ] CHK029 - Is the duplicate-SKU failure mapped to a requirement with a specified user-facing outcome (clear field error)? [Coverage, Spec §US1]
- [ ] CHK030 - Are disabled-item edge cases covered across ALL stories (selectable in new movements? historical reports keep showing? valuation excludes/includes?)? [Coverage, Edge Case, Spec §US1/§US4]
## Edge Case Coverage
- [ ] CHK031 - Are zero/non-positive/invalid quantity inputs specified with rejection semantics for every movement flow? [Edge Case, Spec §US2]
- [ ] CHK032 - Is the over-issue-with-shortfall scenario precisely defined (block normal path, 409; consent path negative balance)? [Edge Case, Spec §US2]
- [ ] CHK033 - Is the fractional-quantity boundary defined — which units allow fractional and what happens on mismatch? [Edge Case, Spec §US2]
- [ ] CHK034 - Is the empty search result / no-alert state defined (dashboard shows "no alerts" vs blank)? [Edge Case, Coverage, Spec §US3]
- [ ] CHK035 - Are default-deny behaviors specified for anonymous access (401 vs 302 redirect vs 403) for BOTH the API and the pages? [Edge Case, Gap, Spec §US4]
## Non-Functional Requirements
- [ ] CHK036 - Are SC-005 search latency targets quantified AND reconciled with the index strategy (btree vs pg_trgm)? [Clarity, Completeness, Spec §SC-005]
- [ ] CHK037 - Is a concurrency guarantee (SC-003) stated with the SQL isolation mechanism (SELECT FOR UPDATE) or only as a desired outcome? [Completeness, Spec §US2]
- [ ] CHK038 - Are data-retention/immutability requirements (FR-014, FR-007) independently stated and measurable? [Completeness, Spec §US2/§US3]
- [ ] CHK039 - Is an authentication requirement stated (session-based, role-gated) beyond just "roles exist"? [Coverage, Spec §US4]
- [ ] CHK040 - Is auditability (who recorded each movement, when) required with a testable verification (SC-002)? [Measurability, Spec §US2]
## Dependencies & Assumptions
- [ ] CHK041 - Are the documented assumptions (three roles fixed; no supplier/order management; SQLite dev + PostgreSQL prod) stated and linked to their spec sections? [Coverage, Spec §Assumptions]
- [ ] CHK042 - Is the dependency chain (US2 needs US1 catalogue; US3 needs US2 data; US4 needs US1-3) documented so a new author knows ordering? [Completeness, Spec §US1-4]
- [ ] CHK043 - Is the PostgreSQL runtime dependency stated unambiguously (production requires it; dev/test may use SQLite)? [Clarity, Spec §Dependencies]
## Ambiguities & Conflicts
- [ ] CHK044 - Is 'reorder level' used with ONE meaning everywhere, or ambiguous between product-level and per-location? [Consistency, Spec §US1/§US3]
- [x] CHK045 - Is the unit_cost valuation basis (weighted-average on receipt) reconciled against the FR/SC language that implies per-movement standard cost? [Consistency, Gap, Spec §US2]  **RESOLVED: FR-016/FR-017 weighted-average formula + ROUND_HALF_UP once; FR-019 unit_cost validation; data-model.md unit_cost row CONFIRMED**
- [ ] CHK046 - Is there any conflict between "movements immutable" (FR-007) and "adjustments documented" (reconciliation) in the same spec? [Conflict, Spec §US2]
- [ ] CHK047 - Is 'out of stock' meaning consistent — exactly-zero quantity, or a disabled item also treated as out of stock? [Clarity, Consistency, Spec §US3]
## Traceability
- [ ] CHK048 - Does EVERY acceptance scenario reference its user story and priority (P1..P4) for traceability? [Traceability, Spec]
- [x] CHK049 - Are FR-001..FR-015 IDs referenced in the acceptance scenarios they validate (or is there a separate trace matrix)? [Traceability, Spec]  **RESOLVED: FR-016/FR-017 (weighted-average unit_cost formula + ROUND_HALF_UP once), FR-018 (2dp/3dp precision)**
- [ ] CHK050 - Is there a single source of truth for the API contract that a tester can diff against the implemented endpoints (contracts/openapi.yaml)? [Traceability, Spec, contracts]
