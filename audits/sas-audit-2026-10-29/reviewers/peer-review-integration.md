# Integration peer adjudication — Expert 08

2026-10-29. This note follows my completed independent pass. It preserves `expert08.md` and records a correction after reading E02-F04, E03-F03/F04, E05-F01 and the relevant implementation. No additional tests or source changes were made for this peer pass.

## Correction and disposition

**I withdraw the implication that the failing hash assertion is likely only a bad fixture.** My initial observation was valid but incomplete: equal hashes can identify equal representations, and an unconditional inequality assertion is not a general identity contract. I inspected the empty redaction list but did not follow the later export transformation far enough. The peer counterexamples demonstrate a real handoff defect independently of that assertion.

`tools/artifact_compiler.py:40–44` hashes the canonical input and the pattern-minimized compiler context. Lines 101–104 subsequently omit top-level fields and replace notes before emitting `project.json`. Those transformations occur after `projection_hash` is fixed and do not enter `redaction_report.paths_changed` at lines 106–110. Therefore the observed `923bd6ec…` identity is accurate for an intermediate object, while the final exported object is `7ef6716f…`. Existing `artifact_hashes['project.json']` independently identifies the emitted bytes correctly; this is neither a SHA-256 failure nor evidence that all artifact hashes are wrong.

**Accept E02-F04, E03-F04 and E05-F01 as the same representation-identity defect.** Avoid counting them as independent defects in synthesis. Ambiguous identity alone is P2; its use for resumable handoff or adapter reconciliation makes the repair a release prerequisite. Version the identity contract: `canonical_input_hash`, optional `compiler_context_hash`, `exported_project_hash`, and artifact-byte hashes must name their exact representations. Record omissions/additions/replacements separately from sensitive-value redactions. Preserve legacy aliases only with explicit meaning.

**Accept E03-F03 as a distinct P1 handoff-integrity defect.** `rich-project.json` retains interface `security:[{session:[]}]`, but the default export allowlist drops its native `api_contract` containing the scheme definition. Recompilation consequently reports the undeclared `session` scheme. The first bundle still contains valid `api.json`; the demonstrated failure concerns independently reloading/regenerating the exported project. Preserve supported native contract fields after disclosure checks, or provide a documented offline reference loader. Excluding opaque private extensions does not justify excluding supported native contracts required for regeneration.

Acceptance must compare every named hash to its final actual representation; allow equal hashes for equal representations; verify omission accounting; and exercise default/private, unchanged/redacted, native-only and extension-bearing cases. Export→import→compile must preserve applicable native security/components/references semantically and resolve them offline. A redaction that breaks a necessary reference must block readiness. Strengthen the existing failing test around these properties rather than force inequality or merely delete the assertion.

## Receipt/effect specification refinement

E03's adapter specification and E08-F03/F04/F05 agree on the critical boundary. Consolidate them into one contract rather than parallel incompatible receipt formats. Add three explicit dimensions:

- **Operation outcome:** applied/partial/failed/unknown, with a commit point and recovery reference; receipt persistence has its own outcome. The reproduced `init` success followed by receipt-write failure must return committed state plus telemetry failure.
- **Execution evidence:** request/check-plan identity, expected and observed starting source, observed ending source, actual artifacts and per-required-check terminal outcomes. A process exit or an intermediate projection hash cannot establish tested state for different resulting bytes.
- **Effects and authority:** host-approved effect scope and observed effects, with unknown observations retained. Require an authorization reference for attempted or observed consequential effects, including failed/partial operations; requiring it only for `status: passed` misses partial writes. A reference still does not grant authority. Running repository tests can write files or access networks and must not be authorized merely because a runner labels the operation `read`.

Fault-injection acceptance should cover failure before mutation, between writes, after commit and during receipt persistence; later user edits; mismatched runner/capability/source/version; missing required checks; and tests that modify source. Each result must expose actual or unknown state, preserve unrelated data, and prevent blind non-idempotent replay. These remain proposed implementation obligations, not capabilities verified by this audit.
