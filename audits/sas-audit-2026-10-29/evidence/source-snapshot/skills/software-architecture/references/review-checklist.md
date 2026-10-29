# Architecture review and critique checklist

First reconstruct what is actually known: existing topology, workload, incident history, data classifications, deployments, metrics and constraints. Do not infer absent infrastructure. Separate observed issues from plausible risks.

For each finding, record:

| Priority | Evidence / assumption | Failure or concern | Likely impact | Recommendation | Effort | Validation |
|---|---|---|---|---|---|---|

Review dimensions:

1. **System boundaries and coupling:** single points of failure, sync chains, ownership, service proliferation, high-risk dependency surfaces.
2. **Correctness and data:** transaction scope, idempotency, race conditions, deduplication, temporal ordering, schema migrations, backup/restore.
3. **Performance and scaling:** evidence from metrics, hot paths, read/write amplification, indexes, fan-out, N+1, queues and backpressure, cache invalidation.
4. **Resilience:** timeouts, retries with jitter/bounds, circuit breaking when useful, partial failure, degraded modes, capacity/region assumptions.
5. **Security:** threat boundary mapping, authentication and tenant authorization, secrets, encryption, logging hygiene, supply chain, administrative actions, abuse prevention.
6. **Operational maturity:** structured telemetry, SLI/SLO coverage, on-call runbooks, canaries, rollback, reproducible builds, cost attribution, recovery drills.
7. **Delivery complexity:** maintainability, ownership, skill fit, testing seam quality and phased migration feasibility.

Prioritize by business risk and implementation effort. Propose quick wins plus medium-term decisions, not a wholesale redesign without necessity. Offer a validation plan (load test, security test, fault injection, observability baseline, prototype or ADR) for uncertain claims.
