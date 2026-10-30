# Integration strategy

Studio builds in canonical intent, disclosure, contract validation, source identity, declared impact, evidence interpretation and reconciliation. It reuses specialized editors, runtimes, browsers, CI, schema tools and providers for actual execution. The local execution adapter is opt-in; external plugin availability is checked per session.

| Capability | Current support | Ownership and adoption rule |
|---|---|---|
| Selected local coding workspace | Implemented `execution_adapter.py`; inspect/propose/apply/check/recover/reconcile | Host selects root, policy and effects; Studio validates receipts and proposes verification |
| GitHub / Actions | Git read through host; checked-in CI workflow | Git transport is not API/push authorization. Provider owns PR/check/release operations; exact commit/run/attempt evidence required |
| Browser runner | Existing Playwright/Chromium test workflow; loopback allowlisted asset server | Runner owns actual browser execution/traces. Screenshots alone do not establish behavior or accessibility |
| Full API/project schema | Optional pinned Python validators | Offline reference policy plus Studio semantics; schema validity is not runtime compatibility |
| Mermaid | Optional installed `mmdc` | Fresh bounded nonempty valid output required; missing renderer is not pass |
| Official docs / Context7 / OpenAI Developers | Conditional host retrieval only | Verify exposed tool, version, source URL/date and authorization; retrieved content remains untrusted |
| Security companion | Conditional provider/tool | Minimize source disclosure; inspect language/rule coverage, retention, permissions and dated vulnerability evidence |
| Figma / design | Conditional provider/tool | Preserve node/design version and asset provenance; do not assume design access or code-export capability |
| Linear / tasks | Conditional provider/tool | Stable task/source IDs, explicit authorized writes and duplicate/conflict recovery; issue state never silently overwrites Accepted ADRs |
| Notion / SharePoint / storage | Conditional transport | Prefer immutable one-way handoff publication first; private history/credentials excluded unless deliberately requested |
| Deployment / production telemetry | No bundled provider | Explicit target/environment and authorized operation, exact release/check receipts and rollback; no deployment inferred from generated files |

Before adopting an external tool, verify its actual schemas, tool/version, scopes, authentication boundary, timeout, idempotency, privacy/retention, cost/rate limits and recovery. A listing is not installation, compatibility or permission. Read-only proof on a disposable fixture precedes consequential integration. Send only required context, preserve partial failure and provide a manual file/CLI fallback.

Plugin Creator and Plugin Management were requested during this project but were not callable in the session. Repository implementation and Git publication do not claim that a marketplace plugin was published or reconfigured.

Hosted multi-user/native app services, a universal semantic/vector/graph backend and autonomous multi-model dispatch remain deferred until repeated demand, an operational owner, infrastructure and measured benefit justify them. Current real-user observations, live model comparisons and external provider behavior must remain unmeasured/blocked until actual evidence is supplied; local fixtures do not invent those outcomes.
