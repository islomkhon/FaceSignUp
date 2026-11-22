# Production readiness

This project is hardened for a controlled single-instance deployment, but the
custom browser liveness flow is not a replacement for a certified biometric
liveness product. Do not describe it as high-assurance identity verification.

## Production launch requirements

1. Use the Docker/Caddy package over a real HTTPS hostname.
2. Set every value in `.env`; do not commit `.env`.
3. Generate and retain `FACESIGNUP_EMBEDDING_KEY` in a secret manager.
4. Keep `FACESIGNUP_ALLOW_MOVEMENT_FALLBACK=false`.
5. Test enrollment, matching, recovery, deletion, voice guidance, and lighting
   fallback on the actual browsers, cameras, monitors, and lighting conditions
   used by intended users.
6. Obtain privacy/legal review for the deployment jurisdiction. In mainland
   China, face verification cannot be the only available verification method
   when a suitable non-face alternative exists.
7. If children under 14 may register, add a guardian-consent and age-verification
   flow. The current checkbox alone is not sufficient for that population.

## Non-face access

Users can select **Use name and password instead** from `/faceScanner`.
Face sign-in requires the account password after a successful face match.
Recovery uses the unique registered name and the one user-authored security
question stored at registration. No email address is collected or displayed.

## Biometric data

- Camera frames are processed in memory and are not intentionally persisted.
- SFace embeddings and the small enrollment profile thumbnail are protected at
  rest with Fernet authenticated encryption.
- Passwords and security answers use Argon2id hashes.
- Session bearer tokens are hashed at rest; face-match and enrollment tokens
  expire and are bound to the requesting client address.
- Registration records separate Terms of Service and biometric-consent versions
  and timestamps.
- The current consent flow does not collect age. A separate guardian-consent
  process is required before offering the service to children under the
  relevant legal age.
- Signed-in users can delete their account, face template, profile thumbnail,
  and recovery data.
- The embedding key must be backed up separately from `data/facesignup.db`.
- Losing the embedding key makes stored templates unreadable. Replacing it
  without a key-rotation migration will require users to re-enroll.

## Deployment

```bash
python scripts/init_production.py --domain faces.example.com
# Review the generated .env and place its values in the deployment secret store.
set -a; . ./.env; set +a
python scripts/check_production.py
docker compose up -d --build
docker compose logs -f app
```

Caddy terminates TLS and proxies to the non-root application container. Camera
access requires HTTPS, except on localhost during development.

## Backups

Back up the `app_data` Docker volume using SQLite's online backup mechanism or
during a maintenance window. Encrypt backups, restrict access, test restoration,
and store the embedding key separately. Never put the database key and
biometric database in the same backup bundle.

## Monitoring

- Monitor `GET /api/health`.
- Alert on repeated `401`, `403`, `422`, and `429` responses.
- Monitor face-detection failures and `movement_liveness` fallbacks.
- Never log passwords, security answers, raw frames, or decrypted embeddings.
- Use a reverse-proxy access log with retention limits.

## Remaining blockers for high-assurance public authentication

- The custom movement and screen-light checks are not certified presentation
  attack detection.
- Browser action evidence can be forged by modified client code.
- Camera frames can be injected through virtual-camera or compromised-client
  attacks.
- The in-memory rate limiter and SQLite database target one application
  instance. Multi-instance deployment needs shared rate limiting and PostgreSQL.
- Production requires account recovery abuse testing and a user-support process.
- Model accuracy and fairness must be evaluated with representative local users.

For public, financial, government, or high-risk use, replace the custom
liveness decision with a certified provider such as FaceTec, iProov, AWS Face
Liveness, or Azure Face Liveness, and keep the server-side identity-consistency
and recovery-answer checks already implemented here.
