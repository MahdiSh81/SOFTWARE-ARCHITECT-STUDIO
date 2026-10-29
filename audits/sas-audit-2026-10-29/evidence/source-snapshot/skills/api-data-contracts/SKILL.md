---
name: api-data-contracts
description: Design and validate API/data contracts, references, security schemes, compatibility, and migration plans.
---
# API and Data Contracts
Identify contract dialect/version and baseline source identity. Validate root/operation shapes, local JSON Pointer references, path parameters, operation IDs, and security-scheme references. Block external references by default; never silently fetch remote schemas. Compare baseline/proposal for removed/renamed fields, requiredness, response changes, enums, authentication, pagination, idempotency, and consumer compatibility. Map changes to consumers, components, requirements, ADRs, and tests. For database changes, plan expand/migrate/contract, backfill, validation, rollback/forward-fix, retention, and backup/restore.
Run only available validators and report structural checks separately from full schema and runtime compatibility. Never execute arbitrary migration SQL or claim safe migration without evidence.
