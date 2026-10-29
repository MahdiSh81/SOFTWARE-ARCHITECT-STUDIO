# Example: modular SaaS architecture (PROPOSED, not production evidence)

**Constraints:** small team, moderate traffic, B2B multi-tenant product, uncertain peak; costs need validation.

**Recommendation:** modular API/application, PostgreSQL as transactional store, background job queue, managed identity, scoped server-side tenant access and a metrics/logging baseline. Avoid early microservice fragmentation.

## Requirements

- FR-001: Tenant members sign in with auditable organization membership.
- FR-002: Tenant members can only read and update own organization's records.
- NFR-001: The team must be able to restore a backed-up database in a documented recovery drill.

## Assumptions

- ASM-001: No regulatory demand for dedicated database per organization. Validate before selection.

## Decisions

- ADR-001: Propose shared PostgreSQL with mandatory tenant-scoped repository access, defense-in-depth database policies and cross-tenant leakage tests. Revisit if customer contractual isolation changes.
- ADR-002: Propose modular monolith before microservices, review after independently owned deployments or repeated scaling bottlenecks emerge.

## Open validation

- Run tenant access negative tests and restore drills.
- Measure peak RPS and DB IO before capacity commitments.
