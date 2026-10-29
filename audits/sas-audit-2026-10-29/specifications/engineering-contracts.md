# Proposed engineering contracts — design only

These interfaces and algorithms are proposals, not installed features or provider API definitions. No implementation changes are authorized by this audit. Detailed finding IDs and initiative mapping are in the consolidated register. Preserve project schema v2 compatibility unless an explicitly versioned migration is necessary. Keep a local modular monolith; add a thin capability-checked host boundary rather than a new orchestration service.

## SPEC-01 — Representations, projections and coherent exports

Problem: canonical intent, redacted compiler context and allowlisted exported project are different representations. A hash of one must not identify another. Exported interfaces can retain security requirements after their native security schemes are omitted.

Proposed pipeline:

```text
load canonical -> validate draft -> canonical identity
              -> disclosure policy -> compiler context identity
              -> export policy -> exported project identity
              -> validate exported project -> compile artifacts
              -> verify artifact identities -> immutable generation -> pointer
```

For `hash_semantics_version: 2`, expose `canonical_object_sha256`, `compiler_context_sha256`, `exported_project_sha256`, `exported_project_bytes_sha256`, `source_revision`, `generator_version`, `disclosure_profile`, `redacted_paths`, `omitted_paths` and `artifact_hashes`. Define object hashes using the existing canonical serializer, byte hashes over the exact emitted UTF-8 bytes. Retain legacy fields as documented aliases only; no ambiguous reassignment without version marking. Equal hashes are valid when representations are equal. Do not test mandatory inequality; test equality to the specified representation and changed-input sensitivity.

The exported-project allowlist must include every supported normative contract needed to reload/regenerate it, including `api_contract` and referenced security schemes. Keep opaque extensions excluded from shareable export by policy, but disclose omission paths without including private values. Before publish, call the same semantic validation on exported project and recompile in memory in a conformance fixture. Native schemas/interfaces with conflicting behavior must produce a source-qualified blocker, not a passing correspondence claim. For native-only operations, require an explicit coverage/ownership decision rather than duplicate placeholder interfaces.

Migration: new generation metadata is additive; old generation readers remain supported with an explicit legacy identity interpretation. Do not rewrite old immutable generations. Rollback: keep prior pointer/generation and old parser; never recover by overwriting human-modified convenience projections.

Acceptance: rich fixture default export loads and regenerates successfully; original canonical unchanged; no secret markers/opaque fields in public output; all referenced schemes preserved; manifest hashes match actual bytes; equal unchanged representations accepted; conflicting response schema/security/body/parameters rejected; `--dry-run` writes nothing.

## SPEC-02 — One validation policy, separate evidence and readiness

Normalize JSON and YAML to a single typed document path before structural, OpenAPI, project and correspondence checks. Enforce duplicate-key rejection and finite/depth/size limits in both parsers. `yaml.safe_load` alone does not reject duplicate mapping keys. Reject ambiguous input rather than validating only its last value. Keep remote `$ref` disabled by default and resolve local pointers with explicit invalid-escape/missing-target diagnostics. For non-OAuth schemes, reject nonempty scope arrays; semantic checks supplement the installed schema library.

Proposed check record:

```json
{
  "check_id": "contract.correspondence",
  "status": "failed",
  "subject": {"source_hash": "<sha256>", "artifact_hash": "<sha256>"},
  "method": {"tool": "studio", "version": "<version>"},
  "applicable": true,
  "evidence_refs": ["<bounded artifact/log reference>"],
  "diagnostics": [{"code": "RESPONSE_SCHEMA_MISMATCH", "pointer": "/paths/~1items/get/responses/200"}]
}
```

Terminal states: passed, failed, skipped, blocked, timed_out, partial, unknown, not_applicable. A required check must be passed; waived-with-reason is recorded separately and never recoded as pass. Preserve legacy `ok` semantics only with clear documentation; consumers use `policy_ok` and required-check coverage, not `ok` alone. Requiring full rendering while mmdc is absent must stay nonzero even when structural checks pass.

For Mermaid, exit zero is necessary but insufficient: require a new regular nonempty output within bounds, parse the expected SVG structure, reject unexpected script/external references under configured policy, and hash actual output. This confirms artifact production, not correctness of architecture or browser sandboxing. Keep stderr and timeout evidence independent of heuristic warnings.

Readiness dimensions: draft validity, specification completeness, contract correspondence, implementation coverage, build, tests, runtime, review, freshness and release authorization. Empty projects may be valid drafts; they cannot satisfy an application implementation gate. For each applicable requirement require explicit implementation/task/verification coverage, or an approved not-applicable rationale. `review-ready` needs a precisely named scope: document review readiness is not executable application readiness. Do not impose application gates on a quick architecture question.

Acceptance: JSON/YAML parity on same inputs; duplicate keys rejected; dangling local refs, undeclared schemes and invalid scopes fail; mismatched contract in either extension fails; empty renderer output fails; missing renderer blocks required render; zero-test run cannot pass application verification; intentionally incomplete project remains a valid draft with visible blockers.

## SPEC-03 — Safe workbench drafts and cross-surface conformance

Separate `canonicalProject`, `editorDraft`, `draftOrigin` and `uiPreferences`. An editor draft owns the collection name, stable record ID and base revision/hash. Changing depth/audience/navigation cannot reset draft values. Switching collections must either retain a distinct draft per collection or visibly resolve pending changes; never carry record JSON into a new type with a cleared identity. New/sample/import/restore actions must account for every user-populated canonical field and unsaved editor draft, preserving a recoverable copy before replacement. Avoid confirmation for harmless navigation: persistence is preferable to repeated prompts.

Proposed editor event contract: `{kind, base_project_hash, collection, record_id, draft_value}`. On apply, validate both transport and target record schema; compare origin against current canonical identity; refuse type/identity mismatch; preserve Accepted-record invariants; atomically persist candidate; retain current draft if persistence fails. Rollback is local undo/recovery export, with original input bytes retained.

Use one conformance fixture corpus for Python semantic validator, optional JSON Schema and browser validator: required arrays, known optional reference fields, duplicate global IDs, referenced IDs, finite numbers, size/depth, version, Accepted edits, supersession and unknown opaque extensions. Generated validator tables are possible, but test observable parity rather than mirroring implementation. Add real-browser tests for depth changes while typing, collection-switch edits, sample/new protection, storage quota failure, reload recovery and two-tab expected-hash conflicts. Include keyboard, narrow viewport, RTL and announcement checks; screen-reader certification remains a separate manual assessment.

Acceptance: reported draft-loss and cross-collection reproductions fail on baseline and pass after repair; no data loss after quota/import/write failures; canonical output matches CLI; unknown extensions survive private roundtrip; unsupported input retains original recoverable bytes.

## SPEC-04 — Bounded state writes with recoverable envelopes

Input-size permission and envelope-size permission must agree. A project accepted at the limit must remain committable with its recovery metadata. Define separate `MAX_PROJECT_BYTES`, `MAX_JOURNAL_BYTES` and `MAX_BACKUP_BYTES` derived from the actual encoding overhead, or lower the public accepted maximum with a visible preflight diagnostic. Avoid serializing two full project copies where immutable revision references can preserve equivalent recovery invariants, but do not remove crash recovery to fit a bound.

Transaction preconditions: canonical project ID, expected hash, source revision and selected operation ID; keep cooperating lock, no-follow traversal and same-directory atomic replacement. A proposed project from a different project ID must be rejected unless an explicit import/fork operation is chosen. Validate journals as untrusted data before any write; ensure current committed state matches journal before history reconstruction. Test crash phases before/after canonical replace, history no-clobber, partial projection, stale locks, bounded filesystem state and size boundary. Never automatically delete an unowned lock.

Acceptance: largest advertised project commits/snapshots/recovers; one byte over limit fails before mutation; no-clobber histories and exact expected-hash checks preserved; cross-project replacement rejected; interruption leaves either prior state or recoverable committed state. Rollback uses old reader and original snapshots; any new journal format requires explicit versioning and legacy recovery fixtures.

Lifecycle extension: define `supersedes`/`superseded_by` as validated references with explicit reciprocal and acyclic rules. Decide whether branching is supported; until modeled explicitly, reject a second successor of the same predecessor rather than cloning its stale successor link. A Proposed successor records predecessor provenance separately and does not inherit the predecessor's approval as its own. Preserve unchanged imported Accepted facts and unknown approval origins; never invent an approver. Python/browser conformance must cover valid multi-generation chains, repeated supersession, dangling/self/cyclic links, malformed provenance and interrupted state publication. State clearly when the old Accepted decision is retired: on proposal creation or successor acceptance; that product decision remains open for implementation review.

## SPEC-05 — Evidence completeness and impact honesty

Extend scan evidence with adapter identity/version and per-language/path states: scanned, parsed, unsupported, parse_failed, excluded, unreadable, stopped. Cache parser diagnostics and omission counters with declarations, not only declarations. Invalid/incompatible cache metadata becomes a miss; cache must never upgrade partial evidence to complete. Limit every descriptor collection and report truncation at the exact limit. A bounded walk cannot claim unseen totals.

Fitness predicate: a matching declaration proves a violation in scope; absence proves only `satisfied-in-supported-scope` when all relevant selected files were parsed by a suitable adapter. Any unsupported/failed relevant file gives unknown/partial, even when file traversal completed. Exclude intentionally non-source fixtures by explicit configured scope, not by silently pretending they were analyzed.

For change analysis, seed impacts from changed/added/removed records in all supported collections, not requirements alone. Emit typed witness paths and reached record kinds including verifications; record unsupported edge semantics. An ADR/interface/data change can affect code/tests even if requirements did not change. Incremental analysis compares equivalent scope/adapter/inputs, and old line references are never used as current after content changes.

Acceptance: cold/warm cache outputs preserve diagnostics and coverage; Go/no-adapter and Python parse-failed fixtures cannot pass import fitness; descriptors beyond limit report truncation; interface-only and ADR-only changes have appropriate witnesses or explicit unknown; missing links remain unknown. Do not build a universal semantic graph before language-specific fixtures demonstrate benefit.

## SPEC-06 — Capability adapter and receipt reconciliation

Proposed local protocol, following existing docs rather than pretending a connector exists:

```text
capabilities() -> manifest
inspect(source_ref, scope) -> source_snapshot
propose_change(change_plan, source_snapshot) -> diff_artifact
apply_change(diff_artifact, expected_source_identity, host_authorization) -> operation_receipt
run_checks(check_plan, expected_source_identity) -> check_receipt
recover(operation_id) -> observed_state_and_receipt
```

Studio owns intent and accepted decisions; the host owns enforcement, editor and process execution; source code is authoritative about implementation; providers own remote objects; receipts are evidence to verify. Manifests declare operation IDs, tool/version, input/output schema, read/write/deploy scope, timeout, idempotency and capabilities. Verify actual tool availability each session. Proposed operation names are not actual plugin tool names.

Source identity includes repository commit plus dirty-file hashes and normalized path scope; commit alone is insufficient with uncommitted edits. On apply mismatch return `conflict` before mutation. Partial writes return observed changed paths and recovery hint, never a fake atomic success. For non-idempotent operations, query operation state before retry. A receipt must match tool/capability/operation/source and existing authorized scope; reject passed checks with missing output identity, omitted required checks, contradictory errors or invalid chronology. Do not accept `authorization_reference` text as actual permission: host authorization remains decisive. Schema and Python validator must agree using a shared adversarial corpus and explicit datetime format enforcement.

Only reconcile canonical verification status after checking artifact existence/hashes, exit code and actual test count/required scenarios. A formatter pass cannot mark runtime verified. Failed tests preserve failed status; dependency/setup errors are classified separately. Export a manual check plan if no runner is present. Never reclassify an unavailable external tool as a skill capability.

Results bind both observed starting and ending source identity, request/check-plan identity, selected runner/capability/version and observed effects. Running repository checks can write files or reach networks; a self-reported `read` label is not authorization for those effects. Attempted/observed consequential effects require a host-resolved authorization reference even on failed/partial operations. Unknown state stays unknown. Minimized run telemetry and verification receipts have distinct versioned schemas; include gate/exit/status counts and shared operation correlation in summaries without treating summaries as proof of verification.

Acceptance: minimal disposable service change modifies at least two source files and tests, builds and passes behavior; stale source rejected; injected repo instruction cannot gain deploy scope; timeout/duplicate/partial write preserved; fabricated receipt rejected; authorized no-change checks remain idempotent. No deployment test runs against production during initial adoption.

## SPEC-07 — Release, dependency and error hygiene

Choose one release identity source and generate/check all package/toolkit/workbench/capability versions. A CI job must execute a real tracked integrity checker; deterministic inventory excludes its own recursive hash and includes every intended packaged path. Check expected mismatches before regenerating after an approved change; never overwrite manifest hashes merely to conceal unexplained edits. A generated manifest is a consistency record, not a signature or provenance attestation.

Keep optional validation dependencies isolated. Establish whether requirements-validation.lock is installable on the target platform before making it the reproduction command; record Python/platform and resolved transitive versions. Pin browser tooling and use an actual lockfile in a future authorized change; separate browser engine version from Playwright version. Consider commit-pinning GitHub Actions and vulnerability/license scanning under a defined update policy, without claiming current CVE cleanliness.

Normalize domain failures (`sqlite3.Error` included) into bounded typed CLI diagnostics while preserving nonzero exit. Never expose arbitrary tracebacks as a substitute for input diagnosis. Test duplicate generated table names and invalid constraints in ephemeral SQLite only; never execute arbitrary supplied migration SQL.

Acceptance: fresh checkout executes every CI command; version/inventory checks fail intentional stale changes; lock reproduction has consistent package versions; missing/failed tests remain nonzero; invalid SQLite fixture yields typed JSON and no traceback. Rollback keeps previous published artifact/configuration; publication requires separate user authority.

## SPEC-08 — Auxiliary outputs, authentication and instruction boundaries

Auxiliary writers, including `--receipt`, must create new owned outputs exclusively. Preflight destination collisions before a primary mutating command; reject input/source/project/journal/history/handoff collisions and aliases. Do not infer permission to overwrite from selecting an output path. If the primary operation committed before an auxiliary failure, report both facts, not a single ambiguous failure. Explicit replacement must require a matching owned artifact identity and documented scope. Acceptance includes existing project/source/unrelated JSON/hardlink/symlink destinations with unchanged original bytes, plus successful fresh receipt creation.

Represent authentication intent as `unspecified`, `public` with reason, or `required` with scheme references/scopes. Supplied native OpenAPI remains authoritative for its concrete contract; compare it with declared intent. Prose such as “BearerAuth required” cannot disappear or be treated as an implemented policy. Unsupported/prose-only intent blocks a claimed fully specified protected interface until resolved. Explicit `security: []` is a public override, not evidence of protection. Acceptance covers inherited/overridden schemes, public/required contradiction, declared schemes, non-OAuth scope rules and preserved native protected contracts. `security.md` reports resolved intent and conflicts rather than “None documented” simply because no field is missing.

Preserve imported Accepted decisions as canonical facts with approval provenance. Ordinary handoff should put them in quoted/structured architecture-constraints data, not automatically active `AGENTS.md`. A separate explicitly scoped native-instruction export may show exact selected content and source; receiving host authority remains decisive. Do not require users to reapprove unchanged Accepted architecture facts merely to preserve them. Acceptance uses a hostile multiline imported record: content/provenance retained as data, no automatic instruction activation, no extension of filesystem/network/message/deploy rights, no forged passed checks. The present audit reproduced dangerous-file generation, not downstream model obedience.

Treat opt-in caches as performance artifacts with an explicit trust owner. A source fingerprint cannot authenticate cache edges. Release/security fitness gates should re-extract without untrusted caches, or prove trusted cache provenance through the host; a hash stored beside editable cache content alone is insufficient. Fitness must match evidence edge kinds, not confuse package/CI associations with parsed imports. Cold/warm parity includes parser failures, unsupported languages and truncation. A forged empty-edge entry cannot turn a real violation into green.

Default diagnostics should include bounded error code/location and safe summary. Raw validator exceptions can echo confidential input: retain them only in an explicitly private local debug artifact with clear access/retention, never automatically in shared reports. Do not promise complete redaction from a regex. Browser test servers should bind loopback and serve only required fixtures/workbench assets; no claim of an actual network exposure follows from configuration alone. Acceptance includes synthetic secret markers absent from default logs and private-debug content appropriately scoped, plus repository metadata not retrievable from the test server.

Status migration must preserve existing distinct `tool_error`, `not_run_due_to_budget` and other terminal reasons as typed causes or explicit states; do not collapse them into pass or generic skipped. Every proposed consolidated enum needs a versioned compatibility mapping and old/new receipt fixtures.
