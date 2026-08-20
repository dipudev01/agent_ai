# Multi-Tenancy

## 1. Hierarchy

```
Platform → Institution → Organization → Department → User → Roles → Permissions → Resources
   │           │             │              │          │
   └── tenant_id is the hard boundary at EVERY layer
```

## 2. Isolation Matrix

| Layer | Isolation mechanism |
|---|---|
| **API** | token carries `tenant_id`; middleware sets tenant context; server-side only |
| **Service** | tenant-scoped principals; ABAC tenant-match rule; bulkheads |
| **Database** | `tenant_id` column + composite indexes; scoped session contextvar |
| **Cache** | key namespace `{tenant_id}:`; cross-tenant eviction impossible by construction |
| **Object storage** | prefix `{tenant_id}/` + S3 bucket policies; per-tenant KMS key |
| **Vector DB** | `tenant_id` term filter on every search + document ACL |
| **Search** | index-per-tenant-group or tenant filter; ACL in query |
| **Events** | partition by `tenant_id`; topic ACLs |
| **AI memory** | memory keys namespaced by tenant; retrieval scoped |

## 3. Enforcement Rules

1. **Never trust client-supplied tenant id.** The tenant always comes from the
   verified principal (JWT / mTLS identity).
2. **Fail closed**: any query without a resolvable tenant context is rejected.
3. **Tenant scoping in code**: `app/db/session.py` exposes `current_tenant_id`
   ContextVar; repository/query helpers must inject it. No raw global queries.
4. **Cross-tenant tests** are part of the security test suite
   (`tests/security/test_tenant_isolation.py`).

## 4. Per-Tenant Configuration

- Tenant settings: plan, quotas, model entitlements, policy overrides
  (decision thresholds), data residency, KMS key, feature flags.
- Tenants can configure agent availability (which of the 17 agents they expose)
  and tool access per role.

## 5. Data Residency

- `data_residency` on Tenant; region pinning enforced at storage.
- Tenant KMS key per residency region.
- Audit/compliance evidence stays in the tenant's residency region (with
  lawful-hold archive exceptions).

## 6. Failure Modes

| Mode | Impact | Mitigation |
|---|---|---|
| Missing tenant filter in a query | cross-tenant leak | default-denied scoping + tests + lint guard |
| Cache key collision | leak | tenant namespace prefix mandatory |
| Vector ACL missing | retrieval leak | ACL filter fail-closed in `search()` |
| Object storage policy misconfig | doc leak | bucket policy tests + guardrails |
| Event consumer without tenant check | cross-tenant write | consumer must re-resolve tenant from event and validate