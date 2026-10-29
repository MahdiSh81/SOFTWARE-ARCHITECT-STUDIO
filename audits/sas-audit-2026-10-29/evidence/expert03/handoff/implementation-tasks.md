# Implementation tasks

- **TASK-001** Implement persistent task store · Requirements: FR-001, FR-002
  Acceptance criteria: Temporary database tests prove add, list, complete and invalid-ID behavior.
  Dependencies: ADR-001
- **TASK-002** Implement CLI and integration tests · Requirements: FR-001, FR-002
  Acceptance criteria: python -m unittest discover -s tests passes; separate subprocesses prove persistence and error exits.
  Dependencies: ADR-001