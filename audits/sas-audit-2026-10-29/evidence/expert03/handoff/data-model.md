# Data models (proposal)

- **DATA-TASK** Task

```json
{
  "columns": [
    {
      "name": "id",
      "primary_key": true,
      "type": "INTEGER"
    },
    {
      "name": "title",
      "nullable": false,
      "type": "TEXT"
    },
    {
      "name": "done",
      "nullable": false,
      "type": "INTEGER"
    }
  ],
  "components": [
    "CMP-STORE"
  ],
  "dialect": "sqlite",
  "id": "DATA-TASK",
  "name": "Task",
  "requirements": [
    "FR-001",
    "FR-002"
  ],
  "table": "tasks"
}
```