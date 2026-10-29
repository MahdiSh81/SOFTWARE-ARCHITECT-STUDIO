# Deliverable package contracts

Emit only scope-relevant artifacts and prefer consistency to volume. Suggested repository structure:

```
architecture/
  README.md
  requirements.md
  architecture.md
  context.mmd
  containers.mmd
  sequence-critical.mmd
  data-model.md
  api.yaml
  security.md
  reliability.md
  capacity.json
  risk-register.md
  traceability.md
  implementation-plan.md
  adrs/ADR-001.md
```

Every artifact must label actual/observed vs proposed. IDs referenced in ADRs and traceability must resolve to a real requirement or assumption; `ADR-*` referenced must have a file. Keep naming consistent between diagram nodes, API owners and deployment units.

`requirements.md`: numbered user requirements with source, priority, measurable acceptance criteria and change status.
`architecture.md`: recommendation, rationale, C4 layers, trust and dependency boundaries, critical flows, data consistency, alternatives, migration triggers.
`api.yaml`: syntactically valid OpenAPI 3.x candidate; declare auth schemes, error responses, idempotency where needed and contract version policy. Validate with a parser/tool when present and otherwise mark unvalidated. Do not claim backend routes exist.
`security.md`: assets, threats, trust boundaries, mitigations, unmitigated risks, tests. Not compliance certification.
`capacity.json`: explicit inputs for CLI; any cost values are `assumed` unless tied to verifiable quote metadata.
`risk-register.md`: risk status, likelihood/impact, severity, mitigation, validation and owner if known.
`implementation-plan.md`: phases, dependencies, operational acceptance gates, rollback criteria and measurable exit checks.

Before export, run documented validators and display validation outcomes and limitations. A proposed architecture does not prove technical implementation.
