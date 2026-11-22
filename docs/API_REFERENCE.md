# API Reference

The production application disables FastAPI `/docs`, `/redoc`, and
`/openapi.json`. This document is the maintained external reference.

All paths below are relative to the application base. The browser normally uses
`/api` and `/ws`.

## Request rules

- State-changing JSON requests must include `Content-Type: application/json`.
- Production requests must include an allowed `Origin`.
- JSON request bodies are limited to `FACESIGNUP_MAX_REQUEST_BYTES`.
- API responses use `Cache-Control: no-store`.
- Authentication uses the HTTP-only `fs_session` cookie.

## Error format

Most application errors use:

```json
{
  "detail": "Readable error message."
}
```

Common statuses:

| Status | Meaning |
| ---: | --- |
| 400 | Invalid form values or request |
| 401 | Authentication or temporary token failed |
| 403 | Wrong origin, role, or locked administrator |
| 404 | Resource not found |
| 409 | Duplicate display name |
| 411 | Missing request body length in production |
| 413 | Request body too large |
| 415 | Non-JSON write request |
| 422 | Schema validation failure |
| 429 | Rate limit exceeded |

## Health and readiness

### `GET /api/health`

Returns application mode, model version, match threshold, environment, and
whether movement-only fallback is enabled.

### `GET /api/ready`

Checks that SQLite is available.

```json
{
  "ready": true,
  "model": "sface-2021dec/yunet-2023mar"
}
```

## Face sessions

### `POST /api/face/sessions`

Creates a short-lived scan session and movement challenge.

Response:

```json
{
  "sessionId": "opaque-token",
  "expiresIn": 180,
  "challenge": {
    "step": 1,
    "action": "blink_both",
    "instruction": "Blink both eyes normally"
  }
}
```

Limits:

- 20 requests per client per 60 seconds.
- Session expires after 180 seconds.
- The WebSocket must connect from the same client address.

## Face WebSocket

### `WS /ws/face?session_id=<sessionId>`

The socket alternates between binary JPEG frames and JSON text commands.

Client frames:

- Recommended: JPEG, width 640 pixels.
- Maximum: `FACESIGNUP_MAX_FRAME_BYTES`.

Client commands:

```json
{"type":"action_detected","action":"blink_both","confidence":0.82}
```

```json
{"type":"lighting_ready"}
```

```json
{"type":"lighting_complete"}
```

```json
{"type":"capture_final"}
```

```json
{"type":"cancel"}
```

Server events:

| Type | Purpose |
| --- | --- |
| `session_ready` | Socket accepted and challenge delivered |
| `frame_quality` | Current face count, size, center, and brightness |
| `action_retry` | Movement needs to be repeated |
| `action_passed` | Movement accepted; prepare for light challenge |
| `lighting_started` | Authoritative light timer has started |
| `step_started` | Final embedding stage has started |
| `face_match` | Ranked account candidates |
| `face_no_match` | Enrollment ticket for a new account |
| `scan_failed` | Scan rejected |
| `session_expired` | Session timed out |
| `error` | Invalid command or size error |
| `cancelled` | Client cancelled |

Example candidate event:

```json
{
  "type": "face_match",
  "step": 4,
  "candidates": [
    {"token": "opaque-token", "name": "Sunny"},
    {"token": "opaque-token-2", "name": "Sunny 2"}
  ],
  "expiresIn": 90,
  "quality": {
    "faces": 1,
    "areaRatio": 0.22,
    "brightness": 112
  }
}
```

Example no-match event:

```json
{
  "type": "face_no_match",
  "step": 4,
  "enrollmentTicket": "opaque-token",
  "quality": {
    "faces": 1,
    "areaRatio": 0.22,
    "brightness": 112
  }
}
```

## Authentication

### `POST /api/auth/password`

Completes face sign-in.

```json
{
  "candidate_token": "opaque-token",
  "password": "user-password"
}
```

The backend rechecks the face score and verifies the password hash.

### `POST /api/auth/name-login`

Signs in without a face scan.

```json
{
  "display_name": "Sunny",
  "password": "user-password"
}
```

### `POST /api/auth/register`

Creates an account using a valid enrollment ticket.

```json
{
  "enrollment_ticket": "opaque-token",
  "display_name": "Sunny",
  "password": "secure-password-42",
  "security_answers": [
    {
      "question": "What was the name of my first pet?",
      "answer": "Milo"
    }
  ],
  "terms_accepted": true,
  "biometric_consent": true
}
```

Rules:

- Exactly one question and answer.
- Password: at least 10 characters with a letter and number.
- Answer: at least 4 characters.
- Unique case-insensitive display name.
- Current Terms and biometric consent required.

### `POST /api/auth/recovery/questions`

Returns the account's one recovery question.

```json
{
  "display_name": "Sunny"
}
```

### `POST /api/auth/recovery/reset`

Verifies the recovery answer and replaces the password.

```json
{
  "display_name": "Sunny",
  "answers": [
    {
      "question": "What was the name of my first pet?",
      "answer": "Milo"
    }
  ],
  "new_password": "new-secure-password-42"
}
```

Resetting a password deletes all active sessions for that account.

### `GET /api/auth/me`

Returns the current user or `401`.

### `POST /api/auth/logout`

Deletes the current auth session and clears the cookie.

### `POST /api/auth/account/delete`

Permanently deletes the current account, face template, encrypted photo,
recovery answer, and sessions after password verification.

```json
{
  "password": "user-password"
}
```

## Administrator APIs

All administrator routes require a signed-in `admin` account whose bootstrap
password has been changed.

### `GET /api/admin/users`

Returns account ID, name, role, password-change state, face state, photo state,
and creation date. Photo blobs are not embedded in this response.

### `GET /api/admin/users/{user_id}/photo`

Returns the authenticated account's decrypted JPEG thumbnail.

### `PATCH /api/admin/users/{user_id}/role`

```json
{
  "role": "admin"
}
```

An administrator cannot demote themselves. The final administrator cannot be
demoted.

### `DELETE /api/admin/users/{user_id}`

Permanently deletes another account and cascades its biometric, recovery, and
session data. The final administrator cannot be deleted.

### `POST /api/admin/password`

Changes the current administrator password.

```json
{
  "current_password": "current-password",
  "new_password": "new-secure-password-42"
}
```

## Rate-limit summary

| Action | Limit |
| --- | ---: |
| Face session creation | 20 / 60 seconds |
| Face password login | 8 / 60 seconds |
| Name login | 8 / 60 seconds |
| Registration | 6 / 5 minutes |
| Recovery question lookup | 8 / 5 minutes |
| Recovery reset | 6 / 5 minutes |
| Account deletion | 5 / 5 minutes |
| Password attempts per candidate token | 5 |

Rate limiting is process-local in this MVP.
