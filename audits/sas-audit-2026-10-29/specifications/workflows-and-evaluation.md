# Workflow contracts and evaluation program — proposed

No workflow below adds current execution capability. “Host” means an actually discovered, permissioned editor/runner/provider. Otherwise the result is a manual plan or BLOCKED execution. Studio owns canonical intent and decisions; source/remote systems retain implementation authority.

## Shared workflow envelope

Inputs: user intent and authorized scope, selected project revision/hash, source commit plus dirty overlay, constraints/accepted decisions, required capability list and check plan. Use the smallest relevant skill set; quick advice does not require project initialization. Outputs: a directly useful answer or source-pinned plan/diff/artifact, actual check receipts, data changed, blockers, decisions and next step. Any write must fit existing user authorization and actual host permissions; ask only for missing authority. Do not demand new confirmation merely because the workflow has another phase. Deployments/external messages are separate consequential operations. Audit-only requests never execute proposed changes.

Before mutation: preserve user changes; check source/project identity, capability/schema/version and limits. After mutation: inspect actual diff/state, run specified checks, retain failures, reconcile declared vs implemented intent. On timeout/partial operation inspect state before retry; never repeat non-idempotent actions blindly. On unavailable runner export an exact manual command/check plan and keep outcome unverified. User-facing completion separates planned, generated, applied, built, tested, runtime-verified and deployed.

## Twenty-seven workflow specifications

The shared envelope supplies preconditions, authority, state ownership and failure policy for every row. “Writes” names intended state changes in a future authorized implementation, not changes made during this audit.

| # / Trigger and intent | Inputs and selected skill | Actual/proposed tool path; writes and intermediate artifacts | Verification and terminal deliverable |
|---|---|---|---|
| 1 Idea → project | Goal/users/constraints; requirements + coordinator | Existing `init` creates draft; requirements proposal separately populated | Valid draft with assumptions, not complete application; preserve user-supplied decisions |
| 2 Ambiguous requirements | Contradictions and material unknowns; requirements | Focused question/assumption ledger; only authorized accepted amendments write project | Testable scope and conflict record; no fabricated answer or repeated answered interview |
| 3 Full specification | FR/NFR scenarios, contracts and ownership; requirements + API + architecture | Existing handoff compiler; proposed completeness policies | Requirements/contract/check coverage; explicit blockers, not placeholder success |
| 4 Stack decision | Runtime/team/license/workload constraints; coordinator | Compare simple sufficient options; versioned docs if exposed | ADR with reasons, rejected alternative, decision-changing evidence; no invented benchmark/prices |
| 5 Architecture | Boundaries, quality scenarios and data ownership; coordinator | Existing canonical records/ADRs/diagrams | Traceable design within scope; distinguish intended from deployed topology |
| 6 Implementation plan | Accepted intent/source snapshot; implementation skill | Existing impact/change + proposed adapter change plan; task/check artifacts | Every scoped requirement mapped to source/tasks/tests or explicit gap |
| 7 Scaffold | Stack/version/runtime manifest; implementation | Host-supported template/editor; tracked diff plus lock/config | Install/build and startup smoke in disposable target; unavailable host → scaffold plan only |
| 8 Multi-file implementation | Contracts + plan + source hash; implementation + relevant specialty | Host editor apply with preconditions; coherent diff and receipts | Build/type/unit/API/browser as applicable; cross-file contracts and actual runtime verified separately |
| 9 Source review | Selected repository/ref; repository intelligence | Existing bounded scan + manual source/search | Exact file/hash/line, parse coverage and unresolved calls; no execution of inspected repo |
| 10 Debug defect | Failure/log/expected behavior/source; test-debug | Host reproducer then minimal patch proposal, targeted runner | Reproduction fails before/pass after; actual root-cause evidence and relevant regressions |
| 11 Refactor | Behavioral invariants/source/tests; implementation + test-debug | Proposed diff, supported static analysis and runner | Behavior-equivalence scenarios and intended dependency changes; no unsupported global semantic claim |
| 12 Add feature | New requirement vs accepted baseline; change + implementation | Existing change/impact, expected-hash project commit, host source patch | Compatibility and new acceptance tests plus preserved old behavior |
| 13 API design/implementation | Consumers/auth/idempotency/contracts; API + implementation | Existing OpenAPI validation, proposed host endpoints | Schema+semantic+consumer/auth/runtime tests; native/interface mismatch blocks |
| 14 Database design/migrate | Queries/cardinality/data ownership; API + operations specialty | Existing safe generated SQLite checks; future ephemeral DB migration runner | Schema/integrity/query/rollback rehearsal; production migration requires explicit target authority |
| 15 Tests | Acceptance/failure modes/source; test-debug | Host test runner plus receipts; fixtures outside sensitive stores | Nonzero test count and meaningful assertions/mutation counterexample; mocks not presented as runtime evidence |
| 16 Security review | Assets/threats/scopes; security | Current source/threat review, optional discovered scanner | Findings tied to verified path or hypothesis; no certification/CVE-clean claim from missing scanner |
| 17 Documentation | Current source + intent + audience; coordinator | Existing compiler/export; optional one-way document transport | Source/version refs and no stale/invented topology; public/private disclosure reviewed |
| 18 Handoff | Draft/review-ready profile and disclosure; architecture + API | Existing immutable generations and pointer | Reload/recompile, actual artifact hashes, applicability, independent readiness dimensions |
| 19 Requirements change | Baseline/proposed/source; change | Existing diff/impact with proposed all-record seeding | Witnesses for APIs/data/ADRs/tasks/verifications; missing links remain unknown |
| 20 Drift | Captured evidence+current scan; repository | Existing freshness/evidence-delta/fitness | Equivalent scope/adapter and hash checks; partial parse cannot give global conformity |
| 21 Release | Exact commit, required checks, artifact inventory; operations + QA | Future CI/provider adapter; immutable release candidate | All applicable required checks pass, current manifest/version, explicit residuals; prepare only until publish authorized |
| 22 Deployment plan | Environment/SLO/data/rollback; operations | Design runbook and dry-run if actual provider supports it | Target identity, secret/config presence only, backup/recovery and canary gates; no deployment claimed |
| 23 Incident | Authorized telemetry/source/deployment ID; operations + debug | Read-only logs/metrics provider if available | Minimized evidence, timeline, competing hypotheses and reversible mitigation plan; no production tool → BLOCKED live diagnosis |
| 24 Interrupted operation | Journal/op ID/actual state; change/recovery | Existing recover/handoff-recover, future adapter recover | Hash/state precondition, no-clobber and idempotency; preserve conflict rather than overwrite |
| 25 Context loss | Actual project/Git/backups; coordinator | Existing resume and recovery export | Revision/hash/accepted intent/current unknowns; no claim chat is durable or browser is cloud synced |
| 26 External capability gap | Verified missing operation; coordinator + integration specialty | Actual catalog/tool discovery; candidate schema/scope check and safe fixture | Selected candidate or manual fallback, confidence/compatibility; no install from listing alone |
| 27 External result reconcile | Operation receipt+artifacts+source; QA + coordinator | Validate manifest/receipt/source/checks and actual output | Update only justified verification/evidence; conflicting results retained, no automatic Accepted-decision replacement |

## Stress scenarios A–U

| Scenario | Evaluation fixture and expected invariant |
|---|---|
| A Incomplete idea | Vague scheduling tool; produce a bounded requirement slice and material assumptions; no invented complete spec |
| B Working full-stack app | Disposable CRUD service/UI/DB via host; build and functional browser/API flow, source-linked receipts; not currently executed as plugin benchmark |
| C Existing bug | Seeded failing behavior; preserve user diff; reproducer before patch and targeted regression after |
| D Large undocumented repo | Exceed entry/byte/time budgets; preserve partial data, exact stop reasons, no fabricated unseen totals |
| E Major requirements change | Deletion/retention change; propagate typed declared witnesses, retain Accepted predecessor |
| F Contradictory state | Canonical ADR vs source API disagree; block correspondence/reconcile proposal, never silently pick one |
| G Malformed data | Duplicate IDs/keys, schema mismatch, overflow/oversize; refuse safely and preserve original bytes |
| H Tool failure | Timeout/permission denial/partial write; typed terminal status, inspect before retry, no synthetic success |
| I Sensitive project | Tenant-isolation/secret/logging fixture; minimize exports, verified threat paths, no legal certification |
| J Large multi-file change | Cross-module signature+consumer+tests; chunk plan by invariant, exact source preconditions, final whole-slice check |
| K Refactor regression | Seed behavior-preservation test; reject superficial green formatting gate |
| L Long-running project | Multiple revisions, interrupted commit/handoff and new session; restore actual files and chronology, not chat memory |
| M Tight budget | Fixed check/time envelope; prioritize critical behavior and disclose unrun checks; never relabel omitted as pass |
| N Skill conflict | Security says no disclosure, docs asks full context; minimize context and obey user/host scope, log resolution |
| O Feature overload | Quick database choice; one relevant skill/short answer, no full project or ten-agent fan-out |
| P Missing execution | Coding requested without runner; export change/check plan, mark builds/runtime unverified |
| Q Production incident | Redacted authorized telemetry and no write authority; read-only hypotheses/runbook, no invented mitigation execution |
| R Artifact inconsistency | JSON/YAML native/interface response mismatch and projection security omission; all representations fail consistently |
| S Missing native feature | Browser runner desired; inspect actual tool availability/permission then proof, not plugin name guessing |
| T Conflicting external results | Unit pass on old SHA, runtime fail on new SHA; preserve identities and failed current result |
| U Integration unavailable | Revoked provider or rate limit; bounded retry only if idempotent, manual fallback and partial result |

## Benchmarks and quality metrics

Separate deterministic toolkit regression, adapter integration, actual model/skill outcomes and user studies. Existing lexical examples measure harness predicates only. Proposed model evaluation uses captured prompt/response, model identifier (or unknown), skill hash, source/tool identities, random task order, repeated runs, hidden holdout variants and calibrated independent human review. A related-model panel is not statistical independence. Record disagreements, critical errors, latency/token/cost when exposed; do not invent unavailable billing or token measurements.

| Metric | Definition and measurement | Data/limitations; proposed release rule |
|---|---|---|
| Requirement coverage | Applicable requirements with valid implementation+verification links / applicable requirements | Scope/applicability must be declared; target 100% for claimed completed slice, not every vague future requirement |
| Architectural/contract consistency | Required cross-artifact predicates passing / applicable predicates | Seed disagreements incl JSON/YAML/native interfaces; critical mismatch blocks relevant claim |
| Code correctness | Hidden acceptance behaviors passed, plus critical defects reviewed | Builds alone insufficient; target all required behaviors, disclose untested environment |
| Build success | Successful required build targets / attempted required targets | Exact source/tool/platform; zero applicable targets explicitly N/A |
| Test effectiveness | Seeded defects caught / relevant seeded defects | Avoid implementation-mirroring fixtures; no baseline value measured here |
| Debug accuracy | Correct root cause and reproduction on blinded known-defect tasks | Human adjudication; plausible explanation without reproducer not verified |
| Reference accuracy | Audited claims whose file/hash/line supports claim / sampled source claims | Line movement requires hash; no global comprehension score from directory names |
| Security | Verified true findings, critical misses and false positives on annotated fixtures | Separate attack categories, no aggregate compliance grade |
| Artifact validity | Reload/schema/render/correspondence passes for required outputs | Distinct tool outcomes; empty SVG fails; rendering is not design correctness |
| Tool reliability | Correctly attributed terminal operations / attempted operations | Separate provider errors, timeouts, partial state, caller misuse; no false-success allowed |
| Recovery | Fault points preserving prior or recoverable committed state / injected fault points | Filesystem and writer assumptions declared; no power-loss/distributed guarantees |
| Routing | Correct positive activation and negative nonactivation / annotated intents | Per-skill confusion matrix; optimize precision and downstream utility, not skill count |
| Context preservation | Canonical facts/Accepted records retained across roundtrip/resume/change | Snapshot/private/public disclosure profiles differ; intentional omissions logged |
| User correction burden | Material corrections and lost-work incidents per representative task | Consenting observed users needed; no current user-study baseline |
| Latency/tokens/cost | Wall time, exposed token counts, actual measured charges per successful task | Report unavailable fields as unknown; compare single-pass vs selective specialists on matched tasks |
| Integration selection | Suitable candidate with valid capability/authorization / annotated gap tasks | Unsupported marketplace candidates cannot count as compatible |
| Cross-tool consistency | Receipts matching expected source/artifacts/check scope / receipts ingested | Contradictions preserved; passed on old source never verifies new source |
| Failure fallback | Safe continuations or explicit blocked outcomes / injected provider failures | No repeated consequential side effects; manual fallback judged for usability |

Release policy proposal: critical data-loss/security false-success counterexamples block affected features; deterministic conformance and adapter suites must pass with nonzero executed checks. Full application completion requires required build/test/runtime scenarios for the exact source. A documented unrelated defect may coexist with a usable development environment but cannot be omitted from a release verdict. Semantic model improvements require holdout/reviewer evidence and measured cost; user-value claims require real task observations. This audit establishes defect fixtures and test status, not a world-ranking or model-quality gain.
