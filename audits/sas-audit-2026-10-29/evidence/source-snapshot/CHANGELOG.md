# 0.7.1 — 2026-10-29

- Reject malformed recovery journals, path-like operation IDs, payload/hash/revision mismatches and conflicting history records before replacing project data. Preserve existing revision directories at initialization; list resulting revisions in commit order.
- Detect first-save conflicts between blank browser tabs. Keep recovery protection after failed imports; validate full backup/UI transport, snapshot identities and next-revision precision.
- Preserve Accepted records during record deletion/full-JSON edits; allow unchanged Accepted records and semantically identical object-key reorderings without reapproval. Failed calculator input cannot mutate UI state.
- Keep structural gates incomplete when YAML parsing is unavailable; normalize supported extensions and retain independent results after an unreadable subtree. Validate verification requirement references before coverage calculation.
- Add explicit counterexample regressions; preserve the existing binding, private audience and starter prompts. Actual browser/render checks and comparative/user measurements remain pending.

Validation: 77 Python tests, 25 Node code/DOM-model checks and 14 actual CLI integrations passed. New counterexamples failed on the actual v0.7.0 baseline and pass in v0.7.1. See release/verification.json.

# 0.7.0 — 2026-10-29

- Repair canonical project roundtrips, bounded snapshots, recovery and lossless editing. Preserve accepted facts, unknown fields and original import bytes.
- Add journaled revision commits, expected-hash conflict detection, coherent handoff generations and ownership-aware recovery.
- Compile declared contracts, typed diagram edges, data models, tasks, ADRs and acceptance obligations with explicit profiles and disclosure controls.
- Add typed impact/change witnesses, scoped static source evidence, content freshness, fitness counterexamples, optional cache and decision/migration worksheets.
- Separate actual validation from heuristics, incomplete checks and human judgments. Add installed full schema adapters, bounded subprocesses/regex and explicit CI gates.
- Improve local workbench navigation, independent intent/depth/audience, supersession, undo, tab drafts, session/purge controls and finite scenario arithmetic.
- Add captured-response/research/review instruments; do not claim unperformed model comparisons or user studies. Retain the report's M38–M40 deferrals.
- Preserve plugin identity, audience, binding and all starter prompt values/order. Optional validators are not installed automatically.

Validation: 67 Python tests, 14 Node code/DOM-model checks and 14 real CLI integration commands passed. Actual full OpenAPI and project JSON Schema workers passed. Browser launch and real Mermaid rendering were blocked by this host; those checks remain unverified. See release/verification.json and IMPLEMENTATION_STATUS.json.
