# Diagram contracts

Use distinct views instead of one overstuffed graph:
- **System context**: actors, owned system boundary, external dependencies.
- **Containers**: deployable apps/services, databases, queues, sync/async flows.
- **Component**: only when a specific container needs internal boundaries.
- **Sequence**: at least one critical success path and relevant failure branch.
- **ER**: high-value entities and cardinality, tenant key where applicable.
- **Deployment**: topology only if environments/regions/network boundaries are known or explicitly proposed.

Name Mermaid files `*.mmd` and start with a supported declaration (`flowchart`, `graph`, `sequenceDiagram`, `erDiagram`, `stateDiagram-v2`, `classDiagram`, `gantt`). Avoid code fences inside `.mmd`. Mermaid text must be checked with an installed Mermaid CLI (`mmdc`) for real parser/render checks; bundled lightweight validator can only do superficial checks and never warrants a 'Mermaid syntax verified' claim.

Validation tiers:
1. Manual conceptual audit: directional correctness, trust boundaries and consistency with implementation.
2. `architect_cli.py validate <artifact-dir>`: structured contracts and non-empty Mermaid, balanced delimiters, suspicious dangling links (heuristic).
3. If `mmdc` is locally present, attempt each `.mmd` render to SVG and treat failures as syntax/render errors.
4. Browser workbench visualization is intentionally a simple client-side logical graph, **not** a Mermaid engine, and does not validate `.mmd` syntax.

For code repositories, never call a proposed diagram 'current state' without actual verified repo evidence. If architecture differs from docs or code, make a `current` and `target` view explicit.
