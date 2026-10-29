# Real-browser workbench tests
Playwright runs Chromium on a GitHub-hosted runner and covers startup, keyboard focus, persistence, export, and cross-tab writes. It is not full screen-reader certification.
Run `npm install`, `npx playwright install chromium`, `npm test`. Web Locks serialize same-origin writes where supported. Browsers without Web Locks retain optimistic conflict checks and per-tab drafts; that fallback is advisory. Manually validate screen-reader announcements, zoom, RTL Persian, and narrow viewports before claiming full accessibility conformance.
