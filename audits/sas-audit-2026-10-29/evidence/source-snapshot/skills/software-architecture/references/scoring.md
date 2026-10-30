# Evidence-aware architecture scorecard

Assess six dimensions, each 0–4, with evidence and confidence. Do not use an aggregate if coverage is inadequate. Defaults: security weight 25; reliability 20; scalability/performance 15; maintainability 15; observability 15; cost/efficiency 10. Users may set different explicit weights (must sum to 100); report weights used. Do not award `4` merely because the architecture proposes controls: the score must reflect verified or user-supplied implementation evidence. Use `null`/`N/E` (not evaluated) if evidence insufficient; exclude its weight from the denominator and explicitly show assessed weight coverage.

| Score | Meaning |
|---|---|
| 0 | Evidence of serious gap, broken required control or non-functional system |
| 1 | Weak or ad hoc practice, significant documented deficiency |
| 2 | Partially implemented with material known gaps |
| 3 | Implemented and reasonably exercised, residual limitations recorded |
| 4 | Implemented, measured and validated against the system's stated objective |
| N/E | Not enough evidence to evaluate |

Dimension prompts:
- Security: trust boundaries, authn/authz on server, secret handling, tenant isolation, audit, threat tests.
- Reliability: SLO/SLI, restore drills, idempotency, error budgets, dependencies and graceful degradation.
- Scalability: measured hot paths, load tests, capacity plan, caching/backpressure, data query behavior.
- Maintainability: module boundaries, ownership, ADR currency, tests, migration path, CI reproducibility.
- Observability: structured logs, metrics, tracing, alert thresholds, actionable runbooks and ownership.
- Cost: reconciled spend, forecasting, rightsizing, quotas, peak margin, and financial risks.

Compute `weighted_percent = 100 * sum(weight_i * score_i / 4) / sum(weight_i for evaluated)`; `evidence_coverage = sum(weight_i for evaluated) / 100`. If coverage < 60%, show individual dimension results and mark aggregate as **provisional** even if computed. Avoid equating high score with compliance/security certification.

Audit finding format: `ID | Dimension | Priority (Critical/High/Medium/Low) | observed evidence | issue | impact | recommendation | effort | validation | confidence`. Qualify scenario-based risks as risks, not existing confirmed defects. Prefer priorities that account for exploitability/likelihood, blast radius, affected users and recovery, not scoring alone.
