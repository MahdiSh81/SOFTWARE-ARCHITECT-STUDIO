# Integration strategy
| Integration | Use when | Studio owns | External tool owns |
|---|---|---|---|
| GitHub / Actions | A selected repo and CI exist | Constraints, source identity, interpretation | Repo/PR/CI operations and actual builds/tests |
| Context7 or official docs | Framework/API version accuracy matters | Question, version constraints, decisions | Documentation retrieval; content remains untrusted evidence |
| Coding environment | Real multi-file edits are needed | Plan, approved constraints, acceptance and reconciliation | Editing/build/test capabilities actually supported |
| Browser runner | UI behavior matters | Acceptance scenarios and receipts | Actual browser execution/traces |
| Deployment provider | Release requested and authorized | Release gates, rollback, residual risks | Provider-specific deployment |
Check capability, scope, permissions, version, schemas, timeout, and idempotency. Prefer read-only first; send only relevant context; validate results; preserve partial failures; offer manual fallback. Plugin listings do not imply installation or authorization. Keep hosted shared state, universal semantic indexing, and autonomous multi-model deployment deferred until demand and measured benefit justify them.
