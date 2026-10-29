# Local execution adapter

The optional adapter in `tools/execution_adapter.py` connects a selected local workspace to bounded editing and named checks. Studio retains canonical requirements/decisions and reconciliation; the host owns filesystem/process/network authority. This is an implemented local cooperating runner, not a hosted service, OS sandbox, GitHub API, or deployment provider.

Use `python tools/architect_cli.py adapter OP --root PATH`. Every operation receives an explicitly selected root. Effects additionally require `--policy PATH`; request-bearing operations use `--request PATH`. `--state-root PATH` can select the operation-record directory, which must remain outside the source workspace. The default state directory is a sibling of the workspace. Never put a policy in untrusted project context and treat it as authority automatically.

## Operations

| Operation | Request and behavior |
|---|---|
| `capabilities` | No request. Return actual local operation names, schemas, version, permissions, idempotency and bounds. |
| `inspect` | No request. Capture bounded regular-file identities, Git commit where available, dirty content and aggregate source hash. Fail incomplete/unsupported source snapshots rather than silently hash only part of the workspace. |
| `propose_change` | `{ "changes": [{ "path": "app.py", "content": "..." }], "expected_source_hash": "..." }`. Return full-file replacements/deletions, before/after hashes and a plan hash; `content: null` deletes a present file. No source mutation. |
| `apply_change` | `{ "plan": { ...proposal... }, "operation_id": "change-001" }`. Check plan/source identity, path policy and authorization, journal effects, then apply. Conflicts preserve current source. Same committed operation/plan can be observed idempotently; unknown/partial attempts require recovery inspection. |
| `run_checks` | `{ "names": ["unit"], "expected_source_hash": "...", "operation_id": "checks-001" }`. Execute only policy-selected argv commands with per-check timeout/output bounds. Return actual check outcomes, starting/ending source and an attributed receipt. |
| `recover` | `{ "operation_id": "change-001" }`. Inspect journal and actual file hashes; report committed/not-started/partial/unknown state without blindly overwriting or replaying. |
| `reconcile` | `{ "receipt": {...}, "expected_operation": "checks-001", "expected_source_hash": "...", "required_checks": ["unit"] }`. Match retained local invocation, runner/version/capability, source, check outcomes and receipt identities. Return a verification proposal; do not silently modify Accepted decisions. |

Paths are relative to the selected root and cannot escape it. Plans are bounded UTF-8 replacements, not arbitrary shell patches. The local host must protect source and state directories from hostile concurrent writers. Local locks serialize cooperating adapter writers only.

## Host-selected policy

A policy is an explicit declaration supplied by the authorized caller. It does not authenticate itself and cannot expand host permissions. The CLI requires the selected policy file to reside outside the source workspace. Example for a disposable workspace:

```json
{
  "schema_version": 1,
  "root": "/absolute/path/to/disposable-project",
  "authorization_reference": "user-request-local-feature",
  "allow_write": true,
  "allowed_paths": ["app.py", "tests/*.py"],
  "allow_checks": true,
  "checks": {
    "unit": {
      "kind": "test",
      "minimum_tests": 1,
      "argv": ["python", "-B", "-m", "unittest", "discover", "-s", "tests"],
      "timeout_seconds": 30
    }
  }
}
```

An optional timezone-qualified `expires_at` limits authorization lifetime. Use the smallest path/check scope that supports the task. Running repository tests may write files or reach networks: the host must authorize and isolate those effects. A `read` label or a receipt text is never a sandbox or permission grant. Do not pass user/repository strings to a shell.

## Safe sequence

1. Define acceptance and inspect the actual workspace; retain `source_hash`.
2. Prepare changes against that identity and inspect the complete returned plan.
3. Supply the caller-selected policy for only the approved effects.
4. Apply with a stable operation ID. Record any partial result and inspect before retry.
5. Inspect the resulting source and run required named checks against its current hash.
6. Reconcile the exact returned receipt and retained invocation against required checks.
7. Record the verification proposal for the appropriate project/source revision through the ordinary expected-hash change workflow.

For example:

```bash
python tools/architect_cli.py adapter inspect --root /absolute/path/to/project
python tools/architect_cli.py adapter propose_change --root /absolute/path/to/project --request proposal-request.json
python tools/architect_cli.py adapter apply_change --root /absolute/path/to/project --request apply-request.json --policy /trusted/host-policy.json
python tools/architect_cli.py adapter run_checks --root /absolute/path/to/project --request check-request.json --policy /trusted/host-policy.json
python tools/architect_cli.py adapter recover --root /absolute/path/to/project --request recovery-request.json
```

These are operation invocations with distinct request files, not a script that makes an arbitrary project correct. A build, test and representative runtime interaction must each be included when applicable. No checks means no verification. Test checks use `kind: "test"` and a positive `minimum_tests`; supported unittest output must show that enough tests actually executed. A generic command is not test-coverage evidence. Design named check plans to fail when the intended behavior is broken.

## Results, summaries and failure handling

Capability and verification schemas are validated with `python tools/architect_cli.py validate-contract PATH --kind capability` or `--kind receipt`; generic JSON syntax success is not equivalent to capability/receipt validation. Canonical JSON object hashes, exact artifact-byte hashes, input source and output source are separate identities.

The ordinary CLI `--receipt` writes minimized run-summary telemetry, not an adapter verification receipt. Existing destinations are non-clobbering, gate/exit outcomes remain explicit, and operation IDs correlate results. Input failures and publication failures remain distinguishable. If a primary operation committed before a later receipt write failed, the result preserves that committed outcome and separately reports receipt failure (CLI exit 3). Do not treat every nonzero response as proof that no state changed.

Adapter receipts are attributed local evidence, not tamper-resistant logs. A self-consistent forged receipt cannot establish runtime verification without its matching retained invocation/current source. Failed/blocked/timed-out/partial/skipped/unknown outcomes never become passed through a formatting step. Authorization references are required for attempted consequential effects even when those effects fail.

If the adapter or required tooling is unavailable, export the plan/checks for manual execution, retain exact source identity and mark execution blocked or supplied/unverified. Provider-specific GitHub/deployment operations require a separately available compatible tool and actual authorization; no local operation pushes Git or deploys automatically.
