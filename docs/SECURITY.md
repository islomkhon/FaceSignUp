# Security

## Security posture

FaceSignUp uses defense-in-depth controls for a controlled, single-instance
deployment. It is not certified presentation-attack detection, identity
proofing, or a substitute for a qualified liveness vendor.

## Threat model

### Protected assets

- Face embeddings
- Encrypted profile thumbnails
- Password and recovery-answer hashes
- Authentication sessions
- Role and account-management access
- TLS and encryption keys
- Integrity of recognition models and application code

### Relevant attackers

- Remote unauthenticated API client
- Malicious website attempting cross-origin requests
- Attacker holding a stolen temporary or session token
- Attacker using a photo, replay, virtual camera, or injected video
- Compromised or modified browser client
- Local unprivileged user on the host
- Administrator making accidental destructive changes

## Implemented controls

### Network and browser

- HTTPS required outside localhost.
- Trusted Host middleware.
- Strict allowed-origin checks on write APIs.
- Origin-checked WebSockets.
- HTTP-only, `SameSite=Strict` cookies.
- Secure production cookies with the `__Host-` prefix.
- CSP, HSTS, frame denial, MIME sniff protection, referrer restriction,
  permissions policy, and cross-origin isolation headers.
- API and HTML responses marked `no-store`.
- Production API documentation endpoints disabled.

### Temporary scan state

- Random opaque session, candidate, and enrollment tokens.
- Server-side expiry.
- Client-address binding.
- One-time candidate/enrollment consumption.
- Bounded WebSocket command size.
- Bounded frame size and face sample counts.
- Session count and rate limits.

### Authentication

- Face match followed by password verification.
- Argon2id password hashes with 64 MiB memory cost.
- Argon2id recovery-answer hashes.
- Five password attempts per candidate token.
- Session bearer token hashes stored with SHA-256.
- Password reset invalidates all sessions for the account.
- Account deletion requires the current password.

### Administrator

- Role checked on every administrator API call.
- Bootstrap password must be changed before management access.
- Final administrator cannot be demoted or deleted.
- Administrators cannot change their own role.
- Profile images require an authenticated administrator.

### Biometric storage

- Fernet authenticated encryption for embeddings and images.
- Encryption key separate from the database backup.
- Raw camera frames are not intentionally persisted.
- Only one 256x256 profile thumbnail is retained per enrollment.
- Account deletion cascades to biometric and recovery data.

### Supply chain and host

- Dependency audit commands and CI.
- SHA-256 checks for recognition models.
- Root-owned, service-read-only application and model files.
- systemd sandboxing.
- Read-only container root filesystem.
- No runtime CDN dependencies.

## Residual risks

### Custom liveness

The browser reports movement evidence. A modified client can forge it. Screen
light is useful but cannot prevent sophisticated replay, virtual cameras, or
display attacks. Use a certified provider for material identity decisions.

### Account discovery

The candidate list exposes up to three names, and recovery-question lookup can
reveal whether a named account exists. Production systems that cannot expose
enrollment status should use neutral aliases or a private identifier.

### Recovery question

One user-authored answer is weaker than a password, passkey, or high-entropy
recovery code. Rate limits reduce online guessing but do not prevent a person
or public profile from revealing the answer.

### Shared-origin deployment

Putting FaceSignUp under the same origin as unrelated web projects reduces
isolation. A compromised sibling application on the same host/origin can issue
same-origin requests. Use a dedicated hostname for stronger separation.

### Single-instance state

Rate limits and temporary scan tokens are in memory. Multiple workers or
instances would need Redis and PostgreSQL.

### SQLite

SQLite is appropriate for a small single-instance service. It is not a
multi-writer cluster database.

### Model fairness

Face-recognition accuracy can vary by demographics, occlusion, lighting,
camera quality, and disability. Test the system with representative intended
users and provide a non-face fallback.

## Secret handling

- Never commit `.env`, Fernet keys, session cookies, database copies, logs, or
  real biometric data.
- Restrict the environment file to `root:service 0640`.
- Store the Fernet key in a secret manager.
- Keep the key outside database backups.
- Rotate any credential that was shared in chat, screenshots, or source.
- Use SSH keys instead of root password authentication.

## Dependency checks

```bash
npm audit --omit=dev
pip-audit -r backend/requirements.txt
```

Also run:

```bash
npm ci
npm test
npm run check:locales
python scripts/check_production.py
```

## Incident response

1. Stop the FaceSignUp service.
2. Preserve logs without copying biometric payloads.
3. Rotate the Fernet key only with a documented migration because rotation
   makes existing templates unreadable.
4. Invalidate all sessions:

```sql
DELETE FROM auth_sessions;
```

5. Rotate the administrator password.
6. Rotate the compromised encryption key and plan account re-enrollment.
7. Review proxy, authentication, rate-limit, and model-integrity logs.
8. Restore a known-good release and database if integrity is uncertain.
9. Notify affected users and regulators when required by applicable law.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use the repository's
private GitHub Security Advisory feature and include:

- Affected version/commit
- Reproduction steps
- Security impact
- Whether real personal data is involved
- Suggested mitigation

Avoid attaching real face images, embeddings, passwords, recovery answers, or
production database exports.
