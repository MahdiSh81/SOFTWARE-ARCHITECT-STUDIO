# Expert 06 — Security, privacy, and software supply chain

**Independent first-pass assessment, 2026-10-29.** Source: `/workspace/SOFTWARE-ARCHITECT-STUDIO`, clean commit `83812e1d31c17ed857be8d2fb5c98126a8ccb5c8`. The checkout remained unchanged. Tests used Python 3.12.14 in `/workspace/sas-env` with `PYTHONDONTWRITEBYTECODE=1`; adversarial fixtures and the harness were outside the checkout. No additional agents, network probes, package installations, external writes, publication, or destructive tests were performed. I did not read other reviewers' first passes.

## Recommendation and scope of confidence

Preserve the local, offline architecture and its existing safety controls. Repair the three highest-priority boundaries before expanding implementation or deployment authority: auxiliary output ownership, authentication fidelity in generated contracts, and the conversion of imported project text into native agent instructions. Then repair evidence identity/receipt parity, define a cache trust policy, and make CI dependencies reproducible.

The reviewed release is a local architecture toolkit and offline workbench. It does not implement application authentication, a multi-tenant service, a connected implementation adapter, or a deployment service. No verified remote-code-execution exploit, unauthorized remote action, production data breach, or P0 security vulnerability was established. Several meaningful local integrity defects were reproduced. A secure skill instruction is not an enforcement boundary, and an exported contract is not an implemented security control.

Labels below distinguish **OBSERVED** source behavior, **TESTED** local counterexamples, **THREAT HYPOTHESIS** downstream exploitation requiring additional conditions, and **PROPOSED** changes. Priorities reflect this product's current local scope; P1 means fix before relying on the affected workflow for consequential engineering handoffs, not a claim of an Internet-facing exploit.

## Prioritized findings

### E06-F01 — P1 — A receipt option lets an observational command overwrite canonical project or source files

**OBSERVED / TESTED.** `--receipt` accepts any local path (`tools/architect_cli.py:27`), and successful commands call `record_run` at `tools/architect_cli.py:99`. That function writes through `atomic_write(path, ...)` without exclusive publication or ownership/collision checks (`tools/workflow_tools.py:96-101`). `atomic_write` deliberately replaces an existing regular file (`tools/safe_io.py:75-94`). The robust no-follow checks prevent symlink escapes but do not prevent replacing a legitimate unrelated regular file.

A temporary `project.json` containing a valid canonical document was passed as the receipt path to `doctor`. Exit code was 0; the project was replaced with a small object containing `receipt_schema: 1`. This does not require a malicious import or race. A mistaken filename, or a source-suggested command accepted without host review, is sufficient. The original project is not backed up by the receipt operation.

**Impact / limits.** Silent local data loss from an otherwise observational workflow. Filesystem permissions and the explicit path argument constrain the affected files. This is not privilege escalation. The same defect can affect a source file or other user-owned file within available host permissions.

**PROPOSED contract.** Receipt creation must be non-clobbering by default. Use exclusive publication; a separately requested replacement must verify that the existing file is a matching receipt owned by this operation family. Reject collisions with command inputs, canonical project/history/journal/lock files, handoff outputs, and source files. Do not treat `--receipt` as blanket overwrite authorization. Check for collisions before running a mutating primary command so a late receipt error does not make a completed write appear wholly failed.

**Acceptance.** `doctor --receipt EXISTING_PROJECT`, source-file, unrelated-JSON, hardlink-alias, and symlink fixtures all preserve original bytes and fail with a typed collision result. A fresh path creates one minimized receipt. An explicitly owned receipt replacement follows the documented policy. A primary operation that commits before a later receipt failure reports its committed state and the receipt failure separately.

### E06-F02 — P1 — Declared authentication can disappear from a review-ready OpenAPI projection

**OBSERVED / TESTED.** Readiness treats a truthy `interface.authentication` as enough to remove the authentication obligation (`tools/artifact_compiler.py:18-19`). Compilation copies only `interface.operation` into the OpenAPI operation (`tools/artifact_compiler.py:81-87`); it never converts or reconciles the separate authentication declaration. The generated `security.md` lists only remaining authentication obligations (`tools/artifact_compiler.py:93`).

A valid project with one GET `/private` interface, `authentication: "BearerAuth required"`, and an operation with valid responses produced:

- `profile: review-ready`, `profile_satisfied: true`, and `blockers: []`;
- an OpenAPI document with no root or operation `security` requirement;
- `security.md` containing `- None documented.`

The original authentication text remains in `contracts.json`, so data is not entirely lost. The problem is contradictory executable-interface and readiness projections, which can guide an implementer toward a publicly accessible operation. The independent runtime/human-review disclaimers remain helpful but do not repair this correspondence defect.

**PROPOSED contract.** Introduce typed interface authentication intent: `unspecified`, `public` with a reason, or `required` with explicitly declared scheme references and scopes. For native OpenAPI, preserve its security semantics and check consistency with interface intent. For generated OpenAPI, require a supplied scheme definition and translate supported intent; never invent a bearer/OAuth implementation from prose. Prose-only authentication remains visible and blocks review-ready correspondence until resolved. `security: []` must be recognized as an explicit public operation rather than proof that a declared protected interface has authentication.

**Acceptance.** Protected intent cannot produce a review-ready operation with absent or public security. Public intent, root inheritance, operation overrides, declared schemes, OAuth scopes, and unsupported/prose-only intent each have positive and negative fixtures. Missing or conflicting security produces an exact record/field blocker. Native protected contracts remain unchanged. `security.md` states the resolved policy and unresolved conflicts, not just the absence of missing fields.

### E06-F03 — P1 integration-boundary risk — Imported Accepted decisions are emitted into native agent instruction files

**OBSERVED / TESTED generation; downstream obedience is a THREAT HYPOTHESIS.** Canonical imports may retain `status: Accepted`; ordinary project validation checks the lifecycle enum, not the identity of an approver (`tools/project_model.py:43-51`). This is intentional and should remain so. The compiler then copies every Accepted decision's text directly into a default `AGENTS.md` (`tools/artifact_compiler.py:95-96`). The browser offers the same transformation (`workbench/index.html:69`). These outputs omit `approval_origin`, although resume packets preserve it (`tools/project_model.py:94-100`).

A synthetic external decision containing multiline instructions to report checks as passed survived verbatim in generated `AGENTS.md`; its `approval_origin: external unverified import` did not. No model was asked to obey that file, and no unauthorized action occurred. The verified defect is promotion into a filename that coding hosts commonly treat as operational instructions, with provenance reduced to an architecture constraint label.

The opening disclaimer that constraints grant no tool authority is a useful control. It does not prevent imported text from directing test selection, suppressing findings, changing scope, or contradicting later instructions within the same file. `IMPLEMENTATION_STATUS.json:151-162` records an acceptance objective that synthetic instruction fixtures do not authorize actions; a plain-text disclaimer alone does not demonstrate that property across hosts.

**PROPOSED contract.** Default handoff should emit an ordinary architecture-constraints document or structured JSON with source revision, record IDs, and approval provenance. Preserve imported Accepted status in canonical state without another approval interview. Make native instruction-file emission an explicit action scoped to a reviewed set of records and destination; the receiving host must still enforce actual user/session authority. Do not interpolate arbitrary imported prose into an automatically active instruction surface. Do not propose filtering a few injection keywords as a security boundary.

**Acceptance.** A hostile multiline Accepted record remains available as quoted/structured project data, retains provenance, and cannot become an active instruction file through ordinary handoff. Explicit instruction export shows exact content and source identity. In an authorized host integration test, malicious project/tool output cannot add file reads, network access, messages, writes, or deployments to the approved action plan, and cannot change evidence statuses. Human review of architecture decisions must remain distinct from grants of tool authority.

### E06-F04 — P2 — The advertised projection identity is computed before the actual disclosure projection

**OBSERVED / TESTED; existing regression fails.** `projection_hash` is computed after pattern redaction at `tools/artifact_compiler.py:40-44`, before the root-field allowlist and replacement `notes` are applied at `tools/artifact_compiler.py:98-104`. Consequently it identifies an intermediate object, not the exported `project.json`. It can equal the canonical hash even when the exported project omits private history/extensions. `redaction_report.paths_changed` only reflects pattern substitutions, not omitted root paths (`tools/artifact_compiler.py:106-110`).

A temporary project with `private_extension` and `history` produced `canonical_input_hash == projection_hash`, `projection_hash != digest(exported_project)`, no exported private fields, and `paths_changed: []`. Existing `test_handoff_identity_distinguishes_canonical_and_projection_hashes` failed at `tests/test_audit_followups.py:101`; the other ten tests in that file passed.

**Impact / limits.** A recipient cannot use the claimed projection identity to identify the received minimized context or audit what was omitted. The per-artifact hashes correctly identify individual emitted files; no private-field disclosure was observed in this fixture. This is provenance/disclosure accounting failure, not evidence that SHA-256 is broken.

**PROPOSED contract.** Define exactly what `projection_hash` hashes, calculate it after redaction and selection, and expose a separate intermediate hash only if a consumer needs it. Report `changed_paths` and `omitted_paths` separately, with escaped JSON Pointer paths. Canonical identity remains the unmodified source identity. Define the hash of serialized bytes versus canonicalized JSON explicitly.

**Acceptance.** For ordinary handoff, the documented projection identity recomputes from the disclosed project; omitted-only and redacted-only fixtures both report the correct changes. Explicit full-private export recomputes to the canonical identity under the same normalization. Artifact hashes remain correct. The existing failing regression is repaired without weakening the assertion to disguise the intermediate-object mismatch.

### E06-F05 — P2 — The published verification-receipt schema admits passed results without an output identity

**OBSERVED / TESTED.** The receipt schema allows `output_hash` to be `null` (`schemas/verification-receipt-v1.schema.json:76-82`). Its passed-result conditional requires the property but does not narrow its type (`schemas/verification-receipt-v1.schema.json:127-143`). `validate_verification_receipt` correctly rejects that same record through `validate_tool_result` (`tools/integration_contracts.py:100-104,115-116`).

A complete `status: passed`, `permission_class: read`, `output_hash: null` receipt had zero Draft 2020-12 schema errors and one runtime error: `passed tool result requires output_hash as SHA-256 identity`.

**Impact / limits.** External adapters using the published schema can accept evidence that native code refuses, weakening source/output binding. This package does not currently discover or invoke adapters (`tools/integration_contracts.py:1-4`; `docs/implementation-adapter.md:2-5`), so no current authority bypass was demonstrated. Neither validation path authenticates the tool, proves its assertions, or resolves an authorization reference.

**PROPOSED contract.** In the passed branch, require a non-null lowercase SHA-256 string. Maintain one conformance corpus for schema and Python validation, including missing/null/blank hashes, timestamps, consequential authorization references, unknown fields, and status combinations. An eventual host adapter must bind tool identity, operation/capability, expected source, output artifacts, and a host-resolved authorization reference. A syntactically valid receipt never grants authority.

**Acceptance.** Schema and Python agree on every supported fixture; passed null identity is rejected. A forged but well-formed receipt may be stored as attributed evidence, but it cannot mark implementation/runtime/deployment verification as trusted without the receiving host's matching invocation and artifact evidence. No signatures or tamper-resistant storage are claimed unless actually provided.

### E06-F06 — P2 conditional — An altered extraction cache can launder a fitness violation into a scoped pass

**OBSERVED / TESTED.** An opt-in cache is accepted based on schema, adapter version, root, and shallow list/dict shapes (`tools/repository_evidence.py:119-124`). For a matching `relative_path:source_sha256` key, its items and edges are used without re-extraction (`tools/repository_evidence.py:131-149`). `fitness` then uses those edges and the fact that source bytes were observed to produce `satisfied-in-scope` (`tools/repository_evidence.py:181-189`).

A temporary source containing `import forbidden.module` initially produced one edge and a `violation`. Replacing only the cache entry's `items` and `edges` with empty lists produced one cache hit, zero edges, an unchanged source fingerprint, and `satisfied-in-scope`. No source edit was made. Both clean and cached ordinary parity tests still pass, as expected; they do not test malicious cache alteration.

**Preconditions / limits.** The user must opt into that cache and an actor must be able to modify it. A hostile same-user process can already damage other local evidence, so this is not privilege escalation. It matters when caches are copied, restored, shared, consumed as untrusted files, or treated as independently verified extraction evidence. A content-addressed source key does not authenticate derived observations.

**PROPOSED contract.** Document cache ownership/trust explicitly. Clean no-cache extraction should be required for a release/security fitness gate unless the host has established trusted cache provenance. Imported/untrusted caches must be ignored, recomputed, or yield `unknown`, never an apparently verified clean rule. Bind cache identity to the actual extractor implementation as well as a release label; a digest of editable cache contents alone is not authentication.

**Acceptance.** A forged empty-edge entry cannot change a clean-collection violation into a green gate. Legitimate cache runs retain parity and disclose hits. Unsupported/parser-failed extraction also remains `unknown` for rules whose evidence was not actually extracted. Tampered cache tests must hold source fingerprint constant to catch this failure mode.

### E06-F07 — P2 — CI dependency resolution is not bound to the recorded dependency inventory

**OBSERVED configuration; compromise is a THREAT HYPOTHESIS.** `requirements-validation.txt:2-4` pins three direct Python dependencies. The 19-entry transitive inventory in `requirements-validation.lock` has version pins but no distribution hashes. CI installs the direct requirements file, not that lock (`.github/workflows/ci.yml:22-27`). GitHub Actions are referenced by mutable major-version tags (`.github/workflows/ci.yml:17-23,37-41`). Browser CI runs `npm install` (`.github/workflows/ci.yml:44-46`), and the only tracked `*lock*` file is the Python inventory; `tests/browser/package.json:8-10` pins Playwright directly but not its transitive dependency graph.

**Impact / limits.** Re-running the same source commit can resolve different transitives and retrieve changed action code. This undermines reproducible release verification and increases external code trust. It is not evidence that a dependency or GitHub Action is malicious or vulnerable. `permissions: contents: read` (`.github/workflows/ci.yml:8-9`) reduces GitHub token authority and should be preserved.

**PROPOSED contract.** Generate a reviewed, platform-supported full Python lock with hashes and install it using hash enforcement; keep human direct requirements separately if useful. Commit an npm lock and use `npm ci`. Pin third-party Actions to reviewed immutable commits with automated update PRs, retaining readable version comments. Record interpreter, OS, package distributions, browser binary version, and lock hashes in release evidence. Use a small maintained SCA/secret scanning workflow with scoped exceptions rather than inventing a native vulnerability database.

**Acceptance.** CI's install commands consume the reviewed locks; a lock change is required for a dependency change. Clean repeat installation yields the declared versions/identities on each supported target. Dependency/action updates run regressions and produce a reviewable diff. Generate an SBOM or equivalent machine-readable resolved inventory for releases. Findings and suppression ownership are retained, and vulnerability freshness is dated.

### E06-F08 — P2 privacy hardening — Validator diagnostics can reproduce confidential input in CLI results

**OBSERVED / TESTED.** Optional validators catch exceptions and print `str(e)` (`tools/validator_worker.py:22-23`). Validation copies the tail of worker output into check details (`tools/validation_engine.py:319-320`), and the CLI prints the complete result (`tools/architect_cli.py:100`). Schema validation exception text can include the offending object and its values. This path does not use the disclosure minimizer.

A temporary OpenAPI security scheme with an invalid `type`, a `password` property containing a synthetic marker, and a synthetic extension passed the basic gate and failed full validation. The marker appeared in the returned validation report. Only synthetic data was used. The minimized run receipt itself did not leak it; this finding concerns the ordinary diagnostic report/stdout, which may be copied to CI logs or shared reports.

**Impact / limits.** Local validation reports must currently be treated as having the input's confidentiality. Full error details can help debugging; the tool makes no blanket promise that all diagnostics are sanitized. This is a concrete disclosure channel and a hardening opportunity, not a verified external exfiltration.

**PROPOSED contract.** Return structured validator name, source hash, schema/instance path, rule code, and bounded safe summary by default. Keep full raw errors only in an explicitly private local diagnostic artifact. Apply disclosure rules at every stdout/report boundary, not just handoff generation. Pattern redaction remains defense in depth and cannot make arbitrary project text public-safe.

**Acceptance.** Synthetic secrets in invalid schemas, YAML values, quoted names, JSON Pointer targets, exception messages, and subprocess output do not appear in default logs/reports. A private diagnostic mode is explicit, locally scoped, and clearly labeled. Useful location/rule diagnostics survive minimization. Raw private errors do not enter portable receipts or shared evidence.

### E06-F09 — P2 test-environment exposure — The browser-test web server binds all interfaces and serves the repository root

**OBSERVED configuration and interpreter help; no listening server or network probe was launched.** `tests/browser/playwright.config.cjs:5` launches `python -m http.server 4173 --directory ../..`. From the configured browser-test working directory (`.github/workflows/ci.yml:44-49`), this serves the repository root. The actual Python 3.12.14 `http.server --help` states that the default bind address is **all interfaces**. A loopback `baseURL` does not change the listening address.

**Impact / preconditions.** While a developer runs browser tests, reachable peers may read repository contents, including any sensitive local/untracked files present under that root, subject to host firewall and network reachability. The audited source contains no identified real secret, and no remote exposure was demonstrated. The server is a test utility, not the shipped offline workbench.

**PROPOSED / acceptance.** Bind explicitly to `127.0.0.1` and serve only the workbench directory or a dedicated temporary fixture root. Update paths consistently. A local process/socket inspection test confirms loopback-only binding; HTTP tests confirm repository metadata, unrelated source, and sensitive fixture files outside the fixture root are unavailable. Do not add authentication infrastructure to solve a test-only static-file serving scope issue.

## Threat model

### Assets and actors

| Asset | Required property | Relevant actors and assumptions |
|---|---|---|
| Canonical project, source, accepted decisions, human-edited outputs | Integrity, recoverability, explicit change scope | Legitimate user; accidental CLI mistakes; collaborator/import supplier; cooperating local writers. Hostile same-account writers are not fully isolated. |
| Private context/history, prompts/responses, source snippets, credentials | Confidentiality, minimized disclosure, controllable retention | User; recipient of exports/logs; browser extension or same-origin script; external validator/connector; dependency code. No encrypted local storage is claimed. |
| Local filesystem, network, process and credential authority | Least privilege and host-mediated authorization | CLI user; external tool; installed packages; coding host. Subprocesses inherit the user's OS authority despite reduced environment. |
| Source hashes, evidence, verification status and receipts | Correct attribution, source/output binding, honest completeness | Repository author, tool/result producer, cache editor, reviewer. Hashes identify bytes, not truth or approval. |
| Release artifacts and dependencies | Reproducible, reviewable provenance | Maintainer; package registry; action publisher; transitive dependency maintainer; update workflow. No authenticated release attestation was verified. |

The current browser has no server-side user/tenant model. Its relevant isolation is browser profile/origin and host storage permissions. A future hosted product would need a separate identity, tenant, authorization, audit, key-management and deletion design; none should be inferred from the offline UI.

### Boundaries, threats, existing controls, and residuals

| Boundary / scenario | Existing mitigations with source | Missing control / recommendation | Residual after the proposed control |
|---|---|---|---|
| User/session instructions versus project/repository/tool text | Explicit authority rule in `skills/software-architecture/SKILL.md:28,65`; adapter remains declarative (`docs/implementation-adapter.md:2-5`). | E06-F03; host must mediate concrete actions and effects using actual session authorization. | Natural-language prompt injection cannot be eliminated by prose. Host permission checks and human scope review remain necessary. |
| Untrusted files versus filesystem operations | Bounded regular-file reads, no-follow POSIX descriptor traversal, private new-file modes (`tools/safe_io.py:20-67,75-94`); scanner skips symlinks/special files (`tools/repository_evidence.py:98-107`). | E06-F01 for auxiliary writes; keep host workspace restrictions and explicit output roots. | Non-POSIX race protection is preflight only (`tools/safe_io.py:112-116`); hardlinks/mounts/hostile writers are not a sandbox. |
| Canonical revision versus journal/history | Expected hash, cooperating lock, validated journal payload/identity, current-hash reconciliation (`tools/revision_store.py:24-35,50-67,78-97`). | Preserve these repairs; do not relabel local history as authenticated evidence. | Local writable history can be altered by its owner; fsync is not certified power-loss durability or distributed concurrency. |
| Exported files versus managed handoff ownership | Root containment, committed generation pointer, per-artifact hashes and human-edit preservation (`tools/artifact_compiler.py:122-175`). | E06-F04; validate untrusted recovery manifests as data, including reserved names, normalized relative paths, hash types and generation consistency. | Output metadata remains local and editable, not a tamper-resistant record. Imported bundles require explicit trust handling. |
| Canonical context versus public/shared export | Root allowlist and pattern minimizer (`tools/artifact_compiler.py:41-43,98-115`); snippets off by default (`tools/repository_evidence.py:13-19,147,159`). | Explicit disclosure profile/preview; E06-F08. Never equate portable with public. | `tools/disclosure.py:3-20` is intentionally incomplete; credentials in aliases, URLs, PEM blocks or prose may survive. Recipient review remains necessary. |
| Browser import versus DOM/execution | Bounded validated import and number checks (`workbench/project-core.js:32-42`); UI places values using `textContent`, input `.value`, and created elements (`workbench/index.html:38-40`). No remote scripts or network calls were found in this source. | Keep text-only insertion, add malicious-markup regression fixtures; optional restrictive CSP is defense in depth if hosting changes. | No full browser-origin/XSS audit was executed here. Browser extensions/same-origin code can read unencrypted state. |
| Browser storage/history versus user privacy | Session-only, flat 20 snapshots, scoped purge and recovery controls (`workbench/index.html:17-18,33,59-61`); explicit unencrypted/storage-copy warning (`workbench/index.html:28`). | Label current portable exports confidential by default; provide disclosure preview and retention guidance. | Purge cannot delete downloads, Git, backups or remote copies. Per-tab drafts retain context until scoped purge. |
| Optional validators versus local OS authority | Explicit opt-in render; allowlist-style resource blocking; strict Mermaid config; bounded process group/deadline/file output; reduced environment (`tools/validation_engine.py:203-220,280-320`); external OpenAPI refs rejected (`tools/validator_worker.py:11-15`). | Run untrusted renderers/checks in a host-enforced restricted environment when available; capture exact executable/package versions. | Process limits are not filesystem/network isolation. `mmdc` is PATH-selected and no real renderer was installed/tested. Dependencies and browser engines remain attack surfaces. |
| Cache/receipt/tool claims versus trusted verification | Typed result validation and source-hash checks (`tools/integration_contracts.py:68-116`); no native invocation/authorization claim. | E06-F05/F06; attach actual host invocation evidence to trusted completion states. | Well-formed but dishonest tool outputs remain possible; host trust and independent checks matter. |
| Generated application security versus design advice | Security review skill names assets/boundaries and limits claims (`skills/security-review/SKILL.md:1-8`); placeholder operations labeled as drafts (`tools/artifact_compiler.py:82-83`). | E06-F02; stack-specific implementation and runtime acceptance below. | No app runtime, authentication middleware, tenant enforcement, deployment or production security was verified. |

**Likelihood / impact assessment.** Receipt collision is easy to trigger locally and can have high integrity impact. Authentication drift is easy to trigger for prose-modeled interfaces and can affect later generated software. Imported-instruction abuse requires consumption by an instruction-reading host and has potentially high impact. Cache poisoning requires access to an opted-in cache and primarily harms assurance integrity. Dependency compromise is lower-frequency/high-impact and not established here. Validator disclosure and test-server exposure require shared logs or network reachability respectively; both are avoidable with small changes.

## Security semantics and residual issues that are not elevated to verified exploits

The basic OpenAPI gate checks that security requirements name declared schemes and that scopes are arrays of strings (`tools/validation_engine.py:72-86,102-113,167`). It does not validate scheme types or scope semantics. A bearer scheme with a nonempty scope list, and even a scheme with `type: made-up`, produced no basic issues. The optional full validator correctly failed the invalid scheme. Keep the basic/full distinction explicit. Add full-schema checks for relevant review-ready contracts; do not market the basic gate as authorization-policy verification. E06-F02 concerns lost intent even when syntax is valid and will not be solved solely by running a schema validator.

The redactor is explicitly pattern-based and incomplete. Failure to remove every arbitrary secret is not a newly discovered contradiction of its stated contract. Default minimized CLI handoffs still need review, while browser portable project export intentionally preserves canonical data (`README.md:58`; `workbench/index.html:52-53`). These are different disclosure profiles. A consistent, visible profile vocabulary is preferable to silently stripping canonical data from portable exports.

Recovery journals now validate payload hashes and committed-current identity before rebuilding history. The relevant existing mismatch regression passed. I found no basis to re-open the historical claim that a mismatched committed journal silently rewrites current state. Local hashes and editable provenance also cannot prove a human actually accepted a decision; the skill already states that limitation.

Manifest recovery remains an area for targeted malformed-metadata tests. I did not establish a path escape through `guard`; it rejects lexical escape and symlinks. Metadata-chosen filenames can still affect recovery behavior inside an authorized output root, so validate generation manifests, reserve control-file names, and preserve all user bytes on malformed input. Treat this as a hardening hypothesis until a concrete destructive path outside the documented ownership model is verified.

## Minimal target security contracts

These are **PROPOSED**, not existing capabilities, and should fit the existing local toolkit rather than create a hosted security platform.

1. **Action authorization.** Before an external adapter performs effects, bind a concrete operation ID, tool identity/version, exact source identity, input/output schemas, allowed read/write roots, network destinations, secret selectors, process execution, idempotency/retry policy, timeout and session authorization reference. Permission class `read` alone is insufficient to describe a test process that can write files or contact a network. Resolve authorization in the host; never resolve it from project text, Accepted status or tool receipts.
2. **Evidence acceptance.** Separate `attributed`, `structurally_valid`, `invocation_bound`, `artifact_verified`, `human_reviewed` and runtime/deployment evidence. Keep source hash, result artifact hashes, collection scope, omitted checks and terminal status. Do not automatically promote a schema-valid receipt or cache hit into a trusted pass. A single status field cannot carry all these claims safely.
3. **Disclosure.** Explicit profiles: portable canonical project, minimized shared handoff, and private history-inclusive backup. Each has documented included/omitted data and identity. Default logs contain structured safe diagnostics. Private artifacts are clearly labeled and created with private local modes; no promise of encryption or remote deletion.
4. **Artifact ownership.** Every auxiliary writer follows the same non-clobbering/owned-replacement policy as managed outputs. Normalize paths, reject reserved control names and aliases, preserve human edits, and distinguish primary commit status from projection/receipt failure.
5. **Security requirements.** A generated application handoff records principal/tenant boundaries, each operation's authn/authz policy, sensitive data classification, secret delivery, retention/deletion, audit-event minimization, abuse limits and deployment assumptions. Required controls have concrete implementation tasks and negative acceptance cases. Missing facts are blockers or explicit waivers, never inferred security.
6. **Dependency provenance.** Keep immutable lock identities, exact tools/versions and dated SCA results with scope. An external security plugin or scanner is optional infrastructure requiring actual availability/authorization; the current package should orchestrate evidence, not claim to supply a vulnerability database or certification.

## Acceptance pack for software the Studio helps create

No generated application was available to execute these checks. They are proposed workflow acceptance requirements that must be tailored to a real stack and deployed architecture.

| Concern | Required evidence before claiming implementation security | Representative negative case |
|---|---|---|
| Authentication/session | Actual framework middleware/configuration plus integration tests; cookie/token lifecycle reviewed where applicable. | Missing, expired and invalid credentials cannot access protected operations; logout/revocation behavior matches contract. |
| Authorization/tenant isolation | Object- and action-level enforcement at actual access paths; policy mapped to API intent. | A valid tenant A user cannot read/update/export tenant B's IDs, bulk endpoints, background jobs or cached objects. |
| Input/query/command handling | Bound schemas, parameterized database access, safe process invocation, bounded upload/archive handling. | Injection strings, traversal/archive escapes, malformed encodings, overlarge payloads and unsupported content types are rejected without unintended effects. |
| Secrets/privacy/logs | Secret selectors and deployment delivery reviewed; redacted audit/error paths; retention/deletion/recovery behavior tested. | Synthetic credentials and personal data do not reach shared logs, traces, exports or error responses. |
| Network/deployment | Actual IaC/runtime configuration, least-privilege identities and ingress/egress policy; approved rollout and recovery evidence. | Private services/storage are not inadvertently reachable; debug endpoints and admin routes require intended access. |
| Dependencies/artifacts | Resolved lock/SBOM, integrity identities and dated SCA/secret-scan scope. | Known applicable high-impact issues either block or have owned, time-bounded exceptions with compensating evidence. |
| Abuse/reliability security | Measured rate/resource limits and failure behavior at the real boundary. | Expensive unauthenticated requests, retries and parser workloads cannot bypass declared limits or leak data on failure. |

Security advice, code presence, static checks, local integration tests, runtime verification, independent review and residual-risk acceptance must remain separate reported states. No passing row implies certification or absence of unknown vulnerabilities.

## Actual execution evidence and limitations

The reviewer used shell/static source inspection (`rg`, numbered reads, clean commit/status), the managed environment readiness tool, the runtime skill, the architecture skill, and the repository's `skills/security-review/SKILL.md`. The managed environment reported current enforced restricted network policy and no configured credentials; no network action was needed. Skill instructions were treated as review workflow guidance, not proof of implementation.

| Check actually run | Result / scope |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 /workspace/sas-env/bin/python -m unittest discover -s tests -p test_audit_followups.py -v` | **FAILED:** 11 tests; 10 passed, 1 failed at `test_handoff_identity_distinguishes_canonical_and_projection_hashes`, line 101. E06-F04 explains the source-backed mismatch. |
| Same unittest command with `-p test_release.py -v` | **PASSED:** 42 tests. Includes symlink/special-file refusal, conflict/recovery, managed output ownership, renderer invocation stub behavior, bounded timeout, offline refs, full validator worker, SQLite allowlist, minimization and cache parity. This is scoped regression evidence, not a general security scan. |
| `node tests/test_workbench.cjs` | **PASSED:** 25 reported checks. Actual core/inline UI code in a minimal DOM model, not a browser engine. |
| `PYTHONDONTWRITEBYTECODE=1 /workspace/sas-env/bin/python /tmp/sas-expert06-counterexamples.py` | **PASSED reproduction harness:** E06-F01/F02/F03/F05/F06/F08 reproduced with temporary synthetic data. Also observed incomplete basic security-scheme/scope semantics. The harness returning 0 means the reproductions ran, not that those product behaviors are acceptable. |
| Independent projection fixture through `compile_plan` | E06-F04 reproduced omitted private roots, equal canonical/intermediate projection hash, nonmatching actual exported-project hash and empty changed-path report. |
| `architect_cli.py doctor` | Python 3.12.14; PyYAML 6.0.3, jsonschema 4.23.0, openapi-spec-validator 0.7.2; POSIX no-follow available; `mmdc: null`. |
| `python -m http.server --help` and browser config inspection | Confirmed all-interface default and repository-root serving configuration without starting a server. |
| Installed checker discovery | `pip_audit` and `bandit` unavailable. No installations or remote CVE lookup performed. |
| `git status --short` before and after tests | Clean; frozen source unchanged. |

Reproduction details are intentionally synthetic. The harness creates a fresh temporary project/source/cache; calls `compile_plan` on a protected interface and an externally attributed Accepted decision; runs `doctor` with its temporary project file as `--receipt`; empties a content-keyed cache entry; compares JSON Schema to native receipt validation; and validates an invalid OpenAPI security scheme with a synthetic password marker. It performs no remote actions and executes no inspected repository's application/build code.

**Not run / unavailable:** real browser security/XSS tests, real Mermaid renderer tests, network sandbox escape tests, external connector invocation, live implementation adapter tests, SAST/SCA/secret scans with specialized engines, remote penetration tests, production probes, signed-artifact verification, hardware/power-loss recovery, non-POSIX race testing, or privacy/compliance certification. No real credential was collected or printed. Dependency CVE status, external tool security, host enforcement effectiveness, and prompt-injection resistance across coding hosts remain unverified.

## Historical reconciliation and verdict

Preserve the demonstrated M04 filesystem controls (`IMPLEMENTATION_STATUS.json:48-58`) and M05 revision/publication approach. The 42 release regressions passed; committed-journal mismatch protection also passed. M12's minimization and authority separation are partially implemented, but E06-F03/F04/F08 limit the stronger acceptance interpretation (`IMPLEMENTATION_STATUS.json:151-162`). M31's minimized receipts avoid raw prompts/source as intended, while E06-F01 shows their output-ownership gap (`IMPLEMENTATION_STATUS.json:397-408`). This is an extension of verified controls, not justification for a rewrite.

**Verdict:** The offline toolkit has credible, honestly scoped local safeguards and should remain the foundation. It is suitable for careful local architecture work under the user's host permissions. Do not rely on the affected handoff's authentication readiness, its current projection identity, or its auxiliary writers for consequential automation until the verified defects are fixed. Native instruction export and future adapter execution need explicit trust-boundary contracts. Expanding execution/deployment powers before these repairs would increase exposure faster than assurance. No security certification or production-readiness claim is supported by this review.
