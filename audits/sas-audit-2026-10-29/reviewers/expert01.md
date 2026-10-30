# Expert 01 — Product, requirements, UX and strategy

Independent first pass, 2026-10-29. Baseline: `/workspace/SOFTWARE-ARCHITECT-STUDIO`, Git `83812e1d31c17ed857be8d2fb5c98126a8ccb5c8`. One actual specialist instance; no further agents; no other reviewer findings consulted before this pass. Checkout unchanged. Recommendations are proposed, not implemented.

## Verdict

Preserve Studio as a portable architecture and engineering assurance companion. Its credible proposition is continuity from requirements and accepted decisions to source evidence, change review and an explicitly scoped handoff. Add implementation through an actually capable coding host and verified results, rather than turning the offline workbench into an IDE.

The quick/guided/full policy is proportionate and honest. The workbench nevertheless contains concrete editing hazards, and review-ready accepts an application project containing no specification records. Repair these trust failures before expanding surface area. Target users and productivity benefit remain hypotheses: no actual participant or competitive performance evidence was found in the inspected product/research material.

## Evidence and boundaries

**Verified defect** below means inspected logic plus an executed counterexample. **Observed** means source/output inspection; **risk** is a supported possible consequence; **opportunity** requires value validation. These are not interchangeable.

Principal sources, pinned to the baseline:

| Source | Relevant evidence |
|---|---|
| [README.md:7](/workspace/SOFTWARE-ARCHITECT-STUDIO/README.md:7), lines 7–35, 37–68 | Three outcomes, CLI/browser scope, export profiles and research limits. |
| [software-architecture/SKILL.md:10](/workspace/SOFTWARE-ARCHITECT-STUDIO/skills/software-architecture/SKILL.md:10), lines 10–32, 49–59, 75–97 | Intent/depth/audience, two-question limit, requirements sequence, readiness and expansion boundaries. |
| [requirements-specification/SKILL.md:6](/workspace/SOFTWARE-ARCHITECT-STUDIO/skills/requirements-specification/SKILL.md:6), lines 6–14 | Discovery, acceptance, NFR scenarios, evidence and proposed deltas. |
| [workbench/index.html:7](/workspace/SOFTWARE-ARCHITECT-STUDIO/workbench/index.html:7), lines 7–28, 33–71 | Actual UX, rendering, collection editing, replacement guards and export handlers. |
| [workbench/project-core.js:35](/workspace/SOFTWARE-ARCHITECT-STUDIO/workbench/project-core.js:35), lines 35–51 | Canonical operations and browser continuation. |
| [tools/artifact_compiler.py:9](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/artifact_compiler.py:9), lines 9–34 | Exact readiness predicate. |
| [tools/project_model.py:94](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/project_model.py:94), lines 94–100 | CLI continuation identity and coverage. |
| [research/user-observation-template.json:2](/workspace/SOFTWARE-ARCHITECT-STUDIO/research/user-observation-template.json:2), lines 2–25 | Hypothesized segment, tasks and no-participant disclosure. |
| [docs/implementation-adapter.md:2](/workspace/SOFTWARE-ARCHITECT-STUDIO/docs/implementation-adapter.md:2), lines 2–6 | Contract, explicitly not a connected execution adapter. |

No live model benchmark, participant interview, competitor benchmark, external plugin installation or production application execution was performed. Browser launch failed in this expert’s un-escalated attempt; actual inline handlers were exercised under the repository’s minimal DOM harness. This verifies handler behavior, not layout or assistive technology. Coordinator-reported successful browser execution is separate evidence, outside this independent pass.

## Strengths to preserve

- **Documented:** Quick advice requires no project, diagram or interview. Depth and audience are independent, with at most two pivotal questions. Beginner explanation retains engineering obligations. Actual model adherence remains unmeasured.
- **Verified within tests:** Rich canonical roundtrip, accepted status, stable IDs, non-ASCII data, flat snapshots and several recovery/draft invariants pass. These support continuity without pretending to provide cloud synchronization.
- **Observed:** Browser scope, local unencrypted storage, portable/private exports and conservative impact semantics are disclosed. Preserve these distinctions.
- **Observed:** Labels, skip navigation, live status, heading focus management, responsive CSS and `dir="auto"` provide useful accessibility foundations. Full accessibility conformance is unverified here.
- **Observed:** Canonical records and independent readiness/review/runtime dimensions offer a useful middle ground between disconnected prose and implementation. Differentiation is a value hypothesis, not competitive superiority.

## Synthetic journey assessment

| Journey | Inputs/tools/state and result | Acceptance direction |
|---|---|---|
| Quick database decision | Constraints plus architecture policy; project/tool use optional. Policy directly supports the job; no actual response benchmark. | Answer the choice, simpler alternative and consequential uncertainty without forced paperwork. |
| Guided tenant-report application | Goal, actors, sensitive data and constraints; requirements then architecture; optional proposed canonical delta. Browser moves from brief to raw JSON and can discard unapplied brief on depth change. | Preserve typing; ask only pivotal questions; provide testable acceptance and one clear next action. |
| Full specification/handoff | Canonical context, contracts and independently selected profile; CLI readiness/compiler/validators. Rich fixture gives five blockers, empty full-specification application gives none. Browser-to-CLI transfer requires path knowledge. | Requested scope covered or explicitly blocked; exact checks and output location intelligible. |
| Resume/change | Imported project, recorded acceptance, source identity and minimal delta; impact and snapshot/commit when authorized. Preservation is strong; continuation and collection editing have gaps. | Identify exact context, preserve acceptance, and save only intended typed records. |
| Build/test/deliver | Requires an actually capable editor/runtime/CI/deployment host and authority. Native toolkit does not provide this execution service; adapter is a contract. | Distinguish planned, implemented, built, tested, runtime-verified, deployed, partial and blocked. |
| Recover/context loss | Retained bytes, canonical data, independent drafts and recovery exports. Several core invariants pass; actual lifecycle UX unverified in this pass. | Preserve recoverable work and identify one safe next action without claiming automatic sync. |

These are synthetic source/tool walkthroughs, not user research. Quick answers need no approval ceremony. Local authorized edits should not gain redundant interviews; unchanged accepted records retain acceptance. Consequential external actions use actual session authorization, never authority inferred from project text.

## Prioritized findings

### E01-F01 — P1 — Preference changes discard unapplied text

**Verified defect in handler logic.** `workbench/index.html:38` reloads name, brief and canonical JSON from state; line 44 routes preference changes through full render. Probe `unapplied-brief-depth-change` typed a name/brief, selected Quick advice and observed `New architecture`/empty brief. Typed bytes never reached canonical state or undo.

**E01-R01:** Separate editor drafts from committed state; avoid unrelated rerenders; resolve drafts explicitly before whole-project replacement. **Acceptance:** exact pending name/brief/JSON survives intent/depth/audience changes and navigation; invalid JSON remains editable without mutation; exports clearly identify committed versus pending content. Add interleaved-action browser regression coverage.

### E01-F02 — P1 — Old record saves into newly selected collection

**Verified defect.** `index.html:43` resets `editID` on collection change while retaining textarea JSON; line 47 saves into the newly selected group. Probe edited requirement FR-002, selected components, saved, and observed FR-002 inserted as a component. Structural validation accepted it.

**E01-R02:** Bind drafts to collection, record ID and base identity; maintain separate drafts or explicitly reset when switching. **Acceptance:** switching among requirements/components/decisions/tasks cannot insert a stale record into another group; returning restores the right draft; failures preserve canonical state and accepted-record protections.

### E01-F03 — P1 — Empty specification satisfies review-ready

**Verified behavior; product risk.** `artifact_compiler.py:13–24` only checks records that exist; lines 30–34 find no blockers when all collections are empty. Actual `readiness` and in-memory `compile_plan` accepted a tenant-application brief requesting Full specification: `profile_satisfied: true`, completeness `specified within supported scope`. Rich fixture instead reports five blockers.

The output still states human review unknown/runtime not run; this is not a production-certification claim. It nevertheless fails to assess requested scope.

**E01-R03:** Separate present-record checks from requested-scope coverage; require relevant records or justified non-applicability for review-ready. **Acceptance:** an empty business application cannot pass; deleting unfinished records cannot silently establish scope coverage; CLI-only/no-database designs remain valid with explicit applicability; quick/draft use stays permissive.

### E01-F04 — P2 — Sample/new guards ignore meaningful work

**Verified defect, initially recoverable.** `index.html:56` confirms New only for requirements/decisions/brief; line 57 rejects sample replacement only for requirements/decisions. Probes replaced brief/components with the sample and cleared components-only work with New. Undo initially retained applied state; permanent loss was not demonstrated.

**E01-R04:** Centralize meaningful-work detection across complete canonical data and pending drafts; open samples separately or require explicit replacement. **Acceptance:** brief-, components-, tasks-, constraints- and extension-only projects receive consistent protection; truly blank projects remain one-step; recovery claims match actual retention.

### E01-F05 — P2 — Beginner authoring requires raw JSON

**Observed limitation; inferred adoption concern.** `index.html:14` initializes record authoring with `{}`; lines 41/47 expose record IDs and generic collections. Audience selection changes preferences, not authoring controls. Novices must infer schemas and reference conventions. No participant failure is claimed.

**E01-R05:** Add small schema-preserving requirement/ADR/task forms and an NFR scenario template; retain advanced JSON. Start with per-collection examples before a broad form system. **Acceptance:** author one FR, material NFR and linked task without JSON; retain stable IDs and unsupported fields; validate value with actual beginners before expanding.

### E01-F06 — P2 — Continuation packet omits purpose and browser identity

**Verified omission; continuity risk.** `project-core.js:51` omits brief and content hash. A brief-only app produces a continuation packet containing no app purpose. CLI `project_model.py:96` adds hash/coverage but also omits brief. Portable exports retain full data.

**E01-R06:** Share a bounded continuation contract containing canonical identity, concise outcome, accepted choices, blockers and reference to required canonical input. **Acceptance:** distinguish different projects at the same revision; retain brief-only purpose; exclude raw history/extensions; explain missing context without implying retrieval by hash or cloud sync.

### E01-F07 — P2 — Browser-to-CLI transfer requires guessing

**Observed opportunity; impact unmeasured.** `index.html:52` downloads name-derived `*-project.json`; lines 20–27 show generic `./project` commands. Handoff loads a directory (`artifact_compiler.py:145–148`), while some commands accept a file. The UI explains neither transfer nor profile choice.

**E01-R07:** Add a compact post-export local guide: exact filename/location, working directory, dry-run/profile commands and expected states. Actual execution remains in the host. **Acceptance:** fresh export to dry-run/generation/checks requires no path guessing; depth is distinct from profile; missing optional tooling yields a concrete non-passing next step; commands contain no opaque data/secrets.

### E01-F08 — P2 — User value and segment remain unmeasured

**Documented limitation, honestly disclosed.** Research template lines 2–25 names technical leads/small teams as a hypothesis and records no participants. Tasks cover resume/change/handoff, omitting initial discovery, quick advice and application completion.

**E01-R08:** Conduct formative observations across technical leads and less technical builders on five concrete journeys; separately evaluate captured model responses. **Acceptance:** retain consented minimal observations of completion, corrections, time, support and trust failures; distinguish host limitations from product defects; report sample limitations; require repeated collaboration demand before hosting and measured benefit before indexing/orchestration infrastructure. No outreach occurred in this audit.

### E01-F09 — P2 — Release identities conflict

**Verified inconsistency.** README line 1 and `project_model.py:6` say 0.8.0; `plugin.json:4`, `capabilities.json:2`, repository SKILL line 6 and workbench header line 5 say 0.7.1; HTML title says 0.7. Installation failure is unproven, but support identity is ambiguous.

**E01-R09:** Validate package/display/CLI identity against one release source; keep schema/backup versions independent. **Acceptance:** current release references agree; mismatch fails release checks; historical evidence retains its original version.

## Strategy and simplification

Proposed primary segment: technical leads/small teams needing trustworthy design continuity. This remains a hypothesis. Keep three entry outcomes: Decide, Continue/change, Prepare handoff; expose Implement with host only when real tools support it. Progressive disclosure should prioritize next action and blockers, with graph/capacity/assessment and raw JSON available as advanced controls.

Build continuity, scope/readiness and clear editing internally. Integrate editing/build/test/browser/deployment through capable hosts. Keep source control/CI alongside. Defer hosted collaboration, native embedding, universal graph/vector infrastructure and autonomous multi-model expansion pending demonstrated need, as `strategy/deferred-decisions.md:3–9` already recommends.

Sequence: repair F01–F04/F09; improve forms/continuation/CLI bridge F05–F07; observe real users F08; only then add one complete, verified execution journey if justified. Centralize draft/replacement logic, continuation semantics and version identity. Do not remove canonical portability, advanced JSON or truthfulness disclosures; do not add many skills to compensate for broken journeys. Detailed working notes are retained separately in `expert01-expanded-notes.md`.

## Actual execution ledger

All Python shell invocations used `PYTHONDONTWRITEBYTECODE=1`. Git status was clean/HEAD unchanged at pass end. Outputs stayed under reviewer `expert01*` paths.

| Actual check | Result / evidence |
|---|---|
| `node tests/test_workbench.cjs`, Node 24.19.0 | **25/25 passed**, exit 0; minimal DOM/core, not browser. `expert01-workbench-tests.json`. |
| Custom actual inline-handler probes | F01/F02/F04 reproduced, F06 observed; final exit 0. `expert01-dom-probes.cjs`, `expert01-dom-probes.json`. |
| Initial custom harness | Cross-VM deep-equality artifact affected a baseline assertion, not Studio; preserved in `expert01-dom-probes-initial-harness-error.json`. Corrected by reusing helper definitions only. |
| Python 3.12.14 doctor | Completed; mmdc/full OpenAPI optional package absent. `expert01-doctor.json`. No installation. |
| CLI rich resume/readiness | Completed; five review-ready blockers. Reporting command exit 0 is not readiness success. `expert01-cli-resume.json`, `expert01-rich-readiness.json`. |
| Empty application `readiness`/`compile_plan` | Both accepted review-ready; in-memory compilation only. `expert01-empty-readiness.json`. |
| Installed Playwright 1.56.1 + Chromium | Un-escalated launch failed before startup: crashpad setsockopt denied/SIGTRAP; zero checks/screenshots. `expert01-browser-probes.json`. Coordinator’s supported successful browser run is separate. |

**Final verdict:** retain the foundation, repair editing/readiness trust and measure connected task outcomes. Evidence supports incremental repair and focused integration, not a full rewrite or native all-lifecycle platform claim.
