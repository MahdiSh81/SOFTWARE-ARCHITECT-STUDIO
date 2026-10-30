# Expert 02 — Chief Software Architect and System Design Review

**First independent pass, 2026-10-29. Baseline:** `/workspace/SOFTWARE-ARCHITECT-STUDIO`, clean commit `83812e1d31c17ed857be8d2fb5c98126a8ccb5c8`. **Scope:** architecture, module boundaries, data/contract authority, change propagation, reliability, errors, extension seams and migration. No other reviewer reports were read. No child agents were created. This review inspected source and ran safe local probes; it did not change the checkout, install tools, publish, reconfigure or execute an inspected application's code.

## Recommendation and verdict

Retain the local modular architecture and repair its contract boundaries before broadening execution. Its main weakness is overlapping representations that disagree while separate checks appear satisfactory. Prioritize an authoritative contract resolver, equivalent project validation across runtimes, composable storage budgets and typed operations/results. A rewrite or distributed platform is unjustified.

**Verdict:** suitable as a scoped architecture assistant and local toolkit with disclosed limits; **not ready to serve as the authoritative end-to-end software delivery coordinator** until P1 integrity repairs and a real, permissioned execution adapter have demonstrated acceptance. The defects are repairable incrementally.

## Current architecture and strengths

The source establishes a host-invoked plugin with seven instruction skills, a separately invoked Python CLI, and a separately opened offline browser workbench. It has conditional host GitHub support, no native execution service, and contract-only integration records. Domain validation, change graphs, revision storage, artifact compilation, source extraction and validation are separate modules. The browser independently implements core domain operations.

An AST inspection found **39 local import edges across 16 Python modules, without cycles**. Preserve canonical intent, explicit graph witnesses, budgeted read-only extraction, POSIX no-follow IO, expected-hash commits, validated recovery journals, immutable handoff generations and recoverable projections. These are sound local patterns, with honestly disclosed cooperating-writer and durability limits. Detailed current/target maps, interfaces, alternatives and migration stages are in `expert02-architecture-notes.md`.

## Prioritized findings

### E02-F01 — P1 — Verified defect: two HTTP contract authorities yield contradictory green handoffs

**Evidence:** `artifact_compiler.py:65–89` preserves native `api_contract`; when it exists, each declared HTTP interface is checked only for method/path presence at lines 78–80. The same compiler writes the original `interfaces` to `contracts.json` at line 90. `validation_engine.py:324–331` checks operation coverage only, not equivalent operation semantics.

**Reproduction:** a valid canonical project contains `/count GET` twice: `interface.operation` specifies JSON string, and native OpenAPI specifies JSON integer. Both have the same operation ID, explicit public security and valid responses. Compilation reports `review-ready/profile_satisfied=true`; `contracts.json` says string, `api.json` says integer; structural validation returns `policy_ok=true` and correspondence `passed` with detail `supported operation coverage only`. Evidence: `expert02-probes/results.json`, `contract_divergence` and the retained contradictory handoff.

**Root cause and impact:** a native API and an embedded operation are both accepted as supplied intent; there is no declared precedence/conflict policy shared by readiness, compiler and validator. Different implementers can follow contradictory outputs. 

**Recommendation E02-R01:** resolve each HTTP interface exactly once through a pure `resolve_contracts(project)` function. A native reference can own the operation and a per-interface duplicate must either be absent or match a documented normalized subset. Preserve native authoring bytes separately if required; never silently overwrite supplied semantics. Reject conflict with field-level locations before creating a generation. Distinguish operation coverage from operation correspondence.

**Acceptance E02-A01:** the retained counterexample is rejected before publication; supplied native-only contracts compile; equivalent duplicates pass; conflicts in response, request, security, parameters and operation ID produce precise findings; all artifacts use the resolved operation and current coverage checks remain scoped truthfully.

### E02-F02 — P1 — Verified defect: valid project size does not compose into the revision envelope

**Evidence:** `safe_io.py:10,75–77` applies one 5 MiB limit to all written files; `project_model.py:74–76` admits canonical documents up to that limit. A commit embeds the entire new object inside a metadata-bearing, additionally indented journal (`revision_store.py:86–95`).

**Reproduction:** a canonical object of 5,242,860 bytes, 20 bytes below the 5,242,880-byte limit, passes `project_checks`. `commit_project` fails with `ValueError: output byte budget exceeded` while writing the prepared journal. Current project remains unchanged and no journal is written. This is a save failure, not observed canonical corruption. Evidence: `expert02-probes/results.json`, `large_project_commit`.

**Recommendation E02-R02:** make budgets representation-specific and compositional: project payload, journal, snapshot and artifact budgets. Preflight the complete serialized operation before any mutation. The journal could reference a separately written immutable payload by hash; alternatively, use a bounded envelope limit large enough for the supported payload and metadata. A larger envelope alone must account for indentation growth, not only a guessed fixed overhead. Retain per-file and total-output limits.

**Acceptance E02-A02:** all accepted canonical sizes can commit/snapshot/restore at documented limits, including deep/wide JSON that grows when embedded. Over-budget operations fail before creating snapshots/journals/generations. Injected failures preserve current bytes and recoverable state. Browser backup envelope limits remain separately documented.

### E02-F03 — P1 — Verified defect: published schema and both lightweight validators disagree

**Evidence:** the published `$defs.record` declares reference-array fields, including `tasks`, as arrays of strings (`schemas/project-v2.schema.json:331–374`). Python validates references only for `LINKS` entries (`project_model.py:12–16,56–62`); JavaScript repeats that subset (`project-core.js:5,30`). Known fields outside those per-group links avoid even their structural field checks.

**Reproduction:** `requirements[0].tasks=[{"malformed":"not a string"}]` passes both Python `project_checks` and JavaScript `errors`; installed `jsonschema.Draft202012Validator` rejects `/requirements/0/tasks/0`. Evidence: `expert02-schema-probe.json` and tool output. 

**Recommendation E02-R03:** define one small contract metadata source for known field types, allowed links, lifecycle values and endpoint groups. Derive published schema plus Python/JS core checks or verify them against a shared generated conformance corpus. Require the lightweight core to satisfy the declared structural subset. Unknown extension preservation must remain intact.

**Acceptance E02-A03:** a shared corpus contains positive and negative cases for every published known field on every applicable record, malformed/dangling references, unsafe numeric browser inputs and unknown extensions. Core acceptance implies published-schema validity except explicitly enumerated and tested host-specific restrictions; equivalent portable inputs produce matching validity results in Python and Node.

### E02-F04 — P2 — Verified regression and evidence-backed identity ambiguity: projection hash names an intermediate representation

**Evidence:** `compile_plan` computes `projection_hash` immediately after recursive minimization (`artifact_compiler.py:40–44`). Later it removes fields with an export allowlist and replaces `notes` (`artifact_compiler.py:99–104`), without recomputing a digest for exported `project.json`. Identity and redaction reporting occur at lines 105–110. File artifact hashes themselves are correct in the inspected path.

**Observed regression:** existing `test_handoff_identity_distinguishes_canonical_and_projection_hashes` fails (`tests/test_audit_followups.py:91–102`). With the rich fixture, canonical and declared projection hashes both equal `923bd6ec…`, but emitted project digest is `7ef6716f…`. `custom_extension` and `api_contract` are absent in emitted project and redactions are `[]`. Evidence: `expert02-projection-probe.json`.

**Interpretation:** identical hashes are legitimate when the identified representations are identical. The problem is ambiguous representation identity: the claimed projection is an intermediate compiler object that is not emitted as such, while omissions are not listed as changed paths. Do not claim a cryptographic failure or fix the test by forcing hashes to differ unconditionally.

**Recommendation E02-R04 / acceptance E02-A04:** name `canonical_input_hash`, `compiler_context_hash` and `exported_project_hash` separately when their representations differ; define canonicalization/version and removal/redaction reports. Assert each hash against its exact representation, including allowlist removals. Verify full private exports and default minimized exports. Existing artifact-byte hashes remain independent and correct.

### E02-F05 — P2 — Demonstrated limitation: change seeds and returned impact omit material record classes

**Evidence:** `change_bundle` seeds traversal solely from changed requirements (`graph_engine.py:56–63`). `impacts` traverses optional nodes but constructs returned affected groups only from core `GROUPS` (`graph_engine.py:28–42`).

**Reproduction:** changing `ADR-001` with `TASK-001.decisions=["ADR-001"]` yields a correct decision delta but empty task impact in both baseline and proposed analyses. Separately, a verification linked to `FR-001` is reached by traversal and absent from `unreached_records`, yet never appears in `affected`. Evidence: `expert02-probes/results.json`, `decision_change_impact` and `verification_impact`.

This is a scoped implementation limitation; the tool does not claim semantic impact or automatic revalidation. It nevertheless creates an incomplete basis for the target change workflow.

**Recommendation E02-R05 / acceptance E02-A05:** expose generic typed impact seeds `{group,id}` and let change analysis seed all changed/removed supported records, retaining baseline/proposal views and evidence witnesses. Return optional groups or explicitly declare filtered groups. Tests must cover ADR-only/interface-only/data-only changes, removed nodes, verification reruns, cycles and order independence. Connectivity must continue to mean review scope.

### E02-F06 — P2 — Verified defect: readiness does not share native contract resolution

**Evidence:** `artifact_compiler.py:16–20` requires per-interface `operation` and checks per-interface/root authentication; it does not inspect a matching native operation. An explicit native operation `security: []` is a valid public decision but is ignored there.

**Reproduction:** removing duplicate per-interface `operation` and `authentication` from the valid `/count` native project produces `operation` and `authentication` blockers, even though the native operation supplies complete responses and explicit public security. Conversely a completely empty new project passes `review-ready` with completeness `specified within supported scope` because there are no records to create obligations. The latter is a vacuity/product policy gap, not proof that every project must contain every artifact.

**Recommendation E02-R06 / acceptance E02-A06:** readiness consumes E02-R01 resolved contracts and an explicit applicability/expected-deliverables profile. Native and embedded equivalent contracts have identical obligations. Empty/incomplete applicability is `unknown` until scope is declared; documented intentionally empty/not-applicable profiles may pass. Do not add compulsory full-project paperwork to quick advice.

### E02-F07 — P2 — Verified defect: SQLite check errors escape the machine-readable CLI boundary

**Evidence:** `workflow_tools.py:46–64` executes generated CREATE TABLE statements without translating `sqlite3.Error`. The CLI exception tuple excludes SQLite errors (`architect_cli.py:101–102`).

**Reproduction:** two valid model records with different IDs but the same SQLite table name produce `sqlite3.OperationalError: table "same_name" already exists`, a raw traceback, empty stdout and exit 1 instead of the CLI's structured error. Evidence: `expert02-sqlite-input.json`, `expert02-sqlite-result.json`. In-memory connection closes through `finally`; no external database is modified.

**Recommendation E02-R07 / acceptance E02-A07:** validate table/column conflicts and translate adapter exceptions to a typed operation failure with record locations. Keep unexpected programmer errors distinguishable from bad input; do not simply suppress all exceptions. Duplicate table/column names, impossible PK declarations and subprocess failures must give bounded stable JSON and documented exit semantics, while normal data-check passes remain unchanged.

### E02-F08 — P2 — Evidence-backed risk: project identity is optional and not enforced across a revision chain

**Evidence:** Python `new_project` emits UUID `project_id` (`project_model.py:18–21`), JS `blank` does not (`project-core.js:35`), published schema does not require or type it, and commit checks only expected current hash, not logical project identity (`revision_store.py:78–95`).

**Reproduction:** commit a fresh Project B object over initialized Project A with A's expected hash; B's distinct project ID becomes revision 2 while revision 1 remains A. This is permitted behavior today, not a violated published immutable-ID rule. Evidence: `expert02-probes/results.json`, `cross_project_commit`.

**Risk/response:** a local directory is adequate current ownership context, but host integrations, task receipts and cross-project imports need a stable identity to prevent accidental record/history mixing. Define explicit `fork/import/replace-project` semantics before using IDs for integration routing. Preserve legacy imports and unknown fields; do not silently assign a new identity on every open.

**Acceptance E02-A08:** new projects from both runtimes have stable IDs; same-project commits preserve identity; cross-project replacement is an explicit typed operation; legacy identity migration is reviewable, deterministic after persistence and lossless. Project identity grants no permission.

### E02-F09 — P1 for lifecycle expansion — Verified missing capability in inspected scope: adapter contract has no execution/reconciliation implementation

**Evidence:** `docs/implementation-adapter.md:2–6` specifies capabilities/inspect/propose/apply/checks/recover but explicitly identifies itself as unconnected. `integration_contracts.py:1–5` validates records only; no CLI command uses it (`architect_cli.py:6–14,57–97`). The minimized local `--receipt` record is a different summary format, with counts rather than source-bound check details (`workflow_tools.py:96–101`), and must not be presented as the verification-receipt contract.

**Consequence:** current source does not implement orchestration from accepted design through multi-file apply/build/test/deploy. A capable host can perform those operations independently; that is a conditional external capability, not a demonstrated Studio service. This is not a defect against the current documented local toolkit boundary.

**Recommendation E02-R09:** implement one optional host adapter end to end before designing a universal dispatcher. Bind capability/version, schema, source identity, permission class, operation ID and terminal status; validate result before proposing canonical updates. Keep read-only inspect and change preparation useful without an executor. Preserve `planned/implemented/built/tested/runtime-verified/deployed/partial/unknown` separately. No receipt may grant authority.

**Acceptance E02-A09:** a fixture repository workflow demonstrates inspect → bounded plan/diff → source-hash-conflict refusal → authorized apply → build/check → validated receipt → reconciliation proposal, including timeout, lost-response, partial-write and unavailable-adapter cases. No replay of non-idempotent operations without reconciliation. No synthetic passed tests or deployments are inferred from artifact generation.

### E02-F10 — P2 — Improvement opportunity: useful modules still combine policy, pure contracts and effects

**Evidence:** domain `project_model` imports serialization/hash from filesystem module `safe_io`; compiler imports contract constants/checks from a module also owning subprocess/renderer/optional-package orchestration; static scanner imports YAML process parsing from that same validation module (`project_model.py:4`; `artifact_compiler.py:5–7`; `repository_evidence.py:54–61`; `validation_engine.py:203–229`). `workflow_tools` combines SQLite execution, research, model capture, scenario calculations and run summaries. Semicolon-dense source makes ownership/error review harder, despite short file counts.

**Recommendation E02-R10:** a small internal package refactor, preserving compatibility facades: `codec`, `domain/contracts`, `application`, and `adapters` with readable formatting. Extract a shared pure contract resolver, validation metadata and typed results first; split other files only when a demonstrated change needs the seam. No dependency inversion framework or service mesh is needed.

**Acceptance E02-A10:** source-level dependency rules prevent domain imports of process/filesystem adapters; existing CLI/result compatibility and regression corpus pass; precise adapter exceptions translate at one application boundary; no extra hosted runtime is required for local use.

## Architecture decision

**Proposed:** retain a modular local core. Add a pure shared contract resolver and validation metadata, typed application operations, explicit project/source identities, and optional effect adapters. Preserve existing CLI/workbench import/export and local commit points. One host execution adapter should prove a complete workflow before universal orchestration is considered.

**Alternatives:** incremental fixes have the lowest compatibility risk and should precede a targeted package refactor. A rewrite would replace working recovery/IO safety without demonstrated benefit. Microservices, hosted collaboration and a graph platform add infrastructure and distributed consistency costs unsupported by current demand evidence.

**Migration order:** contract consistency and explicit identities (R01/R03/R04/R06), storage budgets/errors and project identity policy (R02/R07/R08), typed change seeds and internal dependency seams (R05/R10), then one optional execution integration (R09). Every phase preserves old inputs and has counterexample-based acceptance. No proposed change was applied.

## Actual verification and limitations

Executed on Python 3.12.14 with bytecode disabled: `architect_cli.py doctor`, Python AST/import inspection, safe local counterexamples, and installed jsonschema 4.26.0. Node checked the JS counterexample. Git, rg and numbered source reads established evidence. Architecture/cloud-runtime skills and managed environment status were read. No network retrieval or installation occurred.

- `unittest discover -s tests -p test_project_workflows.py -v`: **12 passed**.
- `unittest discover -s tests -p test_audit_followups.py -v`: **10 passed, 1 failed**, the identity distinction test.
- Counterexamples and results are retained in `expert02-probes/results.json`, `expert02-schema-probe.json`, `expert02-projection-probe.json`, `expert02-sqlite-input.json`, and `expert02-sqlite-result.json`.
- Git remained clean after probes. Full suite, live browser, real rendering, full OpenAPI validation, live execution integration and power-loss recovery were **not run**. `mmdc` and openapi-spec-validator were unavailable.

Unknowns include host activation quality, actual connector availability, team workloads, SLOs/cost, reasoning quality, collaboration demand and adversarial writers. Static acyclicity is not runtime isolation. The supporting proposed Mermaid source was not rendered. Findings apply to the pinned checkout and observed environment.

**Final judgment:** repair consistent representations and reliable persistence, then prove one integration; preserve the existing local architecture.
