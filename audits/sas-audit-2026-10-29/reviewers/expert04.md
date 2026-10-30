# Expert 04 — Repository intelligence, code understanding and modernization

## Independent first-pass disposition

**Verdict: retain the small static-evidence architecture and declared graph, repair the evidence-state and change-seeding defects before treating repository fitness or change bundles as reliable engineering gates, and expand adapters only against measured repository tasks.** The inspected implementation is useful for bounded import/configuration collection and declared connectivity. It does not yet constitute semantic code understanding, automated modernization, a call graph, or an implementation adapter. Its documentation generally states those boundaries accurately.

This was a real independent specialist pass. I read the assignment, target source, relevant skill and documentation, then ran my own fixtures and selected existing tests. I did not read other reviewers' reports or delegate work before completing this report. No plugin installation, network research, publication, checkout modification, inspected repository execution, or configuration change was performed.

- **Source identity:** `/workspace/SOFTWARE-ARCHITECT-STUDIO`, Git `83812e1d31c17ed857be8d2fb5c98126a8ccb5c8`; clean before and after this pass. The imported toolkit identifies itself as `0.8.0` in [project_model.py](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/project_model.py:6). The cloud skill package read by this reviewer identifies itself as `0.7.2`; that package is workflow guidance, not a substitute for inspecting this checkout.
- **Runtime actually used:** `/workspace/sas-env/bin/python`, Python `3.12.14`, with `PYTHONDONTWRITEBYTECODE=1`. All fixtures, caches, logs and reports are outside the checkout under this reviewer's evidence directory.
- **Relevant instructions applied:** local `skills/repository-intelligence/SKILL.md`, local change/evidence references, and the available software-architecture/cloud-runtime skills. Managed environment status was inspected; no network operation was needed.
- **Primary inspected code:** `repository_evidence.py`, `graph_engine.py`, `workflow_tools.py`, `project_model.py`, `safe_io.py`, `architect_cli.py`, related schemas, integration contracts/documentation, and targeted scanner/graph tests.

## Actual source collection and tests

The actual CLI scan was:

```text
PYTHONDONTWRITEBYTECODE=1 /workspace/sas-env/bin/python \
  /workspace/SOFTWARE-ARCHITECT-STUDIO/tools/architect_cli.py \
  repo-scan /workspace/SOFTWARE-ARCHITECT-STUDIO --deadline 20 --limit 1000
```

It read **47 files / 324,683 bytes**, visited **111 entries**, discovered **47 eligible files**, extracted **206 declarations / 203 edges**, completed enumeration and recorded no budget stop. Its `coverage` remained `partial` because it recorded exclusions and unsupported files. Observed suffixes were 21 Python, 23 JSON, one JS, one YAML and one YML. It correctly did not claim a commit pin: observations say `unpinned local tree`. The immutable Git identity above was established separately using Git.

The scan omits Markdown, HTML and `.cjs`; on this product that includes architecture instructions/documentation, the workbench HTML and browser/test files. These omissions are recorded, not hidden. Consequently the 47-file scan alone cannot reconstruct this product's complete architecture or verify its complete implementation. Evidence: [checkout-scan.json](/workspace/sas-audit-2026-10-29/reviewers/expert04-evidence/checkout-scan.json).

**Ten selected existing regression tests passed**, covering cyclic/order-independent graph closure, removed requirements, CI prioritization among irrelevant files, Python comment false routes, special-file/entry bounds, cache dependency-edge parity, preservation of an unrelated cache-path file, JS comment/template exclusions, requirement impact, and file/line drift evidence. The exact names and current output are in [targeted-unittest.txt](/workspace/sas-audit-2026-10-29/reviewers/expert04-evidence/targeted-unittest.txt). This is not a claim that the entire suite or live model quality was tested by this reviewer.

The reproducible independent fixture runner is [expert04-probes.py](/workspace/sas-audit-2026-10-29/reviewers/expert04-probes.py). Run it with the Python and environment prefix above. Its cases persist source files, scan results and summaries in [probe-results.json](/workspace/sas-audit-2026-10-29/reviewers/expert04-evidence/probe-results.json). Real CLI invocations of `impact`, `fitness`, `evidence-delta`, and a cache-overflow `repo-scan` were also run; [cli-probes.json](/workspace/sas-audit-2026-10-29/reviewers/expert04-evidence/cli-probes.json) records command arguments, return codes, stdout and stderr for the last three. No inspected application source was executed.

## Findings

### E04-F01 — Fitness treats a byte read as sufficient extractor evidence

**Classification:** verified defect. **Priority/severity:** P1 / high, because a purported architecture-rule result can become a false pass.

[repository_evidence.py:187](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/repository_evidence.py:187) computes counterexamples from available edges, then builds `scope` from any observed matching file. Line 189 returns `satisfied-in-scope` whenever such a file exists and no stored edge matches. It does not require a supported import adapter, successful parsing, complete extraction, or nontruncated dependency coverage. This contradicts the explicit M27 acceptance that missing extractor evidence yields unknown in [IMPLEMENTATION_STATUS.json:358](/workspace/SOFTWARE-ARCHITECT-STUDIO/IMPLEMENTATION_STATUS.json:358).

Independent counterexamples:

1. `main.go` contains `import "forbidden/secret"`. The file has no Go adapter, explicitly receives `filename/content identity only; no language adapter`, yet `forbid_import(source_prefix="main.go", target_prefix="forbidden")` returns `satisfied-in-scope`. The CLI also returns exit 0 for that result.
2. `broken.py` contains `import forbidden` followed by invalid Python. The cold scan records a parser error, but fitness still returns `satisfied-in-scope`.
3. `a.py` has 100 `import os` lines followed by `import forbidden`. The scan honestly records one declaration omitted by its 100-item quota; fitness still returns `satisfied-in-scope` while the omitted line is the violation.

The note that no *global* compliance is inferred does not repair the missing evidence inside the selected file scope. See `unsupported_language_fitness`, `parser_cache`, and `import_quota_fitness` in the probe results.

**Recommendation E04-R01:** define rule-specific extraction coverage; return `unknown` when any relevant file lacks successful, complete import extraction. Return a violation whenever a supported exact counterexample is known, even if other scope is incomplete. Only use `satisfied-in-scope` for the declared evaluated scope with explicit unresolved/omitted coverage. Add an optional fitness gate that makes the caller choose an unknown policy; current CLI behavior is report-only, with no nonzero violation/unknown policy.

**Acceptance:** all three cases above return `unknown` absent a known counterexample; a fully parsed supported clean file returns `satisfied-in-scope`; a supported violating file returns `violation` with path, span, syntax and content identity. The result identifies evaluated and unevaluated files separately.

### E04-F02 — Cache hits erase parser-error and unsupported-adapter metadata

**Classification:** verified defect. **Priority/severity:** P1 / high.

At [repository_evidence.py:134](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/repository_evidence.py:134), a hit restores only `items` and `edges`. Parser status lives on `obs['extraction']` and in `omissions` inside the miss branch at lines 140–141. The cache entry stored at line 144 contains neither. A failed parse is cached as an indistinguishable pair of empty lists.

The unchanged `broken.py` fixture has cold `coverage="partial"` and a parser-error omission. Its immediate warm scan reports `coverage="complete within supported static scope"`, no omission and no extraction error. Both scans have the same source bytes and source fingerprint. The current cache test asserts dependency-edge equality only ([test_release.py:161](/workspace/SOFTWARE-ARCHITECT-STUDIO/tests/test_release.py:161)); it does not check extraction status, omissions or coverage. The same storage shape drops the explicit no-language-adapter observation on warm hits.

**Recommendation E04-R02:** cache the complete bounded extraction result, including terminal status, diagnostics, adapter applicability, completeness and omitted counts, then reconstruct identical semantics on hit. Version this entry schema and fingerprint adapter/configuration identity independently of the overall toolkit release.

**Acceptance:** cold and warm scans agree on extraction status, diagnostics, omissions, completeness and emitted evidence, excluding timing/capture/cache counters. Invalid source never becomes complete solely because the cache is warm. Adapter upgrades invalidate only affected entries. Include syntax failure, unsupported language, truncation and descriptor failure fixtures.

### E04-F03 — Change bundles omit impacts for interface/component/decision-only changes

**Classification:** verified defect in change analysis completeness. **Priority/severity:** P1 / high for implementation-change handoffs.

`project_diff` correctly detects all core and optional record changes at [graph_engine.py:47](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/graph_engine.py:47), but `change_bundle` seeds both impact traversals exclusively from changed requirement IDs at lines 57–61. The public `impact` interface likewise accepts only requirement IDs at lines 22–27. A changed interface, schema, component, decision, task or relationship with unchanged requirements does not seed any graph traversal.

The fixture changes `API-001.path` from `/records` to `/records/v2`. `TASK-001` explicitly references that interface. The bundle correctly says interface `API-001` changed, but `changed_requirements=[]` and all baseline/proposed affected lists are empty. The generic API-compatibility review-obligation string remains present; it does not identify the already declared downstream task. Evidence: [interface-only-change.json](/workspace/sas-audit-2026-10-29/reviewers/expert04-evidence/interface-only-change.json).

**Recommendation E04-R03:** introduce an internal typed-seed traversal taking `{group,id}`; retain requirement CLI compatibility. Seed the baseline from removed/changed records and the proposal from added/changed records in every supported group. Treat changed relationships as an explicit review delta and evaluate their old/new endpoint neighborhoods. Distinguish directly changed records from transitive candidates and manual-review gaps.

**Acceptance:** an interface-path or operation change reaches declared consumers/tasks; schema changes reach declared readers/writers/tasks; component-only changes reach dependents; removed records retain baseline witnesses; added/removed edges receive explicit review coverage; no-change bundles have no seeds. Cycles and order independence continue to pass. An empty impact set must explicitly distinguish no seeds from analyzed seeds with no declared dependents.

### E04-F04 — Dependency-edge truncation can be silent

**Classification:** verified defect. **Priority/severity:** P2 / medium.

At [repository_evidence.py:149](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/repository_evidence.py:149), only the first 100 edges per file are emitted. Line 150 reports a quota omission only when `len(items)>100`. Descriptors can have many edges but few declarations.

A supported `jobs` descriptor containing one consumer with 101 `needs` entries produces one declaration and exactly 100 dependency edges, `coverage="complete within supported static scope"`, and no omissions. The last dependency is lost. Evidence: `silent_edge_quota` in the probe results and [edge-quota-scan.json](/workspace/sas-audit-2026-10-29/reviewers/expert04-evidence/edge-quota-scan.json). The associated broad fitness result is included in the raw fixture, but the defect established here is lost dependency evidence; a jobs dependency is not itself a Python/JS import.

**Recommendation E04-R04:** account for declaration and edge quotas independently and expose extracted/emitted/omitted counts by file and adapter. Mark affected relation coverage partial; record the exact stop reason.

**Acceptance:** the 101-needs fixture reports one edge omitted; boundary cases 99/100/101 reconcile; rules that depend on the omitted relation cannot pass through absence. Total-output quotas must be explicit in addition to per-file quotas.

### E04-F05 — Descriptor failures and unsupported manifest formats are indistinguishable from successful empty extraction

**Classification:** verified defect for invalid supported JSON; demonstrated limitation for other listed manifest formats. **Priority/severity:** P2 / medium.

[_descriptor at repository_evidence.py:54](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/repository_evidence.py:54) parses only JSON and YAML. It catches `Exception` and returns empty lists at line 61. A malformed `package.json`, YAML timeout, unavailable YAML parser, nonmapping document, and a valid document with no supported declarations all look the same to the caller. Listed manifests such as `pyproject.toml`, `requirements.txt`, `go.mod`, `Cargo.toml`, `pom.xml`, Gradle, Dockerfile and Makefile are prioritized but have no corresponding semantic parser in this function ([lines 9, 137–140](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/repository_evidence.py:9)); they also lack the no-adapter marker used for unsupported source languages.

A fixture containing malformed `package.json` plus valid Python TOML/requirements dependency declarations yields three observed files, no declarations, no omissions and `complete within supported static scope`. The parser failure is not disclosed. See `descriptor_failures` in the probe results. Reading/prioritizing these files is useful; the missing terminal status makes it impossible to tell what was actually analyzed.

**Recommendation E04-R05:** return a typed extraction envelope (`parsed`, `unsupported`, `failed`, `timed_out`, `partial`) and bounded diagnostics. Add small demand-backed manifest adapters first: Python `tomllib` for project dependencies and conservative requirements syntax, package workspaces, then selected actual monorepo manifests. Keep unsupported features explicit rather than treating them as empty.

**Acceptance:** malformed JSON/YAML remains failed on cold and cached scans; unavailable parser and timeout remain distinct; every eligible manifest has an explicit adapter/applicability status. Supported dependencies cite their actual source location or a clearly labeled whole-document span.

### E04-F06 — Python relative import identity is discarded

**Classification:** verified evidence-loss defect; resolution remains a separate scoped capability. **Priority/severity:** P2 / medium.

At [repository_evidence.py:25](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/repository_evidence.py:25), an `ImportFrom` emits only `node.module or ''`. It discards `node.level` and imported names. `from . import forbidden` becomes `target=''`; the information needed to identify the declaration is gone even though Python AST supplied it. `from ..domain import x` and `from domain import x` are likewise collapsed to the same target.

The actual `pkg/consumer.py` fixture contains `from . import forbidden`, but its edge target is empty and fitness with target prefix `forbidden` reports satisfied. Resolving that to an absolute module requires package/root knowledge; preserving the literal syntax does not. Evidence: [relative-python-scan.json](/workspace/sas-audit-2026-10-29/reviewers/expert04-evidence/relative-python-scan.json).

**Recommendation E04-R06:** preserve `module`, relative `level`, imported names/aliases and raw declaration span. Add an optional conservative package resolver that reports `resolved`, `ambiguous` or `unresolved`, with package roots from manifests/caller configuration. Rules must declare whether they match raw syntax, normalized module IDs, or resolved local files.

**Acceptance:** absolute and relative imports remain distinguishable; `from . import forbidden` retains the symbol and relative level; namespace packages, `src` layouts and multiple monorepo roots receive tested ambiguity behavior; unresolved edges produce unknown rule coverage instead of disappearing.

### E04-F07 — JS/TS token scanning attributes an import to an unrelated preceding export

**Classification:** verified false observation inside the advertised static-module subset. **Priority/severity:** P2 / medium.

At [repository_evidence.py:43](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/repository_evidence.py:43), each `import`/`export` token searches up to 80 following tokens and eight lines for `from`. It stops on a semicolon but not on a new statement/import declaration. In valid semicolon-free TypeScript:

```typescript
export const marker = 1
import x from "forbidden";
```

the scan emits two module edges: a false one on line 1 and the real one on line 2. Both claim `JS/TS static module token declaration`. Evidence: [js-bleed-scan.json](/workspace/sas-audit-2026-10-29/reviewers/expert04-evidence/js-bleed-scan.json). The unresolved classification correctly avoids claiming symbol resolution, but the declaration location itself is wrong.

**Recommendation E04-R07:** tighten the small recognizer to supported import/export grammar and statement boundaries, or use an explicitly optional real syntax parser where the host supplies one. Unsupported/dynamic/regex/template forms should remain unknown. Do not expand this into a whole-language hand-written parser.

**Acceptance:** the example emits exactly the line-2 import; test semicolon-free exports, multiline import/export-from, side-effect imports, comments, templates, regex literals and dynamic imports separately. Track precision and supported-form recall on a held-out fixture set before broadening claims.

### E04-F08 — Reached optional graph records disappear from impact output

**Classification:** verified output-coverage defect. **Priority/severity:** P2 / medium.

The graph includes `GROUPS+OPTIONAL` nodes ([graph_engine.py:8](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/graph_engine.py:8)), and the canonical links explicitly connect requirements to verifications ([project_model.py:16](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/project_model.py:16)). Impact traversal reaches them. However `affected` is constructed only for core `GROUPS` at graph_engine line 36. Reached optional records are neither in `affected` nor `unreached_records`.

In the fixture, accepted passed verification `VER-001` references `FR-001`. Impact for `FR-001` does not report `VER-001` as affected, and also does not list it as unreached. The result therefore cannot guide review of existing verification evidence when that requirement changes. Evidence: [optional-graph-impact.json](/workspace/sas-audit-2026-10-29/reviewers/expert04-evidence/optional-graph-impact.json).

**Recommendation E04-R08:** report reached optional records or a separate explicitly typed evidence/verification review set. Do not mutate their acceptance or pass status automatically; flag the evidence for reconsideration with the same witness semantics.

**Acceptance:** every reached node is accounted for exactly once as a seed, direct/transitive candidate or separately typed reached record; every unreached node remains listed. Requirement-linked verifications, evidence and risks survive output projection and have supported witness paths.

### E04-F09 — Optional cache serialization can turn a successful bounded scan into an error; parser time is cooperative

**Classification:** verified cache availability defect plus demonstrated time-bound limitation. **Priority/severity:** P2 / medium.

The 100-item output quota is applied only after full extraction and after full `items`/`edges` have been placed into `new_cache` ([repository_evidence.py:136–154](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/repository_evidence.py:136)). `atomic_write` rejects output above 5 MiB ([safe_io.py:75](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/safe_io.py:75)). Cache persistence is mandatory once requested, and its failure aborts the scan rather than returning collected evidence with a cache error.

One 180,000-byte `a.py` with 20,000 `import a` declarations is within the scanner's 300,000-byte file cap. Without a cache it completes, emits 100 declarations and records 19,900 omitted. With a cache it raises `ValueError: output byte budget exceeded`; the real CLI returns exit 2 and no scan result. This is not an unrelated-file overwrite: the cache path was new and outside the checkout.

The same source with `deadline=.01` took approximately **0.253 seconds** in the final fixture run, completed parsing and reported no deadline stop. Python AST extraction is in process and has no preemption/check inside it. This is a measured example of cooperative time accounting, not a benchmark or a claim of indefinite execution. Evidence: [large-declaration-probe.json](/workspace/sas-audit-2026-10-29/reviewers/expert04-evidence/large-declaration-probe.json).

**Recommendation E04-R09:** enforce bounded extraction records before cache materialization; preserve explicit truncation; cap cache bytes/entries; report a typed cache-write failure while preserving the otherwise valid scan result. Describe parsing deadlines as cooperative until costly adapters run in killable workers with explicit resource/output limits. Reuse the existing worker pattern where appropriate rather than adding a service.

**Acceptance:** this fixture returns coherent partial scan evidence with and without caching; cache output remains bounded; no silent 5-MiB failure discards the result. A claimed hard adapter deadline is actually enforced by worker termination; a cooperative adapter discloses its enforcement mode and elapsed/budget overrun.

### E04-F10 — Evidence delta does not validate input envelopes or collection identity

**Classification:** verified input-validation gap; evidence-backed risk for comparing unrelated or incompatible evidence. **Priority/severity:** P2 / medium.

[repository_evidence.py:176](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/repository_evidence.py:176) checks only equality of `adapter_version`, builds path-to-hash maps and compares them. `evidence_delta({}, {})` returns an empty successful-looking delta because two missing versions compare equal. The CLI routes arbitrary JSON directly into it ([architect_cli.py:79](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/architect_cli.py:79)); the evidence schema is not enforced here. Two unrelated roots using the same adapter version are also compared as if relative paths share identity, without a mismatch warning. The latter can be a legitimate explicit cross-tree comparison, so a different root alone should not be prohibited.

**Recommendation E04-R10:** validate envelopes and hash/path uniqueness, then require a comparable logical repository identity or an explicit caller-declared cross-tree comparison. Compare adapter ID/version/configuration and relevant scope semantics, not the overall version string alone. Keep `removed_or_unread` unless complete comparable enumeration can prove deletion.

**Acceptance:** `{}` inputs return a typed invalid-evidence error; duplicate paths/invalid hashes are rejected; incompatible adapters/scopes return unknown with reasons; two explicitly identified worktrees of the same repository can compare; unrelated roots require an explicit comparison mode. Added/changed/removed-or-unread remain scoped, with coverage differences returned alongside the file delta.

### E04-F11 — Modernization and freshness workflows are useful instruments, with important unimplemented analysis layers

**Classification:** demonstrated capability boundary and improvement opportunity, not a defect claim. **Priority:** P2 where a real modernization task establishes demand; otherwise defer.

`migration_plan` at [workflow_tools.py:17](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/workflow_tools.py:17) emits the same five proposed stages with component IDs/files and explicit unknown business invariants, traffic, ownership and recovery. This correctly prevents invented migration seams, but it does not inspect code, find actual seams, identify coupling, derive a migration dependency DAG, or verify a refactor. `freshness` at [workflow_tools.py:9](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/workflow_tools.py:9) correctly returns stale for changed content and unknown for unread evidence; it compares evidence hashes and optional whole-project input identity, rather than selectively invalidating derived artifacts based on a source-to-artifact dependency graph. The fixture confirms `stale` and `unknown` are preserved. The broader M24 acceptance of invalidating the correct derived artifacts ([IMPLEMENTATION_STATUS.json:322](/workspace/SOFTWARE-ARCHITECT-STUDIO/IMPLEMENTATION_STATUS.json:322)) is not fully realized by this function alone.

`repo_scan` produces raw module targets rather than a resolved file dependency graph, and its project drift check only tests declared path existence/read status ([repository_evidence.py:160](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/repository_evidence.py:160)). The graph engine traverses canonical declarations, not automatically reconstructed source relationships. There is no source semantic call graph, data-flow analysis, framework binding, runtime topology verification, generalized entrypoint/test discovery, or repository search/index service in the inspected paths. Broader absence across arbitrary host tools is not claimed.

The implementation adapter is explicitly a contract rather than a connection ([implementation-adapter.md:1](/workspace/SOFTWARE-ARCHITECT-STUDIO/docs/implementation-adapter.md:1)). The integration strategy assigns actual builds/tests and repository operations to external tools ([integrations.md:4](/workspace/SOFTWARE-ARCHITECT-STUDIO/docs/integrations.md:4)). Preserve these honest boundaries.

**Recommendation E04-R11:** make modernization evidence-backed incrementally: pair a declared seam with resolved local dependencies, contract/characterization tests, actual owner confirmation and current source identity; propose one bounded migration slice; request implementation through a real capability-checked host adapter; record actual checks and source preconditions. Add source-to-derived-artifact links only where consumers need selective invalidation. Do not add a vector store, graph database or universal semantic index before a benchmark proves the simpler map insufficient.

**Acceptance:** a representative modernization task identifies one real source seam with inbound/outbound dependencies and unknowns; preserves a supplied compatibility invariant; produces an ordered, testable slice and recovery condition; never changes `proposed` to `implemented/tested` without execution receipts. A changed linked source marks only the declared dependent artifacts stale; unread source remains unknown; unrelated stable artifacts remain reusable.

## What works and should remain

1. **Safe collection baseline.** The scanner reads regular files through bounded no-follow IO, skips symlinks/FIFOs and never executes inspected code. The safe fixture containing `raise RuntimeError(...)`, a symlink and a FIFO returned evidence/omissions without executing the file. Relevant implementation: [repository_evidence.py:99](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/repository_evidence.py:99) and [safe_io.py:50](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/safe_io.py:50).
2. **Honest enumeration bounds.** `.github` is included; exact `.git`, vendor/build exclusions and unsupported extensions are recorded. The existing entry-budget test confirms unknown total when enumeration stops. Descriptor prioritization is limited to discovered scope, as documented. Preserve this distinction.
3. **Parsed Python evidence, not route regex guesses.** Imports and supported literal route decorator candidates use Python AST, with file hashes and source lines. Comments are excluded. Framework binding is explicitly unverified.
4. **Declared graph semantics are restrained.** Direction is documented, cycles terminate, ordering is stable, and witness paths are labeled review candidates rather than causality. Existing tests pass. Extend the seed/output coverage without replacing the graph storage model.
5. **Drift/freshness do not equate unread with deleted.** Missing/unread mappings have scoped labels; evidence delta uses `removed_or_unread`; hash freshness preserves unknown. Maintain these semantics while tightening envelope validation.
6. **Cache ownership and disclosure precautions exist.** An unrelated existing JSON file is preserved by the current test, snippets are opt-in, and obvious sensitive data is minimized. This is a useful local cache, not an authority source or tamper-resistant evidence store. Fix metadata/bounds rather than replacing it with distributed infrastructure.
7. **Documentation rejects unsupported execution claims.** The CLI does not install dependencies, build a scanned repository, call a model, publish code or deploy. Migration and integration plans accurately describe their proposed/conditional status.

## Historical regression reconciliation for this scope

| Historical target | Current verified status | Remaining risk / finding |
|---|---|---|
| Scanner selection and `.github` inclusion, M10 | Existing relevant-file/CI and special-file tests pass; actual scan reports omissions | Silent edge truncation E04-F04; parser time is cooperative E04-F09 |
| Typed graph closure, M09 | Cycle/order and requirement propagation tests pass | Nonrequirement seeds E04-F03; optional records E04-F08 |
| Shared evidence envelope, M11 | Paths/content hashes/version/capture/scoped observations are present | Delta does not enforce envelope validity/identity E04-F10; descriptors use whole-document line 1 |
| Language adapters, M25 | Python AST and narrow JS static modules demonstrated | Relative imports E04-F06; valid JS false span E04-F07; unsupported language coverage E04-F01 |
| Deployment/data/event descriptors, M26 | Selected JSON/YAML jobs/package/API declarations exist | Failed parses vanish E04-F05; silent needs-edge cap E04-F04 |
| Fitness counterexamples, M27 | Known direct Python violation test passes | Missing extractor evidence still passes in scope E04-F01 |
| Cache overwrite/parity, M28 | Unrelated cache-path preservation and edge parity tests pass | Cold/warm semantic parity fails E04-F02; overflow aborts E04-F09 |
| Source/artifact freshness, M24 | Changed content becomes stale; unread remains unknown | Selective derived-artifact invalidation is only partial E04-F11 |
| Modernization packs, M29 | Proposed staged worksheet and unknowns are present | Actual seam analysis/check execution requires source work and real host adapter E04-F11 |
| Universal semantic index, M39 | Deferred consistently | Keep deferred until measured retrieval/coupling tasks justify it |

## Proposed bounded target design and implementation sequence

### 1. Repair the evidence contract before adding more parsers

**Initiative E04-I01** addresses R01/R02/R04/R05/R09/R10. Introduce a versioned per-file extraction result with:

```text
source_identity: logical_repository_id, actual_commit_if_known,
                 dirty_overlay_identity_if_known, collection_root
file_identity: relative_path, content_hash, byte_count
adapter_identity: adapter_id, version, relevant_config_hash
extraction: terminal_status, supported_relation_kinds, parsed_spans,
            complete_for_rule, diagnostics, extracted/emitted/omitted_counts
collection: requested/used budgets, enforcement_mode, stop_reasons,
            enumerated/read/unread/unsupported/excluded counts
```

Commit and dirty-overlay fields remain unknown unless actually collected. A changed path set can be reflected in both a source fingerprint and a separate extraction/coverage identity; a source hash alone does not identify the correctness of parser output. The cache stores this complete bounded result. Fitness and delta consume validated envelopes and explicit supported relation coverage. Validate opaque data without executing it. Preserve current no-follow IO and opt-in disclosure.

Implement this as an in-process schema/data refactor plus bounded adapter workers where needed, not a hosted service. Tests above are the first acceptance suite; add held-out repositories and collect timings/memory/output bytes before asserting scalability. Roll back by retaining v1 read support with explicit unknown coverage; do not reinterpret old empty extractions as passed.

### 2. Generalize graph queries without changing the canonical intent model

**Initiative E04-I02** addresses R03/R08. Add typed seed traversal over the existing graph and keep requirement-only compatibility. Emit direct changes, reachable review candidates, seed identities, witness paths, reached optional records, unreached records and manual-review reasons. Reuse before/after identities for removed/added records. Explicitly compare relationship changes and avoid falsely translating ownership order into runtime flow.

Acceptance is the E04-F03/F08 matrix plus existing cycles/order tests. The value is concrete: interface/schema/component edits receive actionable downstream review scope without requiring artificial requirement edits. There is no need for a graph database at this size.

### 3. Add a small local-resolution layer against demonstrated demand

**Initiative E04-I03** addresses R05/R06/R07/R11. Start with lossless Python import records and the repository's actual manifests, then conservative local module/package resolution. Improve JS declaration precision using a small grammar or a real optional syntax parser. Add monorepo/workspace support only with pinned fixtures spanning multiple package roots and import aliases. Keep exact file/line/hash attribution and expose unresolved edges explicitly.

For languages beyond the shipped adapters, select optional syntax/compiler/LSP integrations per repository workload, actual availability and licensing/maintenance cost. An integration must declare read scope, language/tool version, limits, supported relationships and terminal failure status. Do not infer that a recommended or described tool is installed. A zero-result adapter is never proof of zero dependencies.

Evaluate against tasks such as finding entrypoints, identifying a contract's local consumers, tracing changed configuration and locating tests for one module. Measure precision, supported-form recall, unresolved fraction, unique correct review candidates, latency, memory, bytes and maintenance burden. Compare to simple `rg` plus manifests first. Do not promise full semantic call/data-flow reconstruction from token extraction.

### 4. Connect modernization to actual implementation evidence

**Initiative E04-I04** addresses R11 and depends on I01/I02 plus a real authorized coding environment. A modernization slice consumes a current canonical design, comparable source scan, one declared seam, verified owner/compatibility constraints and check plan. It outputs a proposed change, source precondition, tests to run, staged migration/reconciliation and recovery criterion. A real adapter performs editing/build/checks only when authorized and returns evidence tied to the resulting source identity. Studio validates the result before updating canonical intent.

The internal product should own evidence interpretation and traceability; host repository/build/browser/deployment tools should own actual execution. Every result preserves planned/implemented/built/tested/runtime-verified distinctions. Without those tools, the final deliverable stays a reviewable migration proposal, which is still useful.

## Limits and unverified areas

- This reviewer tested the selected modules and listed cases, not every source file, complete browser UI, every installed connector, all languages, or real external repositories.
- No live model benchmark, user study, runtime program analysis, deployment, hosted service, multi-repository discovery or external tool integration was executed by this reviewer.
- Git commit identity was manually pinned for the audit; `repo_scan` itself deliberately does not infer it. Dirty-tree race/snapshot consistency during a changing working tree was not stress-tested.
- The measured large-file timings demonstrate behavior in this runtime, not throughput guarantees. Hard resource containment is not established for in-process Python/JS adapters.
- Descriptor observations generally cite line 1 for a whole document, not exact dependency spans; this limits navigational precision even where the declaration is correct.
- Raw `source_prefix`/`target_prefix` checks use lexical `startswith`; this behavior is observable, but I do not classify matching `src2` from prefix `src` as a defect because the current API explicitly names prefixes. A future path/module selector should define segment semantics clearly.
- Current static output has no independently measured adapter precision/recall corpus. Passing sample tests is a regression signal, not evidence of general repository understanding.

The decisive first implementation work is evidence-state correctness and typed change coverage. Broader language coverage and modernization automation should follow measured needs, with the existing safe, local, source-attributed foundation retained.
