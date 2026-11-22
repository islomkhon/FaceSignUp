# Configuration

FaceSignUp reads environment variables at backend startup. Do not commit real
configuration or encryption keys.

## Environment variables

### Core

#### `FACESIGNUP_ENV`

- Values: `development`, `production`
- Default: `development`
- Production enables strict host/origin checks, Secure cookies, HSTS, CSP, and
  disabled API documentation.

#### `FACESIGNUP_ALLOWED_HOSTS`

- Comma-separated hostnames accepted by Trusted Host middleware.
- Required in production.
- Example: `faces.example.com`

#### `FACESIGNUP_ALLOWED_ORIGINS`

- Comma-separated HTTPS origins accepted for write APIs and WebSockets.
- Required in production.
- Example: `https://faces.example.com`

#### `FACESIGNUP_COOKIE_SECURE`

- Boolean.
- Default: `true` in production, `false` in development.
- Keep `true` for every HTTPS deployment.

### Encryption and data

#### `FACESIGNUP_EMBEDDING_KEY`

- Fernet key required in production.
- Encrypts face embeddings and profile thumbnails.
- Generate once:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

- Store outside the database backup.
- Never rotate it without a migration; existing templates and photos become
  unreadable.

#### `FACESIGNUP_DB`

- Optional SQLite path.
- Default: `data/facesignup.db`
- Production example: `/var/lib/facesignup/facesignup.db`

### Liveness

#### `FACESIGNUP_ALLOW_MOVEMENT_FALLBACK`

- Boolean.
- Production default: `false`.
- When enabled, a scan with captured light phases but no measurable color
  response can continue using movement evidence alone.
- This weakens liveness assurance and is intended only for controlled
  compatibility testing.

### Request limits

#### `FACESIGNUP_MAX_FRAME_BYTES`

- Default: `2097152` (2 MiB)
- Maximum binary WebSocket frame accepted by the backend.

#### `FACESIGNUP_MAX_REQUEST_BYTES`

- Default: `524288` (512 KiB)
- Maximum HTTP JSON request size.
- Reverse proxies must enforce the same or a smaller limit.

### Docker compose only

#### `DOMAIN`

- Required by `compose.yaml` and `Caddyfile`.
- Must be a hostname without a scheme.

## Environment profiles

### Development

No `.env` is required.

```text
FACESIGNUP_ENV=development
Allowed origins: localhost:5173 and localhost:8100
Encryption key: data/embedding.key
Movement fallback: enabled
API docs: enabled
```

### Production

```dotenv
DOMAIN=faces.example.com
FACESIGNUP_ENV=production
FACESIGNUP_ALLOWED_HOSTS=faces.example.com
FACESIGNUP_ALLOWED_ORIGINS=https://faces.example.com
FACESIGNUP_COOKIE_SECURE=true
FACESIGNUP_ALLOW_MOVEMENT_FALLBACK=false
FACESIGNUP_MAX_FRAME_BYTES=2097152
FACESIGNUP_MAX_REQUEST_BYTES=524288
FACESIGNUP_EMBEDDING_KEY=replace-with-generated-key
```

`.env` is ignored by Git. Restrict it to the service account and deployment
administrator.

## Production validation

Run:

```bash
set -a
. ./.env
set +a
python scripts/check_production.py
```

The check verifies:

- Production mode
- HTTPS origins and allowed hosts
- Secure cookies
- Disabled movement fallback
- Valid Fernet key
- Required frontend/model files
- YuNet and SFace model integrity hashes
- Encrypted embeddings
- Consent metadata
- No administrator still using the bootstrap password

## Frontend build configuration

`VITE_BASE` controls the Vite asset and router base.

- Root deployment: `/`
- Subpath deployment: `/face-signup/`

The base must exactly match the public application path used by the reverse
proxy.

## Runtime assumptions

- One Uvicorn worker.
- One process owns all active scan and rate-limit state.
- SQLite database is writable only by the service account.
- Camera access works only on HTTPS or localhost.
- Browser and server clocks should be NTP-synchronized.
