# Backend Scope Boundaries - What NOT to Build Yet

This document explicitly defines what should **NOT** be built in the MVP phase to prevent scope creep and premature optimization.

**Golden Rule:** If it's not critical for basic personal finance tracking, defer it.

---

## ❌ DO NOT BUILD (MVP Phase)

### 🚫 Authentication & User Management

#### DO NOT BUILD:
- ❌ **OAuth integration** (Google, Facebook, GitHub login)
  - **Why:** Adds complexity without core value
  - **When:** Phase 5 (Productization)
  - **Alternative:** Email/password is sufficient for MVP

- ❌ **Email verification**
  - **Why:** Not critical for personal use
  - **When:** Phase 5 (Public deployment)
  - **Alternative:** Allow immediate login after signup

- ❌ **Password reset via email**
  - **Why:** Requires email infrastructure
  - **When:** Phase 4 or 5
  - **Alternative:** Manual password reset by user

- ❌ **Two-factor authentication (2FA)**
  - **Why:** Security overkill for personal MVP
  - **When:** Phase 5 (Production hardening)

- ❌ **User roles & permissions**
  - **Why:** Single-user ownership model is sufficient
  - **When:** Phase 4 (Shared accounts)
  - **Current:** All resources belong to authenticated user

- ❌ **Session management (refresh tokens)**
  - **Why:** Adds state management complexity
  - **When:** Phase 2 or later
  - **Current:** Simple JWT with 30-min expiration

- ❌ **Rate limiting**
  - **Why:** Not needed for single-user personal use
  - **When:** Phase 5 (Public API)

- ❌ **IP-based login tracking**
  - **Why:** Security theater for MVP
  - **When:** Phase 5

- ❌ **Account deletion with data export**
  - **Why:** Edge case for personal use
  - **When:** Phase 5 (GDPR compliance)

---

### 🚫 Account Management

#### DO NOT BUILD:
- ❌ **Account editing (rename, change currency)**
  - **Why:** Immutability prevents errors
  - **When:** Phase 2 (with validation)
  - **Current:** Create new account if needed

- ❌ **Account deletion**
  - **Why:** Risk of data loss, requires orphan handling
  - **When:** Phase 2 (with soft delete + cascade rules)
  - **Current:** Accounts persist

- ❌ **Account archiving/deactivation**
  - **Why:** Not critical for MVP
  - **When:** Phase 2
  - **Alternative:** Just stop using the account

- ❌ **Account grouping/categories**
  - **Why:** Adds UI/query complexity
  - **When:** Phase 3 or 4
  - **Alternative:** Use naming conventions

- ❌ **Joint/shared accounts**
  - **Why:** Multi-user ownership is complex
  - **When:** Phase 4 (Collaboration)
  - **Current:** One user per account

- ❌ **Account balance limits/alerts**
  - **Why:** Feature bloat
  - **When:** Phase 4 (Rules engine)

- ❌ **Account color coding**
  - **Why:** Pure UI feature
  - **When:** Frontend implementation

- ❌ **Default account selection**
  - **Why:** UI preference, not backend concern
  - **When:** Frontend state management

---

### 🚫 Transaction Management

#### DO NOT BUILD:
- ❌ **Transaction editing**
  - **Why:** Violates immutability (ADR-005)
  - **When:** Never (use reversal + new transaction)
  - **Impact:** Would break audit trail

- ❌ **Transaction deletion**
  - **Why:** Violates audit trail
  - **When:** Never for completed transactions
  - **Alternative:** Reversal transactions

- ❌ **Bulk transaction creation**
  - **Why:** CSV import is better solution
  - **When:** Phase 4 (Data ingestion)

- ❌ **Transaction templates**
  - **Why:** Overlaps with recurring transactions
  - **When:** Phase 4 (Recurring)

- ❌ **Transaction attachments (receipts, images)**
  - **Why:** Requires file storage infrastructure
  - **When:** Phase 4 or 5
  - **Complexity:** File upload, storage, retrieval, deletion

- ❌ **Transaction geolocation**
  - **Why:** Not useful for personal finance
  - **When:** Probably never

- ❌ **Transaction notes/comments (separate from description)**
  - **Why:** Description field is sufficient
  - **When:** Phase 3 (if needed)

- ❌ **Transaction approval workflow**
  - **Why:** Overkill for single-user
  - **When:** Phase 4 (Shared accounts)

- ❌ **Scheduled/future transactions**
  - **Why:** Adds scheduling complexity
  - **When:** Phase 4 (Recurring transactions)
  - **Current:** Record transactions when they occur

- ❌ **Pending transaction status**
  - **Why:** Complicates balance calculation
  - **When:** Phase 2 (Transaction lifecycle states)
  - **Current:** All transactions are "posted"

- ❌ **Transaction search (full-text)**
  - **Why:** Tag/date/account filters are sufficient
  - **When:** Phase 3 or 4
  - **Current:** Basic filtering by tag, type, account

- ❌ **Transaction splitting (one expense → multiple tags)**
  - **Why:** Adds data model complexity
  - **When:** Phase 3 or 4
  - **Alternative:** Create separate transactions

---

### 🚫 Transfer Logic

#### DO NOT BUILD:
- ❌ **Currency conversion in transfers**
  - **Why:** Exchange rate complexity
  - **When:** Phase 3 (Multi-currency support)
  - **Current:** Same currency only

- ❌ **Transfer fees**
  - **Why:** Edge case, model as separate expense
  - **When:** Phase 3
  - **Alternative:** Record fee as separate transaction

- ❌ **Transfer templates/favorites**
  - **Why:** Not critical for MVP
  - **When:** Phase 4

- ❌ **Automatic transfer reversal**
  - **Why:** Complex atomicity requirements
  - **When:** Phase 2 or 3
  - **Alternative:** Manual reversal (create 2 opposite transactions)

---

### 🚫 Summaries & Reports

#### DO NOT BUILD:
- ❌ **Cached summaries**
  - **Why:** Premature optimization (ADR-004)
  - **When:** Phase 2 (Performance enhancements)
  - **Current:** Derive on-demand from transactions
  - **Impact:** Adds cache invalidation complexity

- ❌ **Yearly summaries**
  - **Why:** Monthly is sufficient for MVP
  - **When:** Phase 2
  - **Alternative:** Frontend can aggregate 12 months

- ❌ **Custom date range summaries**
  - **Why:** Nice-to-have feature
  - **When:** Phase 2 or 3
  - **Alternative:** Use monthly summaries

- ❌ **Trend analysis (growth rates, projections)**
  - **Why:** Complex analytics
  - **When:** Phase 3 or later
  - **Alternative:** Frontend charting

- ❌ **Budget tracking**
  - **Why:** Separate feature domain
  - **When:** Phase 4
  - **Complexity:** Budget creation, tracking, alerts

- ❌ **Goals tracking (savings goals)**
  - **Why:** Separate feature domain
  - **When:** Phase 4

- ❌ **Expense categories with limits**
  - **Why:** Budget feature
  - **When:** Phase 4
  - **Current:** Tags are simple labels only

- ❌ **Report generation (PDF, Excel)**
  - **Why:** External tool dependency
  - **When:** Phase 4 or 5

- ❌ **Scheduled reports via email**
  - **Why:** Email infrastructure
  - **When:** Phase 5

- ❌ **Comparative analysis (month-over-month)**
  - **Why:** Frontend analytics
  - **When:** Phase 3

---

### 🚫 Data Management

#### DO NOT BUILD:
- ❌ **Data export (CSV, JSON)**
  - **Why:** Not critical for personal use
  - **When:** Phase 4 (Data portability)
  - **Alternative:** Direct database access

- ❌ **Data import (CSV, bank statements)**
  - **Why:** Complex parsing + validation
  - **When:** Phase 4 (Data ingestion)
  - **Current:** Manual transaction entry

- ❌ **Bank integration/Plaid API**
  - **Why:** External dependency, API costs
  - **When:** Phase 5 (if ever)
  - **Complexity:** OAuth, webhook handling, reconciliation

- ❌ **Automatic categorization (ML tagging)**
  - **Why:** ML infrastructure
  - **When:** Phase 5 or later
  - **Current:** Manual tagging

- ❌ **Duplicate detection**
  - **Why:** Nice-to-have
  - **When:** Phase 3 or 4

- ❌ **Data backup automation**
  - **Why:** Ops concern, not app feature
  - **When:** Deployment phase
  - **Alternative:** Database backups

- ❌ **Data archiving (move old transactions)**
  - **Why:** PostgreSQL can handle years of data
  - **When:** Only if performance issues arise

---

### 🚫 Performance Optimizations

#### DO NOT BUILD:
- ❌ **Database connection pooling tuning**
  - **Why:** Default pool is sufficient for single-user
  - **When:** Phase 5 (High traffic)
  - **Current:** pool_size=5, max_overflow=10

- ❌ **Redis caching**
  - **Why:** Premature optimization
  - **When:** Phase 2 (if needed)
  - **Current:** Direct PostgreSQL queries

- ❌ **Database read replicas**
  - **Why:** Single user doesn't need replication
  - **When:** Phase 5 (High availability)

- ❌ **GraphQL API**
  - **Why:** REST is simpler for CRUD
  - **When:** Probably never
  - **Current:** REST API with FastAPI

- ❌ **WebSocket real-time updates**
  - **Why:** Single-user doesn't need push updates
  - **When:** Phase 5 (Collaborative features)
  - **Current:** HTTP polling is fine

- ❌ **Query optimization (indexing beyond basics)**
  - **Why:** Don't optimize until you measure
  - **When:** Phase 2 (if slow queries found)
  - **Current:** Basic indexes on foreign keys

- ❌ **Materialized views**
  - **Why:** Premature optimization
  - **When:** Phase 2 (if aggregation queries are slow)

- ❌ **Database sharding**
  - **Why:** Single database handles millions of transactions
  - **When:** Probably never needed

- ❌ **CDN for API responses**
  - **Why:** Overkill for personal use
  - **When:** Never

- ❌ **Response compression (gzip)**
  - **Why:** FastAPI handles this automatically if needed
  - **When:** Already available via middleware

---

### 🚫 Security Features

#### DO NOT BUILD:
- ❌ **Advanced password requirements (complexity rules)**
  - **Why:** Minimum length is sufficient for personal use
  - **When:** Phase 5 (Public deployment)
  - **Current:** Min 8 characters

- ❌ **Login attempt limiting**
  - **Why:** Not critical for personal use
  - **When:** Phase 5
  - **Alternative:** Use strong passwords

- ❌ **CAPTCHA**
  - **Why:** No public registration
  - **When:** Phase 5

- ❌ **API key authentication (in addition to JWT)**
  - **Why:** JWT is sufficient
  - **When:** Phase 5 (Third-party integrations)

- ❌ **Audit logging (who changed what when)**
  - **Why:** Single user doesn't need audit trail
  - **When:** Phase 4 (Shared accounts)
  - **Current:** created_at timestamps only

- ❌ **Encryption at rest**
  - **Why:** Database-level encryption is enough
  - **When:** Deployment consideration
  - **Alternative:** Encrypted PostgreSQL volume

- ❌ **Field-level encryption**
  - **Why:** Complicates queries, not needed for personal finance
  - **When:** Probably never

---

### 🚫 API Features

#### DO NOT BUILD:
- ❌ **API versioning (v2, v3)**
  - **Why:** No external API consumers
  - **When:** Phase 5 (Breaking changes)
  - **Current:** v1 is fine

- ❌ **API pagination (cursor-based)**
  - **Why:** Limit/offset is sufficient
  - **When:** Phase 3 (if needed)
  - **Current:** limit/offset pagination

- ❌ **Webhook notifications**
  - **Why:** No external integrations
  - **When:** Phase 5

- ❌ **Batch API endpoints**
  - **Why:** Not needed for UI
  - **When:** Phase 4 (Data import)

- ❌ **Partial response fields (?fields=name,balance)**
  - **Why:** Over-engineering
  - **When:** Probably never

- ❌ **API SDK generation**
  - **Why:** OpenAPI spec is sufficient
  - **When:** Phase 5 (Public API)

---

### 🚫 Multi-Currency Support

#### DO NOT BUILD:
- ❌ **Real-time exchange rates**
  - **Why:** Complex external API integration
  - **When:** Phase 3
  - **Current:** Single currency per account

- ❌ **Currency conversion in reports**
  - **Why:** Exchange rate complexity
  - **When:** Phase 3

- ❌ **Historical exchange rates**
  - **Why:** Data storage + API costs
  - **When:** Phase 3

- ❌ **Base currency selection**
  - **Why:** Not needed for single-currency MVP
  - **When:** Phase 3

---

### 🚫 Testing Infrastructure

#### DO NOT BUILD (in MVP):
- ❌ **End-to-end test suite**
  - **Why:** Manual testing is sufficient for MVP
  - **When:** Phase 2
  - **Current:** Manual testing via Swagger UI

- ❌ **Load testing**
  - **Why:** Single user = no load
  - **When:** Phase 5 (Public deployment)

- ❌ **Integration tests**
  - **Why:** Not critical for MVP
  - **When:** Phase 2

- ❌ **Test fixtures/factories**
  - **Why:** No tests yet
  - **When:** Phase 2

**Note:** Unit tests can be added incrementally, but comprehensive test coverage is deferred.

---

### 🚫 DevOps & Infrastructure

#### DO NOT BUILD:
- ❌ **Docker containerization**
  - **Why:** Direct deployment is simpler for MVP
  - **When:** Phase 2 or 3
  - **Current:** Native Python + PostgreSQL

- ❌ **CI/CD pipeline**
  - **Why:** Manual deployment is fine for MVP
  - **When:** Phase 2 or 3

- ❌ **Automated deployment**
  - **Why:** Not needed for personal use
  - **When:** Phase 5 (Production)

- ❌ **Monitoring & alerting**
  - **Why:** Can check logs manually
  - **When:** Phase 5
  - **Current:** Console logs

- ❌ **Log aggregation (ELK stack, Datadog)**
  - **Why:** Overkill for single-user
  - **When:** Phase 5

- ❌ **Health check endpoints with detailed metrics**
  - **Why:** Basic health check exists
  - **When:** Phase 5
  - **Current:** Simple /health endpoint

- ❌ **Auto-scaling**
  - **Why:** Fixed capacity is fine
  - **When:** Never needed for personal use

- ❌ **Load balancer**
  - **Why:** Single server is sufficient
  - **When:** Phase 5 (High availability)

---

### 🚫 Database Features

#### DO NOT BUILD:
- ❌ **Stored procedures**
  - **Why:** Business logic belongs in Python
  - **When:** Only if performance-critical
  - **Current:** ORM handles queries

- ❌ **Database triggers**
  - **Why:** Logic should be explicit in code
  - **When:** Avoid if possible

- ❌ **Full-text search indexes**
  - **Why:** Simple filtering is sufficient
  - **When:** Phase 3 or 4

- ❌ **Soft deletes**
  - **Why:** No deletion in MVP
  - **When:** Phase 2 (if deletion added)

- ❌ **Database-level balance calculations**
  - **Why:** Python can handle it
  - **When:** Phase 2 (if performance issue)

- ❌ **Custom PostgreSQL extensions**
  - **Why:** Vanilla PostgreSQL is sufficient
  - **When:** Probably never

---

### 🚫 Notification System

#### DO NOT BUILD:
- ❌ **Email notifications**
  - **Why:** Email infrastructure overhead
  - **When:** Phase 5

- ❌ **Push notifications**
  - **Why:** Requires mobile app + notification service
  - **When:** Phase 5 (Mobile)

- ❌ **SMS notifications**
  - **Why:** Cost + complexity
  - **When:** Probably never

- ❌ **In-app notifications**
  - **Why:** Not needed for personal use
  - **When:** Phase 4 (Shared accounts)

---

### 🚫 Advanced Analytics

#### DO NOT BUILD:
- ❌ **Spending predictions**
  - **Why:** ML complexity
  - **When:** Phase 5 or later

- ❌ **Anomaly detection**
  - **Why:** ML infrastructure
  - **When:** Phase 5 or later

- ❌ **Savings recommendations**
  - **Why:** Complex algorithm development
  - **When:** Phase 5 or later

- ❌ **Financial health score**
  - **Why:** Arbitrary metric
  - **When:** Phase 4 or later

---

## ✅ WHAT TO BUILD (MVP Focus)

For clarity, here's what **IS** in scope:

### Core Features (Already Implemented)
- ✅ User registration & login (JWT)
- ✅ Account creation (name, currency, opening balance)
- ✅ Transactions (income, expense, transfer)
- ✅ Monthly summaries (derived)
- ✅ Tag-based categorization
- ✅ Basic filtering (by account, type, tag)
- ✅ User data isolation
- ✅ Currency validation
- ✅ Error handling

### Minimal Additions Allowed
- ✅ Bug fixes
- ✅ Documentation improvements
- ✅ Performance fixes (if measurably slow)
- ✅ Security patches
- ✅ Data validation improvements

---

## 🎯 Decision Framework

When tempted to add a feature, ask:

1. **Is it critical for personal finance tracking?**
   - If NO → Defer it

2. **Does it prevent using the app?**
   - If NO → Defer it

3. **Does it add significant complexity?**
   - If YES → Defer it

4. **Can we live without it for 6 months?**
   - If YES → Defer it

5. **Does it require external dependencies?**
   - If YES → Probably defer it

6. **Is it in the roadmap for later phases?**
   - If YES → Defer it

---

## 📊 Complexity-to-Value Matrix

| Feature | Complexity | Value | Decision |
|---------|-----------|-------|----------|
| **Password reset** | High (email) | Low (single user) | ❌ Defer |
| **Transaction edit** | Medium | Low (immutability better) | ❌ Defer |
| **Cached summaries** | Medium | Low (queries fast enough) | ❌ Defer |
| **CSV import** | High (parsing) | Medium | ❌ Defer to Phase 4 |
| **Budget tracking** | High (new domain) | High (but separate feature) | ❌ Defer to Phase 4 |
| **Monthly summaries** | Low | High | ✅ Build (done) |
| **Tag filtering** | Low | High | ✅ Build (done) |

---

## 🚀 Phase Assignments

### Phase 1 (MVP) - CURRENT
**Focus:** Core personal finance tracking
**Status:** ✅ Complete

### Phase 2 (Performance)
- Cached summaries
- Transaction lifecycle states
- Idempotency keys

### Phase 3 (Accounting)
- Double-entry ledger
- Reversal workflows
- Multi-currency

### Phase 4 (Collaboration)
- Shared accounts
- CSV import
- Recurring transactions
- Budget tracking

### Phase 5 (Production)
- Email verification
- OAuth
- Mobile apps
- Public deployment

---

## 🛑 Red Flags (Scope Creep Indicators)

**STOP** if you hear these phrases:

- "We should also add..." → Review this document first
- "While we're at it..." → NO, stay focused
- "This will only take 5 minutes..." → It never does
- "Everyone expects this feature..." → Not in MVP
- "But X app has this..." → We're not X app yet
- "It would be nice if..." → Nice ≠ necessary
- "Just a small enhancement..." → Adds up quickly

---

## 📝 Acceptance Criteria

**MVP is complete when:**
- ✅ User can register & login
- ✅ User can create accounts
- ✅ User can record income & expenses
- ✅ User can transfer between accounts
- ✅ User can see monthly summaries
- ✅ All data is user-scoped (secure)
- ✅ Money calculations are accurate (no precision loss)
- ✅ Documentation exists

**MVP is NOT blocked by:**
- ❌ Missing OAuth
- ❌ Missing CSV import
- ❌ Missing budget tracking
- ❌ Missing reports
- ❌ Missing mobile app
- ❌ Missing email notifications
- ❌ Missing Docker setup

---

## 🎓 Learning from Mistakes

Common premature optimizations to avoid:

1. **"Let's add caching now"**
   - Wait until you measure slow queries
   - Current: Queries are fast enough

2. **"We'll need this for scale"**
   - Single user ≠ scale concerns
   - Wait until Phase 5

3. **"Better to build it now"**
   - Requirements change
   - YAGNI (You Aren't Gonna Need It)

4. **"It's industry standard"**
   - Maybe for production SaaS
   - Not for personal MVP

---

## 📖 Reference Documents

- [Architectural Decisions](../decisions.md) - Why we made certain choices
- [Development Roadmap](../roadmap.md) - Phased implementation plan
- [API Reference](./api-reference.md) - What IS implemented

---

## ✍️ Changelog

| Date | Change | Reason |
|------|--------|--------|
| 2024-01-12 | Initial document | Define MVP boundaries |

---

**Remember:** The goal is a working personal finance tracker, not a feature-complete SaaS product. Ship the MVP, use it, learn from it, then decide what to build next.

**When in doubt, defer it.** ✋
