---
name: implementation-planning-and-change
description: Convert an approved requirement or defect into a minimal reviewable code-change plan using authorized tools when available.
---
# Implementation Planning and Change
Establish repository/ref, source identity, dirty state, accepted requirements/ADRs, available tool capabilities, and permissions. If an actual editor or runner is unavailable, provide a plan or patch proposal and mark execution blocked.
1. Convert the request into acceptance criteria and affected files/contracts.
2. Inspect relevant source and tests; define a regression test before implementation.
3. Produce a minimal plan/diff; flag generated and unrelated modifications.
4. Validate scope; obtain required authorization before consequential writes/deployments.
5. Apply only through an authorized tool with expected-hash preconditions where supported.
6. Run targeted and relevant regression/build/security checks through actual runners.
7. Record source identity, changed files, hashes, versions, checks run/not run, and residual risks.
8. Reconcile code and architecture artifacts without silently overwriting accepted decisions.
Never claim a patch, build, test, or deployment happened without a real tool result. Do not blindly retry non-idempotent operations.
