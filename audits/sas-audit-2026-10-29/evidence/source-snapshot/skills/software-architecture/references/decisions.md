# Architecture decisions, sizing and trade-offs

## Decision record (ADR)

Use concise entries:

- **ADR-NNN / Status / Date:** Proposed, Accepted or Superseded; date only if known or explicitly generated.
- **Context:** the requirement, known constraints, current design and missing facts.
- **Decision:** specific choice and scope.
- **Options considered:** reasonable alternatives, including a simpler baseline.
- **Consequences:** benefits, limitations, operational and cost impacts.
- **Validation / revisit trigger:** evidence required and thresholds that would alter choice.

Never disguise preferences as universal best practices. Avoid unsupported production performance figures, magic thresholds and fabricated cloud costs.

## Comparing alternatives

Compare only decisive criteria—usually developer velocity, data model fit, correctness/consistency, scale, reliability, security, operational burden, flexibility, team familiarity and cost. Say which are hard constraints, and offer a recommendation tied to user priorities. Use numerical scores only if the chosen weights and evidence are stated; otherwise use qualitative trade-offs.

## Database selection guide

- Begin with entity relationships, query patterns, transactions, concurrency, retention, tenant isolation and data size.
- Relational DB: default candidate when transactional consistency, joins and integrity dominate.
- Document DB: consider for document-centric aggregate access and flexible schema, while weighing transactional and query limitations.
- Key-value: consider for low-latency access and narrowly defined read/write patterns.
- Search engine: typically a complementary indexing/search subsystem, not an automatic system of record.
- Warehouse/columnar analytics: consider for large analytical scans, aggregations and separation of OLTP/OLAP.
- Graph: consider for graph traversals as a primary requirement; test alternatives first.
- Vector search: consider for embedding-based retrieval after defining relevance metrics and hybrid-search needs; often start with an existing database extension.

## Capacity and cost reasoning

With provided workload data, derive QPS = daily requests × peak factor / 86,400 when a daily peak factor definition is clear. Estimate storage from records × average bytes × replicas/index/backup overhead, with assumptions explicit. Separately consider ingress/egress, compute, storage IOPS, human operation costs and commercial licensing. Mark any broad industry examples as illustrative, not forecasts. When numbers are absent, give formulas and the measurements required.
