# Real-browser workbench tests
Playwright covers startup, keyboard focus, persistence, cross-tab writes, portable export, pending drafts across preference changes and reload, collection-bound editing, common-field authoring, replacement guards, and structured constraints export. These checks do not certify screen-reader behavior.

From this directory run `npm ci`, `npx playwright install chromium`, then `npm test`. The test runner starts `serve_workbench.py`, which binds only `127.0.0.1` and exposes only the workbench HTML and JavaScript. Repository source and Git metadata return 404; a regression verifies that boundary. Use a free port 4173 and avoid unrelated servers on it.

Web Locks serialize same-origin writes where supported. Browsers without Web Locks retain optimistic conflict checks and per-tab drafts; that fallback is advisory. Unapplied editor drafts are included in private workbench backups, while portable project exports contain applied canonical state. Reset a stale full-JSON draft only after preserving or reconciling it. Manually validate screen-reader announcements, zoom, RTL Persian, and narrow viewports before claiming full accessibility conformance.
