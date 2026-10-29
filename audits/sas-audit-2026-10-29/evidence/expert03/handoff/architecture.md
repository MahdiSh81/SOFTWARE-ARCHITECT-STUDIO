# Offline Task Tracker — architecture

Revision 2; canonical input SHA-256 0be8a325e1056b811d8b5ea99819d7b44490ede7b23371c280fe69fd821a28c3; projection SHA-256 0be8a325e1056b811d8b5ea99819d7b44490ede7b23371c280fe69fd821a28c3. Design intent; not deployed behavior.

## Brief
A personal offline task tracker: add, list, complete tasks; SQLite persists across runs; reject empty titles; no network, authentication, or deployment.

## Constraints
- Python 3.12 standard library only; SQLite; local CLI
- No remote service, auth or deployment; data stays in selected local DB

## Components
- CMP-CLI: CLI — Parse commands; validate input; render result and error exit codes.
- CMP-STORE: Task Store — Own SQLite schema and transactional task persistence.

## Open questions
- Exact package/distribution method remains proposed