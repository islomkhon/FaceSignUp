# Development

## Prerequisites

- Node.js 24+
- npm 11+
- Python 3.13+
- A webcam and modern Chromium, Edge, Firefox, or Safari browser

## Initial setup

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
npm ci
```

### Linux/macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
npm ci
```

`npm ci` runs `scripts/localize-mediapipe.mjs`, which copies the matching
MediaPipe WASM runtime into `public/mediapipe/wasm`.

The generated `public/mediapipe/wasm/` directory is intentionally ignored by
Git and must be regenerated after cloning or changing the MediaPipe package.

## Start development

```powershell
npm run dev
```

Services:

- Vue/Vite: `http://127.0.0.1:5173/faceScanner`
- FastAPI: `http://127.0.0.1:8100`

Vite proxies `/api` and `/ws` to FastAPI.

## Commands

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start frontend and backend |
| `npm run dev:web` | Start Vite only |
| `npm run dev:api` | Start FastAPI with reload |
| `npm run build` | Build production frontend |
| `npm start` | Serve built frontend through FastAPI |
| `npm test` | Run backend tests |
| `npm run check:locales` | Validate all translations and Terms |
| `npm run check:production` | Run production configuration checks |
| `npm run localize:mediapipe` | Refresh local MediaPipe runtime |

Python checks:

```powershell
.\.venv\Scripts\python.exe -m ruff check backend scripts
.\.venv\Scripts\python.exe -m ruff format --check backend scripts
```

## Tests

Backend tests cover:

- Password and recovery-answer hashing
- Face candidate ranking
- Three-stage face consistency
- Lighting evaluation
- Encrypted database storage
- Profile photo encryption
- Face-plus-password login
- Candidate expiry and client binding
- Single-question recovery
- Registration retry behavior
- Enrollment client binding
- WebSocket session binding
- Administrator and role controls
- Frontend cache headers

Run the complete local verification before committing:

```powershell
npm test
npm run check:locales
$env:VITE_BASE = "/"
npm run build
.\.venv\Scripts\python.exe -m ruff check backend scripts
.\.venv\Scripts\python.exe -m ruff format --check backend scripts
```

## Adding a language

1. Add the locale and speech locale to `localeOptions` in `src/locales.js`.
2. Add a complete message dictionary with the same keys as `messages.en`.
3. Add all 11 Terms sections to `termsByLocale` in `src/terms.js`.
4. Preserve placeholders such as `{name}`.
5. Run `npm run check:locales`.
6. Test speech synthesis on a device with a matching language voice.

The locale checker rejects missing keys, extra keys, empty values, untranslated
English values, placeholder mismatches, and Terms structure differences.

## Updating models

1. Replace the model only with a trusted upstream artifact.
2. Record its source and license.
3. Update the SHA-256 in `MODEL_MANIFEST.md`.
4. Update `EXPECTED_MODEL_HASHES` in `scripts/check_production.py`.
5. Run backend tests and representative camera tests.
6. Re-enroll test users if the embedding model changes.

The current model version is stored with each face embedding. A recognition
model migration requires a compatibility strategy or re-enrollment.

## Database changes

SQLite migrations are applied in `Database.initialize()`. Rules:

- Preserve existing user and biometric records.
- Use nullable columns or explicit defaults for added fields.
- Never log decrypted biometric values.
- Back up the database before a destructive migration.
- Test both a fresh database and a migrated database.

## WebSocket debugging

Browser developer tools show the WebSocket handshake and JSON control events.
Binary frame contents are intentionally not logged.

Useful backend logs:

- Accepted movement action
- Start of each lighting phase
- Lighting sample and detection-failure counts
- Face consistency scores
- Number of ranked candidates

Never add raw frames, passwords, answers, embeddings, or decrypted profile
images to logs.

## Code style

- Python: Ruff defaults from repository configuration.
- JavaScript/Vue: two-space indentation and semicolons.
- Keep security decisions server-side.
- Preserve all translations when changing user-facing text.
- Add regression tests for authentication and token behavior.

## Local data

The following are ignored by Git:

- `.venv/`
- `node_modules/`
- `data/`
- `dist/`
- `.env`
- logs, backups, test data, Python caches, and deployment archives

To start with a completely fresh local database, stop the backend and remove the
local `data/facesignup.db`. This deletes local test accounts and cannot be
undone.
