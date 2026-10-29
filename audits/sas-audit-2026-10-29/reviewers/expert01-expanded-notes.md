# Expert 01 — Product, requirements, user experience and strategy

Independent first pass, 2026-10-29. Baseline: `/workspace/SOFTWARE-ARCHITECT-STUDIO`, Git `83812e1d31c17ed857be8d2fb5c98126a8ccb5c8`. This reviewer inspected no other expert report before reaching these findings. One actual specialist instance performed this review; no further agents were created. The checkout remained unchanged. Proposed changes below are specifications, not implementation.

## Verdict

Preserve Studio as a portable architecture and engineering assurance companion. Its strongest product proposition is continuity from requirements and accepted decisions to source evidence, change review and an explicitly scoped handoff. Expand implementation through an actual capable coding host and verified receipts, rather than making the offline workbench into an IDE or treating skill instructions as a deployed engineering platform.

The existing interaction policy is unusually disciplined: a quick question need not create a project; depth and audience are independent; imported acceptance is preserved; uncertainty and tool limits are explicit. Those are source-observed strengths, not measured model performance. The workbench has concrete editing hazards and its review-ready predicate can accept a business application containing no specification records. Repair these trust failures before adding product surface area.

The intended users are still a hypothesis. No user observation or comparative product-performance evidence was found in the inspected product/research sources. Beginner accessibility, collaboration demand and productivity benefit remain unmeasured. The correct next product investment is a small number of reliable task journeys plus formative observation, not a larger skill catalog by default.

## Evidence and inspection boundaries

Classifications used below: **verified defect** means source logic plus an executed counterexample; **verified capability** means inspected and/or executed within the stated scope; **documented capability** means policy exists but end-user outcome was not measured; **evidence-backed risk** is an implementation-supported consequence; **improvement opportunity** is a proposal requiring value validation; **unknown** means evidence is insufficient.

Principal sources, all pinned to the baseline commit:

| Source | What it establishes |
|---|---|
| [README.md:7](/workspace/SOFTWARE-ARCHITECT-STUDIO/README.md:7), lines 7–35 and 37–68 | Three outcomes, workbench/CLI boundaries, export profiles, validator honesty and research limitations. |
| [plugin.json:4](/workspace/SOFTWARE-ARCHITECT-STUDIO/plugin.json:4), lines 4–5 and 34–43 | Product identity, release identity, architecture-first description and starter prompts. |
| [software-architecture/SKILL.md:10](/workspace/SOFTWARE-ARCHITECT-STUDIO/skills/software-architecture/SKILL.md:10), lines 10–32, 49–59 and 75–97 | Independent intent/depth/audience, two-question limit, requirements sequence, readiness dimensions and deferred expansion. |
| [requirements-specification/SKILL.md:6](/workspace/SOFTWARE-ARCHITECT-STUDIO/skills/requirements-specification/SKILL.md:6), lines 6–14 | Discovery, observable acceptance, NFR scenarios, evidence separation and proposed canonical deltas. |
| [workbench/index.html:7](/workspace/SOFTWARE-ARCHITECT-STUDIO/workbench/index.html:7), lines 7–28 | Actual navigation, input controls, raw JSON editors, scope disclosures and CLI bridge. |
| [workbench/index.html:33](/workspace/SOFTWARE-ARCHITECT-STUDIO/workbench/index.html:33), lines 33–71 | Actual mutation, rendering, collection editing, new/sample, persistence, import/export and recovery handlers. |
| [workbench/project-core.js:35](/workspace/SOFTWARE-ARCHITECT-STUDIO/workbench/project-core.js:35), lines 35–51 | Blank project, snapshot/restore, supersession, impact, calculation and browser continuation behavior. |
| [tools/artifact_compiler.py:9](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/artifact_compiler.py:9), lines 9–34 and 144–149 | Exact readiness predicate and dry-run boundary. |
| [tools/project_model.py:94](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/project_model.py:94), lines 94–100 | CLI continuation identity and coverage versus browser continuation. |
| [docs/implementation-adapter.md:2](/workspace/SOFTWARE-ARCHITECT-STUDIO/docs/implementation-adapter.md:2), lines 2–6; [docs/integrations.md:4](/workspace/SOFTWARE-ARCHITECT-STUDIO/docs/integrations.md:4), lines 4–9 | Proposed adapter operations, explicit absence of connected execution adapter, ownership and authority boundaries. |
| [research/user-observation-template.json:2](/workspace/SOFTWARE-ARCHITECT-STUDIO/research/user-observation-template.json:2), lines 2–25; [tools/workflow_tools.py:66](/workspace/SOFTWARE-ARCHITECT-STUDIO/tools/workflow_tools.py:66), lines 66–71 | Research instrument, hypothesized target segment, task list and no-participants disclosure. |
| [strategy/deferred-decisions.md:3](/workspace/SOFTWARE-ARCHITECT-STUDIO/strategy/deferred-decisions.md:3), lines 3–9 | Demand/evidence prerequisites for hosted collaboration, semantic infrastructure and autonomous expansion. |
| [tests/test_workbench.cjs:18](/workspace/SOFTWARE-ARCHITECT-STUDIO/tests/test_workbench.cjs:18), lines 18–34; [tests/browser/workbench.spec.cjs:1](/workspace/SOFTWARE-ARCHITECT-STUDIO/tests/browser/workbench.spec.cjs:1), lines 1–21 | Existing DOM test harness and limited browser scenarios. |

This was a product and interaction review, not exhaustive security or compiler verification. No live model was invoked for a benchmark, no participant was interviewed, no competitor was benchmarked, and no external plugin was installed. The installed cloud skill was read as audit workflow guidance; conclusions concern the pinned repository, whose instruction text differs from the cloud package.

## What works and should remain

1. **Proportionate interaction policy — documented capability.** Quick advice explicitly avoids mandatory project files, diagrams and interviews. Guided and full outputs add appropriate obligations without conflating beginner language with weaker engineering. At most two pivotal questions are allowed, with available context used first. This directly addresses users who need a decision rather than a process. Actual model adherence remains unmeasured.
2. **Portable continuity — verified scoped capability.** The actual Node suite passed rich roundtrip preservation, accepted status retention, non-ASCII data, stable IDs, flat snapshots, recovery protection and independent tab drafts. These are valuable prerequisites for technical leads handing work between sessions and tools. They do not prove cross-device sync or production durability.
3. **Honest control boundaries — observed.** Browser text says it does not scan repositories, deploy, evaluate models or fully validate contracts. Export versus private backup and local unencrypted storage are disclosed. Impact results explicitly describe conservative review candidates, not proven causality. Preserve these distinctions in any redesign.
4. **A useful middle ground between prose and implementation — observed.** The canonical project can retain native API contracts, tasks and explicit associations, while the compiler reports blockers and independent review/runtime dimensions. This offers a credible differentiated workflow hypothesis: preserve intent and expose gaps across tools. Competitive superiority is unverified.
5. **Basic inclusive markup — observed, incompletely verified.** There are explicit labels, a skip link, section heading focus management, live status, visible focus CSS, responsive CSS and `dir="auto"` on key free-text fields. Screen-reader behavior, zoom, mobile layout and RTL usability were not verified by this expert.

## Realistic journey assessment

These are synthetic walkthroughs of policy, code and tools. They are not participant observations or proof of assistant response quality.

| Journey and trigger | Inputs, tools and state | Observed result / remaining gap | Target acceptance |
|---|---|---|---|
| **Quick decision:** “Five people, low budget: PostgreSQL or a document database?” | User constraints; architecture skill; no project required. No tool call is intrinsically necessary. | Policy supports direct recommendation, simpler alternative and uncertainty. No live response was evaluated. The workbench is optional and adds little to this job. | Answer the actual choice and decision-changing uncertainty without forcing an interview, schema, diagram or save. |
| **Guided new project:** “Staff need to export authorized tenant reports.” | Outcome, actors, sensitive data, constraints and unknowns; requirements then architecture; optionally proposed canonical delta. | Requirements policy covers acceptance and NFRs; the UI starts with a brief, then `{}` in a JSON editor. No guided conversion is executed by the browser. Changing depth can erase the typed brief before Apply. | Preserve typing; ask only material unanswered questions; produce one understandable proposal with testable acceptance and a next action. |
| **Full specification and handoff:** “Prepare an implementation handoff for this application.” | Canonical project, actual contracts and a separately selected handoff profile; CLI readiness/compiler/validators. | Rich fixture reports five useful blockers. Empty full-specification business project instead reports review-ready, zero blockers. Browser provides generic CLI examples and exports, not a coherent named-file/directory transfer. | Missing scope/specification must remain visible; all applicable fields and contracts trace to records; exact checks and output locations are explained. |
| **Resume/change:** “Keep accepted tenant isolation; add audit export.” | Actual imported project, accepted choices and source identity; minimal proposed delta, impact witnesses, validation and snapshot/commit when authorized. | Canonical preservation and explicit impact are strong. Browser “Continuation packet” omits brief and source hash; record editing can save into the wrong collection after a selector change. | Preserve unchanged accepted records and unknown fields; identify exact context; show what changes and what remains unknown; save only the intended typed record. |
| **Build and deliver an application:** “Implement, test and deploy it.” | A capable, permissioned host/editor/build/test/deploy integration, with source identity and verification receipts. | Native local toolkit does not provide this execution service; adapter document explicitly describes a contract, not a connected adapter. A skill may guide a host that actually has tools. No native app-build/deploy outcome is verified here. | Detect actual capabilities; perform only authorized available operations; distinguish planned, implemented, built, tested, runtime-verified, deployed, partial and blocked. Offer a concrete handoff when execution is unavailable. |
| **Recover after failure:** malformed import or conflicting tab | Retained bytes, current canonical state, draft export and explicit recovery; no new external authority. | Existing Node checks verify several recovery invariants. Recovery UI requires technical interpretation, and draft/conflict text is scattered across status/history. Actual browser lifecycle behavior was not verified in this pass. | Current work stays intact; identify recoverable draft and next safe action; export available data before a deliberate replacement; never label a failed import as a restored project. |

User approvals should follow actual effect and existing authorization, not depth mode. A quick answer needs none. Local draft editing should not add approval interviews. Accepted-record changes need a deliberate, visible change path, while unchanged imported acceptance should not require renewed approval. External execution/publication must use the session's actual authorization and tool controls. The current policy correctly distinguishes architectural acceptance from permission to act.

## Prioritized findings and implementation criteria

### E01-F01 — P1 — Editing a preference discards unapplied project text

**Classification:** verified defect in actual inline UI logic under the minimal DOM harness; inferred real-browser consequence. **Evidence:** `workbench/index.html:38` overwrites name, brief, canonical JSON and calculation editors from state. Lines 44 and 36 route preference changes through a full render. There is no draft layer for these fields. Executed probe `unapplied-brief-depth-change` typed a project name and brief, changed depth, and observed name reset to `New architecture` and brief reset to an empty string. The canonical state and undo history never held the typed text.

**Impact:** a user doing normal setup in either order can lose discovery work before the first save. The visible save status reflects canonical mutations, not unapplied typing. This is distinct from a stored-project corruption claim.

**Recommendation E01-R01:** keep editor drafts separately from committed canonical state and render only fields affected by a preference change. Track dirty fields; before an operation that replaces the whole project, preserve or explicitly resolve drafts. Do not silently auto-accept edited JSON or accepted decisions.

**Acceptance:** type into name/brief and full JSON, then change each intent/depth/audience control and navigate sections; exact draft bytes remain until Apply or explicit discard. Export clearly identifies whether it exports committed state or includes pending changes. Invalid JSON stays editable and does not replace canonical data. Add meaningful browser regression coverage for interleaved actions, in addition to a core handler test.

### E01-F02 — P1 — Collection changes can save an old record into the wrong collection

**Classification:** verified defect. **Evidence:** `workbench/index.html:43` changes collection and resets `editID` without resetting or rebinding `recordJSON`; line 47 saves that textarea into the newly selected group. Probe `record-collection-context-change` edited `FR-002`, switched from requirements to components and saved. `components` acquired an `FR-002` record, and canonical validation accepted it. Generic group record schemas permit the payload.

**Impact:** structure validation does not protect the user's editing intent. A stale requirement becomes an unintended component, altering graph/handoff context without an explicit move operation.

**Recommendation E01-R02:** bind the draft editor to `{group, record_id, base_identity}`. Changing collection must preserve a separate per-collection draft or explicitly switch to an empty/template editor. A save must validate the draft's bound collection against the selected collection. Record movement, if desired, is a separate reviewed operation.

**Acceptance:** reproduce this sequence with requirements, components, decisions and tasks; no cross-collection insertion occurs. Returning to a collection restores its intended pending draft. Save errors preserve both draft and canonical state. Existing accepted-record protection continues to hold.

### E01-F03 — P1 — Review-ready can be satisfied with no specification records

**Classification:** verified predicate behavior and evidence-backed product risk. **Evidence:** `tools/artifact_compiler.py:13` through line 24 checks fields only on records that exist. Lines 30–34 declare review-ready satisfied when there are no gaps. Executed `readiness` and `compile_plan` on a project whose brief requests a tenant reporting application and whose depth is Full specification, with all record collections empty. Both returned `profile_satisfied: true`, no blockers, and completeness `specified within supported scope`. Existing rich fixture correctly returned five blockers, demonstrating the predicate rewards an empty scope more than an incomplete real specification.

**Scope caveat:** output still says human review unknown and runtime verification not run; this is not a fabricated production-certification claim. Nevertheless, the label does not establish completeness against the user's application request, and its supported-scope qualifier is too easy to overinterpret.

**Recommendation E01-R03:** add explicit scope/applicability obligations to review-ready. Require an actual statement of intended deliverables and either the relevant specification records or explicit justified non-applicability. Distinguish “all present records pass their checks” from “requested handoff scope is covered.” Keep draft validity and quick advice permissive.

**Acceptance:** an empty business-application project cannot satisfy review-ready. Removing the last unfinished requirement or interface does not silently establish requested-scope coverage. A CLI-only tool with no HTTP API and a stateless design with no database remain valid when non-applicability is explicitly recorded. Present-record checks, human review, runtime verification and scope coverage stay separate. No unrequested bureaucracy is imposed on quick answers.

### E01-F04 — P2 — Sample/new-project guards ignore meaningful existing work

**Classification:** verified defect with recoverability limits. **Evidence:** `workbench/index.html:56` checks only requirements, decisions and brief before confirming New. Line 57 checks only requirements and decisions before replacing the project with an illustrative sample. Executed probes showed a brief-and-component project replaced by the sample, and a components-only project cleared by New. Both remain in the in-memory undo stack initially; this report does not claim immediate permanent loss of applied canonical data.

**Recommendation E01-R04:** use a common meaningful-work/dirty-state predicate comparing the whole project to its blank baseline, including opaque retained fields and pending drafts. Open samples in a separate draft or require an explicit replace action with a concrete recovery/export path.

**Acceptance:** brief-only, components-only, tasks-only, constraints-only and opaque-extension projects trigger consistent replacement protection. A truly blank project loads the sample in one step. Undo/recovery preserves the replaced state within the declared retention behavior; do not imply an unexported undo stack is durable.

### E01-F05 — P2 — Beginner workflow stops at raw JSON authoring

**Classification:** observed implementation limitation; inferred adoption concern, not measured user failure. **Evidence:** `workbench/index.html:14` provides a collection selector and raw JSON textarea initialized to `{}`; lines 41 and 47 expose all record groups and ID/schema obligations. The audience control changes `project.preferences` at line 44; it does not change authoring controls. A novice must infer record shapes, ASCII IDs, references and NFR scenario fields from elsewhere. Explicit JSON editing is valuable for experts but currently serves as the primary record entry path.

**Recommendation E01-R05:** add small schema-preserving forms for requirements, ADRs and tasks first. Offer an NFR scenario template with workload/environment/measure/target/verification and inline examples. Keep advanced JSON editing for every record and retain opaque fields when using forms. Offer a sample record per selected collection before building a broad form system.

**Acceptance:** a first-time user can author one functional requirement with observable acceptance, one material NFR scenario and one linked task without writing JSON. Form edits preserve unsupported fields and stable IDs. Technical users can still use the existing raw path. Test with actual beginners before expanding forms to every record type.

### E01-F06 — P2 — Continuation packet omits both project purpose and browser identity

**Classification:** verified output omission; evidence-backed continuity risk. **Evidence:** `workbench/project-core.js:51` returns name/revision, accepted decisions, constraints and questions, with neither brief nor content hash. The executed packet for a brief-only application contained no application purpose. CLI `tools/project_model.py:96` adds a source hash and coverage but also omits the brief. Full canonical import remains available; this is not loss in portable export.

**Recommendation E01-R06:** define a bounded shared continuation contract with canonical identity, concise brief/outcome, recorded acceptance, open blockers and a clear reference to the required canonical input. Either include enough safe context for a useful continuation or explicitly label the packet a summary requiring the exported project. Never imply automatic retrieval by hash or synchronization.

**Acceptance:** two different canonical projects at the same revision are distinguishable; a brief-only project retains its stated goal; unknown fields/history are still excluded. A user resuming from only the summary is told what context is missing. Browser and CLI show the same semantic fields, with any unavailable hash explicitly identified rather than invented.

### E01-F07 — P2 — Browser-to-CLI handoff has an avoidable manual gap

**Classification:** observed gap and improvement opportunity; usability impact unmeasured. **Evidence:** browser export at `workbench/index.html:52` downloads a name-derived `*-project.json`, while lines 20–27 show generic CLI commands using `./project`. Compiler `handoff` loads a project directory (`tools/artifact_compiler.py:145–148`); CLI readiness/resume also support file inputs, but the UI does not teach their difference. There is no profile selection or command bound to this export in the UI. The browser correctly discloses that it does not execute these commands.

**Recommendation E01-R07:** provide one compact “continue locally” guide after export: exact required file location/name, working directory assumption, command templates, profile meaning and expected output/check states. Optionally accept a portable file as input consistently in a future CLI change. Keep execution in the actual host; a copy-command guide is sufficient until demand justifies an adapter.

**Acceptance:** from a fresh export, a user can locate `project.json`, run the shown dry-run, understand blockers, generate a package and run the appropriate available checks without guessing paths or conflating Full specification depth with review-ready profile. Command text never includes opaque project fields or secrets. Missing optional tools yield a concrete next action and non-passing status.

### E01-F08 — P2 — Product demand and interaction value remain unmeasured

**Classification:** documented evidence limitation and strategic risk. **Evidence:** research template explicitly says instrument only, target segment hypothesis, no participants interviewed. Its three tasks focus on resume/change/handoff, omitting initial discovery, quick advice and actual implementation completion. `tools/workflow_tools.py:66–71` emits the same instrument. README acknowledges pending user observations. No fabricated research was found.

**Recommendation E01-R08:** run a small formative study spanning a technical lead and a less technical builder, with actual task outcomes and minimal consented notes. Include quick decision, incomplete idea, accepted-state change, handoff blocker identification and capability-limited implementation. Separately benchmark model outputs; do not use usability observations as a reasoning-quality score or agreement as ground truth.

**Acceptance:** retain anonymized actual observations, task completion/corrections/time, support needed, trust failures and counterexamples; distinguish product bugs from missing host capability. Compare current and revised journeys with predefined success criteria and report participant/sample limitations. Require repeated observed collaboration need before hosted shared state; require measured benefit before universal indexing or multi-model expansion. Numeric product success thresholds remain proposed until calibrated.

### E01-F09 — P2 — Conflicting release identities impede support and trust

**Classification:** verified documentation/metadata inconsistency. **Evidence:** README line 1 and `tools/project_model.py:6` identify 0.8.0. `plugin.json:4`, `capabilities.json:2`, repository core SKILL line 6 and workbench header line 5 identify 0.7.1; the HTML title says 0.7. Users cannot reliably infer which behavior or instructions a reported version denotes. This does not prove a package installation failure.

**Recommendation E01-R09:** choose one canonical release version and validate generated/package/display references against it. Distinguish project schema, backup schema and toolkit version explicitly rather than making them identical.

**Acceptance:** package manifest, skill title, capabilities, workbench and CLI agree on the released toolkit identity; schema/backup identities retain independent meaning. A release check fails mismatches before publication. Historical verification records retain their original attributed versions rather than being relabeled current.

## Coherent target experience and scope decisions

**Proposed primary segment:** technical leads and small engineering teams needing trustworthy design continuity and a concrete implementation handoff. This is a prioritization hypothesis, not a validated market conclusion. Beginner-friendly explanation should remain available; a nontechnical one-click application builder is a different product promise and should not be made without real execution integrations and evidence.

Preserve the three existing outcomes as the primary entry points: **Decide**, **Continue/change**, **Prepare handoff**. An optional **Implement with available host** action becomes visible only when actual capabilities support it. Keep intent/depth/audience independent, but expose them when useful rather than requiring users to learn an abstract mode taxonomy. Project data remains optional for the focused decision path.

For a stateful task, show project identity, local/draft/export state, requested outcome and the next useful action. A short task list should lead to the applicable record editor or blocker. Advanced graph/capacity/assessment and raw JSON remain available, with less prominence during first-project discovery. A giant dashboard or new agent framework is unnecessary.

The minimum proposed interaction contract is:

1. Capture the desired outcome and use existing evidence; ask at most two pivotal unanswered questions, only when the answer changes a material choice.
2. Produce a proportional proposal. Show assumptions and unresolved constraints; preserve recorded acceptance and opaque retained data.
3. Validate a proposed canonical delta and show the intended changed records before a consequential replacement. Keep draft editing separate from canonical commits and source execution.
4. For handoff, state requested scope and profile; show coverage, present-record validity, tool checks, human review and runtime evidence independently. The user must be able to find a blocker and the next action.
5. For implementation, discover actual host capabilities and authorization, bind the change/check plan to source identity, and record actual terminal outcomes. An unavailable execution capability produces an actionable handoff or blocked step, not simulated completion.
6. For resumption/recovery, identify the exact state, preserve recoverable bytes and point to one safe next action. Never infer cloud retrieval or automatic sync from an identifier.

Build internally: canonical continuity, clear record editing, scope/readiness semantics, impact explanation and portable exports. Integrate: source editing, actual builds/tests, browser automation and deployment through a capable host. Use alongside: source control/CI and existing issue/documentation systems, with explicit source identity. Defer: hosted collaboration, native app embedding, universal graph/vector services and autonomous multi-model orchestration until repeated demand and measured advantage establish their value. These decisions align with the repository's deferred strategy and avoid unnecessary replacement.

## Prioritized implementation sequence

| Stage | Findings / proposed initiative | Dependencies and reviewable exit |
|---|---|---|
| 1 — Restore task trust | R01–R04, R09: editor draft safety, bound record saves, requested-scope readiness, consistent replacement guards and version identity | Small changes to the existing UI/core/readiness logic. Exit: adversarial interleaving regressions, meaningful zero-record readiness test, existing preservation suite retained, synchronized release identity. |
| 2 — Make three journeys navigable | R05–R07: minimal requirement/ADR/task forms, bounded continuation contract and export-to-CLI instructions | Stage 1 invariants first; use the existing canonical schema and validators. Exit: first-project and resume/handoff walkthroughs completed without JSON/path guessing; unknown fields and acceptance preserved. |
| 3 — Measure before broad expansion | R08: actual formative observations and separate captured-response evaluation | Baseline task definitions and instruments; no outreach performed during this audit. Exit: attributable observations, limitations and a prioritized friction register. Avoid claiming a market ranking or causal productivity gain from a small study. |
| 4 — Add one verified execution journey if justified | Capability-aware implementation with existing host adapter, bounded change/check receipts and concrete fallback | A selected capable coding environment, authorization and source/check identity. Exit: one complete application/change is implemented and tested with actual evidence; no claims for unsupported deployments or unseen runtimes. |

Simplify as work lands: centralize repeated new/sample replacement predicates and draft logic; share continuation semantics between CLI/browser; remove duplicate version literals; group advanced calculation/assessment away from the primary discovery path. Do not remove the expert JSON escape hatch, canonical portability, truthfulness disclosures or recovery exports. Do not create a dozen new skills to compensate for a broken editing journey.

## Execution and transparency ledger

All shell Python invocations used `PYTHONDONTWRITEBYTECODE=1`; no checkout write or configuration change was made. Git status was clean and HEAD unchanged at the end of this pass. Reports/probes were written only under this reviewer's `expert01*` output paths.

| Actual action | Result and limit | Retained evidence |
|---|---|---|
| Source/brief inspection using `rg`, `nl`, `sed`, `cat`; Git HEAD/status | Baseline identity confirmed; source-backed product review. | Sources above. |
| `node tests/test_workbench.cjs` using Node 24.19.0 | **25/25 passed**, exit 0. Actual canonical core and inline script under minimal DOM, not real browser/a11y validation. | [expert01-workbench-tests.json](expert01-workbench-tests.json) |
| Custom probes using actual checkout core and inline handlers with the checkout's DOM harness | Reproduced F01, F02 and F04; observed F06. No visual/browser lifecycle claims. | [expert01-dom-probes.cjs](expert01-dom-probes.cjs), [expert01-dom-probes.json](expert01-dom-probes.json) |
| Initial custom-harness construction | A baseline deep equality check failed because values crossed VM realms; this was a reviewer harness artifact, not a Studio defect. The standalone repository suite passed. Corrected harness reuses only helper definitions; final run exit 0. | [expert01-dom-probes-initial-harness-error.json](expert01-dom-probes-initial-harness-error.json) |
| Python 3.12.14 `doctor` | Standard local capabilities reported; optional full OpenAPI validator and mmdc absent in this environment. No installation attempted. | [expert01-doctor.json](expert01-doctor.json) |
| CLI `resume` and `readiness ... --profile review-ready` on rich fixture | Resume output observed; five explicit readiness blockers returned. CLI command exit 0 for this reporting command does not imply review-ready success. | [expert01-cli-resume.json](expert01-cli-resume.json), [expert01-rich-readiness.json](expert01-rich-readiness.json) |
| Imported `readiness` and `compile_plan` on synthetic empty application project | Both accepted review-ready with zero records. Functions produced an in-memory plan; no handoff files were generated in the checkout. | [expert01-empty-readiness.json](expert01-empty-readiness.json) |
| Playwright 1.56.1 with installed `/usr/bin/chromium`, persistent profile under reviewer output | This expert's **un-escalated launch failed before page startup** with crashpad `setsockopt: Operation not permitted`, SIGTRAP. Zero browser checks completed; zero screenshots. This is a scoped failed attempt, not proof the host cannot run browsers with supported authorization. The coordinator separately reported successful supported browser execution; its evidence is outside this independent first pass. | [expert01-probes.cjs](expert01-probes.cjs), [expert01-browser-probes.json](expert01-browser-probes.json) |
| User/competitive/live-model research | **Not performed.** No participant outcomes, competitor ranking, model-quality lift, production deployment or real application completion claimed. | Research instrument limitations recorded above. |

Final expert verdict: **retain the architecture-first foundation, repair editing and readiness trust, then validate a small connected set of user journeys.** The evidence supports incremental repair and focused host integration. It does not justify a full rewrite, hosted platform build, universal repository intelligence service or expanding every conceivable lifecycle skill at once.
