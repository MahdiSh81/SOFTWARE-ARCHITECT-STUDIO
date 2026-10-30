# Exact gates and verification — 0.7

Run `validate PATH [--render] [--full-openapi] [--gate report|structural|full]`. CLI defaults to structural gating; report mode is explicitly non-gating. Each applicable check records file, method, toolkit/input identity and passed/failed/skipped/blocked/timed_out/tool_error/not_run_due_to_budget. A required incomplete gate cannot pass. Existing independent results survive a failed/timed-out validator.

JSON/YAML enter the same OAS basic checks, including legal path-item metadata, responses and path parameters. Basic checks are not complete schema validation. Optional installed openapi-spec-validator supplies the full adapter; optional jsonschema validates the published project schema in full mode. External refs are blocked. Optional YAML parsing runs in a bounded worker. Versions/environment are recorded via doctor and release verification; tools are never downloaded automatically by CLI.

Mermaid text lint is explicitly heuristic. A requested, policy-permitted configured renderer is attempted even if lint warns. No external resource/directive/active-markup input is rendered under the built-in policy. Renderer output, deadline/process group and file-size bounds are scoped local controls; they do not create a full authority sandbox. Full syntax/render claims require an actual tool run and expected output.

Use `data-check` only for the supplied allowlisted structured SQLite schema; arbitrary SQL/migrations and production data are not executed. API/project correspondence covers supported operations; arbitrary prose and runtime behavior still need review. `evaluate --gate` is a distinct lexical/constraint gate, not model-quality certification. Use the regression, cross-surface and optional full-validator suites described in README.

Patch 0.7.1 treats a missing YAML parser as an incomplete structural gate, normalizes supported file extensions, and retains other file results when a subtree cannot be enumerated. A blocked subtree keeps the policy gate unsatisfied. Verification-to-requirement references are checked before coverage calculation.
