# Specialized architecture patterns

## Multi-tenant B2B SaaS

Decide tenant identity propagation and authorization before database isolation. Compare:
- Shared database/shared schema with tenant key: operationally lean, high need for disciplined scoped queries, tests and row-level safeguards.
- Shared database/separate schemas: moderate isolation with migration/operational complexity.
- Database per tenant: strongest configuration/restore isolation in many contexts but greater operational overhead and cost.
- Hybrid: segment enterprise/high-compliance tenants only when justified.

Review tenant ID authority, cross-tenant queries, data export/deletion, backups and restoration, quotas, noisy neighbors, encryption boundaries, observability, support staff impersonation and audit trails. Do not recommend DB isolation as a substitute for authorization.

## Identity, roles and administration

Specify identity provider, session/token lifetime and revocation, OAuth/OIDC flows where relevant, RBAC vs ABAC, privilege elevation, MFA, invite lifecycle, account linking, offboarding and recovery. Model organization/tenant memberships explicitly. Define access-control checks on every resource transition. Include auditability and effective-permission tests; distinguish UI hiding from server-side enforcement.

## Analytics applications

Separate transactional ingestion from analytical serving when needed. Map collection, validation, event schema evolution, buffering, CDC/batch vs streaming, warehouse/lakehouse options, ETL/ELT, semantic definitions, data freshness, retention, lineage, PII access controls, late events and reconciliation. Provide data quality gates, backfills and reproducibility.

## Marketplace and ride-sharing applications

Discuss matching/dispatch, geospatial indexing, location freshness, driver/rider state transitions, concurrent reservation contention, trips and payments, pricing, fraud, cancellation, notifications, audit logs, retries, idempotency and eventual consistency. Begin with a bounded MVP rather than prematurely requiring fully distributed geo-sharding.

## LLM-powered applications

Define measurable quality tasks and representative eval datasets first. Compare hosted models and self-hosted inference based on quality, latency, context, geography/privacy, throughput, cost and operations. For retrieval systems cover corpus provenance, chunking/indexing, access-filtered retrieval, hybrid search, evaluation, reindexing and stale content. For tool-using agents enforce scoped credentials, human approval for consequential actions, prompt-injection defenses, tool argument validation and audit trails. Address hallucination and abstention policies, rate limits, caching, prompt/version management, fallbacks, incident monitoring and per-request cost accounting. Treat model benchmark rankings, pricing, context limits and API features as rapidly changing facts requiring current vendor documentation.
