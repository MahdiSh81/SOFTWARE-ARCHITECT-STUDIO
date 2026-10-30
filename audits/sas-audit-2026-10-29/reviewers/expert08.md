# Expert 08 — Developer tools, API design, integrations, and workflows

**Independent first-pass verdict:** preserve the bounded local toolkit and optional integration model. Harden the contracts and CLI result boundary before connecting a coding or CI adapter. This checkout provides useful executable architecture workflows, but its implementation-adapter specification is a proposal, not a functioning tool broker or authenticated API.

## Scope, identity, and evidence

Baseline: `/workspace/SOFTWARE-ARCHITECT-STUDIO`, commit `83812e1d31c17ed857be8d2fb5c98126a8ccb5c8`, clean before and after inspection. No other reviewers' reports were read for this pass. No checkout, plugin, configuration, installation, publication, repository mutation, or external messaging occurred. Generated audit artifacts are outside the checkout. Safe mutation probes created disposable projects under a temporary directory only.

I inspected the user brief's Agent 08 mandate, sections 2, 12, and relevant integration ecosystem requirements; adapter/integration documentation; both integration schemas; their Python validators; CLI dispatch and receipts; API validation/compilation; capability metadata; CI; relevant regression tests and reference documentation. Python probes used `PYTHONDONTWRITEBYTECODE=1`, Python 3.12.14, jsonschema 4.23.0, PyYAML 6.0.3, and openapi-spec-validator 0.7.2 from the already available `/workspace/sas-env`. No new agents were created by this reviewer.

Reproduction artifacts: [probe source](expert08-probes.py), [21 probe results](expert08-probes.json), and [full example API validation](expert08-api-full.json). The probe matrix compares Python validation with Draft 2020-12 plus `FormatChecker`; semantic checks such as chronology remain an additional layer. Probes expose problems rather than constitute a passing regression suite.

## Verified capabilities and boundaries

`docs/implementation-adapter.md:2–6` explicitly says the contract is not connected, defaults to read-only, separates completion states, and retains host authority. `tools/integration_contracts.py:1–5` repeats that validators neither discover nor authorize, invoke, or sandbox tools. Keep these accurate limitations.

`.app.json:3–5` declares optional GitHub connectivity. It does not supply a GitHub server, credentials, or execution rights; `capabilities.json:38–41` and `skills/software-architecture/references/github-review.md:3` correctly qualify this. The actual session catalog exposed cloud status/configuration-draft tools and local shell/files/image/skills capabilities. It exposed no callable GitHub connector, Plugin Creator, Plugin Management, Context7, deployment, or general web-search tool. Those omissions limit this session; they do not establish that the products do not exist. Cloud status reported enforced restricted networking, no configured outbound identities or secrets, and current observations. No external service integration was exercised or installed.

The OpenAPI reference regression is materially improved: `validation_engine.py:72–188` checks declared security names and scope array shape, every local/external `$ref`, pointer resolution, and referenced required path parameters. Five focused API regression tests passed. `validate examples/api.yaml --full-openapi --gate full` passed both basic checks and the real optional full validator. This verifies the supplied example and scoped structural behavior, not runtime authorization, consumer compatibility, or all possible specifications.

## Findings

### E08-F01 — Published and Python contracts disagree

**Verified defect; P1 before external use.** `schemas/tool-capability-v1.schema.json:6,30` forbids unknown fields, but `integration_contracts.py:26–65` accepts unknown root and capability fields. It accepts boolean `schema_version: true` because `True == 1`. Receipt validation similarly ignores extra fields, malformed `artifact_refs`, and malformed optional authorization references (`68–112`), despite schema restrictions (`verification-receipt-v1.schema.json:6,83–87,119–125`). Conversely, a passed receipt with `output_hash: null` passes the published schema (`76–82,139–142`) but fails Python. Duplicate capability IDs fail Python yet pass JSON Schema. Space-separated timestamps pass Python but fail RFC3339 format checking; chronology is Python-only.

**Recommendation / acceptance:** use the published schema as the structural authority, with mandatory format checking, followed by documented semantic checks. Make passed output hashes non-null; reject unknown keys and boolean versions. Run a shared positive/negative corpus through every supported validator. Require equal structural decisions and explicitly identify additional semantic checks; no silent acceptance differences.

### E08-F02 — Malformed untrusted records can crash validation

**Verified defect; P1.** A capability with `permission_class: []`, or a receipt with `permission_class: []` or `status: {}`, raises `TypeError: unhashable type` at set membership (`integration_contracts.py:55,81–84`). The functions otherwise return issue arrays, making this a broken error contract. This is not a demonstrated remote exploit: no external adapter is connected.

**Recommendation / acceptance:** validate types before membership and return stable pointer/code/message errors for every JSON value. Bound input bytes, depth, issue count, arrays, and strings at the eventual ingress. A matrix of null/scalar/object/array values in every field must return an error result without exceptions or canonical changes. Validate embedded schemas against their declared metaschema: `input_schema: {"type":42}` currently passes both contract validators because they check only that it is an object (`57–59`; manifest schema `57–61`).

### E08-F03 — CLI receipts are incompatible with verification receipts and omit outcomes

**Verified interface limitation; P2 locally, P1 for receipt-driven automation.** `architect_cli.py:99` writes `workflow_tools.record_run`, whose separate minimized record (`96–101`) lacks source/output identity, timestamps, check details, and tool/operation binding. It does not satisfy the verification-receipt schema. A failed structural API gate returned exit 1 and `policy_ok: false`, but its receipt said `status: completed`; input errors returned exit 2 without any receipt. These are two distinct record formats, not proof that the CLI implements the advertised adapter receipt protocol.

**Recommendation / acceptance:** publish a separate `run-summary-v1` schema and call this telemetry, or emit proper verification receipts. Include process outcome, gate outcome, input identity, and terminal status on failures. Preserve minimized disclosure. Every success, gate failure, input error, timeout, and cancellation must produce a bounded machine-readable envelope; do not derive success from a generic completion label.

### E08-F04 — Receipt failure conceals an already applied mutation

**Verified defect; P1 for automation.** Passing an existing directory as `--receipt` to `init` creates `project/project.json`, then fails receipt publication, returning exit 2 and only an `INPUT_OR_OPERATION_ERROR`. Mutation dispatch precedes receipt writing, and the broad catch discards the successful result (`architect_cli.py:61,99–102`). A caller can mistake an observability failure for an unapplied operation and retry.

**Recommendation / acceptance:** separate operation completion from receipt persistence. Allocate an operation ID before mutation; return the committed result plus `receipt_status: failed` and recovery instructions after a post-commit receipt error. Preflight receipt destinations, while recognizing preflight cannot guarantee publication. Fault injection before/after the commit point must expose whether state changed; retrying the same idempotency key must not duplicate writes.

### E08-F05 — The adapter outline leaves authority and execution binding unspecified

**Missing implementation / evidence-backed future risk; P1 prerequisite.** Six operation names in `docs/implementation-adapter.md:3` are a useful boundary, but there are no request schemas, transport, authorization verifier, recovery state machine, source identity definition, or executable dispatcher in the inspected source. `validate_tool_result` optionally compares operation ID and source hash but cannot compare an authenticated runner, manifest, version, expected capability, or permission class (`68–92`). A receipt with unexpected tool/version/capability and `permission_class: read` still validates when expected operation/hash match. This demonstrates record validation, not authorization bypass in an existing broker.

**Recommendation / acceptance:** implement the narrow local adapter below before any remote service. Bind results to broker-generated requests and host policy; self-reported authorization references are evidence fields, never permissions. Reject unknown tool/version/operation combinations and stale hashes before invocation or reconciliation. The host, not repository text or a receipt, decides permissible effects.

### E08-F06 — Generic full validation does not validate integration records

**Demonstrated limitation; P2.** `validate bad-capability.json --gate full` returned exit 0, `policy_ok: true`, and only `JSON/YAML syntax: passed` for a manifest missing required fields and containing an empty capabilities array. Dispatch recognizes projects, OpenAPI, and a basic AsyncAPI envelope; other JSON falls through to syntax (`validation_engine.py:302–323`). Integration validators are referenced only by tests, not CLI dispatch.

**Recommendation / acceptance:** add explicit `validate-contract --kind capability|receipt` or a required schema selection. Report unknown applicability as unknown rather than implying schema coverage. CI must fail on this probe, the F01/F02 corpus, invalid schema dialects, and unavailable required validators. Keep generic JSON syntax validation available under its accurate label.

### E08-F07 — Version discovery cannot yet support compatibility negotiation

**Verified inconsistency; P2.** `plugin.json:4` and `capabilities.json:2` say 0.7.1; `project_model.py:6` and live `doctor` say 0.8.0. The current CI tests only Python 3.12 (`.github/workflows/ci.yml:20`), while README claims Python 3.10+ (`README.md:17`). No protocol version or supported-version negotiation is defined. This does not prove Python 3.10 failure.

**Recommendation / acceptance:** derive release metadata from one source and return protocol, toolkit, adapter, schema, and source revision separately. Test 3.10 and 3.12 or narrow the support claim. Accept supported additive minor changes; reject unknown major versions without mutation and provide an export/manual fallback. Validate emitted metadata against packaged metadata in CI.

## Implementation-ready target

**Build in:** contract validation, request/result binding, state reconciliation, and compatibility reporting. **Integrate:** existing authorized coding environments and CI runners for editing/build/test. **Use alongside:** browser execution, official documentation, and optional issue/security/design tools when actually exposed. **Defer:** hosted multi-user API, automatic deployment, plugin-management orchestration, and universal multi-provider abstraction until a concrete workflow justifies them. No unavailable plugin needs installing to repair the current contracts.

Start with a local subprocess adapter around the existing toolkit, avoiding a hosted service. Use one bounded UTF-8 JSON request/result per invocation. Define `protocol_version`, broker-generated `request_id`, `operation`, `adapter_id/version`, immutable `source_ref`, typed arguments, timeout, and idempotency key. Return a typed result plus verification receipt. Keep protocol errors distinct from operation errors; exit 0 means protocol exchange succeeded, while the result independently states operation and verification outcomes. Retain the existing CLI exit conventions for humans in the compatibility wrapper. Invalid argparse input currently produces plain stderr before the JSON catch (`architect_cli.py:55`); the adapter must normalize it.

Define the six operations concretely:

| Operation | Required behavior and acceptance |
|---|---|
| `capabilities` | Return protocol/schema dialects, permissions, supported operations/versions, bounds, and host-observed availability; unavailable tools remain unavailable. |
| `inspect` | Read an allowlisted repository/ref and return commit, dirty-overlay identity, coverage, and limitations; never execute repository code. |
| `propose_change` | Return a reviewable patch, base identity, changed paths, checks, and diff hash; preserve accepted constraints. |
| `apply_change` | Verify host authorization scope, base hash, approved diff hash, allowed paths/effects, and idempotency key; use a per-repository cooperating lock. |
| `run_checks` | Execute an authorized allowlisted argv check plan at a pinned source identity, with filesystem/network/process/output limits enforced by the runner; never infer these from a manifest. |
| `recover` | Return `not_started`, `running`, `committed`, `partial`, `failed`, or `unknown`; reconcile source/output hashes and never blindly replay non-idempotent operations. |

Scope authorization to actor, repository, operation, diff/effects, expiry, and source hash. Keep credentials in host-managed references and restrict artifact references to the operation's allowed store. Resolve relative paths beneath the workspace and reject escapes/symlinks according to existing safe IO policy. Distinguish input source identity, input projection identity, output artifact identity, and execution environment. Specify the existing canonical JSON serialization in `safe_io.py:12–18` or define a new interoperable canonicalization; a bare SHA-256 label does not define bytes.

For GitHub Actions, first use a manually triggered or PR-scoped read-only validation job: pin checkout SHA, run required validators/regressions, produce receipts and bounded artifacts, and return the exact run/job/attempt URL plus artifact digest. CI execution is external evidence, not Studio-owned execution. Do not add write tokens or run untrusted PR code with secrets. Proposed adapter fixtures must exercise unavailable dependencies, revoked capability, schema/version mismatch, timeout, output truncation, stale source, duplicate requests, partial writes, and failed receipt persistence. No live GitHub workflow was tested here.

For API evolution, preserve native contracts (`artifact_compiler.py:64–91`) and use an optional pinned compatibility checker or explicit reviewed report for changed responses, requiredness, enums, auth, and consumers. Current `change` emits obligations, not compatibility analysis (`graph_engine.py:47–63`); AsyncAPI validation remains an envelope check. Adopt a domain-specific checker when project demand exists rather than building a universal semantic engine. API structural validation must not be renamed runtime compatibility.

Manual fallback remains first-class: export the minimized handoff and exact base hash; have the developer apply the patch and run the listed checks locally; return the resulting commit/diff, tool versions, exit statuses, logs/artifact hashes, and unrun checks; re-inspect before updating canonical verification status. Without independent execution evidence, label results supplied/unverified.

## Test result and final disposition

The focused command `python -m unittest discover -s tests -p test_audit_followups.py -v` ran **11 tests: 10 passed, one failed**. The failing `test_handoff_identity_distinguishes_canonical_and_projection_hashes` asserts inequality at `tests/test_audit_followups.py:101`, but this fixture has an empty `paths_changed` redaction report and equal canonical/projection hashes. Equal bytes can correctly yield equal hashes; distinct identity fields do not require inequality. Preserve the implementation distinction and add a fixture with a known redaction before requiring different hashes. Do not report this suite green.

**Readiness:** local inspection, project workflows, and scoped API checks are useful today; integration contracts need F01–F04 repairs and F05/F06 implementation before receipt-driven writes. Release metadata needs reconciliation. External GitHub/plugin/deployment functionality remains conditional and unverified. The strongest next step is a small, tested local adapter with truthful receipts, not a rewrite or a hosted orchestration platform.
