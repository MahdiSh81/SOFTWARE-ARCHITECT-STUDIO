# Expert 03 — Program creation, code generation, and implementation

Independent first pass, 2026-10-29. Frozen source: `/workspace/SOFTWARE-ARCHITECT-STUDIO`, commit `83812e1d31c17ed857be8d2fb5c98126a8ccb5c8`; clean at start and after testing. No other reviewers' first passes read, no child agents created. No checkout files modified, no installation/configuration/publication/deployment performed. All proposed changes below are specifications, not implementations.

## Verdict

**OBSERVED:** Studio is an architecture/context/contract/handoff toolkit that can materially support program creation. It is not a connected application scaffolder, source-code generator, build runner, debugger, or deployment service. Its source and documentation mostly state that boundary accurately. It should become an architecture-led software creation workflow through a small host implementation adapter and evidence reconciliation, using the actual host editor and runner rather than building another generic IDE or model runtime.

**OBSERVED:** This session exposes `apply_patch`, `exec_command`, filesystem reads, Python, Node, npm, Git, Docker and gh command binaries. Those host tools could support real multi-file implementation when the user authorizes implementation. Binary presence does not establish daemon health, authentication, remote permissions, or successful builds. The audit itself authorizes audit artifacts and safe tests, not implementing a sample application or modifying Studio. Consequently, application-generation quality and model performance remain **UNMEASURED**, not failed. No native Studio MCP coding/build tool was exposed by tool discovery; discovered architecture capability lives in skills plus local scripts. No recommendation to install a coding plugin is needed to use this host's existing editor/shell.

The immediate engineering priorities are: preserve and repair handoff reproducibility; define a distinct implementation-readiness gate; bind real changes/checks to source identity; then prove one small end-to-end implementation workflow before adding framework breadth. A rewrite is unjustified.

## Evidence baseline and test inventory

Repository source paths and line numbers below refer to the frozen commit. The separately installed cloud `software-architecture` skill reports v0.7.2; the inspected repository's `tools/project_model.py:6` and CLI doctor report v0.8.0. These are different artifacts. I read the runtime and software-architecture cloud skills, the Agent 03 brief and idea-to-implementation requirements, all six repository specialist skills, core architecture guidance, adapter/integration docs, compiler/model/revision/validation code, manifests, representative tests and fixtures. Installed skill instructions are not evidence that repository routing code or a connected adapter exists.

Evidence retained at `/workspace/sas-audit-2026-10-29/evidence/expert03/`:

| Actual check | Result | Retained evidence |
|---|---|---|
| CLI `--help`, `doctor` | Executed; no model/repository-execution command. Python 3.12.14, toolkit 0.8.0; PyYAML 6.0.3, jsonschema 4.23.0, openapi-spec-validator 0.7.2; mmdc missing | Initial tool outputs; environment/source identity in `source-identity.json` |
| `python -m unittest discover -s tests -p test_project_workflows.py -v` | **12 passed** | `test_project_workflows.py.log` |
| `python -m unittest discover -s tests -p test_audit_followups.py -v` | **10 passed, 1 failed** | `test_audit_followups.py.log` |
| Scratch idea → manually authored structured plan → `change` → expected-hash `commit` → review-ready dry-run/handoff | Executed successfully, revision 2; 19 named handoff artifacts; **zero application source files or application tests generated** | `exercise.py`, `idea.txt`, `proposed.json`, `01-init.stdout` through `07-handoff.stdout`, `results.json`, `task-tracker/`, `handoff/` |
| Structural handoff validation | Exit 0; `ok:true`, `policy_ok:true`; full OAS/render deliberately not requested | `08-validate.stdout` |
| Full handoff validation with `--render --full-openapi --gate full` | Exit 1; full OAS and project schema passed; renderer skipped because missing; `ok:true`, **`policy_ok:false`** | `09-validate-full.stdout` |
| `data-check` of structured SQLite table | Passed generated `CREATE TABLE` in memory; no app queries, persistence, migration or business behavior checked | `10-data-check.stdout` |
| Empty draft and requirements-only review readiness | Both return `profile_satisfied:true` and `completeness: specified within supported scope` | `02-empty-readiness.stdout`, `11-requirements-only-readiness.stdout` |
| Rich fixture → handoff exported project → handoff again | Second compilation fails: undeclared `session` security scheme | `handoff-roundtrip.json` |
| Passed receipt with `output_hash:null` | Published JSON Schema accepts; Python semantic validator rejects | `results.json`, `12-null-output-receipt` entry |
| Frozen source identity and dirty state | Correct commit; clean | `source-identity.json` |

The repeat executions of the two small test files captured durable logs; their outcomes matched the first run. No network, browser, app build, deployment, live model evaluation or end-user study was attempted. Managed-environment status reported current/enforced restricted networking and no configured secrets/outbound identities. This establishes environment configuration, not remote access or API permission.

## Findings register

### E03-F01 — The implementation bridge is a design contract, not a connected capability

**Type:** verified capability boundary / missing capability relative to the expanded product objective. **Priority:** P1 foundation for program creation; not a defect in the existing architecture-only scope.

**Sources:** `docs/implementation-adapter.md:2-6`; `docs/integrations.md:4-9`; `tools/architect_cli.py:25-54`; `tools/integration_contracts.py:1-4`; `capabilities.json:21-41`; `skills/implementation-planning-and-change/SKILL.md:6-15`.

The adapter specifies `capabilities`, `inspect`, `propose_change`, `apply_change`, `run_checks`, `recover` but implements none of them. The integration module validates manifests/receipts only. CLI `init` creates context/history, not application directories or a package manifest (`tools/revision_store.py:13-22`); `handoff` generates architecture contracts/tasks/docs, not application source (`tools/artifact_compiler.py:48-104`). There is no CLI source-generation/edit/install/build/run/deploy command. The scratch test reached a valid architecture package but no app source. The host model can draft code and host tools can edit/run it; that is conditional host work, not a bundled deterministic Studio function.

**Impact:** An architecture package can accelerate development but does not itself supply runnable software or enforce consistency between application files. Calling this a software creation system without a connected host workflow would overstate capability.

**Recommendation:** Preserve the existing compiler/context boundary. Implement one thin host adapter and expand the current implementation skill, as specified below. Do not add a general-purpose editor, autonomous model server, generic deployment engine or framework factory. Offline fallback returns the plan/patch proposal and `blocked` execution state. **Acceptance:** one authorized multi-file feature and one subsequent defect fix produce actual diffs, checks and source-bound receipts; unavailable editor/runner returns useful blockers without invented output.

### E03-F02 — Review readiness checks fields on present records but cannot establish implementation coverage

**Type:** reproduced scope gap; not a claim that runtime readiness is currently promised. **Priority:** P1 before using the profile to start automated implementation.

**Sources:** `tools/artifact_compiler.py:9-34`; `tools/project_model.py:18-21,84-92`; `schemas/project-v2.schema.json:295-297,316-320`; `IMPLEMENTATION_STATUS.json:206-215`; retained readiness fixtures.

A newly initialized empty project passes review-ready and says completeness is specified within supported scope. A project retaining two requirements with acceptance criteria but removing all components/interfaces/data models/tasks also passes. `readiness` only walks present records; it does not require scoped requirement→component/task/test coverage, a selected environment, task order, file/module contracts, dependency compatibility, or runnable verification. Runtime remains explicitly `not run`, which is a good safeguard. `traceability_coverage` separately exposes missing links but is not a readiness blocker.

**Impact:** Consumers using `profile_satisfied` as permission to begin implementation may start from insufficient specifications; empty lists erase obligations. This is especially important for large multi-file work. Current labels should not be read as production or implementation readiness.

**Recommendation:** Keep incomplete drafts valid and keep review-ready as an architecture review profile. Add an explicit implementation-plan gate for a selected scope, with requirement applicability and `not_applicable`/waived reasons. For every in-scope requirement require an owning component or rationale, an implementation task or already-implemented source evidence, and a verification obligation; require contracts only where applicable. Record runtime/tool/dependency constraints and task/file dependencies. Do not require every project to have an HTTP API, database, auth or rollout plan. **Acceptance:** empty and uncovered implementation plans fail with exact missing requirement IDs; a local CLI with explicit no-HTTP/no-auth/no-deployment applicability passes when its real obligations are specified; review-ready output still says runtime not run until actual receipts exist.

### E03-F03 — Minimized handoff project loses native contract context and cannot regenerate the rich fixture

**Type:** reproduced defect. **Priority:** P1 handoff integrity.

**Sources:** `tools/artifact_compiler.py:65-90,99-104`; `tests/fixtures/rich-project.json:74-96` and its native `api_contract`; `tools/validation_engine.py:326-332`; retained `handoff-roundtrip.json`.

Initial `compile_plan(rich_project)` preserves the supplied OpenAPI in `api.json`. The exported `project.json` allowlist omits `api_contract` and `asyncapi_contract`. The rich fixture's interface operation retains `security:[{session:[]}]`, while the native contract's `components.securitySchemes` disappears from exported project context. Compiling the exported project raises `API projection invalid: ['/records get security/0: security scheme is not declared: session']`.

**Impact:** The bundle still contains `api.json`, so the first exported contract is not erased. However, the portable project cannot independently reproduce that handoff. A developer resuming/importing it may encounter failure or, in other fixtures, lose native contract details when regenerating. The supported-operation correspondence check only verifies method/path presence, not a complete round trip.

**Recommendation:** Explicitly preserve supported native OpenAPI/AsyncAPI contracts in engineering export, or supply a versioned offline contract-reference manifest and a documented loader that restores them before compiling. The simpler option is preserving the supported fields after disclosure review. Keep opaque private extensions excluded. **Acceptance:** rich fixture and native-only schemas/security/components survive export→import→compile semantically; exact refs resolve offline; first and regenerated applicable contract content match after documented canonicalization; redaction changes that make contracts unusable produce a blocker rather than a misleading successful handoff.

### E03-F04 — Projection identity does not describe the final minimized project representation

**Type:** reproduced identity/coverage defect and failing existing test. **Priority:** P1; coordinate with F03.

**Sources:** `tools/artifact_compiler.py:39-44,99-110`; `tools/disclosure.py:7-21`; `tests/test_audit_followups.py:91-102`; retained test log and `handoff-roundtrip.json`.

The compiler computes `projection_hash` after recursive string/key redaction but before export allowlist omissions and replacement of `notes`. For the rich fixture, redaction paths are empty and canonical/projection hashes both equal `923bd6ec83536acbc9c4d65acdbebffacf4627d42038f9717ae5a21d72bba8e0`; exported project digest is `7ef6716fb73bf0e53d2901ee2af2607ad3899f96ffa70f0e6774f16a061f8808`. `api_contract` and `custom_extension` are omitted but not represented in the path-change report. Existing `test_handoff_identity_distinguishes_canonical_and_projection_hashes` fails on this fixture.

**Qualification:** canonical and projected hashes are allowed to be equal when no representation changes occur. The bug is the unclear/incomplete projection identity and missing omission accounting, not equality itself. Artifact hashes do identify exact file bytes and should be retained.

**Recommendation:** Name identity scopes precisely: canonical input, redacted compiler input if needed, exported canonical project, and generated artifact bytes. Compute each after its actual transformation and include omitted/replaced paths. Avoid forcing arbitrary inequality. **Acceptance:** unchanged representation may hash equally; unknown-extension omission and note replacement change exported-project identity and produce omission records; all artifact hashes verify; existing failing regression is repaired with explicit semantic expectations.

### E03-F05 — Published passed-receipt JSON Schema permits null output identity

**Type:** reproduced schema/semantic-validator divergence. **Priority:** P1 before third-party receipt consumption; current Python validator rejects it correctly.

**Sources:** `schemas/verification-receipt-v1.schema.json:76-82,127-143`; `tools/integration_contracts.py:100-104`; `tests/test_audit_followups.py:131-138`; retained `results.json`.

A passed receipt with `output_hash:null` has no Draft 2020-12 JSON Schema errors, because the property permits null and the `passed` conditional only requires presence. Python returns `passed tool result requires output_hash as SHA-256 identity`.

**Impact:** An integration validating only the published schema can accept a success receipt without output identity. This does not show a current unauthorized action: no executable adapter consumes it.

**Recommendation:** In the `passed` conditional require `output_hash` to be a lowercase 64-digit string. Validate published schemas and semantic predicates together at the integration boundary. Add a conformance corpus covering null/missing/invalid identities, timestamps, duplicate capabilities, operation/source mismatches and terminal states. **Acceptance:** all consumers reject null on passed, permit documented absent/null identity on appropriate failures, and agree on the shared invariants.

### E03-F06 — Integration contracts need execution effects and source/result binding before they can safely drive code

**Type:** evidence-backed design risk; no connected-adapter exploit demonstrated. **Priority:** P1 dependency of F01.

**Sources:** `schemas/tool-capability-v1.schema.json:31-69`; `schemas/verification-receipt-v1.schema.json:7-22,83-99`; `tools/integration_contracts.py:68-116`; `tests/test_audit_followups.py:117-143`; `docs/implementation-adapter.md:3-5`.

The schemas establish useful IDs, versions, permission classes, schema objects, timeouts, idempotency, hashes and status. They do not bind a receipt to the manifest capability/version, admitted arguments, actual command, output artifacts, workspace allowlist, execution/network/credential effects or check requirements. `read` can describe running tests in the test fixture, although arbitrary project tests can write files, execute subprocesses and access networks. An authorization reference is a string, not an authorization check. The docs correctly reserve authority to the host; validators cannot supply that missing mediation.

**Recommendation:** Retain this minimal validator module but add host-owned effect/scope mediation in the first adapter. Separate data-read scope from process execution, package-install/network access and production-data access. Bind operation invocation, input source, check plan and resulting artifacts to receipts; verify output hashes and formats through the host before reconciling project state. Use existing host permissions, not an invented in-project approval token. **Acceptance:** adversarial repository text cannot widen scope; stale hashes/path traversal/symlink targets/unadmitted commands fail before mutation; receipt for wrong capability/version/source or unverified artifacts is not accepted; running tests is explicitly reported as code execution with actual effects/limits.

### E03-F07 — Architecture records and implementation verification are not a closed evidence loop

**Type:** observed missing capability for software creation. **Priority:** P1 after source-bound receipts; P2 for richer reporting.

**Sources:** `tools/project_model.py:7-16,84-100`; `tools/artifact_compiler.py:21-34,50-53,94-97`; `skills/test-debug-verify/SKILL.md:6-7`; `skills/implementation-planning-and-change/SKILL.md:7-15`; `tools/workflow_tools.py:46-64,96-100`.

Task acceptance is free text and file mappings are declared paths. The skills tell the host to inspect, minimally change, test and reconcile, but no executable workflow connects a task to an applied patch, checked source tree, check-plan hash, detailed result or deployment state. Project verification coverage uses declared `Accepted` plus `result:passed` records; it does not ingest validated actual run receipts. `data-check` verifies limited in-memory DDL, not migrations, persistence, authorization, queries or business invariants. Minimized CLI run receipts are accounting records rather than comprehensive implementation receipts.

**Impact:** There is no deterministic mechanism to prevent stale checks from being attributed to later edits, or to tell whether a multi-file feature is planned, implemented, built, tested, runtime verified or deployed. Honest skill instructions help, but are not the same as enforced transitions.

**Recommendation:** Add an optional implementation ledger referencing external immutable evidence, rather than embedding raw logs and source in project.json. Track in-scope requirement/task→change-set→resulting source identity→check obligation→receipt/artifact. A newer source tree invalidates applicable checks until rerun or explicitly justified by a reviewable scope decision. Do not silently change accepted architectural intent when reconciling source. **Acceptance:** edits after a passed test mark its applicability stale; failed/blocked/skipped/timed-out obligations never produce verified completion; a trivial documentation change needs only proportionate checks; NFR verification cannot become measured solely by entering an Accepted flag.

### E03-F08 — Specialist implementation guidance is a useful seed but lacks operational recipes and measured program outcomes

**Type:** observed coverage gap; model quality unknown. **Priority:** P2, after core execution/evidence path.

**Sources:** `skills/implementation-planning-and-change/SKILL.md:6-15`; `skills/test-debug-verify/SKILL.md:6-7`; `skills/api-data-contracts/SKILL.md:6-7`; `skills/security-review/SKILL.md:6-7`; `docs/integrations.md:4-9`; `tools/workflow_tools.py:73-85`.

The current specialist instructions correctly require real tools and preserve missing-capability status. They do not specify small concrete scaffolding/module/dependency recipes, safe multi-file patch protocol, framework/version validation, code-quality checks or domain-specific runnable acceptance packs. No sampled program or live model benchmark was created here, so these omissions are not proof that the host model cannot code. The plugin's own tested Python toolkit and browser workbench show software exists in the repository, not that Studio can reliably generate new applications.

**Recommendation:** Expand the existing implementation and verification skills using the contracts below. Add a few verified recipes selected on demand; avoid a skill per framework. Measure actual runnable task outcomes before claiming broader generation reliability. Defer GPU/embedded/mobile/regulated/complex distributed execution until tools, fixtures and expert validation exist.

## Lifecycle capability matrix

N = native executable toolkit; I = instruction/host reasoning; H = actual host tool, conditional on task authorization; X = no connected native capability. This matrix is about the audited environment, not every possible host.

| Lifecycle stage / domain | Current support and evidence | Remaining work / verification |
|---|---|---|
| 1. Understand idea | I: core + requirements skill | Human/model interpretation; no automatic natural-language ingestion command |
| 2. Identify missing requirements | I; N: field readiness on present records | Coverage/applicability and ambiguity judgment; F02 |
| 3. Clarify pivotal ambiguities | I: at most two pivotal questions in core guidance | Requires actual user answer when material; no fabricated defaults |
| 4. Establish constraints | I; N: portable project constraints/ADRs | Validate tool/runtime/business constraints against source |
| 5. Select technologies/dependencies | I; N: selected manifest extraction | Retrieve version-matched official docs when available; compatibility/lock/licensing/SCA through real checks |
| 6. Design architecture | I; N: project model, references, impact, cost worksheets | Semantic design quality remains human/model judgment |
| 7. Scaffold project/module structure | X native app scaffold; N context init; H editor/shell | Manifest/build/env/conventions and files must actually be created |
| 8. Define implementation tasks | I; N task storage/export | Ordered task/file/contract/check obligations; no dispatcher |
| 9. Generate source files | X native; H model + apply_patch | Actual source generation not measured in audit |
| 10. Maintain multi-file consistency | N declared IDs/refs/contracts/hashes; I source review; H compilers/tests | No universal semantic cross-file consistency; enforce imports/types/contracts at actual build/check layer |
| 11. Generate tests | I/H; X native app-test generator | Independent behavior-oriented assertions and negative cases |
| 12. Execute available checks | N artifact/schema/DDL checks; H actual shell | App checks require authorized code execution; state scope clearly |
| 13. Diagnose failures | I test-debug skill; H logs/runner | Reproduction/hypothesis/discriminating check; no automatic debugger integration |
| 14. Correct defects/refactor | I change skill; H editor | Small source-bound patch; protect dirty/unrelated files and data |
| 15. Rerun checks | H shell; N artifact validation | Rerun relevant checks on resulting tree, not old plan hash |
| 16. Document decisions/project | N handoff/ADRs/tasks; I docs | Executable README commands and source/API correspondence need check; F03/F04 |
| 17. Package result | X app packager; H existing package tools | Actual package manifest/build/install/smoke checks; reproducible dependency policy |
| 18. Deployment instructions | I; X native deployment | Provider-specific environments, migrations, secrets, rollback, authorization and actual deploy receipts |
| 19. Complete handoff | N 19+ architecture artifacts/profile/manifest | Working-software handoff additionally needs diff/source/build/tests/runtime/packaging evidence |
| 20. Record limitations | N typed statuses and independent readiness dimensions; I honest summaries | Connect implementation receipts; F07 |
| Frontend/UI/accessibility | I generic design; H Node and optional browser tools if exposed | No native UI scaffold/browser runner. Browser availability and app behavior not established by npm presence |
| Backend/API/business logic | N OpenAPI/native contract support; I; H Python/Node | Runtime routes, validation, error/type correctness require app tests/builds |
| Database/migrations | N data records + limited in-memory SQLite DDL | Real migration safety, backups, transaction/concurrency/reconciliation behavior outside native scope |
| Authentication/authorization | I security/API skills; N contract auth gaps | No auth implementation; negative access/tenant tests and runtime enforcement required |
| Environments/config/secrets | N doctor/tool limits; H managed shell | No app environment manager; inspect existing manifests, isolate installs, never expose secret values |
| Reviews/diffs/maintenance | N project-level change/diff/impact/source scanning; I/H code review | Project diff is not source patch; unsupported languages/runtime dependencies remain unknown |

## Target workflow using tools genuinely available

1. Establish the requested outcome, data sensitivity, constraints and pivotal ambiguity. Use a simple conversational answer for small tasks; persistent project state is optional until continuity adds value. Record assumptions and user facts distinctly.
2. Discover actual host editor/runner/browser/repository capabilities and authority. Read applicable AGENTS instructions, manifests and relevant tests. Pin commit plus dirty/untracked overlay; preserve unrelated user changes. For a new project choose the smallest viable runtime and framework. Reuse repository conventions before introducing dependencies.
3. Select a vertical slice with observable user behavior. Map its requirements to components/contracts/data and behavioral tests. Prefer one deployable application until evidence demands distribution. State explicit no-HTTP/no-auth/etc applicability where relevant.
4. Produce a source-bound implementation plan: intended paths, module responsibilities/public types, data/API contracts, dependencies/runtime versions, expected per-file hashes, task dependencies, behavior/check obligations and recovery. Keep architecture intent and code authority separate.
5. Use actual `apply_patch` or the mediated adapter to prepare a bounded multi-file patch. Generate shared contracts/types once; update all known consumers and tests together. Build path/manifest changes before dependent source. Pin needed package versions based on real docs/manifests and resolve/install only in an authorized isolated environment; a lockfile must come from the package tool, not invented integrity fields.
6. Validate scope/path/expected-hash preconditions before applying. Use isolated scratch checkout/worktree where practical; do not claim cross-file atomicity. Preserve preimages and show partial application on failure. Never delete unknown files or overwrite dirty user content to make tests pass.
7. Run the smallest behavior test, then relevant type/import/build/unit/integration/contract checks. Include negative inputs, authorization/tenant cases, real persistence across process restart and error exit behavior as applicable. Run browser checks only when actual UI runner exists; accessibility and human UX remain separate obligations. Tests are code execution and require the host's actual process/network/filesystem controls.
8. Diagnose failures from actual output, form one testable hypothesis and patch minimally. Cap retries/time/tool budget with a useful blocked/partial result; never hide failing/skipped tests or replace them with changed acceptance criteria. Rerun relevant checks on the changed tree.
9. Review the complete diff and reconcile module imports/types/config/contracts/data/docs. Verify generated-file ownership. Acceptance tests establish the requested behavior; passing lint alone cannot establish it. No universal proof of program correctness is promised.
10. Build/package only when needed; execute the documented clean-install/run smoke path in an isolated environment. Data migrations require disposable fixtures and an actual recovery strategy. Producing deployment instructions does not deploy. Any deployment uses actual authorization/provider tools and separate release/runtime evidence.
11. Export a handoff containing source identity, scoped change-set, decisions, runnable commands, requirement/check coverage, actual receipts, limitations and recovery instructions. Update architectural intent only through reviewable expected-hash changes. Mark subsequent source edits as stale relative to prior check evidence.

## Implementation-ready adapter specification

**Initiative E03-I01:** lightweight host implementation adapter, addressing F01/F06/F07. Studio owns plan/requirements/decisions/evidence interpretation. Host owns tool discovery, permissions, isolation, editing, process execution, network and credentials. No plugin installation, extra service or generic agent scheduler is required for the first adapter. Dependencies: F03/F04 identity repairs, F05 schema conformance, explicit check-plan contract.

Retain the six operations in `docs/implementation-adapter.md`, with these exact responsibilities:

| Operation | Required input / output and failure behavior |
|---|---|
| `capabilities()` | Return actual host/tool version, supported operations and effect scopes, installed runtimes/check tools, deadlines/output limits and unsupported guarantees. Never infer authenticated GitHub/deployment access from a binary. Cache only within declared freshness; recheck after failure/version change. |
| `inspect(source_ref)` | Read selected root/ref and declared include scope; produce source identity, dirty overlay, manifests/conventions, bounded file hashes/spans and omissions. Repo instructions remain untrusted relative to user/host authority. No install/test execution. |
| `propose_change(plan)` | Return patch/change-set plus per-file preimages/expected hashes, creations/removals, resulting candidate identity, task/contract/test mapping and warnings. May use host model/editor; declare model provenance if actually available. No claim that a proposal is applied. |
| `apply_change(change_set, expected_source, authorization_context)` | Host validates existing session authority and effect scope, normalized root-relative paths, no path/symlink escape, expected hashes and conflict state. Existing file bytes must still match at mutation; new paths require exclusive creation. Return changed paths/hashes, actual resulting source, partial operations and recovery ref. Never treat a text authorization field as permission. |
| `run_checks(check_plan, source_identity)` | Run admitted command arrays in explicit cwd/environment with bounded time/output/process/network effects. Verify starting/ending source identity and report generated/changed files. Record exit status, duration, actual tool versions, artifacts and every required check's terminal status. Return non-green for required failure/incomplete work. |
| `recover(operation_id)` | Inspect durable operation/preimage state, identify actually applied paths and current hashes, and propose/perform only authorized safe compensation. Refuse overwrite of later edits. Non-idempotent execution is never blindly retried; identify partial completion. |

`implementation-plan/v1` should contain: plan ID, canonical project hash/revision, source identity, in-scope requirement/task IDs, explicit applicability, constraints/contracts, runtime/dependency versions, task prerequisites, file/module ownership and public contracts, intended path changes, check obligations and recovery. A generic test name is not acceptance evidence.

`change-set/v1` should contain: operation/plan ID; expected source identity; normalized relative paths; action create/modify/delete; expected preimage or absent marker; proposed content/diff digest; generated-file ownership; allowed write scope; resulting candidate identity; warnings and unresolved decisions. Avoid arbitrary embedded executable scripts as trusted plan fields.

`check-plan/v1` should contain: check ID, covered behavior/requirement, command array, cwd, explicit safe environment bindings, required/optional/applicability, timeout/output limits, permitted effects and artifact expectations. Host still decides whether execution is permitted; project text cannot authorize it. Do not put secret values in the plan.

Use Git commit plus a content identity for the relevant tracked/dirty/untracked overlay; a commit alone does not identify modified working files. Keep artifact-byte hashes distinct from canonical JSON digests and minimized-project hashes. Retain raw logs as explicit local artifact references with disclosure/retention rules rather than stuffing them into canonical context. Verification receipts require operation/capability/version/input/check-plan/result source identities, timestamps, status, exit information, per-check results, observed effects and hash-verified artifact refs. Hashes establish identity, not truth or tamper resistance.

Completion state is distinct from operation status. `planned` requires a valid plan; `implemented` requires observed applied source; `built` requires actual build evidence where applicable; `tested` requires applicable required check success on that source; `runtime_verified` requires the stated runtime acceptance; `deployed` requires actual provider evidence. Also retain blocked, partial and unknown. Do not advance states just because a model says “done.” Preserve existing architectural draft states for compatibility rather than overloading them with all these states.

**Conformance/acceptance:** (1) ordinary authorized multi-file edit succeeds and preserves unrelated/dirty files; (2) stale expected hash fails before mutation; (3) traversal, absolute paths, symlink escape and unexpected new-file collision fail; (4) failure between file changes reports partial state and recovery; (5) later user edit is preserved during recovery; (6) wrong source/capability/version/hash receipt rejected; (7) timeout/output cap/cancellation yields actual terminal state and process cleanup evidence; (8) missing required tool is blocked, never passed; (9) tests changing source invalidate or explicitly identify the resulting source; (10) hostile repo text cannot widen permissions/install/deploy; (11) logs avoid secret values and context sharing is minimized; (12) no write/deployment occurs in read-only/offline fallback. These are future regression obligations, not tests claimed to have run in this audit.

## Skill specifications and expansion policy

**E03-I02: expand `implementation-planning-and-change` in place**, addressing F01/F02/F07/F08. Trigger: user requests a new application, feature, defect fix or refactor requiring source edits. Inputs: user scope/authority, source identity, relevant repository instructions/conventions, requirements/contracts and available tool capabilities. Workflow: inspect → scoped plan/check obligations → minimal patch → conflict-safe apply → real checks → diff review → evidence reconciliation. Outputs: plan/change-set, actual changed source, per-check status/artifacts, acceptance coverage, unresolved risks and runnable handoff. Unsupported environment yields a patch/plan plus exact blockers. Do not add a second competing coordinator.

**E03-I03: expand `test-debug-verify` in place.** Trigger: a behavior failure, new implemented behavior, or readiness request. Inputs: expected/actual behavior, reproduction, source/runtime identity and actual runner. Workflow: discriminate hypotheses, preserve negative/regression tests, run targeted then relevant wider checks, bind outcomes to source, and separately assess runtime/packaging/security evidence. Outputs: reproduction, test/check plan, actual statuses, useful logs, residual uncertainty and source-bound receipt. Required acceptance: intentionally broken behavior fails; corrected behavior passes; stale results cannot certify later code; disabling a failing test does not mark the requirement satisfied.

**E03-I04: optional recipe packs, not a framework skill explosion.** Begin with (A) Python standard-library CLI/SQLite vertical slice, and (B) one chosen web stack with exact manifest/lock/runtime and actual UI/API tools. Select B from observed user demand and existing maintainers' expertise; the audit does not establish which web framework is optimal. A recipe defines directory/module conventions, environment commands, pinned compatibility policy, error/type practices, acceptance tests and clean packaging/run procedure. It is an example, not a default forced onto every repository. Activate API/data and security skills only for applicable contracts/trust boundaries. External docs retrieval is optional and version-scoped; unavailable retrieval becomes a declared limitation, not a guessed version claim.

**Recipe acceptance and quality measurement:** execute an authorized idea→working software task, a multi-file contract change, an injected defect/debug task, dirty-tree conflict, missing runner/dependency, and interrupted operation. For UI work include actual browser behavior and relevant accessibility checks. For auth include negative permission/tenant tests; for data include persistence/migration fixtures. Freeze task/source/model/skill/tool provenance and retain outcomes. Measure end-user acceptance success, critical defect count, useful corrections, reversions, time/cost and unresolved blockers across repeated tasks. Compare to the same host without the recipe using calibrated review; deterministic fixture tests alone do not establish generation quality. No universal “production-ready” or “works in all languages” score.

## Delivery sequence and alternatives

1. **Repair reproducibility first:** F03/F04, restore green existing regression, and add native contract round-trip/schema conformance tests (F05). Preserve safe revision, output ownership, immutable generation and independent readiness dimensions. This is a bounded repair, not redesign.
2. **Define the implementation gate and contracts:** F02/F06/F07. Keep draft/architecture review use lightweight. Add scoped coverage and source/check identity without requiring every optional field on every task.
3. **Implement a single host adapter and two vertical-slice proof tasks:** use existing editor/shell, not a new coding plugin or autonomous runtime. If only manual execution is available, export the same plan/check artifacts and require imported actual receipts. Do not mark the manual fallback automated.
4. **Expand implementation/verification skills and one recipe at a time:** only after actual acceptance outcomes demonstrate benefit. Add official version-matched docs, browser, CI or deployment integrations when a concrete workflow requires them and capability/permission tests pass.
5. **Delivery remains provider-specific:** package and deployment capabilities are optional; do not build native multi-provider deployment/orchestration, universal semantic index, hosted shared project service or multi-model autonomous expansion without a demonstrated need and separate evidence.

Alternative A, architecture-only Studio plus manual coding handoff, is viable and simplest if users mainly need design support. Alternative B, the recommended host adapter, adds traceable real implementation with modest maintenance while respecting current tools. Alternative C, a native all-language IDE/compiler/deployment platform, duplicates mature host tooling and creates disproportionate security/maintenance burden. The evidence supports B incrementally, while keeping A as graceful fallback.

## Residual limits and cross-track observations

This review did not measure live model coding quality, large-repository semantic reasoning, actual app behavior, browser interaction, package installation, deployment, Docker daemon health or remote credentials. Passing Studio tests does not prove generated software quality. F01/F06/F07 are honest gaps against the requested expanded destination, not claims that existing docs falsely advertise execution.

The CI workflow invokes `python tools/check_source_manifest.py --check` at `.github/workflows/ci.yml:32`; that path was absent from the checkout file inventory. This is a source-backed cross-track observation sent to the coordinator, not a claim that remote CI was executed. The repository core skill lacks the installed cloud skill's explicit six-specialist routing section; source/package version alignment should be handled by the release/skills tracks rather than inferred to be a runtime dispatcher defect.

**Final assessment:** retain the existing architecture toolkit and integrity controls, fix the reproducible handoff defects, then add a small host-backed edit/check/evidence path. This is the strongest practical route to coherent, tested programs in the tools actually available. Program generation reliability remains unverified until real source, behavior checks and repeated outcomes are measured.
