# Deployment

> This document describes a controlled deployment. Read
> [Security](SECURITY.md) and the remaining limitations before accepting
> high-risk identity decisions.

## Option 1: Docker Compose with Caddy

### 1. Configure

```bash
python scripts/init_production.py --domain faces.example.com
```

Review `.env`, then store the Fernet key in the deployment secret manager.

### 2. Validate

```bash
set -a
. ./.env
set +a
python scripts/check_production.py
```

### 3. Start

```bash
docker compose up -d --build
docker compose logs -f app
```

Caddy obtains TLS certificates automatically.

The application container:

- Runs as UID 10001
- Uses a read-only root filesystem
- Drops all Linux capabilities
- Enables `no-new-privileges`
- Persists only the data volume
- Uses a health check against `/api/ready`

## Option 2: systemd and Nginx

The repository includes templates:

- `deploy/facesignup.service`
- `deploy/nginx-facesignup.conf`
- `deploy/setup-face-signup-env.sh`
- `deploy/install-nginx-snippet.py`

Adapt names, paths, domain, and process ownership to the host. Do not overwrite
an unrelated site configuration.

### Recommended filesystem layout

```text
/var/www/facesignup/app       Source and built frontend
/var/lib/facesignup           Writable database directory
/var/log/facesignup           Service logs
/etc/facesignup.env           Root-owned environment file
```

Files under `app` should be root-owned and read-only to the service account.
Only the database and log directories should be writable.

### Build

```bash
VITE_BASE=/face-signup/ npm run build
```

The final application needs:

- `backend/`
- `dist/`
- Python virtual environment or installed requirements
- `scripts/check_production.py` for operational checks

### Service

The provided unit runs:

```text
uvicorn backend.app:app --host 127.0.0.1 --port 8123 --workers 1
```

It includes memory, CPU, task, filesystem, address-family, privilege, kernel,
and syscall hardening.

### Nginx

The snippet proxies a dedicated path or host to `127.0.0.1:8123`, preserves
WebSocket upgrades, limits client request bodies, and reapplies security
headers.

Validate before reloading:

```bash
nginx -t
systemctl reload nginx
```

Never reload Nginx if validation fails.

## TLS and camera access

`getUserMedia` requires HTTPS outside localhost. TLS must terminate at the
reverse proxy and the proxy must send:

- `Host`
- `X-Real-IP`
- `X-Forwarded-For`
- `X-Forwarded-Proto: https`

## Reverse-proxy requirements

- WebSocket upgrade support
- At least 300-second read timeout for scan sessions
- Request limit of 512 KiB or less
- Buffering disabled for WebSocket traffic
- No public access to the backend port
- HSTS, CSP, frame denial, and MIME sniffing protection

## Permissions

Recommended:

```text
Environment file: root:service 0640
Application files: root:service 0640
Application directories: root:service 0750
Database directory: service:service 0700
Database file: service:service 0600
Log directory: service:service 0750
```

The service account must not be able to modify executable source or model files.

## First administrator login

1. Sign in with `admin` / `admin123`.
2. The application forces a password change.
3. Management APIs remain locked until the change succeeds.
4. Confirm the production check reports no default administrator.

## Upgrade procedure

1. Back up the database.
2. Build and test the release.
3. Verify model hashes.
4. Copy code and frontend.
5. Keep application files root-owned and service-read-only.
6. Restart only the FaceSignUp service.
7. Check `/api/ready`.
8. Test registration, face login, recovery, and admin login.

## Rollback

- Restore the previous application files.
- Restore the previous database only if the new release changed schema in an
  incompatible way.
- Restart the service.
- Validate health, login, and admin access.

## Clean uninstall

Before deleting data, confirm the target belongs to FaceSignUp:

```bash
systemctl disable --now facesignup.service
```

Remove only the FaceSignUp include from the reverse-proxy site configuration.
Validate the proxy configuration before reloading it. Then remove the
FaceSignUp application, database, backups, logs, service user, service unit, and
proxy snippet.

Do not delete a broad parent directory shared with other applications.
