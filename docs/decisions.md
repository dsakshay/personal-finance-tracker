# Architectural Decisions Log

This document records significant architectural and design decisions made during the development of the Personal Finance Tracker.

The goal is to preserve *why* a decision was made, not just *what* was implemented.

---

## ADR-001: Platform Multi-User Support from Day One

**Decision**  
The system will support multiple independent users from the start, with strict data isolation between users.

**Rationale**  
- Enables future public deployment without major refactors  
- Enforces clear ownership of financial data  
- Minimal added complexity at early stages  

**Consequences**  
- All core entities must include `user_id`  
- All queries must be scoped to the authenticated user  

**Status**  
Accepted

**Date**  
2026-01-06

---

## ADR-002: Integer-Based Monetary Storage

**Decision**  
All monetary values will be stored as integers in the smallest currency unit (e.g., cents, paise).

**Rationale**  
- Avoids floating-point precision errors  
- Industry standard for financial systems  
- Simplifies validation and aggregation logic  

**Consequences**  
- UI must handle formatting and conversion  
- Database fields use integer types (`BIGINT`)  

**Status**  
Accepted

**Date**  
2026-01-06

---

## ADR-003: Account-Centric Transaction Model

**Decision**  
All financial activity flows through accounts. There is no global balance.

**Rationale**  
- Mirrors real-world financial systems  
- Enables clear tracing of money movement  
- Simplifies support for multiple accounts per user  

**Consequences**  
- Every transaction must reference an account  
- Aggregations are account-aware  

**Status**  
Accepted

**Date**  
2026-01-06

---

## ADR-004: Derived Aggregates for MVP

**Decision**  
Monthly and yearly summaries will be derived from transaction data rather than stored.

**Rationale**  
- Keeps MVP simple and transparent  
- Avoids premature denormalization  
- Allows easy validation of correctness  

**Consequences**  
- Aggregation queries run on demand  
- Performance optimizations deferred to later phases  

**Status**  
Accepted

**Date**  
2026-01-06

---

## ADR-005: Transaction Immutability in MVP

**Decision**  
Transactions are immutable once created. Corrections are represented as reversal or compensating entries.

**Rationale**  
- Preserves auditability  
- Avoids complex edit histories in MVP  
- Aligns with accounting best practices  

**Consequences**  
- UI must support correction flows  
- Historical data remains intact  

**Status**  
Accepted

**Date**  
2026-01-06

---

## ADR-006: Simplified Transfer Representation in MVP

**Decision**  
Transfers are represented as two linked transactions (debit and credit).

**Rationale**  
- Simple to implement and reason about  
- Matches account-centric design  
- Can be upgraded later to a ledger/journal model  

**Consequences**  
- Backend must ensure atomic creation  
- Consistency enforced at service layer  

**Status**  
Accepted

**Date**  
2026-01-06

---

## ADR-007: Deferred Double-Entry Ledger Model

**Decision**  
A full double-entry bookkeeping system (journal entries) will be deferred to a later phase.

**Rationale**  
- Adds significant conceptual and implementation complexity  
- Not required for MVP correctness  
- Schema designed to allow future migration  

**Consequences**  
- MVP relies on single-entry with safeguards  
- Migration path must be documented  

**Status**  
Accepted (Deferred)

**Date**  
2026-01-06

---

_End of decisions log_

