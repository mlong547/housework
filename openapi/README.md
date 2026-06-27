# Housework Task API OpenAPI

This folder contains an OpenAPI v3 schema for a REST API that tracks recurring and one-off housework tasks.

- Schema: `openapi.yaml`
- Base URL in the schema: `http://localhost:5000`
- Date format: ISO 8601 calendar dates such as `2026-07-03`
- Timestamp format: ISO 8601 date-times such as `2026-07-03T20:25:00Z`

## Resource model

The basic resource is a task. A task has an `endGoalDate`, a `status`, and a `repeating` flag.

One-off tasks set `repeating` to `false` and omit `recurrence` or set it to `null`.

Repeating tasks set `repeating` to `true` and include a `recurrence` rule. The task's `endGoalDate` must fall on that recurrence cadence. For example, "every other Friday" is represented as:

```json
{
  "frequency": "weekly",
  "interval": 2,
  "daysOfWeek": ["friday"]
}
```

## Routes

### `GET /tasks`

Lists tasks. Use this route to query tasks by end goal date and to see completed and pending tasks.

Query parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `endGoalDate` | date | No | Return tasks with this exact end goal date. |
| `endGoalDateFrom` | date | No | Return tasks with an end goal date on or after this date. |
| `endGoalDateTo` | date | No | Return tasks with an end goal date on or before this date. |
| `status` | string | No | Return `pending` or `completed` tasks. |
| `repeating` | boolean | No | Return only recurring tasks or only one-off tasks. |

Request body: none.

Response body:

```json
{
  "data": [
    {
      "id": "9f7f0c87-5506-4df7-9f4a-8bdf9735de6b",
      "title": "Clean kitchen counters",
      "description": "Wipe counters and stovetop.",
      "status": "pending",
      "endGoalDate": "2026-07-03",
      "repeating": true,
      "recurrence": {
        "frequency": "weekly",
        "interval": 1,
        "daysOfWeek": ["friday"]
      },
      "completedAt": null,
      "createdAt": "2026-06-26T18:12:00Z",
      "updatedAt": "2026-06-26T18:12:00Z"
    }
  ],
  "meta": {
    "count": 1
  }
}
```

Error responses:

- `400` with `ErrorResponse` when query parameters are invalid.

### `POST /tasks`

Creates a one-off or repeating task.

Request body:

```json
{
  "title": "Clean bathrooms",
  "description": "Full sink, shower, mirror, and toilet clean.",
  "endGoalDate": "2026-07-03",
  "repeating": true,
  "recurrence": {
    "frequency": "weekly",
    "interval": 2,
    "daysOfWeek": ["friday"]
  }
}
```

Request fields:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `title` | string | Yes | Short task name. |
| `description` | string or null | No | Optional notes. |
| `endGoalDate` | date | Yes | Date by which the task occurrence should be completed. |
| `repeating` | boolean | Yes | Whether the task uses a recurrence rule. |
| `recurrence` | object or null | Conditional | Required when `repeating` is `true`; otherwise omit or set to `null`. |

Response body:

```json
{
  "data": {
    "id": "9f7f0c87-5506-4df7-9f4a-8bdf9735de6b",
    "title": "Clean bathrooms",
    "description": "Full sink, shower, mirror, and toilet clean.",
    "status": "pending",
    "endGoalDate": "2026-07-03",
    "repeating": true,
    "recurrence": {
      "frequency": "weekly",
      "interval": 2,
      "daysOfWeek": ["friday"]
    },
    "completedAt": null,
    "createdAt": "2026-06-26T18:12:00Z",
    "updatedAt": "2026-06-26T18:12:00Z"
  }
}
```

Status codes:

- `201` when the task is created. The `Location` header points to the created task.
- `400` with `ErrorResponse` when the body is invalid.

### `GET /tasks/{taskId}`

Returns one task by ID.

Path parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | UUID string | Yes | Unique task identifier. |

Request body: none.

Response body:

```json
{
  "data": {
    "id": "9f7f0c87-5506-4df7-9f4a-8bdf9735de6b",
    "title": "Replace HVAC filter",
    "description": "Use 20x25x1 filter from garage shelf.",
    "status": "completed",
    "endGoalDate": "2026-07-01",
    "repeating": false,
    "recurrence": null,
    "completedAt": "2026-07-01T14:30:00Z",
    "createdAt": "2026-06-26T18:12:00Z",
    "updatedAt": "2026-07-01T14:30:00Z"
  }
}
```

Error responses:

- `404` with `ErrorResponse` when the task does not exist.

### `PUT /tasks/{taskId}`

Replaces all editable fields on a task.

Path parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | UUID string | Yes | Unique task identifier. |

Request body:

```json
{
  "title": "Clean bathrooms",
  "description": "Full sink, shower, mirror, and toilet clean.",
  "status": "pending",
  "endGoalDate": "2026-07-17",
  "repeating": true,
  "recurrence": {
    "frequency": "weekly",
    "interval": 2,
    "daysOfWeek": ["friday"]
  },
  "completedAt": null
}
```

Request fields:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `title` | string | Yes | Short task name. |
| `description` | string or null | No | Optional notes. |
| `status` | string | Yes | `pending` or `completed`. |
| `endGoalDate` | date | Yes | Date by which the task occurrence should be completed. |
| `repeating` | boolean | Yes | Whether the task uses a recurrence rule. |
| `recurrence` | object or null | Conditional | Required when `repeating` is `true`; otherwise omit or set to `null`. |
| `completedAt` | date-time or null | No | Completion timestamp. |

Response body: the same `TaskResponse` shape returned by `GET /tasks/{taskId}`.

Error responses:

- `400` with `ErrorResponse` when the body is invalid.
- `404` with `ErrorResponse` when the task does not exist.

### `PATCH /tasks/{taskId}`

Updates selected task fields while leaving omitted fields unchanged. This is the simplest way to mark a task complete or pending.

Path parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | UUID string | Yes | Unique task identifier. |

Request body:

```json
{
  "status": "completed",
  "completedAt": "2026-07-03T20:25:00Z"
}
```

Request fields:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `title` | string | No | Short task name. |
| `description` | string or null | No | Optional notes. |
| `status` | string | No | `pending` or `completed`. |
| `endGoalDate` | date | No | Date by which the task occurrence should be completed. |
| `repeating` | boolean | No | Whether the task uses a recurrence rule. |
| `recurrence` | object or null | No | Recurrence rule. Required if the updated task is repeating. |
| `completedAt` | date-time or null | No | Completion timestamp. |

Response body: the same `TaskResponse` shape returned by `GET /tasks/{taskId}`.

Error responses:

- `400` with `ErrorResponse` when the body is invalid.
- `404` with `ErrorResponse` when the task does not exist.

### `DELETE /tasks/{taskId}`

Deletes a one-off task or a recurring task series definition.

Path parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `taskId` | UUID string | Yes | Unique task identifier. |

Request body: none.

Response body: none.

Status codes:

- `204` when the task is deleted.
- `404` with `ErrorResponse` when the task does not exist.

## Shared schemas

### `Task`

Response representation of a task.

| Name | Type | Description |
| --- | --- | --- |
| `id` | UUID string | Unique task identifier. |
| `title` | string | Short task name. |
| `description` | string or null | Optional notes. |
| `status` | string | `pending` or `completed`. |
| `endGoalDate` | date | Date by which this task occurrence should be completed. |
| `repeating` | boolean | Whether the task follows a recurrence rule. |
| `recurrence` | object or null | Recurrence definition for repeating tasks. |
| `completedAt` | date-time or null | Timestamp when the task was completed. |
| `createdAt` | date-time | Timestamp when the task was created. |
| `updatedAt` | date-time | Timestamp when the task was last updated. |

### `RecurrenceRule`

Defines the cadence for a repeating task. Each generated `endGoalDate` must match the rule.

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `frequency` | string | Yes | One of `daily`, `weekly`, `monthly`, or `yearly`. |
| `interval` | integer | Yes | Number of frequency units between occurrences. `2` with `weekly` means every other week. |
| `daysOfWeek` | string array | No | Weekdays for weekly cadences, such as `["friday"]`. |
| `dayOfMonth` | integer | No | Calendar day for monthly cadences. |
| `weekOfMonth` | integer | No | Ordinal week for monthly rules, such as the second Saturday. |
| `monthOfYear` | integer | No | Month for yearly cadences. |
| `startsOn` | date | No | First date in the recurrence schedule. Defaults to the task `endGoalDate` when omitted. |
| `endsOn` | date or null | No | Optional final recurrence date. |

### `ErrorResponse`

Standard error response body:

```json
{
  "error": {
    "code": "validation_error",
    "message": "recurrence is required when repeating is true.",
    "details": {
      "field": "recurrence"
    }
  }
}
```
