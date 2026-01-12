# MVP Scope Checklist

Quick reference for scope decisions. When considering a feature, check if it's on the "Do Not Build" list.

## 🚫 Quick "Do Not Build" List

### Authentication
- [ ] OAuth (Google/GitHub login)
- [ ] Email verification
- [ ] Password reset via email
- [ ] Two-factor authentication
- [ ] Refresh tokens
- [ ] Rate limiting
- [ ] Session management

### Accounts
- [ ] Account editing
- [ ] Account deletion
- [ ] Account archiving
- [ ] Shared/joint accounts
- [ ] Account balance alerts
- [ ] Account grouping

### Transactions
- [ ] Transaction editing
- [ ] Transaction deletion
- [ ] Bulk creation
- [ ] File attachments (receipts)
- [ ] Scheduled transactions
- [ ] Pending status
- [ ] Full-text search
- [ ] Transaction splitting

### Transfers
- [ ] Currency conversion
- [ ] Transfer fees
- [ ] Automatic reversal

### Reports
- [ ] Cached summaries
- [ ] Custom date ranges
- [ ] Budget tracking
- [ ] Goals tracking
- [ ] PDF/Excel export
- [ ] Scheduled reports

### Data
- [ ] CSV import/export
- [ ] Bank integration (Plaid)
- [ ] Automatic categorization (ML)
- [ ] Duplicate detection

### Performance
- [ ] Redis caching
- [ ] Database replicas
- [ ] GraphQL
- [ ] WebSockets
- [ ] Materialized views

### Security
- [ ] Complex password rules
- [ ] Login attempt limiting
- [ ] CAPTCHA
- [ ] Audit logging
- [ ] Field-level encryption

### DevOps
- [ ] Docker
- [ ] CI/CD
- [ ] Monitoring/alerting
- [ ] Log aggregation
- [ ] Auto-scaling

### Notifications
- [ ] Email notifications
- [ ] Push notifications
- [ ] SMS notifications

### Testing
- [ ] E2E test suite
- [ ] Load testing
- [ ] Comprehensive integration tests

---

## ✅ MVP Feature Checklist (Already Done)

- [x] User registration & login (JWT)
- [x] Password hashing (bcrypt)
- [x] Account creation
- [x] List accounts
- [x] Create income transaction
- [x] Create expense transaction
- [x] Create transfer (atomic)
- [x] List transactions
- [x] Filter transactions (account, type, tag)
- [x] Monthly summary
- [x] Tag breakdown
- [x] User data isolation
- [x] Currency validation
- [x] Error handling
- [x] API documentation (Swagger)

---

## 🎯 Decision Shortcuts

| Question | Answer | Action |
|----------|--------|--------|
| Does it require email? | YES | ❌ Defer |
| Does it require ML? | YES | ❌ Defer |
| Does it require file storage? | YES | ❌ Defer |
| Does it require external API? | YES | ❌ Defer |
| Is it for multi-user? | YES | ❌ Defer to Phase 4 |
| Is it for performance? | YES | ❌ Defer to Phase 2 |
| Is it for production? | YES | ❌ Defer to Phase 5 |
| Is it a bug fix? | YES | ✅ Build now |
| Is it a security fix? | YES | ✅ Build now |

---

## 🛑 Stop Words

If you hear these, **STOP and review scope**:

- "While we're at it..."
- "We should also..."
- "Just a quick add..."
- "It would be nice if..."
- "Everyone expects..."
- "But X app has..."
- "This will be easy..."
- "We'll need this eventually..."

---

## ✍️ Approval Required

Before building ANY new feature:

1. ☐ Check [Scope Boundaries](./scope-boundaries.md)
2. ☐ Verify it's not on "Do Not Build" list
3. ☐ Ask: "Does MVP work without this?"
4. ☐ If answer is "yes" → Defer it
5. ☐ Document decision

---

## 📊 Current Status

**MVP Phase 1:** ✅ **COMPLETE**

**Next Steps:**
1. Use the app with real data
2. Identify actual pain points
3. Prioritize Phase 2 features based on usage
4. Resist temptation to add features preemptively

---

**Remember:** Build less, ship faster, learn more. 🚀
