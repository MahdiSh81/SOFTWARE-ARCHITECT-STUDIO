# Software Architect Studio 0.8.0

A skills-based architecture assistant with a local, portable engineering toolkit and offline workbench. This release implements the audit's integrity repairs and scoped local workflows. It preserves the existing plugin identity, audience, optional GitHub declaration and starter prompts. It is not a hosted MCP App or automatic repository/model execution service.

The 0.7.1 acceptance pass adds strict recovery-journal validation, no-clobber commit records and chronological resulting-revision history. It fixes first-save conflicts between blank tabs, failed-import recovery protection, Accepted-record editing consistency, complete backup transport bounds, required YAML parser gates and partial-directory validation. See CHANGELOG.md and release/verification.json.

## Start with the outcome

- **A focused decision:** ask the architecture question directly; quick/guided/full depth is independent of beginner/technical explanation.
- **Resume or assess a change:** import actual `project.json`, inspect revision/acceptance, compare baseline/proposal and trace explicit impact witnesses.
- **Prepare a handoff:** compile supported contracts/data/diagrams/ADRs/tasks and inspect exact completeness blockers and check results.

Open `workbench/index.html` directly. Keep `project-core.js` beside it. The workbench preserves the canonical project instead of reconstructing it from display names. It includes record editing, supersession, undo, impact/table/diagram source, 20 flat snapshots, restore, private-backup/current-only exports, recovery, session-only storage, independent tab drafts, accessible section navigation and Persian/English free text. No network calls occur. Local storage is unencrypted and not cloud-synchronized.

## Local CLI

Core commands use Python 3.10+ standard library; the tested hardened IO environment is Linux/POSIX. On non-POSIX platforms, preflight checks remain but hostile path-race protection is not claimed. Node is used only for optional workbench tests, not the CLI. Optional YAML/schema tools are pinned in `requirements-validation.txt`; `requirements-validation.lock` captures the isolated validated environment. The toolkit never installs them automatically.

```bash
python tools/architect_cli.py doctor
python tools/architect_cli.py init ./my-project --name "My product"
# Populate canonical project.json; preserve supplied accepted decisions and unknown fields.
python tools/architect_cli.py resume ./my-project
python tools/architect_cli.py snapshot ./my-project --message "Baseline"
python tools/architect_cli.py impact ./my-project --requirement FR-001
python tools/architect_cli.py change --baseline old-project.json --proposed project.json
python tools/architect_cli.py handoff ./my-project --output ./handoff --dry-run
python tools/architect_cli.py handoff ./my-project --output ./handoff
python tools/architect_cli.py validate ./handoff --gate structural
python tools/architect_cli.py validate ./handoff --render --full-openapi --gate full
python -m unittest discover -s tests -v
node tests/test_workbench.cjs
```

`schemas/project-v2.schema.json` defines a valid **draft**, not a complete implementation specification. The semantic validator also checks IDs/references and finite/transport bounds. A browser refuses numbers it cannot represent losslessly, unsupported versions and oversized data; it retains original recovery bytes instead of silently normalizing IDs or truncating records. Old UI-only backups cannot restore facts already lost by the old version; use retained bytes or an original portable project.

## Commands and scope

| Workflow | Commands | Boundary |
|---|---|---|
| Context/history | `init`, `resume`, `snapshot`, `recover`, `restore`, `commit` | Atomic project-file commit point, journal and cooperating local lock; no distributed concurrency/durability certification |
| Evolution | `diff`, `change`, `impact`, `freshness`, `evidence-delta` | Typed declared connectivity and observed scope; not semantic causality or runtime proof |
| Handoff | `handoff`, `handoff-recover`, `readiness` | `brief`/`draft`/`review-ready` profiles; independent completeness/structure/review/runtime/freshness dimensions |
| Source | `repo-scan`, `fitness` | Bounded regular-file static evidence; Python AST, narrow JS/TS module tokens and selected config/contracts; no repo install/build execution |
| Checks | `validate`, `data-check`, `doctor` | Scoped gates; optional installed full OAS/project-schema/render tools; generated allowlisted SQLite schema in memory only |
| Quality | `capture`, `evaluate`, `quality-summary` | Actual caller-supplied captures and deterministic/lexical checks; independent semantic review remains required |
| Decisions | `capacity`, `score`, `sensitivity`, `experiments`, `migration-plan` | Declared assumptions and proposed measurement/migration worksheets, not production tests or current vendor quotes |
| Research/reviews | `research-kit`, `review-plan` | Instruments/protocols; no interviews or agent dispatch performed |

Use `--help` for arguments. `--receipt PATH` before the command emits an explicit local minimized run record, without raw prompts/snippets. The repository cache is opt-in `--cache PATH`; delete it to purge cached extraction. It does not authorize new collection or make old conclusions current.

## Safe revisions and publication

Snapshot records the current revision, retains the message in a journal, and atomically replaces `project.json` with the next revision. That file is the authoritative commit point. Human history is recoverable projection; use `recover` after an interruption. `commit` and `restore` require the current expected hash. A conflicting draft is never silently overwritten. Stale locks are not automatically broken; inspect actual writer ownership rather than deleting an unknown lock blindly.

Handoff builds an immutable generation and atomically publishes `.handoff-current.json`. **Use the returned `read_path` or `resolve_generation()` for coherent readers.** Direct legacy files are convenience projections and may need `handoff-recover` after an interrupted projection. Unowned/human-modified outputs are preserved; unchanged stale managed ADRs are removed under hash checks. Generation manifests identify exact outputs; recursive self-hashes are explicitly excluded. Multi-file atomicity, hostile-writer locks and power-loss durability are not implied.

Default handoff excludes opaque root extensions/private history and redacts obvious credential values. Detection is incomplete; inspect exports before sharing. `--include-private` explicitly retains full canonical context and sensitive values for a private backup. Current portable browser exports retain canonical data; a private workbench backup additionally includes selected history/UI state. Deleting local copies does not delete downloads/Git/remote backups.

## Validation truthfulness

`validate` produces one terminal result per applicable check, scoped input identity and a separate gate decision. JSON/YAML share the same OpenAPI structural semantics; external refs are blocked. A requested permitted real renderer runs independently of heuristic warnings. Missing required tools, timeouts and blocked operations are never green gates. Full schema validation and rendering remain optional installed capabilities, not claims derived from JSON parsing.

`evaluate` defaults to report-only. Use `--gate --min-pass 100` for an explicit CI predicate. Patterns run in killable workers; direct character/word/sentence limits replace a newline-only brevity proxy. A perfect example score is not a model-quality result. Capture real responses with model/skill/source/tool provenance and calibrated human reviews before claiming improved reasoning. Product interviews and specialist-vs-single-pass comparisons have not been fabricated.

## Recommendation coverage

See `IMPLEMENTATION_STATUS.json` and `skills/software-architecture/references/implementation-status.md` for all M01–M40. Code/workflow slices are distinguished from unavailable evidence. M37 includes a research instrument; real user observations remain pending. M14/M35 include capture/review protocols; measured comparative quality remains pending. M38–M40 remain deliberately deferred, matching the report: hosted multi-user/native app services, universal semantic indexing/graph databases, and multi-model autonomous expansion require a separate demonstrated need and infrastructure.
