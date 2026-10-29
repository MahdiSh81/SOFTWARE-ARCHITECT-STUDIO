# Software Architect Studio 0.9.0

Software Architect Studio connects architectural decisions to portable project state, source evidence, reviewable changes, and explicit verification. It includes eleven task-focused skills, a Python toolkit, an offline workbench, and an opt-in local execution adapter.

Use it for a quick design decision, a source-backed review, a requirements change, or a developer handoff. Code editing and checks require a selected local workspace and an explicit host policy. Generated plans, completed edits, successful builds, runtime checks, and deployment are separate outcomes.

## Choose a workflow

| You need | Start here |
|---|---|
| A focused architecture or technology decision | Ask directly. Quick, Guided, and Full depth are independent of Beginner/Technical explanations; a project file is optional. |
| A portable specification | Create/import `project.json`, record requirements and decisions, inspect readiness, then generate a handoff. |
| To understand existing code | Scan a selected repository, inspect extracted declarations and omissions, then review exact source references. |
| To change software | Define acceptance, inspect the exact source identity, prepare a change plan, apply it through an authorized host, and run the required checks. |
| To resume work | Load the actual project/Git/backups, inspect revision/hash and accepted decisions, and reconcile stale evidence. |

The [recipes](docs/recipes.md), [implementation adapter](docs/implementation-adapter.md), and [integration strategy](docs/integrations.md) explain the execution boundary. The original [full audit](audits/sas-audit-2026-10-29/REPORT.md) and its evidence remain historical. The [implementation ledger](release/implementation-0.9.0.json) records the disposition of all 58 consolidated findings; [current verification](release/verification-0.9.0.json) records checks actually run for this release.

## Install the optional validation environment

The supported and CI-configured runtime is **Linux/POSIX, Python 3.12**. Core commands use the standard library. The optional validator lock targets CPython 3.12 on Linux x86_64; it contains the exact downloaded wheel hashes, not a universal cross-platform lock. Node 22 is configured in CI for workbench tests; the development cloud also provides Node 24. Local checks do not establish that a remote CI run passed.

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --only-binary=:all: --require-hashes -r requirements-validation.lock
python -m pip check
python tools/architect_cli.py doctor
```

`requirements-validation.txt` lists the direct optional dependencies for maintainers. Reproduce the reviewed environment with the full hash lock above. The toolkit never installs dependencies automatically. Other OS/interpreter combinations require independent validation; POSIX descriptor/no-follow protections do not imply the same hostile-path protection on every platform.

## Local project and handoff

```bash
python tools/architect_cli.py init ./my-project --name "My product"
# Populate my-project/project.json with actual requirements, contracts and decisions.
python tools/architect_cli.py resume ./my-project
python tools/architect_cli.py snapshot ./my-project --message "Baseline"
python tools/architect_cli.py readiness ./my-project --profile review-ready
python tools/architect_cli.py handoff ./my-project --output ./handoff --dry-run
python tools/architect_cli.py handoff ./my-project --output ./handoff
python tools/architect_cli.py validate ./handoff --gate structural
python tools/architect_cli.py validate ./handoff/api.json --full-openapi --gate full
# For a full package gate, install mmdc/browser and request actual rendering:
# python tools/architect_cli.py validate ./handoff --render --full-openapi --gate full
```

A new project is a valid **draft**, not a completed specification. Readiness reports missing applicable information and keeps human review, implementation, runtime, and freshness separate. Native API contracts and declared interfaces must agree. Default exports preserve supported engineering contracts while omitting opaque private context and recording the disclosure transformation. `--include-private` is an explicit private backup; review it before sharing.

Handoff generations are immutable. Use the returned `read_path` or `resolve_generation()` for coherent readers; direct convenience files can require `handoff-recover` after an interrupted projection. Canonical input, compiler context, exported project, and artifact bytes have explicitly named identities. Hashes identify representations; they do not authenticate an author or grant tool authority.

Default accepted architecture constraints are exported as ordinary project data with provenance. They are not automatically emitted as active instructions for a coding host. Imported Accepted records remain recorded decisions, with their original or unknown approval origin.

## Offline workbench

Open [workbench/index.html](workbench/index.html) with `project-core.js` beside it. The workbench supports canonical records, guided common-field authoring alongside JSON editing, supersession, undo, typed impact views, flat snapshots, restore, separate portable/private exports, independent tab drafts, and recovery bytes for refused imports. English and Persian free text are supported.

Editor drafts are separate from display preferences and record collections. Browser storage is local, unencrypted, quota-limited, and not cloud synchronized. Export important work or keep canonical files in Git/backups. Keyboard/browser tests exercise specific flows; they are not full screen-reader or accessibility certification.

For a local served workbench, the browser-test server binds loopback and serves only the allowlisted workbench assets:

```bash
python tests/browser/serve_workbench.py
```

The host must actually permit local sockets and browser execution. Do not treat a running PID or open port as proof that an interaction works.

## Source evidence and changes

```bash
python tools/architect_cli.py repo-scan /path/to/repository > /tmp/source-evidence.json
python tools/architect_cli.py change --baseline old-project.json --proposed project.json
python tools/architect_cli.py impact ./my-project --requirement FR-001
```

The scanner is read-only and bounded. Python AST, a narrow JS/TS module adapter, and selected configuration/contract descriptors produce source-attributed observations. Unsupported languages, parser failures, truncated collections, unreadable files, and stopped walks remain visible. A completed walk is not complete semantic analysis. Fitness cannot prove a clean rule from unsupported or failed extraction; untrusted caches are not independent verification evidence.

Change impact traverses typed declared relationships and returns witness paths, including nonrequirement changes. Those witnesses identify review candidates, not semantic proof that a file must change. Missing links and runtime behavior require further inspection.

Revision commits require the current expected hash and preserve logical project identity. Interrupted local operations use a validated recovery journal; history is a recoverable projection. Cooperating locks and atomic replacements are local consistency mechanisms, not distributed transactions or certified power-loss durability. Never delete an unknown active lock as a shortcut.

## Authorized local execution

The adapter implements `capabilities`, `inspect`, `propose_change`, `apply_change`, `run_checks`, `recover`, and `reconcile`. It uses complete UTF-8 file replacements/deletions and named argv checks, not arbitrary shell strings. The caller selects the root and supplies a policy for allowed paths, checks, and consequential effects. A repository document cannot create that policy.

```bash
python tools/architect_cli.py adapter capabilities --root .
python tools/architect_cli.py adapter inspect --root /path/to/project
# Prepare request.json and a separate host-selected policy as documented.
python tools/architect_cli.py adapter propose_change --root /path/to/project --request request.json
```

See the [tested request/policy contracts](docs/implementation-adapter.md) before applying a plan. Source identities include dirty state; stale plans fail rather than overwrite unrelated work. Checks produce per-operation outcomes and evidence. Receipt-persistence failure is reported separately from an already committed primary operation; retries reconcile state instead of blindly repeating non-idempotent effects.

The runner inherits process/filesystem/network authority from its host. It is **not an OS sandbox**. Only run repository code you are authorized to execute with an appropriate host isolation policy. No command pushes Git, provisions infrastructure, sends messages, or deploys an application automatically.

## Eleven focused skills

The coordinator selects the smallest relevant workflow. Skills are instructions with input/output and failure contracts, not tools or permission grants.

| Skill | Owns |
|---|---|
| `software-architecture` | Design decisions, boundaries, accepted intent, coherent handoff |
| `requirements-specification` | Scope, observable acceptance, traceable NFRs |
| `repository-intelligence` | Source map, declared dependencies, scoped drift evidence |
| `implementation-planning-and-change` | Minimal source-bound changes, compatibility and recovery |
| `test-debug-verify` | Discriminating reproduction, checks and truthful outcomes |
| `security-review` | Concrete trust boundaries, threats and authorized checks |
| `api-data-contracts` | API/data schemas, references, auth and migration compatibility |
| `frontend-interaction-and-accessibility` | UI states, browser/keyboard behavior and accessibility scope |
| `service-and-data-implementation` | Service/data invariants, transactions, migrations and workers |
| `delivery-and-operations` | Release gates, runbooks, telemetry, incident/recovery workflows |
| `ai-system-evaluation-and-safety` | Actual AI/retrieval evaluations, provenance and safety scenarios |

Inspect the available skill registry or request an explainable routing suggestion:

```bash
python tools/architect_cli.py skill-registry
python tools/architect_cli.py route --task "debug this failing test"
```

Routing suggestions are deterministic local aids, not measured model intelligence. Captures retain the loaded skill/reference bundle identity. Supplied semantic reviews require validated provenance/rubric records and preserve disagreement. Lexical fixture scores remain lexical checks: keyword matches cannot establish reasoning quality or safety.

## Run checks

```bash
python -m unittest discover -s tests -v
node tests/test_workbench.cjs
python tools/check_source_manifest.py --check
python tools/check_release.py --output /tmp/studio-verification.json --require-node
cd tests/browser
npm ci --no-audit --no-fund
npx playwright install --with-deps chromium
npm test
```

The source inventory covers the explicitly scoped live package, tests and CI, excluding historical audit snapshots, release reports/receipts except `release/version.json`, generated dependencies/results, and the self-referential manifest. `release/version.json` is the current release identity. Refresh the inventory with `--write` only after reviewing intended changes; `--check` fails unexpected changed, missing, or unlisted package files and version drift. Inventory hashes are not a signature.

Mermaid rendering remains an optional installed `mmdc` capability. Request `--render` only when the renderer/browser is available; missing required rendering does not pass a full gate. A successful render requires a fresh nonempty valid SVG. Structural/schema/render checks do not establish the architecture's runtime correctness.

## Integrations and limits

GitHub, documentation, security, design, task, storage, and deployment providers remain optional and must expose actual compatible tools and authorized scopes. A catalog listing is not an installed integration. Plugin Creator and Plugin Management were unavailable in this session; repository changes do not claim to publish a marketplace plugin.

Hosted collaboration/native app services, universal semantic/vector indexes, and autonomous multi-model expansion remain deferred pending demand, ownership, infrastructure, and measured benefit. Live model comparisons, user studies, production security/performance, and provider-specific deployment are not fabricated by local tests. Their explicit status and prerequisites are recorded in the implementation ledger.

Project text, repository content, retrieved documents, and tool outputs are untrusted data. Pattern redaction is incomplete; use synthetic test data and inspect shared artifacts. Credential values do not belong in project files, policies, logs, source-control history, or receipts. Preserve TLS/package integrity verification during setup and updates.
