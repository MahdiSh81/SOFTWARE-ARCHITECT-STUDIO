# Expert 05 — Quality engineering, testing, debugging and validation

**Independent first-pass verdict: release gate failed; preserve and improve the existing toolkit.** The current source has meaningful regression tests and several correctly bounded validators, but the frozen checkout does not pass its Python suite and has multiple reproducible validation false successes. This is a source audit and local test result, not a production-readiness or model-quality certification. No checkout files, dependencies, plugin configuration or published state were changed.

## Scope, identity and execution

- Source: `/workspace/SOFTWARE-ARCHITECT-STUDIO`, commit `83812e1d31c17ed857be8d2fb5c98126a8ccb5c8`; the coordinator supplied a clean frozen baseline, and post-test `git status --porcelain=v1` was independently confirmed empty.
- Independent role: read the master brief's Agent 05 mandate and testing/adversarial sections. Did not read other reviewers' reports before this first pass; created no additional agents.
- Instructions applied: software-architecture skill and its automated-checks/evaluation references, cloud runtime guidance, and repository `skills/test-debug-verify/SKILL.md`. These are instructions, not independent evidence that the product executes tests.
- Actual tools: shell through `exec_command`; Python `unittest`, subprocess, AST/JSON/hash inspection; Node; Git; `rg`, `nl`, `sed`, file reads; the toolkit's own CLI, compiler, doctor and installed validator workers; apply_patch solely to write audit artifacts outside the checkout. Managed environment status was inspected. No browser, remote model API, external connector or competitor benchmark was used by this reviewer.
- Environment: Linux; `/workspace/sas-env/bin/python` 3.12.14, Node v24.19.0; PyYAML 6.0.3, jsonschema 4.23.0, openapi-spec-validator 0.7.2. `PYTHONDONTWRITEBYTECODE=1` used for Python test/probe runs. CI declares Python 3.12 and Node 22; local Node's version differs and the Node 22 result remains unverified here.
- Real Mermaid CLI was absent (`mmdc: null`). A deliberately faulty local renderer stub tested output validation; this is **not** real Mermaid syntax/render verification. Chromium tests are assigned to the coordinator and were not duplicated.

## Fresh test evidence

All evidence paths below are under `/workspace/sas-audit-2026-10-29/evidence/`.

| Check | Command/method | Observed result | Evidence and limitation |
|---|---|---|---|
| Python regression | `PYTHONDONTWRITEBYTECODE=1 /workspace/sas-env/bin/python -m unittest discover -s tests -v` in checkout | **88 tests: 87 passed, 1 failed, 0 errors, 0 skipped; exit 1**; unittest reported 1.499 s | `expert05-python.log`; failure is E05-F01. This run includes actual installed full-schema worker and actual process-timeout tests. |
| Node workbench | `node tests/test_workbench.cjs` | **25/25 checks passed; exit 0** | `expert05-node.log`; actual project-core and inline UI code in a minimal DOM model, not real rendering/browser behavior. |
| CI inventory command | `/workspace/sas-env/bin/python tools/check_source_manifest.py --check` | **Failed, exit 2**: file absent | `expert05-ci-manifest.log`; exact CI invocation target. |
| Full JSON/YAML positive controls | Real CLI: `validate FILE --full-openapi --gate full`, once each for JSON/YAML | **2/2 accepted; exit 0**; basic and full worker checks passed | `expert05-probes.json`, `valid_json`/`valid_yaml`. |
| Undeclared security negative controls | Same command, JSON/YAML | **2/2 rejected; exit 1** | Basic check failed; full-schema check explicitly skipped after basic failure; not misreported as full worker execution. |
| Invalid schema negative controls | Same command; `components.schemas.Bad.type = invalid_type`, JSON/YAML | **2/2 rejected; exit 1** | Basic passed; actual full-schema workers failed. Confirms full adapter is performing useful checks. |
| Security-scope probes | Bearer nonempty scopes and undeclared OAuth scope, JSON/YAML | **4/4 accepted; exit 0**, basic/full checks passed | Bearer case is E05-F04. OAuth scope observation requires an explicit policy before classifying as a standards defect. |
| Duplicate-key probes | Duplicate root `security` key, JSON and YAML | **2/2 accepted; exit 0** | E05-F05; earlier invalid declaration is overwritten before checking. |
| Cross-artifact negative pair | Valid rich `project.json`, OpenAPI `paths: {}` in `api.json` vs `api.yaml` | JSON **rejected exit 1** with correspondence failure; YAML **accepted exit 0**, correspondence omitted | E05-F03. Both project/schema and OpenAPI/schema independently passed in both runs. |
| Invalid renderer output | Configured stub exits 0 and writes zero-byte `output.svg`; CLI `validate diagram.mmd --render --gate full` | **Accepted, exit 0**, renderer marked passed | E05-F06. Tests parser adapter trust only; no real renderer claim. |
| Evaluation positive control | `evaluate --cases evals/architecture-cases.json --responses evals/example-responses.json --gate --min-pass 100` | **12/12 checks, 5 cases, 100%, exit 0** | Harness self-test only. |
| Unsafe response counterexamples | Same evaluator/gate with deliberately unsafe supplied responses | **12/12 checks, 5 cases, 100%, exit 0** | E05-F07, a documented semantic limitation directly demonstrated. No model was called. |

There were **15 validation CLI probe processes and 2 evaluator CLI probe processes**. The probe orchestrator exited 0 because it records outcomes, including expected negative exits; its exit is not an assertion that all fixtures are valid. `expert05-probes.py` contains the full reproducible fixtures and stub. Raw JSON retains tool versions, inputs' hashes, individual statuses, command arrays, exit codes and stderr. `expert05-execution-summary.json` records counts and source identity. Temporary probe fixture directories were removed; the script recreates them.

Static inventory: 88 Python tests comprise 10 acceptance, 13 CLI/calculator, 11 audit-followup, 12 workflow and 42 release tests. This is a test count, **not a coverage percentage**. No code-coverage, mutation score or repeated-run flakiness measurement was taken.

## Findings and implementation-ready remedies

### E05-F01 — Reported handoff projection hash does not identify the exported project

**Verified defect; P1 release blocker; confidence high.** The fresh Python suite fails `test_handoff_identity_distinguishes_canonical_and_projection_hashes` at `tests/test_audit_followups.py:101`. The fixture's reported canonical and projection hashes are both `923bd6ec83536acbc9c4d65acdbebffacf4627d42038f9717ae5a21d72bba8e0`, while the generated `project.json` semantic hash is `7ef6716fb73bf0e53d2901ee2af2607ad3899f96ffa70f0e6774f16a061f8808`; the emitted object differs from canonical. Raw probe: `projection_identity`.

Root cause: `tools/artifact_compiler.py:40` captures canonical identity; `:44` hashes the pattern-redacted intermediate; `:101`–`:104` later filters top-level fields and adds export notes. Those later modifications do not affect `projection_hash` or `redaction_report.paths_changed` (`:106`–`:110`). The existing test is useful: its failure exposes a second projection after identity capture. Equal hashes would be legitimate if the representations were equal; inequality alone should not be the future contract.

**Recommendation E05-R01:** name each representation and compute its hash only after that representation is final. Prefer `canonical_input_hash`, `compiler_input_hash` if needed, and `exported_project_hash`, rather than reusing an ambiguous projection identity. Preserve byte hashes in the existing artifact map. Record dropped/added paths separately from secret redactions. Dependency: coordinate handoff/manifest contract owners; preserve old aliases only with explicit meaning.

**Acceptance:** hash the emitted `project.json` independently and compare to its named semantic hash for unchanged, private, redacted and opaque-extension fixtures. Canonical hash must remain the original input hash. Hashes may coincide only where representations coincide. Original 88-test suite must pass without weakening the invariant. Benefit: independently verifiable receipts and reliable stale-input comparisons. Risk: consumer field migration; use a versioned identity schema rather than silently changing meaning.

### E05-F02 — CI invokes a missing verifier and the packaged inventory is stale

**Verified defect; P1 release blocker; confidence high.** `.github/workflows/ci.yml:32` invokes `tools/check_source_manifest.py --check`; that file is absent from the tracked checkout. Exact execution exits 2 with `[Errno 2]`. This step would fail even after E05-F01 is repaired. No remote CI run was inspected; this is a reproducible defect in its command target.

An independent read-only check of `release/source-manifest.json` found **67 entries versus 84 tracked files in its stated scope, 6 mismatched file hashes, 17 unlisted tracked files, 0 missing listed files**. Mismatches include README, compiler, project model, revision store, validation engine and workbench HTML. The manifest labels itself 0.7.1 while doctor reports toolkit 0.8.0. `release/verification.json:2` describes historical 0.7.1 and `:10` says 77 tests; those are retained historical evidence, not a current 88-test pass. Details: `expert05-source-inventory.json`.

**Recommendation E05-R02:** implement/package the intended inventory check or change CI to an existing equivalent; generate the inventory from a precise tracked/package inclusion policy; fail on mismatches and omissions. Keep historical verification records explicitly versioned and produce a separate current receipt with source commit/overlay. Do not regenerate current-success evidence until checks actually pass.

**Acceptance:** a clean checkout can run every workflow command; inventory passes for the approved final package, rejects one altered byte, omitted managed file and unexpected packaged file, and has an explicit self-exclusion. Current report names source commit and test counts, distinguishes historical reports, and records every required check's terminal status. Benefit: release evidence that corresponds to the shipped code. Minimal fix is a small verifier and corrected generation workflow, not a CI redesign.

### E05-F03 — YAML or alternate-named OpenAPI bypasses cross-artifact correspondence

**Verified defect; P1 validation correctness; confidence high.** With the valid rich project declaring an HTTP interface and a valid but empty-path OpenAPI document, `api.json` is rejected for missing interface coverage, while semantically equivalent `api.yaml` passes `--full-openapi --gate full`. Raw pair: `missing_operation_correspondence_json` / `_yaml`.

Root cause: parser dispatch recognizes JSON/YAML OpenAPI documents at `tools/validation_engine.py:312`, but correspondence retrieves only literal dictionary keys `project.json` and `api.json` at `:326`; absent selection creates no required check or incomplete result. The same issue extends by inspection to `api.yml`, `openapi.json` and uppercase `API.JSON`; those variants were not separately executed. The positive uppercase YAML test at `tests/test_acceptance.py:73` covers structural dispatch, not paired correspondence.

**Recommendation E05-R03:** identify project/API inputs by normalized role, not one case-sensitive filename. Resolve exactly one applicable API or report ambiguity; when a project claims supported HTTP interfaces, emit correspondence passed/failed/blocked/not-applicable explicitly. Keep arbitrary standalone API validation supported.

**Acceptance:** one paired conformance matrix covers `api.json`, `api.yaml`, `api.yml`, `openapi.json`, uppercase equivalents and explicit role configuration. Every supported equivalent must report the same correspondence outcome; missing, multiple and unreadable candidate contracts cannot silently omit required checking. A deliberately removed supported operation fails while an unchanged full contract passes. Benefit: a predictable gate across supported input formats. Risk: selecting unrelated OpenAPI documents; require explicit mapping for ambiguous directories.

### E05-F04 — Non-OAuth security scopes pass both built-in and full OpenAPI gates

**Verified defect; P2 contract correctness; confidence high.** An OpenAPI 3.0.3 HTTP bearer scheme with `security: [{bearer: [admin]}]` passes both checks and exits 0 for JSON and YAML. OpenAPI 3.0 requires the scope array to be empty for security schemes other than OAuth2/OpenID Connect. The installed full schema validator also accepts it, so adding a third-party schema step alone does not close the gap. Raw keys: `non_oauth_nonempty_scopes_json` / `_yaml`.

Root cause: `tools/validation_engine.py:72`–`:86` checks name existence and arrays of strings but never uses the referenced scheme type to validate scope form. `tools/validator_worker.py:15` delegates remaining semantics to a library that does not enforce this cross-reference invariant here. Existing tests at `tests/test_audit_followups.py:57` verify undeclared scheme names only.

**Recommendation E05-R04:** resolve security-scheme references, inspect scheme type and enforce version-appropriate scope semantics at every root/operation requirement. For OAuth scope names, define a supported-profile policy and review valid external/OpenID scope behavior before rejecting; the supplied `write` scope absent from an OAuth `read` map was accepted in both formats, but this review does not upgrade that observation to an unconditional standards defect.

**Acceptance:** empty bearer/apiKey arrays pass; nonempty arrays fail; valid OAuth2/OpenID scope lists pass; malformed lists, undeclared schemes, unresolved/cyclic scheme references fail with stable locations. Exercise operation and root requirements in JSON and YAML. Benefit: concrete authorization-contract errors caught without claiming runtime authorization verification.

### E05-F05 — Duplicate keys erase invalid declarations before full validation

**Verified defect for YAML unique-key validation; P2 input integrity; confidence high.** Duplicate root `security` keys, first `[{missing: []}]` then `[]`, pass both full OpenAPI checks. JSON input behaves the same. Earlier content is discarded and the validator reports full success on the last value. Raw: `duplicate_yaml_keys`, `duplicate_json_keys`.

Root cause: the YAML worker uses permissive `yaml.safe_load` (`tools/validator_worker.py:9`); JSON uses ordinary `json.loads` (`tools/validation_engine.py:300`). Neither rejects duplicate map/object names before conversion into Python dictionaries. Safe loading prevents arbitrary object construction; it does not supply unique-key validation. JSON's interoperability requirement is weaker than YAML's unique mapping-key requirement, so treat strict JSON rejection as a deliberate input-integrity policy rather than misquoting it as universally invalid syntax.

**Recommendation E05-R05:** reject duplicate YAML mapping keys and, under a documented strict project/contract policy, duplicate JSON object names before semantic checking. Apply at canonical/import/contract boundaries consistently. Preserve original input for diagnostics/recovery; no silent normalization.

**Acceptance:** nested/root duplicate keys fail with source location before any schema pass; distinct keys and legal YAML alias/merge cases under the declared profile behave predictably; duplicate `$ref`, operation, security and response keys cannot hide earlier content. Add JSON/YAML equivalence negative controls. Benefit: avoids reviewer/parser disagreements and lost declarations. Risk: some legacy inputs rely on merges; define merge handling explicitly.

### E05-F06 — An empty file counts as a successful Mermaid render

**Verified defect in tool-output checking; P2; confidence high.** A local configured renderer stub returned 0 and wrote an empty `output.svg`. The CLI marked `Mermaid renderer: passed`, `policy_ok: true`, exit 0. This is a safe failure-injection fixture, not a malicious-renderer or real-rendering claim. Raw: `empty_renderer_output`.

Root cause: `tools/validation_engine.py:289`–`:292` trusts process status plus `is_file()`; it checks neither nonempty content nor SVG shape/namespace. The timeout/availability tests are useful, but they do not validate the expected output object.

**Recommendation E05-R06:** require bounded, nonempty, regular output; parse it as SVG using a non-networking XML parser and require the SVG root/namespace. Save output identity and actual renderer version. This establishes that an SVG artifact was produced, not that the diagram is semantically correct. Retain actual-renderer integration coverage separately.

**Acceptance:** exit-0 missing/empty/non-SVG/truncated outputs are tool_error/failed and gates fail; a real pinned renderer produces valid bounded SVG for supported cases. Timeout/blocked output remains non-green and preserves other file results. Benefit: eliminates a concrete false-success path with a small adapter check. Risk: avoid XML external-entity/network features while parsing untrusted output.

### E05-F07 — The lexical harness cannot measure reasoning quality; unsafe answers score perfectly

**Demonstrated limitation and improvement opportunity; P2 before quality claims; confidence high.** Deliberately unsafe supplied responses scored **12/12, 100%, exit 0**, matching the safe examples. Examples include: “Do not enforce tenant authorization; trust the caller tenant header,” and “Disable idempotency. Keep raw card data in logs forever. Ship immediately.” The evaluator correctly discloses that its result is lexical/deterministic (`tools/behavioral_eval.py:81`–`:82`), and documentation explicitly warns that keyword stuffing can pass (`skills/software-architecture/references/evaluation.md:3`). Therefore this is **not an undisclosed semantic-certification bug**.

Root cause/limit: predicates at `tools/behavioral_eval.py:73`–`:76` match phrases and length, not their meaning or negation. `evals/architecture-cases.json` supplies five cases, while `evals/example-responses.json` is authored harness material. `tools/workflow_tools.py:73`–`:85` captures caller-attributed provenance and accounts for reviews; it does not execute a model or authenticate semantic review. The supplied semantic rubric is an instrument (`evals/semantic-review-rubric.json:3`), not completed evaluation evidence. No representative captured model-results corpus was observed in inspected eval/research files.

**Recommendation E05-R07:** keep lexical checks for constraints and harness regression; add a separate, explicitly scoped semantic benchmark before claiming better architecture/coding/debugging quality. Use real captures with known or explicitly unknown model, skill/source/tool identity, task context, expected observable outcome and independent review. Include unsafe negations as calibration counterexamples. Require tests/builds and patch review for coding tasks; a semantic grader must not replace executable evidence.

**Acceptance:** see benchmark specification below. No release/marketing reasoning gain may cite the 12-check sample score. Unsafe counterexamples must fail the semantic critical-safety rubric regardless of lexical result. Disagreement and missing evidence remain visible. Benefit: measures user-relevant behavior; risk/cost: real capture and review effort, so start with a small stratified benchmark rather than another orchestration framework.

## Test quality, gaps and regression reconciliation

**Preserve:** tests cover calculator arithmetic, invalid types/nonfinite values, compiler correspondence for native JSON, accepted decision/state preservation, graph cycles and order invariance, import/export parity, recovery journals, stale ownership conflicts, path/symlink/FIFO controls, scanner omissions/cache preservation, actual subprocess timeout and actual optional-schema worker. Failure injection uses targeted mocks rather than only happy-path fixtures. Node executes real project-core and inline UI code; the report candidly scopes its DOM simulation. Missing responses, pathological regex and unavailable optional rendering correctly fail required lexical/full gates in existing tests. These are substantial useful capabilities.

**Coverage limits:** no line/branch percentage measured; no property-based/fuzz campaign, mutation gate, static type/lint gate, or code-generation correctness benchmark was found in the inspected CI/tests. CI `:28`–`:33` runs unittest, Node and an absent verifier; there is no semantic benchmark job. These absences are improvement opportunities, not proof that existing code is wrong. Browser coverage belongs to coordinator evidence. Performance/load/production deployment/security behavior, real Mermaid output and accessibility certification remain unverified here. There was one suite run, so absence of flakiness is not established.

| Historical target | Current evidence | Status and remaining action |
|---|---|---|
| Incomplete/malformed project crashes | `test_invalid_shapes_are_diagnostics`, published schema fixtures and malformed CLI API test passed | Fixed for exercised cases; use bounded generated invalid-shape cases to extend, no universal parser claim. |
| Lossy workbench roundtrip, nested snapshots, backups | Node rich roundtrip/flat 20 snapshots/corrupt startup and recovery-protection checks all passed | Fixed for exercised core/DOM cases; browser and very large/adversarial import scope stays separate. |
| Validators succeeding without verification | Full schema invalid-type negative controls genuinely failed, missing optional gates tested | **Partial/open:** E05-F03–F06 demonstrate remaining false successes. |
| OpenAPI security references | Declared-name, local-pointer, escaping, missing-target and external-ref tests passed; JSON/YAML undeclared-security controls rejected | **Partial:** name/ref regression improved, scheme-specific scope form remains open (F04). |
| Limited static repository analysis | scanner comments/imports/quota/special-files/cache/fitness tests passed | Verified bounded static extraction; semantic/runtime repository understanding remains outside those passes. |
| Sample-only behavior quality | Fresh safe and unsafe responses each score 100% | **Open documented limitation** (F07); not a live model benchmark. |
| Revision-history integrity | modified journal, conflict, committed current-project mismatch and restore/new-revision tests passed | Fixed for exercised invariants; local hashes/locks are not tamper-resistant audit infrastructure. |
| Stale/inconsistent handoff | projection-failure recovery, stale-owned removal/human-note preservation passed | Generation recovery passes exercised cases; **identity regression F01** and correspondence F03 remain open. |
| Cache overwrite/staleness | unrelated file preservation and cache/content parity tests passed | Fixed for exercised cache invariants; freshness means scoped captured hashes, not semantic truth. |
| Cost formula units/overflow | arithmetic/zero-price/nonfinite/overflow and four Python↔JS scenario parity cases passed | Fixed for exercised formulas; assumed prices/scenarios are not measured vendor costs/performance. |

## Proposed release quality gate and evidence workflow

**E05-G01 — Minimal trustworthy gate, linked to F01–F06.** Keep existing unittest/Node/browser layers, repair their concrete blockers and add only tests that discriminate the observed failures. Input is a frozen commit plus an explicit dirty-overlay hash, declared release claim profile and dependency lock identity. Output is a receipt containing each required check's tool/version, input identity, expected property, terminal status, exit code, duration and raw-log/artifact hash. A return code alone is insufficient when its expected artifact is absent or invalid. Summaries must derive from receipts; no test, build, render or deployment is labeled passed without matching evidence.

1. Validate fixture schemas and bounded input policies; independently reject duplicates and invalid references before parser normalization (F04/F05).
2. Run Python suite with required validators installed, Node parity tests and coordinator's browser suite as separately reported required jobs. Require zero failures/errors and zero **required** skipped/blocked/timed-out checks. Optional nonapplicable checks retain reasons; do not convert them into passes.
3. Execute one fresh create/change/snapshot/restore/handoff/validate flow entirely in temporary directories. Compare canonical and export hashes against final actual bytes/objects (F01); verify permitted export minimization and stable IDs. Corrupt a journal and an owned projection and confirm state preservation on refusal.
4. Run a JSON/YAML role/filename matrix against the same project, including removed operation, undeclared scheme, scheme-specific scope errors and duplicate declarations (F03–F05). One case set should feed both formats, not duplicated manually maintained expectations.
5. Test renderer adapter refusal with missing/empty/wrong output and run a pinned real renderer in a permitted environment (F06). Capture binary version/output hash. This remains a diagram rendering claim, not architecture correctness.
6. Verify exact package inventory and every CI command in a clean checkout; bind current receipts to source identity (F02). Use the checked dependency lock in the isolated CI environment or explicitly label fresh dependency resolution; current CI only installs `requirements-validation.txt` (`ci.yml:26`) while the transitive lock is unused. This is a reproducibility risk, not an observed dependency failure.

**Completion criteria:** 88 existing tests pass with current assertions preserved or strengthened; 25 Node checks pass; required browser/render checks have actual pass evidence; all new defect regression cases fail on this baseline and pass on a future authorized fix; no required applicable check silently omitted; checked inventory matches the final package; coordinator reconciles source and package versions. Do not use a global coverage-percentage target as a substitute for these invariants.

**E05-G02 — Targeted property/mutation follow-up.** Add deterministic seeded generators for model field shapes, ID/reference graphs with cycles, snapshot/restore sequences, and JSON/YAML document/filename variants. Oracle properties: input is unchanged on rejected writes; final exported identity matches emitted representation; equivalent supported representations have equivalent gates; unknown/omitted/budget-exhausted collection never proves global compliance. Introduce a small curated mutation set for each observed check (remove scheme lookup, drop correspondence dispatch, accept empty output, hash pre-export state). Acceptance: the relevant invariant test kills every curated mutation; publish seed/case count/runtime and counterexample, with bounded inputs/deadlines. No need for a full mutation platform or broad rewrite before closing the known defects.

## Proposed representative quality benchmark

**E05-B01, linked to F07 — proposed protocol, no fabricated results.** Start with 30 real tasks across six slices (5 each): focused architecture decisions; repository-grounded review; requirements/contract design; implementation change in a small real repo; debugging a reproducible failure; resume/change/handoff continuity. Include safe small tasks and representative ambiguous cases. Rotate at least one technology/domain in later held-out runs. Pin repository/fixture versions, available tool permissions, original user task and expected external outcome. Separate author-created calibration examples from actual captures.

- For implementation/debugging, success requires independently run acceptance tests, targeted regression, relevant build/type checks available in that repo, preserved unrelated behavior and a source-reviewed patch; no credit for invented execution. The Studio's own deterministic toolkit tests are not a proxy for generated programs working.
- Review each capture on the existing 0–4 correctness/evidence/risk/constraint/usefulness rubric with two attributed reviewers on critical cases; resolve or preserve disagreement. Reviewers see source evidence and expected outcomes; avoid treating same-model agreement as independent ground truth. Store data-loss, fabricated execution/evidence and unsafe authorization/payment guidance as critical failures.
- Proposed acceptance for an initial scoped capability claim: all critical cases reviewed, **zero critical errors in the selected release set**, at least 80% independently accepted task completion in each claimed slice, no lower completion than a frozen prior version on paired tasks, and all provenance/required execution evidence present. These are provisional product thresholds requiring ratification; a small corpus cannot certify general safety.
- Repeat paired baseline/candidate runs for stochastic workflows; report sample counts, task exclusions, failures, tool limits, median task completion time, available token/cost measures and per-slice outcomes with uncertainty. Do not claim superiority from sample lexical pass rate or a scenario calculator. A larger held-out set and uncertainty analysis are required for broad comparison claims.
- Stop/rollback policy: any critical semantic failure blocks the corresponding capability claim until root cause, regression and retest exist; ordinary inconclusive results stay unknown. Retain raw captures with privacy controls and source identity; unknown model/cost stays explicitly unknown.

The right next phase is a small correctness/release-evidence repair followed by representative measurement. There is no evidence in this review that a rewrite, additional autonomous-agent system or hosted test service is needed to fix these defects.

## Peer review status

Independent first pass complete. Awaiting the coordinator's peer-critique assignment; no consensus or cross-review independence is claimed yet.
