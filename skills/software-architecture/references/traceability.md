# Decision ledger and traceability

Maintain machine-readable IDs across the same project. Never mark proposed designs as deployed facts. Link any costly / irreversible choice to evidence and a revisit trigger. A decision becomes `Accepted` only upon user approval or explicitly reported existing policy.

## Minimum traceability matrix

| Requirement ID | Text/source | Priority | Architecture choice | ADR | Deliverable / code reference | Verification | Status |
|---|---|---|---|---|---|---|---|
| FR-001 | User can sign in (user) | P0 | External OIDC | ADR-001 | auth design, /auth route (proposed) | Auth integration test (planned) | proposed |

Add `NFR-*` for latency, availability, residency, recovery and cost. Note `ASM-*` assumptions and their impact if false. An unverified assumption is not a requirement. Never represent example paths as observed repo paths.

## ADR template

```
# ADR-001: Choice name
Status: Proposed | Accepted | Superseded
Date: YYYY-MM-DD (only when known)
Related: FR-001, NFR-002, ASM-003
Evidence: user requirement / repository path and line / verified external reference / none
Context: why now, what constraints
Decision: precise scope
Alternatives: at least one simpler viable option
Consequences: benefits; costs/risks; failure modes
Validation: what to test/measure
Revisit: measurable change that triggers review
Owner: only if known
```

## Persistent handoff

When the user needs persistence, offer exported text/JSON, ADR files in a repo (only after approved write), or use `workbench/index.html` locally. Do not assume a chat session or `localStorage` is a shared team decision repository. On subsequent interactions import or read the actual ledger rather than guessing prior commitments.
