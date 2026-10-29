# Project evolution and regression matrix — Expert 10 independent first pass

Baseline `83812e1d31c17ed857be8d2fb5c98126a8ccb5c8`, 2026-10-29. This is a current-source reconciliation, not a claim to have independently rerun every test. `RUN` below means executed in this track; `SOURCE` means inspected implementation and named tests exist but were not executed here; `HISTORICAL` means supplied repository evidence only. Other reviewer results may refine statuses during synthesis. No other reviewer report informed this first pass.

## Historical record and confidence

The user brief’s earlier 67 Python/14 workbench result corresponds to `release/verification-0.7.0.json` and the 0.7.0 changelog. The next repository receipt, `release/verification.json`, declares 77 Python/25 Node checks and 14 CLI integrations for 0.7.1. `release/counterexamples-0.7.0.json` explicitly records 10 Python acceptance counterexamples (nine failures, one error) and eleven additional workbench failures on the older baseline; those are historical baseline failures, not current failures. They provide useful regression intent but were not independently replayed against an archived baseline in this track.

Current Git history contains six commits: `1b4b744` first import; `6998867` adds reference/security validation, committed-journal guard, handoff identity fields and integration contracts; `061952e` adds six specialist skills, adapter docs and browser CI; `5cb748c` merges; `7a05e0b` and `83812e1` edit README. The current CLI/core version is 0.8.0 while manifests/status/receipts retain 0.7.1. Therefore historical success counts are not current release certification. Current focused evidence totals 27 tests, 26 pass/one fail; exact lists and traceback are in `reviewers/expert10-probes/`.

## Twelve explicit historical issues

| # / Historical finding | Previous status | Current evidence and regression test | Current status | Remaining risk and next action |
|---|---|---|---|---|
| H01 Malformed/incomplete schema crashes | M01 declared repaired; blank draft distinct from readiness | SOURCE `project_model.py:23–81` validates envelopes/arrays/IDs/finite transport; `test_release` has invalid-shape/rich-schema tests. RUN malformed verification references returns diagnostics | Fixed in code but insufficiently tested across every command in this track | Per-command prerequisites and schema/semantic parity need a command fixture matrix; do not equate valid draft with implementation readiness |
| H02 Lossy browser import/export | M02 declared lossless within supported bounded contract | SOURCE `project-core.js:37–42` retains canonical/opaque fields; explicit legacy/precision errors; `test_workbench.cjs` rich roundtrip/accepted retention tests | Fixed in code but insufficiently tested here | No current browser or full Node rerun in this track; portable handoff intentionally omits private/opaque fields and is not a private backup |
| H03 Nested snapshot growth | M03 flat snapshots, 20 count and 5 MiB budget | SOURCE `project-core.js:39–45` rejects nested envelopes, slices latest twenty and refuses byte overflow; tests include flat twenty and corrupt snapshot identity | Fixed in code but insufficiently tested here | Large repeated canonical payloads remain bounded by refusal; clarify retention versus recovery; never silently discard original import bytes |
| H04 Validators pass without verifying outputs | M06/M15 structural/full/report gates and installed adapters | RUN readiness waiver is not verification; missing outputs evaluator test; five current OpenAPI checks. SOURCE `validation_engine.py` per-check terminal states and gate logic | Partially fixed | Structural success remains scoped; no actual render/runtime evidence here. E10-F04 receipts lose gate failure; CI invokes missing checker; preserve terminal statuses end to end |
| H05 Weak OpenAPI security-reference checks | Earlier checks narrow; `6998867` adds followup validator work | RUN all five `AuditFollowupTests` reference/security tests: valid escaped local pointer; missing local ref; unknown security scheme; invalid referenced path parameter; external/nonstring ref rejection | Fixed and verified for these cases | Full OpenAPI conformance and framework/runtime authorization remain separate; preserve negative cases and optional offline schema validation |
| H06 Limited static repository analysis | M10/M25–28 add bounded AST/token/config adapters | SOURCE `repository_evidence.py:100–159`; Python AST/static JS imports/package/compose/CI/API descriptors; RUN cache/fitness counterexample | Partially fixed by design | Narrow adapters cannot establish complete dependency/runtime topology. Preserve unknowns, omission counts and explicit adapter support; add languages only from task demand |
| H07 Samples used as behavioral quality evidence | M14 now marked instrument pending | RUN unsafe/wrong response map passes 12/12, 100%, CLI gate exit 0. `behavioral_eval.py:82` truthfully labels lexical-only | Still present as a measurement gap, openly disclosed | E10-F05/EVAL-01: separate semantic reviewed-task gate, calibrated reviewers and captured actual outputs. Do not claim current model-quality gains |
| H08 Editing/recovery data loss | M02/M03/M19 declare defensive import, drafts, Accepted guard and recovery bytes | RUN conflict, snapshot retry, history recovery, restore-new-revision pass; SOURCE workbench original bytes/per-tab draft/Accepted checks and historical Node counterexamples | Partially fixed; selected CLI paths verified | Real browser interleaving and storage failure not measured here; advisory localStorage CAS is explicitly limited; E10-F02 lifecycle inconsistency remains |
| H09 Revision-history integrity | M05/0.7.1 journal validation and ordering repaired; later committed-state hash guard | RUN journal escape/tamper/conflict/init preservation, resulting-revision order, retry/history repair, committed mismatch and restore pass | Fixed and verified within selected local cooperating-writer scope | Local hashes/journals are not authenticated and locks are not distributed; no hostile-writer/power-loss proof. Add new faults only for uncovered invariants |
| H10 Stale/inconsistent handoff | M05/M07/M24 committed generation and manifests | RUN generation identity passes; existing canonical/projection identity test fails. SOURCE ownership-aware projections, `resolve_generation`, `freshness` hash comparison | Partially fixed | E10-F03: define representation hash domains; avoid treating mixed direct projections as coherent reads; source absence from partial scan stays unknown |
| H11 Cache overwrite/stale cache | M28 optional content/adapter/root keyed cache and ownership refusal | RUN `test_cache_parity_and_fitness_counterexample` and `test_cache_preserves_unrelated_file` pass; SOURCE key `rel:sha`, adapter/version/root checks | Fixed and verified for named invariants | Cached extraction is attributed data, not semantic truth; no stale conclusion becomes fresh from a hit. Keep malformed cache/error handling explicit |
| H12 Cost formula/unit errors | M32 raw intermediate math, finite checking, GB/GiB distinction | RUN `test_capacity_formulas` and `test_cross_surface_capacity_cases` pass; SOURCE `calculators.py:12–31` | Fixed and verified for conformance cases | Assumed rates and partial coverage do not become current provider quotes. Retain unit tests and omissions; no cloud pricing/performance benchmark measured |

## M01–M40 complete reconciliation

Status key: **S** scoped implementation evidenced by source; **V** selected invariant executed in this track; **P** partial/current gap; **I** instrument implemented, outcome measurement pending; **D** deferred as recommended. These are independent of the historical JSON’s broad status labels. A V never certifies the entire ambitious recommendation.

| ID | Current disposition | Current source / execution and qualification |
|---|---|---|
| M01 Canonical model | S/P | `project_model.py`, `project-v2.schema.json`; verification references RUN; lifecycle references not validated (E10-F02); broad command parity not rerun |
| M02 Lossless browser editing | S | `project-core.js`, `index.html`; rich/precision/opaque transport tests SOURCE, real browser not run here |
| M03 Flat snapshots/recovery | S | Core bounded flat envelopes and original bytes; browser tests SOURCE; CLI restore/retry RUN |
| M04 Filesystem containment/init | V | `safe_io.py`, `revision_store.py`; no-clobber history initialization/journal escape RUN; Linux local scope only |
| M05 Revisions/publication | V/P | Journal conflict/hash/retry/order/restore RUN; generation identity RUN; no distributed transaction claim |
| M06 Symmetric validation | V/P | Five new reference/security negative cases RUN; structural/full policies SOURCE; receipts lose gate result |
| M07 Contract handoff | S/P | Compiler preserves native/API and non-HTTP contracts separately; handoff hash semantics/test currently fail |
| M08 Diagram aliases/topology | S | Compiler aliases and explicit typed edges SOURCE; actual renderer not run |
| M09 Explainable graph closure | S | `graph_engine.py`, JS core, typed witnesses/tests SOURCE; connectivity is not causal proof |
| M10 Scanner scope/budgets | S | `repository_evidence.py` independent quotas, .github inclusion and partial coverage SOURCE |
| M11 Evidence envelope | S | `evidence-v1.schema.json`, observed hashes/version/source identity; no invented Git pin; SOURCE |
| M12 Untrusted/minimized export | S/P | `disclosure.py`, compiler and skill authority distinction SOURCE; pattern redaction incomplete; actual exported hash domain needs repair |
| M13 Resource bounds | S | Bounded reads/workers/deadlines SOURCE; evaluator tests RUN; no OS authority sandbox or host token enforcement |
| M14 Measured model quality | I/P | Capture/rubric/lexical instrument exists; unsafe responses RUN 12/12; actual comparative quality unmeasured |
| M15 CI gate semantics | V/P | Invalid API RUN exits 1 with policy false; report-only versus evaluate gate explicit; missing source-manifest checker blocks declared CI |
| M16 Per-artifact readiness | V | Waiver-not-verification RUN; independent completeness/human/runtime dimensions; no production readiness inferred |
| M17 Preflight/diagnostics | S | `doctor`, typed CLI errors and dry-run SOURCE; no unavailable tool execution claimed |
| M18 Intent/depth/audience | S | Skill and capabilities vocabulary SOURCE; outcome usefulness/routing accuracy unmeasured |
| M19 Safe correction/supersession | P | Browser deliberate Accepted edit guard SOURCE; predecessor test RUN; repeated supersession creates invalid lifecycle (E10-F02) |
| M20 Accessible bilingual authoring | S/P | Labels/dir=auto/focus/status and browser fixture SOURCE; assistive technology and actual browser usability unmeasured here |
| M21 Assumptions/risks/NFRs | S | Optional canonical records, scenario/readiness/verification distinction SOURCE; evidence quality not automatically established |
| M22 Continuation/freshness | S/P | `resume_packet` source hash/revision/unknown approver, compact accepted choices; probe shows malformed provenance forwarded; no chat sync |
| M23 Reviewable changes | S | Graph diff/change bundle and expected-hash commit SOURCE; CLI conflict RUN; no automatic acceptance rewriting |
| M24 Staleness/revisit | S/P | `freshness` content identity distinguishes unknown; generation hashes SOURCE/RUN; E10-F03 projection ambiguity |
| M25 Language/framework adapters | S | Python AST/narrow JS static declarations SOURCE; dynamic framework/runtime binding remains unknown |
| M26 Deployment/data/event extraction | S | Package/compose/CI/OAS/AsyncAPI descriptor adapters SOURCE; no generic IaC/runtime reconstruction |
| M27 Fitness counterexamples | V | Cache/fitness counterexample test RUN; violation versus satisfied-in-scope/unknown retained; no global grade |
| M28 Evidence delta/cache | V | Content/adapter/root addressed cache parity/no-clobber RUN; delta source inspected; no universal index |
| M29 Modernization packs | S | `migration_plan` declared seams, modularization-first stages and unknowns SOURCE; no migration executed |
| M30 Portable exports | S/P | Native artifacts/task and Accepted constraints exports SOURCE; hashes preserved; export is not tracker write, lifecycle/projection fixes needed |
| M31 Telemetry/metrics | P | Minimized receipt RUN records failed validation as completed; counts/identity/outcome insufficient for reliability metric (E10-F04) |
| M32 Capacity/scoring | V | Raw/unit-safe formula and Python/JS conformance RUN; assumptions and omissions explicit, no actual vendor quote |
| M33 Outcome journeys/examples | S | README/workbench blank versus samples and resume/change/handoff SOURCE; user benefit not measured |
| M34 Release conformance/package | P | Historical receipts retained; current 27 focused tests include one failure; version/inventory/CI mismatch E10-F01; full suite not rerun here |
| M35 Selective specialists | I | Protocol and bounded plan SOURCE; actual host needed; no benefit/cost comparison; this audit does not supply comparative baseline |
| M36 Experiments/sensitivity | S | Measurement/revisit worksheet and bounded scenario generator SOURCE; no provisioning or measured runtime benefit |
| M37 User research/outcomes | I | `research-kit`, observation template SOURCE; no participants, interviews, adoption or ROI evidence |
| M38 Hosted shared/native app | D | `strategy/deferred-decisions.md`; no service built; require repeated demand and auth/storage/operations design |
| M39 Universal semantic index | D | Existing local graph/adapters SOURCE; no graph/vector service; require representative retrieval value before build |
| M40 Autonomous multi-model expansion | D | Deferred protocol only; no autonomous deployment or model service; need measured benefit and host authority controls |

## Preservation and next release gates

Do not reopen the already demonstrated journal, cache and finite formula fixes without a new counterexample. Keep all historical counterexamples as regression intent. Repair E10-F01–F04 first, then create the actual-capture/review schemas and representative quality pilot in E10-F05–F06. An accepted decision remains a sourced historical decision; it does not authorize execution, authenticate an approver or require an approval interview for unchanged content.

Suggested current release evidence: exact commit plus dirty status; aligned package versions; complete checkable source inventory; current test receipt with passed/failed/skipped/blocked counts; explicit failure of the existing identity test until repaired; no required missing validator treated as green. Add only targeted lifecycle/hash/receipt counterexamples now. Separately report model evaluation and user research as pending until actual observations exist.

## Coordinator synthesis addendum (after independent first pass)

The scoped statuses above preserve Expert10's original evidence. Other independent probes refine the overall result: H02/H08 remain partial because Expert01 reproduces draft loss and cross-collection record corruption; H04/H05 remain partial because Expert05 reproduces YAML correspondence omission, duplicate keys, security-scope and empty-render false successes; H06/H11 are partial overall because Expert04 reproduces unsupported/parser-failed fitness passes, lost cold/warm cache diagnostics, silent edge truncation and cache overflow. Named historical cache no-clobber/parity tests still pass; do not generalize that to every cache invariant. Coordinator Chromium baseline 4/4 passes, while visual/screen-reader conformance remains unmeasured. See the canonical register for full attribution and acceptance.

Independent artifact paths: `reviewers/expert10.md`, `reviewers/expert10-probes/focused-tests.log`, `historical-tests.log`, `probe.py`, `probe.json`, `cli-probe.py`, `cli-probe.jsonl`, `wrong-responses.json`. No checkout changes were needed.
